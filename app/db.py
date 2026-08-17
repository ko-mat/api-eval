import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local.db")

# Connection pool configurations
is_sqlite = DATABASE_URL.startswith("sqlite")

engine_kwargs = {
    "echo": os.getenv("DB_ECHO", "false").lower() == "true",
}

if not is_sqlite:
    # Configure production pool size for PostgreSQL / MySQL
    engine_kwargs.update({
        "pool_size": int(os.getenv("DB_POOL_SIZE", "15")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_timeout": float(os.getenv("DB_POOL_TIMEOUT", "20")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
        "pool_pre_ping": True,
    })

# Create asynchronous engine
engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Enable foreign keys for SQLite specifically
if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Dependency to get DB session
async def get_db():
    """Dependency for API routes to get a database session."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
