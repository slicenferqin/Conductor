"""Agent and TeamMember schemas."""

from enum import Enum
from pydantic import BaseModel


class AgentStatusAPI(str, Enum):
    """Agent status matching frontend types."""
    ONLINE = "ONLINE"
    WORKING = "WORKING"
    WAITING = "WAITING"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"


class AgentRoleSchema(BaseModel):
    """Agent role definition."""
    id: str
    name: str
    emoji: str
    description: str


class TeamMemberSchema(BaseModel):
    """Team member (agent instance) schema."""
    id: str
    role: AgentRoleSchema
    status: AgentStatusAPI
    currentAction: str | None = None
    progress: int | None = None
    errorMessage: str | None = None
