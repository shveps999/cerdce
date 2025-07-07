#!/usr/bin/env python3
"""
Тестовый бот с временной базой данных
Запуск: TEST_MODE=true python test_bot.py
"""

import asyncio
import os
from aiogram import Bot, Dispatcher
from events_bot.database.connection import create_async_engine_and_session, create_tables
from events_bot.database.init_db import init_database
from events_bot.bot.handlers import (
    register_start_handler,
    register_user_handlers,
    register_post_handlers,
    register_callback_handlers,
    register_moderation_handlers
)
import logfire

async def main():
    """Основная функция запуска тестового бота"""
    # Устанавливаем переменную окружения для тестового режима
    os.environ['TEST_MODE'] = 'true'
    
    # Получаем токен бота
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logfire.error("BOT_TOKEN не найден в переменных окружения")
        return
    
    # Создаем бота и диспетчер
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    
    # Создаем временную базу данных в памяти
    engine, session_maker = create_async_engine_and_session()
    
    # Инициализируем базу данных
    await create_tables(engine)
    await init_database(session_maker)
    
    logfire.info("Тестовый бот запущен с временной базой данных в памяти")
    logfire.info("База данных будет очищена при перезапуске бота")
    
    # Регистрируем обработчики
    register_start_handler(dp)
    register_user_handlers(dp)
    register_post_handlers(dp)
    register_callback_handlers(dp)
    register_moderation_handlers(dp)
    
    try:
        # Запускаем бота
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logfire.info("Тестовый бот остановлен")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 