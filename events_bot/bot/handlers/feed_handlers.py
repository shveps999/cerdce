from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.services import PostService, LikeService
from ..bot.keyboards import get_main_keyboard, get_feed_keyboard
from ..storage import file_storage
from ..models import CategoryNames
import logfire

router = Router()
POSTS_PER_PAGE = 1

def format_post_for_feed(post, current_position: int, total_posts: int, likes_count: int = 0) -> str:
    """Форматирование поста для ленты с текстовыми названиями категорий"""
    # Получаем автора
    author_name = getattr(post.author, 'username', None) or \
                 getattr(post.author, 'first_name', None) or 'Аноним'
    
    # Получаем категории через CategoryNames
    category_names = []
    if hasattr(post, 'categories') and post.categories:
        category_names = [
            CategoryNames.get_text_name(cat.id)
            for cat in post.categories
            if hasattr(cat, 'id')
        ]
    
    # Формируем строки
    category_str = ', '.join(category_names) or 'Без категории'
    city = getattr(post, 'city', 'Не указан')
    published_at = getattr(post, 'published_at', None)
    published_str = published_at.strftime('%d.%m.%Y %H:%M') if published_at else ''
    
    return (
        f"📰 *{post.title}*\n\n"
        f"{post.content}\n\n"
        f"🏙️ Город: {city}\n"
        f"📂 Категории: {category_str}\n"
        f"👤 Автор: {author_name}\n"
        f"📅 {published_str}\n\n"
        f"📊 {current_position}/{total_posts} | ❤️ {likes_count}"
    )

@router.message(F.text == "/feed")
async def cmd_feed(message: Message, db: AsyncSession):
    """Обработчик команды /feed"""
    try:
        await show_feed_page(message, db, 0)
    except Exception as e:
        logfire.error(f"Ошибка в cmd_feed: {e}")
        await message.answer("⚠️ Произошла ошибка при загрузке ленты")

async def show_feed_page(
    message: Message | CallbackQuery, 
    db: AsyncSession,
    page: int,
    edit_message: bool = False
):
    """Основная функция отображения ленты"""
    try:
        # Получаем посты
        posts = await PostService.get_feed_posts(
            db, 
            message.from_user.id,
            POSTS_PER_PAGE,
            page * POSTS_PER_PAGE
        )
        
        if not posts:
            text = "📭 В ленте пока нет постов по вашим категориям."
            if isinstance(message, CallbackQuery):
                await message.message.edit_text(text, reply_markup=get_main_keyboard())
            else:
                await message.answer(text, reply_markup=get_main_keyboard())
            return

        post = posts[0]
        await db.refresh(post, ["author", "categories"])
        
        # Получаем данные о лайках
        is_liked = await LikeService.is_post_liked_by_user(db, message.from_user.id, post.id)
        likes_count = await LikeService.get_post_likes_count(db, post.id)
        total_posts = await PostService.get_feed_posts_count(db, message.from_user.id)
        total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
        
        # Формируем сообщение
        text = format_post_for_feed(post, page + 1, total_posts, likes_count)
        reply_markup = get_feed_keyboard(page, total_pages, post.id, is_liked, likes_count)
        
        # Отправка/редактирование сообщения
        if post.image_id:
            media = await file_storage.get_media_photo(post.image_id)
            if media:
                if isinstance(message, CallbackQuery) and edit_message:
                    await message.message.edit_media(
                        media=InputMediaPhoto(
                            media=media.media,
                            caption=text,
                            parse_mode="MarkdownV2"
                        ),
                        reply_markup=reply_markup
                    )
                else:
                    msg = message if isinstance(message, Message) else message.message
                    await msg.answer_photo(
                        photo=media.media,
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode="MarkdownV2"
                    )
                return
        
        if isinstance(message, CallbackQuery) and edit_message:
            await message.message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2"
            )
        else:
            msg = message if isinstance(message, Message) else message.message
            await msg.answer(
                text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2"
            )
            
    except Exception as e:
        logfire.error(f"Ошибка в show_feed_page: {e}")
        if isinstance(message, CallbackQuery):
            await message.message.answer("⚠️ Ошибка загрузки поста")
        else:
            await message.answer("⚠️ Ошибка загрузки поста")

@router.callback_query(F.data == "feed")
async def show_feed_callback(callback: CallbackQuery, db: AsyncSession):
    """Обработчик кнопки ленты"""
    try:
        await show_feed_page(callback, db, 0, True)
        await callback.answer()
    except Exception as e:
        logfire.error(f"Ошибка в show_feed_callback: {e}")
        await callback.answer("⚠️ Ошибка загрузки ленты")

@router.callback_query(F.data.startswith("feed_"))
async def handle_feed_navigation(callback: CallbackQuery, db: AsyncSession):
    """Обработка навигации по ленте"""
    try:
        _, action, *data = callback.data.split('_')
        
        if action in ["prev", "next"]:
            current_page = int(data[0])
            new_page = current_page - 1 if action == "prev" else current_page + 1
            await show_feed_page(callback, db, new_page, True)
            
        elif action == "heart":
            post_id = int(data[0])
            current_page = int(data[1])
            total_pages = int(data[2])
            
            result = await LikeService.toggle_like(db, callback.from_user.id, post_id)
            is_liked = result["action"] == "added"
            likes_count = result["likes_count"]
            
            await callback.message.edit_reply_markup(
                reply_markup=get_feed_keyboard(
                    current_page,
                    total_pages,
                    post_id,
                    is_liked,
                    likes_count
                )
            )
            await callback.answer(f"❤️ {likes_count}")
            
    except Exception as e:
        logfire.error(f"Ошибка навигации: {e}")
        await callback.answer("⚠️ Ошибка обработки действия")

@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    try:
        await callback.message.edit_text(
            "Выберите действие:",
            reply_markup=get_main_keyboard()
        )
        await callback.answer()
    except Exception as e:
        logfire.error(f"Ошибка возврата в меню: {e}")
        await callback.answer("⚠️ Ошибка возврата")
