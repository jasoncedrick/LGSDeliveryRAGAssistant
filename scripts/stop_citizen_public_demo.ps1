$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $projectRoot 'tmp\citizen-website\tunnel.pid'
$expectedExecutable = Join-Path $projectRoot 'tmp\citizen-website\cloudflared.exe'
if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host 'No recorded demo tunnel.'
    exit 0
}
$tunnelProcessId = [int](Get-Content -LiteralPath $pidFile -Raw).Trim()
$tunnelProcess = Get-Process -Id $tunnelProcessId -ErrorAction SilentlyContinue
if ($null -eq $tunnelProcess) {
    Write-Host 'The recorded tunnel has already stopped.'
    exit 0
}
if ($tunnelProcess.Path -ne $expectedExecutable) {
    throw 'The recorded process ID belongs to a different program. No process was stopped.'
}
Stop-Process -Id $tunnelProcessId
Write-Host 'Public demo stopped. The local website and Ollama were left running.'
