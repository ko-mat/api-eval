import aioboto3
from typing import BinaryIO
from app.storage.base import StorageService, StorageError

class S3Storage(StorageService):
    def __init__(self, bucket: str, endpoint_url: str | None = None, region: str = "us-east-1"):
        self.bucket = bucket
        self.endpoint_url = endpoint_url
        self.region = region
        self.session = aioboto3.Session()

    async def upload(self, file: BinaryIO, filename: str) -> str:
        try:
            if hasattr(file, "seek"):
                file.seek(0)
            
            async with self.session.client("s3", endpoint_url=self.endpoint_url, region_name=self.region) as s3:
                # Determine basic content type if possible, or upload as generic binary
                await s3.upload_fileobj(file, self.bucket, filename)
                
                # Build public accessing URL
                if self.endpoint_url:
                    return f"{self.endpoint_url.rstrip('/')}/{self.bucket}/{filename}"
                return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{filename}"
        except Exception as e:
            raise StorageError(f"S3 upload operation failed: {str(e)}") from e

    async def delete(self, filename: str) -> None:
        try:
            async with self.session.client("s3", endpoint_url=self.endpoint_url, region_name=self.region) as s3:
                await s3.delete_object(Bucket=self.bucket, Key=filename)
        except Exception as e:
            raise StorageError(f"S3 delete operation failed: {str(e)}") from e

    async def download(self, filename: str) -> bytes:
        try:
            async with self.session.client("s3", endpoint_url=self.endpoint_url, region_name=self.region) as s3:
                response = await s3.get_object(Bucket=self.bucket, Key=filename)
                async with response['Body'] as stream:
                    return await stream.read()
        except Exception as e:
            raise StorageError(f"S3 download operation failed: {str(e)}") from e
