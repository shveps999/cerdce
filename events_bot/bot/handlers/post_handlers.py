from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from typing import Union
import logfire
from events_bot.database.services import PostService, UserService, CategoryService
from events_bot.bot.states import PostStates
from events_bot.bot.keyboards import (
    get_main_keyboard,
    get_category_selection_keyboard,
    get_city_keyboard,
)
from events_bot.storage import file_storage
from loguru import logger

router = Router()


def register_post_handlers(dp: Router):
    """Регистрация обработчиков постов"""
    dp.include_router(router)


@router.message(F.text == "/create_post")
async def cmd_create_post(message: Message, state: FSMContext, db):
    """Обработчик команды /create_post"""
    # Устанавливаем начальное состояние создания поста
    await state.set_state(PostStates.creating_post)
    
    # Сначала предлагаем выбрать город
    await message.answer(
        "🏙️ Выберите город для поста:",
        reply_markup=get_city_keyboard(for_post=True)
    )
    await state.set_state(PostStates.waiting_for_city_selection)


@router.message(F.text == "/cancel")
async def cmd_cancel_post(message: Message, state: FSMContext, db):
    """Отмена создания поста на любом этапе"""
    logfire.info(f"Пользователь {message.from_user.id} отменил создание поста")
    await state.clear()
    await message.answer(
        "❌ Создание поста отменено.",
        reply_markup=get_main_keyboard()
    )


@router.callback_query(F.data == "create_post")
async def start_create_post(callback: CallbackQuery, state: FSMContext, db):
    """Начать создание поста через инлайн-кнопку"""
    # Устанавливаем начальное состояние создания поста
    await state.set_state(PostStates.creating_post)
    
    # Сначала предлагаем выбрать город
    await callback.message.edit_text(
        "🏙️ Выберите город для поста:",
        reply_markup=get_city_keyboard(for_post=True)
    )
    await state.set_state(PostStates.waiting_for_city_selection)
    await callback.answer()


@router.callback_query(F.data == "cancel_post")
async def cancel_post_creation(callback: CallbackQuery, state: FSMContext, db):
    """Отмена создания поста"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Создание поста отменено.",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(PostStates.waiting_for_city_selection, F.data.startswith("post_city_"))
async def process_post_city_selection(callback: CallbackQuery, state: FSMContext, db):
    """Обработка выбора города для поста"""
    city = callback.data[10:]  # Убираем префикс "post_city_"

    # Сохраняем выбранный город
    await state.update_data(post_city=city)
    
    # Получаем все категории для выбора
    all_categories = await CategoryService.get_all_categories(db)
    
    await callback.message.edit_text(
        f"🏙️ Город {city} выбран!\n\n📂 Теперь выберите категории для поста:",
        reply_markup=get_category_selection_keyboard(all_categories, for_post=True)
    )
    await state.set_state(PostStates.waiting_for_category_selection)
    await callback.answer()


@router.callback_query(PostStates.waiting_for_category_selection, F.data.startswith("post_category_"))
async def process_post_category_selection(callback: CallbackQuery, state: FSMContext, db):
    """Мультивыбор категорий для поста"""
    category_id = int(callback.data.split("_")[2])  # post_category_123 -> 123
    data = await state.get_data()
    category_ids = data.get("category_ids", [])

    if category_id in category_ids:
        category_ids.remove(category_id)
    else:
        category_ids.append(category_id)
    await state.update_data(category_ids=category_ids)

    # Получаем все категории для выбора
    all_categories = await CategoryService.get_all_categories(db)
    await callback.message.edit_text(
        "📂 Выберите одну или несколько категорий для поста (можно выбрать несколько):",
        reply_markup=get_category_selection_keyboard(all_categories, category_ids, for_post=True)
    )
    await callback.answer()

@router.callback_query(PostStates.waiting_for_category_selection, F.data == "confirm_post_categories")
@logger.catch
async def confirm_post_categories(callback: CallbackQuery, state: FSMContext, db):
    """Подтверждение выбора категорий для поста"""
    data = await state.get_data()
    category_ids = data.get("category_ids", [])
    if not category_ids:
        await callback.answer("Выберите хотя бы одну категорию", show_alert=True)
        return
    await state.update_data(category_ids=category_ids)
    logfire.info(f"Категории подтверждены для пользователя {callback.from_user.id}: {category_ids}")
    await callback.message.edit_text(
        f"📝 Создание поста в категориях: {len(category_ids)} выбрано\n\nВведите заголовок поста:"
    )
    await state.set_state(PostStates.waiting_for_title)
    logfire.info(f"Состояние изменено на waiting_for_title для пользователя {callback.from_user.id}")
    await callback.answer()

@router.message(PostStates.waiting_for_title)
@logger.catch
async def process_post_title(message: Message, state: FSMContext, db):
    """Обработка заголовка поста"""
    logfire.info(f"Получен заголовок поста от пользователя {message.from_user.id}: {message.text}")
    
    if len(message.text) > 100:
        await message.answer("❌ Заголовок слишком длинный. Максимум 100 символов.")
        return

    await state.update_data(title=message.text)
    logfire.info(f"Заголовок сохранен в состоянии: {message.text}")
    await message.answer("📄 Введите содержание поста:")
    await state.set_state(PostStates.waiting_for_content)
    logfire.info(f"Состояние изменено на waiting_for_content для пользователя {message.from_user.id}")


@router.message(PostStates.waiting_for_content)
async def process_post_content(message: Message, state: FSMContext, db):
    """Обработка содержания поста"""
    if len(message.text) > 2000:
        await message.answer("❌ Содержание слишком длинное. Максимум 2000 символов.")
        return

    await state.update_data(content=message.text)
    await message.answer(
        "🖼️ Отправьте изображение для поста (или нажмите /skip для пропуска):"
    )
    await state.set_state(PostStates.waiting_for_image)


@router.message(PostStates.waiting_for_image)
async def process_post_image(message: Message, state: FSMContext, db):
    """Обработка изображения поста"""
    if message.text == "/skip":
        await continue_post_creation(message, state, db)
        return

    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте изображение или нажмите /skip")
        return

    # Получаем самое большое изображение
    photo = message.photo[-1]
    
    # Скачиваем файл
    file_info = await message.bot.get_file(photo.file_id)
    file_data = await message.bot.download_file(file_info.file_path)
    
    # Сохраняем файл
    file_id = await file_storage.save_file(file_data.read(), 'jpg')
    
    await state.update_data(image_id=file_id)
    await continue_post_creation(message, state, db)


async def continue_post_creation(callback_or_message: Union[Message, CallbackQuery], state: FSMContext, db):
    """Продолжение создания поста после загрузки изображения"""
    user_id = callback_or_message.from_user.id
    message = callback_or_message if isinstance(callback_or_message, Message) else callback_or_message.message
    data = await state.get_data()
    title = data.get("title")
    content = data.get("content")
    category_ids = data.get("category_ids", [])
    post_city = data.get("post_city")
    image_id = data.get("image_id")

    if not all([title, content, category_ids, post_city]):
        await message.answer(
            "❌ Ошибка: не все данные поста заполнены. Попробуйте создать пост заново.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    # Создаем один пост с несколькими категориями
    post = await PostService.create_post_and_send_to_moderation(
        db=db,
        title=title,
        content=content,
        author_id=user_id,
        category_ids=category_ids,
        city=post_city,
        image_id=image_id,
        bot=message.bot
    )

    if post:
        await message.answer(
            f"✅ Пост создан и отправлен на модерацию в городе {post_city} в {len(category_ids)} категориях!",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
    else:
        await message.answer(
            "❌ Ошибка при создании поста. Попробуйте еще раз.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()


@router.callback_query(F.data == "liked_posts")
async def show_liked_posts(callback: CallbackQuery, db: AsyncSession):
    """Показ избранных постов с кнопками удаления"""
    user_id = callback.from_user.id
    
    try:
        liked_posts = await PostService.get_liked_posts_with_details(db, user_id)
        
        if not liked_posts:
            await callback.message.edit_text(
                "❤️ Ваше избранное пусто.",
                reply_markup=get_main_keyboard()
            )
            return

        builder = InlineKeyboardBuilder()
        message_text = "❤️ <b>Ваше избранное:</b>\n\n"
        
        for post in liked_posts:
            categories = ", ".join(post.category_names)
            like_date = post.likes[0].created_at  # Получаем дату лайка
            
            message_text += (
                f"📌 <b>{post.title}</b>\n"
                f"📅 Добавлено: {like_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"🏷️ Категории: {categories}\n\n"
            )
            builder.button(
                text=f"❌ Удалить", 
                callback_data=f"remove_like_{post.id}"
            )
        
        builder.button(text="🔙 Назад", callback_data="main_menu")
        builder.adjust(1)
        
        await callback.message.edit_text(
            message_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logfire.error(f"Error showing liked posts: {e}")
        await callback.answer("❌ Ошибка загрузки избранного", show_alert=True)

@router.callback_query(F.data.startswith("remove_like_"))
async def remove_like_handler(callback: CallbackQuery, db: AsyncSession):
    """Обработчик удаления из избранного"""
    try:
        post_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id
        
        success = await PostService.remove_like(db, user_id, post_id)
        
        if success:
            await callback.answer("✅ Удалено из избранного")
            await show_liked_posts(callback, db)  # Обновляем список
        else:
            await callback.answer("⚠️ Пост не найден в избранном", show_alert=True)
    except Exception as e:
        logfire.error(f"Error removing like: {e}")
        await callback.answer("❌ Ошибка при удалении", show_alert=True)
