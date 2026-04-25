from aiogram.fsm.state import State, StatesGroup


class ManagerBindingStates(StatesGroup):
    waiting_lead = State()