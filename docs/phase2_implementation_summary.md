# Phase 2 Implementation Summary

This document summarizes the implemented Phase 2 prototype for the smart home security thesis. It is written as source material for the implementation and evaluation chapters.

## Prototype Objective

The Phase 2 prototype implements a local-first smart home security camera system. The system uses a webcam or video file as input, detects motion, runs AI-based person detection only when motion is present, stores evidence snapshots, displays a live dashboard, and sends Telegram notifications when a person is detected while the system is armed.

## Implemented Scope

- Live webcam mode and repeatable saved-video mode.
- Flask dashboard with MJPEG camera stream.
- Arm, disarm, and manual snapshot controls.
- Motion-gated AI person detection.
- MobileNet SSD person detector through OpenCV DNN.
- Event logging in JSONL format.
- Snapshot storage with retention cleanup.
- Telegram photo alerts with background delivery.
- Dashboard authentication using Flask-Login.
- Optional MQTT event/status/command integration.
- Token-protected voice webhook endpoint.
- CSV-based evaluation workflow for thesis metrics.

## High-Level Architecture

```text
Camera or video source
        |
        v
Frame capture loop
        |
        v
Motion detection
        |
        +---- no motion ----> live stream only
        |
        v
Person detection
        |
        +---- no person ----> live stream with diagnostics
        |
        v
Event creation
        |
        +---- save snapshot
        +---- append logs/events.jsonl
        +---- publish MQTT event if enabled
        +---- queue Telegram notification if enabled
        |
        v
Dashboard and evaluation logs
```

## Main Components

| File | Responsibility |
| --- | --- |
| `app.py` | Flask routes, camera loop, state transitions, event creation, notification queue |
| `config.py` | Environment-based configuration loading |
| `motion.py` | Frame differencing and contour-based motion detection |
| `detector.py` | MobileNet SSD person detection through OpenCV DNN |
| `state_manager.py` | `DISARMED`, `ARMED`, and `COOLDOWN` state management |
| `event_logger.py` | Thread-safe JSONL event and notification logging |
| `notifier.py` | Telegram photo notification delivery |
| `mqtt_client.py` | Optional MQTT publishing and command subscription |
| `utils.py` | Snapshot naming, drawing, timestamp, and cleanup helpers |
| `templates/index.html` | Main dashboard UI |
| `templates/login.html` | Dashboard login UI |
| `scripts/evaluate_trials.py` | CSV-based official trial evaluation |
| `scripts/export_event_trials.py` | Prefills evaluation CSV rows from runtime event logs |
| `scripts/monitor_status.py` | Records uptime and API response-time evidence |
| `docs/evaluation_protocol.md` | Official thesis evaluation procedure |

## Runtime States

### DISARMED

The live feed remains active, but automatic person alerts are disabled. The user can still take a manual snapshot from the dashboard.

### ARMED

The system monitors the camera feed. When motion is detected, the person detector is executed. If the detector finds a person above the configured confidence threshold, an event is saved and a Telegram notification is queued.

### COOLDOWN

After an alert, the system temporarily suppresses repeated alerts for the same continuous presence. The current recommended value is:

```text
COOLDOWN_SECONDS=30
```

This reduces duplicate Telegram messages during live demonstrations.

## Security Measures

- Sensitive configuration is stored in `.env`, not committed source files.
- Dashboard authentication can be enabled with `DASHBOARD_AUTH_ENABLED=true`.
- Dashboard password is stored as a hash, not plain text.
- Voice webhook commands require a token.
- Telegram token and chat ID are environment variables.
- `.gitignore` excludes `.env`, virtual environments, cache files, and runtime artifacts.

Important operational note: the Telegram bot token should be rotated before final submission if it has appeared in screenshots, browser history, chat logs, or demo recordings.

## Evaluation Support

The prototype records:

- Event timestamp.
- Event type.
- Detection confidence.
- Bounding box.
- Source mode and source label.
- Local processing latency.
- Telegram delivery result and elapsed time.

Official trials should be recorded in:

```text
data/evaluation_trials_template.csv
```

Metrics can be generated with:

```powershell
python scripts/evaluate_trials.py data/evaluation_trials_template.csv --output logs/evaluation_trials_summary.json
```

The script reports TP, FP, FN, TN, precision, recall, F1 score, accuracy, specificity, per-scenario metrics, and latency summaries.

Existing detection logs can be exported into the trial CSV format:

```powershell
python scripts/export_event_trials.py --output data/evaluation_trials_from_logs.csv
```

Status API uptime and response-time evidence can be recorded with:

```powershell
$env:DASHBOARD_PASSWORD="your-dashboard-password"
python scripts/monitor_status.py --username admin --password-env DASHBOARD_PASSWORD --duration-seconds 3600 --interval-seconds 5 --output logs/status_monitor.csv
```

## Current Limitations

- The AI detector is lightweight and suitable for local prototype use, but it can be less accurate in low light, unusual camera angles, partial body views, and cluttered scenes.
- Motion-gated detection reduces CPU usage but may miss a stationary person if the person enters before the system is armed or if there is very little movement.
- Telegram notification latency depends on internet connectivity and Telegram API response time.
- The Flask development server is suitable for local prototype demonstration, not direct public internet exposure.
- Long-term reliability still requires an extended uptime test.

## Suggested Future Improvements

- Add a stronger person detector if hardware resources allow.
- Add local event search and filtering in the dashboard.
- Add encrypted storage for sensitive event snapshots.
- Add role-based dashboard accounts.
- Package the system as a Windows startup service.
- Add a longer 24-hour or 48-hour stability test with CPU and memory monitoring.
