from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import threading


@dataclass
class SystemStateManager:
    state: str = "DISARMED"
    cooldown_until: datetime | None = None
    lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def arm(self):
        with self.lock:
            self.state = "ARMED"
            self.cooldown_until = None
            print("ARMED")

    def disarm(self):
        with self.lock:
            self.state = "DISARMED"
            self.cooldown_until = None
            print("DISARMED")

    def trigger_alert(self, cooldown):
        with self.lock:
            self.state = "COOLDOWN"
            self.cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=cooldown)
            print("COOLDOWN")

    def refresh(self):
        with self.lock:
            if self.state == "COOLDOWN" and self.cooldown_until is not None:
                if datetime.now(timezone.utc) >= self.cooldown_until:
                    self.state = "ARMED"
                    self.cooldown_until = None

    def can_trigger_detection(self):
        self.refresh()
        with self.lock:
            return self.state == "ARMED"

    def get_status(self):
        self.refresh()
        with self.lock:
            remaining = 0
            if self.cooldown_until is not None:
                remaining = max(
                    0,
                    int((self.cooldown_until - datetime.now(timezone.utc)).total_seconds()),
                )

            return {
                "state": self.state,
                "state_normalized": self.state.lower(),
                "cooldown_remaining_seconds": remaining,
            }
