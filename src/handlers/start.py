from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.auth_menu import get_start_menu_keyboard
from constants.texts import WELCOME_TEXT

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        WELCOME_TEXT,
        reply_markup=get_start_menu_keyboard(),
    )