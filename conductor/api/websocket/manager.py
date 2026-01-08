"""WebSocket connection manager for real-time updates."""

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # All active connections
        self._connections: set[WebSocket] = set()
        # Connections subscribed to specific projects
        self._project_subscriptions: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections.discard(websocket)
            # Remove from all project subscriptions
            for project_id in list(self._project_subscriptions.keys()):
                self._project_subscriptions[project_id].discard(websocket)
                if not self._project_subscriptions[project_id]:
                    del self._project_subscriptions[project_id]
        logger.info(f"WebSocket disconnected. Total connections: {len(self._connections)}")

    async def subscribe_to_project(self, websocket: WebSocket, project_id: str) -> None:
        """Subscribe a connection to project updates."""
        async with self._lock:
            if project_id not in self._project_subscriptions:
                self._project_subscriptions[project_id] = set()
            self._project_subscriptions[project_id].add(websocket)
        logger.info(f"WebSocket subscribed to project {project_id}")

    async def unsubscribe_from_project(self, websocket: WebSocket, project_id: str) -> None:
        """Unsubscribe a connection from project updates."""
        async with self._lock:
            if project_id in self._project_subscriptions:
                self._project_subscriptions[project_id].discard(websocket)
        logger.info(f"WebSocket unsubscribed from project {project_id}")

    async def broadcast(self, event: dict[str, Any]) -> None:
        """Broadcast event to all connected clients."""
        message = json.dumps(event)
        disconnected: list[WebSocket] = []

        for connection in self._connections.copy():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            await self.disconnect(conn)

    async def broadcast_to_project(self, project_id: str, event: dict[str, Any]) -> None:
        """Broadcast event to clients subscribed to a specific project."""
        if project_id not in self._project_subscriptions:
            return

        message = json.dumps(event)
        disconnected: list[WebSocket] = []

        for connection in self._project_subscriptions[project_id].copy():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            await self.disconnect(conn)

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)

    def get_project_subscriber_count(self, project_id: str) -> int:
        """Get the number of subscribers for a project."""
        return len(self._project_subscriptions.get(project_id, set()))


# Global singleton
connection_manager = ConnectionManager()
