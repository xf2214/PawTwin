param(
    [switch]$InstallBrowser,
    [string]$NodeDirectory,
    [ValidateRange(1, 64)][int]$ShardCount = 4
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'node-runtime.ps1')
$runtime = Get-PawTwinNodeRuntime -NodeDirectory $NodeDirectory
$frontendRoot = Join-Path $repoRoot 'frontend'

Push-Location $frontendRoot
try {
    if ($InstallBrowser) {
        $playwrightCli = Join-Path $frontendRoot 'node_modules\@playwright\test\cli.js'
        & $runtime.NodeExe $playwrightCli install chromium
        if ($LASTEXITCODE -ne 0) {
            throw "Playwright browser install failed with exit code $LASTEXITCODE"
        }
    }
    Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run', 'build')
    # Each invocation creates a fresh isolated server. A single full-suite server
    # exceeds the real registration rate limit; do not weaken production policy.
    for ($shard = 1; $shard -le $ShardCount; $shard++) {
        Write-Host "Browser shard $shard/$ShardCount"
        Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @(
            'run', 'test:e2e', '--', "--shard=$shard/$ShardCount",
            "--output=test-results/shard-$shard"
        )
    }
}
finally {
    Pop-Location
}
