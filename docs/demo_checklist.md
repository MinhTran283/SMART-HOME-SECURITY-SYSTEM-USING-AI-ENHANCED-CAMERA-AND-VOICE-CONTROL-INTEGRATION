# Phase 2 Demo Checklist

Use this checklist before recording a demo video or presenting the prototype.

## Before Starting

1. Connect the webcam.
2. Confirm the camera is physically stable.
3. Confirm the room lighting matches the planned test scenario.
4. Make sure private objects are not visible in the camera view.
5. Confirm the Telegram bot token has not been exposed in the recording area.
6. Open the project folder:

```powershell
cd "C:\Users\minha\OneDrive\Desktop\Hox pai\Thesis\security_prototype"
```

## Start the App

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Pre-Demo Verification

1. Log in to the dashboard.
2. Confirm the live feed is moving.
3. Confirm the source label shows webcam mode.
4. Confirm the system starts in `DISARMED` or disarm it manually.
5. Confirm manual snapshot works.
6. Confirm the latest event appears in the event list.

## Telegram Verification

Use this only when you are ready to send a test message to the group.

```powershell
python scripts/test_telegram.py
```

Expected result:

- Telegram receives a photo.
- The terminal reports a successful send.
- `logs/notifications.jsonl` receives a delivery record.

## Main Demo Flow

1. Show the live feed in `DISARMED`.
2. Move in front of the camera and confirm no automatic Telegram alert is generated.
3. Click `Arm`.
4. Leave the frame briefly.
5. Re-enter the frame naturally.
6. Confirm motion is detected.
7. Confirm person detection confidence appears.
8. Confirm a snapshot appears in the dashboard event list.
9. Confirm Telegram receives the alert.
10. Wait for cooldown or click `Disarm`.
11. Explain why cooldown prevents repeated messages.

## Evidence to Save

After the demo, preserve:

- `logs/events.jsonl`
- `logs/notifications.jsonl`
- `logs/status_monitor.csv`, if uptime monitoring was enabled
- `logs/evaluation_trials_summary.json`, if official trials were run
- Selected event screenshots if they are suitable for the thesis

To prefill an evaluation CSV from recent event logs:

```powershell
python scripts/export_event_trials.py --output data/evaluation_trials_from_logs.csv
```

To record status API uptime during a demo:

```powershell
$env:DASHBOARD_PASSWORD="your-dashboard-password"
python scripts/monitor_status.py --username admin --password-env DASHBOARD_PASSWORD --duration-seconds 1800 --interval-seconds 5 --output logs/status_monitor.csv
```

## If Something Fails

| Problem | Quick check |
| --- | --- |
| Live feed is frozen | Refresh the dashboard and check whether another app is using the webcam |
| No person detection | Improve lighting and stand fully inside the frame |
| Too many alerts | Confirm `COOLDOWN_SECONDS=30` |
| Telegram does not send | Check internet connection, bot token, chat ID, and group permission |
| Dashboard asks for login repeatedly | Check `SECRET_KEY` in `.env` and restart the app |

## After Recording

1. Disarm the system.
2. Stop the Flask server.
3. Review snapshots before including them in the thesis.
4. Rotate the Telegram bot token if it appeared anywhere in the recording.
