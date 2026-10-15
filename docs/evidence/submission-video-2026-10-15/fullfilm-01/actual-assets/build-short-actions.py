"""Explicit editorial cuts between real normal-speed claim and complete actions."""

import hashlib
import json
import subprocess
from pathlib import Path

STUDIO = Path(r"C:\Users\11831\Desktop\hks\outputs\pawtwin-video-studio-2026-10-15")
SOURCE = Path(
    r"C:\Users\11831\Desktop\hks\outputs\pawtwin-app\docs\evidence\hackathon-cinematic-capture-2026-10-15\attempt-03-native1920\carer.webm"
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


clips = []
for name, start, dur in [("alex-claim-action", 82.7, 2.4), ("alex-complete-action", 91.7, 7.0)]:
    dest = OUT / (name + ".mp4")
    run(
        [
            FF,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            start,
            "-i",
            SOURCE,
            "-t",
            dur,
            "-vf",
            "crop=736:630:304:244",
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
    hold = OUT / (name + "-hold.png")
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
    for label, t in [("start", 0.04), ("middle", actual / 2)]:
        run(
            [
                FF,
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                t,
                "-i",
                dest,
                "-frames:v",
                "1",
                "-an",
                "-c:v",
                "png",
                "-y",
                EVID / (name + "-" + label + ".png"),
            ]
        )
    run(
        [
            FF,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            dest,
            "-an",
            "-c:v",
            "png",
            "-f",
            "null",
            "-",
        ]
    )
    clips.append(
        {
            "id": name,
            "source": str(SOURCE),
            "source_sha256": sha(SOURCE),
            "start": start,
            "requested_duration": dur,
            "crop": [304, 244, 736, 630],
            "speed": 1.0,
            "file": str(dest),
            "sha256": sha(dest),
            "hold": str(hold),
            "hold_sha256": sha(hold),
            "encoded": meta,
            "full_decode": "passed",
        }
    )
(EVID / "short-action-provenance.json").write_text(
    json.dumps(
        {
            "clips": clips,
            "edit_note": (
                "The full original clip remains unchanged. The separate normal-speed excerpts "
                "omit only the between-action expanded form waiting section; this is an explicit "
                "editorial cut, with no synthesized UI."
            ),
        },
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(clips, indent=2))
