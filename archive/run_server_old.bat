@echo off
REM ==========================================================
REM GreenStream FastAPI Server Starter (LAN + Local)
REM Project structure: Server runs on Lenovo, Frontend elsewhere
REM Mohammad Mehravaran
REM ==========================================================

:: Go to server directory
cd /d E:\Projects\GreenStream\server

:: Create venv if it does not exist
IF NOT EXIST ..\venv (
    echo 🔹 Creating Python virtual environment...
    python -m venv ..\venv
)

:: Activate venv
call ..\venv\Scripts\activate

:: Install dependencies from server/requirements.txt
IF EXIST requirements.txt (
    echo 🔹 Installing dependencies from requirements.txt...
    pip install --quiet -r requirements.txt
) ELSE (
    echo ⚠️ No requirements.txt found in server directory!
    echo Installing core packages: fastapi, uvicorn
    pip install --quiet fastapi uvicorn
)

:: Ensure ui_web folder exists
IF NOT EXIST ui_web (
    mkdir ui_web
)
IF NOT EXIST ui_web\assets (
    mkdir ui_web\assets
    echo placeholder > ui_web\assets\placeholder.txt
)

:: Show access URLs
echo.
echo ✅ Local access:  http://127.0.0.1:8000
echo ✅ LAN access:    http://192.168.50.100:8000
echo.

:: Start FastAPI backend
python main.py

:: Keep window open after server stops
echo.
pause
