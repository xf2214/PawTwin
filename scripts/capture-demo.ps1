param(
    [ValidateRange(1024, 65535)][int]$Port = 8812,
    [string]$OutputDirectory,
    [string]$NodeDirectory
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$frontendRoot = Join-Path $repoRoot 'frontend'
. (Join-Path $PSScriptRoot 'node-runtime.ps1')

if (-not $OutputDirectory) {
    $captureId = '{0}-{1}' -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'), ([guid]::NewGuid().ToString('N').Substring(0, 8))
    $OutputDirectory = Join-Path $repoRoot "docs\evidence\hackathon-capture\$captureId"
}
elseif (-not [IO.Path]::IsPathRooted($OutputDirectory)) {
    $OutputDirectory = Join-Path $repoRoot $OutputDirectory
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
if ($OutputDirectory.TrimEnd('\', '/') -eq [IO.Path]::GetPathRoot($OutputDirectory).TrimEnd('\', '/')) {
    throw 'OutputDirectory must be a dedicated capture directory, not a filesystem root.'
}
$OutputDirectory = $OutputDirectory.TrimEnd('\', '/')
if (Test-Path -LiteralPath $OutputDirectory) {
    if (-not (Test-Path -LiteralPath $OutputDirectory -PathType Container)) {
        throw "OutputDirectory must be a new or empty directory: $OutputDirectory"
    }
    if (Get-ChildItem -LiteralPath $OutputDirectory -Force | Select-Object -First 1) {
        throw "OutputDirectory is not empty. Use a new directory; existing evidence will not be overwritten: $OutputDirectory"
    }
}

# Refuse an occupied port without inspecting or stopping another process.
$listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $Port)
try {
    $listener.Start()
}
catch {
    throw "Port $Port is unavailable. Choose another -Port; no existing service was stopped."
}
finally {
    $listener.Stop()
}

$runtime = Get-PawTwinNodeRuntime -NodeDirectory $NodeDirectory
$playwrightCli = Join-Path $frontendRoot 'node_modules\@playwright\test\cli.js'
if (-not (Test-Path -LiteralPath $playwrightCli -PathType Leaf)) {
    throw 'Playwright is not installed. Run scripts/setup.ps1 before capturing.'
}

if (-not (Test-Path -LiteralPath $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}
$rawDirectory = Join-Path $OutputDirectory 'raw'
$reportPath = Join-Path $OutputDirectory 'results.json'
$logPath = Join-Path $OutputDirectory 'capture.log'
$manifestPath = Join-Path $OutputDirectory 'sha256-manifest.json'
$startedAt = [DateTime]::UtcNow.ToString('o')
"Started UTC: $startedAt`nPort: $Port`nDatabase: :memory:`nMode: local; model: local_fake; memory: not_implemented; photos: manual`nNode: $($runtime.NodeVersion)" |
    Set-Content -LiteralPath $logPath -Encoding UTF8

function Write-CaptureLog {
    param([Parameter(ValueFromPipeline)]$Message)
    process {
        # Tee-Object uses different default encodings in PowerShell 5.1 and 7.
        [string]$Message | Add-Content -LiteralPath $logPath -Encoding UTF8
        Write-Output $Message
    }
}

function Get-CaptureResults {
    param([object[]]$Suites)
    foreach ($suite in $Suites) {
        foreach ($spec in $suite.specs) {
            foreach ($test in $spec.tests) {
                foreach ($result in $test.results) {
                    [pscustomobject]@{
                        Spec = $spec
                        Test = $test
                        Result = $result
                    }
                }
            }
        }
        if ($suite.suites) { Get-CaptureResults -Suites $suite.suites }
    }
}

function Get-AttachmentBytes {
    param([Parameter(Mandatory)]$Attachment)
    if ($Attachment.path) {
        $sourcePath = [string]$Attachment.path
        if (-not [IO.Path]::IsPathRooted($sourcePath)) {
            $sourcePath = Join-Path $frontendRoot $sourcePath
        }
        $sourcePath = [IO.Path]::GetFullPath($sourcePath)
        $rawPrefix = $rawDirectory.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
        if (-not $sourcePath.StartsWith($rawPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Attachment '$($Attachment.name)' is outside this run's raw directory."
        }
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            throw "Attachment '$($Attachment.name)' was reported but its file is missing."
        }
        $bytes = [IO.File]::ReadAllBytes($sourcePath)
    }
    elseif ($Attachment.body) {
        # Playwright's JSON reporter serializes attachment bodies as base64.
        $bytes = [Convert]::FromBase64String([string]$Attachment.body)
    }
    else {
        throw "Attachment '$($Attachment.name)' has neither a file nor a body."
    }
    if ($bytes.Length -eq 0) { throw "Attachment '$($Attachment.name)' is empty." }
    return ,$bytes
}

$localValues = @{
    PAWTWIN_E2E_PORT = [string]$Port
    PAWTWIN_DB_PATH = ':memory:'
    PAWTWIN_MODE = 'local'
    PAWTWIN_MODEL_BACKEND = 'local_fake'
    PAWTWIN_MEMORY_BACKEND = 'not_implemented'
    PAWTWIN_WORKER_MODE = 'background'
    PAWTWIN_PHOTO_RECOGNITION_ENABLED = 'false'
    PAWTWIN_FAMILY_MODEL_BACKEND = 'local_rules'
    PAWTWIN_RECORD_DEMO = '1'
    PLAYWRIGHT_JSON_OUTPUT_NAME = $reportPath
    PATH = "$($runtime.NodeDirectory)$([IO.Path]::PathSeparator)$env:PATH"
}
$previousValues = @{}
foreach ($key in $localValues.Keys) {
    $previousValues[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
}

Push-Location $frontendRoot
try {
    foreach ($key in $localValues.Keys) {
        [Environment]::SetEnvironmentVariable($key, $localValues[$key], 'Process')
    }
    'Building the production frontend.' | Write-CaptureLog
    Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run', 'build') *>&1 |
        Write-CaptureLog

    'Capturing only e2e/demo-rehearsal.spec.ts with one worker and no retries.' |
        Write-CaptureLog
    & $runtime.NodeExe $playwrightCli test 'e2e/demo-rehearsal.spec.ts' `
        --config 'playwright.config.ts' --workers 1 --retries 0 `
        --output $rawDirectory --reporter=json *>&1 |
        Write-CaptureLog
    if ($LASTEXITCODE -ne 0) { throw "Demo rehearsal failed with exit code $LASTEXITCODE. Diagnostics remain in $OutputDirectory" }
    if (-not (Test-Path -LiteralPath $reportPath -PathType Leaf)) {
        throw 'Playwright returned success without the required JSON report.'
    }

    $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
    $results = @(Get-CaptureResults -Suites $report.suites)
    if ($report.stats.expected -ne 1 -or $report.stats.unexpected -ne 0 -or
        $report.stats.flaky -ne 0 -or $report.stats.skipped -ne 0 -or
        $results.Count -ne 1 -or $results[0].Result.status -ne 'passed' -or
        $results[0].Result.retry -ne 0 -or -not $results[0].Spec.ok) {
        throw 'The JSON report does not show exactly one passing, unretried demo rehearsal.'
    }
    $attachments = @($results[0].Result.attachments)
    $jsonEvidence = @($attachments | Where-Object { $_.name -eq 'demo-evidence' -and $_.contentType -eq 'application/json' })
    $ownerVideos = @($attachments | Where-Object { $_.contentType -eq 'video/webm' -and $_.name -match '(^|[^a-z])owner([^a-z]|$)' })
    $carerVideos = @($attachments | Where-Object { $_.contentType -eq 'video/webm' -and $_.name -match '(^|[^a-z])carer([^a-z]|$)' })
    $screenshots = @($attachments | Where-Object { $_.contentType -eq 'image/png' })
    if ($jsonEvidence.Count -ne 1 -or $ownerVideos.Count -ne 1 -or
        $carerVideos.Count -ne 1 -or $screenshots.Count -lt 14) {
        throw 'Required attachments are missing or ambiguous: demo-evidence JSON, owner/carer WebM, and fourteen current PNGs. No successful capture manifest will be written.'
    }

    # Validate every actual attachment before creating the collected package.
    $collected = @(
        [pscustomobject]@{ Name = 'demo-evidence.json'; Attachment = $jsonEvidence[0]; Bytes = (Get-AttachmentBytes $jsonEvidence[0]) }
        [pscustomobject]@{ Name = 'owner.webm'; Attachment = $ownerVideos[0]; Bytes = (Get-AttachmentBytes $ownerVideos[0]) }
        [pscustomobject]@{ Name = 'carer.webm'; Attachment = $carerVideos[0]; Bytes = (Get-AttachmentBytes $carerVideos[0]) }
    )
    $evidence = [Text.Encoding]::UTF8.GetString($collected[0].Bytes) | ConvertFrom-Json
    if ($evidence.schema_version -ne 2 -or $evidence.backend -ne 'local_rules' -or
        $evidence.cloud_calls -ne 0 -or -not $evidence.alexa_care.confirmed_proposal.task_id -or
        $evidence.screenshots.Count -lt 14) {
        throw 'Evidence does not establish the current isolated Alexa draft/confirmation rehearsal.'
    }
    foreach ($attachment in $screenshots) {
        $fileName = [IO.Path]::GetFileName([string]$attachment.name)
        if (-not $fileName.EndsWith('.png', [StringComparison]::OrdinalIgnoreCase)) { $fileName += '.png' }
        if ($fileName -notmatch '^[a-zA-Z0-9][a-zA-Z0-9._-]*\.png$') {
            throw "PNG attachment name is unsuitable for a portable package: $($attachment.name)"
        }
        $collected += [pscustomobject]@{
            Name = $fileName
            Attachment = $attachment
            Bytes = (Get-AttachmentBytes $attachment)
        }
    }
    $uniqueNames = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($item in $collected) {
        if (-not $uniqueNames.Add($item.Name)) { throw "Duplicate collected filename: $($item.Name)" }
        $destination = Join-Path $OutputDirectory $item.Name
        if (Test-Path -LiteralPath $destination) { throw "Refusing to overwrite $destination" }
    }
    foreach ($item in $collected) {
        $destination = Join-Path $OutputDirectory $item.Name
        $stream = [IO.File]::Open($destination, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
        try { $stream.Write($item.Bytes, 0, $item.Bytes.Length) }
        finally { $stream.Dispose() }
    }

    $completedAt = [DateTime]::UtcNow.ToString('o')
    "Capture succeeded UTC: $completedAt. Collected files are original local test artifacts; the videos have no narration." |
        Write-CaptureLog
    $files = @(Get-ChildItem -LiteralPath $OutputDirectory -Recurse -File | Sort-Object FullName | ForEach-Object {
        [pscustomobject]@{
            path = $_.FullName.Substring($OutputDirectory.Length + 1).Replace('\', '/')
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    })
    [ordered]@{
        schema_version = 1
        started_utc = $startedAt
        completed_utc = $completedAt
        test = 'e2e/demo-rehearsal.spec.ts'
        port = $Port
        node_version = $runtime.NodeVersion
        boundary = 'Current product page and independent Alexa web simulation; local SQLite in memory; rule drafts with explicit manual-care confirmation; silent raw footage; no cloud call or publication. Screenshot test elapsed timestamps are not raw video seek positions.'
        collected_attachments = @($collected | ForEach-Object {
            [pscustomobject]@{ file = $_.Name; attachment_name = $_.Attachment.name; content_type = $_.Attachment.contentType }
        })
        files = $files
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    Write-Host "Capture package: $OutputDirectory"
    Write-Host 'Review owner.webm and carer.webm before editing a final presentation video.'
}
catch {
    "FAILED: $($_.Exception.Message)" | Add-Content -LiteralPath $logPath -Encoding UTF8
    throw
}
finally {
    foreach ($key in $previousValues.Keys) {
        [Environment]::SetEnvironmentVariable($key, $previousValues[$key], 'Process')
    }
    Pop-Location
}
