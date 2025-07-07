#!/usr/bin/env python3
"""
Telegram Events Bot - Основной файл приложения
"""

import logfire

logfire.configure()

import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from events_bot.database import init_database
from events_bot.bot.handlers import (
    register_start_handlers,
    register_user_handlers,
    register_post_handlers,
    register_callback_handlers,
    register_moderation_handlers,
)


async def main():
    """Главная функция бота"""
    # Получаем токен из переменных окружения
    token = os.getenv("BOT_TOKEN")
    if not token:
        logfire.error("❌ Error: BOT_TOKEN not set")
        return

    # Инициализируем базу данных

    with logfire.span("🔧 Initializing database..."):
        await init_database()
    logfire.info("✅ Database initialized")

    # Создаем бота и диспетчер
    bot = Bot(token=token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем обработчики
    register_start_handlers(dp)
    register_user_handlers(dp)
    register_post_handlers(dp)
    register_callback_handlers(dp)
    register_moderation_handlers(dp)

    logfire.info("🤖 Bot started...")

    try:
        # Запускаем бота
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logfire.info("🛑 Bot stopped")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
