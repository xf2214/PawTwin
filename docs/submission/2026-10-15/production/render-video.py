"""Reproduce the 15 October family-story edit using the established offline encoder."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clip-map", type=Path)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location(
        "pawtwin_offline_encoder", ROOT / "scripts/render-submission-video.py"
    )
    encoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(encoder)
    encoder.DEMO_EDIT = True
    encoder.FFMPEG = args.ffmpeg.resolve()
    if not encoder.FFMPEG.is_file():
        raise FileNotFoundError(encoder.FFMPEG)
    encoder.STORY = json.loads((HERE / "story.en.json").read_text(encoding="utf-8"))
    capture, output = args.capture.resolve(), args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Refusing nonempty output directory {output}")
    evidence = json.loads((capture / "demo-evidence.json").read_text(encoding="utf-8-sig"))
    if evidence["backend"] != "local_rules" or evidence["cloud_calls"] != 0:
        raise ValueError("Expected the explicitly labelled local demonstration")
    for scene in encoder.STORY:
        if not (capture / scene["source"]).is_file():
            raise FileNotFoundError(scene["source"])
    clip_map = None
    if args.clip_map:
        clip_map = json.loads(args.clip_map.read_text(encoding="utf-8-sig"))
        sources = {}
        for scene in encoder.STORY:
            sources.setdefault(scene["source"], scene)
        for clip in clip_map["clips"]:
            source = capture / f"{clip['role']}.webm"
            if (
                hashlib.sha256(source.read_bytes()).hexdigest()
                != clip_map["sources"][clip["role"]]["sha256"]
            ):
                raise ValueError("Replay source hash mismatch")
            if (
                clip["start"] < 0
                or clip["duration"] <= 0
                or clip["start"] + clip["duration"]
                > clip_map["sources"][clip["role"]]["duration_seconds"]
            ):
                raise ValueError("Replay range exceeds inspected source")
            sources[clip["scene_source"]]["clip"] = {
                key: clip[key] for key in ["role", "start", "duration"]
            }
    output.mkdir(parents=True, exist_ok=True)
    scratch = (
        ROOT
        / ".cache/submission-video"
        / ("family-story-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    )
    scratch.mkdir(parents=True, exist_ok=False)
    log = output / "build.log"
    log.write_text("Actual English capture: " + str(capture) + "\n", encoding="utf-8")
    if clip_map:
        (output / "clip-map.json").write_text(json.dumps(clip_map, indent=2), encoding="utf-8")
    # Retain the source-aware compositor and all actual codec, audio, timing,
    # subtitle-fit, decoded-frame and SHA-256 checks from the existing encoder.
    original_compose = encoder.compose

    def compose(*values):
        image = original_compose(*values)
        draw = encoder.ImageDraw.Draw(image)
        draw.rectangle((1370, 200, 1840, 258), fill="#E5EEDD")
        draw.text(
            (1384, 218), "THE FAMILY CARE ROUTINE", font=encoder.font(22, True), fill="#4D6B50"
        )
        return image

    encoder.compose = compose
    encoder.build_review(capture, output, scratch, log, evidence)


if __name__ == "__main__":
    main()
