import os
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import get_db
from app.storage.base import StorageService
from app.models.user import User
from app.utils.auth import decode_access_token

# Cache for singleton instance
_storage_service: StorageService | None = None

def get_storage() -> StorageService:
    """Dependency injection target to retrieve the configured StorageService with lazy imports."""
    global _storage_service
    if _storage_service is not None:
        return _storage_service

    backend = os.getenv("STORAGE_BACKEND", "local").lower()

    if backend in ["azure", "azure_blob", "blob"]:
        from app.storage.azure_blob import AzureBlobStorage
        conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        container = os.environ["AZURE_CONTAINER_NAME"]
        _storage_service = AzureBlobStorage(conn_str, container)
        
    elif backend in ["s3", "aws_s3", "aws"]:
        from app.storage.s3 import S3Storage
        bucket = os.environ["S3_BUCKET_NAME"]
        endpoint = os.getenv("S3_ENDPOINT_URL")
        region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
        _storage_service = S3Storage(bucket, endpoint_url=endpoint, region=region)
        
    elif backend in ["local", "filesystem", "file"]:
        from app.storage.local import LocalStorage
        base_dir = os.getenv("LOCAL_STORAGE_DIR", "./data/photos")
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        _storage_service = LocalStorage(base_dir, base_url)
        
    else:
        raise ValueError(f"Unsupported storage backend: {backend}")

    return _storage_service


security_bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer)
) -> User:
    """
    Validates JWT token from Authorization header or ?token= query param in-memory.
    Completely stateless: does not consume DB connections, maximizing high-concurrency throughput.
    """
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    else:
        # Fallback to query parameter (useful for <img src="..."> tags)
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload["sub"]
    role: str = payload.get("role", "admin")

    # In-memory User instance (zero DB query overhead)
    return User(
        id=1,
        username=username,
        role=role,
        is_active=True
    )

