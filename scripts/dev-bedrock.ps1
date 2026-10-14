param(
    [int]$Port = 8807,
    [string]$DatabasePath,
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]*$')][string]$LoginProfile = 'pawtwin',
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]*$')][string]$SdkProfile = 'pawtwin-sdk',
    [switch]$EnablePhotoRecognition,
    [switch]$ProbeOnly
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$awsCommand = Get-Command aws -CommandType Application -ErrorAction SilentlyContinue
$awsExecutable = if ($awsCommand) { $awsCommand.Source } else { 'C:\Program Files\Amazon\AWSCLIV2\aws.exe' }
if (-not (Test-Path -LiteralPath $awsExecutable)) {
    throw 'AWS CLI v2 is required. Install the official MSI, then run aws login --profile pawtwin --region us-east-1. Never send credential values in chat.'
}
$awsVersion = & $awsExecutable --version
if ($awsVersion -notmatch 'aws-cli/2\.') { throw 'AWS CLI v2 is required for temporary console login.' }
$loginSession = & $awsExecutable configure get login_session --profile $LoginProfile 2>$null
if (-not $loginSession) { throw "First complete: aws login --profile $LoginProfile --region us-east-1" }

# The official CLI credential-process bridge avoids requiring a second SDK login
# or exporting secret values to the shell, repository, logs, or frontend.
$providerCommand = '"' + $awsExecutable + '" configure export-credentials --profile ' + $LoginProfile + ' --format process'
$existingProvider = & $awsExecutable configure get credential_process --profile $SdkProfile 2>$null
if ($existingProvider -and $existingProvider -ne $providerCommand) {
    throw "SDK profile $SdkProfile already uses another provider. Choose a fresh SdkProfile."
}
& $awsExecutable configure set credential_process $providerCommand --profile $SdkProfile
if ($LASTEXITCODE -ne 0) { throw 'Could not configure the non-secret SDK credential-process bridge.' }
& $awsExecutable configure set region us-east-1 --profile $SdkProfile
if ($LASTEXITCODE -ne 0) { throw 'Could not configure the SDK region.' }

if (-not $DatabasePath) { $DatabasePath = Join-Path $repoRoot 'data\alexa-preview.db' }
$DatabasePath = [IO.Path]::GetFullPath($DatabasePath)
New-Item -ItemType Directory -Path (Split-Path -Parent $DatabasePath) -Force | Out-Null
$runtimeValues = @{
    AWS_PROFILE = $SdkProfile
    AWS_REGION = 'us-east-1'
    BEDROCK_MODEL_ID = 'amazon.nova-lite-v1:0'
    PAWTWIN_MODE = 'local'
    PAWTWIN_MODEL_BACKEND = 'local_fake'
    PAWTWIN_MEMORY_BACKEND = 'not_implemented'
    PAWTWIN_FAMILY_MODEL_BACKEND = 'bedrock'
    PAWTWIN_FAMILY_MODEL_BUDGET_USD = '1'
    PAWTWIN_FAMILY_MODEL_MAX_CALLS = '50'
    PAWTWIN_PHOTO_RECOGNITION_ENABLED = $EnablePhotoRecognition.IsPresent.ToString().ToLowerInvariant()
    PAWTWIN_WORKER_MODE = 'background'
    PAWTWIN_DB_PATH = $DatabasePath
}
$previousValues = @{}
foreach ($key in $runtimeValues.Keys) {
    $previousValues[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
    [Environment]::SetEnvironmentVariable($key, $runtimeValues[$key], 'Process')
}
Push-Location $repoRoot
try {
    & uv run --frozen --extra memory python scripts/aws_probe.py
    if ($LASTEXITCODE -ne 0) { throw 'Read-only AWS preflight failed; the live-model server was not started.' }
    if (-not $ProbeOnly) {
        Write-Host 'Family chat/photo: Bedrock; identity/data/reports: local backend; Alexa: web simulation.'
        Write-Host 'Persistent family-model budget: USD 1 and 50 attempts; excludes other AWS services.'
        & uv run --frozen --extra memory uvicorn pawtwin.main:create_app --factory --host 127.0.0.1 --port $Port --no-proxy-headers
        if ($LASTEXITCODE -ne 0) { throw 'Bedrock family server exited with an error.' }
    }
}
finally {
    Pop-Location
    foreach ($key in $previousValues.Keys) {
        [Environment]::SetEnvironmentVariable($key, $previousValues[$key], 'Process')
    }
}
