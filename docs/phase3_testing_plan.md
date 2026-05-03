# Phase 3 Testing and Documentation Plan

This document defines the official Phase 3 testing plan for the smart home security prototype. Phase 2 proved that the implementation works end to end. Phase 3 expands that evidence into a realistic evaluation that can be used in the thesis testing, results, limitations, and future work chapters.

## Phase 3 Objectives

1. Test the prototype in a realistic home-like setup.
2. Measure detection accuracy, alert latency, dashboard responsiveness, stability, and usability.
3. Analyze limitations, security, and privacy considerations.
4. Finalize the source code, testing evidence, documentation, and thesis recommendations.

## Test Environment Record

Before running official trials, record the environment in the thesis report.

| Field | Value to record |
| --- | --- |
| Test date | Date and approximate time of testing |
| Room type | Bedroom, living room, hallway, or other home-like area |
| Camera | Webcam model or "USB webcam" if model is unknown |
| Camera position | Height, distance to entry path, and approximate angle |
| Lighting | Daylight, artificial light, low light, or mixed |
| Computer | OS, Python version, CPU/RAM if known |
| Network | Wi-Fi or wired, approximate stability |
| App configuration | `USE_WEBCAM`, `WEBCAM_INDEX`, `PERSON_CONFIDENCE_THRESHOLD`, `COOLDOWN_SECONDS`, `TELEGRAM_ENABLED`, `DASHBOARD_AUTH_ENABLED` |

## Fixed Configuration for Official Runs

Use one baseline configuration for most official trials.

```text
USE_WEBCAM=true
WEBCAM_INDEX=0
PERSON_CONFIDENCE_THRESHOLD=0.60
COOLDOWN_SECONDS=30
DASHBOARD_AUTH_ENABLED=true
TELEGRAM_ENABLED=true
```

If a setting is changed, record it in the trial notes.

## Detection Accuracy Test Matrix

Use `data/phase3_trials_template.csv` to record official results. The recommended Phase 3 matrix contains 24 detection trials.

| Scenario | Trial IDs | Expected person | Purpose |
| --- | --- | --- | --- |
| `daylight_person_crossing` | D01-D05 | true | Normal person-entry condition |
| `low_light_person_crossing` | L01-L05 | true | Reduced lighting robustness |
| `side_angle_person_crossing` | A01-A04 | true | Camera-angle robustness |
| `partial_body_or_fast_entry` | P01-P03 | true | Stress test for partial/fast movement |
| `no_person_static_scene` | N01-N03 | false | True-negative baseline |
| `no_person_object_motion` | O01-O04 | false | False-positive stress test |

Minimum acceptable run if time is tight: 12 trials, including at least 6 person trials and 6 no-person trials.

## Trial Procedure

For each detection trial:

1. Start the Flask app and open the dashboard.
2. Confirm the live feed updates correctly.
3. Confirm Telegram is ready if alert latency is being measured.
4. Set the system to `ARMED`.
5. Perform the scenario naturally.
6. Wait for either an alert or the agreed observation window, usually 20-30 seconds.
7. Record `system_alerted`, event ID, confidence, latency fields, and notes in the CSV.
8. Disarm or wait for cooldown before the next trial.

Use these rules:

- A person trial is successful when one person alert is generated during the scenario.
- A no-person trial is successful when no person alert is generated.
- Manual snapshot tests must not be counted in detection accuracy metrics.
- Cooldown prevents duplicate alerts; it should not be counted as a detection failure if the first alert was correct.

## Latency Evaluation

Measure three latency values when available:

| Latency field | Source | Meaning |
| --- | --- | --- |
| `end_to_end_local_seconds` | `logs/events.jsonl` or exported trial CSV | Local processing time for the event |
| `event_to_notification_seconds` | `logs/notifications.jsonl` | Time from event creation to Telegram result log |
| `telegram_elapsed_seconds` | `logs/notifications.jsonl` | Telegram API upload time |

Run:

```powershell
python scripts/evaluate_trials.py data/phase3_trials_template.csv --output logs/phase3_trials_summary.json
python scripts/generate_phase3_report.py --trials data/phase3_trials_template.csv --summary logs/phase3_trials_summary.json --status-monitor logs/status_monitor.csv --output docs/phase3_results_report.md
```

## Stability Test

Run a short stability test if time is limited, and a longer test if the schedule allows.

| Test | Duration | Evidence |
| --- | ---: | --- |
| Short stability check | 30-60 minutes | `logs/status_monitor.csv` |
| Stronger Phase 3 test | 4-8 hours | `logs/status_monitor.csv` plus notes |
| Ideal extended test | 24 hours | Long uptime evidence and failure notes |

Command:

```powershell
$env:DASHBOARD_PASSWORD="your-dashboard-password"
python scripts/monitor_status.py --username admin --password-env DASHBOARD_PASSWORD --duration-seconds 3600 --interval-seconds 5 --output logs/status_monitor.csv
```

Record whether the dashboard stream remained responsive, whether the status API stayed reachable, and whether any errors occurred.

## Usability Test

Use `data/phase3_usability_checklist.csv` to record usability observations. The minimum usability evaluation can be done by the project author during demo rehearsal, but it is stronger if one additional person tries the dashboard.

Recommended tasks:

1. Log in to the dashboard.
2. Confirm live stream status.
3. Arm the system.
4. Trigger a person-detection scenario.
5. Find the latest event snapshot.
6. Request a manual snapshot.
7. Disarm the system.

Record task success, completion time, difficulty rating, and notes.

## Security and Privacy Review

The Phase 3 report should discuss:

- `.env` stores Telegram token, chat ID, dashboard password hash, Flask secret key, and webhook token.
- `.env`, `events/`, `logs/`, virtual environment folders, and cache files are excluded from GitHub.
- Dashboard authentication protects the UI when enabled.
- Voice webhook requires a token.
- Telegram snapshots leave the local machine, so only event snapshots and manual snapshots should be sent.
- A real deployment would require HTTPS, firewall rules, production WSGI hosting, secure backup policy, and camera privacy notices.

## Thesis Output

The final Phase 3 thesis section should contain:

1. Test setup table.
2. Scenario matrix.
3. Confusion matrix and metrics table.
4. Latency summary table.
5. Stability summary.
6. Usability observations.
7. Limitations and security/privacy discussion.
8. Future work recommendations.
