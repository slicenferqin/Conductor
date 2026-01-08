"""In-memory application state management."""

import threading
import json
import os
from pathlib import Path
from typing import Any

from .schemas import ProjectResponse, MessageSchema, TeamMemberSchema

DATA_DIR = Path("data")
STORAGE_FILE = DATA_DIR / "storage.json"

class AppState:
    """In-memory application state with JSON persistence."""

    def __init__(self):
        self._projects: dict[str, ProjectResponse] = {}
        self._messages: dict[str, list[MessageSchema]] = {}
        self._lock = threading.Lock()
        self._load_state()

    def _ensure_data_dir(self):
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True)

    def _save_state(self):
        """Save state to JSON file."""
        try:
            self._ensure_data_dir()
            data = {
                "projects": {
                    pid: project.model_dump() 
                    for pid, project in self._projects.items()
                },
                "messages": {
                    pid: [msg.model_dump() for msg in msgs]
                    for pid, msgs in self._messages.items()
                }
            }
            with open(STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

    def _load_state(self):
        """Load state from JSON file."""
        if not STORAGE_FILE.exists():
            return

        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Restore projects
            if "projects" in data:
                for pid, p_data in data["projects"].items():
                    # Handle nested models (Role) in team members if needed
                    # Pydantic's model_validate should handle dicts recursively
                    self._projects[pid] = ProjectResponse.model_validate(p_data)

            # Restore messages
            if "messages" in data:
                for pid, msgs_data in data["messages"].items():
                    self._messages[pid] = [
                        MessageSchema.model_validate(msg) 
                        for msg in msgs_data
                    ]
        except Exception as e:
            print(f"Error loading state: {e}")

    def add_project(self, project: ProjectResponse) -> None:
        """Add a project to state."""
        with self._lock:
            self._projects[project.id] = project
            if project.id not in self._messages:
                self._messages[project.id] = []
            self._save_state()

    def get_project(self, project_id: str) -> ProjectResponse | None:
        """Get a project by ID."""
        return self._projects.get(project_id)

    def get_all_projects(self) -> list[ProjectResponse]:
        """Get all projects."""
        return list(self._projects.values())

    def update_project(self, project: ProjectResponse) -> None:
        """Update a project in state."""
        with self._lock:
            self._projects[project.id] = project
            self._save_state()

    def update_project_status(self, project_id: str, status: str) -> None:
        """Update a project's status."""
        with self._lock:
            if project_id in self._projects:
                project = self._projects[project_id]
                # Create new ProjectResponse with updated status
                self._projects[project_id] = ProjectResponse(
                    id=project.id,
                    name=project.name,
                    requirement=project.requirement,
                    workspace=project.workspace,
                    status=status,
                    team=project.team,
                    createdAt=project.createdAt,
                    lastUpdated=project.lastUpdated,
                    duration=project.duration,
                )
                self._save_state()

    def update_agent_status(
        self,
        project_id: str,
        agent_id: str,
        status: str,
        current_action: str | None = None,
        progress: int | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update an agent's status within a project."""
        with self._lock:
            if project_id not in self._projects:
                return

            project = self._projects[project_id]
            updated_team = []

            for member in project.team:
                if member.id == agent_id:
                    updated_team.append(TeamMemberSchema(
                        id=member.id,
                        role=member.role,
                        status=status,
                        currentAction=current_action,
                        progress=progress,
                        errorMessage=error_message,
                    ))
                else:
                    updated_team.append(member)

            self._projects[project_id] = ProjectResponse(
                id=project.id,
                name=project.name,
                requirement=project.requirement,
                workspace=project.workspace,
                status=project.status,
                team=updated_team,
                createdAt=project.createdAt,
                lastUpdated=project.lastUpdated,
                duration=project.duration,
            )
            self._save_state()

    def add_message(self, project_id: str, message: MessageSchema) -> None:
        """Add a message to a project."""
        with self._lock:
            if project_id not in self._messages:
                self._messages[project_id] = []
            self._messages[project_id].append(message)
            self._save_state()

    def get_messages(self, project_id: str) -> list[MessageSchema]:
        """Get messages for a project."""
        return self._messages.get(project_id, [])

    def clear(self) -> None:
        """Clear all state (for testing)."""
        with self._lock:
            self._projects.clear()
            self._messages.clear()


# Global singleton
app_state = AppState()
