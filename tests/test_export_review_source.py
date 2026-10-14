"""Review exports must exclude databases, sidecars and browser credentials."""

import importlib.util
from pathlib import Path

import pytest

_script = Path(__file__).resolve().parents[1] / "scripts" / "export-review-source.py"
_spec = importlib.util.spec_from_file_location("review_export", _script)
assert _spec is not None and _spec.loader is not None
_export = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_export)


@pytest.mark.parametrize(
    "name",
    [
        "local-demo.db-wal",
        "local-demo.db-shm",
        "local-demo.db-journal",
        "local-demo.db.before-family-20261014.bak",
        "custom/LOCAL.SQLITE3-wal",
        "custom/local.sqlite.backup",
        "docs/evidence/browser/trace.zip",
    ],
)
def test_export_rejects_runtime_data_and_browser_traces(name):
    assert not _export.allowed(name)


@pytest.mark.parametrize(
    "name",
    [".env.example", "backend/pawtwin/family_store.py", "docs/evidence/review/verify.log"],
)
def test_export_keeps_source_and_review_evidence(name):
    assert _export.allowed(name)
