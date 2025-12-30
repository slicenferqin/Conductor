"""Task Queue - Manages pending and running tasks."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class TaskStatus(Enum):
    """Task status enum."""
    PENDING = "pending"
    PLAN_REVIEW = "plan_review"  # Waiting for user to confirm plan
    RUNNING = "running"
    PAUSED = "paused"
    NEED_HELP = "need_help"  # Stuck, needs human intervention
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStage(Enum):
    """Task execution stage."""
    PLANNING = "planning"
    DESIGN = "design"
    BACKEND = "backend"
    FRONTEND = "frontend"
    TESTING = "testing"
    DELIVERY = "delivery"


@dataclass
class Task:
    """A development task."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    requirement: str = ""
    status: TaskStatus = TaskStatus.PENDING
    stage: TaskStage = TaskStage.PLANNING
    progress: int = 0  # 0-100
    plan: dict[str, Any] | None = None
    output_dir: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "requirement": self.requirement,
            "status": self.status.value,
            "stage": self.stage.value,
            "progress": self.progress,
            "plan": self.plan,
            "output_dir": self.output_dir,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error": self.error,
        }


class TaskQueue:
    """In-memory task queue. TODO: Replace with persistent storage."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def add(self, task: Task) -> str:
        """Add a task to the queue."""
        self._tasks[task.id] = task
        return task.id

    def get(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def update(self, task: Task) -> None:
        """Update a task."""
        task.updated_at = datetime.now()
        self._tasks[task.id] = task

    def list_all(self) -> list[Task]:
        """List all tasks."""
        return list(self._tasks.values())

    def get_pending(self) -> list[Task]:
        """Get pending tasks."""
        return [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]