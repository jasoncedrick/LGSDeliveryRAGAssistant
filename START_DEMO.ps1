param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& "$PSScriptRoot\CHECK_DEMO.ps1" -Port $Port
if ($LASTEXITCODE -ne 0) { throw 'Preflight failed. Read the message above before starting.' }
$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    Write-Host "Port $Port is already in use. No second server was started."
    Write-Host "Check http://127.0.0.1:$Port/health and the terminal that owns this server."
    return
}
Write-Host "Open http://127.0.0.1:$Port once the assistant reports ready."
Write-Host 'Keep this terminal open. One answer runs at a time; Ctrl+C stops this server.'
& 'D:\thesis\venv\Scripts\python.exe' -m uvicorn app.website:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
