from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dateutil.relativedelta import relativedelta

from services.google_sheets import GoogleSheetsClient

logger = logging.getLogger(__name__)

_DATE_COLUMNS = [
    "CreatedAt",
    "StartedAt",
    "Date",
    "created_at",
    "date",
]


def _parse_date(value: str) -> datetime | None:
    value = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y", "%d.%m.%Y %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _find_date_col_index(headers: list[str]) -> int | None:
    normalized = [h.strip() for h in headers]
    for candidate in _DATE_COLUMNS:
        if candidate in normalized:
            return normalized.index(candidate)
    return None


class CleanupService:
    def __init__(
        self,
        sheets_client: GoogleSheetsClient,
        *,
        task_requests_sheet_name: str,
        role_requests_sheet_name: str,
        manager_bind_requests_sheet_name: str,
        reports_sheet_name: str,
        visits_sheet_name: str,
        accepted_tasks_sheet_name: str,
        timezone: str = "Europe/Moscow",
        cleanup_hour: int = 3,
    ):
        self.sheets_client = sheets_client
        self._month_sheets = [
            task_requests_sheet_name,
            role_requests_sheet_name,
            manager_bind_requests_sheet_name,
        ]
        self._year_sheets = [
            reports_sheet_name,
            visits_sheet_name,
            accepted_tasks_sheet_name,
        ]
        self._tz = ZoneInfo(timezone)
        self._cleanup_hour = cleanup_hour
        self._scheduler = AsyncIOScheduler(timezone=self._tz)
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._scheduler.add_job(
            self._run,
            trigger=CronTrigger(hour=self._cleanup_hour, minute=0, timezone=self._tz),
            id="cleanup:daily",
            replace_existing=True,
            coalesce=True,
            misfire_grace_time=60 * 60,
            max_instances=1,
        )
        self._scheduler.start()
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        self._scheduler.shutdown(wait=False)
        self._started = False

    async def _run(self) -> None:
        try:
            results = await asyncio.to_thread(self.run)
            total = sum(results.values())
            logger.info("Cleanup завершён: удалено %d строк. Детали: %s", total, results)
        except Exception as exc:
            logger.error("Ошибка при очистке: %s", exc)

    def _cleanup_sheet(self, sheet_name: str, cutoff: datetime) -> int:
        try:
            values = self.sheets_client.get_all_values(sheet_name)
        except Exception as exc:
            logger.warning("Cleanup: не удалось прочитать лист '%s': %s", sheet_name, exc)
            return 0

        if len(values) < 2:
            return 0

        headers = values[0]
        date_col = _find_date_col_index(headers)

        if date_col is None:
            logger.warning(
                "Cleanup: в листе '%s' не найдена колонка с датой (искал: %s)",
                sheet_name,
                _DATE_COLUMNS,
            )
            return 0

        rows_to_delete: list[int] = []
        for row_index, row in enumerate(values[1:], start=2):
            raw = row[date_col] if date_col < len(row) else ""
            dt = _parse_date(raw)
            if dt is not None and dt < cutoff:
                rows_to_delete.append(row_index)

        if not rows_to_delete:
            return 0

        deleted = self.sheets_client.delete_rows_batch(sheet_name, rows_to_delete)
        logger.info(
            "Cleanup: лист '%s' — удалено %d строк (старше %s)",
            sheet_name,
            deleted,
            cutoff.strftime("%Y-%m-%d"),
        )
        return deleted

    def run(self) -> dict[str, int]:
        now = datetime.now(timezone.utc)
        month_cutoff = now - relativedelta(months=1)
        year_cutoff = now - relativedelta(years=1)

        results: dict[str, int] = {}
        for sheet_name in self._month_sheets:
            results[sheet_name] = self._cleanup_sheet(sheet_name, month_cutoff)
        for sheet_name in self._year_sheets:
            results[sheet_name] = self._cleanup_sheet(sheet_name, year_cutoff)
        return results