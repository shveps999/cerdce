from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from ..models import Post, Like
from ..repositories import PostRepository
import os
import logfire
from events_bot.bot.keyboards.moderation_keyboard import get_moderation_keyboard
from events_bot.storage import file_storage
from aiogram.types import FSInputFile, InputMediaPhoto
from .moderation_service import ModerationService

class PostService:
    """Сервис для работы с постами"""

    @staticmethod
    async def create_post(
        db: AsyncSession, title: str, content: str, author_id: int,
        category_ids: List[int], city: str = None, image_id: str = None
    ) -> Post:
        return await PostRepository.create_post(
            db, title, content, author_id, category_ids, city, image_id
        )

    @staticmethod
    async def create_post_and_send_to_moderation(
        db: AsyncSession, title: str, content: str, author_id: int,
        category_ids: List[int], city: str = None, image_id: str = None, bot=None
    ) -> Post:
        post = await PostRepository.create_post(
            db, title, content, author_id, category_ids, city, image_id
        )
        
        if post and bot:
            await PostService.send_post_to_moderation(bot, post, db)
        
        return post

    @staticmethod
    async def send_post_to_moderation(bot, post: Post, db=None):
        moderation_group_id = os.getenv("MODERATION_GROUP_ID")
        if not moderation_group_id:
            logfire.error("MODERATION_GROUP_ID не установлен")
            return
        
        if db:
            await db.refresh(post, attribute_names=["author", "categories"])
        
        moderation_text = ModerationService.format_post_for_moderation(post)
        moderation_keyboard = get_moderation_keyboard(post.id)
        
        try:
            if post.image_id:
                media_photo = await file_storage.get_media_photo(post.image_id)
                if media_photo:
                    await bot.send_photo(
                        chat_id=moderation_group_id,
                        photo=media_photo.media,
                        caption=moderation_text,
                        reply_markup=moderation_keyboard
                    )
                    return
            
            await bot.send_message(
                chat_id=moderation_group_id,
                text=moderation_text,
                reply_markup=moderation_keyboard
            )
        except Exception as e:
            logfire.error(f"Ошибка отправки поста на модерацию: {e}")

    @staticmethod
    async def get_user_posts(db: AsyncSession, user_id: int) -> List[Post]:
        return await PostRepository.get_user_posts(db, user_id)

    @staticmethod
    async def get_post_by_id(db: AsyncSession, post_id: int) -> Optional[Post]:
        return await PostRepository.get_post_by_id(db, post_id)

    @staticmethod
    async def get_posts_by_categories(
        db: AsyncSession, category_ids: list[int]
    ) -> list[Post]:
        return await PostRepository.get_posts_by_categories(db, category_ids)

    @staticmethod
    async def get_pending_moderation_posts(db: AsyncSession) -> List[Post]:
        return await PostRepository.get_pending_moderation(db)

    @staticmethod
    async def approve_post(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        return await PostRepository.approve_post(db, post_id, moderator_id, comment)

    @staticmethod
    async def publish_post(db: AsyncSession, post_id: int) -> Post:
        return await PostRepository.publish_post(db, post_id)

    @staticmethod
    async def reject_post(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        return await PostRepository.reject_post(db, post_id, moderator_id, comment)

    @staticmethod
    async def request_changes(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        return await PostRepository.request_changes(db, post_id, moderator_id, comment)

    @staticmethod
    async def get_feed_posts(
        db: AsyncSession, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Post]:
        return await PostRepository.get_feed_posts(db, user_id, limit, offset)

    @staticmethod
    async def get_feed_posts_count(db: AsyncSession, user_id: int) -> int:
        return await PostRepository.get_feed_posts_count(db, user_id)

    @staticmethod
    async def get_liked_posts_with_details(db: AsyncSession, user_id: int) -> List[Post]:
        result = await db.execute(
            select(Post)
            .join(Like, Like.post_id == Post.id)
            .where(Like.user_id == user_id)
            .options(selectinload(Post.categories))
            .order_by(Like.created_at.desc())
        )
        
        posts = result.scalars().all()
        for post in posts:
            post.category_names = [c.name for c in post.categories]
            if post.likes:
                post.like_date = post.likes[0].created_at
        
        return posts

    @staticmethod
    async def remove_like(db: AsyncSession, user_id: int, post_id: int) -> bool:
        try:
            result = await db.execute(
                select(Like)
                .where(Like.user_id == user_id)
                .where(Like.post_id == post_id)
                .limit(1)
            )
            like = result.scalar_one_or_none()
            
            if like:
                await db.delete(like)
                await db.commit()
                return True
            return False
        except Exception as e:
            logfire.error(f"Error removing like: {e}")
            await db.rollback()
            return False
