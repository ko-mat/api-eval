import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db import engine
from app.models.department import Base
# Make sure to import all models to register them on the Base.metadata
from app.models import employee, history, user
from app.routes import employee as employee_routes, department as department_routes, auth as auth_routes
from app.db import async_session_maker
from app.models.user import User
from app.utils.auth import hash_password
from sqlalchemy.future import select

async def init_db():
    """Initializes tables and seeds default admin user if not present."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed default admin
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "AdminPass2026!")
    async with async_session_maker() as session:
        stmt = select(User).filter(User.username == admin_user)
        result = await session.execute(stmt)
        if not result.scalars().first():
            user_obj = User(
                username=admin_user,
                hashed_password=hash_password(admin_pass),
                role="admin",
                is_active=True
            )
            session.add(user_obj)
            await session.commit()
            print(f"[AUTH] Initial admin user '{admin_user}' created.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and local storage folders
    await init_db()
    
    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    if backend in ["local", "filesystem", "file"]:
        base_dir = os.getenv("LOCAL_STORAGE_DIR", "./data/photos")
        os.makedirs(base_dir, exist_ok=True)
        
    yield
    # Shutdown: clean up DB connections
    await engine.dispose()

app = FastAPI(
    title="人事管理API評価システム (HR Management API)",
    description="FastAPI with SQLAlchemy async engine, JWT Auth, and abstraction storage for k6 load testing.",
    version="1.0.0",
    lifespan=lifespan
)

# Register routes under /api/v1 prefix
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(employee_routes.router, prefix="/api/v1")
app.include_router(department_routes.router, prefix="/api/v1")

# Mount StaticFiles if LocalStorage backend is enabled
backend = os.getenv("STORAGE_BACKEND", "local").lower()
if backend in ["local", "filesystem", "file"]:
    base_dir = os.getenv("LOCAL_STORAGE_DIR", "./data/photos")
    os.makedirs(base_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=base_dir), name="static")

app.mount("/dashboard", StaticFiles(directory="app/static/dashboard", html=True), name="dashboard")

@app.get("/")
async def root():
    return {"status": "ok", "message": "HR API System is running."}
