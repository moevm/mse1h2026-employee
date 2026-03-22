from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from constants.bot_constants import Buttons


def get_superuser_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.SUPERUSER_ROLE_REQUESTS)
    builder.button(text=Buttons.SUPERUSER_BAN_USER)
    builder.button(text=Buttons.EXIT)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_role_request_action_keyboard(tg_id: str, role: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="Подтвердить", callback_data=f"req_approve:{tg_id}:{role}")
    builder.button(text="Отклонить", callback_data=f"req_deny:{tg_id}:{role}")
    builder.adjust(2)
    return builder.as_markup()


def get_lead_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.LEAD_TASKS)
    builder.button(text=Buttons.LEAD_REPORTS)
    builder.button(text=Buttons.LEAD_WEEKLY_REPORT)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def get_lead_tasks_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.LEAD_CREATE_TASK)
    builder.button(text=Buttons.LEAD_TASKS_LIST)
    builder.button(text=Buttons.MAIN_MENU)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)


def get_lead_reports_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.LEAD_REPORTS_LIST)
    builder.button(text=Buttons.LEAD_OPEN_REPORT)
    builder.button(text=Buttons.MAIN_MENU)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)


def get_lead_report_actions_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.LEAD_CONFIRM_REPORT)
    builder.button(text=Buttons.LEAD_DENY_REPORT)
    builder.button(text=Buttons.LEAD_BACK_TO_REPORTS)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)


def get_lead_cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.CANCEL)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_employee_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.EMPLOYEE_START_WORK)
    builder.button(text=Buttons.EMPLOYEE_FINISH_WORK)
    builder.button(text=Buttons.EMPLOYEE_CREATE_TASK)
    builder.button(text=Buttons.EMPLOYEE_TASKS_LIST)
    builder.button(text=Buttons.EMPLOYEE_COMPLETE_TASK)
    builder.button(text=Buttons.EMPLOYEE_REPORT_COMMENT)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def get_intern_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.INTERN_TASKS_LIST)
    builder.button(text=Buttons.INTERN_COMPLETE_TASK)
    builder.button(text=Buttons.INTERN_REPORT_COMMENT)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2, 1, 1)
    return builder.as_markup(resize_keyboard=True)


def get_manager_selection_keyboard(manager_usernames: list[str]):
    builder = ReplyKeyboardBuilder()
    for username in manager_usernames:
        builder.button(text=username)
    builder.button(text=Buttons.CANCEL)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)