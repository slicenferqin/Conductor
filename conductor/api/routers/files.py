from typing import List, Optional
from pathlib import Path
import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from conductor.config import get_config

router = APIRouter(
    prefix="/api/projects/{project_id}/files",
    tags=["files"],
)

class FileNode(BaseModel):
    name: str
    path: str
    type: str  # 'file' or 'directory'
    size: Optional[int] = None
    last_modified: Optional[float] = None
    children: Optional[List["FileNode"]] = None

class FileContent(BaseModel):
    path: str
    content: str
    size: int

def _scan_directory(root: Path, relative_to: Path) -> List[FileNode]:
    """Recursively scan directory and return file tree."""
    nodes = []
    
    # Sort: Directories first, then files
    try:
        entries = sorted(root.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    except FileNotFoundError:
        return []

    for entry in entries:
        # Ignore hidden files/dirs (starting with .)
        if entry.name.startswith("."):
            continue

        relative_path = str(entry.relative_to(relative_to))
        
        node = FileNode(
            name=entry.name,
            path=relative_path,
            type="directory" if entry.is_dir() else "file",
            last_modified=entry.stat().st_mtime
        )

        if entry.is_dir():
            node.children = _scan_directory(entry, relative_to)
        else:
            node.size = entry.stat().st_size
        
        nodes.append(node)
    
    return nodes

@router.get("", response_model=List[FileNode])
async def list_files(project_id: str):
    """List all files in the project workspace."""
    config = get_config()
    # Project workspace is in projects/project-{project_id}
    project_path = config.workspace / f"project-{project_id}"

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    return _scan_directory(project_path, project_path)

@router.get("/content", response_model=FileContent)
async def get_file_content(project_id: str, path: str = Query(..., description="Relative path to file")):
    """Get content of a specific file."""
    config = get_config()
    # Project workspace is in projects/project-{project_id}
    project_path = config.workspace / f"project-{project_id}"
    file_path = project_path / path
    
    # Security check: Ensure file path is within project directory
    try:
        file_path = file_path.resolve()
        project_path = project_path.resolve()
        if not str(file_path).startswith(str(project_path)):
             raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
         raise HTTPException(status_code=400, detail="Invalid path")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        # Try reading as text
        content = file_path.read_text(encoding="utf-8")
        return FileContent(
            path=path,
            content=content,
            size=file_path.stat().st_size
        )
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Binary files are not supported for preview")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
