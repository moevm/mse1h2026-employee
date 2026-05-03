@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo Проверка Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Ошибка: Python не найден.
    exit /b 1
)

if not exist ".env" (
    echo Ошибка: .env не найден.
    exit /b 1
)

echo Настройка .venv...
if not exist ".venv" (
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Установка зависимостей...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

echo Проверка суперпользователя...
python setup\init_superuser.py
if %ERRORLEVEL% NEQ 0 (
    echo Ошибка инициализации.
    exit /b 1
)

echo Установка завершена.
pause
exit /b 0
