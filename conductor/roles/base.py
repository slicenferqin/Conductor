"""Base role definitions."""

from dataclasses import dataclass, field
from enum import Enum


class RoleType(Enum):
    """Available role types."""
    PM = "pm"
    ARCHITECT = "architect"
    BACKEND = "backend"
    FRONTEND = "frontend"
    TESTER = "tester"


@dataclass
class Role:
    """A role that an AI agent can assume."""
    type: RoleType
    name: str
    description: str
    skills: list[str] = field(default_factory=list)
    system_prompt: str = ""

    def get_prompt_prefix(self) -> str:
        """Get the prompt prefix for this role."""
        return f"""You are acting as a {self.name}.
{self.description}

Your skills include: {', '.join(self.skills)}

{self.system_prompt}
"""


# Pre-defined roles
ROLES: dict[RoleType, Role] = {
    RoleType.PM: Role(
        type=RoleType.PM,
        name="Product Manager",
        description="You analyze requirements and write clear PRDs.",
        skills=["Requirement analysis", "User story writing", "PRD creation"],
        system_prompt="Focus on clarity and completeness. Break down requirements into specific features.",
    ),
    RoleType.ARCHITECT: Role(
        type=RoleType.ARCHITECT,
        name="Software Architect",
        description="You design system architecture and API specifications.",
        skills=["System design", "API design", "Database modeling", "Tech stack selection"],
        system_prompt="Design for simplicity and maintainability. Create clear API contracts.",
    ),
    RoleType.BACKEND: Role(
        type=RoleType.BACKEND,
        name="Backend Developer",
        description="You implement backend APIs using FastAPI and SQLAlchemy.",
        skills=["FastAPI", "SQLAlchemy", "PostgreSQL", "REST API", "pytest"],
        system_prompt="Write clean, tested code. Follow FastAPI best practices.",
    ),
    RoleType.FRONTEND: Role(
        type=RoleType.FRONTEND,
        name="Frontend Developer",
        description="You implement frontend UIs using React and TypeScript.",
        skills=["React", "TypeScript", "TailwindCSS", "Zustand", "Axios"],
        system_prompt="Create responsive, accessible UIs. Use TypeScript strictly.",
    ),
    RoleType.TESTER: Role(
        type=RoleType.TESTER,
        name="Test Engineer",
        description="You write and run tests to ensure quality.",
        skills=["pytest", "Playwright", "E2E testing", "API testing"],
        system_prompt="Ensure comprehensive test coverage. Write both unit and integration tests.",
    ),
}


def get_role(role_type: RoleType) -> Role:
    """Get a role by type."""
    return ROLES[role_type]