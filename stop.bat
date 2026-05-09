@echo off
chcp 65001 >nul 2>&1
cls

echo ====================================
echo   Info-Butler Stopping Services
echo ====================================
echo.

echo Stopping backend service...
taskkill /FI "WINDOWTITLE eq Info-Butler-Backend*" /F >nul 2>&1

echo Stopping frontend service...
taskkill /FI "WINDOWTITLE eq Info-Butler-Frontend*" /F >nul 2>&1

echo.
echo All services stopped
pause
