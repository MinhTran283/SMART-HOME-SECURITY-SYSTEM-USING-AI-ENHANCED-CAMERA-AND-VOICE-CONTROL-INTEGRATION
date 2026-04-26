import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from notifier import Notifier


def load_latest_event_with_image(log_path: Path):
    if not log_path.exists():
        raise SystemExit(f"Event log does not exist: {log_path}")

    for line in reversed(log_path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        image_path = event.get("image_path")
        if image_path and Path(image_path).exists():
            return event

    raise SystemExit("No event with an existing image was found.")


def main():
    if not config.TELEGRAM_ENABLED:
        raise SystemExit("Set TELEGRAM_ENABLED=true in .env before testing Telegram.")

    event = load_latest_event_with_image(config.LOGS_DIR / "events.jsonl")
    notifier = Notifier(
        enabled=config.TELEGRAM_ENABLED,
        bot_token=config.TELEGRAM_BOT_TOKEN,
        chat_id=config.TELEGRAM_CHAT_ID,
        timeout_seconds=config.TELEGRAM_TIMEOUT_SECONDS,
    )
    result = notifier.send_snapshot_notification(event)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
