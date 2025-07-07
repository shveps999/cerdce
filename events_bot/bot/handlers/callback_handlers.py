from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService, CategoryService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import get_category_selection_keyboard, get_main_keyboard
from events_bot.bot.utils import get_db_session

router = Router()

def register_callback_handlers(dp: Router):
    """Регистрация обработчиков callback"""
    dp.include_router(router)

@router.callback_query(F.data.startswith("category_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    category_id = int(callback.data.split("_")[1])
    
    async with get_db_session() as db:
        # Получаем все категории
        categories = await CategoryService.get_all_categories(db)
        
        # Выбираем только одну категорию
        selected_ids = [category_id]
        await state.update_data(selected_categories=selected_ids)
        
        # Обновляем клавиатуру
        await callback.message.edit_reply_markup(
            reply_markup=get_category_selection_keyboard(categories, selected_ids)
        )

@router.callback_query(F.data == "confirm_categories")
async def confirm_categories_selection(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора категории"""
    data = await state.get_data()
    selected_ids = data.get('selected_categories', [])
    
    if not selected_ids:
        await callback.answer("❌ Выберите категорию!")
        return
    
    async with get_db_session() as db:
        # Сохраняем выбранную категорию пользователю
        await UserService.select_categories(db, callback.from_user.id, selected_ids)
        
        # Получаем название выбранной категории
        categories = await CategoryService.get_all_categories(db)
        selected_category = next((cat for cat in categories if cat.id in selected_ids), None)
        
        if selected_category:
            await callback.message.edit_text(
                f"✅ Категория выбрана: {selected_category.name}\n\n"
                "Теперь вы можете создавать посты в этой категории."
            )
        
        await callback.message.edit_text(
            "Выберите действие:",
            reply_markup=get_main_keyboard()
        )
        await state.clear() 