from aiogram.fsm.state import State, StatesGroup


class LeadStates(StatesGroup):
    waiting_task_title = State()
    waiting_task_description = State()
    waiting_task_deadline = State()
    waiting_task_employee = State()
    waiting_report_id = State()
    viewing_report = State()
    waiting_deny_comment = State()
    waiting_weekly_user = State()
