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
        self.reconnect_event = threading.Event()
        self.subscriptions: typing.List[str] = []
        self.pending_subscriptions: typing.List[str] = []
        self.pending_unsubscriptions: typing.List[str] = []
        self.reconnect_delay: int = 5  # seconds
        self.should_run = True

    def _set_state(self, new_state: WebSocketState):
        self.state = new_state
        self.logger.info("State changed to: %s", self.state)

    def connect(self):
        self._set_state(WebSocketState.CONNECTING)
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
                self.logger.info("WebSocketApp started")
                break
            except Exception as e:  # pylint: disable=broad-except
                self.logger.error("Error connecting WebSocket: %s", e)
                time.sleep(self.reconnect_delay)

    def _run_forever(self):
        while self.should_run:
            try:
                self.ws.run_forever(ping_interval=10, ping_timeout=5)
                if self.should_run:
                    self.logger.info("WebSocket disconnected. Reconnecting...")
                    self._reconnect()
            except BrokenPipeError as e:
                self.logger.error("WebSocket run_forever error (Broken pipe): %s", e)
            except Exception as e:  # pylint: disable=broad-except
                self.logger.error("WebSocket run_forever error: %s", e)
            finally:
                if self.should_run:
                    self.logger.info("WebSocket disconnected. Reconnecting...")
                    self._reconnect()

    def _reconnect(self):
        self._set_state(WebSocketState.CONNECTING)
        self._refresh_token()
        if self.ws:
            self.ws.header = {"Authorization": f"Bearer {self.token}"}
        self._set_state(WebSocketState.AUTHENTICATED)
        self.reconnect_event.set()
        time.sleep(self.reconnect_delay)
        self.reconnect_event.clear()

    def _refresh_token(self):
        try:
            self.token = self._authenticate()
            self.logger.info("Token refreshed successfully.")
            self.reconnect_delay = 5  # Reset reconnect delay after successful refresh
        except Exception as e:  # pylint: disable=broad-except
            self.logger.error("Failed to refresh token: %s", e)
            self.reconnect_delay = min(self.reconnect_delay * 2, 60)

    def on_open(self, ws):
        self._set_state(WebSocketState.CONNECTED)
        self.logger.info("WebSocket connection opened.")
        self._set_state(WebSocketState.AUTHENTICATED)
        self._process_pending_subscriptions()

    def on_message(self, ws, message):
        self.logger.debug("Received raw message: %s", message)
        try:
            data = json.loads(message)
            self.logger.debug("Processed message: %s", data)
        except json.JSONDecodeError as e:
            self.logger.error("Failed to decode message: %s", e)

    def on_error(self, ws, error):
        self.logger.error("WebSocket error: %s", error)
        if isinstance(error, websocket.WebSocketException):
            if error.status_code == 401:
                self.logger.error(
                    "Error: 401 Unauthorized. Refreshing token and reconnecting."
                )
                self._reconnect()
            else:
                self.logger.error("WebSocket bad status: %s", error.status_code)
        self._set_state(WebSocketState.DISCONNECTED)

    def on_close(self, ws, close_status_code, close_msg):
        self.logger.info(
            "WebSocket connection closed with code: %s, message: %s",
            close_status_code,
            close_msg,
        )
        self._set_state(WebSocketState.DISCONNECTED)
        if self.should_run and not self.reconnect_event.is_set():
            self.logger.info("Attempting to reconnect...")
            self._reconnect()

    def on_ping(self, ws, message):
        self.logger.debug("Ping received")

    def on_pong(self, ws, message):
        self.logger.debug("Pong received")

    def _send_subscription(self, subscription):
        message = {
            "type": "SUBSCRIBE",
            "channels": [subscription],
        }
        self.ws.send(json.dumps(message))
        self.logger.info("Sent subscription message: %s", json.dumps(message))

    def _send_unsubscription(self, subscription):
        message = {
            "type": "UNSUBSCRIBE",
            "channels": [subscription],
        }
        self.ws.send(json.dumps(message))
        self.logger.info("Sent unsubscription message: %s", json.dumps(message))

    def _process_pending_subscriptions(self):
        with self.lock:
            for subscription in self.pending_subscriptions:
                self._send_subscription(subscription)
                self.subscriptions.append(subscription)
            self.pending_subscriptions.clear()

            for unsubscription in self.pending_unsubscriptions:
                if unsubscription in self.subscriptions:
                    self._send_unsubscription(unsubscription)
                    self.subscriptions.remove(unsubscription)
            self.pending_unsubscriptions.clear()

    def subscribe(self, subscription):
        with self.lock:
            if (
                subscription not in self.subscriptions
                and subscription not in self.pending_subscriptions
            ):
                if self.state == WebSocketState.AUTHENTICATED:
                    self._send_subscription(subscription)
                    self.subscriptions.append(subscription)
                else:
                    self.pending_subscriptions.append(subscription)
                    self.logger.info("Queued subscription for later: %s", subscription)

    def unsubscribe(self, subscription):
        with self.lock:
            if subscription in self.subscriptions:
                if self.state == WebSocketState.AUTHENTICATED:
                    self._send_unsubscription(subscription)
                    self.subscriptions.remove(subscription)
                else:
                    self.pending_unsubscriptions.append(subscription)
                    self.logger.info(
                        "Queued unsubscription for later: %s", subscription
                    )
            elif subscription in self.pending_subscriptions:
                self.pending_subscriptions.remove(subscription)
                self.logger.info("Removed pending subscription: %s", subscription)

    def close(self):
        self.should_run = False
        if self.ws:
            self.ws.close()
        if hasattr(self, "thread"):
            self.thread.join()
        self.logger.info("WebSocket closed and thread joined")
