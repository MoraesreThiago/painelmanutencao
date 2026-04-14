$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $repoRoot "api")

py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
