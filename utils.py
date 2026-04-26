import time
from datetime import datetime, timezone
from pathlib import Path

import cv2


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def event_id(prefix="evt"):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}_{stamp}"


def draw_boxes(frame, motion_boxes=None, person_bbox=None, person_confidence=None, status_text=""):
    output = frame.copy()

    if motion_boxes:
        for (x, y, w, h) in motion_boxes:
            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 255), 2)
            cv2.putText(
                output,
                "Motion",
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                2,
            )

    if person_bbox:
        x, y, w, h = person_bbox
        cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)

        label = "Person"
        if person_confidence is not None:
            label = f"Person {person_confidence:.2f}"

        cv2.putText(
            output,
            label,
            (x, max(20, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    if status_text:
        cv2.putText(
            output,
            status_text,
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

    return output


def save_snapshot(frame, events_dir: Path, image_id=None, event_type="snapshot"):
    events_dir.mkdir(parents=True, exist_ok=True)
    image_id = image_id or event_id("img")
    safe_event_type = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in event_type)
    filename = f"{image_id}_{safe_event_type}.jpg"
    filepath = events_dir / filename

    ok = cv2.imwrite(str(filepath), frame)
    if not ok:
        raise RuntimeError(f"Failed to save snapshot to {filepath}")

    return filepath


def cleanup_old_snapshots(events_dir: Path, retention_days: int):
    if retention_days <= 0 or not events_dir.exists():
        return 0

    cutoff = time.time() - retention_days * 24 * 60 * 60
    deleted = 0

    for path in events_dir.glob("*.jpg"):
        if path.stat().st_mtime < cutoff:
            path.unlink()
            deleted += 1

    return deleted
