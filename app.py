import hmac
import os
import threading
import time
from pathlib import Path

import cv2
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    has_request_context,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from werkzeug.security import check_password_hash

try:
    from flask_login import (
        LoginManager,
        UserMixin,
        current_user,
        login_required,
        login_user,
        logout_user,
    )
except ImportError:
    LoginManager = None
    UserMixin = object
    current_user = None
    login_required = None
    login_user = None
    logout_user = None

import config
from detector import PersonDetector
from event_logger import EventLogger
from motion import MotionDetector
from mqtt_client import MqttGateway
from notifier import Notifier
from state_manager import SystemStateManager
from utils import cleanup_old_snapshots, draw_boxes, event_id, save_snapshot


app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

if config.DASHBOARD_AUTH_ENABLED and LoginManager is None:
    raise RuntimeError("DASHBOARD_AUTH_ENABLED requires Flask-Login. Install requirements.txt.")

login_manager = LoginManager(app) if LoginManager is not None else None
if login_manager is not None:
    login_manager.login_view = "login"


class DashboardUser(UserMixin):
    def __init__(self, username):
        self.id = username


if login_manager is not None:
    @login_manager.user_loader
    def load_user(user_id):
        if user_id == config.DASHBOARD_USERNAME:
            return DashboardUser(user_id)
        return None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/") or request.path.startswith("/video_feed"):
            return jsonify({"message": "Authentication required"}), 401
        return redirect(url_for("login"))


state_manager = SystemStateManager()
motion_detector = MotionDetector(
    threshold=config.MOTION_THRESHOLD,
    min_area=config.MOTION_MIN_AREA,
    blur_size=config.BLUR_SIZE,
)
person_detector = PersonDetector(
    confidence_threshold=config.PERSON_CONFIDENCE_THRESHOLD,
    model_path=config.MODEL_PATH,
    proto_path=config.PROTO_PATH,
)
event_logger = EventLogger(config.EVENTS_DIR, config.LOGS_DIR)
notifier = Notifier(
    enabled=config.TELEGRAM_ENABLED,
    bot_token=config.TELEGRAM_BOT_TOKEN,
    chat_id=config.TELEGRAM_CHAT_ID,
    timeout_seconds=config.TELEGRAM_TIMEOUT_SECONDS,
)
mqtt_gateway = None

frame_lock = threading.Lock()
latest_raw_frame = None
latest_display_frame = None
latest_detection_status = {
    "motion_detected": False,
    "motion_box_count": 0,
    "person_detected": False,
    "person_confidence": None,
    "person_bbox": None,
    "motion_detection_seconds": None,
    "person_inference_seconds": None,
    "updated_at": None,
}
capture_running = True


def to_json_bbox(bbox):
    if bbox is None:
        return None
    return [int(value) for value in bbox]


def to_json_float(value):
    if value is None:
        return None
    return round(float(value), 3)


def require_dashboard_auth(view):
    if config.DASHBOARD_AUTH_ENABLED and login_required is not None:
        return login_required(view)
    return view


def open_capture():
    source = config.WEBCAM_INDEX if config.USE_WEBCAM else config.VIDEO_SOURCE
    print("[VIDEO] Opening source:", source)

    cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    print("[VIDEO] Capture opened:", cap.isOpened())
    return cap


def current_frame_copy():
    with frame_lock:
        if latest_raw_frame is None:
            return None
        return latest_raw_frame.copy()


def build_event(event_id_value, event_type, image_path, source, person_result=None, timing=None):
    person_result = person_result or {}
    timing = timing or {}
    path = Path(image_path)
    status = state_manager.get_status()

    return {
        "event_id": event_id_value,
        "timestamp": event_logger.now_iso(),
        "event_type": event_type,
        "confidence": to_json_float(person_result.get("confidence")),
        "bounding_box": to_json_bbox(person_result.get("bbox")),
        "camera_id": config.CAMERA_ID,
        "image_filename": path.name,
        "image_path": str(path),
        "system_state": status["state_normalized"],
        "source": source,
        "source_mode": "webcam" if config.USE_WEBCAM else "video",
        "source_label": config.SOURCE_LABEL,
        "latency": timing,
    }


def queue_notification(event, title, started_at_perf):
    if not notifier.enabled:
        return {"enabled": False, "status": "skipped"}

    queued_at_perf = time.perf_counter()

    def send_in_background():
        if event["event_type"] == "person_detected":
            result = notifier.send_alert(event)
        else:
            result = notifier.send_snapshot_notification(event)

        notification_result = {
            "notification_id": event_id("ntf"),
            "parent_event_id": event["event_id"],
            "timestamp": event_logger.now_iso(),
            "title": title,
            "event_type": "notification_result",
            "camera_id": event["camera_id"],
            "system_state": event["system_state"],
            "status": result.get("status"),
            "enabled": result.get("enabled"),
            "telegram_elapsed_seconds": result.get("elapsed_seconds"),
            "event_to_notification_seconds": round(
                time.perf_counter() - started_at_perf,
                3,
            ),
            "background_worker_seconds": round(time.perf_counter() - queued_at_perf, 3),
            "error": result.get("error"),
        }
        event_logger.log_notification_result(notification_result)

    threading.Thread(target=send_in_background, daemon=True).start()
    return {"enabled": True, "status": "queued"}


def create_snapshot_event(
    event_type,
    source,
    frame=None,
    person_result=None,
    timing=None,
    started_at_perf=None,
):
    timing = dict(timing or {})
    started_at_perf = started_at_perf or time.perf_counter()
    timing.setdefault("event_started_at", event_logger.now_iso())

    frame = frame.copy() if frame is not None else current_frame_copy()
    if frame is None:
        return None

    image_id = event_id("evt")
    snapshot_started_at = time.perf_counter()
    image_path = save_snapshot(
        frame,
        config.EVENTS_DIR,
        image_id=image_id,
        event_type=event_type,
    )
    timing["snapshot_save_seconds"] = round(time.perf_counter() - snapshot_started_at, 3)
    event = build_event(image_id, event_type, image_path, source, person_result, timing)

    if event_type == "person_detected":
        event["notification"] = queue_notification(
            event,
            "Security alert",
            started_at_perf,
        )
    else:
        event["notification"] = queue_notification(
            event,
            "Manual snapshot",
            started_at_perf,
        )
    event["latency"]["end_to_end_local_seconds"] = round(
        time.perf_counter() - started_at_perf,
        3,
    )

    event_logger.log_event(event)
    cleanup_old_snapshots(config.EVENTS_DIR, config.RETENTION_DAYS)

    if mqtt_gateway is not None:
        mqtt_gateway.publish_event(event)

    return event


def publish_status():
    if mqtt_gateway is not None:
        mqtt_gateway.publish_status(state_manager.get_status())


def get_detection_status():
    with frame_lock:
        return dict(latest_detection_status)


def execute_command(command, source="dashboard"):
    cmd = str(command or "").lower().strip()
    if cmd == "arm":
        state_manager.arm()
        publish_status()
        return {"message": "Armed", "state": state_manager.get_status()}, 200

    if cmd == "disarm":
        state_manager.disarm()
        publish_status()
        return {"message": "Disarmed", "state": state_manager.get_status()}, 200

    if cmd == "snapshot":
        started_at_perf = time.perf_counter()
        event = create_snapshot_event(
            "manual_snapshot",
            source=source,
            timing={"command_received_at": event_logger.now_iso()},
            started_at_perf=started_at_perf,
        )
        if event is None:
            return {"message": "No frame available"}, 400
        return {"message": "Snapshot saved", "event": public_event(event)}, 200

    return {"message": "Invalid command"}, 400


def validate_voice_token(payload):
    expected = config.VOICE_WEBHOOK_TOKEN
    if not expected:
        return False

    supplied = (
        request.headers.get("X-Webhook-Token")
        or request.args.get("token")
        or payload.get("token")
        or ""
    )
    return hmac.compare_digest(str(supplied), expected)


def public_event(event):
    public = dict(event)
    filename = public.get("image_filename")
    image_path = public.get("image_path")
    image_available = bool(image_path and Path(image_path).exists())
    public["image_available"] = image_available

    if filename and image_available:
        if has_request_context():
            public["image_url"] = url_for("event_image", filename=filename)
        else:
            public["image_url"] = f"/events/{filename}"
    else:
        public["image_url"] = None
    return public


def process_loop():
    global latest_raw_frame, latest_display_frame, latest_detection_status

    cap = open_capture()

    while capture_running:
        try:
            if not cap.isOpened():
                time.sleep(1)
                cap.release()
                cap = open_capture()
                continue

            ret, frame = cap.read()
            if not ret:
                cap.release()
                time.sleep(0.5)
                cap = open_capture()
                continue

            frame_captured_at = event_logger.now_iso()
            frame_started_at_perf = time.perf_counter()
            state_manager.refresh()

            motion_started_at = time.perf_counter()
            motion_detected, motion_boxes = motion_detector.detect(frame)
            motion_seconds = round(time.perf_counter() - motion_started_at, 3)

            person_result = {
                "detected": False,
                "confidence": None,
                "bbox": None,
                "label": "person",
                "inference_seconds": None,
            }

            if motion_detected:
                inference_started_at = time.perf_counter()
                person_result = person_detector.detect_person(frame)
                person_result["inference_seconds"] = round(
                    time.perf_counter() - inference_started_at,
                    3,
                )

            if (
                motion_detected
                and person_result["detected"]
                and state_manager.can_trigger_detection()
            ):
                event = create_snapshot_event(
                    "person_detected",
                    source="camera",
                    frame=frame,
                    person_result=person_result,
                    timing={
                        "frame_captured_at": frame_captured_at,
                        "motion_detection_seconds": motion_seconds,
                        "person_inference_seconds": person_result.get("inference_seconds"),
                    },
                    started_at_perf=frame_started_at_perf,
                )
                if event is not None:
                    state_manager.trigger_alert(config.COOLDOWN_SECONDS)
                    publish_status()

            display = draw_boxes(
                frame,
                motion_boxes,
                person_result["bbox"],
                person_result["confidence"],
                state_manager.get_status()["state"],
            )

            with frame_lock:
                latest_raw_frame = frame.copy()
                latest_display_frame = display.copy()
                latest_detection_status = {
                    "motion_detected": motion_detected,
                    "motion_box_count": len(motion_boxes),
                    "person_detected": person_result["detected"],
                    "person_confidence": to_json_float(person_result["confidence"]),
                    "person_bbox": to_json_bbox(person_result["bbox"]),
                    "motion_detection_seconds": motion_seconds,
                    "person_inference_seconds": person_result.get("inference_seconds"),
                    "updated_at": event_logger.now_iso(),
                }

            time.sleep(0.03)

        except Exception as exc:
            print("[PROCESS] ERROR:", exc)
            time.sleep(1)

    cap.release()


def heartbeat_loop():
    while capture_running:
        if mqtt_gateway is not None:
            mqtt_gateway.publish_heartbeat(state_manager.get_status())
        time.sleep(config.HEARTBEAT_INTERVAL_SECONDS)


def generate_mjpeg():
    while True:
        with frame_lock:
            frame = latest_display_frame.copy() if latest_display_frame is not None else None

        if frame is None:
            time.sleep(0.05)
            continue

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), config.JPEG_QUALITY],
        )
        if not success:
            continue

        jpg_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n"
        )


@app.route("/login", methods=["GET", "POST"])
def login():
    if not config.DASHBOARD_AUTH_ENABLED:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (
            username == config.DASHBOARD_USERNAME
            and config.DASHBOARD_PASSWORD_HASH
            and check_password_hash(config.DASHBOARD_PASSWORD_HASH, password)
        ):
            login_user(DashboardUser(username))
            return redirect(request.args.get("next") or url_for("index"))

        error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route("/logout", methods=["POST"])
@require_dashboard_auth
def logout():
    if logout_user is not None and current_user is not None and current_user.is_authenticated:
        logout_user()
    return redirect(url_for("login"))


@app.route("/")
@require_dashboard_auth
def index():
    return render_template(
        "index.html",
        auth_enabled=config.DASHBOARD_AUTH_ENABLED,
        camera_id=config.CAMERA_ID,
        source_label=config.SOURCE_LABEL,
    )


@app.route("/video_feed")
@require_dashboard_auth
def video_feed():
    return Response(
        generate_mjpeg(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/events/<path:filename>")
@require_dashboard_auth
def event_image(filename):
    return send_from_directory(str(config.EVENTS_DIR), Path(filename).name)


@app.route("/snapshot", methods=["GET"])
@require_dashboard_auth
def snapshot():
    event = create_snapshot_event("manual_snapshot", source="dashboard")
    if event is None:
        return jsonify({"message": "No frame available"}), 400
    return send_file(event["image_path"], mimetype="image/jpeg")


@app.route("/api/status", methods=["GET"])
@require_dashboard_auth
def api_status():
    status = state_manager.get_status()
    status["source_mode"] = "webcam" if config.USE_WEBCAM else "video"
    status["source_label"] = config.SOURCE_LABEL
    status["detection"] = get_detection_status()
    return jsonify(status)


@app.route("/api/events", methods=["GET"])
@require_dashboard_auth
def api_events():
    events = [public_event(event) for event in event_logger.read_events(limit=20)]
    return jsonify(events)


@app.route("/api/command", methods=["POST"])
@require_dashboard_auth
def api_command():
    data = request.get_json(silent=True) or {}
    response, status_code = execute_command(data.get("command"), source="dashboard")
    return jsonify(response), status_code


@app.route("/api/voice-command", methods=["POST"])
def api_voice_command():
    data = request.get_json(silent=True) or {}
    if not validate_voice_token(data):
        return jsonify({"message": "Invalid voice webhook token"}), 401

    response, status_code = execute_command(data.get("command"), source="voice")
    return jsonify(response), status_code


def start_background_services():
    global mqtt_gateway

    mqtt_gateway = MqttGateway(config, on_command=lambda command, source="mqtt": execute_command(command, source))
    mqtt_gateway.start()
    publish_status()

    capture_thread = threading.Thread(target=process_loop, daemon=True)
    capture_thread.start()

    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()


if __name__ == "__main__":
    print("MODEL_PATH =", config.MODEL_PATH)
    print("PROTO_PATH =", config.PROTO_PATH)
    print("MODEL EXISTS =", os.path.exists(config.MODEL_PATH))
    print("PROTO EXISTS =", os.path.exists(config.PROTO_PATH))
    print("VIDEO_SOURCE =", config.VIDEO_SOURCE)
    print("VIDEO EXISTS =", os.path.exists(config.VIDEO_SOURCE))
    print("AUTH ENABLED =", config.DASHBOARD_AUTH_ENABLED)
    print("TELEGRAM ENABLED =", config.TELEGRAM_ENABLED)
    print("MQTT ENABLED =", config.MQTT_ENABLED)

    start_background_services()
    app.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        debug=config.DEBUG,
        use_reloader=False,
        threaded=True,
    )
