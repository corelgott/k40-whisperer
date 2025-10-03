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
    action: PathAction = Field(PathAction.IGNORE, description="Action to perform on this path")
    speed_mm_s: float = Field(100.0, ge=0.1, le=500.0, description="Speed in mm/s")
    repetitions: int = Field(1, ge=0, le=100, description="Number of times to repeat this path")
    order_index: int = Field(0, description="Position in execution order")
    virtual_group_id: Optional[str] = Field(None, description="ID of virtual group if assigned")
    coordinates: List[Tuple[float, float]] = Field(default_factory=list, description="Path coordinates for simulation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "path_id": "path_001",
                "svg_id": "svg_123",
                "action": "cut",
                "speed_mm_s": 150.0,
                "repetitions": 2,
                "order_index": 0,
                "virtual_group_id": None
            }
        }

class PathConfigUpdate(BaseModel):
    action: Optional[PathAction] = None
    speed_mm_s: Optional[float] = Field(None, ge=0.1, le=500.0)
    repetitions: Optional[int] = Field(None, ge=0, le=100)
    order_index: Optional[int] = None
    virtual_group_id: Optional[str] = None
