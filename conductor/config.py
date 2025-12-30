"""Conductor Configuration."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class CheckpointConfig:
    """Checkpoint configuration."""
    mode: str = "required"  # required, auto, optional
    timeout: int = 1800  # 30 minutes in seconds
    notify: bool = True
    max_fix_attempts: int = 3


@dataclass
class TechStackConfig:
    """Technology stack configuration."""
    backend: str = "FastAPI + SQLAlchemy + PostgreSQL"
    frontend: str = "React + TypeScript + TailwindCSS"
    testing: str = "pytest + Playwright"
    deployment: str = "Docker + docker-compose"


@dataclass
class Config:
    """Conductor configuration."""
    # Workspace settings
    workspace: Path = field(default_factory=lambda: Path.cwd() / "projects")

    # Claude Code settings
    claude_timeout: int = 300  # 5 minutes per stage

    # Checkpoints
    plan_checkpoint: CheckpointConfig = field(default_factory=lambda: CheckpointConfig(mode="required"))
    design_checkpoint: CheckpointConfig = field(default_factory=lambda: CheckpointConfig(mode="auto", notify=False))
    dev_checkpoint: CheckpointConfig = field(default_factory=lambda: CheckpointConfig(mode="auto", max_fix_attempts=3))
    delivery_checkpoint: CheckpointConfig = field(default_factory=lambda: CheckpointConfig(mode="required"))

    # Tech stack (fixed for MVP)
    tech_stack: TechStackConfig = field(default_factory=TechStackConfig)

    @classmethod
    def load(cls, config_path: str | None = None) -> "Config":
        """Load configuration from file or use defaults."""
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                data = yaml.safe_load(f)
                return cls._from_dict(data)

        # Try default locations
        default_paths = [
            Path.cwd() / ".conductor.yaml",
            Path.home() / ".conductor.yaml",
        ]

        for path in default_paths:
            if path.exists():
                with open(path) as f:
                    data = yaml.safe_load(f)
                    return cls._from_dict(data)

        return cls()

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        config = cls()

        if "workspace" in data:
            config.workspace = Path(data["workspace"])

        if "claude_timeout" in data:
            config.claude_timeout = data["claude_timeout"]

        if "tech_stack" in data:
            ts = data["tech_stack"]
            config.tech_stack = TechStackConfig(
                backend=ts.get("backend", config.tech_stack.backend),
                frontend=ts.get("frontend", config.tech_stack.frontend),
                testing=ts.get("testing", config.tech_stack.testing),
                deployment=ts.get("deployment", config.tech_stack.deployment),
            )

        return config


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config