from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from text_menu import WELCOME_MENU_TEXT

def welcome_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="/grant_role employee")
    kb.button(text="/use_role employee")
    kb.button(text="/grant_role lead")
    kb.button(text="/use_role lead")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)


def register_welcome_menu(dp: Dispatcher):
    @dp.message(Command("start"))
    async def start_handler(message: Message):
        await message.answer(WELCOME_MENU_TEXT, reply_markup=welcome_kb())

    @dp.message(Command("grant_role"))
    async def grant_role_stub(message: Message):
        await message.answer(
            "/grant_role — заглушка (функционал пока не реализован).",
            reply_markup=welcome_kb(),
        )