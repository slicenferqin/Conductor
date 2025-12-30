"""Task Decomposer - Breaks down requirements into actionable plan."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Plan:
    """A development plan."""
    requirement: str
    features: list[str]
    tech_stack: dict[str, str]
    stages: list[dict[str, Any]]
    estimated_time: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requirement": self.requirement,
            "features": self.features,
            "tech_stack": self.tech_stack,
            "stages": self.stages,
            "estimated_time": self.estimated_time,
        }


class TaskDecomposer:
    """Decomposes requirements into development plans."""

    # Fixed tech stack for MVP
    DEFAULT_TECH_STACK = {
        "backend": "FastAPI + SQLAlchemy + PostgreSQL",
        "frontend": "React + TypeScript + TailwindCSS",
        "testing": "pytest + Playwright",
        "deployment": "Docker + docker-compose",
    }

    async def decompose(self, requirement: str) -> Plan:
        """Decompose a requirement into a development plan."""
        # TODO: Use Claude to analyze requirement and generate plan
        # This is a placeholder implementation

        features = await self._extract_features(requirement)
        stages = self._create_stages(features)

        return Plan(
            requirement=requirement,
            features=features,
            tech_stack=self.DEFAULT_TECH_STACK,
            stages=stages,
            estimated_time="15-20 minutes",
        )

    async def _extract_features(self, requirement: str) -> list[str]:
        """Extract features from requirement."""
        # TODO: Use Claude to extract features
        # Placeholder
        return [
            "User authentication (register/login/logout)",
            "Core CRUD operations",
            "Data persistence",
        ]

    def _create_stages(self, features: list[str]) -> list[dict[str, Any]]:
        """Create execution stages based on features."""
        return [
            {
                "name": "design",
                "description": "Architecture and API design",
                "outputs": ["prd.md", "architecture.md", "api_design.md"],
            },
            {
                "name": "backend",
                "description": "Backend API implementation",
                "outputs": ["backend/"],
            },
            {
                "name": "frontend",
                "description": "Frontend UI implementation",
                "outputs": ["frontend/"],
            },
            {
                "name": "testing",
                "description": "Testing and bug fixes",
                "outputs": ["tests/"],
            },
            {
                "name": "delivery",
                "description": "Final packaging",
                "outputs": ["docker-compose.yml", "README.md"],
            },
        ]