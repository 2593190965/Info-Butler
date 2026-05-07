@echo off
chcp 65001 >nul
echo ====================================
echo   Info-Butler 停止服务
echo ====================================
echo.

echo 正在停止后端服务...
taskkill /FI "WINDOWTITLE eq Info-Butler Backend*" /F >nul 2>&1

echo 正在停止前端服务...
taskkill /FI "WINDOWTITLE eq Info-Butler Frontend*" /F >nul 2>&1

echo.
echo 所有服务已停止
pause
