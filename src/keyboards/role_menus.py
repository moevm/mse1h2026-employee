from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from constants.bot_constants import Buttons

TASK_CALLBACK_PREFIX = "task_action"
LEAD_REPORT_CALLBACK_PREFIX = "lead_report"
TASK_PROPOSAL_CALLBACK_PREFIX = "task_proposal"
SUPERUSER_REVOKE_CALLBACK_PREFIX = "superuser_revoke"
MANAGER_BIND_CALLBACK_PREFIX = "manager_bind"


def get_superuser_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.SUPERUSER_ROLE_REQUESTS)
    builder.button(text=Buttons.SUPERUSER_BAN_USER)
    builder.button(text=Buttons.SUPERUSER_REVOKE_ROLE)
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
    builder.button(text=Buttons.START_WORK)
    builder.button(text=Buttons.FINISH_WORK)
    builder.button(text=Buttons.LEAD_TASKS)
    builder.button(text=Buttons.LEAD_REPORTS)
    builder.button(text=Buttons.LEAD_WEEKLY_REPORT)
    builder.button(text=Buttons.LEAD_BIND_REQUESTS)
    builder.button(text=Buttons.NOTIFICATION_SETTINGS)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def get_task_proposal_action_keyboard(token: str | int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=Buttons.TASK_ACCEPT,
        callback_data=f"{TASK_PROPOSAL_CALLBACK_PREFIX}:accept:{token}",
    )
    builder.button(
        text="Отклонить",
        callback_data=f"{TASK_PROPOSAL_CALLBACK_PREFIX}:reject:{token}",
    )
    builder.adjust(2)
    return builder.as_markup()


def get_lead_tasks_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.LEAD_CREATE_TASK)
    builder.button(text=Buttons.LEAD_TASK_PROPOSALS)
    builder.button(text=Buttons.LEAD_TASKS_LIST)
    builder.button(text=Buttons.MAIN_MENU)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2, 1, 2)
    return builder.as_markup(resize_keyboard=True)


def get_lead_reports_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.LEAD_REPORTS_LIST)
    builder.button(text=Buttons.LEAD_DAILY_REPORTS)
    builder.button(text=Buttons.MAIN_MENU)
    builder.button(text=Buttons.EXIT)
    builder.adjust(1, 1, 2)
    return builder.as_markup(resize_keyboard=True)


def get_lead_report_item_keyboard(task_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=Buttons.LEAD_VIEW_REPORT,
        callback_data=f"{LEAD_REPORT_CALLBACK_PREFIX}:view:{task_id}",
    )
    builder.button(
        text=Buttons.LEAD_CONFIRM_REPORT,
        callback_data=f"{LEAD_REPORT_CALLBACK_PREFIX}:accept:{task_id}",
    )
    builder.button(
        text=Buttons.LEAD_REJECT_REPORT,
        callback_data=f"{LEAD_REPORT_CALLBACK_PREFIX}:reject:{task_id}",
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def get_lead_cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.CANCEL)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_employee_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.START_WORK)
    builder.button(text=Buttons.FINISH_WORK)
    builder.button(text=Buttons.EMPLOYEE_CREATE_TASK)
    builder.button(text=Buttons.EMPLOYEE_TASKS_LIST)
    builder.button(text=Buttons.EMPLOYEE_DAILY_REPORT)
    builder.button(text=Buttons.EMPLOYEE_REPORT_COMMENT)
    builder.button(text=Buttons.EMPLOYEE_BIND_MANAGER)
    builder.button(text=Buttons.NOTIFICATION_SETTINGS)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def get_intern_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.START_WORK)
    builder.button(text=Buttons.FINISH_WORK)
    builder.button(text=Buttons.INTERN_TASKS_LIST)
    builder.button(text=Buttons.INTERN_DAILY_REPORT)
    builder.button(text=Buttons.INTERN_REPORT_COMMENT)
    builder.button(text=Buttons.INTERN_BIND_MANAGER)
    builder.button(text=Buttons.NOTIFICATION_SETTINGS)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup(resize_keyboard=True)


def get_manager_selection_keyboard(manager_usernames: list[str]):
    builder = ReplyKeyboardBuilder()
    for username in manager_usernames:
        builder.button(text=username)
    builder.button(text=Buttons.CANCEL)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.CANCEL)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_employee_selection_keyboard(employee_names: list[str]):
    builder = ReplyKeyboardBuilder()
    for name in employee_names:
        builder.button(text=name)
    builder.button(text=Buttons.CANCEL)
    builder.button(text=Buttons.EXIT)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_task_action_keyboard(task_id: str, status: str) -> InlineKeyboardMarkup | None:
    builder = InlineKeyboardBuilder()
    normalized_status = (status or "").strip().lower()

    if normalized_status == "created":
        builder.button(
            text=Buttons.TASK_ACCEPT,
            callback_data=f"{TASK_CALLBACK_PREFIX}:accept:{task_id}",
        )
        builder.adjust(1)
        return builder.as_markup()

    if normalized_status == "in process":
        builder.button(
            text=Buttons.TASK_FINISH,
            callback_data=f"{TASK_CALLBACK_PREFIX}:finish:{task_id}",
        )
        builder.button(
            text=Buttons.TASK_REPORT,
            callback_data=f"{TASK_CALLBACK_PREFIX}:report:{task_id}",
        )
        builder.adjust(2)
        return builder.as_markup()

    if normalized_status in ("on consideration", "finished", "cancelled"):
        builder.button(
            text=Buttons.TASK_REPORT,
            callback_data=f"{TASK_CALLBACK_PREFIX}:report:{task_id}",
        )
        builder.adjust(1)
        return builder.as_markup()

    return None


def get_report_cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.CANCEL)
    builder.button(text=Buttons.EXIT)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_lead_accept_comment_choice_keyboard(task_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да",
                    callback_data=f"lead_report_comment:yes:{task_id}",
                ),
                InlineKeyboardButton(
                    text="Нет",
                    callback_data=f"lead_report_comment:no:{task_id}",
                ),
            ]
        ]
    )


def get_superuser_revoke_role_keyboard(tg_id: int, roles: list[str]):
    builder = InlineKeyboardBuilder()
    role_titles = {
        "lead": "руководитель",
        "employee": "сотрудник",
        "intern": "стажер",
        "superuser": "суперпользователь",
    }
    for role in roles:
        builder.button(
            text=f"Отозвать роль: {role_titles.get(role, role)}",
            callback_data=f"{SUPERUSER_REVOKE_CALLBACK_PREFIX}:{tg_id}:{role}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_manager_bind_action_keyboard(request_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Подтвердить",
        callback_data=f"{MANAGER_BIND_CALLBACK_PREFIX}:accept:{request_id}",
    )
    builder.button(
        text="Отклонить",
        callback_data=f"{MANAGER_BIND_CALLBACK_PREFIX}:reject:{request_id}",
    )
    builder.adjust(2)
    return builder.as_markup()