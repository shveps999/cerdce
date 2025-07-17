from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message
from aiogram.fsm.context import FSMContext
from events_bot.database.services import PostService, LikeService
from events_bot.bot.keyboards.main_keyboard import get_main_keyboard
from events_bot.bot.keyboards.feed_keyboard import get_feed_keyboard
from events_bot.storage import file_storage
from ..models import CategoryNames  # Импортируем текстовые названия категорий
import logfire

router = Router()

POSTS_PER_PAGE = 1  # Показываем по одному посту на странице

def register_feed_handlers(dp: Router):
    """Регистрация обработчиков ленты"""
    dp.include_router(router)

def format_post_for_feed(post, current_position: int, total_posts: int, likes_count: int = 0) -> str:
    """Форматировать пост для ленты с текстовыми названиями категорий"""
    # Безопасно получаем данные
    author_name = 'Аноним'
    if hasattr(post, 'author') and post.author is not None:
        author = post.author
        author_name = (getattr(author, 'first_name', None) or 
                     getattr(author, 'username', None) or 'Аноним')
    
    # Получаем текстовые названия категорий через CategoryNames
    category_names = []
    if hasattr(post, 'categories') and post.categories is not None:
        category_names = [
            CategoryNames.get_text_name(cat.id) 
            for cat in post.categories
            if getattr(cat, 'id', None) is not None
        ]
    
    category_str = ', '.join(category_names) if category_names else 'Неизвестно'
    
    post_city = getattr(post, 'city', 'Не указан')
    published_at = getattr(post, 'published_at', None)
    published_str = published_at.strftime('%d.%m.%Y %H:%M') if published_at else ''
    
    return (
        f"📰 Лента постов\n\n"
        f"📝 *{post.title}*\n\n"
        f"{post.content}\n\n"
        f"👤 Автор: {author_name}\n"
        f"🏙️ Город: {post_city}\n"
        f"📂 Категории: {category_str}\n"
        f"💖 Сердечек: {likes_count}\n"
        f"📅 {published_str}\n\n"
        f"📊 {current_position} из {total_posts} постов"
    )

@router.message(F.text == "/feed")
async def cmd_feed(message: Message, db):
    """Обработчик команды /feed"""
    logfire.info(f"Пользователь {message.from_user.id} открывает ленту через команду")
    await show_feed_page_cmd(message, 0, db)

@router.callback_query(F.data == "feed")
async def show_feed_callback(callback: CallbackQuery, db):
    """Показать ленту постов"""
    logfire.info(f"Пользователь {callback.from_user.id} открывает ленту")
    await show_feed_page(callback, 0, db)

@router.callback_query(F.data.startswith("feed_"))
async def handle_feed_navigation(callback: CallbackQuery, db):
    """Обработка навигации по ленте"""
    data = callback.data.split("_")
    action = data[1]
    logfire.info(f"Пользователь {callback.from_user.id} навигация по ленте: {action}")
    try:
        if action in ["prev", "next"]:
            current_page = int(data[2])
            total_pages = int(data[3])
            if action == "prev":
                new_page = max(0, current_page - 1)
            else:
                new_page = current_page + 1
            await show_feed_page(callback, new_page, db)
        elif action == "heart":
            post_id = int(data[2])
            current_page = int(data[3])
            total_pages = int(data[4])
            await handle_post_heart(callback, post_id, db, data)
    except Exception as e:
        logfire.exception("Ошибка навигации по ленте {e}", e=e)
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "Выберите действие:", reply_markup=get_main_keyboard()
    )
    await callback.answer()

async def show_feed_page_cmd(message: Message, page: int, db):
    """Показать страницу ленты через сообщение"""
    logfire.info(f"Пользователь {message.from_user.id} загружает страницу {page} ленты")
    posts = await PostService.get_feed_posts(
        db, message.from_user.id, POSTS_PER_PAGE, page * POSTS_PER_PAGE
    )
    if not posts:
        logfire.info(f"Пользователь {message.from_user.id} — в ленте нет постов")
        await message.answer(
            "📭 В ленте пока нет постов по вашим категориям.\n\n"
            "Попробуйте:\n"
            "• Выбрать другие категории\n"
            "• Создать пост самому",
            reply_markup=get_main_keyboard()
        )
        return
    
    post = posts[0]
    await db.refresh(post, attribute_names=["author", "categories"])
    
    is_liked = await LikeService.is_post_liked_by_user(db, message.from_user.id, post.id)
    likes_count = await LikeService.get_post_likes_count(db, post.id)
    total_posts = await PostService.get_feed_posts_count(db, message.from_user.id)
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    
    feed_text = format_post_for_feed(post, page + 1, total_posts, likes_count)
    
    if post.image_id:
        media_photo = await file_storage.get_media_photo(post.image_id)
        if media_photo:
            await message.answer_photo(
                photo=media_photo.media,
                caption=feed_text,
                reply_markup=get_feed_keyboard(page, total_pages, post.id, is_liked, likes_count),
                parse_mode="MarkdownV2"
            )
            return
    
    await message.answer(
        feed_text,
        reply_markup=get_feed_keyboard(page, total_pages, post.id, is_liked, likes_count),
        parse_mode="MarkdownV2"
    )

async def show_feed_page(callback: CallbackQuery, page: int, db):
    """Показать страницу ленты"""
    logfire.info(f"Пользователь {callback.from_user.id} загружает страницу {page} ленты")
    posts = await PostService.get_feed_posts(
        db, callback.from_user.id, POSTS_PER_PAGE, page * POSTS_PER_PAGE
    )
    if not posts:
        logfire.info(f"Пользователь {callback.from_user.id} — в ленте нет постов")
        await callback.message.edit_text(
            "📭 В ленте пока нет постов по вашим категориям.\n\n"
            "Попробуйте:\n"
            "• Выбрать другие категории\n"
            "• Создать пост самому",
            reply_markup=get_main_keyboard()
        )
        return
    
    post = posts[0]
    await db.refresh(post, attribute_names=["author", "categories"])
    
    is_liked = await LikeService.is_post_liked_by_user(db, callback.from_user.id, post.id)
    likes_count = await LikeService.get_post_likes_count(db, post.id)
    total_posts = await PostService.get_feed_posts_count(db, callback.from_user.id)
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    
    feed_text = format_post_for_feed(post, page + 1, total_posts, likes_count)
    
    if post.image_id:
        media_photo = await file_storage.get_media_photo(post.image_id)
        if media_photo:
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=media_photo.media,
                    caption=feed_text,
                    parse_mode="MarkdownV2"
                ),
                reply_markup=get_feed_keyboard(page, total_pages, post.id, is_liked, likes_count)
            )
            return
    
    await callback.message.edit_text(
        feed_text,
        reply_markup=get_feed_keyboard(page, total_pages, post.id, is_liked, likes_count),
        parse_mode="MarkdownV2"
    )

async def handle_post_heart(callback: CallbackQuery, post_id: int, db, data):
    """Обработка нажатия на сердечко"""
    logfire.info(f"Пользователь {callback.from_user.id} нажал на сердечко посту {post_id}")
    
    try:
        result = await LikeService.toggle_like(db, callback.from_user.id, post_id)
        action_text = "добавлено" if result["action"] == "added" else "удалено"
        
        await callback.answer(
            f"Сердечко {action_text}! 💖 {result['likes_count']}",
            show_alert=False
        )
        
        current_page = int(data[3])
        total_pages = int(data[4])
        is_liked = result["action"] == "added"
        
        await callback.message.edit_reply_markup(
            reply_markup=get_feed_keyboard(
                current_page,
                total_pages,
                post_id,
                is_liked,
                result["likes_count"]
            )
        )
    except Exception as e:
        logfire.error(f"Ошибка при сохранении сердечка: {e}")
        await callback.answer("❌ Ошибка", show_alert=False)
