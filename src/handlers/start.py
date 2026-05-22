from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from constants.texts import (
    BANNED_USER_RESPONSE_TEXT,
    START_MENU_OPEN_TEXT,
    WELCOME_TEXT,
)
from keyboards.auth_menu import get_start_menu_keyboard
from services.auth_service import AuthService


def setup_start_router(auth_service: AuthService):
    router = Router()

    @router.message(CommandStart())
    async def start_handler(message: Message):
        if auth_service.is_banned(message.from_user.id):
            await message.answer(BANNED_USER_RESPONSE_TEXT)
            return

        auth_service.logout(message.from_user.id)
        await message.answer(START_MENU_OPEN_TEXT, reply_markup=ReplyKeyboardRemove())
        await message.answer(
            WELCOME_TEXT,
            reply_markup=get_start_menu_keyboard(),
        )

    return router
