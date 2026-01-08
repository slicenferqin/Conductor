"""WebSocket event schemas."""

from typing import Literal, Union
from pydantic import BaseModel

from .message import MessageSchema
from .project import ProjectResponse
from .agent import TeamMemberSchema


class AgentStatusChangedPayload(BaseModel):
    """Payload for agent status changed event."""
    projectId: str
    agentId: str
    status: str
    currentAction: str | None = None
    progress: int | None = None
    errorMessage: str | None = None


class AgentStatusChangedEvent(BaseModel):
    """Agent status changed WebSocket event."""
    type: Literal["agent_status_changed"] = "agent_status_changed"
    payload: AgentStatusChangedPayload


class NewMessageEvent(BaseModel):
    """New message WebSocket event."""
    type: Literal["new_message"] = "new_message"
    payload: MessageSchema


class ProjectCreatedEvent(BaseModel):
    """Project created WebSocket event."""
    type: Literal["project_created"] = "project_created"
    payload: ProjectResponse


class TeamFormedPayload(BaseModel):
    """Payload for team formed event."""
    projectId: str
    team: list[TeamMemberSchema]


class TeamFormedEvent(BaseModel):
    """Team formed WebSocket event."""
    type: Literal["team_formed"] = "team_formed"
    payload: TeamFormedPayload


class ProjectStatusChangedPayload(BaseModel):
    """Payload for project status changed event."""
    projectId: str
    status: str
    error: str | None = None


class ProjectStatusChangedEvent(BaseModel):
    """Project status changed WebSocket event."""
    type: Literal["project_status_changed"] = "project_status_changed"
    payload: ProjectStatusChangedPayload


WSEvent = Union[
    AgentStatusChangedEvent,
    NewMessageEvent,
    ProjectCreatedEvent,
    TeamFormedEvent,
    ProjectStatusChangedEvent,
]
