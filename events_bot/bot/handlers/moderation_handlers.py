from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import ModerationService, PostService, NotificationService
from events_bot.bot.utils import get_db_session, send_post_notification
from events_bot.database.models import ModerationAction
from events_bot.bot.keyboards import get_moderation_keyboard, get_moderation_queue_keyboard

router = Router()

def register_moderation_handlers(dp: Router):
    """Регистрация обработчиков модерации"""
    dp.include_router(router)

@router.callback_query(F.data == "moderation")
async def show_moderation_queue_callback(callback: CallbackQuery):
    """Показать очередь модерации через инлайн-кнопку"""
    async with get_db_session() as db:
        pending_posts = await ModerationService.get_moderation_queue(db)
        
        if not pending_posts:
            await callback.message.edit_text(
                "📭 Нет постов на модерации.",
                reply_markup=get_moderation_queue_keyboard()
            )
            return
        
        response = "🔍 Посты на модерации:\n\n"
        for post in pending_posts:
            response += f"📝 {post.title}\n"
            response += f"👤 {post.author.first_name or post.author.username}\n"
            response += f"📂 {post.category.name}\n"
            response += f"🆔 ID: {post.id}\n\n"
        
        await callback.message.edit_text(
            response,
            reply_markup=get_moderation_queue_keyboard()
        )
        await callback.answer()

@router.callback_query(F.data.startswith("moderate_"))
async def process_moderation_action(callback: CallbackQuery):
    """Обработка действий модерации"""
    data = callback.data.split("_")
    action = data[1]
    post_id = int(data[2])
    
    async with get_db_session() as db:
        if action == "approve":
            post = await PostService.approve_post(db, post_id, callback.from_user.id)
            if post:
                # Отправляем уведомления пользователям
                users_to_notify = await NotificationService.get_users_to_notify(db, post)
                await send_post_notification(callback.bot, post, users_to_notify)
                
                await callback.answer("✅ Пост одобрен и опубликован!")
            else:
                await callback.answer("❌ Ошибка при одобрении поста")
                
        elif action == "reject":
            post = await PostService.reject_post(db, post_id, callback.from_user.id)
            if post:
                await callback.answer("❌ Пост отклонен!")
            else:
                await callback.answer("❌ Ошибка при отклонении поста")
                
        elif action == "changes":
            post = await PostService.request_changes(db, post_id, callback.from_user.id)
            if post:
                await callback.answer("📝 Запрошены изменения в посте!")
            else:
                await callback.answer("❌ Ошибка при запросе изменений") 