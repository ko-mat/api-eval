from abc import ABC, abstractmethod
from typing import BinaryIO

class StorageError(Exception):
    """Exception raised when storage operations fail."""
    pass

class StorageService(ABC):

    @abstractmethod
    async def upload(self, file: BinaryIO, filename: str) -> str:
        """
        Uploads a file asynchronously to the storage backend.
        
        Args:
            file (BinaryIO): The file-like object to upload.
            filename (str): The destination path/filename in the storage.
            
        Returns:
            str: The public access URL or path of the uploaded file.
            
        Raises:
            StorageError: If the upload operation fails.
        """
        pass

    @abstractmethod
    async def delete(self, filename: str) -> None:
        """
        Deletes a file asynchronously from the storage backend.
        
        Args:
            filename (str): The filename/path of the target file to delete.
            
        Raises:
            StorageError: If the deletion operation fails.
        """
        pass

    @abstractmethod
    async def download(self, filename: str) -> bytes:
        """
        Downloads a file asynchronously from the storage backend.
        
        Args:
            filename (str): The filename/path of the target file to download.
            
        Returns:
            bytes: The downloaded file contents.
            
        Raises:
            StorageError: If the download operation fails.
        """
        pass
