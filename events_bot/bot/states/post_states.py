from aiogram.fsm.state import State, StatesGroup

class PostStates(StatesGroup):
    """Состояния для создания поста"""
    waiting_for_title = State()
    waiting_for_content = State() 