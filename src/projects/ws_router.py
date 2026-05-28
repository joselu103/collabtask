# src/projects/ws_router.py
import uuid

from fastapi import APIRouter, WebSocket, WebSocketException
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.organizations.models import MemberRole
from src.organizations.permissions import check_role
from src.organizations.repository import OrganizationMemberRepository
from src.projects.service import ProjectNotFound, ProjectService
from src.shared.connection_manager import ConnectionManager
from src.shared.exceptions import InsufficientPermissionError
from src.shared.schemas import WSMessage
from src.shared.websocket_auth import WebSocketAuthError, authenticate_websocket

router = APIRouter(prefix="/{project_id}/ws", tags=["websocket"])


@router.websocket("")
async def start_connection(
    project_id: uuid.UUID,
    token: str,
    websocket: WebSocket,
):
    """"""
    cm: ConnectionManager = websocket.app.state.connection_manager

    # Validation
    session_factory: async_sessionmaker = websocket.app.state.session_factory

    async with session_factory() as session:
        try:
            user = await authenticate_websocket(token=token, session=session)
        except WebSocketAuthError:
            raise WebSocketException(1008, "Authentication failure")

        try:
            project = await ProjectService(session).get_project(project_id)
        except ProjectNotFound:
            raise WebSocketException(1008, "Project does not exist")

        try:
            await check_role(
                member_repo=OrganizationMemberRepository(session),
                user_id=user.id,
                organization_id=project.organization_id,
                min_role=MemberRole.MEMBER,
            )
        except InsufficientPermissionError:
            raise WebSocketException(1008, "User is not a member of the organization")

    try:
        # Start connection
        await cm.connect(websocket=websocket, room_id=project_id)

        # Websocket loop
        while True:
            raw = await websocket.receive_json()
            message = WSMessage.model_validate(raw)
            await cm.broadcast(message=message.model_dump(), room_id=project_id)

    finally:
        # Close connection
        await cm.disconnect(websocket=websocket, room_id=project_id)
