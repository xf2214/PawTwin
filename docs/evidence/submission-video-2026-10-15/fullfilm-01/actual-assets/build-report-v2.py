"""Preserve the original report crop and add a version with the full left heading."""

import hashlib
import json
import subprocess
from pathlib import Path

STUDIO = Path(r"C:\Users\11831\Desktop\hks\outputs\pawtwin-video-studio-2026-10-15")
SOURCE = Path(
    r"C:\Users\11831\Desktop\hks\outputs\pawtwin-app\docs\evidence\hackathon-cinematic-capture-2026-10-15\attempt-03-native1920\owner.webm"
)
OUT = STUDIO / "public/fullfilm"
EVID = Path(__file__).parent
FF = STUDIO / "node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
FP = FF.with_name("ffprobe.exe")


def run(a):
    p = subprocess.run([str(x) for x in a], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-4000:])
    return p.stdout


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


dest = OUT / "emma-daily-report-v2.mp4"
hold = OUT / "emma-daily-report-v2-hold.png"
run(
    [
        FF,
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        "128",
        "-i",
        SOURCE,
        "-t",
        "7",
        "-vf",
        "crop=1100:734:280:334",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-y",
        dest,
    ]
)
meta = json.loads(
    run(
        [
            FP,
            "-v",
            "error",
            "-show_entries",
            "stream=width,height,nb_frames,r_frame_rate",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            dest,
        ]
    )
)
actual = float(meta["format"]["duration"])
run(
    [
        FF,
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        round(actual - 0.04, 3),
        "-i",
        dest,
        "-frames:v",
        "1",
        "-an",
        "-c:v",
        "png",
        "-y",
        hold,
    ]
)
run(
    [
        FF,
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        "0.04",
        "-i",
        dest,
        "-frames:v",
        "1",
        "-an",
        "-c:v",
        "png",
        "-y",
        EVID / "emma-daily-report-v2-start.png",
    ]
)
run([FF, "-hide_banner", "-loglevel", "error", "-i", dest, "-an", "-c:v", "png", "-f", "null", "-"])
data = {
    "id": "emma-daily-report-v2",
    "source": str(SOURCE),
    "source_sha256": sha(SOURCE),
    "start": 128.0,
    "requested_duration": 7.0,
    "crop": [280, 334, 1100, 734],
    "speed": 1.0,
    "file": str(dest),
    "sha256": sha(dest),
    "hold": str(hold),
    "hold_encoded_timestamp": round(actual - 0.04, 3),
    "hold_sha256": sha(hold),
    "encoded": meta,
    "full_decode": "passed",
    "change": (
        "Spatial crop shifted 20 source pixels left to preserve the full Mochi heading. "
        "Original assets unchanged."
    ),
}
(EVID / "report-v2-provenance.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
print(json.dumps(data, indent=2))
