from abc import ABC, abstractmethod
from typing import Tuple, Dict
import asyncio

from app.core.config import settings

class LaserController(ABC):
    @abstractmethod
    async def move(self, dx: float, dy: float):
        pass
    
    @abstractmethod
    async def home(self):
        pass
    
    @abstractmethod
    async def get_position(self) -> Tuple[float, float]:
        pass
    
    @abstractmethod
    async def execute_project(self, project_id: str):
        pass
    
    @abstractmethod
    async def stop(self):
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict:
        pass

_controller_instance = None

def get_laser_controller() -> LaserController:
    global _controller_instance
    
    if _controller_instance is None:
        if settings.simulator_mode:
            from app.hardware.simulator import SimulatorController
            _controller_instance = SimulatorController()
        else:
            from app.hardware.k40_hardware import K40HardwareController
            _controller_instance = K40HardwareController()
    
    return _controller_instance
