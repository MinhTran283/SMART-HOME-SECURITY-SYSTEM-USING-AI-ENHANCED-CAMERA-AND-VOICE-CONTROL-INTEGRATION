# Phase 3 Results Report

This report is generated from the Phase 3 trial CSV and optional status-monitor evidence.

## Source Files

- Trial CSV: `data/phase3_trials_results.csv`
- Metric source: `scripts/evaluate_trials.py`

## Test Scope

The completed detection run contains 19 evaluated live-camera trials. Manual snapshot trials are not included in the detection metrics.

The test evidence focuses on detection correctness and alert behavior. Per-event latency values are reported only when the trial CSV contains exported event and notification latency fields.
No Phase 3 latency values were provided in the trial CSV for this generated report.

## Detection Metrics

| Metric | Value |
| --- | ---: |
| True positives | 13 |
| False positives | 0 |
| False negatives | 0 |
| True negatives | 6 |
| Evaluated trials | 19 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 score | 1.000 |
| Accuracy | 1.000 |
| Specificity | 1.000 |

## Latency Summary

| Latency field | Count | Average | Median | Minimum | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| `end_to_end_local_seconds` | 0 | N/A | N/A | N/A | N/A |
| `event_to_notification_seconds` | 0 | N/A | N/A | N/A | N/A |
| `telegram_elapsed_seconds` | 0 | N/A | N/A | N/A | N/A |

## Per-Scenario Results

| Scenario | Trials | TP | FP | FN | TN | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `daylight_person_crossing` | 3 | 3 | 0 | 0 | 0 | 1.000 | 1.000 |
| `low_light_person_crossing` | 3 | 3 | 0 | 0 | 0 | 1.000 | 1.000 |
| `no_person_object_motion` | 3 | 0 | 0 | 0 | 3 | N/A | N/A |
| `no_person_static_scene` | 3 | 0 | 0 | 0 | 3 | N/A | N/A |
| `partial_body_or_fast_entry` | 3 | 3 | 0 | 0 | 0 | 1.000 | 1.000 |
| `side_angle_person_crossing` | 4 | 4 | 0 | 0 | 0 | 1.000 | 1.000 |

## Stability Summary

| Field | Value |
| --- | ---: |
| Samples | 360 |
| Successful samples | 360 |
| Failed samples | 0 |
| Average API response | 8.500 ms |
| Maximum API response | 27.000 ms |

## Interpretation Notes

- True positives: 13; false positives: 0; false negatives: 0; true negatives: 6.
- Person-present trials succeeded in 13 out of 13 cases.
- No-person trials avoided unnecessary alerts in 6 out of 6 cases.
- Precision, recall, F1 score, accuracy, and specificity are 1.000, 1.000, 1.000, 1.000, and 1.000, respectively.
- Treat high metrics carefully if the number of trials is small; present the results as prototype evaluation rather than a large-scale statistical benchmark.
- Discuss any false positive as unnecessary alert risk and any false negative as missed-intrusion risk.
- Mention whether the dashboard stream and status API stayed responsive during testing.

## Limitations and Future Work

- The prototype performs person detection, not identity recognition.
- Accuracy can change with camera angle, lighting, distance, partial body views, and background motion.
- Telegram snapshots leave the local machine, so privacy controls and token management are important.
- Production deployment would require HTTPS, firewall rules, production WSGI hosting, and stronger retention policy enforcement.
