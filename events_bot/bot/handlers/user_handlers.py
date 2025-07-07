from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService, CategoryService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import (
    get_main_keyboard,
    get_category_selection_keyboard,
    get_city_keyboard,
)
from events_bot.bot.utils import get_db_session

router = Router()


def register_user_handlers(dp: Router):
    """Регистрация обработчиков пользователя"""
    dp.include_router(router)


@router.message(UserStates.waiting_for_city, F.text)
async def process_city_selection(message: Message, state: FSMContext):
    """Обработчик выбора города"""
    if message.text == "🔙 Назад":
        await message.answer("Выберите город:", reply_markup=get_city_keyboard())
        return

    async with get_db_session() as db:
        # Обновляем город пользователя
        user = await UserService.register_user(
            db=db,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

        # Обновляем город в базе данных
        user.city = message.text
        await db.commit()

        # Получаем категории для выбора
        categories = await CategoryService.get_all_categories(db)

        await message.answer(
            f"🏙️ Город {message.text} выбран!\n\n"
            "Теперь выберите категорию для публикации постов:",
            reply_markup=get_category_selection_keyboard(categories),
        )
        await state.set_state(UserStates.waiting_for_categories)


@router.callback_query(F.data == "change_city")
async def change_city_callback(callback: CallbackQuery, state: FSMContext):
    """Изменение города через инлайн-кнопку"""
    await callback.message.edit_text(
        "Выберите новый город:", reply_markup=get_city_keyboard()
    )
    await state.set_state(UserStates.waiting_for_city)
    await callback.answer()


@router.callback_query(F.data == "change_category")
async def change_category_callback(callback: CallbackQuery, state: FSMContext):
    """Изменение категории через инлайн-кнопку"""
    async with get_db_session() as db:
        categories = await CategoryService.get_all_categories(db)
        user_categories = await UserService.get_user_categories(
            db, callback.from_user.id
        )
        selected_ids = [cat.id for cat in user_categories]

        await callback.message.edit_text(
            "Выберите категорию для публикации постов:",
            reply_markup=get_category_selection_keyboard(categories, selected_ids),
        )
        await state.set_state(UserStates.waiting_for_categories)
        await callback.answer()


@router.callback_query(F.data == "my_posts")
async def show_my_posts_callback(callback: CallbackQuery):
    """Показать посты пользователя через инлайн-кнопку"""
    from events_bot.database.services import PostService

    async with get_db_session() as db:
        posts = await PostService.get_user_posts(db, callback.from_user.id)

        if not posts:
            await callback.message.edit_text(
                "📭 У вас пока нет постов.", reply_markup=get_main_keyboard()
            )
            return

        response = "📊 Ваши посты:\n\n"
        for post in posts:
            status = "✅ Одобрен" if post.is_approved else "⏳ На модерации"
            response += f"📝 {post.title}\n"
            response += f"📂 {post.category.name}\n"
            response += f"📅 {post.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            response += f"📊 {status}\n\n"

        await callback.message.edit_text(response, reply_markup=get_main_keyboard())
        await callback.answer()


@router.callback_query(F.data == "help")
async def show_help_callback(callback: CallbackQuery):
    """Показать справку через инлайн-кнопку"""
    help_text = """
ℹ️ **Справка по боту**

🤖 **Основные функции:**
• 📝 Создать пост - создание нового поста в выбранной категории
• 📊 Мои посты - просмотр ваших опубликованных постов
• 🏙️ Изменить город - смена города для получения уведомлений
• 📂 Изменить категорию - смена категории для публикации постов

📋 **Как использовать:**
1. Выберите город проживания
2. Выберите категорию для публикации постов
3. Создавайте посты в выбранной категории
4. Получайте уведомления о новых постах в вашем городе

📝 **Создание поста:**
• Заголовок: до 200 символов
• Содержание: до 4000 символов
• Посты проходят модерацию перед публикацией

❓ **Поддержка:** Обратитесь к администратору бота
"""

    await callback.message.edit_text(
        help_text, reply_markup=get_main_keyboard(), parse_mode="Markdown"
    )
    await callback.answer()
