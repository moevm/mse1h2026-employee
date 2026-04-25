from aiogram.fsm.state import State, StatesGroup


class LeadStates(StatesGroup):
    waiting_task_title = State()
    waiting_task_description = State()
    waiting_task_deadline = State()
    waiting_task_employee = State()
    waiting_task_proposal_deadline = State()
    waiting_weekly_user = State()
    waiting_accept_comment = State()
    waiting_reject_comment = State()