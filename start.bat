@echo off
python --version > nul 2> nul
echo Starting...



if %errorlevel% neq 0 (
    echo Python is not installed
    exit /b
)

set "VENV_NAME=venv"
set "VENV_PATH=%CD%\%VENV_NAME%"
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo Creating a virtual environment...
    python -m venv "%VENV_PATH%"
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment
        exit /b
    )
)


call %VENV_NAME%\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment
)

echo Installing dependencies
pip install --upgrade pip

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies
)

cd ./dashboard
start cmd /k "py manage.py runserver"
cd ..

cd /d %~dp0bot
py main.py

deactivate
echo virtual environment is deactivated
pause