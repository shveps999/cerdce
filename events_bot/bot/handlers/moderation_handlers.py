from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logfire
from events_bot.database.services import (
    ModerationService,
    PostService,
    NotificationService,
)
from events_bot.bot.utils import send_post_notification
from events_bot.storage import file_storage
from events_bot.database.models import ModerationAction
from events_bot.bot.keyboards import (
    get_moderation_keyboard,
    get_moderation_queue_keyboard,
    get_main_keyboard,
)
from events_bot.bot.messages import ModerationMessages, CommonMessages

router = Router()


def register_moderation_handlers(dp: Router):
    """Регистрация обработчиков модерации"""
    dp.include_router(router)


@router.message(F.text == "/moderation")
async def cmd_moderation(message: Message, db):
    """Обработчик команды /moderation"""
    logfire.info(f"Пользователь {message.from_user.id} запросил модерацию через команду")
    pending_posts = await ModerationService.get_moderation_queue(db)

    if not pending_posts:
        logfire.info("Очередь модерации пуста")
        await message.answer(
            ModerationMessages.MODERATION_QUEUE_EMPTY,
            reply_markup=get_main_keyboard(),
        )
        return

    logfire.info(f"Найдено {len(pending_posts)} постов на модерации")
    response = ModerationMessages.MODERATION_QUEUE_HEADER
    for post in pending_posts:
        await db.refresh(post, attribute_names=["author", "categories"])
        category_names = [cat.name for cat in post.categories] if post.categories else ['Неизвестно']
        category_str = ', '.join(category_names)
        post_city = getattr(post, 'city', 'Не указан')
        response += f"{post.title}\n"
        response += f"Город: {post_city}\n"
        response += f"{post.author.first_name or post.author.username}\n"
        response += f"{category_str}\n"
        response += f"ID: {post.id}\n\n"

    await message.answer(
        response, reply_markup=get_main_keyboard()
    )


@router.callback_query(F.data == "moderation")
async def show_moderation_queue_callback(callback: CallbackQuery, db):
    """Показать очередь модерации через инлайн-кнопку"""
    logfire.info(f"Пользователь {callback.from_user.id} запросил очередь модерации")
    pending_posts = await ModerationService.get_moderation_queue(db)

    if not pending_posts:
        logfire.info("Очередь модерации пуста")
        await callback.message.edit_text(
            ModerationMessages.MODERATION_QUEUE_EMPTY,
            reply_markup=get_moderation_queue_keyboard(),
        )
        return

    logfire.info(f"Найдено {len(pending_posts)} постов на модерации")
    response = ModerationMessages.MODERATION_QUEUE_HEADER
    for post in pending_posts:
        await db.refresh(post, attribute_names=["author", "categories"])
        category_names = [cat.name for cat in post.categories] if post.categories else ['Неизвестно']
        category_str = ', '.join(category_names)
        post_city = getattr(post, 'city', 'Не указан')
        response += f"{post.title}\n"
        response += f"Город: {post_city}\n"
        response += f"{post.author.first_name or post.author.username}\n"
        response += f"{category_str}\n"
        response += f"ID: {post.id}\n\n"

    await callback.message.edit_text(
        response, reply_markup=get_moderation_queue_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "refresh_moderation")
async def refresh_moderation_queue(callback: CallbackQuery, db):
    """Обновить очередь модерации"""
    logfire.info(f"Пользователь {callback.from_user.id} обновил очередь модерации")
    pending_posts = await ModerationService.get_moderation_queue(db)

    if not pending_posts:
        logfire.info("Очередь модерации пуста при обновлении")
        await callback.message.edit_text(
            ModerationMessages.MODERATION_QUEUE_EMPTY,
            reply_markup=get_moderation_queue_keyboard(),
        )
        await callback.answer(ModerationMessages.MODERATION_QUEUE_UPDATED)
        return

    logfire.info(f"Обновлено: найдено {len(pending_posts)} постов на модерации")
    response = ModerationMessages.MODERATION_QUEUE_HEADER
    for post in pending_posts:
        await db.refresh(post, attribute_names=["author", "categories"])
        category_names = [cat.name for cat in post.categories] if post.categories else ['Неизвестно']
        category_str = ', '.join(category_names)
        post_city = getattr(post, 'city', 'Не указан')
        response += f"{post.title}\n"
        response += f"Город: {post_city}\n"
        response += f"{post.author.first_name or post.author.username}\n"
        response += f"{category_str}\n"
        response += f"ID: {post.id}\n\n"

    await callback.message.edit_text(
        response, reply_markup=get_moderation_queue_keyboard()
    )
    await callback.answer(ModerationMessages.MODERATION_QUEUE_UPDATED)


@router.callback_query(F.data.startswith("moderate_"))
async def process_moderation_action(callback: CallbackQuery, db):
    """Обработка действий модерации"""
    data = callback.data.split("_")
    action = data[1]
    post_id = int(data[2])
    
    logfire.info(f"Модератор {callback.from_user.id} выполняет действие {action} для поста {post_id}")

    if action == "approve":
        post = await PostService.approve_post(db, post_id, callback.from_user.id)
        if post:
            # Публикуем пост
            post = await PostService.publish_post(db, post_id)
            await db.refresh(post, attribute_names=["author", "categories"])
            logfire.info(f"Пост {post_id} одобрен и опубликован модератором {callback.from_user.id}")
            
            # Отправляем уведомления пользователям
            users_to_notify = await NotificationService.get_users_to_notify(
                db, post
            )
            logfire.info(f"Отправляем уведомления {len(users_to_notify)} пользователям")
            await send_post_notification(callback.bot, post, users_to_notify, db)

            await callback.answer(ModerationMessages.POST_APPROVED)
            await callback.message.delete()
        else:
            logfire.error(f"Ошибка при одобрении поста {post_id}")
            await callback.answer(ModerationMessages.POST_APPROVAL_ERROR)

    elif action == "reject":
        post = await PostService.reject_post(db, post_id, callback.from_user.id)
        if post:
            await db.refresh(post, attribute_names=["author", "categories"])
            logfire.info(f"Пост {post_id} отклонен модератором {callback.from_user.id}")
            await callback.answer(ModerationMessages.POST_REJECTED)
            await callback.message.delete()
        else:
            logfire.error(f"Ошибка при отклонении поста {post_id}")
            await callback.answer(ModerationMessages.POST_REJECTION_ERROR)

    elif action == "changes":
        post = await PostService.request_changes(db, post_id, callback.from_user.id)
        if post:
            await db.refresh(post, attribute_names=["author", "categories"])
            logfire.info(f"Для поста {post_id} запрошены изменения модератором {callback.from_user.id}")
            await callback.answer(ModerationMessages.POST_CHANGES_REQUESTED)
            await callback.message.delete()
        else:
            logfire.error(f"Ошибка при запросе изменений для поста {post_id}")
            await callback.answer(ModerationMessages.POST_CHANGES_ERROR)
