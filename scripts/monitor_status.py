import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path


FIELDNAMES = [
    "timestamp",
    "ok",
    "status_code",
    "response_ms",
    "state",
    "state_normalized",
    "source_mode",
    "source_label",
    "motion_detected",
    "person_detected",
    "person_confidence",
    "motion_detection_seconds",
    "person_inference_seconds",
    "error",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_base_url(value):
    return value.rstrip("/") + "/"


def build_opener():
    cookie_jar = CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))


def request_json(opener, url, timeout):
    started = time.perf_counter()
    status_code = None
    try:
        with opener.open(url, timeout=timeout) as response:
            status_code = response.status
            payload = response.read().decode("utf-8")
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            return status_code, elapsed_ms, json.loads(payload), ""
    except urllib.error.HTTPError as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        try:
            error_text = exc.read().decode("utf-8", errors="replace")
        except Exception:
            error_text = str(exc)
        return exc.code, elapsed_ms, None, error_text.strip()
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        return status_code, elapsed_ms, None, str(exc)


def login(opener, base_url, username, password, timeout):
    login_url = urllib.parse.urljoin(base_url, "login")
    payload = urllib.parse.urlencode(
        {"username": username, "password": password}
    ).encode("utf-8")
    request = urllib.request.Request(
        login_url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with opener.open(request, timeout=timeout) as response:
        return response.status


def status_to_row(status_code, response_ms, data, error):
    detection = (data or {}).get("detection") or {}
    ok = status_code == 200 and isinstance(data, dict)

    return {
        "timestamp": now_iso(),
        "ok": str(ok).lower(),
        "status_code": status_code or "",
        "response_ms": response_ms,
        "state": (data or {}).get("state", ""),
        "state_normalized": (data or {}).get("state_normalized", ""),
        "source_mode": (data or {}).get("source_mode", ""),
        "source_label": (data or {}).get("source_label", ""),
        "motion_detected": detection.get("motion_detected", ""),
        "person_detected": detection.get("person_detected", ""),
        "person_confidence": detection.get("person_confidence", ""),
        "motion_detection_seconds": detection.get("motion_detection_seconds", ""),
        "person_inference_seconds": detection.get("person_inference_seconds", ""),
        "error": error,
    }


def should_continue(started_at, duration_seconds, sample_count, max_samples):
    if max_samples > 0 and sample_count >= max_samples:
        return False
    if duration_seconds > 0 and time.perf_counter() - started_at >= duration_seconds:
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Monitor the Flask status API for uptime and response-time evidence."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--output", default="logs/status_monitor.csv")
    parser.add_argument("--interval-seconds", type=float, default=5.0)
    parser.add_argument("--duration-seconds", type=float, default=60.0)
    parser.add_argument(
        "--samples",
        type=int,
        default=0,
        help="Stop after this many samples. 0 means controlled only by duration.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--username", default="")
    parser.add_argument(
        "--password",
        default="",
        help="Dashboard password. Prefer --password-env for shared logs or screenshots.",
    )
    parser.add_argument(
        "--password-env",
        default="",
        help="Environment variable name containing the dashboard password.",
    )
    args = parser.parse_args()

    base_url = normalize_base_url(args.base_url)
    status_url = urllib.parse.urljoin(base_url, "api/status")
    opener = build_opener()

    password = args.password
    if args.password_env:
        password = os.environ.get(args.password_env, "")

    if args.username and password:
        login_status = login(
            opener,
            base_url,
            args.username,
            password,
            args.timeout_seconds,
        )
        print(f"Login request completed with HTTP {login_status}")
    elif args.username:
        raise SystemExit("Username was provided but password is missing.")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not output_path.exists() or output_path.stat().st_size == 0

    sample_count = 0
    started_at = time.perf_counter()
    with output_path.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()

        while should_continue(started_at, args.duration_seconds, sample_count, args.samples):
            status_code, response_ms, data, error = request_json(
                opener,
                status_url,
                args.timeout_seconds,
            )
            row = status_to_row(status_code, response_ms, data, error)
            writer.writerow(row)
            csv_file.flush()
            sample_count += 1

            print(
                f"{row['timestamp']} ok={row['ok']} status={row['status_code']} "
                f"response_ms={row['response_ms']} state={row['state_normalized']}"
            )

            if should_continue(started_at, args.duration_seconds, sample_count, args.samples):
                time.sleep(max(args.interval_seconds, 0))

    print(f"Wrote {sample_count} samples to {output_path}")


if __name__ == "__main__":
    main()
