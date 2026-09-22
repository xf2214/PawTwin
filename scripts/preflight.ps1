param([string]$NodeDirectory)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'node-runtime.ps1')
foreach ($required in @('git', 'uv')) {
    if (-not (Get-Command $required -CommandType Application -ErrorAction SilentlyContinue)) {
        throw "$required is required. Install it before running setup."
    }
}
$runtime = Get-PawTwinNodeRuntime -NodeDirectory $NodeDirectory
Write-Host "Node $($runtime.NodeVersion); npm $($runtime.NpmVersion)"
& uv --version
if ($LASTEXITCODE -ne 0) { throw 'uv version check failed.' }
foreach ($optional in @('docker', 'aws')) {
    $available = [bool](Get-Command $optional -CommandType Application -ErrorAction SilentlyContinue)
    Write-Host "$optional available on PATH: $available (optional for local development)"
}
Write-Host 'Local runtime preflight passed. AWS connectivity and Docker engine are not checked.'
