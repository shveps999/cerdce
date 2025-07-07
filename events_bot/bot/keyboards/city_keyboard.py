from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_city_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора города"""
    keyboard = [
        [KeyboardButton(text="Москва"), KeyboardButton(text="Санкт-Петербург")],
        [KeyboardButton(text="Новосибирск"), KeyboardButton(text="Екатеринбург")],
        [KeyboardButton(text="Казань"), KeyboardButton(text="Нижний Новгород")],
        [KeyboardButton(text="Челябинск"), KeyboardButton(text="Самара")],
        [KeyboardButton(text="Уфа"), KeyboardButton(text="Ростов-на-Дону")],
        [KeyboardButton(text="🔙 Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
