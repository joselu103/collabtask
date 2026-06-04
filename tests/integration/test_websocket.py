# tests/integration/test_websocket

import uuid

import pytest
from httpx import AsyncClient
from httpx_ws import WebSocketDisconnect, aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport

from src.shared.connection_manager import ConnectionManager, dispose_cm, init_cm

# ASGIWebSocketTransport is intentionally not extracted to a fixture.
# anyio + Python 3.14 bug: cancel scope created in fixture task exits in a
# different task during teardown, raising RuntimeError. Keeping the transport
# inside the test function avoids this.


async def test_ws_connection(app, test_setup):
    _, organization, project, access_token = (
        test_setup.user,
        test_setup.organization,
        test_setup.project,
        test_setup.access_token,
    )
    url = f"http://test/api/v1/organizations/{organization.id}/projects/{project.id}/ws?token={access_token}"
    message = {
        "type": "notification",
        "payload": {"title": "General warning", "content": "This is a test"},
    }
    init_cm(app)

    # When
    try:
        async with AsyncClient(
            transport=ASGIWebSocketTransport(app=app), base_url="http://test"
        ) as client_ws:
            async with aconnect_ws(url, client_ws) as ws:
                await ws.send_json(message)
                notification = await ws.receive_json(timeout=1)

        # Then
        cm: ConnectionManager = app.state.connection_manager
        assert message == notification
        assert project.id not in cm.connections.keys()

    finally:
        await dispose_cm(app)


async def test_ws_connection_validation_error(app, test_setup):
    _, organization, _, access_token = (
        test_setup.user,
        test_setup.organization,
        test_setup.project,
        test_setup.access_token,
    )
    # random project id
    url = f"http://test/api/v1/organizations/{organization.id}/projects/{uuid.uuid4()}/ws?token={access_token}"

    init_cm(app)

    try:
        async with AsyncClient(
            transport=ASGIWebSocketTransport(app=app), base_url="http://test"
        ) as client_ws:
            # Then
            async with aconnect_ws(url, client_ws) as ws:
                with pytest.raises(
                    WebSocketDisconnect, match="Project does not exist"
                ) as exc_info:
                    await ws.receive_json(timeout=1)  # When
            assert exc_info.value.code == 1008
    finally:
        await dispose_cm(app)
