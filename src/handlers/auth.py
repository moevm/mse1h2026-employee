import asyncio

from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.auth_menu import (
    get_roles_keyboard,
    get_start_menu_keyboard,
    get_role_request_keyboard,
)
from roles import Role
from services.auth_service import AuthService
from constants.bot_constants import Callbacks
from services.role_request_service import RoleRequestService
from constants.texts import (
    CHOOSE_ROLE_TEXT,
    NO_ACCESS_ROLE_TEXT,
    ROLE_REQUEST_CHOOSE_TEXT,
    ROLE_REQUEST_SENT_TEXT,
    NO_ROLES_TEXT,
    ROLE_SELECTED_TEXT,
    UNKNOWN_ROLE_TEXT,
    WELCOME_TEXT,
)
from handlers.common import get_role_menu
from keyboards.auth_menu import get_roles_keyboard, get_start_menu_keyboard
from roles import Role
from services.auth_service import AuthService


def setup_auth_router(
    auth_service: AuthService, role_request_service: RoleRequestService
):
    router = Router()

    # кнопка "Авторизация"
    @router.callback_query(F.data == Callbacks.START_AUTH)
    async def start_auth_handler(callback: CallbackQuery):
        tg_id = callback.from_user.id
        user = auth_service.get_user(tg_id)

        if user is None:
            await callback.message.edit_text(
                NO_ROLES_TEXT,
                reply_markup=get_start_menu_keyboard(),
            )
            await callback.answer()
            return

        await callback.message.edit_text(
            CHOOSE_ROLE_TEXT,
            reply_markup=get_roles_keyboard(user.roles),
        )
        await callback.answer()

    # выбор роли
    @router.callback_query(F.data.startswith(f"{Callbacks.AUTH_ROLE}:"))
    async def choose_role_handler(callback: CallbackQuery):
        tg_id = callback.from_user.id
        role_str = callback.data.split(":", maxsplit=1)[1]
        role = Role.from_str(role_str)

        if role is None:
            await callback.answer(UNKNOWN_ROLE_TEXT, show_alert=True)
            return

        if not auth_service.can_login_as_role(tg_id, role):
            await callback.answer(NO_ACCESS_ROLE_TEXT, show_alert=True)
            return

        auth_service.set_active_role(tg_id, role)
        menu_text, keyboard = get_role_menu(role)

        await callback.message.edit_text(
            ROLE_SELECTED_TEXT.format(role=role.title),
        )
        await callback.message.answer(menu_text, reply_markup=keyboard)
        await callback.answer()

    # кнопка назад
    @router.callback_query(F.data == Callbacks.BACK)
    async def back_to_start_handler(callback: CallbackQuery):
        await callback.message.edit_text(
            WELCOME_TEXT,
            reply_markup=get_start_menu_keyboard(),
        )
        await callback.answer()

    # получение роли
    @router.callback_query(F.data == Callbacks.REQUEST_ROLE)
    async def request_role_handler(callback: CallbackQuery):
        await callback.message.edit_text(
            ROLE_REQUEST_CHOOSE_TEXT,
            reply_markup=get_role_request_keyboard(),
        )
        await callback.answer()

    # выбор желаемой роли
    @router.callback_query(F.data.startswith(f"{Callbacks.REQUEST_ROLE_SELECT}:"))
    async def request_role_select_handler(callback: CallbackQuery):
        tg_id = callback.from_user.id
        role_str = callback.data.split(":")[1]

        role = Role.from_str(role_str)
        if role is None:
            await callback.answer(UNKNOWN_ROLE_TEXT, show_alert=True)
            return

        await asyncio.to_thread(role_request_service.create_request, tg_id, role)

        await callback.message.edit_text(
            ROLE_REQUEST_SENT_TEXT.format(role=role.value),
            reply_markup=get_start_menu_keyboard(),
        )
        await callback.answer()

    return router
