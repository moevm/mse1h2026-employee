from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from roles import Role
from constants.bot_constants import Buttons, Callbacks


def get_start_menu_keyboard():
    builder = InlineKeyboardBuilder()

    builder.button(text=Buttons.AUTH, callback_data=Callbacks.START_AUTH)
    builder.button(text=Buttons.REQUEST_ROLE, callback_data=Callbacks.REQUEST_ROLE)

    builder.adjust(1)

    return builder.as_markup()


def get_roles_keyboard(roles: list[Role]):
    builder = InlineKeyboardBuilder()

    for role in roles:
        builder.button(
            text=role.value,
            callback_data=f"{Callbacks.AUTH_ROLE}:{role.value}",
        )

    builder.button(text=Buttons.BACK, callback_data=Callbacks.BACK)

    builder.adjust(1)

    return builder.as_markup()