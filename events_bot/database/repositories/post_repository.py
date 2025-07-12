from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import List
from ..models import Post, ModerationRecord, ModerationAction
from ..models import User


class PostRepository:
    """Асинхронный репозиторий для работы с постами"""

    @staticmethod
    async def create_post(
        db: AsyncSession, title: str, content: str, author_id: int, category_id: int, image_id: str = None
    ) -> Post:
        post = Post(
            title=title, content=content, author_id=author_id, category_id=category_id, image_id=image_id
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    @staticmethod
    async def get_pending_moderation(db: AsyncSession) -> List[Post]:
        result = await db.execute(
            select(Post)
            .where(and_(Post.is_approved == False, Post.is_published == False))
            .options(selectinload(Post.author), selectinload(Post.category))
        )
        return result.scalars().all()

    @staticmethod
    async def get_approved_posts(db: AsyncSession) -> List[Post]:
        result = await db.execute(
            select(Post)
            .where(Post.is_approved == True)
            .options(selectinload(Post.author), selectinload(Post.category))
        )
        return result.scalars().all()

    @staticmethod
    async def get_posts_by_categories(
        db: AsyncSession, category_ids: List[int]
    ) -> List[Post]:
        result = await db.execute(
            select(Post)
            .where(and_(Post.category_id.in_(category_ids), Post.is_approved == True))
            .options(selectinload(Post.author), selectinload(Post.category))
        )
        return result.scalars().all()

    @staticmethod
    async def approve_post(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post:
            post.is_approved = True
            post.is_published = True
            post.published_at = func.now()
            moderation_record = ModerationRecord(
                post_id=post_id,
                moderator_id=moderator_id,
                action=ModerationAction.APPROVE,
                comment=comment,
            )
            db.add(moderation_record)
            await db.commit()
            await db.refresh(post)
        return post

    @staticmethod
    async def reject_post(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post:
            post.is_approved = False
            post.is_published = False
            moderation_record = ModerationRecord(
                post_id=post_id,
                moderator_id=moderator_id,
                action=ModerationAction.REJECT,
                comment=comment,
            )
            db.add(moderation_record)
            await db.commit()
            await db.refresh(post)
        return post

    @staticmethod
    async def request_changes(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post:
            moderation_record = ModerationRecord(
                post_id=post_id,
                moderator_id=moderator_id,
                action=ModerationAction.REQUEST_CHANGES,
                comment=comment,
            )
            db.add(moderation_record)
            await db.commit()
            await db.refresh(post)
        return post

    @staticmethod
    async def get_user_posts(db: AsyncSession, user_id: int) -> List[Post]:
        result = await db.execute(
            select(Post)
            .where(Post.author_id == user_id)
            .options(selectinload(Post.category))
        )
        return result.scalars().all()

    @staticmethod
    async def get_feed_posts(
        db: AsyncSession, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Post]:
        """Получить посты для ленты пользователя (по его категориям, исключая его посты)"""
        # Получаем категории пользователя
        user_categories_result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.categories))
        )
        user = user_categories_result.scalar_one_or_none()
        if not user or not user.categories:
            return []
        
        category_ids = [cat.id for cat in user.categories]
        
        # Получаем посты по категориям пользователя, исключая его собственные
        result = await db.execute(
            select(Post)
            .where(
                and_(
                    Post.category_id.in_(category_ids),
                    Post.is_approved == True,
                    Post.is_published == True,
                )
            )
            .options(selectinload(Post.author), selectinload(Post.category))
            .order_by(Post.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def get_feed_posts_count(db: AsyncSession, user_id: int) -> int:
        """Получить общее количество постов для ленты пользователя"""
        # Получаем категории пользователя
        user_categories_result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.categories))
        )
        user = user_categories_result.scalar_one_or_none()
        if not user or not user.categories:
            return 0
        
        category_ids = [cat.id for cat in user.categories]
        
        # Подсчитываем количество постов
        result = await db.execute(
            select(func.count(Post.id))
            .where(
                and_(
                    Post.category_id.in_(category_ids),
                    Post.is_approved == True,
                    Post.is_published == True,
                )
            )
        )
        return result.scalar() or 0
