@echo off
chcp 65001 >nul
echo ====================================
echo   Info-Butler 一键启动
echo ====================================
echo.

:: 检查是否在项目根目录
if not exist "backend\main.py" (
    echo [错误] 请在项目根目录运行此脚本
    pause
    exit /b 1
)

:: 启动后端
echo [1/2] 启动后端服务...
start "Info-Butler Backend" cmd /k "uv run uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端
echo [2/2] 启动前端服务...
cd frontend
start "Info-Butler Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ====================================
echo   启动完成！
echo ====================================
echo   后端地址: http://localhost:8001
echo   前端地址: http://localhost:5175
echo   API文档:  http://localhost:8001/docs
echo ====================================
echo.
echo 按任意键退出此窗口（前后端会继续运行）
pause >nul
