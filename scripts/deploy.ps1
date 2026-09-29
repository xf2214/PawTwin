<#
.SYNOPSIS
    Fail-closed deployment gate for PawTwin. WITHOUT an AWS CLI, WITHOUT IaC
    sources under infra/, or WITHOUT required parameters this script produces
    NO plan, touches NO AWS API, and exits 2 with NOT EXECUTED. -PlanOnly does
    NOT promise plan output; it only means "plan, never apply".

.DESCRIPTION
    Day-4 ruling 9 (docs/plans/PawTwin_Day4_开发计划.md). This is the honest
    form of the T7 deploy entry point while infra/ contains no IaC source:
    the gate checks run in a FIXED order and any failure exits 2:

      1. AWS CLI + CDK CLI presence on PATH
      2. IaC source presence (infra/cdk.json or infra/templates/*.template.json)
      3. Required session inputs: AWS_REGION, and exactly one mode switch
         (-PlanOnly or -Apply). -Apply additionally requires an explicit
         cost-authorization token supplied by the user in this session.

    Account ids are NEVER prefilled; a real deployment would resolve the
    account only at runtime. This script never calls any AWS API and never
    exits 0 unless a later, not-yet-existing implementation path says so.

.OUTPUTS
    NOT EXECUTED: <reason>   + exit 2  on any failed gate
    (PowerShell parameter BINDING errors, e.g. an unknown switch, terminate
     before the script body runs and exit 1, not 2 -- known boundary.)

.EXAMPLE
    ./scripts/deploy.ps1 -PlanOnly
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
    Write-Host 'Nothing is claimed as deployed or deployable.'
    exit $EXIT_NOT_EXECUTED
}

# --- Gate 0: mutually exclusive mode switches, exactly one required. ----------
if ($PlanOnly -and $Apply) {
    Stop-NotExecuted '-PlanOnly and -Apply are mutually exclusive; choose one explicitly.'
}
if (-not $PlanOnly -and -not $Apply) {
    Stop-NotExecuted 'no mode given. Run with -PlanOnly (never applies changes) or -Apply (requires explicit cost authorization).'
}

# --- Gate 1: CLI presence (checked BEFORE anything that could touch AWS). ----
foreach ($cli in @('aws', 'cdk')) {
    if (-not (Get-Command $cli -CommandType Application -ErrorAction SilentlyContinue)) {
        Stop-NotExecuted "$cli CLI is not on PATH. Deployment cannot plan or apply; see infra/cloud-access-checklist.md for prerequisites."
    }
}

# --- Gate 2: IaC source presence. infra/ currently holds only planning docs. --
$cdkProject = Join-Path $repoRoot 'infra\cdk.json'
$cfnTemplates = @(Get-ChildItem -Path (Join-Path $repoRoot 'infra\templates') -Filter '*.template.json' -ErrorAction SilentlyContinue)
$hasIac = (Test-Path $cdkProject) -or ($cfnTemplates.Count -gt 0)
if (-not $hasIac) {
    Stop-NotExecuted 'no IaC source found under infra/ (expected infra/cdk.json or infra/templates/*.template.json). Only planning documents exist; there is nothing to deploy yet.'
}

# --- Gate 3: required session inputs. Never prefilled. ------------------------
if (-not $env:AWS_REGION) {
    Stop-NotExecuted 'AWS_REGION is not set in this session. Region is resolved at runtime only; it is never hardcoded in this repository.'
}

# --- Gate 4: -Apply requires an explicit, user-supplied cost authorization. ---
if ($Apply) {
    if ($CostAuthorization -ne 'I-AUTHORIZE-BILLABLE-DEPLOYMENT') {
        Stop-NotExecuted '-Apply requires the explicit parameter -CostAuthorization I-AUTHORIZE-BILLABLE-DEPLOYMENT confirmed by the account owner for this session.'
    }
    # Even with every gate above satisfied, apply is NOT implemented in Day-4:
    # no IaC has ever been synthesized, reviewed for cost, or user-approved.
    Stop-NotExecuted '-Apply is not implemented: no IaC has been synthesized, cost-reviewed, or user-approved. This gate script intentionally stops before any AWS call.'
}

# --- -PlanOnly past all gates: still not implemented in Day-4. ----------------
Stop-NotExecuted '-PlanOnly reached all gates, but plan generation is not implemented in Day-4 (no CDK synthesis has ever been reviewed). Recording this as a real limitation, not a pass.'
