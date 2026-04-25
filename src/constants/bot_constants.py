class Buttons:
    AUTH = "Авторизация"
    REQUEST_ROLE = "Получение роли"
    BACK = "Назад"

    REQUEST_INTERN = "<Стажёр>"
    REQUEST_EMPLOYEE = "<Сотрудник>"   
    REQUEST_LEAD = "<Руководитель>"
    REQUEST_SUPERUSER = "<Администратор>"

    EXIT = "Выйти"
    CANCEL = "Отмена"
    MAIN_MENU = "Главное меню"

    SUPERUSER_ROLE_REQUESTS = "Список запросов ролей"
    SUPERUSER_BAN_USER = "Заблокировать пользователя"
    SUPERUSER_LEAD_MENU = "Меню руководителя"
    SUPERUSER_REVOKE_ROLE = "Отозвать роль"

    LEAD_TASKS = "Задачи"
    LEAD_REPORTS = "Отчеты"
    LEAD_WEEKLY_REPORT = "Недельный отчет"
    LEAD_BIND_REQUESTS = "Запросы на привязку"
    LEAD_EMPLOYEE_MENU = "Меню сотрудника"
    LEAD_CREATE_TASK = "Создать задачу"
    LEAD_TASK_PROPOSALS = "Предложения"
    LEAD_TASKS_LIST = "Список задач"
    LEAD_REPORTS_LIST = "Список отчетов"
    LEAD_VIEW_REPORT = "Посмотреть отчет"
    LEAD_CONFIRM_REPORT = "Принять"
    LEAD_REJECT_REPORT = "Отклонить отчет"
    LEAD_BACK_TO_REPORTS = "К отчетам"

    START_WORK = "Начать рабочий день"
    FINISH_WORK = "Завершить рабочий день"
    EMPLOYEE_CREATE_TASK = "Предложить задачу"
    EMPLOYEE_TASKS_LIST = "Мои задачи"
    EMPLOYEE_COMPLETE_TASK = "Отправить отчет"
    EMPLOYEE_REPORT_COMMENT = "Комментарий к отчету"
    EMPLOYEE_BIND_MANAGER = "Привязать руководителя"

    INTERN_TASKS_LIST = "Мои задачи"
    INTERN_COMPLETE_TASK = "Отправить отчет"
    INTERN_REPORT_COMMENT = "Комментарий к отчету"
    INTERN_BIND_MANAGER = "Привязать руководителя"

    TASK_ACCEPT = "Принять"
    TASK_FINISH = "Завершить"
    TASK_REPORT = "Отправить отчет"
    


class Callbacks:
    START_AUTH = "start_auth"
    REQUEST_ROLE = "request_role"
    REQUEST_ROLE_SELECT = "request_role_select"
    BACK = "back_to_start"
    AUTH_ROLE = "auth_role"