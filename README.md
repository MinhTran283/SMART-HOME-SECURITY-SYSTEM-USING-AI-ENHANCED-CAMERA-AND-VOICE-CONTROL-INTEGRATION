# Smart Home Security Prototype

Phase 2 prototype for a local-first smart home security system using motion detection, AI-based person detection, a Flask dashboard, optional Telegram alerts, optional MQTT publishing, and a token-protected voice webhook.

Tested on Windows with Python 3.13.7.

## Features

- Local MJPEG live stream through Flask.
- Motion detection before AI inference to reduce CPU load.
- MobileNet SSD person detection through OpenCV DNN.
- Finite state machine: `DISARMED`, `ARMED`, `COOLDOWN`.
- Unified JSONL event schema for automatic detections and manual snapshots.
- Optional Telegram photo notification.
- Optional MQTT event, status, command, and heartbeat topics.
- Optional Flask-Login dashboard authentication.
- Local snapshot retention cleanup.

## Project Documents

- `docs/phase2_implementation_summary.md`: implementation summary for the thesis write-up.
- `docs/evaluation_protocol.md`: Phase 2 quick-validation protocol and metric definitions.
- `docs/phase3_testing_plan.md`: official Phase 3 testing and documentation plan.
- `docs/phase3_deliverables_checklist.md`: final prototype, testing, thesis, and safety checklist.
- `docs/quick_evaluation_results.md`: completed Phase 2 quick-validation result summary.
- `docs/demo_checklist.md`: practical checklist for demo recording and presentation.

## Setup

1. Create a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create local configuration.

```powershell
Copy-Item .env.example .env
```

4. Place the MobileNet SSD model files in `models/`.

```text
models/MobileNetSSD_deploy.caffemodel
models/MobileNetSSD_deploy.prototxt
```

5. Run the prototype.

```powershell
python app.py
```

Open `http://127.0.0.1:5000`.

## Camera Mode

The prototype can run from either a saved video file or a live webcam.

Video mode:

```text
USE_WEBCAM=false
VIDEO_SOURCE=videos/test_video.mp4
```

Webcam mode:

```text
USE_WEBCAM=true
WEBCAM_INDEX=0
```

To discover the correct camera index:

```powershell
python scripts/list_cameras.py --save-snapshots
```

For the thesis, webcam mode represents the real deployment scenario, while video mode remains useful for repeatable evaluation using the same input footage.

Current local test camera:

```text
USE_WEBCAM=true
WEBCAM_INDEX=0
```

## Dashboard Authentication

Authentication is disabled by default for fast local testing. For a thesis demo, enable it in `.env`.

```text
DASHBOARD_AUTH_ENABLED=true
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD_HASH=<generated-hash>
```

Generate a password hash:

```powershell
python scripts/generate_password_hash.py
```

Do not store the plain dashboard password in source control. Only the hash belongs in `.env`.

## Voice Webhook

The endpoint for Google Assistant or IFTTT-style commands is:

```text
POST /api/voice-command?token=<VOICE_WEBHOOK_TOKEN>
Content-Type: application/json

{"command": "arm"}
```

Supported commands:

- `arm`
- `disarm`
- `snapshot`

The token can also be sent in the `X-Webhook-Token` header.

## Telegram Alerts

Enable Telegram in `.env`:

```text
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_CHAT_ID=<chat-id>
```

Automatic person detections and manual snapshots will send the saved photo and event metadata.

To test Telegram with the latest saved event image:

```powershell
python scripts/test_telegram.py
```

The event log records local event latency, and `logs/notifications.jsonl` records Telegram delivery latency when Telegram is enabled.
Runtime notifications are dispatched in a background thread so the live webcam stream does not freeze while Telegram is uploading a photo. Delivery results are appended to `logs/notifications.jsonl`.

For live webcam demos, `COOLDOWN_SECONDS=30` is recommended to avoid repeated Telegram alerts while the same person remains in view.

Security reminder: keep `.env` private and rotate the Telegram bot token before the final submission if the token appeared in screenshots, browser history, or chat logs during testing.

## MQTT Topics

Enable MQTT in `.env`:

```text
MQTT_ENABLED=true
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_BASE_TOPIC=home/security/camera1
```

Default topics:

- `home/security/camera1/event`
- `home/security/camera1/status`
- `home/security/camera1/cmd`
- `home/security/camera1/heartbeat`

MQTT commands may be plain text (`arm`) or JSON:

```json
{"command": "snapshot"}
```

## Event Schema

Events are appended to `logs/events.jsonl`.

```json
{
  "event_id": "evt_20260426_143022_123456",
  "timestamp": "2026-04-26T11:30:22Z",
  "event_type": "person_detected",
  "confidence": 0.87,
  "bounding_box": [120, 80, 300, 450],
  "camera_id": "living_room",
  "image_filename": "evt_20260426_143022_123456_person_detected.jpg",
  "image_path": "events/evt_20260426_143022_123456_person_detected.jpg",
  "system_state": "armed",
  "source": "camera",
  "notification": {"enabled": true, "status": "sent"}
}
```

## Evaluation Notes

Use `docs/evaluation_protocol.md` for Phase 2 quick validation. Use `docs/phase3_testing_plan.md` for the broader Phase 3 testing and documentation process.

For thesis measurement, record the following fields during tests:

- Precision, recall, and F1 score from manual video annotation.
- End-to-end latency from frame capture to Telegram receipt.
- Command response time for dashboard and voice webhook.
- Uptime and memory usage during a 48-hour run.
- False positive behavior under low light, curtain movement, and pet movement scenarios.

For live webcam trials, fill:

```text
data/evaluation_trials_template.csv
```

For Phase 3 official trials, use:

```text
data/phase3_trials_template.csv
```

The current Phase 3 detection trial results are recorded in:

```text
data/phase3_trials_results.csv
```

You can prefill trial rows from existing event logs:

```powershell
python scripts/export_event_trials.py --output data/evaluation_trials_from_logs.csv
```

Then calculate metrics:

```powershell
python scripts/evaluate_trials.py data/evaluation_trials_template.csv --output logs/evaluation_trials_summary.json
```

For Phase 3:

```powershell
python scripts/evaluate_trials.py data/phase3_trials_template.csv --output logs/phase3_trials_summary.json
```

or, after filling the completed results file:

```powershell
python scripts/evaluate_trials.py data/phase3_trials_results.csv --output logs/phase3_trials_summary.json
```

The CSV-based script reports TP, FP, FN, TN, precision, recall, F1 score, accuracy, specificity, per-scenario results, and latency summaries when the latency fields are filled.

To collect uptime and API response-time evidence:

```powershell
$env:DASHBOARD_PASSWORD="your-dashboard-password"
python scripts/monitor_status.py --username admin --password-env DASHBOARD_PASSWORD --duration-seconds 3600 --interval-seconds 5 --output logs/status_monitor.csv
```

For a quick manual count calculation, use:

```powershell
python scripts/evaluate_results.py --tp 8 --fp 2 --fn 1 --output logs/evaluation_summary.json
```

`scripts/evaluate_results.py` reports precision, recall, F1 score, local event latency from `logs/events.jsonl`, and Telegram delivery latency from `logs/notifications.jsonl`.

To generate a Markdown Phase 3 results report after filling the trial CSV:

```powershell
python scripts/generate_phase3_report.py --trials data/phase3_trials_template.csv --summary logs/phase3_trials_summary.json --status-monitor logs/status_monitor.csv --output docs/phase3_results_report.md
```

`docs/phase3_results_report.md` is generated evidence. Review it before including it in the thesis, especially if it references runtime logs or private test notes.
