from aiogram.fsm.state import State, StatesGroup


class TaskReportStates(StatesGroup):
    waiting_report_text = State()