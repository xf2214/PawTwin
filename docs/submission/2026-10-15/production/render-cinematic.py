"""Render a source-bound product film with real UI, camera movement and natural narration."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import shutil
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FPS = 24
SIZE = (1920, 1080)
PANE = (48, 102, 1872, 978)
CREAM = "#F5F3EC"
FOREST = "#233D35"
ORANGE = "#CB8650"


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def json_file(path, content):
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")


@lru_cache(maxsize=32)
def font(size, bold=False):
    return ImageFont.truetype(
        str(Path("C:/Windows/Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf")), size
    )


def ease(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def wrap(draw, text, text_font, width):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if line and draw.textlength(trial, font=text_font) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def pill(draw, text, xy, *, active=True):
    x, y = xy
    width = draw.textlength(text, font=font(22, True)) + 36
    draw.rounded_rectangle(
        (x, y, x + width, y + 42),
        radius=21,
        fill=FOREST if active else "#E4E9DF",
    )
    draw.text((x + 18, y + 6), text, font=font(22, True), fill="white" if active else FOREST)
    return width


def camera(image, focus, progress):
    # This changes only the editorial camera; every source pixel is actual captured UI.
    width, height = image.size
    amount = ease(progress)
    target_x, target_y, target_zoom = focus
    initial_zoom = 1.06
    zoom = initial_zoom + (target_zoom - initial_zoom) * amount
    crop_width, crop_height = width / zoom, height / zoom
    cx = width * (0.5 + (target_x - 0.5) * amount)
    cy = height * (0.5 + (target_y - 0.5) * amount)
    cx = max(crop_width / 2, min(width - crop_width / 2, cx))
    cy = max(crop_height / 2, min(height - crop_height / 2, cy))
    view = image.crop(
        (
            round(cx - crop_width / 2),
            round(cy - crop_height / 2),
            round(cx + crop_width / 2),
            round(cy + crop_height / 2),
        )
    )
    return ImageOps.fit(
        view, (PANE[2] - PANE[0], PANE[3] - PANE[1]), method=Image.Resampling.LANCZOS
    )


def compose(image, scene, local, duration, caption, index, total, *, outro=False):
    canvas = Image.new("RGB", SIZE, CREAM)
    draw = ImageDraw.Draw(canvas)
    # Compact header and actor replace the former permanent explanatory sidebar.
    draw.text((52, 17), "PawTwin", font=font(34, True), fill=FOREST)
    draw.text((236, 27), scene["chapter"], font=font(18, True), fill="#627469")
    actor_width = draw.textlength(scene["actor"], font=font(22, True)) + 36
    pill(draw, scene["actor"], (1866 - actor_width, 18))
    slide = round(9 * (1 - ease(local / 0.6)))
    draw.text((52, 61 + slide), scene["title"], font=font(28, True), fill=FOREST)
    camera_progress = max(0, (local - 0.5) / max(1, duration - 1))
    viewport = camera(image, scene["focus"], camera_progress)
    canvas.paste(viewport, PANE[:2])
    draw.rounded_rectangle(PANE, radius=10, outline="#D5DDD3", width=2)
    if "step" in scene:
        x = 1198
        for step, label in enumerate(["Draft", "Review", "Confirm"], 1):
            x += pill(draw, label, (x, 57), active=step == scene["step"]) + 10
    if scene.get("tag"):
        draw.rounded_rectangle((70, 121, 640, 159), radius=18, fill=CREAM)
        draw.text((86, 129), scene["tag"], font=font(17, True), fill=FOREST)
    if index == 0 and local < 2.8:
        # A short title treatment over the real home, not a fabricated app screen.
        opacity = round(240 * (1 - ease(max(0, local - 1.7) / 1.1)))
        intro = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        ink = ImageDraw.Draw(intro)
        ink.rounded_rectangle((96, 194, 830, 368), radius=26, fill=(245, 243, 236, opacity))
        ink.text(
            (130, 214), "One pet.", font=font(56, True), fill=(*ImageColorRGB(FOREST), opacity)
        )
        ink.text(
            (130, 282),
            "A shared routine.",
            font=font(56, True),
            fill=(*ImageColorRGB(FOREST), opacity),
        )
        canvas = Image.alpha_composite(canvas.convert("RGBA"), intro).convert("RGB")
        draw = ImageDraw.Draw(canvas)
    if outro and local > duration - 3.0:
        overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        ink = ImageDraw.Draw(overlay)
        opacity = round(224 * ease((local - duration + 3) / 1.5))
        ink.rounded_rectangle((300, 270, 1620, 670), radius=34, fill=(245, 243, 236, opacity))
        ink.text((375, 310), "PawTwin", font=font(76, True), fill=(*ImageColorRGB(FOREST), opacity))
        ink.text(
            (378, 423),
            "Records. Shared plans. Clear handoffs.",
            font=font(38),
            fill=(*ImageColorRGB(FOREST), opacity),
        )
        ink.text(
            (378, 505),
            "Working local prototype",
            font=font(29, True),
            fill=(*ImageColorRGB(FOREST), opacity),
        )
        ink.text(
            (378, 557),
            "Alexa web simulation · Local rules · SQLite",
            font=font(27),
            fill=(*ImageColorRGB(FOREST), opacity),
        )
        canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(canvas)
    if caption:
        caption_lines = wrap(draw, caption, font(30), 1690)
        if len(caption_lines) > 2:
            raise ValueError(f"Caption exceeds two lines: {caption}")
        height = 47 + len(caption_lines) * 37
        layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        ink = ImageDraw.Draw(layer)
        top = 1028 - height
        ink.rounded_rectangle((86, top, 1834, 1028), radius=22, fill=(26, 46, 39, 232))
        for row, line in enumerate(caption_lines):
            x = (1920 - ink.textlength(line, font=font(30))) / 2
            ink.text((x, top + 17 + row * 37), line, font=font(30), fill="white")
        canvas = Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")
        draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 1041, 1920, 1080), fill=CREAM)
    draw.text((52, 1050), "FICTIONAL FAMILY DEMO", font=font(16, True), fill="#607168")
    draw.text((1180, 1050), "LOCAL RULES · ALEXA WEB SIMULATION", font=font(16), fill="#607168")
    draw.rectangle((52, 1039, 1868, 1043), fill="#D9E0D4")
    fraction = (index + local / duration) / total
    draw.rectangle((52, 1039, 52 + 1816 * fraction, 1043), fill=ORANGE)
    return canvas


def ImageColorRGB(value):
    return tuple(int(value[index : index + 2], 16) for index in [1, 3, 5])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--preview-only", action="store_true")
    args = parser.parse_args()
    capture, output = args.capture.resolve(), args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(output)
    evidence = json.loads((capture / "demo-evidence.json").read_text(encoding="utf-8-sig"))
    if evidence["status"] != "passed" or evidence["backend"] != "local_rules":
        raise ValueError("A passed actual local capture is required")
    story = json.loads((HERE / "story.cinematic.en.json").read_text(encoding="utf-8"))
    encoder = module("native_video", ROOT / "scripts/render-submission-video.py")
    music = module("enhanced_audio", HERE / "audio-enhancement.py")
    encoder.FPS, encoder.FFMPEG = FPS, args.ffmpeg.resolve()
    samples = [
        encoder.read_wave(args.audio / f"voice-{n:02d}.wav")[0] for n in range(len(story) * 2)
    ]
    output.mkdir(parents=True, exist_ok=True)
    scratch = (
        ROOT
        / ".cache/submission-video"
        / ("cinematic-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    )
    scratch.mkdir(parents=True, exist_ok=False)
    log = output / "build.log"
    log.write_text(
        "Real UI + editorial camera + natural narration + original music\n", encoding="utf-8"
    )
    timeline, cues, cursor, rate = [], [], 0.0, 22050
    for index, scene in enumerate(story):
        pair = samples[index * 2 : index * 2 + 2]
        voice_seconds = sum(len(part) / rate for part in pair)
        lead = 0.9 if index == 0 else 0.25
        extra = 1.8 if index == len(story) - 1 else 0.65
        seconds = math.ceil(max(scene["seconds"], lead + voice_seconds + extra) * FPS) / FPS
        start = cursor
        voice_cursor = start + lead
        for text, part in zip(scene["sentences"], pair, strict=True):
            cues.append(
                {
                    "start": voice_cursor,
                    "end": voice_cursor + len(part) / rate,
                    "text": text,
                    "scene": index,
                }
            )
            voice_cursor += len(part) / rate + 0.16
        cursor += seconds
        timeline.append(
            {"index": index, "start": start, "end": cursor, "scene": scene, "seconds": seconds}
        )
    duration = math.ceil((cursor + 0.2) * FPS) / FPS
    if duration >= 180:
        raise ValueError("Narration exceeds the competition duration target")
    voice = np.zeros(round(duration * rate), dtype="<i2")
    for cue, part in zip(cues, samples, strict=True):
        offset = round(cue["start"] * rate)
        voice[offset : offset + len(part)] = part
    encoder.write_wave(output / "narration.en.wav", voice, rate)
    mixed = music.mix_voice(voice, rate, cues, duration, music_path=output / "original-music.wav")
    encoder.write_wave(output / "soundtrack.en.wav", mixed, rate)
    (output / "captions.en.srt").write_text(
        "\n\n".join(
            f"{n + 1}\n{encoder.srt_time(c['start'])} --> {encoder.srt_time(c['end'])}\n{c['text']}"
            for n, c in enumerate(cues)
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "narration.en.txt").write_text(
        "\n\n".join(" ".join(s["sentences"]) for s in story), encoding="utf-8"
    )
    for name in ["narration-provenance.json", "narration-qa.json"]:
        shutil.copy2(args.audio / name, output / name)
    shots = {s["file"]: s for s in evidence["screenshots"]}
    clip_map, sequences, pictures = [], {}, []
    previews = output / "review-frames"
    previews.mkdir()
    for item in timeline:
        index, scene = item["index"], item["scene"]
        picture = Image.open(capture / scene["source"]).convert("RGB")
        pictures.append(picture)
        shot = shots[scene["source"]]
        hold = shot["raw_video_elapsed_hold_ms"]
        suggested = shot.get("suggested_clip_ms", {})
        start = max(0, suggested.get("start", hold["start"] - 1000) / 1000)
        if scene["id"] in {"home", "caregiver", "close"}:
            start = hold["start"] / 1000 + 0.1
        # Keep recorded actions at 1x; never run into a subsequent scene's state.
        visible = min(item["seconds"] - 0.7, hold["end"] / 1000 - start - 0.1)
        raw = capture / f"{scene['role']}.webm"
        segments = scene.get("segments", [{"start": start, "duration": visible}])
        visible = sum(segment["duration"] for segment in segments)
        if visible > item["seconds"] - 0.5:
            raise ValueError("Replay segments do not fit the scene")
        clip_map.append(
            {
                "scene": index,
                "source": raw.name,
                "start": start,
                "duration": visible,
                "segments": segments,
                "speed": 1.0,
                "sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
            }
        )
        frame = compose(
            picture,
            scene,
            item["seconds"] * 0.65,
            item["seconds"],
            scene["sentences"][0],
            index,
            len(story),
            outro=False,
        )
        frame.save(previews / f"planned-{index + 1:02d}.jpg")
        if not args.preview_only:
            sequences[index] = []
            for number, segment in enumerate(segments):
                sequences[index].extend(
                    encoder.extract_raw_sequence(
                        raw,
                        segment["start"],
                        segment["duration"],
                        scratch / f"{index:02d}-{number:02d}-raw",
                        log,
                    )
                )
    json_file(
        output / "timeline.json",
        {
            "duration_seconds": duration,
            "fps": FPS,
            "source_capture": str(capture.relative_to(ROOT)),
            "scenes": timeline,
            "cues": cues,
        },
    )
    json_file(
        output / "clip-map.json",
        {
            "clips": clip_map,
            "presentation": "Real UI clips at 1x plus animated source-preserving result views",
        },
    )
    print(
        json.dumps(
            {
                "seconds": duration,
                "real_replay_seconds": sum(c["duration"] for c in clip_map),
                "scene_count": len(story),
                "preview_only": args.preview_only,
            }
        ),
        flush=True,
    )
    if args.preview_only:
        return

    def frames():
        scene_index, previous_last = 0, None
        for number in range(round(duration * FPS)):
            time = number / FPS
            if scene_index < len(timeline) - 1 and time >= timeline[scene_index]["end"]:
                previous_last = compose(
                    pictures[scene_index],
                    story[scene_index],
                    timeline[scene_index]["seconds"],
                    timeline[scene_index]["seconds"],
                    "",
                    scene_index,
                    len(story),
                )
                scene_index += 1
                print(f"Rendering scene {scene_index + 1}/{len(story)}", flush=True)
            item, scene = timeline[scene_index], story[scene_index]
            local = time - item["start"]
            raw_index = max(0, round(local * FPS))
            raw = sequences[scene_index]
            source = (
                Image.open(raw[raw_index]).convert("RGB")
                if raw_index < len(raw)
                else pictures[scene_index]
            )
            caption = next((c["text"] for c in cues if c["start"] <= time < c["end"]), "")
            image = compose(
                source,
                scene,
                local,
                item["seconds"],
                caption,
                scene_index,
                len(story),
                outro=scene_index == len(story) - 1,
            )
            if previous_last is not None and local < 0.42:
                image = Image.blend(previous_last, image, ease(local / 0.42))
            yield encoder.jpeg_bytes(image)

    avi = scratch / "cinematic.avi"
    encoder.write_avi(avi, frames(), round(duration * FPS), mixed, rate)
    print("Encoding native H.264/AAC", flush=True)
    mp4 = output / "pawtwin-cinematic.en.mp4"
    metadata = encoder.transcode(avi, mp4, log)
    if metadata["video_codec"] != "H264" or metadata["audio_codec"] != "AAC":
        raise ValueError("Unexpected codecs")
    decoded = scratch / "decoded-audio.wav"
    encoder.transcode(mp4, decoded, log, audio_only=True)
    decoded_audio, decoded_rate = encoder.read_wave(decoded)
    stats = encoder.sample_stats(decoded_audio, decoded_rate)
    if stats["clipped_samples"] or abs(stats["duration_seconds"] - duration) > 0.1:
        raise ValueError("Decoded AAC length or clipping failure")
    frames_to_check = [
        (
            item["start"] + min(item["seconds"] * 0.72, 8),
            previews / f"actual-{item['index'] + 1:02d}.jpg",
        )
        for item in timeline
    ]
    for clip, item in zip(clip_map, timeline, strict=True):
        for tag, offset in [
            ("start", 0.2),
            ("middle", clip["duration"] / 2),
            ("end", max(0.2, clip["duration"] - 0.2)),
        ]:
            frames_to_check.append(
                (
                    item["start"] + offset,
                    previews / f"actual-replay-{item['index'] + 1:02d}-{tag}.jpg",
                )
            )
    frames_to_check.append((duration - 1, previews / "actual-outro.jpg"))
    encoder.extract_frames(mp4, frames_to_check, log)
    json_file(
        output / "verification.json",
        {
            "actual_mp4": metadata,
            "actual_decoded_audio": stats,
            "caption_count": len(cues),
            "all_sentences_fit": True,
            "caption_lines_max": 2,
            "actual_decoded_frames": len(frames_to_check),
            "fps_requested": FPS,
            "real_replay_seconds": sum(c["duration"] for c in clip_map),
            "source_app_backend": evidence["backend"],
            "source_app_cloud_calls": evidence["cloud_calls"],
            "production_narration": "JennyNeural online public-fictional-text synthesis",
            "music": "Original synthesized 88 BPM bed with speech ducking",
            "full_human_playback_listening": "not_performed",
        },
    )
    encoder.write_manifest(output)
    print(json.dumps({"output": str(output), "metadata": metadata, "audio": stats}), flush=True)


if __name__ == "__main__":
    main()
