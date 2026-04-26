import json
import threading
from datetime import datetime, timezone
from pathlib import Path


class EventLogger:
    def __init__(self, events_dir: Path, logs_dir: Path):
        self.events_dir = Path(events_dir)
        self.logs_dir = Path(logs_dir)
        self.event_log_file = self.logs_dir / "events.jsonl"
        self.notification_log_file = self.logs_dir / "notifications.jsonl"
        self.lock = threading.Lock()

        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: dict):
        required = {"event_id", "timestamp", "event_type", "camera_id", "system_state"}
        missing = required.difference(event)
        if missing:
            raise ValueError(f"Event missing required fields: {sorted(missing)}")

        with self.lock:
            with self.event_log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

        print(f"[EVENT] Logged: {event['event_type']} | {event['event_id']}")

    def log_notification_result(self, result: dict):
        with self.lock:
            with self.notification_log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

        print(
            "[NOTIFICATION] "
            f"{result.get('status')} | parent={result.get('parent_event_id')}"
        )

    def read_events(self, limit: int = 20):
        if not self.event_log_file.exists():
            return []

        with self.lock:
            lines = self.event_log_file.read_text(encoding="utf-8").splitlines()

        results = []
        for line in lines[-limit:]:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event = self._normalize_legacy_event(event)
            results.append(event)

        results.reverse()
        return results

    def _normalize_legacy_event(self, event: dict):
        image_path = event.get("image_path")
        if image_path:
            event.setdefault("image_filename", Path(image_path).name)

        event.setdefault("camera_id", "living_room")
        event["system_state"] = str(event.get("system_state", "unknown")).lower()
        event.setdefault("confidence", None)
        event.setdefault("bounding_box", None)
        event.setdefault("source", "system")
        event.setdefault("source_mode", "unknown")
        event.setdefault("source_label", "unknown")
        event.setdefault("latency", {})
        return event

    @staticmethod
    def now_iso():
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
