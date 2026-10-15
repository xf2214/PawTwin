"""Create source-bound replay ranges and actual decoded calibration frames."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    capture, output = args.capture.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    evidence = json.loads((capture / "demo-evidence.json").read_text(encoding="utf-8-sig"))
    if evidence["status"] != "passed":
        raise ValueError("Refusing a failed or incomplete capture")
    story = json.loads((Path(__file__).parent / "story.en.json").read_text(encoding="utf-8"))
    shots = {shot["file"]: shot for shot in evidence["screenshots"]}
    sources, clips, previews = {}, [], []
    for scene in story[:-1]:
        shot = shots[scene["source"]]
        role = shot["role"]
        raw = capture / f"{role}.webm"
        if role not in sources:
            info = subprocess.run(
                [str(args.ffmpeg), "-hide_banner", "-i", str(raw)],
                capture_output=True,
                text=True,
            ).stderr
            match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", info)
            if not match:
                raise ValueError(f"Missing duration for {role}")
            hours, minutes, seconds = map(float, match.groups())
            sources[role] = {
                "sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
                "duration_seconds": hours * 3600 + minutes * 60 + seconds,
            }
        hold = shot["raw_video_elapsed_hold_ms"]["start"] / 1000
        # Early introductory views deliberately omit registration/invitation entry.
        stable = scene["source"] in {"00-product.png", "01-home.png", "14-caregiver.png"}
        start = hold + 0.15 if stable else max(0.0, hold - 1.1)
        duration = 4.6 if stable else 5.0
        if start + duration >= sources[role]["duration_seconds"]:
            raise ValueError("Requested replay exceeds actual WebM")
        clip = {
            "scene_source": scene["source"],
            "role": role,
            "start": round(start, 3),
            "duration": duration,
            "speed": 1.0,
        }
        clips.append(clip)
        for tag, offset in [("start", 0.1), ("middle", duration / 2), ("end", duration - 0.1)]:
            preview = output / f"{scene['source'][:-4]}-{tag}.png"
            run = subprocess.run(
                [
                    str(args.ffmpeg),
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-ss",
                    str(start + offset),
                    "-i",
                    str(raw),
                    "-frames:v",
                    "1",
                    "-c:v",
                    "png",
                    "-y",
                    str(preview),
                ],
                capture_output=True,
                text=True,
            )
            if run.returncode or not preview.exists():
                raise RuntimeError(run.stderr)
            if tag == "middle":
                previews.append((scene["source"], preview))
    sheet = Image.new("RGB", (1920, 4 * 400), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (label, preview) in enumerate(previews):
        view = Image.open(preview).convert("RGB")
        view.thumbnail((640, 360))
        x, y = (index % 3) * 640, (index // 3) * 400
        sheet.paste(view, (x, y))
        draw.text((x + 10, y + 370), label, fill="black")
    sheet.save(output / "calibration-contact-sheet.jpg")
    (output / "clip-map.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sources": sources,
                "clips": clips,
                "timing_note": (
                    "Ranges decoded from the actual role-specific WebM; "
                    "inspect calibration frames before rendering."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "clips": len(clips),
                "replay_seconds": sum(c["duration"] for c in clips),
                "sources": sources,
                "output": str(output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
