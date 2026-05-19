from __future__ import annotations

import calendar
from datetime import date, timedelta

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

CAL_PREFIX = "leadcal"

MONTHS_RU = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def _month_first_day(year: int, month: int) -> date:
    return date(year, month, 1)


def _month_last_day(year: int, month: int) -> date:
    first_day = _month_first_day(year, month)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    return next_month - timedelta(days=1)


def _previous_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _next_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def _can_open_month(year: int, month: int, min_date: date | None, max_date: date | None) -> bool:
    first_day = _month_first_day(year, month)
    last_day = _month_last_day(year, month)

    if min_date is not None and last_day < min_date:
        return False
    if max_date is not None and first_day > max_date:
        return False
    return True


def build_calendar(
    year: int,
    month: int,
    min_date: date | None = None,
    max_date: date | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=f"{MONTHS_RU[month]} {year}",
            callback_data=f"{CAL_PREFIX}:ignore",
        )
    )

    builder.row(
        *[
            InlineKeyboardButton(text=weekday, callback_data=f"{CAL_PREFIX}:ignore")
            for weekday in WEEKDAYS_RU
        ]
    )

    month_calendar = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)
    for week in month_calendar:
        row_buttons = []
        for day in week:
            if day == 0:
                row_buttons.append(InlineKeyboardButton(text=" ", callback_data=f"{CAL_PREFIX}:ignore"))
                continue

            current_day = date(year, month, day)
            is_allowed = True
            if min_date is not None and current_day < min_date:
                is_allowed = False
            if max_date is not None and current_day > max_date:
                is_allowed = False

            callback_data = (
                f"{CAL_PREFIX}:pick:{year}:{month}:{day}"
                if is_allowed
                else f"{CAL_PREFIX}:ignore"
            )
            row_buttons.append(InlineKeyboardButton(text=str(day), callback_data=callback_data))
        builder.row(*row_buttons)

    prev_y, prev_m = _previous_month(year, month)
    next_y, next_m = _next_month(year, month)

    prev_text = "‹" if _can_open_month(prev_y, prev_m, min_date, max_date) else " "
    prev_callback = (
        f"{CAL_PREFIX}:nav:{prev_y}:{prev_m}"
        if _can_open_month(prev_y, prev_m, min_date, max_date)
        else f"{CAL_PREFIX}:ignore"
    )
    next_text = "›" if _can_open_month(next_y, next_m, min_date, max_date) else " "
    next_callback = (
        f"{CAL_PREFIX}:nav:{next_y}:{next_m}"
        if _can_open_month(next_y, next_m, min_date, max_date)
        else f"{CAL_PREFIX}:ignore"
    )

    builder.row(
        InlineKeyboardButton(text=prev_text, callback_data=prev_callback),
        InlineKeyboardButton(text="Отмена", callback_data=f"{CAL_PREFIX}:cancel"),
        InlineKeyboardButton(text=next_text, callback_data=next_callback),
    )

    return builder.as_markup()


def calendar_for_today() -> InlineKeyboardMarkup:
    today = date.today()
    return build_calendar(today.year, today.month)


def calendar_for_range(
    min_date: date,
    max_date: date,
    initial_date: date | None = None,
) -> InlineKeyboardMarkup:
    initial_date = initial_date or max_date
    return build_calendar(
        initial_date.year,
        initial_date.month,
        min_date=min_date,
        max_date=max_date,
    )
