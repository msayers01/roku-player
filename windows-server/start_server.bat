@echo off
rem Roku LAN Media server - double-click to start, Ctrl+C to stop.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo First run: creating Python environment in .venv ...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    if errorlevel 1 (
        echo Python 3.10+ is required. Install it from https://www.python.org/downloads/windows/
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo Failed to install requirements.
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m app --config config.json
pause
