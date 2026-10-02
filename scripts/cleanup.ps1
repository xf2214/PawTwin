<#
.SYNOPSIS
    Cleanup entry point for PawTwin. Delegates to the boto3 orchestrator
    scripts/cleanup_aws.py (Day-5 ruling 1). Default is an OFFLINE dry-run listing
    from the recorded deploy state; -Destroy is REAL and gated on an explicit cost
    authorization. Resource ids are NEVER guessed -- they come only from
    infra/deploy_state.json written by a prior deploy.

.DESCRIPTION
    Gates run in a FIXED order; any failure prints NOT EXECUTED and exits 2 without
    touching AWS:

      1. `uv` is available to run the orchestrator
      2. infra/deploy_plan.json exists (it carries the reverse-dependency delete order)
      3. infra/deploy_state.json exists (a prior deploy's real inventory). With no
         state file nothing was ever deployed from this checkout, so there is nothing
         to list or destroy -- this is reported, not faked.
      4. -Destroy only: the explicit -CostAuthorization token

    The dry-run listing and the destroy both run in the orchestrator, which deletes in
    reverse dependency order and reads each resource back to confirm absence.

.EXAMPLE
    ./scripts/cleanup.ps1
    ./scripts/cleanup.ps1 -Destroy -CostAuthorization I-AUTHORIZE-BILLABLE-READ
#>
[CmdletBinding()]
param(
    [switch]$Destroy,
    [string]$CostAuthorization
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$EXIT_NOT_EXECUTED = 2

function Stop-NotExecuted {
    param([string]$Reason)
    Write-Host "NOT EXECUTED: $Reason"
    Write-Host 'No AWS API was called. No resource was listed, changed, or deleted. No cost was incurred.'
    exit $EXIT_NOT_EXECUTED
}

# --- Gate 1: the orchestrator runtime (uv) is available. ----------------------
if (-not (Get-Command uv -CommandType Application -ErrorAction SilentlyContinue)) {
    Stop-NotExecuted 'uv is not on PATH; the boto3 orchestrator (scripts/cleanup_aws.py) cannot run.'
}

# --- Gate 2: the plan carries the delete order. -------------------------------
if (-not (Test-Path (Join-Path $repoRoot 'infra\deploy_plan.json'))) {
    Stop-NotExecuted 'no infra/deploy_plan.json; the reverse-dependency delete order is undefined.'
}

# --- Gate 3: a recorded inventory from a prior deploy. ------------------------
if (-not (Test-Path (Join-Path $repoRoot 'infra\deploy_state.json'))) {
    Stop-NotExecuted 'no infra/deploy_state.json. Nothing has been deployed from this checkout, so there is nothing to list or destroy (ids are never guessed).'
}

$orchestrator = Join-Path $repoRoot 'scripts\cleanup_aws.py'

# --- Default: offline dry-run listing from the recorded state. ----------------
if (-not $Destroy) {
    Write-Host 'cleanup: dry-run listing (no AWS request will be sent).'
    Push-Location $repoRoot
    try { uv run --frozen python $orchestrator --dry-run; $code = $LASTEXITCODE }
    finally { Pop-Location }
    exit $code
}

# --- Gate 4 (-Destroy only): explicit cost authorization. ---------------------
if ($CostAuthorization -ne 'I-AUTHORIZE-BILLABLE-READ') {
    Stop-NotExecuted '-Destroy requires -CostAuthorization I-AUTHORIZE-BILLABLE-READ (listing/deleting billable resources is an account operation).'
}

Write-Host 'destroy: REAL deletion in reverse dependency order, with read-back verification.'
Push-Location $repoRoot
try {
    uv run --frozen python $orchestrator --destroy --cost-authorization $CostAuthorization
    $code = $LASTEXITCODE
}
finally { Pop-Location }
exit $code
