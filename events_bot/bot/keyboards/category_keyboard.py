from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from events_bot.database.models import Category

def get_category_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора категорий"""
    keyboard = [
        [KeyboardButton(text="✅ Подтвердить выбор")],
        [KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_category_selection_keyboard(categories: List[Category], selected_ids: List[int] = None) -> InlineKeyboardMarkup:
    """Инлайн клавиатура для выбора категорий"""
    if selected_ids is None:
        selected_ids = []
    
    keyboard = []
    for category in categories:
        is_selected = category.id in selected_ids
        text = f"{'✅' if is_selected else '⬜'} {category.name}"
        keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"category_{category.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_categories")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 