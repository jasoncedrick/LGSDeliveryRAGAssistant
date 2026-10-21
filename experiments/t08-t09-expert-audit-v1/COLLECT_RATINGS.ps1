$ErrorActionPreference = 'Stop'
$auditProject = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$auditReceived = Join-Path $PSScriptRoot 'received-ratings'
$auditDestination = Join-Path $auditReceived 'validated-v1'
& 'D:\thesis\venv\Scripts\python.exe' (Join-Path $auditProject 'scripts/collect_expert_ratings.py') `
    (Join-Path $auditReceived 'R01-final.json') `
    (Join-Path $auditReceived 'R02-final.json') `
    (Join-Path $auditReceived 'R03-final.json') `
    --out $auditDestination
if ($LASTEXITCODE -ne 0) { throw 'Rating validation failed. Original exports were preserved.' }
