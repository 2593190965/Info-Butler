@echo off
chcp 65001 >nul 2>&1
cls

echo ====================================
echo   Info-Butler Starting...
echo ====================================
echo.

:: Check if in project root
if not exist "backend\main.py" (
    echo [Error] Please run this script in project root directory
    pause
    exit /b 1
)

:: Get current directory
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: Start backend
echo [1/2] Starting backend...
start "Info-Butler-Backend" cmd /k "cd /d %ROOT_DIR% && uv run uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload"

:: Wait for backend to start
timeout /t 3 /nobreak >nul 2>&1

:: Start frontend
echo [2/2] Starting frontend...
cd /d "%ROOT_DIR%frontend"
start "Info-Butler-Frontend" cmd /k "cd /d %ROOT_DIR%frontend && npm run dev"

:: Back to root
cd /d "%ROOT_DIR%"

echo.
echo ====================================
echo   Services Started!
echo ====================================
echo   Backend:  http://localhost:8001
echo   Frontend: http://localhost:5175
echo   API Docs: http://localhost:8001/docs
echo ====================================
echo.
echo Press any key to close this window
echo (Services will continue running)
pause >nul
