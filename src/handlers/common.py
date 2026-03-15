from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardRemove

from constants.bot_constants import Buttons
from constants.texts import (
    EMPLOYEE_MENU_TEXT,
    INTERN_MENU_TEXT,
    LEAD_MENU_TEXT,
    LOGOUT_TEXT,
    SUPERUSER_MENU_TEXT,
    WELCOME_TEXT,
)
from keyboards.auth_menu import get_start_menu_keyboard
from keyboards.role_menus import (
    get_employee_menu_keyboard,
    get_intern_menu_keyboard,
    get_lead_main_keyboard,
    get_superuser_menu_keyboard,
)
from roles import Role
from services.auth_service import AuthService


def get_role_menu(role: Role):
    if role == Role.SUPERUSER:
        return SUPERUSER_MENU_TEXT, get_superuser_menu_keyboard()
    if role == Role.LEAD:
        return LEAD_MENU_TEXT, get_lead_main_keyboard()
    if role == Role.EMPLOYEE:
        return EMPLOYEE_MENU_TEXT, get_employee_menu_keyboard()
    if role == Role.INTERN:
        return INTERN_MENU_TEXT, get_intern_menu_keyboard()
    raise ValueError(f"Неподдерживаемая роль: {role}")


def setup_common_router(auth_service: AuthService):
    router = Router()

    @router.message(F.text == Buttons.EXIT)
    async def exit_handler(message: Message):
        auth_service.logout(message.from_user.id)
        await message.answer(LOGOUT_TEXT, reply_markup=ReplyKeyboardRemove())
        await message.answer(WELCOME_TEXT, reply_markup=get_start_menu_keyboard())

    return router
