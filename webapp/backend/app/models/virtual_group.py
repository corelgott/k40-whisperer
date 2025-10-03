from pydantic import BaseModel, Field
from typing import List

class VirtualGroup(BaseModel):
    id: str
    name: str
    project_id: str
    order_index: int = Field(0, description="Position in execution order")
    path_ids: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "group_001",
                "name": "Border Cuts",
                "project_id": "proj_001",
                "order_index": 0,
                "path_ids": ["path_001", "path_002"]
            }
        }

class VirtualGroupCreate(BaseModel):
    name: str
    project_id: str
