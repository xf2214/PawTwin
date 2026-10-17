"""Exercise Node discovery when PATH contains several installations."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_runtime_selects_first_application_when_node_has_multiple_path_matches(tmp_path):
    powershell = shutil.which("pwsh")
    if not powershell:
        pytest.skip("PowerShell 7 is required for the launch-script regression")

    executable = tmp_path / ("node.cmd" if os.name == "nt" else "node")
    executable.write_text(
        "@echo off\necho v24.0.0\n" if os.name == "nt" else "#!/bin/sh\necho v24.0.0\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    npm = tmp_path / "node_modules/npm/bin/npm-cli.js"
    npm.parent.mkdir(parents=True)
    npm.write_text("// fixture: the fake Node command returns its version", encoding="utf-8")
    script = Path(__file__).resolve().parents[1] / "scripts/node-runtime.ps1"

    def quoted(path):
        return "'" + str(path).replace("'", "''") + "'"

    command = f"""
$ErrorActionPreference = 'Stop'
$env:USERPROFILE = {quoted(tmp_path)}
$env:PAWTWIN_NODE_DIR = ''
$env:PAWTWIN_NPM_CLI = ''
. {quoted(script)}
function Get-Command {{
    param($Name, $CommandType, $ErrorAction)
    [pscustomobject]@{{ Source = {quoted(executable)} }}
    [pscustomobject]@{{ Source = {quoted(tmp_path / 'second-install/node')} }}
}}
Get-PawTwinNodeRuntime | ConvertTo-Json -Compress
"""
    result = subprocess.run(
        [powershell, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    runtime = json.loads(result.stdout)
    assert Path(runtime["NodeExe"]) == executable
    assert runtime["NodeVersion"] == "24.0.0"
    assert Path(runtime["NpmPath"]) == npm
