"""Derive 1x real UI excerpts; keep all source captures unchanged."""

import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

BASE = Path(
    r"C:\Users\11831\Desktop\hks\outputs\pawtwin-app\docs\evidence\hackathon-cinematic-capture-2026-10-15\attempt-03-native1920"
)
STUDIO = Path(r"C:\Users\11831\Desktop\hks\outputs\pawtwin-video-studio-2026-10-15")
OUT = STUDIO / "public/fullfilm"
OUT.mkdir(exist_ok=True)
EVID = Path(__file__).parent
FF = STUDIO / "node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
FP = FF.with_name("ffprobe.exe")
CLIPS = [
    {
        "id": "owner-draft-prepare",
        "role": "owner",
        "start": 76.0,
        "duration": 8.0,
        "crop": [780, 304, 1000, 720],
        "operation": "Review draft, prepare proposal, observe confirmation required",
    },
    {
        "id": "owner-explicit-confirm",
        "role": "owner",
        "start": 84.0,
        "duration": 10.0,
        "crop": [780, 304, 1000, 720],
        "operation": "Explicitly confirm manual care, observe planned awaiting manual completion",
    },
    {
        "id": "alex-claim-complete",
        "role": "carer",
        "start": 82.7,
        "duration": 16.0,
        "crop": [304, 244, 736, 630],
        "operation": "Claim manual care as Alex, record completion, view Completed result",
    },
    {
        "id": "alex-household-activity",
        "role": "carer",
        "start": 99.8,
        "duration": 5.0,
        "crop": [1048, 518, 750, 550],
        "operation": "Read saved household activity attribution to Alex",
    },
    {
        "id": "emma-daily-report",
        "role": "owner",
        "start": 128.0,
        "duration": 7.0,
        "crop": [300, 334, 1100, 734],
        "operation": (
            "Generate daily report after completion, "
            "show one manual care completion and missing data"
        ),
    },
]


def run(a):
    p = subprocess.run([str(x) for x in a], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-4000:])
    return p.stdout


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


for c in CLIPS:
    src = BASE / (c["role"] + ".webm")
    x, y, w, h = c["crop"]
    dest = OUT / (c["id"] + ".mp4")
    vf = f"crop={w}:{h}:{x}:{y}"
    run(
        [
            FF,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            c["start"],
            "-i",
            src,
            "-t",
            c["duration"],
            "-vf",
            vf,
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
    # Last displayed source-derived frame is used for any editorial reading hold.
    hold = OUT / (c["id"] + "-hold.png")
    hold_time = round(float(meta["format"]["duration"]) - 0.04, 3)
    run(
        [
            FF,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            hold_time,
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
    frames = []
    for tag, t in [("start", 0.04), ("middle", c["duration"] / 2), ("end", c["duration"] - 0.08)]:
        p = EVID / (c["id"] + "-" + tag + ".png")
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
                p,
            ]
        )
        frames.append(p)
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
    c.update(
        source_path=str(src),
        source_sha256=sha(src),
        source_resolution=[1920, 1080],
        source_frame_rate="25/1",
        speed=1.0,
        transformation="Spatial crop only; no time scaling or synthesized interface",
        file=str(dest),
        sha256=sha(dest),
        hold=str(hold),
        hold_encoded_timestamp=hold_time,
        hold_sha256=sha(hold),
        encoded=meta,
        full_decode_check="passed",
    )
    print(json.dumps({"id": c["id"], "output": str(dest), "meta": meta}), flush=True)
STILLS = []
for sid, role, t, crop, action in [
    ("owner-draft-state", "owner", 77.0, [784, 644, 992, 324], "Review draft; no task created yet"),
    (
        "owner-pending-state",
        "owner",
        84.0,
        [784, 734, 992, 234],
        "Prepared care proposal; explicit confirmation needed",
    ),
    (
        "owner-confirmed-state",
        "owner",
        92.0,
        [780, 728, 1000, 280],
        "Planned; awaiting manual completion",
    ),
    (
        "alex-history-attribution",
        "carer",
        102.8,
        [1048, 654, 750, 374],
        "Saved recent household activity identifies Alex completed and claimed care",
    ),
]:
    x, y, w, h = crop
    p = OUT / (sid + ".png")
    src = BASE / (role + ".webm")
    run(
        [
            FF,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            t,
            "-i",
            src,
            "-vf",
            f"crop={w}:{h}:{x}:{y}",
            "-frames:v",
            "1",
            "-an",
            "-c:v",
            "png",
            "-y",
            p,
        ]
    )
    STILLS.append(
        {
            "id": sid,
            "source": str(src),
            "source_timestamp": t,
            "crop": crop,
            "meaning": action,
            "file": str(p),
            "sha256": sha(p),
        }
    )
sheet = Image.new("RGB", (1920, len(CLIPS) * 420), "white")
draw = ImageDraw.Draw(sheet)
for row, c in enumerate(CLIPS):
    for col, tag in enumerate(["start", "middle", "end"]):
        p = EVID / (c["id"] + "-" + tag + ".png")
        im = Image.open(p).convert("RGB")
        im.thumbnail((630, 370))
        xx = col * 640
        yy = row * 420
        sheet.paste(im, (xx, yy))
        draw.text((xx + 8, yy + 380), c["id"] + " " + tag, fill="black")
sheet.save(EVID / "derived-clip-review.jpg")
(EVID / "provenance.json").write_text(
    json.dumps(
        {
            "status": "derived_from_actual_local_capture",
            "boundary": (
                "Fictional household; real local prototype UI, local rules and SQLite. "
                "Alexa is a web text simulator. No live cloud or hardware."
            ),
            "clips": CLIPS,
            "stills": STILLS,
        },
        indent=2,
    ),
    encoding="utf-8",
)
