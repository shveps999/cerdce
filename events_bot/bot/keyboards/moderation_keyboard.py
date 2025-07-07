from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_moderation_keyboard(post_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для модерации поста"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Одобрить", callback_data=f"moderate_approve_{post_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить", callback_data=f"moderate_reject_{post_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📝 Запросить изменения",
                callback_data=f"moderate_changes_{post_id}",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_moderation_queue_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для очереди модерации"""
    keyboard = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_moderation")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
