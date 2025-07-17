from typing import List
import logfire
from ..repositories import UserRepository
from ..models import User, Post, CategoryNames


class NotificationService:
    """Асинхронный сервис для работы с уведомлениями"""

    @staticmethod
    async def get_users_to_notify(db, post: Post) -> List[User]:
        """Получить пользователей для уведомления о новом посте"""
        # Загружаем связанные объекты
        await db.refresh(post, attribute_names=["author", "categories"])
        
        # Получаем пользователей по городу поста и категориям поста
        post_city = getattr(post, 'city', None)
        category_ids = [cat.id for cat in post.categories]
        logfire.info(f"Ищем пользователей для уведомления: город={post_city}, категории={category_ids}")
        
        users = await UserRepository.get_users_by_city_and_categories(
            db, post_city, category_ids
        )

        # Исключаем автора поста
        filtered_users = [user for user in users if user.id != post.author_id]
        logfire.info(f"Найдено {len(filtered_users)} пользователей для уведомления (исключая автора)")
        
        return filtered_users

    @staticmethod
    def format_post_notification(post: Post) -> str:
        """Форматировать уведомление о посте"""
        # Получаем текстовые названия категорий через CategoryNames
        category_names = []
        if hasattr(post, 'categories') and post.categories is not None:
            category_names = [
                CategoryNames.get_text_name(cat.id) 
                for cat in post.categories
                if getattr(cat, 'id', None) is not None
            ]
        
        category_str = ', '.join(category_names) if category_names else 'Неизвестно'
        
        author_name = 'Аноним'
        if hasattr(post, 'author') and post.author is not None:
            author = post.author
            author_name = (getattr(author, 'first_name', None) or 
                         getattr(author, 'username', None) or 'Аноним')
        
        published_at = getattr(post, 'published_at', None)
        published_str = published_at.strftime('%d.%m.%Y %H:%M') if published_at else ''
        
        return (
            f"Новый пост в категориях: {category_str}\n\n"
            f"🏷 {post.title}\n\n"
            f"📝 {post.content}\n\n"
            f"👤 Автор: {author_name}\n"
            f"⏰ {published_str}"
        )
