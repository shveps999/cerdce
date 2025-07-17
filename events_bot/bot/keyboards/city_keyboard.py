from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_city_keyboard(for_post: bool = False, selected_cities: List[str] = None) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора города с эмодзи выбора"""
    if selected_cities is None:
        selected_cities = []
    
    cities = [
        "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург",
        "Казань", "Нижний Новгород", "Челябинск", "Самара",
        "Уфа", "Ростов-на-Дону"
    ]
    
    builder = InlineKeyboardBuilder()
    prefix = "post_city_" if for_post else "city_"
    
    for city in cities:
        # Добавляем эмодзи выбора если город выбран
        emoji = "⭐️" if city in selected_cities else "▫️"
        builder.button(text=f"{emoji} {city}", callback_data=f"{prefix}{city}")
    
    builder.adjust(2)
    
    buttons = []
    
    if for_post:
        buttons.append(
            InlineKeyboardButton(
                text="❌ Отмена", callback_data="cancel_post"
            )
        )
    
    if buttons:
        builder.row(*buttons)
    
    return builder.as_markup()
