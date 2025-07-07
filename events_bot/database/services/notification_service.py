from typing import List
from ..repositories import UserRepository
from ..models import User, Post


class NotificationService:
    """Асинхронный сервис для работы с уведомлениями"""

    @staticmethod
    async def get_users_to_notify(db, post: Post) -> List[User]:
        """Получить пользователей для уведомления о новом посте"""
        # Получаем пользователей по городу и категории поста
        users = await UserRepository.get_users_by_city_and_categories(
            db, post.author.city, [post.category_id]
        )

        # Исключаем автора поста
        return [user for user in users if user.id != post.author_id]

    @staticmethod
    def format_post_notification(post: Post) -> str:
        """Форматировать уведомление о посте"""
        return (
            f"📢 Новый пост в категории '{post.category.name}'\n\n"
            f"📝 {post.title}\n\n"
            f"{post.content}\n\n"
            f"👤 Автор: {post.author.first_name or post.author.username or 'Аноним'}\n"
            f"📅 {post.published_at.strftime('%d.%m.%Y %H:%M') if post.published_at else ''}"
        )
