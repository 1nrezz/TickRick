from aiogram.fsm.state import State, StatesGroup

class PostStates(StatesGroup):
    editing_text = State()
