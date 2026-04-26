import json
import time


class MqttGateway:
    def __init__(self, config, on_command=None):
        self.config = config
        self.on_command = on_command
        self.client = None
        self.connected = False

    def start(self):
        if not self.config.MQTT_ENABLED:
            print("[MQTT] Disabled")
            return

        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            print("[MQTT] paho-mqtt is not installed; MQTT disabled for this run")
            return

        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        if self.config.MQTT_USERNAME:
            self.client.username_pw_set(
                self.config.MQTT_USERNAME,
                self.config.MQTT_PASSWORD or None,
            )

        if self.config.MQTT_TLS:
            self.client.tls_set()

        try:
            self.client.connect(self.config.MQTT_HOST, self.config.MQTT_PORT, keepalive=60)
            self.client.loop_start()
        except Exception as exc:
            print(f"[MQTT] Connection failed: {exc}")
            self.client = None

    def publish_event(self, event):
        self.publish_json(self.config.MQTT_EVENT_TOPIC, event)

    def publish_status(self, status):
        self.publish_json(self.config.MQTT_STATUS_TOPIC, status, retain=True)

    def publish_heartbeat(self, status):
        payload = {
            "timestamp": time.time(),
            "camera_id": self.config.CAMERA_ID,
            "status": status,
        }
        self.publish_json(self.config.MQTT_HEARTBEAT_TOPIC, payload)

    def publish_json(self, topic, payload, retain=False):
        if not self.client or not self.connected:
            return False

        try:
            self.client.publish(
                topic,
                json.dumps(payload, ensure_ascii=False),
                qos=1,
                retain=retain,
            )
        except Exception as exc:
            print(f"[MQTT] Publish failed on {topic}: {exc}")
            return False

        return True

    def _on_connect(self, client, userdata, flags, rc):
        self.connected = rc == 0
        if not self.connected:
            print(f"[MQTT] Connect returned rc={rc}")
            return

        print(f"[MQTT] Connected to {self.config.MQTT_HOST}:{self.config.MQTT_PORT}")
        client.subscribe(self.config.MQTT_COMMAND_TOPIC, qos=1)

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print(f"[MQTT] Disconnected rc={rc}")

    def _on_message(self, client, userdata, message):
        if not self.on_command:
            return

        payload = message.payload.decode("utf-8", errors="replace").strip()
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {"command": payload}

        command = str(data.get("command", "")).lower()
        if not command:
            return

        self.on_command(command, source="mqtt")
