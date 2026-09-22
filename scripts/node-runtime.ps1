function Get-PawTwinNodeRuntime {
    param([string]$NodeDirectory)

    $explicitNodeDirectory = $NodeDirectory
    if (-not $explicitNodeDirectory) {
        $explicitNodeDirectory = $env:PAWTWIN_NODE_DIR
    }

    if ($explicitNodeDirectory) {
        $NodeDirectory = [IO.Path]::GetFullPath($explicitNodeDirectory)
        $nodeExe = Join-Path $NodeDirectory ($(if ($IsWindows -or $env:OS -eq 'Windows_NT') { 'node.exe' } else { 'node' }))
        if (-not (Test-Path -LiteralPath $nodeExe -PathType Leaf)) {
            throw "The explicit Node directory does not contain a Node executable: $NodeDirectory"
        }
    }
    else {
        $nodeExe = $null
        if ($env:USERPROFILE) {
            $bundledDirectory = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin'
            $bundledNode = Join-Path $bundledDirectory 'node.exe'
            if (Test-Path -LiteralPath $bundledNode -PathType Leaf) {
                $NodeDirectory = $bundledDirectory
                $nodeExe = $bundledNode
            }
        }
        if (-not $nodeExe) {
            $nodeCommand = Get-Command node -CommandType Application -ErrorAction Stop
            $nodeExe = $nodeCommand.Source
            $NodeDirectory = Split-Path -Parent $nodeExe
        }
    }

    $versionText = (& $nodeExe --version).TrimStart('v')
    $version = [version]$versionText
    $compatible = ($version.Major -eq 20 -and $version.Minor -ge 19) -or
        ($version.Major -eq 22 -and $version.Minor -ge 12) -or
        $version.Major -gt 22
    if (-not $compatible) {
        throw "Node $versionText is not compatible with Vite; use Node 20.19+, 22.12+, or newer."
    }

    $npmPath = $env:PAWTWIN_NPM_CLI
    if ($npmPath) {
        $npmPath = [IO.Path]::GetFullPath($npmPath)
        if (-not (Test-Path -LiteralPath $npmPath -PathType Leaf)) {
            throw "The explicit npm path does not exist: $npmPath"
        }
    }
    else {
        $npmCandidates = @(
            (Join-Path $NodeDirectory 'node_modules\npm\bin\npm-cli.js'),
            (Join-Path $NodeDirectory '..\lib\node_modules\npm\bin\npm-cli.js')
        )
        $npmPath = $npmCandidates | Where-Object {
            Test-Path -LiteralPath $_ -PathType Leaf
        } | Select-Object -First 1
        if (-not $npmPath) {
            $npmCommand = Get-Command npm.cmd, npm -ErrorAction SilentlyContinue |
                Where-Object { $_.CommandType -in @('Application', 'ExternalScript') } |
                Select-Object -First 1
            if ($npmCommand) {
                $npmDirectory = Split-Path -Parent $npmCommand.Source
                $npmPath = @(
                    (Join-Path $npmDirectory 'node_modules/npm/bin/npm-cli.js'),
                    (Join-Path $npmDirectory '../lib/node_modules/npm/bin/npm-cli.js')
                ) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
                    Select-Object -First 1
            }
        }
        if (-not $npmPath) {
            throw 'npm was not found beside Node or on PATH. Set PAWTWIN_NPM_CLI explicitly.'
        }
    }

    $pathSeparator = [IO.Path]::PathSeparator
    $previousPath = $env:PATH
    try {
        $env:PATH = "$NodeDirectory$pathSeparator$previousPath"
        $npmVersion = if ([IO.Path]::GetExtension($npmPath) -eq '.js') {
            & $nodeExe $npmPath --version
        }
        else {
            & $npmPath --version
        }
        if ($LASTEXITCODE -ne 0) {
            throw "npm version check failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        $env:PATH = $previousPath
    }

    [pscustomobject]@{
        NodeDirectory = $NodeDirectory
        NodeExe = $nodeExe
        NodeVersion = $versionText
        NpmPath = $npmPath
        NpmVersion = $npmVersion.Trim()
    }
}

function Invoke-PawTwinNpm {
    param(
        [Parameter(Mandatory)]$Runtime,
        [Parameter(Mandatory)][string[]]$NpmArguments
    )

    $previousPath = $env:PATH
    try {
        $env:PATH = "$($Runtime.NodeDirectory)$([IO.Path]::PathSeparator)$previousPath"
        if ([IO.Path]::GetExtension($Runtime.NpmPath) -eq '.js') {
            & $Runtime.NodeExe $Runtime.NpmPath @NpmArguments
        }
        else {
            & $Runtime.NpmPath @NpmArguments
        }
        if ($LASTEXITCODE -ne 0) {
            throw "npm command failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        $env:PATH = $previousPath
    }
}
