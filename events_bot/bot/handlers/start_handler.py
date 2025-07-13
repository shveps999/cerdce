from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import get_city_keyboard, get_main_keyboard
from events_bot.bot.messages import StartMessages

router = Router()


def register_start_handlers(dp: Router):
    """Регистрация обработчиков команды start"""
    dp.include_router(router)


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, db):
    """Обработчик команды /start"""
    # Регистрируем пользователя
    user = await UserService.register_user(
        db=db,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    # Проверяем, есть ли у пользователя город
    if not user.city:
        await message.answer(
            StartMessages.WELCOME,
            reply_markup=get_city_keyboard(),
        )
        await state.set_state(UserStates.waiting_for_city)
    else:
        await message.answer(
            StartMessages.ALREADY_REGISTERED,
            reply_markup=get_main_keyboard(),
        )
