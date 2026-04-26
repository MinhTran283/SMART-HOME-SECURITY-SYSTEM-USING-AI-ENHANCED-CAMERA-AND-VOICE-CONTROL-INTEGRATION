import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if not value:
        return default
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


_load_env_file(BASE_DIR / ".env")

VIDEOS_DIR = _path("VIDEOS_DIR", BASE_DIR / "videos")
EVENTS_DIR = _path("EVENTS_DIR", BASE_DIR / "events")
LOGS_DIR = _path("LOGS_DIR", BASE_DIR / "logs")
MODEL_DIR = _path("MODEL_DIR", BASE_DIR / "models")

CAMERA_ID = os.getenv("CAMERA_ID", "living_room")
VIDEO_SOURCE = str(_path("VIDEO_SOURCE", VIDEOS_DIR / "test_video.mp4"))
USE_WEBCAM = _bool("USE_WEBCAM", False)
WEBCAM_INDEX = _int("WEBCAM_INDEX", 0)
SOURCE_LABEL = f"Webcam {WEBCAM_INDEX}" if USE_WEBCAM else f"Video file: {Path(VIDEO_SOURCE).name}"

FRAME_WIDTH = _int("FRAME_WIDTH", 640)
FRAME_HEIGHT = _int("FRAME_HEIGHT", 480)
JPEG_QUALITY = _int("JPEG_QUALITY", 80)

MOTION_MIN_AREA = _int("MOTION_MIN_AREA", 1500)
MOTION_THRESHOLD = _int("MOTION_THRESHOLD", 25)
BLUR_SIZE_VALUE = _int("BLUR_SIZE_VALUE", 21)
BLUR_SIZE = (BLUR_SIZE_VALUE, BLUR_SIZE_VALUE)

PERSON_CONFIDENCE_THRESHOLD = _float("PERSON_CONFIDENCE_THRESHOLD", 0.60)

MODEL_PATH = _path("MODEL_PATH", MODEL_DIR / "MobileNetSSD_deploy.caffemodel")
PROTO_PATH = _path("PROTO_PATH", MODEL_DIR / "MobileNetSSD_deploy.prototxt")

COOLDOWN_SECONDS = _int("COOLDOWN_SECONDS", 10)
RETENTION_DAYS = _int("RETENTION_DAYS", 7)

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = _int("APP_PORT", 5000)
DEBUG = _bool("DEBUG", False)
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-before-demo")

DASHBOARD_AUTH_ENABLED = _bool("DASHBOARD_AUTH_ENABLED", False)
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD_HASH = os.getenv("DASHBOARD_PASSWORD_HASH", "")

VOICE_WEBHOOK_TOKEN = os.getenv("VOICE_WEBHOOK_TOKEN", "")

TELEGRAM_ENABLED = _bool("TELEGRAM_ENABLED", False)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_TIMEOUT_SECONDS = _int("TELEGRAM_TIMEOUT_SECONDS", 10)

MQTT_ENABLED = _bool("MQTT_ENABLED", False)
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = _int("MQTT_PORT", 1883)
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TLS = _bool("MQTT_TLS", False)
MQTT_CAMERA_ID = os.getenv("MQTT_CAMERA_ID", "camera1")
MQTT_BASE_TOPIC = os.getenv("MQTT_BASE_TOPIC", f"home/security/{MQTT_CAMERA_ID}")
MQTT_EVENT_TOPIC = os.getenv("MQTT_EVENT_TOPIC", f"{MQTT_BASE_TOPIC}/event")
MQTT_STATUS_TOPIC = os.getenv("MQTT_STATUS_TOPIC", f"{MQTT_BASE_TOPIC}/status")
MQTT_COMMAND_TOPIC = os.getenv("MQTT_COMMAND_TOPIC", f"{MQTT_BASE_TOPIC}/cmd")
MQTT_HEARTBEAT_TOPIC = os.getenv("MQTT_HEARTBEAT_TOPIC", f"{MQTT_BASE_TOPIC}/heartbeat")
HEARTBEAT_INTERVAL_SECONDS = _int("HEARTBEAT_INTERVAL_SECONDS", 60)

for directory in (EVENTS_DIR, LOGS_DIR, MODEL_DIR, VIDEOS_DIR):
    directory.mkdir(parents=True, exist_ok=True)
