"""Build a portable v2 materials archive and verify its content hashes."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MATERIALS = HERE.parent
ROOT = HERE.parents[3]
OUTPUTS = ROOT.parent
EVIDENCE = ROOT / "docs/evidence/submission-video-2026-10-15/cinematic-01"


def portable_markdown(file: Path, included: set[str]) -> bytes:
    content = file.read_text(encoding="utf-8")

    def reference(match):
        label, target = match.groups()
        if target.startswith(("http:", "https:", "#")):
            return match.group(0)
        path = (file.parent / target.split("#")[0]).resolve()
        if path.name in included and path.parent in (MATERIALS, OUTPUTS):
            return f"[{label}]({path.name})"
        try:
            relative = path.relative_to(ROOT).as_posix()
        except ValueError:
            relative = path.name
        return f"{label} (source repository: {relative})"

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", reference, content).encode("utf-8")


def main():
    spec = importlib.util.spec_from_file_location(
        "native_encoder", ROOT / "scripts/render-submission-video.py"
    )
    encoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(encoder)
    encoder.write_manifest(EVIDENCE)

    archive = OUTPUTS / "PawTwin-submission-materials-2026-10-15.v2.zip"
    names = [
        "PawTwin-submission-2026-10-15.en.docx",
        "PawTwin-demo-2026-10-15.en.v2.mp4",
        "PawTwin-demo-2026-10-15.en.v2.srt",
        "PawTwin-demo-2026-10-15.v2.poster.jpg",
    ]
    markdown = [
        "project-description.en.md",
        "judge-guide.en.md",
        "product-feedback.en.md",
        "submission-checklist.md",
        "video-optimization-v2.md",
        "video-feedback-addendum.en.md",
    ]
    included = set(names + markdown)
    files = {name: (OUTPUTS / name).read_bytes() for name in names}
    files.update(
        {name: portable_markdown(MATERIALS / name, included) for name in markdown}
    )
    files["README.md"] = b"""# PawTwin English submission materials - optimized video

Prepared 15 October 2026. This archive contains local presentation materials.

- [Editable English document](PawTwin-submission-2026-10-15.en.docx)
- [Optimized English video](PawTwin-demo-2026-10-15.en.v2.mp4)
- [English subtitles](PawTwin-demo-2026-10-15.en.v2.srt)
- [Devpost project description](project-description.en.md)
- [Judge setup and walkthrough](judge-guide.en.md)
- [Participant tool-feedback draft](product-feedback.en.md)
- [New video tool-feedback addendum](video-feedback-addendum.en.md)
- [Remaining submission checklist](submission-checklist.md)
- [Video production and verification](video-optimization-v2.md)

The optimized video lasts 150.2583 seconds at 1920 by 1080 and 24 fps, using
H.264/AAC, natural English narration, original music and 28 burned-in captions.
It includes about 101.8 seconds of real normal-speed UI excerpts, including
reading holds, with camera movement and crossfades over actual source pixels.
Emma, Alex and Mochi are fictional demonstration identities. The application
uses local rules and SQLite; Alexa and devices are simulated. The online voice
service was used only to produce the public fictional narration script.

Sampled finished frames and mechanical audio/caption/codec checks were reviewed.
Full human playback and listening remain unperformed. Complete these before
public upload. Personal tool feedback, eligibility/rights, source access, a
public video URL and final participant submission remain pending.

The editable document is unchanged from the first delivery. The new production
tools are recorded separately in the video-feedback addendum. Previous videos
and the first materials archive remain preserved outside this versioned archive.

This is a materials archive, not the application source. Source evidence is
identified by repository path; share the complete runnable repository separately.
Raw recordings, databases, credentials and production dependencies are excluded.
"""
    for name, source in [
        ("video-verification.json", EVIDENCE / "verification.json"),
        ("video-visual-review.json", EVIDENCE / "visual-review.json"),
        ("narration-provenance.json", EVIDENCE / "narration-provenance.json"),
        ("document-qa.json", MATERIALS / "document-qa.json"),
    ]:
        files[name] = source.read_bytes()
    manifest = {
        "date": "2026-10-15",
        "version": 2,
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
            {"archive": str(archive), "files": len(files), "crc_and_hashes": "PASS"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
