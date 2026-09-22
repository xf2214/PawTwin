param(
    [switch]$InstallBrowser,
    [string]$NodeDirectory
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
    Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run', 'test:e2e')
}
finally {
    Pop-Location
}
