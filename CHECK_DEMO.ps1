param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& 'D:\thesis\venv\Scripts\python.exe' scripts/check_adviser_demo.py --port $Port
exit $LASTEXITCODE
