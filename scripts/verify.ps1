param([string]$NodeDirectory)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'node-runtime.ps1')
$runtime = Get-PawTwinNodeRuntime -NodeDirectory $NodeDirectory
Push-Location $repoRoot
try {
    & uv run --frozen pytest
    if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed.' }
    & uv run --frozen ruff check .
    if ($LASTEXITCODE -ne 0) { throw 'Python static checks failed.' }
    & uv run --frozen python scripts/export_contracts.py --check
    if ($LASTEXITCODE -ne 0) { throw 'Generated contracts are missing or stale.' }
    Push-Location (Join-Path $repoRoot 'frontend')
    try {
        Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run', 'typecheck')
        Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run', 'build')
    }
    finally { Pop-Location }
}
finally { Pop-Location }
Write-Host 'Baseline checks passed. Browser smoke is separate: scripts/test-e2e.ps1'
