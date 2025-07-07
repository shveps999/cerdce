from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import List
from ..models import Post, ModerationRecord, ModerationAction


class PostRepository:
    """Асинхронный репозиторий для работы с постами"""

    @staticmethod
    async def create_post(
        db: AsyncSession, title: str, content: str, author_id: int, category_id: int
    ) -> Post:
        post = Post(
            title=title, content=content, author_id=author_id, category_id=category_id
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
