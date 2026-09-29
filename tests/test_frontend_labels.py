"""G8-review hardening for Day-4 ruling 13 / ruling 11 (frontend side).

The honest e2e assertions in frontend/e2e/*.spec.ts forbid substrings like
「可检索」 inside the memory area. Those forbidden strings and the label
constants in App.tsx are coupled BY CONVENTION only -- a future rewording that
re-introduces such a substring would either trip the browser tests or read to a
judge as proven retrieval. These tests pin the convention at the source level,
offline, without a browser.
"""

from __future__ import annotations

import re
from pathlib import Path

APP_SOURCE = Path(__file__).resolve().parents[1] / "frontend" / "src" / "App.tsx"

# Substrings no status/backend LABEL may contain: each one claims a retrieval or
# an extraction that has not happened (AGENTS.md L18). They mirror the
# not.toContain assertions in feedback.spec.ts and acceptance.spec.ts.
FORBIDDEN_LABEL_SUBSTRINGS = ("可检索", "已检索到记忆", "真实记忆", "真实检索")


def _label_block(name: str) -> str:
    source = APP_SOURCE.read_text("utf-8")
    match = re.search(rf"const {name}[^=]*=\s*\{{(.*?)}}", source, re.DOTALL) or re.search(
        rf"const {name}[^=]*=\s*'(.*?)'", source
    )
    assert match, f"label constant {name} not found in App.tsx -- renamed or removed?"
    return match.group(1)


def test_no_memory_label_claims_retrievability_or_real_memory() -> None:
    for block in ("MEMORY_STATUS_LABELS", "MEMORY_BACKEND_LABELS", "REAL_CALL_EVIDENCE"):
        text = _label_block(block)
        for forbidden in FORBIDDEN_LABEL_SUBSTRINGS:
            assert forbidden not in text, f"{block} contains forbidden 「{forbidden}」"


def test_real_model_wording_exists_only_next_to_its_evidence() -> None:
    """「真实模型」 may only appear in the evidence-guarded branch (request_id +
    bedrock) or the local_fake denial 「非真实模型」 -- never in a config-derived
    label that a judge could read as a proven cloud call."""
    text = _label_block("ANALYZER_CONFIG_LABELS")
    # 「非真实模型」 is the local stand-in DENIAL and is allowed; a bare
    # 「真实模型」 in a config-derived label is not.
    assert "真实模型" not in text.replace("非真实模型", "")

    source = APP_SOURCE.read_text("utf-8")
    for line in source.splitlines():
        if "真实模型" in line and "非真实模型" not in line:
            # FAILURE_LABELS names the real backend to report ITS unavailability
            # (a failure message, never a status claim) -- allowed.
            if "BACKEND_UNAVAILABLE" in line:
                continue
            assert "request_id" in line and "bedrock" in line, (
                f"「真实模型」 wording without its evidence pair: {line.strip()}"
            )
    # The evidence constant itself must name what it proves.
    assert "request id" in _label_block("REAL_CALL_EVIDENCE")
