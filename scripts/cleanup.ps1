<#
.SYNOPSIS
    Fail-closed cleanup gate for PawTwin. Default is dry-run LISTING only.
    WITHOUT an AWS CLI, WITHOUT IaC sources, or WITHOUT a recorded project
    resource inventory this script lists NOTHING from AWS, destroys NOTHING,
    and exits 2 with NOT EXECUTED.

.DESCRIPTION
    Day-4 ruling 9 (docs/plans/PawTwin_Day4_开发计划.md), companion to
    scripts/deploy.ps1. Honest form of T7 cleanup while nothing has ever been
    deployed from this repository:

      1. Mode switch: default is dry-run (list-only). -Destroy is required to
         even express destroy intent, and -Destroy additionally requires an
         explicit cost/state authorization token.
      2. AWS CLI + CDK CLI presence on PATH.
      3. IaC source presence under infra/ (currently only planning docs).
      4. A project resource inventory produced by a previous deploy (none
         exists; deployments have never run).

    Deletion order for a future real implementation is documented in
    infra/cloud-access-checklist.md (service -> load balancer -> image repo ->
    logs -> memory -> table, each verified gone). This script NEVER calls any
    AWS API and NEVER exits 0 while those prerequisites are missing.

.EXAMPLE
    ./scripts/cleanup.ps1
#>
[CmdletBinding()]
param(
    [switch]$Destroy,
    [string]$ConfirmProjectId,
    [string]$CostAuthorization
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$EXIT_NOT_EXECUTED = 2

function Stop-NotExecuted {
    param([string]$Reason)
    Write-Host "NOT EXECUTED: $Reason"
    Write-Host 'No AWS API was called. No resource was listed, changed, or deleted. No cost was incurred.'
    Write-Host 'Nothing is claimed as cleaned up.'
    exit $EXIT_NOT_EXECUTED
}

Write-Host 'cleanup.ps1 default mode is dry-run listing; destroy intent requires -Destroy plus explicit authorization.'

# --- Gate 1: CLIs. -------------------------------------------------------------
foreach ($cli in @('aws', 'cdk')) {
    if (-not (Get-Command $cli -CommandType Application -ErrorAction SilentlyContinue)) {
        Stop-NotExecuted "$cli CLI is not on PATH. Nothing can be listed or destroyed; a dry run would still need to query the account."
    }
}

# --- Gate 2: IaC source. -------------------------------------------------------
$cdkProject = Join-Path $repoRoot 'infra\cdk.json'
$cfnTemplates = @(Get-ChildItem -Path (Join-Path $repoRoot 'infra\templates') -Filter '*.template.json' -ErrorAction SilentlyContinue)
$hasIac = (Test-Path $cdkProject) -or ($cfnTemplates.Count -gt 0)
if (-not $hasIac) {
    Stop-NotExecuted 'no IaC source found under infra/. Nothing has ever been deployed from this repository, so there is no managed stack to list or destroy.'
}

# --- Gate 3: resource inventory (a prior deploy record). -----------------------
if (-not $ConfirmProjectId) {
    Stop-NotExecuted 'no -ConfirmProjectId given. Cleanup must operate on an exact project resource inventory recorded by a prior deploy; inventing or guessing resource ids is forbidden.'
}

# --- Gate 4: destroy intent requires explicit authorization. -------------------
if ($Destroy) {
    if ($CostAuthorization -ne 'I-AUTHORIZE-BILLABLE-READ') {
        Stop-NotExecuted '-Destroy requires -CostAuthorization I-AUTHORIZE-BILLABLE-READ (listing billable resources is itself an account read) confirmed by the account owner.'
    }
    # Even with every gate satisfied, destroy is NOT implemented in Day-4.
    Stop-NotExecuted '-Destroy is not implemented: no deployment has ever run from this repository, so there is nothing to destroy. Refusing to fake a cleanup success.'
}

Stop-NotExecuted 'dry-run listing is not implemented in Day-4 (no deploy record exists to list against). Recorded as a real limitation, not a pass.'
