import time
import json
import asyncio
import pytest
import threading
import websockets
import lmax_python_sdk


class TestWebSocketServer:
    """A test WebSocket server to simulate various scenarios."""

    def __init__(self):
        self.clients = set()
        self.server = None
        self.should_disconnect = False
        self.should_shutdown = False

    async def handler(self, websocket, path):
        self.clients.add(websocket)
        try:
            while not self.should_shutdown:
                if self.should_disconnect:
                    await websocket.close()
                    self.should_disconnect = False
                    continue
                async for message in websocket:
                    data = json.loads(message)
                    if data.get("type") == "AUTH":
                        if data.get("token") == "valid_token":
                            await websocket.send(json.dumps({"type": "AUTH_SUCCESS"}))
                        else:
                            await websocket.send(json.dumps({"type": "AUTH_FAILURE"}))
                            await websocket.close()
                    else:
                        await websocket.send(
                            json.dumps({"type": "ECHO", "message": data})
                        )
        finally:
            self.clients.remove(websocket)

    async def start(self):
        self.server = await websockets.serve(self.handler, "localhost", 8765)
        await self.server.wait_closed()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start())

    def disconnect_clients(self):
        self.should_disconnect = True

    def shutdown_server(self):
        self.should_shutdown = True
        for ws in list(self.clients):  # Iterate over a copy of the clients set
            asyncio.run_coroutine_threadsafe(ws.close(), asyncio.get_event_loop())
        if self.server:
            self.server.close()
            asyncio.run_coroutine_threadsafe(
                self.server.wait_closed(), asyncio.get_event_loop()
            )


@pytest.fixture(scope="module")
def websocket_server():
    server = TestWebSocketServer()
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    time.sleep(1)  # Give the server a moment to start
    yield server
    server.shutdown_server()


class TestLMAXWebSocketClientSync(lmax_python_sdk.ws_client_sync.LMAXWebSocketClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws_url = "ws://localhost:8765"

    def _authenticate(self):
        """Override the authentication method for testing."""
        return "valid_token"


class TestLMAXWebSocketClientAsync(lmax_python_sdk.ws_client_async.LMAXWebSocketClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws_url = "ws://localhost:8765"

    def _authenticate(self):
        """Override the authentication method for testing."""
        return "valid_token"


@pytest.mark.asyncio
async def test_websocket_client_normal_operation_sync(websocket_server):
    client = TestLMAXWebSocketClientSync(
        client_key_id="test_key",
        secret="test_secret",
        base_url="ws://localhost:8765",
        verbose=True,
    )
    client.connect()
    client.subscribe({"name": "TRADE", "instruments": ["EUR-USD"]})

    # Wait for a bit to receive messages
    await asyncio.sleep(5)

    assert client.state == lmax_python_sdk.ws_client_sync.WebSocketState.AUTHENTICATED


@pytest.mark.asyncio
async def test_websocket_client_network_disconnect_sync(websocket_server):
    client = TestLMAXWebSocketClientSync(
        client_key_id="test_key",
        secret="test_secret",
        base_url="ws://localhost:8765",
        verbose=True,
    )
    client.connect()
    client.subscribe({"name": "TRADE", "instruments": ["EUR-USD"]})

    # Simulate network disconnect
    websocket_server.disconnect_clients()
    await asyncio.sleep(5)

    # Wait for reconnection
    await asyncio.sleep(10)

    assert client.state == lmax_python_sdk.ws_client_sync.WebSocketState.AUTHENTICATED


@pytest.mark.asyncio
async def test_websocket_client_server_downtime_sync(websocket_server):
    client = TestLMAXWebSocketClientSync(
        client_key_id="test_key",
        secret="test_secret",
        base_url="ws://localhost:8765",
        verbose=True,
    )
    client.connect()
    client.subscribe({"name": "TRADE", "instruments": ["EUR-USD"]})

    # Simulate server downtime
    websocket_server.shutdown_server()
    await asyncio.sleep(5)

    # Restart server
    websocket_server.should_shutdown = False
    server_thread = threading.Thread(target=websocket_server.run, daemon=True)
    server_thread.start()
    await asyncio.sleep(5)

    # Wait for reconnection
    await asyncio.sleep(20)

    assert client.state == lmax_python_sdk.ws_client_sync.WebSocketState.AUTHENTICATED


@pytest.mark.asyncio
async def test_websocket_client_side_error_sync():
    client = TestLMAXWebSocketClientSync(
        client_key_id="test_key",
        secret="test_secret",
        base_url="ws://localhost:8765",
        verbose=True,
    )
    client.connect()
    client.subscribe({"name": "TRADE", "instruments": ["EUR-USD"]})

    # Simulate client-side error by closing the WebSocket abruptly
    await asyncio.get_event_loop().run_in_executor(None, client.ws.close)
    await asyncio.sleep(5)

    # Wait for reconnection
    await asyncio.sleep(10)

    assert client.state == lmax_python_sdk.ws_client_sync.WebSocketState.AUTHENTICATED


@pytest.mark.asyncio
async def test_websocket_client_normal_operation_async(websocket_server):
    client = TestLMAXWebSocketClientAsync(
        client_key_id="test_key",
        secret="test_secret",
        base_url="ws://localhost:8765",
        verbose=True,
    )
    await client.subscribe({"name": "TRADE", "instruments": ["EUR-USD"]})
    task = asyncio.create_task(client.connect())

    # Wait for a bit to receive messages
    await asyncio.sleep(5)

    assert client.state == lmax_python_sdk.ws_client_async.WebSocketState.AUTHENTICATED


@pytest.mark.asyncio
async def test_websocket_client_network_disconnect_async(websocket_server):
    client = TestLMAXWebSocketClientAsync(
        client_key_id="test_key",
        secret="test_secret",
        base_url="ws://localhost:8765",
        verbose=True,
    )
    await client.subscribe({"name": "TRADE", "instruments": ["EUR-USD"]})
    task = asyncio.create_task(client.connect())

    # Simulate network disconnect
    websocket_server.disconnect_clients()

    # Wait for reconnection
    await asyncio.sleep(10)

    assert client.state == lmax_python_sdk.ws_client_async.WebSocketState.AUTHENTICATED


@pytest.mark.asyncio
async def test_websocket_client_server_downtime_async(websocket_server):
    client = TestLMAXWebSocketClientAsync(
        client_key_id="test_key",
        secret="test_secret",
        base_url="ws://localhost:8765",
        verbose=True,
    )
    await client.subscribe({"name": "TRADE", "instruments": ["EUR-USD"]})
    task = asyncio.create_task(client.connect())

    # Simulate server downtime
    websocket_server.shutdown_server()
    await asyncio.sleep(5)

    # Restart server
    websocket_server.should_shutdown = False
    server_thread = threading.Thread(target=websocket_server.run, daemon=True)
    server_thread.start()
    await asyncio.sleep(5)

    # Wait for reconnection
    await asyncio.sleep(10)

    assert client.state == lmax_python_sdk.ws_client_async.WebSocketState.AUTHENTICATED


@pytest.mark.asyncio
async def test_websocket_client_side_error_async():
    client = TestLMAXWebSocketClientAsync(
        client_key_id="test_key",
        secret="test_secret",
        base_url="ws://localhost:8765",
        verbose=True,
    )
    await client.subscribe({"name": "TRADE", "instruments": ["EUR-USD"]})
    task = asyncio.create_task(client.connect())
    await asyncio.sleep(5)

    # Simulate client-side error by closing the WebSocket abruptly
    await client.ws.close()
    await asyncio.sleep(5)

    # Wait for reconnection
    await asyncio.sleep(10)

    assert client.state == lmax_python_sdk.ws_client_async.WebSocketState.AUTHENTICATED


if __name__ == "__main__":
    pytest.main([__file__])
