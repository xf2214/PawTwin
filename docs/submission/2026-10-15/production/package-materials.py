"""Package final English materials without databases, credentials or raw recordings."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MATERIALS = HERE.parent
ROOT = HERE.parents[3]
OUTPUTS = ROOT.parent


def portable_markdown(file: Path) -> bytes:
    content = file.read_text(encoding="utf-8")

    def reference(match):
        label, target = match.groups()
        if target.startswith(("http:", "https:", "#")):
            return match.group(0)
        path = (file.parent / target.split("#")[0]).resolve()
        if path.parent == MATERIALS:
            return f"[{label}]({path.name})"
        try:
            relative = path.relative_to(ROOT).as_posix()
        except ValueError:
            return match.group(0)
        return f"{label} (source repository: {relative})"

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", reference, content).encode("utf-8")


def main():
    archive = OUTPUTS / "PawTwin-submission-materials-2026-10-15.zip"
    files = {}
    for name in [
        "PawTwin-submission-2026-10-15.en.docx",
        "PawTwin-demo-2026-10-15.en.mp4",
        "PawTwin-demo-2026-10-15.en.srt",
        "PawTwin-demo-2026-10-15.poster.jpg",
    ]:
        files[name] = (OUTPUTS / name).read_bytes()
    for name in [
        "project-description.en.md",
        "judge-guide.en.md",
        "product-feedback.en.md",
        "submission-checklist.md",
    ]:
        files[name] = portable_markdown(MATERIALS / name)
    readme = """# PawTwin English submission materials

Prepared 15 October 2026. This archive contains final local presentation materials.

- [Editable six-page English document](PawTwin-submission-2026-10-15.en.docx)
- [English demonstration video](PawTwin-demo-2026-10-15.en.mp4)
- [English subtitles](PawTwin-demo-2026-10-15.en.srt)
- [Devpost project description](project-description.en.md)
- [Judge setup and walkthrough](judge-guide.en.md)
- [Product Feedback participant-review draft](product-feedback.en.md)
- [Submission checklist](submission-checklist.md)

The MP4 lasts 170.0185 seconds at 1920 by 1080, with H.264/AAC, English narration
and 26 burned-in caption sentences. It combines 58.8 seconds of real, normal-speed
UI excerpts with their actual result screenshots. Emma, Alex and Mochi are fictional
demonstration identities. The runtime uses local rules and SQLite; Alexa and devices
are simulated and live cloud integrations remain unverified.

All six document pages and sampled actual video frames were visually checked.
Mechanical audio/codec/caption checks passed. Complete human playback and listening
remain necessary before public upload. Personal tool feedback, eligibility/rights,
track selection, source access, public video URL and final submission are pending.

This is a materials archive, not the complete application source. Referenced source
evidence is identified by repository path; share the full runnable GitHub repository
separately. Raw recordings, databases, credentials, page-rendering intermediates and
earlier drafts are excluded. MD source-evidence links are adapted to readable paths
for this standalone archive; the repository retains the original linked documents.

Official rules: https://amazonappdev2026.devpost.com/rules
Deadline: 24 October 2026 at 03:00 Beijing time. Recheck the official portal.
"""
    files["README.md"] = readme.encode("utf-8")
    verification = ROOT / "docs/evidence/submission-video-2026-10-15/family-story-01"
    files["video-verification.json"] = (verification / "verification.json").read_bytes()
    files["video-visual-review.json"] = (verification / "visual-review.json").read_bytes()
    files["document-qa.json"] = (MATERIALS / "document-qa.json").read_bytes()
    manifest = {
        "date": "2026-10-15",
        "source_commit": "6342b96a874daa595b2150080ab64adad70b3d7b",
        "files": [
            {"file": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in files.items()
        ],
    }
    files["manifest.json"] = json.dumps(manifest, indent=2).encode("utf-8")
    with zipfile.ZipFile(archive, "x") as package:
        for name, data in files.items():
            compression = zipfile.ZIP_STORED if name.endswith(".mp4") else zipfile.ZIP_DEFLATED
            package.writestr(name, data, compress_type=compression)
    with zipfile.ZipFile(archive) as package:
        if package.testzip():
            raise ValueError("Archive CRC check failed")
        for item in manifest["files"]:
            if hashlib.sha256(package.read(item["file"])).hexdigest() != item["sha256"]:
                raise ValueError("Archive content hash mismatch")
    print(
        json.dumps(
            {
                "archive": str(archive),
                "files": len(files),
                "bytes": archive.stat().st_size,
                "crc_and_hashes": "PASS",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
