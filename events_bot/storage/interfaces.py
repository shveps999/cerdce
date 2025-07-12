from abc import ABC, abstractmethod
from typing import Optional, BinaryIO


class FileStorageInterface(ABC):
    """Абстрактный интерфейс для файлового хранилища"""
    
    @abstractmethod
    async def save_file(self, file_data: BinaryIO, file_extension: str) -> str:
        """
        Сохранить файл и вернуть его id
        
        Args:
            file_data: Файловый объект с данными
            file_extension: Расширение файла (например, '.jpg')
            
        Returns:
            str: Уникальный id файла
        """
        pass
    
    @abstractmethod
    async def get_file(self, file_id: str) -> Optional[BinaryIO]:
        """
        Получить файл по id
        
        Args:
            file_id: Id файла
            
        Returns:
            Optional[BinaryIO]: Файловый объект или None если файл не найден
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """
        Удалить файл по id
        
        Args:
            file_id: Id файла
            
        Returns:
            bool: True если файл удален, False если файл не найден
        """
        pass 