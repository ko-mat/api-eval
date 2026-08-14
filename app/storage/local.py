import os
import aiofiles
from typing import BinaryIO
from app.storage.base import StorageService, StorageError

class LocalStorage(StorageService):
    def __init__(self, base_dir: str, base_url: str):
        self.base_dir = os.path.abspath(base_dir)
        self.base_url = base_url.rstrip("/")

    async def upload(self, file: BinaryIO, filename: str) -> str:
        try:
            # Prevent directory traversal by cleaning up path
            clean_filename = os.path.normpath(filename).lstrip(os.sep).replace("..", "")
            dest_path = os.path.join(self.base_dir, clean_filename)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # Reset file pointer if seek exists
            if hasattr(file, "seek"):
                file.seek(0)
            
            # Write asynchronously in chunks
            async with aiofiles.open(dest_path, "wb") as out_file:
                while content := file.read(1024 * 64):  # 64KB chunks
                    await out_file.write(content)
                    
            url_path = clean_filename.replace(os.sep, "/")
            return f"{self.base_url}/static/{url_path}"
        except Exception as e:
            raise StorageError(f"Failed to upload file to local storage: {str(e)}") from e

    async def delete(self, filename: str) -> None:
        try:
            clean_filename = os.path.normpath(filename).lstrip(os.sep).replace("..", "")
            dest_path = os.path.join(self.base_dir, clean_filename)
            if os.path.exists(dest_path):
                os.remove(dest_path)
        except Exception as e:
            raise StorageError(f"Failed to delete file from local storage: {str(e)}") from e

    async def download(self, filename: str) -> bytes:
        try:
            clean_filename = os.path.normpath(filename).lstrip(os.sep).replace("..", "")
            dest_path = os.path.join(self.base_dir, clean_filename)
            if not os.path.exists(dest_path):
                raise StorageError("File not found in local storage.")
            async with aiofiles.open(dest_path, "rb") as f:
                return await f.read()
        except Exception as e:
            raise StorageError(f"Failed to download file from local storage: {str(e)}") from e
