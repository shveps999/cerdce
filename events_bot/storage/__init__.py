from .file_storage import FileStorageInterface, LocalFileStorage

# Инициализируем файловое хранилище для использования во всем приложении
file_storage = LocalFileStorage()

__all__ = ["FileStorageInterface", "LocalFileStorage", "file_storage"] 