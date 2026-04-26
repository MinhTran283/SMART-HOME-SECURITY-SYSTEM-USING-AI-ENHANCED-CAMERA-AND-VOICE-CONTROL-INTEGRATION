import argparse
import csv
import json
from pathlib import Path


TRIAL_COLUMNS = [
    "trial_id",
    "scenario",
    "lighting_condition",
    "expected_person",
    "system_alerted",
    "event_id",
    "timestamp",
    "source_mode",
    "source_label",
    "confidence",
    "end_to_end_local_seconds",
    "event_to_notification_seconds",
    "telegram_elapsed_seconds",
    "outcome",
    "notes",
]


def load_jsonl(path):
    if not path.exists():
        return []

    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"[WARN] Skipped invalid JSON at {path}:{line_number}")
    return records


def notification_index(notifications):
    by_event_id = {}
    for notification in notifications:
        parent_event_id = notification.get("parent_event_id")
        if not parent_event_id:
            continue
        by_event_id[parent_event_id] = notification
    return by_event_id


def value_or_blank(value):
    if value is None:
        return ""
    return value


def format_float(value):
    if isinstance(value, (int, float)):
        return f"{float(value):.3f}"
    return ""


def event_to_trial_row(event, notification, index, scenario, lighting_condition):
    event_type = event.get("event_type", "")
    latency = event.get("latency") or {}
    confidence = event.get("confidence")
    system_alerted = event_type == "person_detected"

    notes = "prefilled from event log; verify expected_person manually"
    if event_type and event_type != "person_detected":
        notes = f"prefilled from {event_type}; verify whether it belongs in official trials"

    return {
        "trial_id": f"LOG{index:03d}",
        "scenario": scenario,
        "lighting_condition": lighting_condition,
        "expected_person": "",
        "system_alerted": str(system_alerted).lower(),
        "event_id": value_or_blank(event.get("event_id")),
        "timestamp": value_or_blank(event.get("timestamp")),
        "source_mode": value_or_blank(event.get("source_mode")),
        "source_label": value_or_blank(event.get("source_label")),
        "confidence": format_float(confidence),
        "end_to_end_local_seconds": format_float(latency.get("end_to_end_local_seconds")),
        "event_to_notification_seconds": format_float(
            notification.get("event_to_notification_seconds") if notification else None
        ),
        "telegram_elapsed_seconds": format_float(
            notification.get("telegram_elapsed_seconds") if notification else None
        ),
        "outcome": "",
        "notes": notes,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Export logged events into the Phase 2 evaluation trial CSV format."
    )
    parser.add_argument("--events-log", default="logs/events.jsonl")
    parser.add_argument("--notifications-log", default="logs/notifications.jsonl")
    parser.add_argument("--output", default="data/evaluation_trials_from_logs.csv")
    parser.add_argument(
        "--event-type",
        default="person_detected",
        help="Event type to export. Use 'all' to include every event.",
    )
    parser.add_argument("--scenario", default="")
    parser.add_argument("--lighting-condition", default="")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of most recent matching events to export. 0 means no limit.",
    )
    args = parser.parse_args()

    events = load_jsonl(Path(args.events_log))
    notifications = notification_index(load_jsonl(Path(args.notifications_log)))

    if args.event_type != "all":
        events = [event for event in events if event.get("event_type") == args.event_type]

    if args.limit > 0:
        events = events[-args.limit :]

    rows = [
        event_to_trial_row(
            event,
            notifications.get(event.get("event_id")),
            index,
            args.scenario,
            args.lighting_condition,
        )
        for index, event in enumerate(events, start=1)
    ]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=TRIAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} trial rows to {output_path}")
    if rows:
        print("Next step: fill expected_person, scenario, and lighting_condition before running evaluate_trials.py.")


if __name__ == "__main__":
    main()
