import json
import time
import typing
import websocket
import threading
from .client import LMAXClient


class LMAXWebSocketClient(LMAXClient):
    def __init__(self, *args, **kwargs):
        """Initializes the LMAXWebSocketClient object.

        Args:
        - client_key_id (str): LMAX API key
        - secret (str): LMAX API
        - base_url (_type_, optional): LMAX API endpoint to use.
        - rate_limit_seconds (int, optional): Rate limit in seconds. Defaults to 1.
        - verbose (bool, optional): Flag to set verbose logging of requests and responses. Defaults to False.
        """
        super().__init__(*args, **kwargs)
        self.ws: typing.Union[None, websocket.WebSocketApp] = None
        self.subscriptions: list = []
        self.lock: threading.Lock = threading.Lock()
        self.is_subscribed: bool = False
        self.reconnect_delay: int = 5  # seconds

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
            self.logger.info("Reconnecting WebSocket...")

    def on_open(self, ws):
        """Callback executed when WebSocket connection is opened."""
        self.logger.info("WebSocket connection opened.")
        with self.lock:
            if not self.is_subscribed:
                for subscription in self.subscriptions:
                    self.subscribe(subscription)
                self.is_subscribed = True

    def on_message(self, ws, message):
        """Callback executed when a message is received."""
        self.logger.debug("Received raw message: %s", message)
        try:
            data = json.loads(message)
            self.logger.debug("Processed message: %s", data)
        except json.JSONDecodeError as e:
            self.logger.error("Failed to decode message: %s", e)

    def on_error(self, ws, error):
        """Callback executed when an error occurs."""
        self.logger.error("WebSocket error: %s", error)

    def on_close(self, ws, close_status_code, close_msg):
        """Callback executed when WebSocket connection is closed."""
        self.logger.info(
            "WebSocket connection closed with code: %s, message: %s",
            close_status_code,
            close_msg,
        )
        self.is_subscribed = False

    def on_ping(self, ws, message):
        """Callback executed when a ping is received."""
        self.logger.debug("Ping received")
        ws.send("", opcode=websocket.ABNF.OPCODE_PONG)

    def on_pong(self, ws, message):
        """Callback executed when a pong is received."""
        self.logger.debug("Pong received")

    def subscribe(self, subscription):
        """Sends a subscribe message to the WebSocket."""
        message = {
            "type": "SUBSCRIBE",
            "channels": [subscription],
        }
        if subscription not in self.subscriptions:
            self.subscriptions.append(subscription)
            self.logger.info("Added subscription: %s", subscription)
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(message))
            self.logger.info("Sent subscription message: %s", json.dumps(message))

    def unsubscribe(self, subscription):
        """Sends an unsubscribe message to the WebSocket."""
        message = {
            "type": "UNSUBSCRIBE",
            "channels": [subscription],
        }
        if subscription in self.subscriptions:
            self.subscriptions.remove(subscription)
            self.logger.info("Removed subscription: %s", subscription)

        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(message))
            self.logger.info("Sent unsubscription message: %s", json.dumps(message))

    def close(self):
        """Closes the WebSocket connection."""
        if self.ws:
            self.ws.close()
            self.thread.join()
            self.logger.info("WebSocket closed and thread joined")
