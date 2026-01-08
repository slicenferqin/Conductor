"""Projects REST API endpoints."""

import logging
from fastapi import APIRouter, HTTPException

from ..schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from ..state import app_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects():
    """List all projects."""
    return app_state.get_all_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get project details by ID."""
    project = app_state.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("", response_model=ProjectResponse)
async def create_project(data: ProjectCreate):
    """Create a new project (triggers orchestrator)."""
    # Import here to avoid circular imports
    from ..services.orchestrator_bridge import orchestrator_bridge

    try:
        project = await orchestrator_bridge.start_project(data.requirement)
        return project
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate):
    """Pause, resume, or stop a project."""
    from ..services.orchestrator_bridge import orchestrator_bridge

    project = app_state.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if data.action == "pause":
        success = await orchestrator_bridge.pause_project(project_id)
    elif data.action == "resume":
        success = await orchestrator_bridge.resume_project(project_id)
    elif data.action == "stop":
        success = await orchestrator_bridge.stop_project(project_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    if not success:
        raise HTTPException(status_code=400, detail=f"Action '{data.action}' failed")

    return {"status": "ok", "action": data.action}
