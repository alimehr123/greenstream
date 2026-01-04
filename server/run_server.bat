@echo off
setlocal

REM ==========================================================
REM GreenStream FastAPI Server Starter (AUTO LAN IP via PY)
REM ==========================================================

cd /d E:\Projects\GreenStream

REM ----------------------------------
REM DEBUG: Check YOUTUBE_API_KEY
REM ----------------------------------
echo ==========================================
echo DEBUG: Checking YOUTUBE_API_KEY
echo YOUTUBE_API_KEY=%YOUTUBE_API_KEY%
echo ==========================================

IF "%YOUTUBE_API_KEY%"=="" (
    echo.
    echo ERROR: YOUTUBE_API_KEY is NOT set!
    echo Please run this in PowerShell:
    echo.
    echo   setx YOUTUBE_API_KEY "AIzaSyXXXXXXXXXXXXXXXX"
    echo.
    echo Then CLOSE all terminals and run again.
    echo.
    pause
    exit /b 1
)

REM ----------------------------------
REM Create venv if it does not exist
REM ----------------------------------
IF NOT EXIST venv (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM ----------------------------------
REM Activate venv
REM ----------------------------------
call venv\Scripts\activate

REM ----------------------------------
REM Install backend dependencies
REM ----------------------------------
IF EXIST server\requirements.txt (
    echo Installing backend dependencies...
    pip install --quiet -r server\requirements.txt
) ELSE (
    pip install --quiet fastapi uvicorn
)

REM ----------------------------------
REM Detect LAN IP via Python
REM ----------------------------------
set LAN_IP=127.0.0.1

for /f %%A in ('
    python -c "from server.utils.network_info import get_lan_ip; print(get_lan_ip())"
') do (
    set LAN_IP=%%A
)

REM ----------------------------------
REM Start FastAPI Server
REM ----------------------------------
echo.
echo Server starting...
echo Local: http://127.0.0.1:8000
echo LAN:   http://%LAN_IP%:8000
echo.

python -m uvicorn server.main:app --host 0.0.0.0 --port 8000

pause
