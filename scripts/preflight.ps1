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

# Bedrock readiness. Everything below is READ-ONLY: no AWS call is made, and the
# presence of a variable or a credential file never implies connectivity.
Write-Host ''
Write-Host 'Bedrock readiness (read-only):'
$backend = if ($env:PAWTWIN_MODEL_BACKEND) { $env:PAWTWIN_MODEL_BACKEND } else { 'unset -> local_fake in local mode' }
Write-Host "  PAWTWIN_MODEL_BACKEND: $backend"
Write-Host "  BEDROCK_MODEL_ID set: $([bool]$env:BEDROCK_MODEL_ID)"
Write-Host "  AWS_REGION set: $([bool]$env:AWS_REGION)"
$strandsInstalled = & uv run --frozen --no-sync python -c "import importlib.util; print(bool(importlib.util.find_spec('strands')))"
Write-Host "  'bedrock' extra installed: $strandsInstalled"
$awsDirectory = Join-Path $HOME '.aws'
$credentialSource = [bool]$env:AWS_PROFILE -or [bool]$env:AWS_ACCESS_KEY_ID -or `
    [bool]$env:AWS_SESSION_TOKEN -or (Test-Path (Join-Path $awsDirectory 'credentials')) -or `
    (Test-Path (Join-Path $awsDirectory 'config'))
Write-Host "  credential source present: $credentialSource"
if (-not $credentialSource) {
    Write-Host '  NOT EXECUTED: no credential source, so no model call is attempted and'
    Write-Host '  nothing is reported as cloud-verified. Run scripts/bedrock-smoke.ps1 once'
    Write-Host '  an account is authorised.'
}

# AgentCore Memory readiness. Also READ-ONLY: no AWS call is made, and neither the
# variable nor a credential file implies connectivity or that any memory was
# retrieved. A locally 'saved' feedback item is never reported as extracted.
Write-Host ''
Write-Host 'AgentCore Memory readiness (read-only):'
$memoryBackend = if ($env:PAWTWIN_MEMORY_BACKEND) { $env:PAWTWIN_MEMORY_BACKEND } else { 'unset -> not_implemented in local mode' }
Write-Host "  PAWTWIN_MEMORY_BACKEND: $memoryBackend"
Write-Host "  AGENTCORE_MEMORY_ID set: $([bool]$env:AGENTCORE_MEMORY_ID)"
$boto3Installed = & uv run --frozen --no-sync python -c "import importlib.util; print(bool(importlib.util.find_spec('boto3')))"
Write-Host "  'memory' extra (boto3) installed: $boto3Installed"
if (-not $credentialSource) {
    Write-Host '  NOT EXECUTED: no credential source, so no memory call is attempted and'
    Write-Host '  nothing is reported as retrieved. Run scripts/agentcore-smoke.ps1 once an'
    Write-Host '  account is authorised.'
}

Write-Host ''
Write-Host 'Local runtime preflight passed. No AWS call was made and no connectivity is implied; the Docker engine was not exercised.'
