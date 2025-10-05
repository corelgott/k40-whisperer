from fastapi import APIRouter, HTTPException, UploadFile, File, status
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json
import shutil
from pathlib import Path

from app.models import Project, ProjectCreate, SVGFile, SVGFileCreate
from app.models import PathConfig, PathConfigUpdate, VirtualGroup, VirtualGroupCreate
from app.core.config import settings
from app.svg.parser import parse_svg_file, extract_coordinates_from_path
from app.git.repository import GitRepository

router = APIRouter()


def resolve_path_settings(
    path_config: Dict[str, Any],
    group: Optional[Dict[str, Any]],
    project: Dict[str, Any]
) -> Dict[str, Any]:
    """Resolve effective settings for a path considering inheritance"""
    action = path_config.get("action")
    if action is None:
        action = (group and group.get("default_action")) or project.get("default_action", "cut")
    
    speed = path_config.get("speed_mm_s")
    if speed is None:
        speed = (group and group.get("default_speed_mm_s")) or project.get("default_speed_mm_s", 100.0)
    
    reps = path_config.get("repetitions")
    if reps is None:
        reps = (group and group.get("default_repetitions")) or project.get("default_repetitions", 1)
    
    return {
        "action": action,
        "speed_mm_s": speed,
        "repetitions": reps,
        "effective_action": action,
        "effective_speed_mm_s": speed,
        "effective_repetitions": reps
    }


@router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate):
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    project_dir = settings.projects_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    
    (project_dir / "svgs").mkdir(exist_ok=True)
    
    now = datetime.now()
    project_data = Project(
        id=project_id,
        name=project.name,
        created_at=now,
        updated_at=now,
        svg_files=[],
        virtual_groups=[],
        svg_count=0,
        path_count=0
    )
    
    project_file = project_dir / "project.json"
    project_file.write_text(project_data.model_dump_json(indent=2))
    
    config_file = project_dir / "config.json"
    config_file.write_text(json.dumps({
        "paths": [],
        "virtual_groups": []
    }, indent=2))
    
    git_repo = GitRepository(project_dir)
    git_repo.init()
    git_repo.commit("Initial project creation")
    
    return project_data

@router.get("/projects", response_model=List[Project])
async def list_projects():
    projects = []
    for project_dir in settings.projects_dir.iterdir():
        if project_dir.is_dir():
            project_file = project_dir / "project.json"
            if project_file.exists():
                project_data = json.loads(project_file.read_text())
                
                svg_files = []
                svgs_dir = project_dir / "svgs"
                config_file = project_dir / "config.json"
                config_data = json.loads(config_file.read_text()) if config_file.exists() else {"paths": [], "virtual_groups": []}
                
                if svgs_dir.exists():
                    for svg_file in svgs_dir.iterdir():
                        if svg_file.suffix == '.svg':
                            svg_id = svg_file.stem
                            svg_paths = [PathConfig(**p) for p in config_data.get("paths", []) if p.get("svg_id") == svg_id]
                            svg_files.append({
                                "id": svg_id,
                                "filename": svg_file.name,
                                "project_id": project_data["id"],
                                "paths": [p.model_dump() for p in svg_paths],
                                "uploaded_at": datetime.fromtimestamp(svg_file.stat().st_mtime).isoformat()
                            })
                
                virtual_groups = [VirtualGroup(**g).model_dump() for g in config_data.get("virtual_groups", [])]
                
                project = Project(
                    id=project_data["id"],
                    name=project_data["name"],
                    created_at=project_data["created_at"],
                    updated_at=project_data["updated_at"],
                    svg_files=svg_files,
                    virtual_groups=virtual_groups
                )
                projects.append(project)
    return sorted(projects, key=lambda p: p.created_at, reverse=True)

@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    project_dir = settings.projects_dir / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_file = project_dir / "project.json"
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="Project data not found")
    
    project_data = json.loads(project_file.read_text())
    
    svg_files = []
    svgs_dir = project_dir / "svgs"
    config_file = project_dir / "config.json"
    config_data = json.loads(config_file.read_text()) if config_file.exists() else {"paths": [], "virtual_groups": []}
    
    if svgs_dir.exists():
        for svg_file in svgs_dir.iterdir():
            if svg_file.suffix == '.svg':
                svg_id = svg_file.stem
                svg_paths = [PathConfig(**p) for p in config_data.get("paths", []) if p.get("svg_id") == svg_id]
                svg_files.append({
                    "id": svg_id,
                    "filename": svg_file.name,
                    "project_id": project_id,
                    "paths": [p.model_dump() for p in svg_paths],
                    "uploaded_at": datetime.fromtimestamp(svg_file.stat().st_mtime).isoformat()
                })
    
    virtual_groups = [VirtualGroup(**g).model_dump() for g in config_data.get("virtual_groups", [])]
    
    return Project(
        id=project_data["id"],
        name=project_data["name"],
        created_at=project_data["created_at"],
        updated_at=project_data["updated_at"],
        svg_files=svg_files,
        virtual_groups=virtual_groups,
        default_action=config_data.get("default_action"),
        default_speed_mm_s=config_data.get("default_speed_mm_s"),
        default_repetitions=config_data.get("default_repetitions")
    )

@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str):
    project_dir = settings.projects_dir / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    shutil.rmtree(project_dir)
    return None

@router.post("/projects/{project_id}/svgs", response_model=SVGFile, status_code=status.HTTP_201_CREATED)
async def upload_svg(project_id: str, file: UploadFile = File(...)):
    project_dir = settings.projects_dir / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not file.filename.endswith('.svg'):
        raise HTTPException(status_code=400, detail="File must be an SVG")
    
    svg_id = f"svg_{uuid.uuid4().hex[:8]}"
    svgs_dir = project_dir / "svgs"
    svg_path = svgs_dir / f"{svg_id}.svg"
    
    with svg_path.open("wb") as f:
        content = await file.read()
        f.write(content)
    
    svg_data = parse_svg_file(svg_path)
    
    config_file = project_dir / "config.json"
    config_data = json.loads(config_file.read_text())
    
    for path in svg_data.paths:
        coordinates = extract_coordinates_from_path(path.d)
        path_config = PathConfig(
            path_id=path.path_id,
            svg_id=svg_id,
            action=path.detected_action,
            speed_mm_s=100.0,
            repetitions=1,
            order_index=len(config_data["paths"]),
            coordinates=coordinates
        )
        config_data["paths"].append(path_config.model_dump())
    
    config_file.write_text(json.dumps(config_data, indent=2))
    
    project_file = project_dir / "project.json"
    project = json.loads(project_file.read_text())
    project["svg_count"] = len(list(svgs_dir.glob("*.svg")))
    project["path_count"] = len(config_data["paths"])
    project["updated_at"] = datetime.now().isoformat()
    project_file.write_text(json.dumps(project, indent=2))
    
    git_repo = GitRepository(project_dir)
    git_repo.commit(f"Add SVG: {file.filename}")
    
    svg_file = SVGFile(
        id=svg_id,
        filename=file.filename,
        project_id=project_id,
        uploaded_at=datetime.now(),
        paths=svg_data.paths,
        width=svg_data.width,
        height=svg_data.height
    )
    
    return svg_file

@router.get("/projects/{project_id}/svgs/{svg_id}", response_model=SVGFile)
async def get_svg(project_id: str, svg_id: str):
    project_dir = settings.projects_dir / project_id
    svg_path = project_dir / "svgs" / f"{svg_id}.svg"
    
    if not svg_path.exists():
        raise HTTPException(status_code=404, detail="SVG not found")
    
    svg_data = parse_svg_file(svg_path)
    
    return SVGFile(
        id=svg_id,
        filename=svg_path.name,
        project_id=project_id,
        uploaded_at=datetime.fromtimestamp(svg_path.stat().st_mtime),
        paths=svg_data.paths,
        width=svg_data.width,
        height=svg_data.height
    )

@router.delete("/projects/{project_id}/svgs/{svg_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_svg(project_id: str, svg_id: str):
    project_dir = settings.projects_dir / project_id
    svg_path = project_dir / "svgs" / f"{svg_id}.svg"
    
    if not svg_path.exists():
        raise HTTPException(status_code=404, detail="SVG not found")
    
    svg_path.unlink()
    
    config_file = project_dir / "config.json"
    config_data = json.loads(config_file.read_text())
    config_data["paths"] = [p for p in config_data["paths"] if p["svg_id"] != svg_id]
    config_file.write_text(json.dumps(config_data, indent=2))
    
    git_repo = GitRepository(project_dir)
    git_repo.commit(f"Delete SVG: {svg_id}")
    
    return None

@router.get("/projects/{project_id}/paths", response_model=List[PathConfig])
async def get_paths(project_id: str):
    project_dir = settings.projects_dir / project_id
    config_file = project_dir / "config.json"
    
    if not config_file.exists():
        return []
    
    config_data = json.loads(config_file.read_text())
    return [PathConfig(**p) for p in config_data.get("paths", [])]

@router.put("/projects/{project_id}/paths/{path_id}", response_model=PathConfig)
async def update_path(project_id: str, path_id: str, update: PathConfigUpdate):
    project_dir = settings.projects_dir / project_id
    config_file = project_dir / "config.json"
    
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="Project config not found")
    
    config_data = json.loads(config_file.read_text())
    
    path_found = False
    for path in config_data["paths"]:
        if path["path_id"] == path_id:
            path_found = True
            for field, value in update.model_dump(exclude_unset=True).items():
                path[field] = value
            break
    
    if not path_found:
        raise HTTPException(status_code=404, detail="Path not found")
    
    config_file.write_text(json.dumps(config_data, indent=2))
    
    git_repo = GitRepository(project_dir)
    git_repo.commit(f"Update path: {path_id}")
    
    return PathConfig(**path)

@router.post("/projects/{project_id}/paths/reorder")
async def reorder_paths(project_id: str, path_order: List[str]):
    project_dir = settings.projects_dir / project_id
    config_file = project_dir / "config.json"
    
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="Project config not found")
    
    config_data = json.loads(config_file.read_text())
    
    path_map = {p["path_id"]: p for p in config_data["paths"]}
    
    reordered_paths = []
    for idx, path_id in enumerate(path_order):
        if path_id in path_map:
            path = path_map[path_id]
            path["order_index"] = idx
            reordered_paths.append(path)
    
    config_data["paths"] = reordered_paths
    config_file.write_text(json.dumps(config_data, indent=2))
    
    git_repo = GitRepository(project_dir)
    git_repo.commit("Reorder paths")
    
    return {"status": "ok", "reordered_count": len(reordered_paths)}

@router.post("/projects/{project_id}/virtual-groups", response_model=VirtualGroup, status_code=status.HTTP_201_CREATED)
async def create_virtual_group(project_id: str, group: VirtualGroupCreate):
    project_dir = settings.projects_dir / project_id
    config_file = project_dir / "config.json"
    
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="Project config not found")
    
    config_data = json.loads(config_file.read_text())
    
    group_id = f"group_{uuid.uuid4().hex[:8]}"
    virtual_group = VirtualGroup(
        id=group_id,
        name=group.name,
        project_id=project_id,
        default_action=None,
        default_speed_mm_s=None,
        default_repetitions=None,
        order_index=len(config_data.get("virtual_groups", [])),
        path_ids=[]
    )
    
    if "virtual_groups" not in config_data:
        config_data["virtual_groups"] = []
    
    config_data["virtual_groups"].append(virtual_group.model_dump())
    config_file.write_text(json.dumps(config_data, indent=2))
    
    git_repo = GitRepository(project_dir)
    git_repo.commit(f"Create virtual group: {group.name}")
    
    return virtual_group

@router.get("/projects/{project_id}/virtual-groups", response_model=List[VirtualGroup])
async def get_virtual_groups(project_id: str):
    project_dir = settings.projects_dir / project_id
    config_file = project_dir / "config.json"
    
    if not config_file.exists():
        return []
    
    config_data = json.loads(config_file.read_text())
    return [VirtualGroup(**g) for g in config_data.get("virtual_groups", [])]

@router.put("/projects/{project_id}/paths/{path_id}/move")
async def move_path_to_group(project_id: str, path_id: str, target_group_id: Optional[str] = None):
    project_dir = settings.projects_dir / project_id
    config_file = project_dir / "config.json"
    
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="Project config not found")
    
    config_data = json.loads(config_file.read_text())
    
    path_found = False
    original_svg_id = None
    for path in config_data["paths"]:
        if path["path_id"] == path_id:
            path_found = True
            original_svg_id = path["svg_id"]
            
            if target_group_id is None:
                path["virtual_group_id"] = None
            else:
                group_found = any(g["id"] == target_group_id for g in config_data.get("virtual_groups", []))
                if not group_found:
                    raise HTTPException(status_code=404, detail="Virtual group not found")
                path["virtual_group_id"] = target_group_id
            break
    
    if not path_found:
        raise HTTPException(status_code=404, detail="Path not found")
    
    for group in config_data.get("virtual_groups", []):
        if path_id in group["path_ids"]:
            group["path_ids"].remove(path_id)
        if group["id"] == target_group_id and path_id not in group["path_ids"]:
            group["path_ids"].append(path_id)
    
    config_file.write_text(json.dumps(config_data, indent=2))
    
    git_repo = GitRepository(project_dir)
    git_repo.commit(f"Move path {path_id} to group {target_group_id}")
    
    return {"status": "ok", "path_id": path_id, "virtual_group_id": target_group_id}

@router.put("/projects/{project_id}/defaults")
async def update_project_defaults(
    project_id: str,
    default_action: Optional[str] = None,
    default_speed_mm_s: Optional[float] = None,
    default_repetitions: Optional[int] = None
):
    project_dir = settings.projects_dir / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    config_file = project_dir / "config.json"
    config_data = {}
    if config_file.exists():
        with open(config_file, "r") as f:
            config_data = json.load(f)
    
    if default_action is not None:
        config_data["default_action"] = default_action
    if default_speed_mm_s is not None:
        config_data["default_speed_mm_s"] = default_speed_mm_s
    if default_repetitions is not None:
        config_data["default_repetitions"] = default_repetitions
    
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)
    
    return {"message": "Project defaults updated successfully"}


@router.put("/projects/{project_id}/virtual-groups/{group_id}")
async def update_virtual_group(
    project_id: str,
    group_id: str,
    name: Optional[str] = None,
    default_action: Optional[str] = None,
    default_speed_mm_s: Optional[float] = None,
    default_repetitions: Optional[int] = None
):
    project_dir = settings.projects_dir / project_id
    config_file = project_dir / "config.json"
    
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    with open(config_file, "r") as f:
        config_data = json.load(f)
    
    groups = config_data.get("virtual_groups", [])
    group = next((g for g in groups if g["id"] == group_id), None)
    
    if not group:
        raise HTTPException(status_code=404, detail="Virtual group not found")
    
    if name is not None:
        group["name"] = name
    if default_action is not None:
        group["default_action"] = default_action
    if default_speed_mm_s is not None:
        group["default_speed_mm_s"] = default_speed_mm_s
    if default_repetitions is not None:
        group["default_repetitions"] = default_repetitions
    
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)
    
    return VirtualGroup(**group)
