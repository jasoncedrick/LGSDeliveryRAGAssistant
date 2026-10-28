param(
    [string]$Python = 'D:\thesis\venv\Scripts\python.exe',
    [int]$Port = 8000
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw 'Python was not found. Pass -Python with the path to the project environment.'
}
Set-Location -LiteralPath $projectRoot
Write-Host "Citizen website: http://127.0.0.1:$Port"
Write-Host 'Keep this terminal open. Press Ctrl+C to stop. Ollama must be running separately.'
& $Python -m uvicorn app.website:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
