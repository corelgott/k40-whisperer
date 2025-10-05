from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Tuple
from enum import Enum

class PathAction(str, Enum):
    IGNORE = "ignore"
    ENGRAVE = "engrave"
    CUT = "cut"

class PathConfig(BaseModel):
    path_id: str = Field(..., description="Unique identifier for the path")
    svg_id: str = Field(..., description="ID of the parent SVG file")
    action: Optional[PathAction] = Field(None, description="Action to perform on this path, None means inherit from parent")
    speed_mm_s: Optional[float] = Field(None, ge=0.1, le=500.0, description="Speed in mm/s, None means inherit")
    repetitions: Optional[int] = Field(None, ge=0, le=100, description="Number of times to repeat this path, None means inherit")
    order_index: int = Field(0, description="Position in execution order")
    virtual_group_id: Optional[str] = Field(None, description="ID of virtual group if assigned")
    coordinates: List[Tuple[float, float]] = Field(default_factory=list, description="Path coordinates for simulation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "path_id": "path_001",
                "svg_id": "svg_123",
                "action": None,
                "speed_mm_s": None,
                "repetitions": None,
                "order_index": 0,
                "virtual_group_id": None,
                "coordinates": []
            }
        }

class PathConfigUpdate(BaseModel):
    action: Optional[PathAction] = None
    speed_mm_s: Optional[float] = Field(None, ge=0.1, le=500.0)
    repetitions: Optional[int] = Field(None, ge=0, le=100)
    order_index: Optional[int] = None
    virtual_group_id: Optional[str] = None
