"""Project schemas."""

from enum import Enum
from typing import Literal
from pydantic import BaseModel

from .agent import TeamMemberSchema


class ProjectStatusAPI(str, Enum):
    """Project status matching frontend types."""
    PLANNING = "PLANNING"
    FORMING = "FORMING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProjectCreate(BaseModel):
    """Request body for creating a project."""
    requirement: str


class ProjectResponse(BaseModel):
    """Project response schema."""
    id: str
    name: str
    requirement: str
    workspace: str
    status: ProjectStatusAPI
    team: list[TeamMemberSchema]
    createdAt: str
    lastUpdated: str | None = None
    duration: int | None = None


class ProjectUpdate(BaseModel):
    """Request body for updating project status."""
    action: Literal["pause", "resume", "stop"]
