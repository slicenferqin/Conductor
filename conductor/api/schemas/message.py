"""Message schemas."""

from enum import Enum
from pydantic import BaseModel


class MessageType(str, Enum):
    """Message type matching frontend types."""
    USER = "user"
    AGENT = "agent"
    PROGRESS = "progress"
    SYSTEM = "system"


class MessageSchema(BaseModel):
    """Message schema."""
    id: str
    projectId: str
    fromId: str
    fromName: str
    content: str
    mentions: list[str]
    attachments: list[str]
    timestamp: str
    type: MessageType


class MessageCreate(BaseModel):
    """Request body for sending a message."""
    content: str
    mentions: list[str] = []
