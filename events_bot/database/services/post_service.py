from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..repositories import PostRepository, UserRepository
from ..models import Post
import os
import logfire
from events_bot.bot.keyboards.moderation_keyboard import get_moderation_keyboard
from events_bot.storage import file_storage
from aiogram.types import FSInputFile, InputMediaPhoto
from .moderation_service import ModerationService
from .notification_service import NotificationService


class PostService:
    """Асинхронный сервис для работы с постами"""

    @staticmethod
    async def create_post(
        db: AsyncSession, 
        title: str, 
        content: str, 
        author_id: int, 
        category_ids: List[int], 
        city: str = None, 
        image_id: str = None
    ) -> Post:
        """Создать новый пост"""
        return await PostRepository.create_post(
            db, title, content, author_id, category_ids, city, image_id
        )

    @staticmethod
    async def create_post_and_send_to_moderation(
        db: AsyncSession, 
        title: str, 
        content: str, 
        author_id: int, 
        category_ids: List[int], 
        city: str = None, 
        image_id: str = None, 
        bot=None
    ) -> Post:
        """Создать пост и отправить на модерацию"""
        post = await PostRepository.create_post(
            db, title, content, author_id, category_ids, city, image_id
        )
        
        if post and bot:
            await PostService.send_post_to_moderation(bot, post, db)
        
        return post

    @staticmethod
    async def send_post_to_moderation(bot, post: Post, db=None):
        """Отправить пост на модерацию"""
        moderation_group_id = os.getenv("MODERATION_GROUP_ID")
        logfire.info(f"MODERATION_GROUP_ID: {moderation_group_id}")
        
        if not moderation_group_id:
            logfire.error("MODERATION_GROUP_ID не установен")
            return
        
        if db:
            await db.refresh(post, attribute_names=["author", "categories"])
        
        moderation_text = ModerationService.format_post_for_moderation(post)
        moderation_keyboard = get_moderation_keyboard(post.id)
        
        logfire.info(f"Отправляем пост {post.id} на модерацию в группу {moderation_group_id}")
        
        try:
            if post.image_id:
                logfire.info(f"Пост содержит изображение: {post.image_id}")
                media_photo = await file_storage.get_media_photo(post.image_id)
                if media_photo:
                    await bot.send_photo(
                        chat_id=moderation_group_id,
                        photo=media_photo.media,
                        caption=moderation_text,
                        reply_markup=moderation_keyboard
                    )
                    return
                else:
                    logfire.warning("Изображение не найдено")
            
            await bot.send_message(
                chat_id=moderation_group_id,
                text=moderation_text,
                reply_markup=moderation_keyboard
            )
        except Exception as e:
            logfire.error(f"Ошибка отправки поста на модерацию: {e}")
            import traceback
            logfire.error(f"Стек ошибки: {traceback.format_exc()}")

    @staticmethod
    async def get_user_posts(db: AsyncSession, user_id: int) -> List[Post]:
        """Получить посты пользователя"""
        return await PostRepository.get_user_posts(db, user_id)

    @staticmethod
    async def get_post_by_id(db: AsyncSession, post_id: int) -> Optional[Post]:
        """Получить пост по ID"""
        return await PostRepository.get_post_by_id(db, post_id)

    @staticmethod
    async def get_posts_by_categories(
        db: AsyncSession, category_ids: list[int]
    ) -> list[Post]:
        """Получить посты по нескольким категориям"""
        return await PostRepository.get_posts_by_categories(db, category_ids)

    @staticmethod
    async def get_pending_moderation_posts(db: AsyncSession) -> List[Post]:
        """Получить посты, ожидающие модерации"""
        return await PostRepository.get_pending_moderation(db)

    @staticmethod
    async def approve_post(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        """Одобрить пост"""
        return await PostRepository.approve_post(db, post_id, moderator_id, comment)

    @staticmethod
    async def publish_post(
        db: AsyncSession, post_id: int, bot=None
    ) -> Post:
        """Опубликовать одобренный пост и отправить уведомления"""
        post = await PostRepository.publish_post(db, post_id)
        
        if post and bot:
            # Получаем пользователей для уведомления (уникальных)
            users_to_notify = await NotificationService.get_users_to_notify(db, post)
            
            # Формируем сообщение
            message = NotificationService.format_post_notification(post)
            
            # Отправляем уведомления
            for user in users_to_notify:
                try:
                    await bot.send_message(
                        chat_id=user.id,
                        text=message,
                        parse_mode="MarkdownV2"
                    )
                    logfire.info(f"Уведомление отправлено пользователю {user.id}")
                except Exception as e:
                    logfire.error(f"Ошибка отправки уведомления пользователю {user.id}: {e}")
        
        return post

    @staticmethod
    async def reject_post(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        """Отклонить пост"""
        return await PostRepository.reject_post(db, post_id, moderator_id, comment)

    @staticmethod
    async def request_changes(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        """Запросить изменения в посте"""
        return await PostRepository.request_changes(db, post_id, moderator_id, comment)

    @staticmethod
    async def get_feed_posts(
        db: AsyncSession, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Post]:
        """Получить посты для ленты пользователя"""
        return await PostRepository.get_feed_posts(db, user_id, limit, offset)

    @staticmethod
    async def get_feed_posts_count(db: AsyncSession, user_id: int) -> int:
        """Получить общее количество постов для ленты пользователя"""
        return await PostRepository.get_feed_posts_count(db, user_id)
