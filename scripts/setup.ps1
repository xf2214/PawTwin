param([string]$NodeDirectory)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'node-runtime.ps1')

Push-Location $repoRoot
try {
    uv sync --frozen
    if ($LASTEXITCODE -ne 0) {
        throw "uv sync failed with exit code $LASTEXITCODE"
    }

    $runtime = Get-PawTwinNodeRuntime -NodeDirectory $NodeDirectory
    Push-Location (Join-Path $repoRoot 'frontend')
    try {
        Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('ci')
    }
    finally {
        Pop-Location
    }
}
finally {
    Pop-Location
}
