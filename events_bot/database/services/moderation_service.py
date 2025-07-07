from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..repositories import PostRepository, ModerationRepository
from ..models import Post, ModerationAction


class ModerationService:
    """Асинхронный сервис для работы с модерацией"""

    @staticmethod
    async def get_moderation_queue(db: AsyncSession) -> List[Post]:
        """Получить очередь модерации"""
        return await PostRepository.get_pending_moderation(db)

    @staticmethod
    async def get_moderation_history(db: AsyncSession, post_id: int) -> List:
        """Получить историю модерации поста"""
        return await ModerationRepository.get_moderation_history(db, post_id)

    @staticmethod
    async def get_actions_by_type(db: AsyncSession, action: ModerationAction) -> List:
        """Получить записи модерации по типу действия"""
        return await ModerationRepository.get_actions_by_type(db, action)

    @staticmethod
    def format_post_for_moderation(post: Post) -> str:
        """Форматировать пост для модерации"""
        return (
            f"📋 Пост на модерацию\n\n"
            f"📝 Заголовок: {post.title}\n"
            f"📂 Категория: {post.category.name}\n"
            f"👤 Автор: {post.author.first_name or post.author.username or 'Аноним'}\n"
            f"📅 Создан: {post.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📄 Содержание:\n{post.content}\n\n"
            f"🆔 ID поста: {post.id}"
        )

    @staticmethod
    def get_action_display_name(action: ModerationAction) -> str:
        """Получить отображаемое имя действия"""
        action_names = {
            ModerationAction.APPROVE: "Одобрено",
            ModerationAction.REJECT: "Отклонено",
            ModerationAction.REQUEST_CHANGES: "Требуются изменения",
        }
        return action_names.get(action, "Неизвестно")
