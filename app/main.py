import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db import engine
from app.models.department import Base
# Make sure to import all models to register them on the Base.metadata
from app.models import employee, history
from app.routes import employee as employee_routes, department as department_routes

async def init_db():
    """Initializes tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and local storage folders
    await init_db()
    
    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    if backend == "local":
        base_dir = os.getenv("LOCAL_STORAGE_DIR", "./data/photos")
        os.makedirs(base_dir, exist_ok=True)
        
    yield
    # Shutdown: clean up DB connections
    await engine.dispose()

app = FastAPI(
    title="人事管理API評価システム (HR Management API)",
    description="FastAPI with SQLAlchemy async engine and abstraction storage for k6 load testing.",
    version="1.0.0",
    lifespan=lifespan
)

# Register routes under /api/v1 prefix
app.include_router(employee_routes.router, prefix="/api/v1")
app.include_router(department_routes.router, prefix="/api/v1")

# Mount StaticFiles if LocalStorage backend is enabled
backend = os.getenv("STORAGE_BACKEND", "local").lower()
if backend == "local":
    base_dir = os.getenv("LOCAL_STORAGE_DIR", "./data/photos")
    os.makedirs(base_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=base_dir), name="static")

app.mount("/dashboard", StaticFiles(directory="app/static/dashboard", html=True), name="dashboard")

@app.get("/")
async def root():
    return {"status": "ok", "message": "HR API System is running."}
