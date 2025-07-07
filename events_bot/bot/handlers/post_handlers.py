from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import PostService
from events_bot.bot.states import PostStates
from events_bot.bot.keyboards import get_main_keyboard
from events_bot.bot.utils import get_db_session

router = Router()

def register_post_handlers(dp: Router):
    """Регистрация обработчиков постов"""
    dp.include_router(router)

@router.callback_query(F.data == "create_post")
async def start_create_post(callback: CallbackQuery, state: FSMContext):
    """Начало создания поста через инлайн-кнопку"""
    await callback.message.edit_text(
        "📝 Создание нового поста\n\n"
        "Введите заголовок поста:",
        reply_markup=get_main_keyboard()
    )
    await state.set_state(PostStates.waiting_for_title)
    await callback.answer()

@router.message(PostStates.waiting_for_title, F.text)
async def process_post_title(message: Message, state: FSMContext):
    """Обработка заголовка поста"""
    if len(message.text) > 200:
        await message.answer("❌ Заголовок слишком длинный. Максимум 200 символов.")
        return
    
    await state.update_data(title=message.text)
    await message.answer(
        "📄 Теперь введите содержание поста:"
    )
    await state.set_state(PostStates.waiting_for_content)

@router.message(PostStates.waiting_for_content, F.text)
async def process_post_content(message: Message, state: FSMContext):
    """Обработка содержания поста"""
    if len(message.text) > 4000:
        await message.answer("❌ Содержание слишком длинное. Максимум 4000 символов.")
        return
    
    await state.update_data(content=message.text)
    
    # Получаем выбранную категорию пользователя
    async with get_db_session() as db:
        from events_bot.database.services import UserService
        user_categories = await UserService.get_user_categories(db, message.from_user.id)
        
        if not user_categories:
            await message.answer(
                "❌ У вас не выбрана категория. Сначала выберите категорию в настройках.",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
        
        selected_category = user_categories[0]  # Берем первую (и единственную) категорию
        
        # Получаем данные поста
        data = await state.get_data()
        title = data.get('title')
        content = message.text
        
        # Создаем пост в выбранной категории
        post = await PostService.create_post(
            db=db,
            title=title,
            content=content,
            author_id=message.from_user.id,
            category_id=selected_category.id
        )
        
        await message.answer(
            f"✅ Пост создан и отправлен на модерацию!\n\n"
            f"📝 Заголовок: {title}\n"
            f"📂 Категория: {selected_category.name}\n\n"
            f"Пост будет опубликован после одобрения модератором.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

 