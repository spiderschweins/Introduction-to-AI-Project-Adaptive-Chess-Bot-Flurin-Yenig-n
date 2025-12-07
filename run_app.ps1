Param(
    [string]$ApiHost = "127.0.0.1",
    [int]$ApiPort = 8000
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptRoot

Write-Host "=========================================="
Write-Host "Lean Chess Launcher"
Write-Host "=========================================="

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python was not found. Install Python 3.10+ and rerun this script."
    exit 1
}

$env:CHESSBOT_API_URL = "http://${ApiHost}:${ApiPort}"
$escapedRoot = $scriptRoot.Replace('"','`"')
$backendCmd = "cd `"$escapedRoot`"; python -m uvicorn src.api:app --host $ApiHost --port $ApiPort"
$frontendCmd = "cd `"$escapedRoot`"; streamlit run src/app.py"

Write-Host "Starting FastAPI backend window..."
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -PassThru
Start-Sleep -Seconds 3

Write-Host "Starting Streamlit frontend window..."
$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -PassThru

Write-Host "Backend PID: $($backendProcess.Id)"
Write-Host "Frontend PID: $($frontendProcess.Id)"
Write-Host "Keep both windows open while you play. Close them to stop the app."
