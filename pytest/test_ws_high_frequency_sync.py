import json
import time
import uuid
import pytest
import asyncio
import threading
import websockets
import lmax_python_sdk.ws_client_async


class HighFrequencyTestWebSocketServer:
    def __init__(self):
        self.clients = set()
        self.server = None
        self.should_shutdown = False
        self.sent_messages = []

    async def handler(self, websocket, path):
        self.clients.add(websocket)
        start_time = time.perf_counter_ns()
        for _ in range(100000):
            if self.should_shutdown:
                break
            message = {
                "type": "TRADE_EVENT",
                "timestamp": int(time.time() * 1000),
                "id": str(uuid.uuid4()),
                "price": round(1.1000 + (0.0001 * len(self.sent_messages)), 4),
                "quantity": round(100000 + (100 * len(self.sent_messages)), 2),
            }
            self.sent_messages.append(message)
        print("Elapsed time:", (time.perf_counter_ns() - start_time) / 1e9)
        try:
            await websocket.send(json.dumps({"type": "AUTH_SUCCESS"}))
            for msg in self.sent_messages:
                await websocket.send(json.dumps(msg))
                if self.should_shutdown:
                    break
        finally:
            self.clients.remove(websocket)

    async def start(self):
        self.server = await websockets.serve(self.handler, "localhost", 8766)
        await self.server.wait_closed()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start())

    def shutdown_server(self):
        self.should_shutdown = True
        if self.server:
            self.server.close()
            asyncio.run_coroutine_threadsafe(
                self.server.wait_closed(), asyncio.get_event_loop()
            )


@pytest.fixture(scope="function")
def high_frequency_websocket_server():
    server = HighFrequencyTestWebSocketServer()
    server_thread = threading.Thread(target=server.run, daemon=False)
    server_thread.start()
    time.sleep(1)  # Give the server a moment to start
    yield server
    server.shutdown_server()


class HighFrequencyTestLMAXWebSocketClient(
    lmax_python_sdk.ws_client_sync.LMAXWebSocketClient
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws_url = "ws://localhost:8766"
        self.received_messages = []

    def on_message(self, ws, message):
        data = json.loads(message)
        if data.get("type") == "TRADE_EVENT":
            self.received_messages.append(data)

    def _authenticate(self):
        """Override the authentication method for testing."""
        return "valid_token"


@pytest.mark.asyncio
async def test_high_frequency_message_reception(high_frequency_websocket_server):
    client = HighFrequencyTestLMAXWebSocketClient(
        client_key_id="test_key",
        secret="test_secret",
        base_url="ws://localhost:8766",
        verbose=True,
    )

    # Start the connection process in a separate task
    client.connect()

    # Wait for messages to be sent and received
    time.sleep(12)

    # Close the client connection
    client.close()

    # Assertions
    assert (
        len(client.received_messages) == 1000
    ), f"Expected 1000 messages, but received {len(client.received_messages)}"
    assert (
        len(client.received_messages) == 1000
    ), f"Expected 1000 messages, but received {len(client.received_messages)}"

    # Verify message content
    for sent, received in zip(
        high_frequency_websocket_server.sent_messages, client.received_messages
    ):
        assert (
            sent == received
        ), f"Mismatch in messages: sent {sent}, received {received}"

    # Verify message order
    for i in range(1, len(client.received_messages)):
        assert (
            client.received_messages[i]["timestamp"]
            >= client.received_messages[i - 1]["timestamp"]
        ), "Messages are not in order"
        assert (
            client.received_messages[i]["price"]
            > client.received_messages[i - 1]["price"]
        ), "Price is not increasing"
        assert (
            client.received_messages[i]["quantity"]
            > client.received_messages[i - 1]["quantity"]
        ), "Quantity is not increasing"

    print(
        f"Successfully received and verified {len(client.received_messages)} messages"
    )
