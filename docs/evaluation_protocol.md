# Phase 2 Evaluation Protocol

This protocol defines a repeatable evaluation for the smart home security prototype. Use it to collect the evidence needed for the thesis evaluation chapter: detection accuracy, false alerts, local processing latency, and Telegram delivery latency.

## Goal

Evaluate whether the prototype can detect a real person from a live webcam, avoid unnecessary alerts when no person is present, and deliver a notification within an acceptable time for a home security scenario.

## Fixed Test Configuration

Use the same configuration for all official trials unless a scenario explicitly changes one variable.

```text
USE_WEBCAM=true
WEBCAM_INDEX=0
PERSON_CONFIDENCE_THRESHOLD=0.60
COOLDOWN_SECONDS=30
DASHBOARD_AUTH_ENABLED=true
TELEGRAM_ENABLED=true
```

Before testing:

1. Start the Flask application.
2. Log in to the dashboard.
3. Confirm the live feed is updating.
4. Set the system to `ARMED`.
5. Confirm the Telegram group can receive a manual test notification.
6. Keep camera position, room layout, and distance to the person consistent.

## Trial Recording

Record each trial in `data/evaluation_trials_template.csv`. The important fields are:

- `trial_id`: Unique trial code, for example `D01`.
- `scenario`: Test scenario name.
- `lighting_condition`: Daylight, low light, artificial light, or another short label.
- `expected_person`: `true` if a person should be detected.
- `system_alerted`: `true` if the system created a person alert.
- `event_id`: Event ID from the dashboard or `logs/events.jsonl`, if available.
- `timestamp`, `source_mode`, `source_label`: Event timing and input source context.
- `confidence`: Detector confidence from the event or dashboard.
- `end_to_end_local_seconds`: Local processing latency from the event log.
- `event_to_notification_seconds`: Time from event creation to Telegram result log.
- `telegram_elapsed_seconds`: Telegram API upload time.
- `notes`: Any unusual condition, such as partial body view, fast walking, shadow, or camera shake.

To prefill rows from existing logs:

```powershell
python scripts/export_event_trials.py --output data/evaluation_trials_from_logs.csv
```

Then manually fill `expected_person`, `scenario`, and `lighting_condition` before calculating metrics.

## Recommended Scenarios

Run at least 20 official trials if time allows.

| Scenario | Trials | Expected result | Purpose |
| --- | ---: | --- | --- |
| `daylight_person_crossing` | 5 | Person alert | Normal operating condition |
| `low_light_person_crossing` | 5 | Person alert | Robustness under harder lighting |
| `person_stationary_after_entry` | 3 | At least one alert during entry | Shows motion-gated detection behavior |
| `no_person_static_scene` | 3 | No alert | True negative baseline |
| `no_person_object_motion` | 4 | No person alert | False positive stress test |

If the project schedule is tight, use a minimum set of 10 trials: 4 daylight person, 3 low light person, and 3 no-person motion/static trials.

## Outcome Definitions

The evaluation script infers the outcome from `expected_person` and `system_alerted`.

| Expected person | System alerted | Outcome |
| --- | --- | --- |
| true | true | True positive |
| false | true | False positive |
| true | false | False negative |
| false | false | True negative |

Metrics:

```text
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
F1 score = 2 * Precision * Recall / (Precision + Recall)
Accuracy = (TP + TN) / (TP + FP + FN + TN)
Specificity = TN / (TN + FP)
```

## Running the Metric Script

After filling the CSV:

```powershell
python scripts/evaluate_trials.py data/evaluation_trials_template.csv --output logs/evaluation_trials_summary.json
```

The script prints and saves:

- Overall TP, FP, FN, TN counts.
- Precision, recall, F1 score, accuracy, and specificity.
- Per-scenario metrics.
- Average latency values when latency columns are filled.

## Uptime and API Response Monitoring

For stability evidence, monitor the status API while the prototype is running.

When dashboard authentication is enabled, set the password in a temporary environment variable:

```powershell
$env:DASHBOARD_PASSWORD="your-dashboard-password"
python scripts/monitor_status.py --username admin --password-env DASHBOARD_PASSWORD --duration-seconds 3600 --interval-seconds 5 --output logs/status_monitor.csv
```

For a longer stability test, increase `--duration-seconds`. For example, a 24-hour test uses `86400` seconds.

The monitor writes:

- HTTP status code.
- API response time in milliseconds.
- System state.
- Camera source mode.
- Motion/person diagnostic values.
- Error message, if a request fails.

## Thesis Reporting Notes

For the final thesis, include:

1. A table describing the test environment: webcam model if known, camera position, room lighting, approximate distance, and laptop/PC specification.
2. The official trial table or a summarized version of it.
3. The generated JSON metrics converted into a readable results table.
4. A short discussion of false positives and false negatives.
5. A limitation statement: the prototype uses a local webcam and a lightweight MobileNet SSD detector, so performance may differ with other cameras, angles, and lighting conditions.

Do not cite `data/evaluation_trials_sample.csv` as an official result. It is only included to demonstrate the CSV format and validate the script.
