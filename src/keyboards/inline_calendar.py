from datetime import date

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

CAL_PREFIX = "leadcal"

MONTHS_RU = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]


def build_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=f"{MONTHS_RU[month]} {year}",
            callback_data=f"{CAL_PREFIX}:ignore",
        )
    )

    if month == 2:
        leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        days_in_month = 29 if leap else 28
    elif month in (4, 6, 9, 11):
        days_in_month = 30
    else:
        days_in_month = 31

    day = 1
    for _ in range(5):
        row_buttons = []
        for _ in range(7):
            if day <= days_in_month:
                row_buttons.append(
                    InlineKeyboardButton(
                        text=str(day),
                        callback_data=f"{CAL_PREFIX}:pick:{year}:{month}:{day}",
                    )
                )
                day += 1
            else:
                row_buttons.append(
                    InlineKeyboardButton(text=" ", callback_data=f"{CAL_PREFIX}:ignore")
                )
        builder.row(*row_buttons)

    prev_y, prev_m = (year - 1, 12) if month == 1 else (year, month - 1)
    next_y, next_m = (year + 1, 1) if month == 12 else (year, month + 1)

    builder.row(
        InlineKeyboardButton(text="‹", callback_data=f"{CAL_PREFIX}:nav:{prev_y}:{prev_m}"),
        InlineKeyboardButton(text="Отмена", callback_data=f"{CAL_PREFIX}:cancel"),
        InlineKeyboardButton(text="›", callback_data=f"{CAL_PREFIX}:nav:{next_y}:{next_m}"),
    )

    return builder.as_markup()


def calendar_for_today() -> InlineKeyboardMarkup:
    today = date.today()
    return build_calendar(today.year, today.month)