<#
.SYNOPSIS
    Deployment entry point for PawTwin. Delegates to the boto3 orchestrator
    scripts/deploy_aws.py (Day-5 ruling 1: NO CDK/CloudFormation). -PlanOnly is
    OFFLINE and produces a real plan with NO AWS call; -Apply is REAL and BILLABLE
    and is gated on an explicit cost authorization plus a credential source.

.DESCRIPTION
    Day-5 ruling 1 / 17 supersede the Day-4 form. The gates run in a FIXED order and
    any failure prints NOT EXECUTED and exits 2 without touching AWS:

      0. exactly one mode switch (-PlanOnly or -Apply)
      1. `uv` is available to run the orchestrator (the Day-4 `cdk` probe is gone:
         orchestration is boto3, the CLI is only for human diagnosis)
      2. infra/deploy_plan.json exists and parses (the Day-4 `cdk.json`/`templates`
         judgement is replaced by the declarative plan source)
      3. -Apply only: AWS_REGION set, a credential source present, and the explicit
         -CostAuthorization token (the user's written budget approval, AGENTS.md L69)

    -PlanOnly reaches the orchestrator's offline plan and exits with its code (0 on a
    well-formed plan). It NEVER creates a resource. -Apply hands off to the real
    orchestrator; if boto3, credentials or a placeholder are missing the orchestrator
    fails honestly and this script propagates a non-zero exit -- it never fakes success.

.EXAMPLE
    ./scripts/deploy.ps1 -PlanOnly
    ./scripts/deploy.ps1 -Apply -CostAuthorization I-AUTHORIZE-BILLABLE-DEPLOYMENT
#>
[CmdletBinding()]
param(
    [switch]$PlanOnly,
    [switch]$Apply,
    [string]$CostAuthorization
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$EXIT_NOT_EXECUTED = 2

function Stop-NotExecuted {
    param([string]$Reason)
    Write-Host "NOT EXECUTED: $Reason"
    Write-Host 'No AWS API was called. No resource was created or changed. No cost was incurred.'
    exit $EXIT_NOT_EXECUTED
}

# --- Gate 0: mutually exclusive mode switches, exactly one required. ----------
if ($PlanOnly -and $Apply) {
    Stop-NotExecuted '-PlanOnly and -Apply are mutually exclusive; choose one explicitly.'
}
if (-not $PlanOnly -and -not $Apply) {
    Stop-NotExecuted 'no mode given. Run with -PlanOnly (offline, never applies) or -Apply (real, requires cost authorization).'
}

# --- Gate 1: the orchestrator runtime (uv) is available. ----------------------
if (-not (Get-Command uv -CommandType Application -ErrorAction SilentlyContinue)) {
    Stop-NotExecuted 'uv is not on PATH; the boto3 orchestrator (scripts/deploy_aws.py) cannot run.'
}

# --- Gate 2: declarative plan source exists and parses. -----------------------
$planPath = Join-Path $repoRoot 'infra\deploy_plan.json'
if (-not (Test-Path $planPath)) {
    Stop-NotExecuted 'no infra/deploy_plan.json. There is nothing to plan or apply.'
}
try { Get-Content $planPath -Raw | ConvertFrom-Json | Out-Null }
catch { Stop-NotExecuted "infra/deploy_plan.json is not valid JSON: $($_.Exception.Message)" }

$orchestrator = Join-Path $repoRoot 'scripts\deploy_aws.py'

# --- -PlanOnly: offline plan, no AWS call. ------------------------------------
if ($PlanOnly) {
    Write-Host 'plan: running the offline orchestrator plan (no AWS request will be sent).'
    Push-Location $repoRoot
    try { uv run --frozen python $orchestrator --plan; $code = $LASTEXITCODE }
    finally { Pop-Location }
    exit $code
}

# --- Gate 3 (-Apply only): region, credentials, explicit cost authorization. --
if (-not $env:AWS_REGION) {
    Stop-NotExecuted 'AWS_REGION is not set in this session. Region is resolved at runtime only; never hardcoded.'
}
$hasCreds = $env:AWS_ACCESS_KEY_ID -or $env:AWS_PROFILE -or $env:AWS_SESSION_TOKEN -or
    (Test-Path (Join-Path $HOME '.aws\credentials'))
if (-not $hasCreds) {
    Stop-NotExecuted 'no AWS credential source found. Inject SHORT-LIVED credentials for this session; none are ever stored in the repo.'
}
if ($CostAuthorization -ne 'I-AUTHORIZE-BILLABLE-DEPLOYMENT') {
    Stop-NotExecuted '-Apply requires -CostAuthorization I-AUTHORIZE-BILLABLE-DEPLOYMENT, confirming the user''s written budget approval for this session.'
}

Write-Host 'apply: REAL and BILLABLE. Handing off to the boto3 orchestrator.'
Push-Location $repoRoot
try {
    uv run --frozen --extra bedrock --extra memory python $orchestrator --apply --cost-authorization $CostAuthorization
    $code = $LASTEXITCODE
}
finally { Pop-Location }
exit $code
