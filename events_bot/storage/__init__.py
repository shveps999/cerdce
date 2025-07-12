import os
import logfire
from .interfaces import FileStorageInterface
from .file_storage import LocalFileStorage
from .s3_storage import S3FileStorage

# Инициализируем файловое хранилище в зависимости от окружения
def get_file_storage() -> FileStorageInterface:
    """Получить подходящее файловое хранилище в зависимости от окружения"""
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        try:
            return S3FileStorage()
        except ValueError as e:
            logfire.warning(f"Failed to initialize S3 storage: {e}, falling back to local storage")
            return LocalFileStorage()
    else:
        return LocalFileStorage()

# Инициализируем файловое хранилище для использования во всем приложении
file_storage = get_file_storage()

__all__ = ["FileStorageInterface", "LocalFileStorage", "S3FileStorage", "file_storage", "get_file_storage"] 