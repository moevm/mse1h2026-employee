from aiogram.fsm.state import State, StatesGroup


class LeadStates(StatesGroup):
    waiting_task_input = State()
    waiting_report_id = State()
    viewing_report = State()
    waiting_deny_comment = State()
    waiting_weekly_user = State()
