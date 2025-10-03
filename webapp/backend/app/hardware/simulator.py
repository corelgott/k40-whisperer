import asyncio
from typing import Tuple, Dict
from pathlib import Path
import json

from app.hardware.controller import LaserController
from app.core.config import settings

class SimulatorController(LaserController):
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.is_running = False
        self.is_homing = False
        self.current_project = None
        self.progress = 0.0
    
    async def move(self, dx: float, dy: float):
        target_x = self.x + dx
        target_y = self.y + dy
        
        steps = 20
        for i in range(steps):
            await asyncio.sleep(0.05)
            self.x = self.x + dx / steps
            self.y = self.y + dy / steps
        
        self.x = target_x
        self.y = target_y
    
    async def home(self):
        self.is_homing = True
        
        steps = 30
        for i in range(steps):
            await asyncio.sleep(0.05)
            self.x = self.x * (1.0 - (i + 1) / steps)
            self.y = self.y * (1.0 - (i + 1) / steps)
        
        self.x = 0.0
        self.y = 0.0
        self.is_homing = False
    
    async def get_position(self) -> Tuple[float, float]:
        return (self.x, self.y)
    
    async def execute_project(self, project_id: str):
        self.is_running = True
        self.current_project = project_id
        self.progress = 0.0
        
        project_dir = settings.projects_dir / project_id
        config_file = project_dir / "config.json"
        
        if not config_file.exists():
            self.is_running = False
            raise Exception("Project config not found")
        
        config_data = json.loads(config_file.read_text())
        paths = sorted(config_data.get("paths", []), key=lambda p: p.get("order_index", 0))
        
        total_paths = len([p for p in paths if p.get("action") != "ignore"])
        completed_paths = 0
        
        for path_config in paths:
            if not self.is_running:
                break
            
            if path_config.get("action") == "ignore":
                continue
            
            repetitions = path_config.get("repetitions", 1)
            speed_mm_s = path_config.get("speed_mm_s", 100.0)
            coordinates = path_config.get("coordinates", [])
            
            if not coordinates:
                await asyncio.sleep(0.1)
                continue
            
            for rep in range(repetitions):
                if not self.is_running:
                    break
                
                for coord in coordinates:
                    if not self.is_running:
                        break
                    
                    target_x, target_y = coord[0], coord[1]
                    
                    distance = ((target_x - self.x)**2 + (target_y - self.y)**2)**0.5
                    time_to_move = distance / speed_mm_s if speed_mm_s > 0 else 0.1
                    
                    steps = max(1, int(time_to_move * 20))
                    for i in range(steps):
                        if not self.is_running:
                            break
                        
                        progress = (i + 1) / steps
                        self.x = self.x + (target_x - self.x) * progress / steps
                        self.y = self.y + (target_y - self.y) * progress / steps
                        
                        await asyncio.sleep(time_to_move / steps)
                    
                    self.x = target_x
                    self.y = target_y
            
            completed_paths += 1
            self.progress = completed_paths / total_paths if total_paths > 0 else 1.0
        
        self.is_running = False
        self.current_project = None
        self.progress = 0.0
    
    async def stop(self):
        self.is_running = False
    
    async def get_status(self) -> Dict:
        return {
            "is_running": self.is_running,
            "is_homing": self.is_homing,
            "current_project": self.current_project,
            "progress": self.progress,
            "mode": "simulator"
        }
