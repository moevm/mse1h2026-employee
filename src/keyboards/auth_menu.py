from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants.bot_constants import Buttons, Callbacks
from roles import Role


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
            text=role.title.capitalize(),
            callback_data=f"{Callbacks.AUTH_ROLE}:{role.value}",
        )

    builder.button(text=Buttons.BACK, callback_data=Callbacks.BACK)
    builder.adjust(1)

    return builder.as_markup()


def get_role_request_keyboard():
    builder = InlineKeyboardBuilder()

    builder.button(
        text=Buttons.REQUEST_INTERN,
        callback_data=f"{Callbacks.REQUEST_ROLE_SELECT}:{Role.INTERN.value}",
    )

    builder.button(
        text=Buttons.REQUEST_EMPLOYEE,
        callback_data=f"{Callbacks.REQUEST_ROLE_SELECT}:{Role.EMPLOYEE.value}",
    )

    builder.button(
        text=Buttons.REQUEST_LEAD,
        callback_data=f"{Callbacks.REQUEST_ROLE_SELECT}:{Role.LEAD.value}",
    )

    builder.button(
        text=Buttons.REQUEST_SUPERUSER,
        callback_data=f"{Callbacks.REQUEST_ROLE_SELECT}:{Role.SUPERUSER.value}",
    )

    builder.button(text=Buttons.BACK, callback_data=Callbacks.BACK)

    builder.adjust(1)
    
    return builder.as_markup()
