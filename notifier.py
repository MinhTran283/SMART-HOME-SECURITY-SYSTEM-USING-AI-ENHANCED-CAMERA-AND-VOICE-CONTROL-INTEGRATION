from datetime import datetime, timezone
from pathlib import Path
import time


class Notifier:
    def __init__(
        self,
        enabled=False,
        bot_token="",
        chat_id="",
        timeout_seconds=10,
    ):
        self.enabled = enabled
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout_seconds = timeout_seconds

    def send_alert(self, event: dict):
        return self._send_photo(event, "Security alert")

    def send_snapshot_notification(self, event: dict):
        return self._send_photo(event, "Manual snapshot")

    def _send_photo(self, event: dict, title: str):
        if not self.enabled:
            return {"enabled": False, "status": "skipped"}

        if not self.bot_token or not self.chat_id:
            return {"enabled": True, "status": "not_configured"}

        image_path = event.get("image_path")
        if not image_path or not Path(image_path).exists():
            return {"enabled": True, "status": "missing_image"}

        try:
            import requests
        except ImportError:
            return {"enabled": True, "status": "requests_missing"}

        caption = self._build_caption(event, title)
        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        started_at = time.perf_counter()

        try:
            with Path(image_path).open("rb") as image_file:
                response = requests.post(
                    url,
                    data={"chat_id": self.chat_id, "caption": caption},
                    files={"photo": image_file},
                    timeout=self.timeout_seconds,
                )
            response.raise_for_status()
        except Exception as exc:
            print(f"[NOTIFIER] Telegram send failed: {exc}")
            elapsed = round(time.perf_counter() - started_at, 3)
            return {
                "enabled": True,
                "status": "failed",
                "error": str(exc),
                "elapsed_seconds": elapsed,
            }

        print(f"[NOTIFIER] Telegram notification sent: {event['event_id']}")
        elapsed = round(time.perf_counter() - started_at, 3)
        return {"enabled": True, "status": "sent", "elapsed_seconds": elapsed}

    @staticmethod
    def _build_caption(event: dict, title: str):
        confidence = event.get("confidence")
        confidence_text = "n/a" if confidence is None else f"{confidence:.2f}"
        timestamp = event.get("timestamp") or datetime.now(timezone.utc).isoformat()

        return (
            f"{title}\n"
            f"Event: {event.get('event_type')}\n"
            f"Camera: {event.get('camera_id')}\n"
            f"State: {event.get('system_state')}\n"
            f"Confidence: {confidence_text}\n"
            f"Time: {timestamp}"
        )
