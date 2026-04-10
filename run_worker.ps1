$workerPattern = 'python .*backend\\.worker|py .*backend\\.worker'
$existing = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match $workerPattern }

if ($existing) {
    foreach ($process in $existing) {
        Write-Host "Stopping existing worker process (PID: $($process.ProcessId))..." -ForegroundColor Yellow
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Starting Worker Service..." -ForegroundColor Cyan
python -m backend.worker
