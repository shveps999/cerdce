from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService, CategoryService, PostService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import (
    get_main_keyboard,
    get_category_selection_keyboard,
    get_city_keyboard,
)
from events_bot.bot.messages import UserMessages, CommonMessages

router = Router()


def register_user_handlers(dp: Router):
    """Регистрация обработчиков пользователя"""
    dp.include_router(router)


@router.message(F.text == "/my_posts")
async def cmd_my_posts(message: Message, db):
    """Обработчик команды /my_posts"""
    posts = await PostService.get_user_posts(db, message.from_user.id)

    if not posts:
        await message.answer(
            UserMessages.MY_POSTS_EMPTY, reply_markup=get_main_keyboard()
        )
        return

    response = UserMessages.MY_POSTS_HEADER
    for post in posts:
        # Загружаем связанные объекты
        await db.refresh(post, attribute_names=["categories"])
        status = "✅ Одобрен" if post.is_approved else "⏳ На модерации"
        category_names = [cat.name for cat in post.categories] if post.categories else ['Неизвестно']
        category_str = ', '.join(category_names)
        post_city = getattr(post, 'city', 'Не указан')
        response += f"📝 {post.title}\n"
        response += f"🏙️ {post_city}\n"
        response += f"📂 {category_str}\n"
        response += f"📅 {post.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        response += f"📊 {status}\n\n"

    await message.answer(response, reply_markup=get_main_keyboard())


@router.message(F.text == "/change_city")
async def cmd_change_city(message: Message, state: FSMContext):
    """Обработчик команды /change_city"""
    await message.answer(
        UserMessages.SELECT_CATEGORIES, reply_markup=get_city_keyboard()
    )
    await state.set_state(UserStates.waiting_for_city)


@router.message(F.text == "/change_category")
async def cmd_change_category(message: Message, state: FSMContext, db):
    """Обработчик команды /change_category"""
    categories = await CategoryService.get_all_categories(db)
    user_categories = await UserService.get_user_categories(
        db, message.from_user.id
    )
    selected_ids = [cat.id for cat in user_categories]

    await message.answer(
        UserMessages.SELECT_CATEGORIES,
        reply_markup=get_category_selection_keyboard(categories, selected_ids),
    )
    await state.set_state(UserStates.waiting_for_categories)


@router.message(F.text == "/help")
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        CommonMessages.HELP_GENERAL, reply_markup=get_main_keyboard(), parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("city_"))
async def process_city_selection_callback(callback: CallbackQuery, state: FSMContext, db):
    """Обработка выбора города через инлайн-кнопку"""
    city = callback.data[5:]

    # Обновляем город пользователя
    user = await UserService.register_user(
        db=db,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
    )
    user.city = city
    await db.commit()
    categories = await CategoryService.get_all_categories(db)
    await callback.message.edit_text(
        UserMessages.SELECT_CATEGORIES,
        reply_markup=get_category_selection_keyboard(categories),
    )
    await state.set_state(UserStates.waiting_for_categories)
    await callback.answer()


@router.callback_query(F.data == "change_city")
async def change_city_callback(callback: CallbackQuery, state: FSMContext):
    """Изменение города через инлайн-кнопку"""
    await callback.message.edit_text(
        UserMessages.SELECT_CATEGORIES, reply_markup=get_city_keyboard()
    )
    await state.set_state(UserStates.waiting_for_city)
    await callback.answer()


@router.callback_query(F.data == "change_category")
async def change_category_callback(callback: CallbackQuery, state: FSMContext, db):
    """Изменение категории через инлайн-кнопку"""
    categories = await CategoryService.get_all_categories(db)
    user_categories = await UserService.get_user_categories(
        db, callback.from_user.id
    )
    selected_ids = [cat.id for cat in user_categories]

    await callback.message.edit_text(
        UserMessages.SELECT_CATEGORIES,
        reply_markup=get_category_selection_keyboard(categories, selected_ids),
    )
    await state.set_state(UserStates.waiting_for_categories)
    await callback.answer()


@router.callback_query(F.data == "my_posts")
async def show_my_posts_callback(callback: CallbackQuery, db):
    """Показать посты пользователя через инлайн-кнопку"""
    posts = await PostService.get_user_posts(db, callback.from_user.id)

    if not posts:
        await callback.message.edit_text(
            UserMessages.MY_POSTS_EMPTY, reply_markup=get_main_keyboard()
        )
        return

    response = UserMessages.MY_POSTS_HEADER
    for post in posts:
        # Загружаем связанные объекты
        await db.refresh(post, attribute_names=["categories"])
        status = "✅ Одобрен" if post.is_approved else "⏳ На модерации"
        category_names = [cat.name for cat in post.categories] if post.categories else ['Неизвестно']
        category_str = ', '.join(category_names)
        post_city = getattr(post, 'city', 'Не указан')
        response += f"📝 {post.title}\n"
        response += f"🏙️ {post_city}\n"
        response += f"📂 {category_str}\n"
        response += f"📅 {post.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        response += f"📊 {status}\n\n"

    await callback.message.edit_text(response, reply_markup=get_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "help")
async def show_help_callback(callback: CallbackQuery):
    """Показать справку через инлайн-кнопку"""
    await callback.message.edit_text(
        CommonMessages.HELP_GENERAL, reply_markup=get_main_keyboard(), parse_mode="Markdown"
    )
    await callback.answer()
