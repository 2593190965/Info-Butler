# Info-Butler Stop Script (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Info-Butler Stopping Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Stopping backend service..." -ForegroundColor Yellow
Get-Process | Where-Object { $_.MainWindowTitle -like "*Info-Butler-Backend*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Stopping frontend service..." -ForegroundColor Yellow
Get-Process | Where-Object { $_.MainWindowTitle -like "*Info-Butler-Frontend*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "All services stopped" -ForegroundColor Green
Read-Host "Press Enter to exit"
