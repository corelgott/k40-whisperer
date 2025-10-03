from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING, Any
from datetime import datetime

if TYPE_CHECKING:
    from .svg_file import SVGFile
    from .virtual_group import VirtualGroup

class Project(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    svg_files: List[Any] = []
    virtual_groups: List[Any] = []
    svg_count: int = 0
    path_count: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "proj_001",
                "name": "My Laser Project",
                "created_at": "2025-10-03T12:00:00",
                "updated_at": "2025-10-03T12:00:00",
                "svg_files": [],
                "virtual_groups": [],
                "svg_count": 0,
                "path_count": 0
            }
        }

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
