from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главная инлайн-клавиатура с основными действиями (выравнивание по левому краю)"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Создать пост", callback_data="create_post")
    builder.button(text="📊 Мои посты", callback_data="my_posts")
    builder.button(text="📰 Лента", callback_data="feed")
    builder.button(text="🏙️ Изменить город", callback_data="change_city")
    builder.button(text="📂 Изменить категорию", callback_data="change_category")
    builder.button(text="🔍 Модерация", callback_data="moderation")
    builder.button(text="ℹ️ Помощь", callback_data="help")
    
    # Ключевое изменение - выравниваем все кнопки по левому краю
    builder.adjust(1, repeat=True)
    
    return builder.as_markup()
