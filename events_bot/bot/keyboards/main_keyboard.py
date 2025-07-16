from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главная инлайн-клавиатура с основными действиями (выравнивание по левому краю)"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📮 Смотреть подборку", callback_data="feed")
    builder.button(text="✏️ Создать свое", callback_data="create_post")
    builder.button(text="🤍 Мои события", callback_data="my_posts")
    builder.button(text="🎓 Изменить", callback_data="change_city")
    builder.button(text="🌟 Изменить", callback_data="change_category")
    builder.button(text="💬 Помощь", callback_data="help")
    
    return builder.as_markup()
