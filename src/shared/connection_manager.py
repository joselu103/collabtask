# src/shared/connection_manager.py

import uuid
from collections import defaultdict

from fastapi import FastAPI, WebSocket


# Manager
class ConnectionManager:
    def __init__(self):
        self.connections: dict[uuid.UUID, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, room_id: uuid.UUID) -> None:
        """Accept and register a new connection in the provided room.

        Args:
            websocket: new websocket instance.
            room_id: uuid of the room to which the websocket must be
                asigned.
        """
        await websocket.accept()
        self.connections[room_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, room_id: uuid.UUID) -> None:
        """Discard a connection from the provided room.

        If the room is empty, it cleans it up.

        Args:
            websocket: the websocket instance to discard.
            room_id: uuid of the room where it is currently living.
        """
        room = self.connections.get(room_id)

        if room is None:
            return

        room.remove(websocket)

        if not room:
            self.connections.pop(room_id)

    async def broadcast(self, message: dict, room_id: uuid.UUID) -> None:
        """Send JSON to all connections in the room

        Args:
            message: JSON to broadcast.
            room_id: uuid of the room where to broadcast the message.
        """
        room = self.connections.get(room_id)

        if room is None:
            return

        for websocket in room.copy():
            try:
                await websocket.send_json(message)
            except RuntimeError:
                room.remove(websocket)


def init_cm(app: FastAPI) -> None:
    """Instantiate a ConnectionManager and store it in the app state.

    Intended to be called on startup.

    Args:
        app: FastAPI app instance.
    """
    app.state.connection_manager = ConnectionManager()


async def dispose_cm(app: FastAPI) -> None:
    """Cleanup ConnectionManager instance from the app state.

    Intended to be called on shutdown.

    Args:
        app: FastAPI app instance.
    """
    cm: ConnectionManager = app.state.connection_manager
    for connections in cm.connections.values():
        for websocket in connections:
            await websocket.close()
    app.state.connection_manager = None
