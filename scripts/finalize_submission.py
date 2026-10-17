"""Create non-overwriting, portable local source and submission archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

FINAL_VIDEO = "PawTwin-hackathon-submission-2026-10-15.en.mp4"
SOURCE_NAME = "PawTwin-source-2026-10-15.final.zip"
MATERIALS_NAME = "PawTwin-submission-materials-2026-10-15.final.zip"
DOCUMENT_NAME = "PawTwin-submission-2026-10-15.final.en.docx"
REQUIRED = {
    "backend/pawtwin/main.py",
    "backend/pawtwin/family_api.py",
    "frontend/src/WorkbenchConcierge.tsx",
    "frontend/src/PetConciergePreview.tsx",
    "frontend/src/concierge-scenario.ts",
    "frontend/e2e/workbench-concierge.spec.ts",
    "frontend/e2e/pet-concierge.spec.ts",
    "frontend/index.html",
    "contracts/openapi.json",
    "uv.lock",
    "frontend/package-lock.json",
    "scripts/setup.ps1",
    "scripts/dev-home.ps1",
    "docs/submission/2026-10-15/judge-guide.en.md",
    "docs/submission/2026-10-15/release-source.json",
}
RUNTIME_DIRS = {
    ".git",
    ".venv",
    ".cache",
    ".aws",
    ".auth",
    "__pycache__",
    "node_modules",
    "dist",
    "data",
    ".pytest_cache",
    ".ruff_cache",
    "test-results",
    "playwright-report",
}
ROOT_FILES = {
    ".editorconfig",
    ".gitattributes",
    ".env.example",
    ".python-version",
    ".gitignore",
    ".dockerignore",
    "dockerfile",
    "license",
    "readme.md",
    "readme.zh-cn.md",
    "readme.history.zh-cn.md",
    "contributing.md",
    "security.md",
    "agents.md",
    "pyproject.toml",
    "uv.lock",
}
VIDEO_REPORTS = {
    "verification.json",
    "delivery.json",
    "active-assets-sha256.json",
    "timing-plan.json",
    "production-plan.json",
    "audio-production.json",
    "mp4-container.json",
    "sha256-manifest.json",
    "narration.en.txt",
}


def safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not (
        path.is_absolute() or ".." in path.parts or ":" in name or "\\" in name
    )


def include_source(name: str) -> bool:
    if not safe_name(name):
        return False
    path = PurePosixPath(name)
    lower = name.casefold()
    filename = path.name.casefold()
    if RUNTIME_DIRS.intersection(part.casefold() for part in path.parts):
        return False
    if filename.startswith(".env") and filename != ".env.example":
        return False
    if filename in {"credentials", "deploy_state.json", "deploy_state.json.tmp"}:
        return False
    if re.search(r"\.(?:db|sqlite3?)(?:$|[.-])", filename):
        return False
    if path.suffix.casefold() in {".pem", ".key", ".p12", ".pfx", ".bak", ".pyc"}:
        return False
    if path.suffix.casefold() in {".zip", ".webm", ".mp4", ".wav", ".mp3"}:
        return False
    if lower.startswith(
        ("backend/", "frontend/", "tests/", "contracts/", "scripts/", "infra/", ".github/")
    ):
        return True
    if len(path.parts) == 1:
        return filename in ROOT_FILES
    # Keep the image referenced by the public READMEs in standalone source exports.
    if lower == "docs/evidence/i18n-2026-10-14/product-en.png":
        return True
    if lower.startswith("docs/") and path.suffix.casefold() == ".md":
        return True
    if lower.startswith("docs/") and path.suffix.casefold() in {
        ".py",
        ".ps1",
        ".js",
        ".cjs",
        ".mjs",
        ".ts",
        ".tsx",
        ".css",
        ".html",
    }:
        return True
    if lower.startswith("docs/submission/2026-10-15/"):
        return path.suffix.casefold() in {".json", ".py", ".ps1", ".txt", ".ts"}
    if lower.startswith("docs/evidence/submission-repairs-2026-10-15/"):
        return path.suffix.casefold() == ".json"
    if lower.startswith("docs/evidence/current-version-2026-10-14/"):
        return path.name in {"verify.txt", "e2e.txt"}
    if lower.startswith("docs/evidence/submission-video-2026-10-15/fullfilm-01/"):
        return path.name in VIDEO_REPORTS or lower.endswith(
            (
                "/encoded-review/ffprobe.json",
                "/audio/calm-take/provenance.json",
            )
        )
    return False


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=root)


def source_payload(root: Path) -> dict[str, bytes]:
    selected = git(root, "ls-files", "-co", "--exclude-standard", "-z").split(b"\0")
    payload = {}
    for name in sorted({value.decode("utf-8") for value in selected if value}):
        if not include_source(name):
            continue
        path = root / name
        if not path.is_file():
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Source path leaves the checkout: {name}")
        payload[name] = path.read_bytes()
    missing = REQUIRED - payload.keys()
    if missing:
        raise ValueError(f"Required current source absent: {sorted(missing)}")
    return payload


def application_identity(payload: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name, data in sorted(payload.items()):
        if name.startswith(("backend/", "frontend/", "contracts/")) or name in {
            "pyproject.toml",
            "uv.lock",
            ".python-version",
            "Dockerfile",
            ".env.example",
        }:
            if PurePosixPath(name).suffix.casefold() in {
                ".py",
                ".ts",
                ".tsx",
                ".js",
                ".jsx",
                ".json",
                ".css",
                ".html",
                ".toml",
                ".lock",
                ".yaml",
                ".yml",
                ".svg",
                ".txt",
            } or name in {".python-version", "Dockerfile", ".env.example"}:
                data = data.replace(b"\r\n", b"\n")
            digest.update(name.encode("utf-8") + b"\0" + hashlib.sha256(data).digest())
    return digest.hexdigest()


def validate_source_identity(payload: dict[str, bytes]) -> None:
    record = json.loads(payload["docs/submission/2026-10-15/release-source.json"])
    if record["application_sha256"] != application_identity(payload):
        raise ValueError("Recorded application identity is stale; regenerate release-source.json")


def write_archive(destination: Path, payload: dict[str, bytes], identity: dict) -> dict:
    sidecar = destination.with_suffix(".manifest.json")
    if destination.exists() or sidecar.exists():
        raise FileExistsError("Choose a new archive name; existing deliveries are preserved")
    if "manifest.json" in payload or any(not safe_name(name) for name in payload):
        raise ValueError("Unsafe or reserved archive entry")
    manifest = {
        **identity,
        "files": [
            {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in sorted(payload.items())
        ],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    created_archive = created_sidecar = False
    try:
        with zipfile.ZipFile(destination, "x") as package:
            created_archive = True
            for name, data in sorted(payload.items()):
                mode = (
                    zipfile.ZIP_STORED if name.endswith((".mp4", ".zip")) else zipfile.ZIP_DEFLATED
                )
                package.writestr(name, data, compress_type=mode)
            package.writestr("manifest.json", json.dumps(manifest, indent=2).encode())
        with zipfile.ZipFile(destination) as package:
            if package.testzip():
                raise ValueError("ZIP CRC failed")
            for entry in manifest["files"]:
                data = package.read(entry["path"])
                if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                    raise ValueError(f"Archived bytes changed: {entry['path']}")
        report = {
            **manifest,
            "archive": destination.name,
            "archive_bytes": destination.stat().st_size,
            "archive_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "crc_and_hashes": "passed",
        }
        with sidecar.open("x", encoding="utf-8") as handle:
            created_sidecar = True
            json.dump(report, handle, indent=2)
        return report
    except BaseException:
        if created_sidecar:
            sidecar.unlink(missing_ok=True)
        if created_archive:
            destination.unlink(missing_ok=True)
        raise


def portable_markdown(file: Path, root: Path, packaged_names: set[str]) -> bytes:
    def reference(match):
        label, target = match.groups()
        if target.startswith(("http:", "https:", "#")):
            return match.group(0)
        base, separator, fragment = target.partition("#")
        anchor = separator + fragment
        path = (file.parent / base).resolve()
        if path.name in packaged_names and path in {
            (file.parent / path.name).resolve(),
            (root.parent / path.name).resolve(),
        }:
            return f"[{label}]({path.name}{anchor})"
        if path.is_relative_to(root.resolve()):
            return f"{label} (source repository: {path.relative_to(root).as_posix()}{anchor})"
        return f"{label} (historical local artifact: {path.name}; not included)"

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", reference, file.read_text(encoding="utf-8")).encode(
        "utf-8"
    )


def final_video_payload(root: Path) -> dict[str, bytes]:
    evidence = root / "docs/evidence/submission-video-2026-10-15/fullfilm-01"
    delivery = json.loads((evidence / "delivery.json").read_text(encoding="utf-8"))
    verification = json.loads((evidence / "verification.json").read_text(encoding="utf-8"))
    expected = {
        FINAL_VIDEO,
        FINAL_VIDEO.replace(".mp4", ".srt"),
        FINAL_VIDEO.replace(".mp4", ".poster.png"),
    }
    payload = {}
    for item in delivery["files"]:
        name = Path(item["path"]).name
        if name not in expected:
            continue
        data = (root.parent / name).read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError(f"Final film delivery identity mismatch: {name}")
        payload[name] = data
    if payload.keys() != expected:
        raise ValueError("Final film companions are missing")
    if (
        verification.get("status") != "passed"
        or not 0 < verification["actual_duration_seconds"] < 180
        or hashlib.sha256(payload[FINAL_VIDEO]).hexdigest() != verification["sha256"]
    ):
        raise ValueError("Final film verification identity mismatch")
    payload["video-verification.json"] = (evidence / "verification.json").read_bytes()
    payload["video-delivery.json"] = (evidence / "delivery.json").read_bytes()
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--materials", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.source.resolve().is_relative_to(root) or (
        args.materials and args.materials.resolve().is_relative_to(root)
    ):
        parser.error("Place release archives outside the checkout")
    payload = source_payload(root)
    validate_source_identity(payload)
    material_root = root / "docs/submission/2026-10-15"
    files = {}
    markdown = [
        "README.md",
        "project-description.en.md",
        "judge-guide.en.md",
        "product-feedback.en.md",
        "submission-checklist.md",
        "final-video-production.md",
        "video-feedback-addendum.en.md",
    ]
    if args.materials:
        for destination in [args.source.resolve(), args.materials.resolve()]:
            if destination.exists() or destination.with_suffix(".manifest.json").exists():
                raise FileExistsError("Release destination already exists")
        prerequisites = [root.parent / DOCUMENT_NAME]
        prerequisites.extend(
            material_root / name
            for name in [
                "release-source.json",
                "document-final-qa.json",
                *markdown,
            ]
        )
        for file in prerequisites:
            if not file.is_file():
                raise FileNotFoundError(f"Final materials are incomplete: {file.name}")
        files = final_video_payload(root)
        files[DOCUMENT_NAME] = (root.parent / DOCUMENT_NAME).read_bytes()
        for name in ["release-source.json", "document-final-qa.json"]:
            files[name] = (material_root / name).read_bytes()
        doc_qa = json.loads(files["document-final-qa.json"])
        if doc_qa["sha256"] != hashlib.sha256(files[DOCUMENT_NAME]).hexdigest():
            raise ValueError("Final Word document QA hash mismatch")
        packaged = (
            set(files)
            | set(markdown)
            | {
                args.source.name,
                args.source.with_suffix(".manifest.json").name,
            }
        )
        for name in markdown:
            files[name] = portable_markdown(material_root / name, root, packaged)
    identity = {
        "release_id": "pawtwin-local-final-2026-10-15",
        "source_commit": git(root, "rev-parse", "HEAD").decode().strip(),
        "working_tree_dirty": bool(git(root, "status", "--porcelain=v1").strip()),
        "application_sha256": application_identity(payload),
        "boundary": "Runnable local application source; raw media and runtime data omitted. "
        "Film production additionally needs the separate local Remotion studio.",
    }
    source_report = write_archive(args.source.resolve(), payload, identity)
    reports = [source_report]
    if args.materials:
        try:
            for file in [
                args.source.resolve(),
                args.source.with_suffix(".manifest.json").resolve(),
            ]:
                files[file.name] = file.read_bytes()
            reports.append(
                write_archive(
                    args.materials.resolve(),
                    files,
                    {
                        **identity,
                        "source_archive_sha256": source_report["archive_sha256"],
                        "video_sha256": hashlib.sha256(files[FINAL_VIDEO]).hexdigest(),
                        "human_full_listening": "not_performed",
                        "public_upload": "not_performed",
                    },
                )
            )
        except BaseException:
            args.source.resolve().unlink(missing_ok=True)
            args.source.resolve().with_suffix(".manifest.json").unlink(missing_ok=True)
            raise
    print(
        json.dumps(
            [{key: value for key, value in report.items() if key != "files"} for report in reports],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
