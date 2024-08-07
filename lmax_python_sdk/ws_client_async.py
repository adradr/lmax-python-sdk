import json
import enum
import time
import typing
import asyncio
import websockets
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
        self.ws: typing.Optional[websockets.WebSocketClientProtocol] = None
        self.subscriptions: typing.List[str] = []
        self.pending_subscriptions: typing.List[str] = []
        self.pending_unsubscriptions: typing.List[str] = []
        self.reconnect_delay: int = 5  # seconds
        self.should_run = True
        self.message_queue = asyncio.Queue()
        self.reconnect_event = asyncio.Event()

    def _set_state(self, new_state: WebSocketState):
        self.state = new_state
        self.logger.info("State changed to: %s", self.state.name)

    async def _ensure_connection(self):
        if self.state != WebSocketState.AUTHENTICATED:
            self._set_state(WebSocketState.CONNECTING)
            await self._refresh_token()
            try:
                self.ws = await websockets.connect(
                    self.ws_url, extra_headers={"Authorization": f"Bearer {self.token}"}
                )
                self._set_state(WebSocketState.CONNECTED)
                self.logger.info("WebSocket connection opened.")
                self._set_state(WebSocketState.AUTHENTICATED)
                await self._process_pending_subscriptions()
            except Exception as e:
                self.logger.error(f"Connection attempt failed: {e}")
                await self._reconnect()

    async def _reconnect(self):
        self.logger.info("Attempting to reconnect...")
        while self.should_run:
            self._set_state(WebSocketState.CONNECTING)
            try:
                if self.ws:
                    await self.ws.close()
                await asyncio.sleep(self.reconnect_delay)
                await self._ensure_connection()
                self.reconnect_delay = 5  # Reset delay after a successful reconnect
                return
            except Exception as e:
                self.logger.error(f"Reconnection attempt failed: {e}")
                self.reconnect_delay = min(self.reconnect_delay * 2, 60)

    async def connect(self):
        while self.should_run:
            try:
                await self._ensure_connection()
                self._process_queue()
                await asyncio.gather(
                    self._handle_messages(),
                    self._heartbeat(),
                )
            except websockets.ConnectionClosed:
                self.logger.error("WebSocket connection closed unexpectedly.")
                self._set_state(WebSocketState.DISCONNECTED)
                await self._reconnect()
            except Exception as e:
                self.logger.error(f"Error in WebSocket connection: {e}")
                self._set_state(WebSocketState.DISCONNECTED)
                await self._reconnect()

    async def _handle_messages(self):
        while self.should_run and self.state == WebSocketState.AUTHENTICATED:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=30)
                await self.on_message(message)
            except asyncio.TimeoutError:
                self.logger.warning("No message received for 30 seconds")
                await self._ensure_connection()
            except websockets.ConnectionClosed:
                self.logger.info("WebSocket connection closed.")
                break
            except Exception as e:
                self.logger.error(f"Error handling message: {e}")

        self._set_state(WebSocketState.DISCONNECTED)
        self.logger.info("Message handling stopped")

    async def _heartbeat(self):
        while self.should_run and self.state == WebSocketState.AUTHENTICATED:
            try:
                ping = await self.ws.ping()
                latency = await asyncio.wait_for(ping, timeout=5)
                self.logger.debug("Ping latency: %s", latency)
                await asyncio.sleep(10)
            except asyncio.TimeoutError:
                self.logger.warning("Heartbeat ping timed out")
                await self._ensure_connection()
            except websockets.ConnectionClosed:
                self.logger.error("WebSocket connection closed.")
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                break
        self._set_state(WebSocketState.DISCONNECTED)
        self.logger.info("Heartbeat stopped")

    async def _process_queue(self):
        try:
            message = await self.message_queue.get()
            await self._send_message(message)
            self.message_queue.task_done()
        except websockets.ConnectionClosed:
            self.logger.error("WebSocket connection closed.")
        except Exception as e:
            self.logger.error(f"Message queue error: {e}")

    async def _refresh_token(self):
        attempt = 0
        max_attempts = 5
        while attempt < max_attempts:
            try:
                self.token = self._authenticate()
                self.logger.info("Token refreshed successfully.")
                self.reconnect_delay = (
                    5  # Reset reconnect delay after successful refresh
                )
                return
            except ConnectionError as e:
                self.logger.error("Failed to refresh token: %s", e)
                self.reconnect_delay = min(self.reconnect_delay * 2, 60)
                attempt += 1
                time.sleep(self.reconnect_delay)
            except Exception as e:
                self.logger.error("Unexpected error refreshing token: %s", e)
                raise
        raise ConnectionError("Max retries exceeded for token refresh.")

    async def on_message(self, message):
        self.logger.debug("Received raw message: %s", message)
        try:
            data = json.loads(message)
            self.logger.debug("Processed message: %s", data)
            # Handle different message types here
        except json.JSONDecodeError as e:
            self.logger.error("Failed to decode message: %s", e)

    async def _send_message(self, message):
        if self.state == WebSocketState.AUTHENTICATED:
            await self.ws.send(json.dumps(message))
            self.logger.info("Sent message: %s", json.dumps(message))
        else:
            await self.message_queue.put(message)
            self.logger.info("Queued message for later: %s", json.dumps(message))

    async def _process_pending_subscriptions(self):
        for subscription in self.subscriptions:
            await self._send_subscription(subscription)

        for subscription in self.pending_subscriptions:
            await self._send_subscription(subscription)
            self.subscriptions.append(subscription)
        self.pending_subscriptions.clear()

        for unsubscription in self.pending_unsubscriptions:
            if unsubscription in self.subscriptions:
                await self._send_unsubscription(unsubscription)
                self.subscriptions.remove(unsubscription)
        self.pending_unsubscriptions.clear()

    async def _send_subscription(self, subscription):
        message = {
            "type": "SUBSCRIBE",
            "channels": [subscription],
        }
        await self._send_message(message)

    async def _send_unsubscription(self, subscription):
        message = {
            "type": "UNSUBSCRIBE",
            "channels": [subscription],
        }
        await self._send_message(message)

    async def subscribe(self, subscription: str):
        if (
            subscription not in self.subscriptions
            and subscription not in self.pending_subscriptions
        ):
            if self.state == WebSocketState.AUTHENTICATED:
                await self._send_subscription(subscription)
                self.subscriptions.append(subscription)
            else:
                self.pending_subscriptions.append(subscription)
                self.logger.info("Queued subscription for later: %s", subscription)

    async def unsubscribe(self, subscription: str):
        if subscription in self.subscriptions:
            if self.state == WebSocketState.AUTHENTICATED:
                await self._send_unsubscription(subscription)
                self.subscriptions.remove(subscription)
            else:
                self.pending_unsubscriptions.append(subscription)
                self.logger.info("Queued unsubscription for later: %s", subscription)
        elif subscription in self.pending_subscriptions:
            self.pending_subscriptions.remove(subscription)
            self.logger.info("Removed pending subscription: %s", subscription)

    async def close(self):
        self.should_run = False
        if self.ws:
            await self.ws.close()
        self.logger.info("WebSocket closed")
