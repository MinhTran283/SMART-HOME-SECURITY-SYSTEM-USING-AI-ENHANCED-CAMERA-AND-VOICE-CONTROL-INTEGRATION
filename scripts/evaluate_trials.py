import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median


OUTCOMES = ("TP", "FP", "FN", "TN")
LATENCY_FIELDS = (
    "end_to_end_local_seconds",
    "event_to_notification_seconds",
    "telegram_elapsed_seconds",
)


def parse_bool(value):
    if value is None:
        return None

    normalized = str(value).strip().lower()
    if normalized in {"true", "t", "yes", "y", "1", "detected", "alerted"}:
        return True
    if normalized in {"false", "f", "no", "n", "0", "none", "not_detected"}:
        return False
    return None


def parse_float(value):
    if value is None:
        return None

    stripped = str(value).strip()
    if not stripped:
        return None

    try:
        return float(stripped)
    except ValueError:
        return None


def infer_outcome(expected_person, system_alerted):
    if expected_person is True and system_alerted is True:
        return "TP"
    if expected_person is False and system_alerted is True:
        return "FP"
    if expected_person is True and system_alerted is False:
        return "FN"
    if expected_person is False and system_alerted is False:
        return "TN"
    return None


def safe_ratio(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator


def round_metric(value):
    if value is None:
        return None
    return round(value, 3)


def summarize_counts(counts):
    tp = counts["TP"]
    fp = counts["FP"]
    fn = counts["FN"]
    tn = counts["TN"]
    total = tp + fp + fn + tn
    precision = safe_ratio(tp, tp + fp)
    recall = safe_ratio(tp, tp + fn)
    specificity = safe_ratio(tn, tn + fp)
    accuracy = safe_ratio(tp + tn, total)

    if precision is None or recall is None:
        f1_score = None
    elif precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = 2 * precision * recall / (precision + recall)

    return {
        "counts": {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "true_negative": tn,
            "evaluated_trials": total,
        },
        "metrics": {
            "precision": round_metric(precision),
            "recall": round_metric(recall),
            "f1_score": round_metric(f1_score),
            "accuracy": round_metric(accuracy),
            "specificity": round_metric(specificity),
        },
    }


def summarize_values(values):
    if not values:
        return {
            "count": 0,
            "average": None,
            "median": None,
            "minimum": None,
            "maximum": None,
        }

    return {
        "count": len(values),
        "average": round(mean(values), 3),
        "median": round(median(values), 3),
        "minimum": round(min(values), 3),
        "maximum": round(max(values), 3),
    }


def load_trials(csv_path):
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row_number, row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in row.values()):
                continue
            rows.append((row_number, row))
    return rows


def evaluate_trials(rows):
    warnings = []
    overall_counts = defaultdict(int)
    scenario_counts = defaultdict(lambda: defaultdict(int))
    latency_values = {field: [] for field in LATENCY_FIELDS}
    evaluated_rows = []

    for row_number, row in rows:
        trial_id = (row.get("trial_id") or f"row_{row_number}").strip()
        scenario = (row.get("scenario") or "unspecified").strip() or "unspecified"
        expected_person = parse_bool(row.get("expected_person"))
        system_alerted = parse_bool(row.get("system_alerted"))
        inferred = infer_outcome(expected_person, system_alerted)
        provided = (row.get("outcome") or "").strip().upper()

        if inferred is None:
            warnings.append(
                {
                    "trial_id": trial_id,
                    "row": row_number,
                    "message": "Skipped row because expected_person or system_alerted is not a valid boolean.",
                }
            )
            continue

        if provided and provided in OUTCOMES and provided != inferred:
            warnings.append(
                {
                    "trial_id": trial_id,
                    "row": row_number,
                    "message": f"Provided outcome {provided} differs from inferred outcome {inferred}; inferred value was used.",
                }
            )

        overall_counts[inferred] += 1
        scenario_counts[scenario][inferred] += 1

        for field in LATENCY_FIELDS:
            parsed = parse_float(row.get(field))
            if parsed is not None:
                latency_values[field].append(parsed)

        evaluated_rows.append(
            {
                "trial_id": trial_id,
                "scenario": scenario,
                "outcome": inferred,
            }
        )

    per_scenario = {}
    for scenario, counts in sorted(scenario_counts.items()):
        per_scenario[scenario] = summarize_counts(counts)

    return {
        "overall": summarize_counts(overall_counts),
        "per_scenario": per_scenario,
        "latency": {
            field: summarize_values(values) for field, values in latency_values.items()
        },
        "evaluated_trials": evaluated_rows,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Phase 2 person-detection trials from a CSV file."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="data/evaluation_trials_template.csv",
        help="Path to a CSV file with manual trial labels.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional JSON output path, for example logs/evaluation_trials_summary.json.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        raise SystemExit(f"CSV file not found: {csv_path}")

    rows = load_trials(csv_path)
    result = evaluate_trials(rows)
    result["source_csv"] = str(csv_path)
    result["total_rows_read"] = len(rows)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    print(output)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
