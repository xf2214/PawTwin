"""Export the current working tree for local review, without Git history or user data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(
        ["git", "-c", f"core.excludesFile={os.devnull}", *args], cwd=root
    )


def allowed(name: str) -> bool:
    path = PurePosixPath(name)
    parts = {part.casefold() for part in path.parts}
    filename = path.name.casefold()
    denied = {".git", ".venv", ".cache", "node_modules", "dist", "data", ".aws"}
    if denied.intersection(parts):
        return False
    if filename.startswith(".env") and filename != ".env.example":
        return False
    if path.suffix.lower() in {".pem", ".key", ".p12", ".pfx", ".db", ".sqlite"}:
        return False
    if re.search(r"\.(?:db|sqlite3?)(?:$|[.-])", filename) or filename == "trace.zip":
        return False
    return filename not in {"credentials", "deploy_state.json"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="A new ZIP path outside the checkout")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    destination = args.destination.resolve()
    if destination.is_relative_to(root):
        parser.error("Place the export outside the checkout to avoid exporting itself.")
    if destination.suffix.lower() != ".zip":
        parser.error("Destination must end in .zip.")
    sidecar = destination.with_suffix(".manifest.json")
    if destination.exists() or sidecar.exists():
        parser.error("Destination or manifest already exists; choose a fresh name.")

    # Git selects both tracked and non-ignored untracked additions, including dirty files.
    names = {
        item.decode("utf-8")
        for item in git(root, "ls-files", "-co", "--exclude-standard", "-z").split(b"\0")
        if item
    }
    # These local verification logs are ignored by the generic *.log rule but support review.
    for name in (
        "hackathon-verify-delivery-2026-10-03.log",
        "hackathon-verify-complete-2026-10-03.log",
        "hackathon-verify-accepted-2026-10-03.log",
        "hackathon-e2e-accepted-2026-10-03.log",
    ):
        names.add(f"docs/evidence/{name}")
    for name in ("verify.log", "e2e.log", "rehearsal.log"):
        names.add(f"docs/evidence/submission-readiness-2026-10-11/{name}")
    names.update(
        file.relative_to(root).as_posix()
        for file in (root / "docs/evidence/hackathon-capture").glob("*/capture.log")
    )
    names.update(
        file.relative_to(root).as_posix()
        for directory in (root / "docs/evidence").glob("submission-video-*")
        for file in directory.glob("*/build.log")
    )
    files: list[dict[str, object]] = []
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(names):
            if not allowed(name):
                raise ValueError(f"Sensitive/user-data path was selected: {name}")
            source = root / name
            if not source.is_file():
                continue  # Deleted working-tree files are absent from the export.
            if source.is_symlink() or not source.resolve().is_relative_to(root):
                raise ValueError(f"Path leaves the checkout: {name}")
            content = source.read_bytes()
            archive.writestr(f"pawtwin-app/{name}", content)
            files.append(
                {"path": name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
            )
        manifest = {
            "format": 1,
            "head": git(root, "rev-parse", "HEAD").decode().strip(),
            "branch": git(root, "branch", "--show-current").decode().strip(),
            "boundary": (
                "Current local working-tree snapshot, including uncommitted family extensions. "
                "No Git history, credentials, databases, dependencies, build output "
                "or publication. "
                "This export does not choose a license or grant public sharing rights."
            ),
            "files": files,
        }
        archive.writestr("REVIEW_EXPORT_MANIFEST.json", json.dumps(manifest, indent=2))

    # Validate the bytes actually archived, rather than hashing the possibly changing checkout.
    with zipfile.ZipFile(destination) as archive:
        damaged = archive.testzip()
        if damaged:
            raise ValueError(f"ZIP CRC failure: {damaged}")
        for entry in files:
            content = archive.read(f"pawtwin-app/{entry['path']}")
            if hashlib.sha256(content).hexdigest() != entry["sha256"]:
                raise ValueError(f"Archived bytes differ: {entry['path']}")
        required = {
            "backend/pawtwin/family_api.py", "backend/pawtwin/growth.py",
            "backend/pawtwin/family_models.py", "backend/pawtwin/family_store.py",
            "backend/pawtwin/family_views.py", "backend/pawtwin/family_worker.py",
            "backend/pawtwin/pet_context.py",
            "frontend/src/FamilyApp.tsx", "frontend/e2e/family.spec.ts",
            "frontend/src/FamilyRecords.tsx", "frontend/src/family-api.ts",
            "frontend/src/family-app.css",
            "tests/test_agentcore_sdk_contract.py", "contracts/openapi.json",
            "docs/evidence/hackathon-completeness-2026-10-03.md",
            "scripts/export-review-source.py", "uv.lock", "frontend/package-lock.json",
            "frontend/src/AlexaSimulator.tsx", "frontend/src/alexa-simulator.css",
            "frontend/src/Showcase.tsx", "frontend/src/showcase.css",
            "frontend/e2e/alexa.spec.ts", "frontend/e2e/demo-rehearsal.spec.ts",
            "backend/pawtwin/family_assistant.py", "tests/test_family_bedrock.py",
            "scripts/capture-demo.ps1", "scripts/render-submission-video.py",
            "docs/submission/demo-runbook-2026-10-11.md",
            "docs/evidence/submission-readiness-2026-10-11/verify.log",
            "docs/evidence/submission-readiness-2026-10-11/e2e.log",
            "docs/evidence/hackathon-capture/2026-10-11-final/demo-evidence.json",
            "docs/evidence/hackathon-capture/2026-10-11-final/00-product.png",
            "docs/evidence/hackathon-capture/2026-10-11-final/09-alexa-draft.png",
            "docs/evidence/hackathon-capture/2026-10-11-final/10-alexa-pending.png",
            "docs/evidence/hackathon-capture/2026-10-11-final/11-alexa-confirmed.png",
            "docs/evidence/hackathon-capture/2026-10-11-final/12-alexa-result.png",
        }
        missing = required - {entry["path"] for entry in files}
        if missing:
            raise ValueError(f"Required files absent: {sorted(missing)}")
        archived_names = {entry["path"] for entry in files}
        current_videos = {
            name for name in archived_names
            if name.startswith("docs/evidence/submission-video-2026-10-11/")
            and name.endswith("/pawtwin-local-review.en.mp4")
        }
        if not current_videos:
            raise ValueError("Current 2026-10-11 English review MP4 absent from source package")
        for name in current_videos:
            parent = name.rsplit("/", 1)[0]
            companions = {
                f"{parent}/{filename}" for filename in (
                    "verification.json", "timeline.json", "captions.en.srt",
                    "source-manifest.json", "sha256-manifest.json", "build.log",
                )
            }
            if missing_companions := companions - archived_names:
                raise ValueError(f"Current video evidence absent: {sorted(missing_companions)}")
    manifest["archive_sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
    manifest["archive_bytes"] = destination.stat().st_size
    with sidecar.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    print(json.dumps({"archive": str(destination), "files": len(files),
                      "sha256": manifest["archive_sha256"], "crc": "pass"}, indent=2))


if __name__ == "__main__":
    main()
