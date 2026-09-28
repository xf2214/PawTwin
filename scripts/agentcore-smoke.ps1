<#
.SYNOPSIS
    Run ONE real AgentCore Memory round trip and save the evidence, or report NOT EXECUTED.

.DESCRIPTION
    Day-3 condition item. Requires an authorised AWS credential source plus
    AGENTCORE_MEMORY_ID and AWS_REGION in this session, and the optional `memory`
    extra. Without them this script prints NOT EXECUTED and exits 2: it never
    reports a retrieval it did not achieve, and never substitutes a local stand-in
    or presents saved feedback as extracted memory.

    This makes a BILLABLE memory call when it does run. Only run it inside the
    budget and scope the user authorised (see infra/cloud-access-checklist.md).

.EXAMPLE
    ./scripts/agentcore-smoke.ps1
#>
param([switch]$SkipEvidenceFile)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$awsDirectory = Join-Path $HOME '.aws'
$credentialSource = [bool]$env:AWS_PROFILE -or [bool]$env:AWS_ACCESS_KEY_ID -or `
    [bool]$env:AWS_SESSION_TOKEN -or (Test-Path (Join-Path $awsDirectory 'credentials')) -or `
    (Test-Path (Join-Path $awsDirectory 'config'))

if (-not $credentialSource) {
    Write-Host 'NOT EXECUTED: no AWS credential source found.'
    Write-Host 'No memory call was attempted; nothing is claimed as retrieved or cloud-verified.'
    exit 2
}
if (-not $env:AGENTCORE_MEMORY_ID -or -not $env:AWS_REGION) {
    Write-Host 'NOT EXECUTED: AGENTCORE_MEMORY_ID and AWS_REGION must be set in this session.'
    Write-Host 'No memory call was attempted; nothing is claimed as retrieved or cloud-verified.'
    exit 2
}

Push-Location $repoRoot
try {
    $output = & uv run --frozen --extra memory python scripts/agentcore_smoke.py 2>&1
    $code = $LASTEXITCODE
    $output | ForEach-Object { Write-Host $_ }

    if ($code -eq 0 -and -not $SkipEvidenceFile) {
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $target = Join-Path $repoRoot "docs\evidence\agentcore-call-$stamp.md"
        Set-Content -Path $target -Value $output -Encoding utf8
        Write-Host ''
        Write-Host "Evidence written to $target"
        Write-Host 'Review it before committing. The smoke script prints no credential and no'
        Write-Host 'hidden reasoning by design; an empty retrieval is reported honestly.'
    }
    elseif ($code -ne 0) {
        Write-Host ''
        Write-Host "Exit code ${code}: recorded as a real failure, not as a pass."
    }
    exit $code
}
finally {
    Pop-Location
}
