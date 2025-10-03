from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "K40 Whisperer API"
    projects_dir: Path = Path.home() / "laser_projects"
    simulator_mode: bool = True
    max_upload_size: int = 10 * 1024 * 1024
    
    class Config:
        env_file = ".env"

settings = Settings()
settings.projects_dir.mkdir(parents=True, exist_ok=True)
