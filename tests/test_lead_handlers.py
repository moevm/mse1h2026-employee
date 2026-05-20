from __future__ import annotations

import asyncio
from conftest import FakeCallback, FakeChatInfo, FakeMessage, get_handler
from constants.bot_constants import Buttons
from constants.texts import (
    LEAD_BIND_REQUEST_ACCEPTED_TEXT,
    LEAD_BIND_REQUEST_REJECTED_TEXT,
    LEAD_CREATE_TASK_DEADLINE_PROMPT,
    LEAD_CREATE_TASK_INVALID_EMPLOYEE_TEXT,
    LEAD_CREATE_TASK_NO_EMPLOYEES_TEXT,
    LEAD_CREATE_TASK_SELECT_EMPLOYEE_PROMPT,
    LEAD_CREATE_TASK_SUCCESS,
    LEAD_CREATE_TASK_TITLE_PROMPT,
    LEAD_REJECT_COMMENT_EMPTY,
    LEAD_REJECT_REPORT_SUCCESS,
    LEAD_REPORT_NOT_FOUND_TEXT,
    LEAD_REPORTS_EMPTY_TEXT,
    LEAD_REPORTS_LIST_TEXT,
    LEAD_REPORTS_TEXT,
    LEAD_DAILY_REPORTS_EMPTY_TEXT,
    LEAD_DAILY_REPORTS_OUT_OF_RANGE_TEXT,
    LEAD_DAILY_REPORTS_SELECTED_DATE_TEXT,
    LEAD_DAILY_REPORTS_SELECT_DATE_TEXT,
    LEAD_TASK_PROPOSAL_ACCEPT_DEADLINE_PROMPT,
    LEAD_TASK_PROPOSAL_ACCEPT_SUCCESS,
    LEAD_TASK_PROPOSAL_REJECT_SUCCESS,
    LEAD_TASK_PROPOSALS_EMPTY_TEXT,
    LEAD_TASK_PROPOSALS_LIST_TEXT,
    LEAD_TASKS_EMPTY_TEXT,
    LEAD_TASKS_LIST_TEXT,
    LEAD_WEEKLY_TEXT,
    LEAD_WEEKLY_PERIOD_TEXT,
    LEAD_WEEKLY_NO_EMPLOYEES_TEXT,
    LEAD_WEEKLY_INVALID_EMPLOYEE_TEXT,
    LEAD_WEEKLY_INVALID_PERIOD_TEXT,
    TASK_NOT_FOUND_TEXT,
    VISIT_FINISH_NO_OPEN_TEXT,
    VISIT_FINISH_SUCCESS_TEXT,
    VISIT_START_ALREADY_OPEN_TEXT,
    VISIT_START_SUCCESS_TEXT,
    LEAD_ACCEPT_REPORT_SUCCESS,
    LEAD_ACCEPT_REPORT_COMMENT_QUESTION,
    LEAD_ACCEPT_REPORT_COMMENT_PROMPT
)
from handlers.lead import (
    format_manager_bind_request_for_lead,
    format_report_details_for_lead,
    format_report_summary_for_lead,
    format_daily_report_for_lead,
    format_task_proposal_for_lead,
    setup_lead_router,
)
from keyboards.inline_calendar import CAL_PREFIX
from keyboards.role_menus import (
    LEAD_REPORT_CALLBACK_PREFIX,
    MANAGER_BIND_CALLBACK_PREFIX,
    TASK_PROPOSAL_CALLBACK_PREFIX,
    get_lead_main_keyboard,
    get_lead_reports_keyboard,
)
from roles import Role
from states.lead import LeadStates
from helpers import (
    FakeLeadAcceptedTasksService,
    FakeLeadAuthService,
    FakeLeadBot,
    FakeLeadManagerBindingService,
    FakeLeadMessage,
    FakeLeadReportsService,
    FakeLeadState,
    FakeLeadTaskRequestService,
    FakeLeadTasksService,
    FakeDailyReportsService,
    FakeLeadVisitsService,
    make_bind_request,
    make_report,
    make_request,
    make_task,
    make_daily_report,
    make_accepted_task,
)


def run(coro):
    return asyncio.run(coro)


def build_router(*, auth=None, visits=None, tasks=None, reports=None, accepted=None, task_requests=None, bindings=None, daily_reports=None):
    return setup_lead_router(
        auth or FakeLeadAuthService(),
        tasks or FakeLeadTasksService(),
        visits or FakeLeadVisitsService(),
        reports or FakeLeadReportsService(),
        accepted or FakeLeadAcceptedTasksService(),
        task_requests or FakeLeadTaskRequestService(),
        bindings or FakeLeadManagerBindingService(),
        daily_reports_service=daily_reports or FakeDailyReportsService(),
    )


def test_lead_formatters_escape_html_and_fill_empty_values():
    task = make_task(title="<T>", employee_id=100)
    report = make_report(text="<ok>")
    request = make_request()
    bind = make_bind_request()

    assert "&lt;T&gt;" in format_report_summary_for_lead(task, "@dev&qa")
    assert "@dev&amp;qa" in format_report_summary_for_lead(task, "@dev&qa")
    assert "&lt;ok&gt;" in format_report_details_for_lead(task, "@dev", report)
    daily_report = make_daily_report(work_done="<работа>", problems="", completed_tasks_titles="<готово>")

    assert "Предложение" in format_task_proposal_for_lead(request, "@employee")
    assert "Запрос на привязку" in format_manager_bind_request_for_lead(bind, "@employee")
    daily_report_text = format_daily_report_for_lead(daily_report, "@dev&qa")
    assert "@dev&amp;qa" in daily_report_text
    assert "&lt;работа&gt;" in daily_report_text
    assert "&lt;готово&gt;" in daily_report_text


def test_start_and_finish_work_success_and_failure_texts():
    for handler_name, visits, expected in [
        ("start_work", FakeLeadVisitsService(start_result=True), VISIT_START_SUCCESS_TEXT),
        ("start_work", FakeLeadVisitsService(start_result=False), VISIT_START_ALREADY_OPEN_TEXT),
        ("finish_work", FakeLeadVisitsService(finish_result=True), VISIT_FINISH_SUCCESS_TEXT),
        ("finish_work", FakeLeadVisitsService(finish_result=False), VISIT_FINISH_NO_OPEN_TEXT),
    ]:
        router = build_router(visits=visits)
        message = FakeMessage(user_id=200)
        run(get_handler(router, handler_name)(message))
        assert message.answers[-1]["text"] == expected


def test_weekly_report_button_moved_from_main_menu_to_reports_menu():
    assert Buttons.LEAD_WEEKLY_REPORT not in get_lead_main_keyboard().texts()
    assert Buttons.LEAD_WEEKLY_REPORT in get_lead_reports_keyboard().texts()


def test_weekly_report_flow_selects_employee_period_and_renders_task_lists():
    auth = FakeLeadAuthService(team=[100])
    visits = FakeLeadVisitsService(worked_hours=16.5)
    accepted = FakeLeadAcceptedTasksService(records=[
        make_accepted_task(
            "r-closed",
            task_title="Закрытая <задача>",
            description="Описание закрытой",
            closed_at="2026-05-19 18:00:00",
            assigned_at="2026-05-18 09:00:00",
            deadline="2026-05-20",
        ),
        make_accepted_task(
            "r-overdue-closed",
            task_title="Закрытая поздно",
            description="Описание просрочки",
            closed_at="2026-05-20 18:00:00",
            assigned_at="2026-05-18 10:00:00",
            deadline="2026-05-19",
        ),
        make_accepted_task(
            "r-overdue-closed-old-deadline",
            task_title="Закрытая поздно со старым дедлайном",
            description="Не должна попасть в просрочку выбранной недели",
            closed_at="2026-05-21 18:00:00",
            assigned_at="2026-05-15 10:00:00",
            deadline="2026-05-17",
        ),
    ])
    tasks = FakeLeadTasksService([
        make_task(
            "assigned-1",
            title="Назначенная задача",
            description="Описание назначенной",
            created_at="2026-05-18 10:00:00",
            deadline="2026-05-30",
            status="created",
        ),
        make_task(
            "overdue-open",
            title="Открытая просрочка",
            description="Описание открытой просрочки",
            created_at="2026-05-01 10:00:00",
            deadline="2026-05-18",
            status="in process",
        ),
        make_task(
            "overdue-open-old-deadline",
            title="Открытая просрочка со старым дедлайном",
            description="Не должна попасть в просрочку выбранной недели",
            created_at="2026-05-01 10:00:00",
            deadline="2026-05-17",
            status="in process",
        ),
    ])
    daily_reports = FakeDailyReportsService(today="2026-05-20", missing_count=2)
    bot = FakeLeadBot({100: FakeChatInfo(username="employee")})
    router = build_router(auth=auth, visits=visits, tasks=tasks, accepted=accepted, daily_reports=daily_reports)
    state = FakeLeadState()
    message = FakeMessage(user_id=200, bot=bot)

    run(get_handler(router, "lead_weekly_start")(message, state))

    assert message.answers[-1]["text"] == LEAD_WEEKLY_TEXT
    assert state.data["return_to"] == "reports"
    assert state.data["weekly_employee_options"] == {"@employee": 100}
    weekly_employee_buttons = message.answers[-1]["reply_markup"].texts()
    assert "@employee" in weekly_employee_buttons
    assert Buttons.EXIT not in weekly_employee_buttons

    invalid = FakeMessage(text="unknown", user_id=200, bot=bot)
    run(get_handler(router, "lead_weekly_input")(invalid, state))
    assert invalid.answers[-1]["text"] == LEAD_WEEKLY_INVALID_EMPLOYEE_TEXT
    assert Buttons.EXIT not in invalid.answers[-1]["reply_markup"].texts()
    assert state.clear_count == 1

    selected = FakeMessage(text="@employee", user_id=200, bot=bot)
    run(get_handler(router, "lead_weekly_input")(selected, state))

    assert selected.answers[-1]["text"] == LEAD_WEEKLY_PERIOD_TEXT
    period_buttons = selected.answers[-1]["reply_markup"].texts()
    assert len(period_buttons) == 5
    assert period_buttons[0].startswith("Текущая неделя: 18.05.2026 — 20.05.2026")
    assert state.data["weekly_employee_id"] == 100

    invalid_period = FakeMessage(text="не тот период", user_id=200, bot=bot)
    run(get_handler(router, "lead_weekly_period_input")(invalid_period, state))
    assert invalid_period.answers[-1]["text"] == LEAD_WEEKLY_INVALID_PERIOD_TEXT

    period = FakeMessage(text=period_buttons[0], user_id=200, bot=bot)
    run(get_handler(router, "lead_weekly_period_input")(period, state))

    assert state.clear_count == 2
    rendered = period.answers[-1]["text"]
    assert "@employee" in rendered
    assert "<b>Период:</b> 2026-05-18 — 2026-05-20" in rendered
    assert "<b>Закрытые задачи:</b> 2" in rendered
    assert "Закрытая &lt;задача&gt;" in rendered
    assert "Описание закрытой" in rendered
    assert "Дата закрытия: 2026-05-19" in rendered
    assert "<b>Назначенные задачи:</b> 1" in rendered
    assert "Назначенная задача" in rendered
    assert "Дата назначения: 2026-05-18" in rendered
    assert "<b>Задачи с просроченным дедлайном:</b> 2" in rendered
    assert "Закрытая поздно" in rendered
    assert "Открытая просрочка" in rendered
    assert "Дедлайн: 2026-05-19" in rendered
    assert "Дедлайн: 2026-05-18" in rendered
    overdue_block = rendered.split("<b>Задачи с просроченным дедлайном:</b> 2", 1)[1].split("<b>Отработанных часов:</b>", 1)[0]
    assert "Дата назначения:" not in overdue_block
    assert "Дата закрытия:" not in overdue_block
    closed_block = rendered.split("<b>Закрытые задачи:</b> 2", 1)[1].split("<b>Назначенные задачи:</b>", 1)[0]
    assert "Дата назначения:" not in closed_block
    assert "Дата закрытия: 2026-05-19" in closed_block
    assert "Закрытая поздно со старым дедлайном" not in rendered
    assert "Открытая просрочка со старым дедлайном" not in rendered
    assert "<b>Отработанных часов:</b> 16.5\n\n<b>Дней без созданного отчета:</b> 2" in rendered
    assert "Опоздан" not in rendered
    assert period.answers[-1]["parse_mode"] == "HTML"
    assert Buttons.LEAD_WEEKLY_REPORT in period.answers[-1]["reply_markup"].texts()
    assert accepted.get_all_calls == 1
    assert tasks.get_all_calls == 1
    assert visits.hours_calls[0][:1] == (100,)
    assert daily_reports.missing_calls[0][0] == 100


def test_weekly_report_start_shows_empty_team_message():
    router = build_router(auth=FakeLeadAuthService(team=[]))
    message = FakeMessage(user_id=200)
    state = FakeLeadState()

    run(get_handler(router, "lead_weekly_start")(message, state))

    assert message.answers[-1]["text"] == LEAD_WEEKLY_NO_EMPLOYEES_TEXT
    assert message.answers[-1]["reply_markup"].texts() == get_lead_reports_keyboard().texts()
    assert state.state is None


def test_lead_tasks_list_empty_and_non_empty():
    empty_router = build_router(tasks=FakeLeadTasksService([]))
    empty_message = FakeMessage(user_id=200)
    run(get_handler(empty_router, "lead_tasks_list")(empty_message, FakeLeadState()))
    assert empty_message.answers[-1]["text"] == LEAD_TASKS_EMPTY_TEXT

    task = make_task(author_id=200, employee_id=100, title="Важная <задача>")
    bot = FakeLeadBot({100: FakeChatInfo(username="employee")})
    router = build_router(tasks=FakeLeadTasksService([task]))
    message = FakeMessage(user_id=200, bot=bot)
    run(get_handler(router, "lead_tasks_list")(message, FakeLeadState()))
    assert message.answers[0]["text"] == LEAD_TASKS_LIST_TEXT
    assert "Важная &lt;задача&gt;" in message.answers[1]["text"]
    assert "@employee" in message.answers[1]["text"]


def test_bind_requests_list_and_accept_reject_actions():
    request = make_bind_request(lead_id=200, employee_id=100)
    bindings = FakeLeadManagerBindingService([request])
    auth = FakeLeadAuthService(add_manager_result=True)
    bot = FakeLeadBot({100: FakeChatInfo(username="employee")})
    router = build_router(auth=auth, bindings=bindings)

    message = FakeMessage(user_id=200, bot=bot)
    run(get_handler(router, "lead_bind_requests")(message, FakeLeadState()))
    assert "@employee" in message.answers[-1]["text"]

    accept_msg = FakeLeadMessage(user_id=200, bot=bot)
    callback = FakeCallback(data=f"{MANAGER_BIND_CALLBACK_PREFIX}:accept:{request.request_id}", user_id=200, bot=bot, message=accept_msg)
    run(get_handler(router, "lead_bind_request_action")(callback))
    assert auth.add_manager_calls == [(100, Role.EMPLOYEE, 200)]
    assert bindings.deleted == [request.request_id]
    assert accept_msg.answers[-1]["text"] == LEAD_BIND_REQUEST_ACCEPTED_TEXT.format(employee_label="@employee")

    request2 = make_bind_request("bind-2", lead_id=200, employee_id=100)
    bindings2 = FakeLeadManagerBindingService([request2])
    router2 = build_router(bindings=bindings2)
    reject_msg = FakeLeadMessage(user_id=200, bot=bot)
    callback2 = FakeCallback(data=f"{MANAGER_BIND_CALLBACK_PREFIX}:reject:{request2.request_id}", user_id=200, bot=bot, message=reject_msg)
    run(get_handler(router2, "lead_bind_request_action")(callback2))
    assert bindings2.deleted == [request2.request_id]
    assert reject_msg.answers[-1]["text"] == LEAD_BIND_REQUEST_REJECTED_TEXT


def test_task_proposals_list_empty_non_empty_reject_and_accept_start():
    request = make_request(lead_id=200, author_id=100)
    bot = FakeLeadBot({100: FakeChatInfo(username="employee")})
    router = build_router(task_requests=FakeLeadTaskRequestService([request]))

    message = FakeMessage(user_id=200, bot=bot)
    run(get_handler(router, "lead_task_proposals_list")(message, FakeLeadState()))
    assert message.answers[0]["text"] == LEAD_TASK_PROPOSALS_LIST_TEXT
    assert "@employee" in message.answers[1]["text"]

    empty_router = build_router(task_requests=FakeLeadTaskRequestService([]))
    empty_msg = FakeMessage(user_id=200)
    run(get_handler(empty_router, "lead_task_proposals_list")(empty_msg, FakeLeadState()))
    assert empty_msg.answers[-1]["text"] == LEAD_TASK_PROPOSALS_EMPTY_TEXT

    service = FakeLeadTaskRequestService([request])
    reject_router = build_router(task_requests=service)
    reject_msg = FakeLeadMessage(user_id=200)
    cb = FakeCallback(data=f"{TASK_PROPOSAL_CALLBACK_PREFIX}:reject:{request.callback_token}", user_id=200, message=reject_msg)
    run(get_handler(reject_router, "lead_task_proposal_action")(cb, FakeLeadState()))
    assert service.deleted == [request.callback_token]
    assert reject_msg.answers[-1]["text"] == LEAD_TASK_PROPOSAL_REJECT_SUCCESS

    state = FakeLeadState()
    accept_msg = FakeLeadMessage(user_id=200)
    accept_router = build_router(task_requests=FakeLeadTaskRequestService([request]))
    cb2 = FakeCallback(data=f"{TASK_PROPOSAL_CALLBACK_PREFIX}:accept:{request.callback_token}", user_id=200, message=accept_msg)
    run(get_handler(accept_router, "lead_task_proposal_action")(cb2, state))
    assert state.data["task_proposal_token"] == request.callback_token
    assert accept_msg.answers[-1]["text"] == LEAD_TASK_PROPOSAL_ACCEPT_DEADLINE_PROMPT


def test_task_proposal_deadline_pick_creates_task_and_removes_request():
    request = make_request(lead_id=200, author_id=100)
    task_requests = FakeLeadTaskRequestService([request])
    tasks = FakeLeadTasksService()
    bot = FakeLeadBot()
    router = build_router(tasks=tasks, task_requests=task_requests)
    message = FakeLeadMessage(user_id=200, bot=bot)
    state = FakeLeadState({"task_proposal_token": request.callback_token, "task_proposal_message_chat_id": 500, "task_proposal_message_id": 10})
    cb = FakeCallback(data=f"{CAL_PREFIX}:pick:2026:05:20", user_id=200, bot=bot, message=message)

    run(get_handler(router, "lead_task_proposal_deadline_calendar")(cb, state))

    assert tasks.created_tasks == [("Предложение", "Описание", 100, 200, "2026-05-20", "2026-01-01", None)]
    assert task_requests.deleted_related == [request.callback_token]
    assert message.answers[-1]["text"] == LEAD_TASK_PROPOSAL_ACCEPT_SUCCESS
    assert bot.deleted_messages == [(500, 10)]


def test_create_task_flow_validates_title_deadline_employee_and_success():
    auth = FakeLeadAuthService(team=[100, 101])
    tasks = FakeLeadTasksService()
    bot = FakeLeadBot({100: FakeChatInfo(username="dev"), 101: FakeChatInfo(full_name="QA User")})
    router = build_router(auth=auth, tasks=tasks)
    state = FakeLeadState()
    message = FakeMessage(user_id=200, bot=bot)

    run(get_handler(router, "lead_task_create_start")(message, state))
    assert message.answers[-1]["text"] == LEAD_CREATE_TASK_TITLE_PROMPT

    run(get_handler(router, "lead_task_title_input")(FakeMessage(text="", user_id=200), state))
    assert state.data == {}

    run(get_handler(router, "lead_task_title_input")(FakeMessage(text="Новая задача", user_id=200), state))
    assert state.data["task_title"] == "Новая задача"
    assert message.answers[-1]["text"] == LEAD_CREATE_TASK_TITLE_PROMPT

    desc_msg = FakeMessage(text="-", user_id=200)
    run(get_handler(router, "lead_task_description_input")(desc_msg, state))
    assert state.data["task_description"] == ""
    assert desc_msg.answers[-1]["text"] == LEAD_CREATE_TASK_DEADLINE_PROMPT

    deadline_msg = FakeLeadMessage(user_id=200, bot=bot)
    cb = FakeCallback(data=f"{CAL_PREFIX}:pick:2026:06:01", user_id=200, bot=bot, message=deadline_msg)
    run(get_handler(router, "lead_deadline_calendar")(cb, state))
    assert state.data["deadline"] == "2026-06-01"
    assert state.data["employee_options"] == {"@dev": 100, "QA User": 101}
    assert deadline_msg.answers[-1]["text"] == LEAD_CREATE_TASK_SELECT_EMPLOYEE_PROMPT

    invalid = FakeMessage(text="Nobody", user_id=200)
    run(get_handler(router, "lead_task_employee_select")(invalid, state))
    assert invalid.answers[-1]["text"] == LEAD_CREATE_TASK_INVALID_EMPLOYEE_TEXT

    selected = FakeMessage(text="@dev", user_id=200)
    run(get_handler(router, "lead_task_employee_select")(selected, state))
    assert tasks.created_tasks == [("Новая задача", "", 100, 200, "2026-06-01")]
    assert selected.answers[-1]["text"] == LEAD_CREATE_TASK_SUCCESS


def test_create_task_deadline_with_no_team_members_returns_no_employees_text():
    router = build_router(auth=FakeLeadAuthService(team=[]))
    state = FakeLeadState({"task_title": "T", "task_description": "D"})
    message = FakeLeadMessage(user_id=200, bot=FakeLeadBot())
    cb = FakeCallback(data=f"{CAL_PREFIX}:pick:2026:06:01", user_id=200, message=message)

    run(get_handler(router, "lead_deadline_calendar")(cb, state))

    assert state.clear_count == 1
    assert message.answers[-1]["text"] == LEAD_CREATE_TASK_NO_EMPLOYEES_TEXT


def test_reports_list_filters_only_own_reports_on_consideration():
    own = make_task("own", author_id=200, employee_id=100, status="on consideration")
    foreign = make_task("foreign", author_id=201, employee_id=101, status="on consideration")
    done = make_task("done", author_id=200, employee_id=102, status="done")
    reports = [make_report("own"), make_report("foreign", employee_id=101), make_report("done", employee_id=102)]
    bot = FakeLeadBot({100: FakeChatInfo(username="employee")})
    router = build_router(tasks=FakeLeadTasksService([own, foreign, done]), reports=FakeLeadReportsService(reports))
    message = FakeMessage(user_id=200, bot=bot)

    run(get_handler(router, "lead_reports_list")(message, FakeLeadState()))

    assert message.answers[0]["text"] == LEAD_REPORTS_LIST_TEXT
    assert len(message.answers) == 2
    assert "@employee" in message.answers[1]["text"]

    empty_router = build_router(tasks=FakeLeadTasksService([]), reports=FakeLeadReportsService(reports))
    empty_msg = FakeMessage(user_id=200)
    run(get_handler(empty_router, "lead_reports_list")(empty_msg, FakeLeadState()))
    assert empty_msg.answers[-1]["text"] == LEAD_REPORTS_EMPTY_TEXT


def test_report_action_view_accept_reject_and_not_found_paths():
    task = make_task("task-1", author_id=200, employee_id=100, status="on consideration")
    report = make_report("task-1", text="Отчет")
    bot = FakeLeadBot({100: FakeChatInfo(username="employee")})
    router = build_router(tasks=FakeLeadTasksService([task]), reports=FakeLeadReportsService([report]))

    view_msg = FakeLeadMessage(user_id=200, bot=bot)
    view_cb = FakeCallback(data=f"{LEAD_REPORT_CALLBACK_PREFIX}:view:task-1", user_id=200, bot=bot, message=view_msg)
    run(get_handler(router, "lead_report_action")(view_cb, FakeLeadState()))
    assert "Отчет" in view_msg.answers[-1]["text"]
    assert "@employee" in view_msg.answers[-1]["text"]

    state = FakeLeadState()
    accept_msg = FakeLeadMessage(user_id=200, bot=bot)
    accept_cb = FakeCallback(data=f"{LEAD_REPORT_CALLBACK_PREFIX}:accept:task-1", user_id=200, bot=bot, message=accept_msg)
    run(get_handler(router, "lead_report_action")(accept_cb, state))
    assert state.data["task_id"] == "task-1"
    assert accept_msg.answers[-1]["text"] == LEAD_ACCEPT_REPORT_COMMENT_QUESTION

    reject_state = FakeLeadState()
    reject_msg = FakeLeadMessage(user_id=200, bot=bot)
    reject_cb = FakeCallback(data=f"{LEAD_REPORT_CALLBACK_PREFIX}:reject:task-1", user_id=200, bot=bot, message=reject_msg)
    run(get_handler(router, "lead_report_action")(reject_cb, reject_state))
    assert reject_state.data["return_to"] == "reports"

    missing_cb = FakeCallback(data=f"{LEAD_REPORT_CALLBACK_PREFIX}:view:missing", user_id=200)
    run(get_handler(router, "lead_report_action")(missing_cb, FakeLeadState()))
    assert missing_cb.answers[-1]["text"] == TASK_NOT_FOUND_TEXT

    foreign_task = make_task("foreign", author_id=201, employee_id=100, status="on consideration")
    foreign_router = build_router(tasks=FakeLeadTasksService([foreign_task]), reports=FakeLeadReportsService([make_report("foreign")]))
    foreign_cb = FakeCallback(data=f"{LEAD_REPORT_CALLBACK_PREFIX}:view:foreign", user_id=200)
    run(get_handler(foreign_router, "lead_report_action")(foreign_cb, FakeLeadState()))
    assert foreign_cb.answers[-1]["text"] == LEAD_REPORT_NOT_FOUND_TEXT


def test_accept_report_without_and_with_comment_moves_report_to_accepted():
    task = make_task("task-1", author_id=200, employee_id=100, status="on consideration")
    report = make_report("task-1")
    tasks = FakeLeadTasksService([task])
    reports = FakeLeadReportsService([report])
    accepted = FakeLeadAcceptedTasksService()
    bot = FakeLeadBot()
    router = build_router(tasks=tasks, reports=reports, accepted=accepted)

    state = FakeLeadState({"accept_message_chat_id": 500, "accept_message_id": 10})
    msg = FakeLeadMessage(user_id=200, bot=bot)
    cb = FakeCallback(data="lead_report_comment:no:task-1", user_id=200, bot=bot, message=msg)
    run(get_handler(router, "lead_report_accept_without_comment")(cb, state))
    assert accepted.accepted[0][2] == ""
    assert reports.deleted_report_task_ids == ["task-1"]
    assert tasks.deleted_task_ids == ["task-1"]
    assert msg.answers[-1]["text"] == LEAD_ACCEPT_REPORT_SUCCESS

    task2 = make_task("task-2", author_id=200, employee_id=100, status="on consideration")
    report2 = make_report("task-2")
    tasks2 = FakeLeadTasksService([task2])
    reports2 = FakeLeadReportsService([report2])
    accepted2 = FakeLeadAcceptedTasksService()
    router2 = build_router(tasks=tasks2, reports=reports2, accepted=accepted2)
    state2 = FakeLeadState({"task_id": "task-2", "accept_message_chat_id": 500, "accept_message_id": 11})
    run(get_handler(router2, "lead_report_accept_with_comment_finish")(FakeMessage(text="Комментарий", user_id=200, bot=bot), state2))
    assert accepted2.accepted[0][2] == "Комментарий"
    assert reports2.deleted_report_task_ids == ["task-2"]
    assert tasks2.deleted_task_ids == ["task-2"]


def test_accept_report_with_comment_start_and_empty_comment_validation():
    router = build_router()
    state = FakeLeadState({"accept_message_chat_id": 500, "accept_message_id": 10})
    msg = FakeLeadMessage(user_id=200)
    cb = FakeCallback(data="lead_report_comment:yes:task-1", user_id=200, message=msg)
    run(get_handler(router, "lead_report_accept_with_comment_start")(cb, state))
    assert state.data["task_id"] == "task-1"
    assert msg.answers[-1]["text"] == LEAD_ACCEPT_REPORT_COMMENT_PROMPT

    empty_msg = FakeMessage(text="   ", user_id=200)
    run(get_handler(router, "lead_report_accept_with_comment_finish")(empty_msg, state))
    assert empty_msg.answers[-1]["text"] == LEAD_REJECT_COMMENT_EMPTY


def test_reject_report_validates_comment_and_updates_feedback_status_and_notifies_employee():
    task = make_task("task-1", author_id=200, employee_id=100, title="Задача", status="on consideration")
    report = make_report("task-1")
    tasks = FakeLeadTasksService([task])
    reports = FakeLeadReportsService([report])
    bot = FakeLeadBot()
    router = build_router(tasks=tasks, reports=reports)
    state = FakeLeadState({"task_id": "task-1", "reject_message_chat_id": 500, "reject_message_id": 10})

    empty_msg = FakeMessage(text="  ", user_id=200)
    run(get_handler(router, "lead_report_reject_finish")(empty_msg, state))
    assert empty_msg.answers[-1]["text"] == LEAD_REJECT_COMMENT_EMPTY

    message = FakeMessage(text="Исправить", user_id=200, bot=bot)
    run(get_handler(router, "lead_report_reject_finish")(message, state))
    assert reports.feedback_updates == [("task-1", "Исправить")]
    assert tasks.status_updates == [("task-1", "cancelled")]
    assert bot.deleted_messages == [(500, 10)]
    assert bot.sent_messages and "Исправить" in bot.sent_messages[0][1]
    assert message.answers[-1]["text"] == LEAD_REJECT_REPORT_SUCCESS

def test_lead_daily_reports_start_sets_state_and_shows_limited_calendar():
    daily_reports = FakeDailyReportsService(today="2026-05-17")
    router = build_router(daily_reports=daily_reports)
    state = FakeLeadState({"old": "data"})
    message = FakeMessage(text=Buttons.LEAD_DAILY_REPORTS, user_id=200)

    run(get_handler(router, "lead_daily_reports_start")(message, state))

    assert state.clear_count == 1
    assert state.state is LeadStates.waiting_daily_report_date
    assert state.data["return_to"] == "reports"
    assert message.answers[0]["text"] == LEAD_DAILY_REPORTS_SELECT_DATE_TEXT
    keyboard = message.answers[0]["reply_markup"]
    callback_values = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{CAL_PREFIX}:pick:2026:5:17" in callback_values
    assert f"{CAL_PREFIX}:pick:2025:5:16" not in callback_values


def test_lead_daily_reports_pick_date_renders_team_reports_without_reopening_reports_menu():
    report = make_daily_report(
        employee_id=100,
        report_date="2026-05-17",
        work_done="Сделал <задачи>",
        problems="",
        completed_tasks_count=2,
        completed_tasks_titles="Задача 1\nЗадача <2>",
        in_process_tasks_count=1,
        in_process_tasks_titles="Текущая",
    )
    daily_reports = FakeDailyReportsService([report], today="2026-05-17")
    auth = FakeLeadAuthService(team=[100, 101])
    bot = FakeLeadBot({100: FakeChatInfo(username="employee")})
    router = build_router(auth=auth, daily_reports=daily_reports)
    state = FakeLeadState()
    message = FakeLeadMessage(user_id=200, bot=bot)
    callback = FakeCallback(
        data=f"{CAL_PREFIX}:pick:2026:5:17",
        user_id=200,
        bot=bot,
        message=message,
    )

    run(get_handler(router, "lead_daily_reports_calendar")(callback, state))

    assert state.clear_count == 1
    assert daily_reports.list_calls == [("2026-05-17", [100, 101])]
    assert message.edits[0]["text"] == LEAD_DAILY_REPORTS_SELECTED_DATE_TEXT.format(date="2026-05-17")
    assert len(message.answers) == 1
    rendered = message.answers[0]["text"]
    assert "@employee" in rendered
    assert "Сделал &lt;задачи&gt;" in rendered
    assert "Задача &lt;2&gt;" in rendered
    assert "<b>Выполненныx задач за день:</b> 2" in rendered
    assert all(answer["text"] != LEAD_REPORTS_TEXT for answer in message.answers)


def test_lead_daily_reports_pick_date_empty_result_does_not_repeat_reports_menu_text():
    daily_reports = FakeDailyReportsService(today="2026-05-17")
    auth = FakeLeadAuthService(team=[100])
    router = build_router(auth=auth, daily_reports=daily_reports)
    state = FakeLeadState()
    message = FakeLeadMessage(user_id=200)
    callback = FakeCallback(data=f"{CAL_PREFIX}:pick:2026:5:17", user_id=200, message=message)

    run(get_handler(router, "lead_daily_reports_calendar")(callback, state))

    assert state.clear_count == 1
    assert message.edits[0]["text"] == LEAD_DAILY_REPORTS_SELECTED_DATE_TEXT.format(date="2026-05-17")
    assert message.answers[0]["text"] == LEAD_DAILY_REPORTS_EMPTY_TEXT
    assert all(answer["text"] != LEAD_REPORTS_TEXT for answer in message.answers)


def test_lead_daily_reports_rejects_dates_older_than_one_year():
    daily_reports = FakeDailyReportsService(today="2026-05-17")
    router = build_router(daily_reports=daily_reports)
    state = FakeLeadState()
    callback = FakeCallback(data=f"{CAL_PREFIX}:pick:2025:5:16", user_id=200)

    run(get_handler(router, "lead_daily_reports_calendar")(callback, state))

    assert callback.answers[0]["text"] == LEAD_DAILY_REPORTS_OUT_OF_RANGE_TEXT
    assert callback.answers[0]["show_alert"] is True
    assert daily_reports.list_calls == []
    assert state.clear_count == 0
