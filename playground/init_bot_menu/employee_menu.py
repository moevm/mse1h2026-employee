from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from text_menu import WELCOME_MENU_TEXT

def employee_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="/start_work")
    kb.button(text="/finish_work")
    kb.button(text="/create_my_task")
    kb.button(text="/my_task_list")
    kb.button(text="/complete_task")
    kb.button(text="/report_comm")
    kb.button(text="/exit")
    kb.adjust(2, 2, 2, 1) 
    return kb.as_markup(resize_keyboard=True)


def register_employee_menu(dp: Dispatcher):
    @dp.message(Command("start_work"))
    async def start_work(message: Message):
        await message.answer("/start_work - заглушка(здесь будет реализован функционал начала рабочего дня).", reply_markup=employee_kb())

    @dp.message(Command("finish_work"))
    async def finish_work(message: Message):
        await message.answer("/finish_work - заглушка(здесь будет реализован функционал конца рабочего дня).", reply_markup=employee_kb())

    @dp.message(Command("create_my_task"))
    async def create_my_task(message: Message):
        await message.answer("/create_my_task - заглушка(здесь будет реализован функционал создания задачи).", reply_markup=employee_kb())

    @dp.message(Command("my_task_list"))
    async def my_task_list(message: Message):
        await message.answer("/my_task_list - заглушка(здесь будет реализован функционал просмотра списка задач).", reply_markup=employee_kb())

    @dp.message(Command("complete_task"))
    async def complete_task(message: Message):
        await message.answer("/complete_task - заглушка(здесь будет реализован функционал отправки отчета о выполненной задаче).", reply_markup=employee_kb())

    @dp.message(Command("report_comm"))
    async def report_comm(message: Message):
        await message.answer("/report_comm - заглушка(здесь будет реализован функционал просмотра комментария руководителя).", reply_markup=employee_kb())

    @dp.message(Command("exit"))
    async def exit_to_welcome(message: Message):
        await message.answer(WELCOME_MENU_TEXT)