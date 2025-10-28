import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import shutil
import tempfile

from app.main import app
from app.core.config import settings

client = TestClient(app)

@pytest.fixture
def temp_projects_dir():
    temp_dir = Path(tempfile.mkdtemp())
    original_dir = settings.projects_dir
    settings.projects_dir = temp_dir
    yield temp_dir
    settings.projects_dir = original_dir
    shutil.rmtree(temp_dir)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_project(temp_projects_dir):
    response = client.post(
        "/api/v1/project/projects",
        json={"name": "Test Project"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert "id" in data
    assert data["svg_count"] == 0
    assert data["path_count"] == 0

def test_list_projects(temp_projects_dir):
    client.post("/api/v1/project/projects", json={"name": "Project 1"})
    client.post("/api/v1/project/projects", json={"name": "Project 2"})
    
    response = client.get("/api/v1/project/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(p["name"] == "Project 1" for p in data)
    assert any(p["name"] == "Project 2" for p in data)

def test_get_project(temp_projects_dir):
    create_response = client.post(
        "/api/v1/project/projects",
        json={"name": "Test Project"}
    )
    project_id = create_response.json()["id"]
    
    response = client.get(f"/api/v1/project/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["id"] == project_id

def test_delete_project(temp_projects_dir):
    create_response = client.post(
        "/api/v1/project/projects",
        json={"name": "Test Project"}
    )
    project_id = create_response.json()["id"]
    
    response = client.delete(f"/api/v1/project/projects/{project_id}")
    assert response.status_code == 204
    
    response = client.get(f"/api/v1/project/projects/{project_id}")
    assert response.status_code == 404

def test_upload_svg(temp_projects_dir):
    create_response = client.post(
        "/api/v1/project/projects",
        json={"name": "Test Project"}
    )
    project_id = create_response.json()["id"]
    
    svg_content = '''<?xml version="1.0"?>
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <path d="M 10 10 L 90 90" stroke="#ff0000" fill="none"/>
    </svg>'''
    
    response = client.post(
        f"/api/v1/project/projects/{project_id}/svgs",
        files={"file": ("test.svg", svg_content, "image/svg+xml")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.svg"
    assert len(data["paths"]) > 0

def test_get_paths(temp_projects_dir):
    create_response = client.post(
        "/api/v1/project/projects",
        json={"name": "Test Project"}
    )
    project_id = create_response.json()["id"]
    
    response = client.get(f"/api/v1/project/projects/{project_id}/paths")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_laser_position():
    response = client.get("/api/v1/k40/position")
    assert response.status_code == 200
    data = response.json()
    assert "x" in data
    assert "y" in data

def test_laser_home():
    response = client.post("/api/v1/k40/home")
    assert response.status_code == 200
    data = response.json()
    assert data["x"] == 0.0
    assert data["y"] == 0.0

def test_laser_move():
    response = client.post(
        "/api/v1/k40/move",
        json={"dx": 10.0, "dy": 5.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert "x" in data
    assert "y" in data

def test_laser_status():
    response = client.get("/api/v1/k40/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data
    assert "mode" in data
    assert data["mode"] == "simulator"
