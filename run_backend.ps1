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
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --env-file .env.development
