@echo off
echo ========================================
echo VideoExpress AI - Starting Application
echo ========================================
echo.

cd /d "%~dp0"

REM Start Backend
echo [1/2] Starting Backend...
start "VideoExpress Backend" cmd /k "cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

REM Start Frontend
echo [2/2] Starting Frontend...
start "VideoExpress Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo Application Started!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to open browser...
pause >nul

start http://localhost:5173

echo.
echo To stop: Close both terminal windows
echo.
