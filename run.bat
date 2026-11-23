@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    ".venv\Scripts\pythonw.exe" src\main.py
) else (
    pythonw src\main.py 2>nul || python src\main.py
)
endlocal