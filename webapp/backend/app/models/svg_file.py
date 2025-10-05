from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class SVGPath(BaseModel):
    path_id: str
    d: str = Field(..., description="SVG path data")
    color: str = Field(..., description="Path color (hex)")
    detected_action: str = Field(..., description="Auto-detected action based on color")

class SVGTransform(BaseModel):
    svg_id: str
    position_x: float = 0.0
    position_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0

class SVGFile(BaseModel):
    id: str
    filename: str
    project_id: str
    uploaded_at: datetime
    paths: List[SVGPath] = []
    width: float = 0.0
    height: float = 0.0
    transform: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "svg_123",
                "filename": "design.svg",
                "project_id": "proj_001",
                "uploaded_at": "2025-10-03T12:00:00",
                "paths": [],
                "width": 300.0,
                "height": 200.0,
                "transform": None
            }
        }

class SVGFileCreate(BaseModel):
    filename: str
    project_id: str
