"""Message Bus - Central communication hub for agents."""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from conductor.core.models import Message


@dataclass
class Subscriber:
    """A message subscriber."""
    id: str
    callback: Callable[[Message], None]
    filter_mentions: bool = False  # If True, only receive messages that @mention this subscriber


class MessageBus:
    """Central message bus for agent communication.

    Supports:
    - Broadcasting messages to all subscribers
    - Targeted messages via @mentions
    - Message persistence to workspace
    """

    def __init__(self, workspace: str | None = None):
        """Initialize message bus.

        Args:
            workspace: Optional workspace path for message persistence
        """
        self.workspace = Path(workspace) if workspace else None
        self._subscribers: dict[str, Subscriber] = {}
        self._messages: list[Message] = []
        self._lock = asyncio.Lock()

        # Create message storage if workspace provided
        if self.workspace:
            messages_dir = self.workspace / ".conductor" / "messages"
            messages_dir.mkdir(parents=True, exist_ok=True)

    def subscribe(
        self,
        subscriber_id: str,
        callback: Callable[[Message], None],
        filter_mentions: bool = False,
    ) -> None:
        """Subscribe to messages.

        Args:
            subscriber_id: Unique ID for this subscriber
            callback: Function to call when message received
            filter_mentions: If True, only receive messages that @mention this subscriber
        """
        self._subscribers[subscriber_id] = Subscriber(
            id=subscriber_id,
            callback=callback,
            filter_mentions=filter_mentions,
        )

    def unsubscribe(self, subscriber_id: str) -> None:
        """Unsubscribe from messages."""
        self._subscribers.pop(subscriber_id, None)

    async def publish(self, message: Message) -> None:
        """Publish a message to the bus.

        Args:
            message: The message to publish
        """
        async with self._lock:
            self._messages.append(message)

            # Persist message
            if self.workspace:
                self._persist_message(message)

            # Notify subscribers
            for subscriber in self._subscribers.values():
                # Check if subscriber should receive this message
                if subscriber.filter_mentions:
                    # Only send if subscriber is mentioned
                    if subscriber.id not in message.mentions:
                        continue

                try:
                    # Call the callback (may be async or sync)
                    result = subscriber.callback(message)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    print(f"Error notifying subscriber {subscriber.id}: {e}")

    def publish_sync(self, message: Message) -> None:
        """Synchronous publish for non-async contexts."""
        self._messages.append(message)
        if self.workspace:
            self._persist_message(message)

    def get_messages(
        self,
        project_id: str | None = None,
        limit: int | None = None,
    ) -> list[Message]:
        """Get messages, optionally filtered by project.

        Args:
            project_id: Filter by project ID
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        messages = self._messages
        if project_id:
            messages = [m for m in messages if m.project_id == project_id]
        if limit:
            messages = messages[-limit:]
        return messages

    def get_messages_for_agent(
        self,
        agent_id: str,
        project_id: str | None = None,
    ) -> list[Message]:
        """Get messages relevant to a specific agent.

        Returns messages that either:
        - Are broadcast (no specific mentions)
        - Mention this agent

        Args:
            agent_id: The agent's ID
            project_id: Filter by project ID

        Returns:
            List of relevant messages
        """
        messages = self._messages
        if project_id:
            messages = [m for m in messages if m.project_id == project_id]

        relevant = []
        for msg in messages:
            # Include if no mentions (broadcast) or if agent is mentioned
            if not msg.mentions or agent_id in msg.mentions:
                relevant.append(msg)

        return relevant

    def _persist_message(self, message: Message) -> None:
        """Persist message to file system."""
        if not self.workspace:
            return

        messages_dir = self.workspace / ".conductor" / "messages"
        messages_dir.mkdir(parents=True, exist_ok=True)

        # Append to messages log
        log_file = messages_dir / "chat.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            msg_data = {
                "id": message.id,
                "project_id": message.project_id,
                "from_id": message.from_id,
                "from_name": message.from_name,
                "content": message.content,
                "mentions": message.mentions,
                "attachments": message.attachments,
                "timestamp": message.timestamp.isoformat(),
            }
            f.write(json.dumps(msg_data, ensure_ascii=False) + "\n")

    def load_messages(self, project_id: str | None = None) -> list[Message]:
        """Load messages from persistence.

        Args:
            project_id: Filter by project ID

        Returns:
            List of loaded messages
        """
        if not self.workspace:
            return []

        log_file = self.workspace / ".conductor" / "messages" / "chat.jsonl"
        if not log_file.exists():
            return []

        messages = []
        with open(log_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        msg = Message(
                            id=data["id"],
                            project_id=data["project_id"],
                            from_id=data["from_id"],
                            from_name=data["from_name"],
                            content=data["content"],
                            mentions=data.get("mentions", []),
                            attachments=data.get("attachments", []),
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                        )
                        if project_id is None or msg.project_id == project_id:
                            messages.append(msg)
                    except (json.JSONDecodeError, KeyError):
                        continue

        return messages

    def format_chat_history(
        self,
        project_id: str | None = None,
        limit: int = 50,
    ) -> str:
        """Format recent chat history for display.

        Args:
            project_id: Filter by project ID
            limit: Maximum messages to include

        Returns:
            Formatted chat history string
        """
        messages = self.get_messages(project_id=project_id, limit=limit)
        lines = []
        for msg in messages:
            time_str = msg.timestamp.strftime("%H:%M:%S")
            lines.append(f"[{time_str}] {msg.from_name}: {msg.content}")
        return "\n".join(lines)