from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.auth_menu import get_roles_keyboard, get_start_menu_keyboard
from roles import Role
from services.auth_service import AuthService
from constants.bot_constants import Callbacks
from constants.texts import (
    WELCOME_TEXT,
    NO_ROLES_TEXT,
    CHOOSE_ROLE_TEXT,
    UNKNOWN_ROLE_TEXT,
    NO_ACCESS_ROLE_TEXT,
    AUTH_SUCCESS_TEXT,
    ROLE_REQUEST_NOT_READY_TEXT,
)


def setup_auth_router(auth_service: AuthService):
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
        role_str = callback.data.split(":")[1]

        role = Role.from_str(role_str)

        if role is None:
            await callback.answer(UNKNOWN_ROLE_TEXT, show_alert=True)
            return

        if not auth_service.can_login_as_role(tg_id, role):
            await callback.answer(NO_ACCESS_ROLE_TEXT, show_alert=True)
            return

        await callback.message.edit_text(
            AUTH_SUCCESS_TEXT.format(role=role.value)
        )

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
            ROLE_REQUEST_NOT_READY_TEXT,
            reply_markup=get_start_menu_keyboard(),
        )
        await callback.answer()

    return router