from aiogram.fsm.state import State, StatesGroup


class TaskRequestStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_manager = State()
