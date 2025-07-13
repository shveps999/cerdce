#!/usr/bin/env python3
"""
Тест для S3 storage
"""

import asyncio
import os
from events_bot.storage import S3FileStorage, LocalFileStorage


async def test_storage():
    """Тестирование файлового хранилища"""
    
    # Тестируем локальное хранилище
    print("🧪 Тестирование локального хранилища...")
    local_storage = LocalFileStorage()
    
    # Тестовые данные
    test_data = b"test image data"
    file_extension = "jpg"
    
    # Сохраняем файл
    file_id = await local_storage.save_file(test_data, file_extension)
    print(f"✅ Файл сохранен с ID: {file_id}")
    
    # Получаем файл как InputMediaPhoto
    media_photo = await local_storage.get_media_photo(file_id)
    if media_photo:
        print("✅ Файл успешно получен как InputMediaPhoto")
    else:
        print("❌ Ошибка при получении файла")
    
    # Генерируем URL
    url = await local_storage.get_file_url(file_id)
    if url:
        print(f"✅ URL сгенерирован: {url}")
    else:
        print("❌ Ошибка при генерации URL")
    
    # Удаляем файл
    if await local_storage.delete_file(file_id):
        print("✅ Файл успешно удален")
    else:
        print("❌ Ошибка при удалении файла")
    
    # Тестируем S3 storage (если настроены переменные окружения)
    if os.getenv("S3_BUCKET_NAME") and os.getenv("AWS_ACCESS_KEY_ID"):
        print("\n🧪 Тестирование S3 хранилища...")
        try:
            s3_storage = S3FileStorage()
            
            # Тестируем подключение
            if await s3_storage.test_connection():
                print("✅ Подключение к S3 успешно")
                
                # Сохраняем файл
                file_id = await s3_storage.save_file(test_data, file_extension)
                print(f"✅ Файл сохранен в S3 с ID: {file_id}")
                
                # Получаем файл как InputMediaPhoto
                media_photo = await s3_storage.get_media_photo(file_id)
                if media_photo:
                    print("✅ Файл успешно получен из S3 как InputMediaPhoto")
                else:
                    print("❌ Ошибка при получении файла из S3")
                
                # Генерируем URL
                url = await s3_storage.get_file_url(file_id)
                if url:
                    print(f"✅ URL сгенерирован: {url[:50]}...")
                else:
                    print("❌ Ошибка при генерации URL")
                
                # Удаляем файл
                if await s3_storage.delete_file(file_id):
                    print("✅ Файл успешно удален из S3")
                else:
                    print("❌ Ошибка при удалении файла из S3")
            else:
                print("❌ Не удалось подключиться к S3")
                
        except Exception as e:
            print(f"❌ Ошибка при тестировании S3: {e}")
    else:
        print("\n⚠️ S3 переменные окружения не настроены, пропускаем тест S3")


if __name__ == "__main__":
    asyncio.run(test_storage()) 