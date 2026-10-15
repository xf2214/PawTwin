"""Verify the encoded review artifact, without app/browser interactions."""

import hashlib
import json
import re
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "pawtwin-app/docs/evidence/submission-video-2026-10-15/style-sample-audio-v2"
QA = OUT / "encoded-review"
QA.mkdir(exist_ok=True)
VIDEO = HERE.parent / "PawTwin-style-sample-2026-10-15.en.v2.mp4"
BIN = HERE / "node_modules/@remotion/compositor-win32-x64-msvc"
PLAN = json.loads((OUT / "timing-plan.json").read_text(encoding="utf-8"))


def run(args):
    return subprocess.run(
        [str(a) for a in args], check=True, capture_output=True, text=True, encoding="utf-8"
    )


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


metadata = json.loads(
    run(
        [BIN / "ffprobe.exe", "-v", "error", "-show_streams", "-show_format", "-of", "json", VIDEO]
    ).stdout
)
save(QA / "ffprobe.json", metadata)
decoded = run(
    [
        BIN / "ffmpeg.exe",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        VIDEO,
        "-c:v",
        "png",
        "-c:a",
        "pcm_s16le",
        "-f",
        "null",
        "-",
    ]
)
(QA / "full-decode.log").write_text(decoded.stderr, encoding="utf-8")
assert not decoded.stderr.strip(), decoded.stderr
b = PLAN["boundariesInFrames"]
end = PLAN["durationInFrames"]
frames = [
    54,
    b[1] + 30,
    b[1] + 135,
    b[2] - 1,
    b[2] + 12,
    b[2] + 105,
    b[3] - 5,
    b[3] + 45,
    b[3] + 105,
    b[3] + 134,
    b[3] + 175,
    b[4] - 4,
    b[4] + 20,
    b[4] + 50,
    end - 2,
]
for i, n in enumerate(frames, 1):
    run(
        [
            BIN / "ffmpeg.exe",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{n / 30:.9f}",
            "-i",
            VIDEO,
            "-frames:v",
            "1",
            "-an",
            "-c:v",
            "png",
            QA / f"actual-{i:02d}.png",
        ]
    )
for start in range(0, len(frames), 5):
    sheet = Image.new("RGB", (1920, 1710), "#eeeae1")
    draw = ImageDraw.Draw(sheet)
    for i, n in enumerate(frames[start : start + 5]):
        im = Image.open(QA / f"actual-{start + i + 1:02d}.png").convert("RGB")
        im.thumbnail((960, 540))
        x = (i % 2) * 960
        y = (i // 2) * 570
        sheet.paste(im, (x, y))
        draw.text((x + 15, y + 545), f"Encoded frame {n} / {n / 30:.3f}s", fill="#243E34")
    sheet.save(QA / f"contact-{start // 5 + 1}.jpg", quality=90)
run(
    [
        BIN / "ffmpeg.exe",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        VIDEO,
        "-vn",
        "-ac",
        "2",
        "-ar",
        "48000",
        "-c:a",
        "pcm_s16le",
        QA / "encoded-audio.stereo.wav",
    ]
)
with wave.open(str(QA / "encoded-audio.stereo.wav"), "rb") as f:
    samples = np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.int32)
    audio_seconds = f.getnframes() / f.getframerate()
peak = float(np.max(np.abs(samples))) / 32768
level = run(
    [
        BIN / "ffmpeg.exe",
        "-hide_banner",
        "-i",
        VIDEO,
        "-vn",
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json",
        "-f",
        "null",
        "-",
    ]
).stderr
(QA / "encoded-loudness.log").write_text(level, encoding="utf-8")
meter = json.loads(re.search(r'\{\s*"input_i".*?\}', level, re.S).group(0))
stats = {
    "duration_seconds": audio_seconds,
    "integrated_lufs": float(meter["input_i"]),
    "true_peak_dbtp": float(meter["input_tp"]),
    "loudness_range_lu": float(meter["input_lra"]),
    "sample_peak_dbfs": round(float(20 * np.log10(peak)), 3),
    "clipped_samples": int((np.abs(samples) >= 32767).sum()),
}
v = next(s for s in metadata["streams"] if s["codec_type"] == "video")
a = next(s for s in metadata["streams"] if s["codec_type"] == "audio")
assert (v["width"], v["height"], v["avg_frame_rate"], int(v["nb_frames"])) == (
    1920,
    1080,
    "30/1",
    end,
)
assert (v["codec_name"], a["codec_name"], a["channels"], int(a["sample_rate"])) == (
    "h264",
    "aac",
    2,
    48000,
)
assert abs(float(metadata["format"]["duration"]) - PLAN["durationSeconds"]) < 0.05
assert (
    stats["clipped_samples"] == 0
    and stats["true_peak_dbtp"] <= -1.5
    and -16.7 <= stats["integrated_lufs"] <= -15.3
), stats
preserved = {
    "PawTwin-style-sample-2026-10-15.en.mp4": (
        "4f7634c05d46fb885d45d913ddbc8076bfa7baee5b98ac5fdae26c7ec2bbf337"
    ),
    "PawTwin-demo-2026-10-15.en.mp4": (
        "ff878c137e1141aacd7f738edf2e13e9684cd52fff3a8a36160df133a2f24ebb"
    ),
    "PawTwin-demo-2026-10-15.en.v2.mp4": (
        "51129a97a67efe2cde8b21abf6b6bb62990b62b7ee3f1576422d98bf9daa97dc"
    ),
    "PawTwin-submission-2026-10-15.en.docx": (
        "898853181c58f4be5d2e9959b6d048791c0681dca36531c7e822fe0e50e383bb"
    ),
}
for name, expected in preserved.items():
    assert sha(HERE.parent / name) == expected, name
cues = json.loads((HERE / "src/voice-revision-captions.json").read_text(encoding="utf-8"))


def stamp(ms):
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# Resolve brief caption reading holds as displayed by the first matching cue.
effective_start = 0
blocks = []
for i, c in enumerate(cues):
    effective_start = max(c["startMs"], effective_start)
    blocks.append(f"{i + 1}\n{stamp(effective_start)} --> {stamp(c['endMs'])}\n{c['text']}")
    effective_start = c["endMs"]
VIDEO.with_suffix(".srt").write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
poster = VIDEO.with_suffix(".poster.png")
shutil.copyfile(QA / "actual-01.png", poster)
report = {
    "status": "passed",
    "actual_duration_seconds": float(metadata["format"]["duration"]),
    "resolution": [1920, 1080],
    "fps": 30,
    "video_frames": end,
    "decoded_all_streams_without_error": True,
    "actual_stereo_audio": stats,
    "narration": "one continuous Ava story take; default rate and pitch",
    "additional_phrase_pauses": PLAN["insertedPauses"],
    "original_pcm_retained_before_mix": PLAN["sourceVoiceSamplesPreserved"],
    "normal_speed_ui_seconds": [6.3, 5.8],
    "result_frame_holds_seconds": [(b[2] - b[1]) / 30 - 6.3, (b[3] - b[2]) / 30 - 5.8],
    "caption_cues": len(cues),
    "encoded_frames_for_visual_review": frames,
    "previous_deliveries_preserved": list(preserved),
    "human_listening_review": "not_performed",
    "creative_user_review": "pending",
    "video_bytes": VIDEO.stat().st_size,
    "sha256": sha(VIDEO),
}
save(OUT / "verification.json", report)
for name in ["build-voice-revision.py", "verify-voice-revision.py", "render-voice-revision.ps1"]:
    shutil.copyfile(HERE / name, OUT / name)
shutil.copytree(HERE / "src", OUT / "source", dirs_exist_ok=True)
print(json.dumps(report, indent=2))
