$port = 8000
Write-Host "Checking port $port..." -ForegroundColor Cyan

$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($process) {
    $pid_id = $process.OwningProcess
    Write-Host "Found existing backend process (PID: $pid_id). Killing it..." -ForegroundColor Yellow
    Stop-Process -Id $pid_id -Force -ErrorAction SilentlyContinue
    Write-Host "Process killed." -ForegroundColor Green
} else {
    Write-Host "Port $port is free." -ForegroundColor Green
}

Write-Host "Starting Backend Service..." -ForegroundColor Cyan
# Enable reload for development
python backend/main.py
