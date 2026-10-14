param([int]$Port = 8000, [string]$DatabasePath)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $DatabasePath) { $DatabasePath = Join-Path $repoRoot 'data\pet-home.db' }
$DatabasePath = [IO.Path]::GetFullPath($DatabasePath)
New-Item -ItemType Directory -Path (Split-Path -Parent $DatabasePath) -Force | Out-Null
$localValues = @{
    PAWTWIN_MODE = 'local'
    PAWTWIN_MODEL_BACKEND = 'local_fake'
    PAWTWIN_MEMORY_BACKEND = 'not_implemented'
    PAWTWIN_WORKER_MODE = 'background'
    PAWTWIN_DB_PATH = $DatabasePath
    PAWTWIN_PHOTO_RECOGNITION_ENABLED = 'false'
    PAWTWIN_FAMILY_MODEL_BACKEND = 'local_rules'
}
$previousValues = @{}
foreach ($key in $localValues.Keys) {
    $previousValues[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
    [Environment]::SetEnvironmentVariable($key, $localValues[$key], 'Process')
}
Push-Location $repoRoot
try {
    uv run --frozen uvicorn pawtwin.main:create_app --factory --host 127.0.0.1 --port $Port --no-proxy-headers
    if ($LASTEXITCODE -ne 0) { throw "Pet home exited with code $LASTEXITCODE" }
}
finally {
    Pop-Location
    foreach ($key in $previousValues.Keys) {
        [Environment]::SetEnvironmentVariable($key, $previousValues[$key], 'Process')
    }
}
