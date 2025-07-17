from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message
from aiogram.fsm.context import FSMContext
from events_bot.database.services import PostService, LikeService
from events_bot.bot.keyboards.main_keyboard import get_main_keyboard
from events_bot.bot.keyboards.feed_keyboard import get_feed_keyboard
from events_bot.storage import file_storage
from ..models import CategoryNames
import logfire

router = Router()
POSTS_PER_PAGE = 1

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
    
    # Получаем текстовые названия категорий
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
        f"Актуальные события\n\n"
        f"📝 *{post.title}*\n\n"
        f"{post.content}\n\n"
        f"🏙️ Университет: {post_city}\n"
        f"📂 Категории: {category_str}\n"
        f"📅 {published_str}\n\n"
        f"📊 {current_position} из {total_posts} постов\n"
        f"❤️ {likes_count} сердец"
    )

@router.message(F.text == "/feed")
async def cmd_feed(message: Message, db):
    """Обработчик команды /feed"""
    logfire.info(f"Пользователь {message.from_user.id} открывает ленту")
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
    logfire.info(f"Навигация по ленте: {action}")
    
    try:
        if action in ["prev", "next"]:
            current_page = int(data[2])
            new_page = current_page - 1 if action == "prev" else current_page + 1
            await show_feed_page(callback, new_page, db)
        elif action == "heart":
            post_id = int(data[2])
            await handle_post_heart(callback, post_id, db, data)
    except Exception as e:
        logfire.error(f"Ошибка навигации: {e}")
    await callback.answer()

async def show_feed_page_cmd(message: Message, page: int, db):
    """Показать страницу ленты через сообщение"""
    posts = await PostService.get_feed_posts(
        db, message.from_user.id, POSTS_PER_PAGE, page * POSTS_PER_PAGE
    )
    
    if not posts:
        await message.answer(
            "📭 В ленте пока нет постов по вашим категориям.\n"
            "Попробуйте изменить настройки категорий.",
            reply_markup=get_main_keyboard()
        )
        return
    
    post = posts[0]
    await db.refresh(post, attribute_names=["author", "categories"])
    
    is_liked = await LikeService.is_post_liked_by_user(db, message.from_user.id, post.id)
    likes_count = await LikeService.get_post_likes_count(db, post.id)
    total_posts = await PostService.get_feed_posts_count(db, message.from_user.id)
    
    feed_text = format_post_for_feed(post, page + 1, total_posts, likes_count)
    
    if post.image_id:
        media_photo = await file_storage.get_media_photo(post.image_id)
        if media_photo:
            await message.answer_photo(
                photo=media_photo.media,
                caption=feed_text,
                reply_markup=get_feed_keyboard(page, (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE, 
                                             post.id, is_liked, likes_count),
                parse_mode="MarkdownV2"
            )
            return
    
    await message.answer(
        feed_text,
        reply_markup=get_feed_keyboard(page, (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE, 
                                     post.id, is_liked, likes_count),
        parse_mode="MarkdownV2"
    )

async def show_feed_page(callback: CallbackQuery, page: int, db):
    """Показать страницу ленты"""
    posts = await PostService.get_feed_posts(
        db, callback.from_user.id, POSTS_PER_PAGE, page * POSTS_PER_PAGE
    )
    
    if not posts:
        await callback.message.edit_text(
            "📭 В ленте пока нет постов.",
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
    """Обработка лайков"""
    try:
        result = await LikeService.toggle_like(db, callback.from_user.id, post_id)
        action_text = "добавлено" if result["action"] == "added" else "удалено"
        
        await callback.answer(
            f"Событие добавлено в избранное {action_text}! ❤️ {result['likes_count']}",
            show_alert=False
        )
        
        # Обновляем клавиатуру
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
        logfire.error(f"Ошибка лайка: {e}")
        await callback.answer("❌ Ошибка", show_alert=False)

@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()
