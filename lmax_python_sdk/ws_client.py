import json
import time
import enum
import typing
import websocket
import threading
from .client import LMAXClient


class WebSocketState(enum.Enum):
    DISCONNECTED = 1
    CONNECTING = 2
    CONNECTED = 3
    AUTHENTICATING = 4
    AUTHENTICATED = 5


class LMAXWebSocketClient(LMAXClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state: WebSocketState = WebSocketState.DISCONNECTED
        self.ws_url = self.base_url.replace("https", "wss") + "/v1/web-socket"
        self.ws: typing.Optional[websocket.WebSocketApp] = None
        self.lock: threading.Lock = threading.Lock()
        self.subscriptions: typing.List[str] = []
        self.reconnect_delay: int = 5  # seconds
        self.should_run = True

    def connect(self):
        self.state = WebSocketState.CONNECTING
        while self.should_run:
            try:
                self._refresh_token()
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    header={"Authorization": f"Bearer {self.token}"},
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                    on_ping=self.on_ping,
                    on_pong=self.on_pong,
                    on_open=self.on_open,
                )
                self.thread = threading.Thread(target=self._run_forever)
                self.thread.daemon = True
                self.thread.start()
                break
            except Exception as e:
                self.logger.error("Error connecting WebSocket: %s", e)
                time.sleep(self.reconnect_delay)

    def _run_forever(self):
        while self.should_run:
            self.ws.run_forever(ping_interval=10, ping_timeout=5)
            if self.should_run:
                self.logger.info("WebSocket disconnected. Reconnecting...")
                self._reconnect()

    def _reconnect(self):
        self.state = WebSocketState.CONNECTING
        self._refresh_token()
        if self.ws:
            self.ws.header = {"Authorization": f"Bearer {self.token}"}
        time.sleep(self.reconnect_delay)

    def _refresh_token(self):
        try:
            self.token = self._authenticate()
            self.logger.info("Token refreshed successfully.")
            self.reconnect_delay = 5  # Reset reconnect delay after successful refresh
        except Exception as e:
            self.logger.error("Failed to refresh token: %s", e)
            self.reconnect_delay = min(
                self.reconnect_delay * 2, 60
            )  # Exponential backoff

    def on_open(self, ws):
        self.logger.info("WebSocket connection opened.")
        self.state = WebSocketState.AUTHENTICATED
        with self.lock:
            for subscription in self.subscriptions:
                self.subscribe(subscription)

    def on_message(self, ws, message):
        self.logger.debug("Received raw message: %s", message)
        try:
            data = json.loads(message)
            self.logger.debug("Processed message: %s", data)
        except json.JSONDecodeError as e:
            self.logger.error("Failed to decode message: %s", e)

    def on_error(self, ws, error):
        self.logger.error("WebSocket error: %s", error)
        if (
            isinstance(error, websocket.WebSocketBadStatusException)
            and error.status_code == 401
        ):
            self.logger.error(
                "Error: 401 Unauthorized. Refreshing token and reconnecting."
            )
            self._reconnect()

    def on_close(self, ws, close_status_code, close_msg):
        self.logger.info(
            "WebSocket connection closed with code: %s, message: %s",
            close_status_code,
            close_msg,
        )
        self.state = WebSocketState.DISCONNECTED

    def on_ping(self, ws, message):
        self.logger.debug("Ping received")

    def on_pong(self, ws, message):
        self.logger.debug("Pong received")

    def subscribe(self, subscription):
        message = {
            "type": "SUBSCRIBE",
            "channels": [subscription],
        }
        with self.lock:
            if subscription not in self.subscriptions:
                self.subscriptions.append(subscription)
            if self.state == WebSocketState.AUTHENTICATED:
                self.ws.send(json.dumps(message))
                self.logger.info("Sent subscription message: %s", json.dumps(message))

    def unsubscribe(self, subscription):
        message = {
            "type": "UNSUBSCRIBE",
            "channels": [subscription],
        }
        with self.lock:
            if subscription in self.subscriptions:
                self.subscriptions.remove(subscription)
            if self.state == WebSocketState.AUTHENTICATED:
                self.ws.send(json.dumps(message))
                self.logger.info("Sent unsubscription message: %s", json.dumps(message))

    def close(self):
        self.should_run = False
        if self.ws:
            self.ws.close()
        if hasattr(self, "thread"):
            self.thread.join()
        self.logger.info("WebSocket closed and thread joined")
