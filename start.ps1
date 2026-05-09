# Info-Butler Startup Script (PowerShell)
# Run this script from project root directory

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Info-Butler Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if in project root
if (-not (Test-Path "backend\main.py")) {
    Write-Host "[Error] Please run this script in project root directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Get current directory
$ROOT_DIR = $PSScriptRoot
if (-not $ROOT_DIR) {
    $ROOT_DIR = Get-Location
}

# Start backend
Write-Host "[1/2] Starting backend..." -ForegroundColor Yellow
$backendScript = "cd '$ROOT_DIR'; uv run uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript -WindowTitle "Info-Butler-Backend"

# Wait for backend to start
Start-Sleep -Seconds 3

# Start frontend
Write-Host "[2/2] Starting frontend..." -ForegroundColor Yellow
$frontendScript = "cd '$ROOT_DIR\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript -WindowTitle "Info-Butler-Frontend"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Backend:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8001" -ForegroundColor Cyan
Write-Host "  Frontend: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5175" -ForegroundColor Cyan
Write-Host "  API Docs: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to close this window..." -ForegroundColor Gray
Write-Host "(Services will continue running)" -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
