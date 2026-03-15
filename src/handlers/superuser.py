from aiogram import F, Router
from aiogram.types import Message

from constants.bot_constants import Buttons
from constants.texts import (
    CONFIRM_ROLE_NOT_READY_TEXT,
    LEAD_MENU_TEXT,
    ROLE_REQUESTS_NOT_READY_TEXT,
    BAN_USER_NOT_READY_TEXT,
)
from filters.active_role import ActiveRoleFilter
from keyboards.role_menus import get_lead_main_keyboard, get_superuser_menu_keyboard
from roles import Role
from services.auth_service import AuthService


def setup_superuser_router(auth_service: AuthService):
    router = Router()
    router.message.filter(ActiveRoleFilter(auth_service, Role.SUPERUSER))

    @router.message(F.text == Buttons.SUPERUSER_ROLE_REQUESTS)
    async def role_requests_handler(message: Message):
        await message.answer(
            ROLE_REQUESTS_NOT_READY_TEXT,
            reply_markup=get_superuser_menu_keyboard(),
        )

    @router.message(F.text == Buttons.SUPERUSER_CONFIRM_ROLE)
    async def confirm_role_handler(message: Message):
        await message.answer(
            CONFIRM_ROLE_NOT_READY_TEXT,
            reply_markup=get_superuser_menu_keyboard(),
        )

    @router.message(F.text == Buttons.SUPERUSER_BAN_USER)
    async def ban_user_handler(message: Message):
        await message.answer(
            BAN_USER_NOT_READY_TEXT,
            reply_markup=get_superuser_menu_keyboard(),
        )

    @router.message(F.text == Buttons.SUPERUSER_LEAD_MENU)
    async def open_lead_menu_handler(message: Message):
        await message.answer(
            LEAD_MENU_TEXT,
            reply_markup=get_lead_main_keyboard(),
        )

    return router
