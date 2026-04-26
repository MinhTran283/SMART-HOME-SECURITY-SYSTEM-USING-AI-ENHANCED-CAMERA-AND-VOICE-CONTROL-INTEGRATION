# Supervisor Demo Flow

Use this as a short speaking guide during the Phase 2 supervisor demo.

## 1. Opening

Suggested explanation:

```text
In Phase 2, I implemented a working prototype of the smart home security system from Phase 1. The prototype uses a webcam as the live camera source, performs local motion detection, runs person detection only when motion is present, stores event snapshots, displays a web dashboard, and sends Telegram alerts when the system is armed.
```

Key point:

```text
The current prototype focuses on functional validation, not large-scale benchmarking.
```

## 2. Show Dashboard

Show:

- Live webcam feed.
- Current source label: webcam.
- System state.
- Arm/disarm controls.
- Event list.
- Detection diagnostics: motion, person, confidence.

Suggested explanation:

```text
The dashboard lets the user monitor the camera, arm or disarm the system, and review saved events. The live stream continues even when the system is disarmed, but automatic alerts are only generated when the system is armed.
```

## 3. Disarmed Behavior

Action:

1. Click `Disarm`.
2. Move in front of the camera.
3. Show that the camera feed continues.

Suggested explanation:

```text
In DISARMED mode, the system still shows the live feed, but it does not create automatic security alerts. This prevents unwanted notifications when the user is at home.
```

## 4. Armed Person Detection

Action:

1. Click `Arm`.
2. Move out of the frame briefly.
3. Walk into the camera frame.
4. Wait for detection.
5. Show the event list and Telegram alert.

Suggested explanation:

```text
When the system is armed, motion detection acts as a trigger. If motion is detected, the AI person detector runs. If a person is detected above the confidence threshold, the system saves a snapshot and sends a Telegram notification.
```

Important detail:

```text
Telegram sending runs in a background thread, so the webcam stream should not freeze while the image is being uploaded.
```

## 5. No-Person Scenario

Action:

1. Keep the system armed.
2. Keep the frame empty, or move a small object without entering the frame.
3. Show that no person alert is created.

Suggested explanation:

```text
The system separates motion detection from person detection. Motion alone is not enough to create a security alert. The alert is created only when the person detector confirms a person.
```

## 6. Manual Snapshot

Action:

1. Click manual snapshot.
2. Show the new event.
3. Show Telegram delivery if it appears.

Suggested explanation:

```text
Manual snapshot is included as an operator function. It allows the user to capture evidence even when they do not want to wait for automatic detection.
```

## 7. Quick Evaluation Result

Show:

- `docs/quick_evaluation_results.md`
- `logs/evaluation_quick_trials_summary.json`

Suggested explanation:

```text
I also ran a small functional validation with five detection trials: three person-entry cases and two no-person cases. In this limited validation, the system correctly handled all five detection trials. Average Telegram delivery result time was about 0.64 seconds. Because the sample size is small, I treat this as quick functional validation rather than a full statistical benchmark.
```

## 8. Architecture Summary

Show:

- `docs/phase2_implementation_summary.md`

Suggested explanation:

```text
The architecture is local-first. Frames are processed locally with OpenCV. Motion detection reduces unnecessary AI inference, person detection confirms whether the motion is security-relevant, and only confirmed events are logged and sent as notifications.
```

## 9. Limitations

Mention clearly:

- The current detector is lightweight, so accuracy may drop in difficult lighting, unusual angles, or partial body views.
- The validation set is small.
- Telegram latency depends on internet connection.
- The Flask development server is for prototype demonstration, not public deployment.
- Long-term stability testing is future work.

Suggested explanation:

```text
The prototype proves the main workflow, but future work should include larger evaluation, longer uptime testing, stronger models, and production deployment hardening.
```

## 10. Closing

Suggested closing:

```text
The Phase 2 implementation demonstrates the core workflow of the proposed smart home security system: live monitoring, local motion and person detection, event evidence capture, dashboard control, and Telegram notification. The next improvement would be broader testing and production hardening.
```

## Quick Recovery During Demo

| Problem | What to do |
| --- | --- |
| Dashboard not loading | Restart Flask with `python app.py` |
| Login fails | Check username/password and `.env` dashboard auth values |
| Webcam frozen | Refresh page; if still frozen, restart Flask and make sure no other app is using webcam |
| No detection | Improve lighting, stand fully in frame, wait for cooldown to finish |
| Too many alerts | Disarm, wait, confirm `COOLDOWN_SECONDS=30` |
| Telegram not received | Check internet, group permission, token, and chat ID |
| Token visible on screen | Do not show `.env` or Telegram API pages during demo |
