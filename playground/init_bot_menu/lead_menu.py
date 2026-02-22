from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from text_menu import EMPLOYEE_MENU_TEXT
from employee_menu import employee_kb
from text_menu import LEAD_TEXT, TASKS_TEXT, REPORTS_TEXT, WEEKLY_TEXT

class LeadStates(StatesGroup):
    waiting_task_input = State()
    waiting_report_id = State()
    viewing_report = State()
    waiting_deny_comment = State()
    waiting_weekly_user = State()

# Кнопочки
def lead_main_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Задачи")
    kb.button(text="Отчеты")
    kb.button(text="Недельный отчет")
    kb.button(text="Сотрудник")
    kb.button(text="/exit")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def lead_tasks_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Создать задачу")
    kb.button(text="Список задач")
    kb.button(text="Главная")
    kb.button(text="/exit")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)

def lead_reports_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Список отчетов")
    kb.button(text="Открыть отчет")
    kb.button(text="Главная")
    kb.button(text="/exit")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)

def lead_report_actions_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Подтвердить")
    kb.button(text="Отклонить")
    kb.button(text="К отчетам")
    kb.button(text="/exit")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)

def lead_cancel_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Отмена")
    kb.button(text="/exit")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

# Регистрация меню
def register_lead_menu(dp: Dispatcher):
    # Главное меню
    @dp.message(F.text == "Задачи")
    async def lead_tasks_menu(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(TASKS_TEXT, reply_markup=lead_tasks_kb())

    @dp.message(F.text == "Отчеты")
    async def lead_reports_menu(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(REPORTS_TEXT, reply_markup=lead_reports_kb())

    @dp.message(F.text == "Недельный отчет")
    async def lead_weekly_start(message: Message, state: FSMContext):
        await state.set_state(LeadStates.waiting_weekly_user)
        await state.update_data(return_to="main")
        await message.answer(WEEKLY_TEXT, reply_markup=lead_cancel_kb())

    @dp.message(F.text == "Сотрудник")
    async def lead_to_employee(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(EMPLOYEE_MENU_TEXT, reply_markup=employee_kb())

    @dp.message(F.text == "Главная")
    async def lead_back_to_main(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(LEAD_TEXT, reply_markup=lead_main_kb())

    @dp.message(F.text == "Отмена")
    async def lead_cancel(message: Message, state: FSMContext):
        st = await state.get_state()
        if not st:
            return

        data = await state.get_data()
        return_to = data.get("return_to", "main")
        await state.clear()
        
        if return_to == "tasks":
            await message.answer(TASKS_TEXT, reply_markup=lead_tasks_kb())
        elif return_to == "reports":
            await message.answer(REPORTS_TEXT, reply_markup=lead_reports_kb())
        else:
            await message.answer(LEAD_TEXT, reply_markup=lead_main_kb())

    # Задачи
    @dp.message(F.text == "Список задач")
    async def lead_tasks_list(message: Message, state: FSMContext):
        await state.clear()
        await message.answer("Тут будет список задач", reply_markup=lead_tasks_kb())

    @dp.message(F.text == "Создать задачу")
    async def lead_task_create_start(message: Message, state: FSMContext):
        await state.set_state(LeadStates.waiting_task_input)
        await state.update_data(return_to="tasks")
        await message.answer("Тут будут создаваться задачи -> task_desc | employee сообщение", reply_markup=lead_cancel_kb())

    @dp.message(LeadStates.waiting_task_input, F.text)
    async def lead_task_create_input(message: Message, state: FSMContext):
        await state.clear()
        await message.answer("Задача принята", reply_markup=lead_main_kb())

    # Отчеты
    @dp.message(F.text == "Список отчетов")
    async def lead_reports_list(message: Message, state: FSMContext):
        await state.clear()
        await message.answer("Тут будет список отчетов", reply_markup=lead_reports_kb())

    @dp.message(F.text == "Открыть отчет")
    async def lead_report_open_start(message: Message, state: FSMContext):
        await state.set_state(LeadStates.waiting_report_id)
        await state.update_data(return_to="reports")
        await message.answer("Тут можно будет открыть отчет -> report_id одним сообщением", reply_markup=lead_cancel_kb())

    @dp.message(LeadStates.waiting_report_id, F.text)
    async def lead_report_open_input(message: Message, state: FSMContext):
        report_id = message.text.strip().strip("'").strip('"')
        await state.set_state(LeadStates.viewing_report)
        await state.update_data(current_report_id=report_id)
        await message.answer(f"Отчет #{report_id} успешно показан", reply_markup=lead_report_actions_kb())

    @dp.message(LeadStates.viewing_report, F.text == "Подтвердить")
    async def lead_report_confirm(message: Message, state: FSMContext):
        data = await state.get_data()
        report_id = data.get("current_report_id", "UNKNOWN")
        await state.clear()
        await message.answer(f"Отчет '{report_id}' успешно принят", reply_markup=lead_reports_kb())

    @dp.message(LeadStates.viewing_report, F.text == "Отклонить")
    async def lead_report_deny_start(message: Message, state: FSMContext):
        data = await state.get_data()
        report_id = data.get("current_report_id", "UNKNOWN")
        await state.set_state(LeadStates.waiting_deny_comment)
        await state.update_data(return_to="reports", current_report_id=report_id)
        await message.answer(f"Отчет #{report_id} отклонен, оставить комментарий", reply_markup=lead_cancel_kb())

    @dp.message(LeadStates.waiting_deny_comment, F.text)
    async def lead_report_deny_comment(message: Message, state: FSMContext):
        data = await state.get_data()
        report_id = data.get("current_report_id", "UNKNOWN")
        comment = message.text.strip()
        await state.clear()
        await message.answer(f"Комментарий для '{report_id}' '{comment}' отправлен", reply_markup=lead_reports_kb())

    @dp.message(LeadStates.viewing_report, F.text == "К отчетам")
    async def lead_back_to_reports(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(REPORTS_TEXT, reply_markup=lead_reports_kb())

    # Недельный отчет
    @dp.message(LeadStates.waiting_weekly_user, F.text)
    async def lead_weekly_input(message: Message, state: FSMContext):
        user = message.text.strip().strip("'").strip('"')
        await state.clear()
        await message.answer(f"Недельный отчет о сотруднике создан", reply_markup=lead_main_kb())