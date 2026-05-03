from aiogram.fsm.state import State, StatesGroup


class NotificationSettingsStates(StatesGroup):
    waiting_settings = State()