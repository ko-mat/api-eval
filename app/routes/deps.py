import os
from app.storage.base import StorageService
from app.storage.local import LocalStorage
from app.storage.s3 import S3Storage
from app.storage.azure_blob import AzureBlobStorage

# Cache for singleton instance
_storage_service: StorageService | None = None

def get_storage() -> StorageService:
    """Dependency injection target to retrieve the configured StorageService."""
    global _storage_service
    if _storage_service is not None:
        return _storage_service

    backend = os.getenv("STORAGE_BACKEND", "local").lower()

    if backend == "azure":
        conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        container = os.environ["AZURE_CONTAINER_NAME"]
        _storage_service = AzureBlobStorage(conn_str, container)
        
    elif backend == "s3":
        bucket = os.environ["S3_BUCKET_NAME"]
        endpoint = os.getenv("S3_ENDPOINT_URL")
        region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
        _storage_service = S3Storage(bucket, endpoint_url=endpoint, region=region)
        
    elif backend == "local":
        base_dir = os.getenv("LOCAL_STORAGE_DIR", "./data/photos")
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        _storage_service = LocalStorage(base_dir, base_url)
        
    else:
        raise ValueError(f"Unsupported storage backend: {backend}")

    return _storage_service
