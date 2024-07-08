import json
import time
import websocket
import threading
from .client import LMAXClient


class LMAXWebSocketClient(LMAXClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws = None
        self.subscriptions = []
        self.lock = threading.Lock()
        self.is_subscribed = False
        self.reconnect_delay = 5  # seconds

    def connect(self):
        """Establishes a WebSocket connection and authenticates."""
        ws_url = self.base_url.replace("https", "wss") + "/v1/web-socket"
        self.ws = websocket.WebSocketApp(
            ws_url,
            header={"Authorization": f"Bearer {self.token}"},
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_ping=self.on_ping,
            on_pong=self.on_pong,
        )
        self.ws.on_open = self.on_open
        self.thread = threading.Thread(target=self._run_forever)
        self.thread.daemon = True
        self.thread.start()

    def _run_forever(self):
        """Runs the WebSocket client in a loop to handle reconnections."""
        while True:
            self.ws.run_forever(ping_interval=30, ping_timeout=10)
            time.sleep(self.reconnect_delay)
            print("Reconnecting WebSocket...")

    def on_open(self, ws):
        """Callback executed when WebSocket connection is opened."""
        print("WebSocket connection opened.")
        with self.lock:
            if not self.is_subscribed:
                for subscription in self.subscriptions:
                    self.subscribe(subscription)
                self.is_subscribed = True

    def on_message(self, ws, message):
        """Callback executed when a message is received."""
        print(f"Received raw message: {message}")
        try:
            data = json.loads(message)
            print("Processed message:", data)
        except json.JSONDecodeError as e:
            print("Failed to decode message:", e)

    def on_error(self, ws, error):
        """Callback executed when an error occurs."""
        print("WebSocket error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        """Callback executed when WebSocket connection is closed."""
        print(
            f"WebSocket connection closed with code: {close_status_code}, message: {close_msg}"
        )
        self.is_subscribed = False

    def on_ping(self, ws, message):
        """Callback executed when a ping is received."""
        print("Ping received")
        ws.send("", opcode=websocket.ABNF.OPCODE_PONG)

    def on_pong(self, ws, message):
        """Callback executed when a pong is received."""
        print("Pong received")

    def subscribe(self, subscription):
        """Sends a subscribe message to the WebSocket."""
        message = {
            "type": "SUBSCRIBE",
            "channels": [subscription],
        }
        if subscription not in self.subscriptions:
            self.subscriptions.append(subscription)
            print(f"Added subscription: {subscription}")

        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(message))
            print(f"Sent subscription message: {json.dumps(message)}")

    def unsubscribe(self, subscription):
        """Sends an unsubscribe message to the WebSocket."""
        message = {
            "type": "UNSUBSCRIBE",
            "channels": [subscription],
        }
        if subscription in self.subscriptions:
            self.subscriptions.remove(subscription)
            print(f"Removed subscription: {subscription}")

        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(message))
            print(f"Sent unsubscription message: {json.dumps(message)}")

    def close(self):
        """Closes the WebSocket connection."""
        if self.ws:
            self.ws.close()
            self.thread.join()
            print("WebSocket closed and thread joined")
