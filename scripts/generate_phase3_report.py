import argparse
import csv
import json
from pathlib import Path
from statistics import mean

from evaluate_trials import evaluate_trials, load_trials


def fmt(value):
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def parse_float(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def load_json(path):
    if not path or not Path(path).exists():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_status_monitor(path):
    monitor_path = Path(path)
    if not path or not monitor_path.exists():
        return None

    rows = []
    with monitor_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(row)

    if not rows:
        return {
            "samples": 0,
            "ok_samples": 0,
            "failed_samples": 0,
            "average_response_ms": None,
            "maximum_response_ms": None,
        }

    response_values = [
        value
        for value in (parse_float(row.get("response_ms")) for row in rows)
        if value is not None
    ]
    ok_samples = sum(1 for row in rows if str(row.get("ok", "")).lower() == "true")

    return {
        "samples": len(rows),
        "ok_samples": ok_samples,
        "failed_samples": len(rows) - ok_samples,
        "average_response_ms": round(mean(response_values), 1)
        if response_values
        else None,
        "maximum_response_ms": round(max(response_values), 1)
        if response_values
        else None,
    }


def metric_table(summary):
    counts = summary["overall"]["counts"]
    metrics = summary["overall"]["metrics"]
    return [
        "| Metric | Value |",
        "| --- | ---: |",
        f"| True positives | {counts['true_positive']} |",
        f"| False positives | {counts['false_positive']} |",
        f"| False negatives | {counts['false_negative']} |",
        f"| True negatives | {counts['true_negative']} |",
        f"| Evaluated trials | {counts['evaluated_trials']} |",
        f"| Precision | {fmt(metrics['precision'])} |",
        f"| Recall | {fmt(metrics['recall'])} |",
        f"| F1 score | {fmt(metrics['f1_score'])} |",
        f"| Accuracy | {fmt(metrics['accuracy'])} |",
        f"| Specificity | {fmt(metrics['specificity'])} |",
    ]


def latency_table(summary):
    rows = [
        "| Latency field | Count | Average | Median | Minimum | Maximum |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for field, values in summary["latency"].items():
        rows.append(
            f"| `{field}` | {values['count']} | {fmt(values['average'])} | "
            f"{fmt(values['median'])} | {fmt(values['minimum'])} | {fmt(values['maximum'])} |"
        )
    return rows


def scenario_table(summary):
    rows = [
        "| Scenario | Trials | TP | FP | FN | TN | Precision | Recall |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for scenario, data in summary["per_scenario"].items():
        counts = data["counts"]
        metrics = data["metrics"]
        rows.append(
            f"| `{scenario}` | {counts['evaluated_trials']} | "
            f"{counts['true_positive']} | {counts['false_positive']} | "
            f"{counts['false_negative']} | {counts['true_negative']} | "
            f"{fmt(metrics['precision'])} | {fmt(metrics['recall'])} |"
        )
    return rows


def status_table(status_summary):
    if not status_summary:
        return [
            "No status monitor CSV was provided. Run `scripts/monitor_status.py` to add stability evidence."
        ]

    return [
        "| Field | Value |",
        "| --- | ---: |",
        f"| Samples | {status_summary['samples']} |",
        f"| Successful samples | {status_summary['ok_samples']} |",
        f"| Failed samples | {status_summary['failed_samples']} |",
        f"| Average API response | {fmt(status_summary['average_response_ms'])} ms |",
        f"| Maximum API response | {fmt(status_summary['maximum_response_ms'])} ms |",
    ]


def build_report(trial_csv, summary, status_summary):
    counts = summary["overall"]["counts"]
    metrics = summary["overall"]["metrics"]
    trial_csv_display = str(trial_csv).replace("\\", "/")
    latency_available = any(
        values.get("count", 0) > 0 for values in summary["latency"].values()
    )
    lines = [
        "# Phase 3 Results Report",
        "",
        "This report is generated from the Phase 3 trial CSV and optional status-monitor evidence.",
        "",
        "## Source Files",
        "",
        f"- Trial CSV: `{trial_csv_display}`",
        "- Metric source: `scripts/evaluate_trials.py`",
        "",
        "## Test Scope",
        "",
        f"The completed detection run contains {counts['evaluated_trials']} evaluated live-camera trials. Manual snapshot trials are not included in the detection metrics.",
        "",
        "The test evidence focuses on detection correctness and alert behavior. Per-event latency values are reported only when the trial CSV contains exported event and notification latency fields.",
        "" if latency_available else "No Phase 3 latency values were provided in the trial CSV for this generated report.",
        "",
        "## Detection Metrics",
        "",
        *metric_table(summary),
        "",
        "## Latency Summary",
        "",
        *latency_table(summary),
        "",
        "## Per-Scenario Results",
        "",
        *scenario_table(summary),
        "",
        "## Stability Summary",
        "",
        *status_table(status_summary),
        "",
        "## Interpretation Notes",
        "",
        f"- True positives: {counts['true_positive']}; false positives: {counts['false_positive']}; false negatives: {counts['false_negative']}; true negatives: {counts['true_negative']}.",
        f"- Person-present trials succeeded in {counts['true_positive']} out of {counts['true_positive'] + counts['false_negative']} cases.",
        f"- No-person trials avoided unnecessary alerts in {counts['true_negative']} out of {counts['true_negative'] + counts['false_positive']} cases.",
        f"- Precision, recall, F1 score, accuracy, and specificity are {fmt(metrics['precision'])}, {fmt(metrics['recall'])}, {fmt(metrics['f1_score'])}, {fmt(metrics['accuracy'])}, and {fmt(metrics['specificity'])}, respectively.",
        "- Treat high metrics carefully if the number of trials is small; present the results as prototype evaluation rather than a large-scale statistical benchmark.",
        "- Discuss any false positive as unnecessary alert risk and any false negative as missed-intrusion risk.",
        "- Mention whether the dashboard stream and status API stayed responsive during testing.",
        "",
        "## Limitations and Future Work",
        "",
        "- The prototype performs person detection, not identity recognition.",
        "- Accuracy can change with camera angle, lighting, distance, partial body views, and background motion.",
        "- Telegram snapshots leave the local machine, so privacy controls and token management are important.",
        "- Production deployment would require HTTPS, firewall rules, production WSGI hosting, and stronger retention policy enforcement.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Markdown Phase 3 report from trial and stability evidence."
    )
    parser.add_argument("--trials", default="data/phase3_trials_template.csv")
    parser.add_argument("--summary", default="")
    parser.add_argument("--status-monitor", default="")
    parser.add_argument("--output", default="docs/phase3_results_report.md")
    args = parser.parse_args()

    summary = load_json(args.summary)
    if summary is None:
        rows = load_trials(Path(args.trials))
        summary = evaluate_trials(rows)
        summary["source_csv"] = args.trials
        summary["total_rows_read"] = len(rows)

    status_summary = load_status_monitor(args.status_monitor)
    report = build_report(args.trials, summary, status_summary)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
