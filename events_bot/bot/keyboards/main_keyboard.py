from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главная инлайн-клавиатура с основными действиями"""
    keyboard = [
        [InlineKeyboardButton(text="📝 Создать пост", callback_data="create_post")],
        [InlineKeyboardButton(text="📊 Мои посты", callback_data="my_posts")],
        [InlineKeyboardButton(text="🏙️ Изменить город", callback_data="change_city")],
        [
            InlineKeyboardButton(
                text="📂 Изменить категорию", callback_data="change_category"
            )
        ],
        [InlineKeyboardButton(text="🔍 Модерация", callback_data="moderation")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
