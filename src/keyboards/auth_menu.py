from aiogram.utils.keyboard import ReplyKeyboardBuilder

from constants.bot_constants import Buttons
from roles import Role


ROLE_REQUEST_BUTTONS = {
    Role.INTERN: Buttons.REQUEST_INTERN,
    Role.EMPLOYEE: Buttons.REQUEST_EMPLOYEE,
    Role.LEAD: Buttons.REQUEST_LEAD,
    Role.SUPERUSER: Buttons.REQUEST_SUPERUSER,
}


def get_role_request_button_text(role: Role) -> str:
    return ROLE_REQUEST_BUTTONS[role]


def get_start_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=Buttons.AUTH)
    builder.button(text=Buttons.REQUEST_ROLE)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_roles_keyboard(roles: list[Role]):
    builder = ReplyKeyboardBuilder()

    for role in roles:
        builder.button(text=role.title.capitalize())

    builder.button(text=Buttons.BACK)
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


def get_role_request_keyboard(roles: list[Role]):
    builder = ReplyKeyboardBuilder()

    for role in roles:
        builder.button(text=get_role_request_button_text(role))

    builder.button(text=Buttons.BACK)
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)
