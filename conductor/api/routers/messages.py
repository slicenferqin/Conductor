"""Messages REST API endpoints."""

import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..schemas import MessageSchema, MessageCreate, MessageType
from ..state import app_state
from ..websocket import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/messages", tags=["messages"])


@router.get("", response_model=list[MessageSchema])
async def get_messages(project_id: str, limit: int = 100, offset: int = 0):
    """Get messages for a project."""
    project = app_state.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    messages = app_state.get_messages(project_id)
    return messages[offset:offset + limit]


@router.post("", response_model=MessageSchema)
async def send_message(project_id: str, data: MessageCreate):
    """Send a user message to the project."""
    project = app_state.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create message
    message = MessageSchema(
        id=str(uuid.uuid4()),
        projectId=project_id,
        fromId="user",
        fromName="User",
        content=data.content,
        mentions=data.mentions,
        attachments=[],
        timestamp=datetime.now().isoformat(),
        type=MessageType.USER,
    )

    # Store message
    app_state.add_message(project_id, message)

    # Broadcast via WebSocket
    await connection_manager.broadcast_to_project(
        project_id,
        {
            "type": "new_message",
            "payload": message.model_dump(),
        }
    )

    # Inject message into orchestrator if project is running
    from ..services.orchestrator_bridge import orchestrator_bridge
    await orchestrator_bridge.inject_user_message(project_id, message)

    return message
