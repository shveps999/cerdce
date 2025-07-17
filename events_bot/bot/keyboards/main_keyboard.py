from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню с кнопкой избранного"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📮\u00A0Смотреть подборку", callback_data="feed")
    builder.button(text="✏️\u00A0Создать событие", callback_data="create_post") 
    builder.button(text="❤️\u00A0Моё избранное", callback_data="liked_posts")
    builder.button(text="🎓\u00A0Изменить университет", callback_data="change_city")
    builder.button(text="🌟\u00A0Изменить категории", callback_data="change_category")
    builder.button(text="💬\u00A0Помощь", callback_data="help")
    
    builder.adjust(1)
    return builder.as_markup()

def get_category_selection_keyboard(categories, selected_ids=None, for_post=False):
    builder = InlineKeyboardBuilder()
    prefix = "post_category_" if for_post else "category_"
    
    for category in categories:
        emoji = "✅" if selected_ids and category.id in selected_ids else "⚪"
        builder.button(
            text=f"{emoji} {category.name}",
            callback_data=f"{prefix}{category.id}"
        )
    
    if for_post and selected_ids:
        builder.button(text="🔷 Подтвердить выбор", callback_data="confirm_post_categories")
    
    builder.button(text="🔙 Назад", callback_data="cancel_post" if for_post else "main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_city_keyboard(cities=None, for_post=False):
    builder = InlineKeyboardBuilder()
    
    if cities:
        for city in cities:
            prefix = "post_city_" if for_post else "city_"
            builder.button(text=city, callback_data=f"{prefix}{city}")
    else:
        builder.button(text="Москва", callback_data="post_city_Москва" if for_post else "city_Москва")
        builder.button(text="Санкт-Петербург", callback_data="post_city_Санкт-Петербург" if for_post else "city_Санкт-Петербург")
    
    builder.button(text="🔙 Назад", callback_data="cancel_post" if for_post else "main_menu")
    builder.adjust(1)
    return builder.as_markup()
