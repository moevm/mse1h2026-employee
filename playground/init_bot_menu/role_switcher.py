from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from text_menu import WELCOME_MENU_TEXT, EMPLOYEE_MENU_TEXT, LEAD_TEXT
from welcome_menu import welcome_kb
from employee_menu import employee_kb
from lead_menu import lead_main_kb

def register_role_switcher(dp: Dispatcher):
    @dp.message(Command("use_role"))
    async def use_role_handler(message: Message, state: FSMContext):
        await state.clear()

        args = (message.text or "").split(maxsplit=1)
        role = (args[1].strip() if len(args) > 1 else "").lower()

        if role == "employee":
            await message.answer(EMPLOYEE_MENU_TEXT, reply_markup=employee_kb())
            return

        if role == "lead":
            await message.answer(LEAD_TEXT, reply_markup=lead_main_kb())
            return

        await message.answer(WELCOME_MENU_TEXT, reply_markup=welcome_kb())

    @dp.message(Command("exit"))
    async def exit_handler(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(WELCOME_MENU_TEXT, reply_markup=welcome_kb())