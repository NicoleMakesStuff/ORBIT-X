$ProjectRoot = Split-Path -Parent $PSScriptRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

$Script = Join-Path $ProjectRoot "ai\orbit\ingest_satellites.py"

Write-Host "=============================================="
Write-Host "ORBIT-X AUTOMATED TLE INGESTION"
Write-Host "=============================================="

Write-Host "Project root:"
Write-Host $ProjectRoot

Write-Host ""
Write-Host "Python:"
Write-Host $Python

Write-Host ""
Write-Host "Ingestion script:"
Write-Host $Script

Write-Host ""
Write-Host "Starting ingestion..."
Write-Host ""

& $Python $Script

$ExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "=============================================="

if ($ExitCode -eq 0) {
    Write-Host "INGESTION COMPLETED SUCCESSFULLY"
}
else {
    Write-Host "INGESTION FAILED"
}

Write-Host "Exit code: $ExitCode"

Write-Host "=============================================="

exit $ExitCode