from aiogram.utils.keyboard import ReplyKeyboardBuilder

from constants.bot_constants import Buttons


def get_superuser_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.SUPERUSER_ROLE_REQUESTS)
    builder.button(text=Buttons.SUPERUSER_CONFIRM_ROLE)
    builder.button(text=Buttons.SUPERUSER_BAN_USER)
    builder.button(text=Buttons.SUPERUSER_LEAD_MENU)
    builder.button(text=Buttons.EXIT)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


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
