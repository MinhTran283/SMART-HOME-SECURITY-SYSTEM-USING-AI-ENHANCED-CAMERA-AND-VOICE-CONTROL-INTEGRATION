# Quick Evaluation Results

This document summarizes the minimum official Phase 2 validation run. The run used five detection trials plus one manual snapshot/Telegram functional validation.

Event timestamps in the logs are stored in UTC.

## Detection Trial Summary

| Trial | Scenario | Expected person | System alerted | Outcome | Notes |
| --- | --- | --- | --- | --- | --- |
| D01 | Daylight person crossing | true | true | TP | Motion and person detected; Telegram alert sent |
| D02 | Daylight person crossing | true | true | TP | Motion and person detected; Telegram alert sent |
| L01 | Low light person crossing | true | true | TP | Person detected under lower light; Telegram alert sent |
| N01 | No-person static scene | false | false | TN | No motion and no Telegram notification |
| O01 | No-person object motion | false | false | TN | Motion occurred, but no person alert was generated |

## Functional Validation

| Trial | Feature | Result | Notes |
| --- | --- | --- | --- |
| M01 | Manual snapshot and Telegram delivery | Success | Manual snapshot was saved and delivered to Telegram; excluded from detection metrics |

## Metrics

The metric script evaluated five detection trials.

| Metric | Result |
| --- | ---: |
| True positives | 3 |
| False positives | 0 |
| False negatives | 0 |
| True negatives | 2 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 score | 1.000 |
| Accuracy | 1.000 |
| Specificity | 1.000 |

## Latency

Latency values are calculated from the three person-detection alerts.

| Latency field | Average | Median | Minimum | Maximum |
| --- | ---: | ---: | ---: | ---: |
| Local end-to-end processing | 0.020 s | 0.019 s | 0.018 s | 0.022 s |
| Event to Telegram result | 0.639 s | 0.650 s | 0.577 s | 0.691 s |
| Telegram API elapsed time | 0.619 s | 0.631 s | 0.558 s | 0.667 s |

## Interpretation

Within this limited validation run, the prototype successfully detected all three person-entry scenarios and avoided alerts during both no-person scenarios. The system also delivered Telegram alerts in under one second on average.

Because the sample size is small, these results should be presented as a minimum functional validation rather than a broad statistical accuracy claim. A larger evaluation with more lighting conditions, camera angles, and background motion would be needed for stronger generalization.

## Source Files

- `data/evaluation_trials_quick_results.csv`
- `logs/evaluation_quick_trials_summary.json`
- `logs/events.jsonl`
- `logs/notifications.jsonl`
