from aiogram.fsm.state import State, StatesGroup


class DailyReportStates(StatesGroup):
    waiting_work_done = State()
    waiting_problems = State()
