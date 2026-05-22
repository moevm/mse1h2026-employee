from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from services.cleanup_service import CleanupService


# ── Fake GoogleSheetsClient ───────────────────────────────────────────────────

class FakeSheetsClient:
    def __init__(self, sheets: dict[str, list[list[str]]]):
        """sheets = { sheet_name: [ header_row, data_row, ... ] }"""
        self.sheets = {k: [list(r) for r in v] for k, v in sheets.items()}
        self.deleted_rows: dict[str, list[int]] = {}

    def get_all_values(self, sheet_name: str) -> list[list[str]]:
        return list(self.sheets.get(sheet_name, []))

    def delete_rows_batch(self, sheet_name: str, row_indices: list[int]) -> int:
        self.deleted_rows.setdefault(sheet_name, []).extend(row_indices)
        return len(row_indices)


def make_client(sheets: dict[str, list[list[str]]]) -> FakeSheetsClient:
    return FakeSheetsClient(sheets)


def make_service(client: FakeSheetsClient, **overrides) -> CleanupService:
    defaults = dict(
        task_requests_sheet_name="TaskRequests",
        role_requests_sheet_name="RoleRequests",
        manager_bind_requests_sheet_name="ManagerBindRequests",
        reports_sheet_name="Reports",
        visits_sheet_name="Visits",
        accepted_tasks_sheet_name="AcceptedTasks",
        timezone="Europe/Moscow",
    )
    defaults.update(overrides)
    return CleanupService(sheets_client=client, **defaults)


# ── Helpers ───────────────────────────────────────────────────────────────────

OLD_MONTH = "2020-01-01 00:00:00"   # старше 1 месяца и 1 года
OLD_YEAR  = "2024-01-01 00:00:00"   # старше 1 года
FRESH     = "2099-01-01 00:00:00"   # в будущем — никогда не удаляется


# ── Tests: _parse_date ────────────────────────────────────────────────────────

def test_parse_date_full_format():
    from services.cleanup_service import _parse_date
    dt = _parse_date("2020-06-15 10:30:00")
    assert dt is not None
    assert dt.year == 2020 and dt.month == 6 and dt.day == 15


def test_parse_date_short_format():
    from services.cleanup_service import _parse_date
    dt = _parse_date("2020-06-15")
    assert dt is not None
    assert dt.year == 2020


def test_parse_date_invalid_returns_none():
    from services.cleanup_service import _parse_date
    assert _parse_date("not-a-date") is None
    assert _parse_date("") is None


# ── Tests: _find_date_col_index ───────────────────────────────────────────────

def test_find_date_col_created_at():
    from services.cleanup_service import _find_date_col_index
    assert _find_date_col_index(["Telegram ID", "Role", "CreatedAt"]) == 2


def test_find_date_col_started_at():
    from services.cleanup_service import _find_date_col_index
    assert _find_date_col_index(["Telegram ID", "StartedAt", "EndedAt"]) == 1


def test_find_date_col_not_found():
    from services.cleanup_service import _find_date_col_index
    assert _find_date_col_index(["Telegram ID", "Role"]) is None


# ── Tests: _cleanup_sheet ─────────────────────────────────────────────────────

def test_cleanup_sheet_removes_old_rows():
    client = make_client({
        "TaskRequests": [
            ["Telegram ID", "Role", "CreatedAt"],
            ["111", "employee", OLD_MONTH],
            ["222", "lead",     FRESH],
        ]
    })
    svc = make_service(client)
    cutoff = datetime.now(timezone.utc)

    deleted = svc._cleanup_sheet("TaskRequests", cutoff)

    assert deleted == 1
    assert client.deleted_rows["TaskRequests"] == [2]


def test_cleanup_sheet_keeps_fresh_rows():
    client = make_client({
        "TaskRequests": [
            ["Telegram ID", "Role", "CreatedAt"],
            ["111", "employee", FRESH],
            ["222", "lead",     FRESH],
        ]
    })
    svc = make_service(client)
    cutoff = datetime.now(timezone.utc)

    deleted = svc._cleanup_sheet("TaskRequests", cutoff)

    assert deleted == 0
    assert "TaskRequests" not in client.deleted_rows


def test_cleanup_sheet_skips_empty_date():
    client = make_client({
        "RoleRequests": [
            ["Telegram ID", "Role", "CreatedAt"],
            ["111", "employee", ""],   # пустая дата — пропускается
        ]
    })
    svc = make_service(client)
    cutoff = datetime.now(timezone.utc)

    deleted = svc._cleanup_sheet("RoleRequests", cutoff)

    assert deleted == 0


def test_cleanup_sheet_no_date_column_skips():
    client = make_client({
        "RoleRequests": [
            ["Telegram ID", "Role"],
            ["111", "employee"],
        ]
    })
    svc = make_service(client)
    cutoff = datetime.now(timezone.utc)

    deleted = svc._cleanup_sheet("RoleRequests", cutoff)

    assert deleted == 0


def test_cleanup_sheet_empty_sheet():
    client = make_client({"TaskRequests": []})
    svc = make_service(client)
    cutoff = datetime.now(timezone.utc)

    deleted = svc._cleanup_sheet("TaskRequests", cutoff)

    assert deleted == 0


def test_cleanup_sheet_only_header():
    client = make_client({
        "TaskRequests": [["Telegram ID", "Role", "CreatedAt"]]
    })
    svc = make_service(client)
    cutoff = datetime.now(timezone.utc)

    deleted = svc._cleanup_sheet("TaskRequests", cutoff)

    assert deleted == 0


# ── Tests: run (full cleanup) ─────────────────────────────────────────────────

def test_run_month_sheets_cleaned():
    """Запросы старше месяца должны удаляться."""
    client = make_client({
        "TaskRequests":         [["CreatedAt"], [OLD_MONTH]],
        "RoleRequests":         [["CreatedAt"], [OLD_MONTH]],
        "ManagerBindRequests":  [["CreatedAt"], [OLD_MONTH]],
        "Reports":              [["CreatedAt"], [FRESH]],
        "Visits":               [["StartedAt"], [FRESH]],
        "AcceptedTasks":        [["Date"],      [FRESH]],
    })
    svc = make_service(client)
    results = svc.run()

    assert results["TaskRequests"] == 1
    assert results["RoleRequests"] == 1
    assert results["ManagerBindRequests"] == 1
    assert results["Reports"] == 0
    assert results["Visits"] == 0
    assert results["AcceptedTasks"] == 0


def test_run_year_sheets_cleaned():
    """Отчёты/посещения/принятые задачи старше года должны удаляться."""
    client = make_client({
        "TaskRequests":         [["CreatedAt"], [FRESH]],
        "RoleRequests":         [["CreatedAt"], [FRESH]],
        "ManagerBindRequests":  [["CreatedAt"], [FRESH]],
        "Reports":              [["CreatedAt"], [OLD_YEAR]],
        "Visits":               [["StartedAt"], [OLD_YEAR]],
        "AcceptedTasks":        [["Date"],      [OLD_YEAR]],
    })
    svc = make_service(client)
    results = svc.run()

    assert results["TaskRequests"] == 0
    assert results["RoleRequests"] == 0
    assert results["ManagerBindRequests"] == 0
    assert results["Reports"] == 1
    assert results["Visits"] == 1
    assert results["AcceptedTasks"] == 1


def test_run_nothing_to_delete():
    client = make_client({
        "TaskRequests":         [["CreatedAt"], [FRESH]],
        "RoleRequests":         [["CreatedAt"], [FRESH]],
        "ManagerBindRequests":  [["CreatedAt"], [FRESH]],
        "Reports":              [["CreatedAt"], [FRESH]],
        "Visits":               [["StartedAt"], [FRESH]],
        "AcceptedTasks":        [["Date"],      [FRESH]],
    })
    svc = make_service(client)
    results = svc.run()

    assert sum(results.values()) == 0


def test_run_mixed_old_and_fresh():
    """Только старые строки удаляются, свежие остаются."""
    client = make_client({
        "TaskRequests": [
            ["CreatedAt"],
            [OLD_MONTH],
            [FRESH],
            [OLD_MONTH],
        ],
        "RoleRequests":         [["CreatedAt"], [FRESH]],
        "ManagerBindRequests":  [["CreatedAt"], [FRESH]],
        "Reports":              [["CreatedAt"], [FRESH]],
        "Visits":               [["StartedAt"], [FRESH]],
        "AcceptedTasks":        [["Date"],      [FRESH]],
    })
    svc = make_service(client)
    results = svc.run()

    assert results["TaskRequests"] == 2