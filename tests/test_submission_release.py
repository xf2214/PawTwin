"""Exercise source filtering and non-destructive release packaging."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "finalize_submission.py"
spec = importlib.util.spec_from_file_location("submission_release", SCRIPT)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


@pytest.mark.parametrize(
    "name",
    [
        ".env",
        "frontend/.env.local",
        "data/pet.db",
        "data/pet.db-wal",
        "docs/evidence/session/trace.zip",
        "frontend/node_modules/pkg/a.js",
        "frontend/dist/index.html",
        "backend/__pycache__/a.pyc",
        "docs/evidence/raw.webm",
        "../outside.py",
        "/outside.py",
        "C:/outside.py",
        "docs/evidence/capture/demo-evidence.json",
        "frontend/.auth/state.json",
        "FRONTEND/TEST-RESULTS/session.json",
        "infra/deploy_state.json.tmp",
        "docs/evidence/trace-renamed.zip",
    ],
)
def test_source_selection_excludes_secrets_runtime_and_raw_evidence(name):
    assert not release.include_source(name)


@pytest.mark.parametrize(
    "name",
    [
        ".env.example",
        "uv.lock",
        "frontend/package-lock.json",
        "frontend/public/logo.png",
        "frontend/src/WorkbenchConcierge.tsx",
        "backend/pawtwin/family_api.py",
        "tests/test_care_access.py",
        "contracts/openapi.json",
        "docs/FEATURES.md",
        "docs/submission/2026-10-15/release-source.json",
        "docs/evidence/submission-repairs-2026-10-15/verification.json",
        "docs/evidence/submission-video-2026-10-15/fullfilm-01/build-fullfilm.py",
        ".gitattributes",
        "docs/evidence/workbench-concierge-2026-10-15/capture.cjs",
        "docs/evidence/submission-video-2026-10-15/fullfilm-01/renderer.mjs",
        "docs/evidence/submission-video-2026-10-15/fullfilm-01/sha256-manifest.json",
        "docs/evidence/submission-video-2026-10-15/fullfilm-01/audio/calm-take/provenance.json",
        "docs/evidence/current-version-2026-10-14/verify.txt",
    ],
)
def test_source_selection_keeps_runnable_assets_and_release_instructions(name):
    assert release.include_source(name)


def test_source_archive_keeps_license_and_public_readme_dependencies(tmp_path, monkeypatch):
    names = {
        "LICENSE",
        "README.md",
        "README.zh-CN.md",
        "README.history.zh-CN.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        ".editorconfig",
        "docs/readme/pawtwin-overview.jpg",
    }
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    monkeypatch.setattr(release, "git", lambda *_: b"\0".join(n.encode() for n in names))
    monkeypatch.setattr(release, "REQUIRED", names)
    payload = release.source_payload(tmp_path)
    target = tmp_path / "source.zip"
    release.write_archive(target, payload, {})
    with zipfile.ZipFile(target) as archive:
        assert names <= set(archive.namelist())
        assert archive.read("LICENSE") == b"LICENSE"


def test_archive_records_actual_bytes_and_preserves_existing_delivery(tmp_path):
    target = tmp_path / "release.zip"
    payload = {"README.md": b"setup", "frontend/public/logo.png": b"asset"}
    report = release.write_archive(target, payload, {"source_commit": "abc"})
    with zipfile.ZipFile(target) as package:
        manifest = json.loads(package.read("manifest.json"))
        for entry in manifest["files"]:
            assert hashlib.sha256(package.read(entry["path"])).hexdigest() == entry["sha256"]
    assert report["archive_sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
    original = target.read_bytes()
    with pytest.raises(FileExistsError):
        release.write_archive(target, {"README.md": b"changed"}, {})
    assert target.read_bytes() == original


def test_existing_sidecar_prevents_partial_delivery(tmp_path):
    target = tmp_path / "release.zip"
    target.with_suffix(".manifest.json").write_text("original", encoding="utf-8")
    with pytest.raises(FileExistsError):
        release.write_archive(target, {"README.md": b"setup"}, {})
    assert not target.exists()


def test_failed_archive_write_removes_only_the_new_partial_delivery(tmp_path, monkeypatch):
    target = tmp_path / "release.zip"
    original = zipfile.ZipFile.writestr

    def fail_on_second(package, name, data, **kwargs):
        if name == "b.txt":
            raise OSError("injected write failure")
        return original(package, name, data, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "writestr", fail_on_second)
    with pytest.raises(OSError, match="injected"):
        release.write_archive(target, {"a.txt": b"first", "b.txt": b"second"}, {})
    assert not target.exists()
    assert not target.with_suffix(".manifest.json").exists()


@pytest.mark.parametrize("name", ["../escape.txt", "/absolute.txt", "C:/drive.txt"])
def test_archive_rejects_escaping_entry_names(tmp_path, name):
    target = tmp_path / "release.zip"
    with pytest.raises(ValueError):
        release.write_archive(target, {name: b"bad"}, {})
    assert not target.exists()


def test_standalone_markdown_links_use_packaged_file_or_repository_path(tmp_path):
    root = tmp_path / "source"
    source = root / "docs" / "submission" / "README.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        "[guide](judge-guide.en.md) [code](../../backend/app.py) "
        "[rules](https://example.com/rules)",
        encoding="utf-8",
    )
    result = release.portable_markdown(source, root, {"judge-guide.en.md"}).decode()
    assert "[guide](judge-guide.en.md)" in result
    assert "code (source repository: backend/app.py)" in result
    assert "[rules](https://example.com/rules)" in result


def test_source_payload_includes_dirty_and_untracked_application_files(tmp_path, monkeypatch):
    root = tmp_path / "source"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    tracked = root / "backend/pawtwin/main.py"
    tracked.parent.mkdir(parents=True)
    tracked.write_text("original", encoding="utf-8")
    subprocess.run(["git", "add", "backend/pawtwin/main.py"], cwd=root, check=True)
    tracked.write_text("current", encoding="utf-8")
    added = root / "frontend/src/WorkbenchConcierge.tsx"
    added.parent.mkdir(parents=True)
    added.write_text("new component", encoding="utf-8")
    (root / ".env").write_text("LOCAL_FIXTURE=excluded", encoding="utf-8")
    monkeypatch.setattr(
        release,
        "REQUIRED",
        {
            "backend/pawtwin/main.py",
            "frontend/src/WorkbenchConcierge.tsx",
        },
    )
    payload = release.source_payload(root)
    assert payload["backend/pawtwin/main.py"] == b"current"
    assert payload["frontend/src/WorkbenchConcierge.tsx"] == b"new component"
    assert ".env" not in payload


def test_source_record_cannot_silently_name_an_older_application():
    payload = {
        "frontend/src/App.tsx": b"current app",
        "docs/submission/2026-10-15/release-source.json": b'{"application_sha256":"stale"}',
    }
    with pytest.raises(ValueError, match="identity"):
        release.validate_source_identity(payload)


def test_markdown_does_not_redirect_historical_same_basename_to_current_file(tmp_path):
    root = tmp_path / "source"
    source = root / "docs" / "submission" / "README.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        "[old](../historical/README.md#evidence) [guide](guide.md#setup)", encoding="utf-8"
    )
    result = release.portable_markdown(source, root, {"README.md", "guide.md"}).decode()
    assert "[old](README.md)" not in result
    assert "docs/historical/README.md#evidence" in result
    assert "[guide](guide.md#setup)" in result


def test_sidecar_write_failure_does_not_leave_a_half_published_release(tmp_path, monkeypatch):
    def fail_json(*args, **kwargs):
        raise OSError("injected sidecar failure")

    monkeypatch.setattr(release.json, "dump", fail_json)
    target = tmp_path / "release.zip"
    with pytest.raises(OSError, match="sidecar"):
        release.write_archive(target, {"README.md": b"setup"}, {})
    assert not target.exists()
    assert not target.with_suffix(".manifest.json").exists()


def test_missing_materials_fail_before_the_source_archive_is_created(tmp_path, monkeypatch):
    root = tmp_path / "app"
    root.mkdir()
    payload = {"frontend/src/App.tsx": b"current"}
    payload["docs/submission/2026-10-15/release-source.json"] = json.dumps(
        {
            "application_sha256": release.application_identity(payload),
        }
    ).encode()
    monkeypatch.setattr(release, "__file__", str(root / "scripts/finalize_submission.py"))
    monkeypatch.setattr(release, "source_payload", lambda _: payload)
    monkeypatch.setattr(release, "git", lambda *_: b"fixture-commit")
    target = tmp_path / "source.zip"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "finalize_submission.py",
            "--source",
            str(target),
            "--materials",
            str(tmp_path / "materials.zip"),
        ],
    )
    with pytest.raises(FileNotFoundError):
        release.main()
    assert not target.exists()


def test_application_identity_survives_gits_configured_line_ending_normalization():
    assert release.application_identity({"frontend/src/App.tsx": b"app\r\n"}) == (
        release.application_identity({"frontend/src/App.tsx": b"app\n"})
    )
