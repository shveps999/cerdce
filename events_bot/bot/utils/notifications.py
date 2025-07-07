from aiogram import Bot
from typing import List
from events_bot.database.models import User, Post
from events_bot.database.services import NotificationService
import logfire


async def send_post_notification(bot: Bot, post: Post, users: List[User]) -> None:
    """Отправить уведомления о новом посте"""
    notification_text = NotificationService.format_post_notification(post)

    for user in users:
        try:
            await bot.send_message(chat_id=user.id, text=notification_text)
        except Exception as e:
            logfire.warning(f"Error sending notification to user {user.id}: {e}")
