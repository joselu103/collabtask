# src/projects/ws_router.py
import uuid

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.organizations.models import MemberRole
from src.organizations.permissions import check_role
from src.organizations.repository import OrganizationMemberRepository
from src.projects.service import ProjectNotFound, ProjectService
from src.shared.connection_manager import ConnectionManager
from src.shared.exceptions import InsufficientPermissionError
from src.shared.schemas import WSMessage
from src.shared.websocket_auth import WebSocketAuthError, authenticate_websocket

logger = structlog.get_logger()

router = APIRouter(prefix="/{project_id}/ws", tags=["websocket"])


@router.websocket("")
async def start_connection(
    org_id: uuid.UUID,  # From parent router (projects)
    project_id: uuid.UUID,
    token: str,
    websocket: WebSocket,
) -> None:
    """Open a websocket connection associated to a project.

    It allows to broadcast messages to the rest of connected members.

    Raises:
        WebSocketException(1008): if the user or project could not be verified.
    """
    # Accept the handshake
    await websocket.accept()

    # Validation
    session_factory: async_sessionmaker = websocket.app.state.session_factory
    async with session_factory() as session:
        try:
            user = await authenticate_websocket(token=token, session=session)
        except WebSocketAuthError:
            await websocket.close(1008, "Authentication failure")
            return

        try:
            await check_role(
                member_repo=OrganizationMemberRepository(session),
                user_id=user.id,
                organization_id=org_id,
                min_role=MemberRole.MEMBER,
            )
        except InsufficientPermissionError:
            await websocket.close(1008, "User is not a member of the organization")
            return

        try:
            project = await ProjectService(session).get_project(project_id)
        except ProjectNotFound:
            await websocket.close(1008, "Project does not exist")
            return

        if project.organization_id != org_id:
            await websocket.close(1008, "Wrong project or organization id")
            return

    try:
        # Start connection
        cm: ConnectionManager = websocket.app.state.connection_manager
        await cm.connect(websocket=websocket, room_id=project_id)

        # Websocket loop
        while True:
            raw = await websocket.receive_json()
            try:
                message = WSMessage.model_validate(raw)
                await cm.broadcast(message=message.model_dump(), room_id=project_id)
            except ValidationError:
                await logger.aexception(f"Invalid message format: {raw}")

    except WebSocketDisconnect:
        pass  # normal client disconnect, handled in finally

    finally:
        # Connection closed -> disconnect
        await cm.disconnect(websocket=websocket, room_id=project_id)
