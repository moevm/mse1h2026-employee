from aiogram.utils.keyboard import ReplyKeyboardBuilder

from constants.bot_constants import Buttons
from roles import Role


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


def get_role_request_keyboard():
    builder = ReplyKeyboardBuilder()

    builder.button(text=Buttons.REQUEST_INTERN)
    builder.button(text=Buttons.REQUEST_EMPLOYEE)
    builder.button(text=Buttons.REQUEST_LEAD)
    builder.button(text=Buttons.REQUEST_SUPERUSER)
    builder.button(text=Buttons.BACK)

    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)