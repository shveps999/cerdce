from typing import Optional, BinaryIO
import aiofiles
import os
import uuid
from pathlib import Path
from .interfaces import FileStorageInterface


class LocalFileStorage(FileStorageInterface):
    """Локальное файловое хранилище через aiofiles"""
    
    def __init__(self, storage_path: str = "uploads"):
        """
        Args:
            storage_path: Путь к папке для хранения файлов
        """
        self.storage_path = Path(os.getcwd()) / Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def save_file(self, file_data: bytes, file_extension: str) -> str:
        """Сохранить файл локально"""
        # Генерируем уникальный id
        file_id = str(uuid.uuid4())
        file_path = self.storage_path / f"{file_id}.{file_extension}"
        
        # Сохраняем файл асинхронно
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)
        
        return file_id
    
    async def get_file(self, file_id: str) -> Optional[BinaryIO]:
        """Получить файл по id"""
        # Ищем файл по id (проверяем все возможные расширения)
        for file_path in self.storage_path.glob(f"{file_id}.*"):
            if file_path.exists():
                async with aiofiles.open(file_path, 'rb') as f:
                    return await f.read()
        return None
    
    async def delete_file(self, file_id: str) -> bool:
        """Удалить файл по id"""
        # Ищем файл по id
        for file_path in self.storage_path.glob(f"{file_id}.*"):
            if file_path.exists():
                file_path.unlink()
                return True
        return False
    
    def get_file_path(self, file_id: str) -> Optional[Path]:
        """Получить путь к файлу по id (для внутреннего использования)"""
        for file_path in self.storage_path.glob(f"{file_id}.*"):
            if file_path.exists():
                return file_path
        return None 