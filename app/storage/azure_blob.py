from typing import BinaryIO
from azure.storage.blob.aio import BlobServiceClient
from app.storage.base import StorageService, StorageError

class AzureBlobStorage(StorageService):
    def __init__(self, connection_string: str, container_name: str):
        self.connection_string = connection_string
        self.container_name = container_name

    async def upload(self, file: BinaryIO, filename: str) -> str:
        try:
            if hasattr(file, "seek"):
                file.seek(0)
            
            data = file.read()
            client = BlobServiceClient.from_connection_string(self.connection_string)
            async with client as service:
                blob_client = service.get_blob_client(container=self.container_name, blob=filename)
                await blob_client.upload_blob(data, overwrite=True)
                return blob_client.url
        except Exception as e:
            raise StorageError(f"Azure Blob upload operation failed: {str(e)}") from e

    async def delete(self, filename: str) -> None:
        try:
            client = BlobServiceClient.from_connection_string(self.connection_string)
            async with client as service:
                blob_client = service.get_blob_client(container=self.container_name, blob=filename)
                await blob_client.delete_blob()
        except Exception as e:
            raise StorageError(f"Azure Blob delete operation failed: {str(e)}") from e

    async def download(self, filename: str) -> bytes:
        try:
            client = BlobServiceClient.from_connection_string(self.connection_string)
            async with client as service:
                blob_client = service.get_blob_client(container=self.container_name, blob=filename)
                download_stream = await blob_client.download_blob()
                return await download_stream.readall()
        except Exception as e:
            raise StorageError(f"Azure Blob download failed: {str(e)}") from e
