from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from constants.texts import START_MENU_OPEN_TEXT, WELCOME_TEXT
from keyboards.auth_menu import get_start_menu_keyboard
from services.auth_service import AuthService


def setup_start_router(auth_service: AuthService):
    router = Router()

    @router.message(CommandStart())
    async def start_handler(message: Message):
        auth_service.logout(message.from_user.id)
        await message.answer(START_MENU_OPEN_TEXT, reply_markup=ReplyKeyboardRemove())
        await message.answer(
            WELCOME_TEXT,
            reply_markup=get_start_menu_keyboard(),
        )

    return router
