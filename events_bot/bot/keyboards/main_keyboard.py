from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главная инлайн-клавиатура с улучшенной видимостью текста"""
    builder = InlineKeyboardBuilder()
    
    # Добавляем неразрывный пробел после эмодзи для лучшего отображения
    builder.button(text="📮\u00A0Смотреть подборку", callback_data="feed")
    builder.button(text="✏️\u00A0Создать событие", callback_data="create_post") 
    builder.button(text="🎓\u00A0Изменить университет", callback_data="change_city")
    builder.button(text="🌟\u00A0Изменить категории", callback_data="change_category")
    builder.button(text="❤️\u00A0Мои события", callback_data="my_posts") 
    builder.button(text="💬\u00A0Помощь", callback_data="help")
    
    builder.adjust(1)  # Одна кнопка в строке
    return builder.as_markup()
