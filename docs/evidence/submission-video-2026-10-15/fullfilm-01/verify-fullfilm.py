"""Verify the actual complete MP4 and export matching submission sidecars."""

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
EVIDENCE = HERE.parent / "pawtwin-app/docs/evidence/submission-video-2026-10-15/fullfilm-01"
QA = EVIDENCE / "encoded-review"
QA.mkdir(exist_ok=True)
VIDEO = HERE.parent / "PawTwin-hackathon-submission-2026-10-15.en.mp4"
BIN = HERE / "node_modules/@remotion/compositor-win32-x64-msvc"
PLAN = json.loads((HERE / "src/fullfilm-plan.json").read_text(encoding="utf-8"))


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
decode = run(
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
(QA / "full-decode.log").write_text(decode.stderr, encoding="utf-8")
assert not decode.stderr.strip(), decode.stderr
frames = [
    54,
    250,
    334,
    507,
    550,
    590,
    655,
    769,
    778,
    804,
    828,
    940,
    1069,
    1227,
    1300,
    1430,
    1474,
    1510,
    1605,
    1685,
    1785,
    1840,
    1910,
    1950,
    2085,
    2140,
    2265,
    2290,
    2440,
    2495,
    2570,
    2646,
    2660,
    2720,
    2910,
    2989,
    3008,
    3070,
    3170,
    3280,
    3439,
    3510,
    3760,
    3869,
    3940,
    4126,
    4180,
    4269,
]
for _i, n in enumerate(frames, 1):
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
            QA / f"actual-{n:04d}.png",
        ]
    )
for start in range(0, len(frames), 6):
    sheet = Image.new("RGB", (1920, 1710), "#eeeae1")
    draw = ImageDraw.Draw(sheet)
    for i, n in enumerate(frames[start : start + 6]):
        im = Image.open(QA / f"actual-{n:04d}.png").convert("RGB")
        im.thumbnail((960, 540))
        x = (i % 2) * 960
        y = (i // 2) * 570
        sheet.paste(im, (x, y))
        draw.text((x + 15, y + 545), f"Encoded frame {n} / {n / 30:.3f}s", fill="#203F35")
    sheet.save(QA / f"contact-{start // 6 + 1}.jpg", quality=92)
audio = QA / "encoded-audio.stereo.wav"
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
        audio,
    ]
)
with wave.open(str(audio), "rb") as f:
    samples = np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.int32)
    audio_seconds = f.getnframes() / f.getframerate()
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
peak = float(np.abs(samples).max() / 32768)
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
    PLAN["durationInFrames"],
)
assert (v["codec_name"], a["codec_name"], a["channels"], int(a["sample_rate"])) == (
    "h264",
    "aac",
    2,
    48000,
)
actual_duration = float(metadata["format"]["duration"])
assert actual_duration < 180 and abs(actual_duration - PLAN["durationSeconds"]) < 0.05
assert (
    stats["clipped_samples"] == 0
    and -16.7 <= stats["integrated_lufs"] <= -15.3
    and stats["true_peak_dbtp"] <= -1.5
), stats
preserved = {
    "PawTwin-style-sample-2026-10-15.en.mp4": (
        "4f7634c05d46fb885d45d913ddbc8076bfa7baee5b98ac5fdae26c7ec2bbf337"
    ),
    "PawTwin-style-sample-2026-10-15.en.v2.mp4": (
        "7426a38abc17dbfea78520de806259736e32752cedf4091338d79d31ce2e3f01"
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
cues = json.loads((HERE / "src/fullfilm-captions.json").read_text(encoding="utf-8"))
assert all(c["startMs"] < c["endMs"] for c in cues) and all(
    c["endMs"] < n["startMs"] for c, n in zip(cues, cues[1:], strict=False)
)
words = json.loads((EVIDENCE / "audio/calm-take/narration-words.json").read_text(encoding="utf-8"))


def clean(x):
    return re.sub("[^a-z0-9]", "", x.lower())


assert clean(" ".join(c["text"] for c in cues)) == clean(words["text"])


def stamp(ms):
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


srt = VIDEO.with_suffix(".srt")
srt.write_text(
    "\n\n".join(
        f"{i + 1}\n{stamp(c['startMs'])} --> {stamp(c['endMs'])}\n{c['text']}"
        for i, c in enumerate(cues)
    )
    + "\n",
    encoding="utf-8",
)
poster = VIDEO.with_suffix(".poster.png")
shutil.copyfile(QA / "actual-0054.png", poster)
report = {
    "status": "passed",
    "video": str(VIDEO),
    "actual_duration_seconds": actual_duration,
    "under_180_seconds": True,
    "resolution": [1920, 1080],
    "fps": 30,
    "video_frames": PLAN["durationInFrames"],
    "codec": ["H264", "AAC"],
    "full_stream_decode": "passed",
    "actual_encoded_stereo_audio": stats,
    "caption_cues": len(cues),
    "caption_text_matches_full_narration": True,
    "no_caption_overlap": True,
    "actual_encoded_frames_extracted": len(frames),
    "visual_review": "pending",
    "independent_audio_review": "pending",
    "human_full_listening": "not_performed",
    "source_ui_speed": 1,
    "application_boundary": (
        "Local prototype and Alexa text web simulator; "
        "Miso/Luna are labelled fictional scripted presets"
    ),
    "previous_deliveries_preserved": list(preserved),
    "bytes": VIDEO.stat().st_size,
    "sha256": sha(VIDEO),
    "external_upload_or_submission": "not_performed",
}
save(EVIDENCE / "verification.json", report)
for name in [
    "build-fullfilm.py",
    "verify-fullfilm.py",
    "render-fullfilm.ps1",
    "check-fullfilm.cjs",
    "fullfilm-script.final.en.txt",
]:
    shutil.copyfile(HERE / name, EVIDENCE / name)
shutil.copytree(HERE / "src", EVIDENCE / "source", dirs_exist_ok=True)
print(json.dumps(report, indent=2))
