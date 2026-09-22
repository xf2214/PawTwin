param(
    [int]$Port = 5173,
    [string]$NodeDirectory
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'node-runtime.ps1')
$runtime = Get-PawTwinNodeRuntime -NodeDirectory $NodeDirectory

Push-Location (Join-Path $repoRoot 'frontend')
try {
    Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @(
        'run', 'dev', '--', '--host', '127.0.0.1', '--port', "$Port", '--strictPort'
    )
}
finally {
    Pop-Location
}
