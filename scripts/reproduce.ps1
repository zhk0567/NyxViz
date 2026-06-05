# NyxViz one-click reproduction (Windows PowerShell)
# Run from repository root: powershell -File scripts/reproduce.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "[NyxViz] Reproduce pipeline starting..." -ForegroundColor Cyan

if (-not (Test-Path ".\Nyx\0000.dat")) {
    Write-Error "Missing Nyx/0000.dat — place competition data under Nyx/ first."
}

npm install
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

npm run precompute
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

npm run figures
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

npm run export-docx
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

npm run submission-pack
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[NyxViz] Done. Open demo: python run.py" -ForegroundColor Green
Write-Host "  Docx: docs/submission/NyxViz_作品说明文档.docx" -ForegroundColor Green
Write-Host "  Optional vtk captures: npm run build; `$env:CAPTURE_SCALE=2; npm run capture-volumes" -ForegroundColor Yellow
