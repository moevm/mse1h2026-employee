# Init bot menu

## Описание
В рамках задания реализованы макеты:
1. приветственное меню бота(`welcome_menu`)
2. меню сотрудника(`employee_menu`)
3. меню руководителя(`lead_menu`)
4. переход между меню(`role_switcher`)

**Зависимости** Необходимо убедится, что все зависимости из файла `requirements.txt` были установлены, добавить недостающие в случае отсутствия. При необходимости воспользоваться виртуальным окружением:
```bash
python -m env myenv
```
```bash
source myenv/bin/activate
```
```bash
pip install -r requirements.txt
```
**Интеграция:** Необходимо импортировать файлы `welcome_menu.py`, `employee_menu.py`, `lead_menu.py` и `role_switcher.py`.
Вместо обработчика команды старт вызвать функции `register_welcome_menu(dp)`, `register_employee_menu(dp)`, `register_role_switcher(dp)` и `register_lead_menu(dp)`