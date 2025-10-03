from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import projects, k40, websocket

app = FastAPI(
    title="K40 Whisperer API",
    version="0.1.0",
    description="REST API for K40 Laser Cutter control and project management"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/v1/project", tags=["projects"])
app.include_router(k40.router, prefix="/api/v1/k40", tags=["k40"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.get("/")
async def root():
    return {
        "message": "K40 Whisperer API",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
