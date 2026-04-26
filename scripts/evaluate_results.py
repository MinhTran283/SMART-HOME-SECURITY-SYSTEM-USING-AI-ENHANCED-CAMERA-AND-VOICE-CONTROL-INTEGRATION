import argparse
import json
from pathlib import Path
from statistics import mean, median


def safe_divide(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator


def load_events(path: Path, event_type: str):
    if not path.exists():
        return []

    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("event_type") == event_type:
            events.append(event)

    return events


def load_notification_results(path: Path):
    if not path.exists():
        return []

    results = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return results


def summarize_latencies(events, notifications):
    values = []
    telegram_values = []
    event_to_notification_values = []
    event_ids = {event.get("event_id") for event in events}

    for event in events:
        latency = event.get("latency") or {}
        end_to_end = latency.get("end_to_end_local_seconds")

        if isinstance(end_to_end, (int, float)):
            values.append(float(end_to_end))

    for notification in notifications:
        if notification.get("parent_event_id") not in event_ids:
            continue

        telegram_elapsed = notification.get("telegram_elapsed_seconds")
        event_to_notification = notification.get("event_to_notification_seconds")

        if isinstance(telegram_elapsed, (int, float)):
            telegram_values.append(float(telegram_elapsed))
        if isinstance(event_to_notification, (int, float)):
            event_to_notification_values.append(float(event_to_notification))

    summary = {
        "count": len(values),
        "avg_end_to_end_local_seconds": round(mean(values), 3) if values else None,
        "median_end_to_end_local_seconds": round(median(values), 3) if values else None,
        "min_end_to_end_local_seconds": round(min(values), 3) if values else None,
        "max_end_to_end_local_seconds": round(max(values), 3) if values else None,
        "notification_count": len(event_to_notification_values),
        "avg_event_to_notification_seconds": round(mean(event_to_notification_values), 3)
        if event_to_notification_values
        else None,
        "avg_telegram_elapsed_seconds": round(mean(telegram_values), 3)
        if telegram_values
        else None,
    }
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Calculate thesis evaluation metrics from manual labels and event logs."
    )
    parser.add_argument("--tp", type=int, default=0, help="True positives")
    parser.add_argument("--fp", type=int, default=0, help="False positives")
    parser.add_argument("--fn", type=int, default=0, help="False negatives")
    parser.add_argument("--events-log", default="logs/events.jsonl")
    parser.add_argument("--notifications-log", default="logs/notifications.jsonl")
    parser.add_argument("--event-type", default="person_detected")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    precision = safe_divide(args.tp, args.tp + args.fp)
    recall = safe_divide(args.tp, args.tp + args.fn)
    f1_score = safe_divide(2 * precision * recall, precision + recall)

    events = load_events(Path(args.events_log), args.event_type)
    notifications = load_notification_results(Path(args.notifications_log))
    result = {
        "manual_counts": {
            "true_positive": args.tp,
            "false_positive": args.fp,
            "false_negative": args.fn,
        },
        "metrics": {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1_score, 3),
        },
        "latency": summarize_latencies(events, notifications),
        "event_type": args.event_type,
        "events_log": args.events_log,
        "notifications_log": args.notifications_log,
    }

    output = json.dumps(result, indent=2)
    print(output)

    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
