"""Base notification interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class NotificationType(Enum):
    """Notification type."""
    PLAN_READY = "plan_ready"
    PROGRESS = "progress"
    NEED_HELP = "need_help"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Notification:
    """A notification to send."""
    type: NotificationType
    title: str
    body: str
    task_id: str
    actions: list[dict[str, str]] | None = None  # e.g., [{"label": "Confirm", "url": "..."}]


class NotificationChannel(ABC):
    """Abstract notification channel."""

    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Send a notification. Returns True if successful."""
        pass


class TerminalNotification(NotificationChannel):
    """Terminal notification (prints to console)."""

    async def send(self, notification: Notification) -> bool:
        """Print notification to terminal."""
        print(f"\n{'='*50}")
        print(f"[{notification.type.value.upper()}] {notification.title}")
        print(f"Task: {notification.task_id}")
        print(f"\n{notification.body}")
        if notification.actions:
            print("\nActions:")
            for action in notification.actions:
                print(f"  - {action['label']}: {action.get('url', 'N/A')}")
        print(f"{'='*50}\n")
        return True