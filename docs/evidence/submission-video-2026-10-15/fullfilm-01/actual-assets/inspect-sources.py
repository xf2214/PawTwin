import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

BASE = Path(
    r"C:\Users\11831\Desktop\hks\outputs\pawtwin-app\docs\evidence\hackathon-cinematic-capture-2026-10-15\attempt-03-native1920"
)
OUT = Path(__file__).parent
FF = Path(
    r"C:\Users\11831\Desktop\hks\outputs\pawtwin-video-studio-2026-10-15\node_modules\@remotion\compositor-win32-x64-msvc\ffmpeg.exe"
)
for role, times in [("owner", [96, 99, 102, 105, 108, 111, 114, 117, 120, 123, 126, 128.5])]:
    sheet = Image.new("RGB", (1920, 4 * 390), "white")
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(times):
        p = OUT / f"{role}-{t}.png"
        subprocess.run(
            [
                str(FF),
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                str(t),
                "-i",
                str(BASE / f"{role}.webm"),
                "-frames:v",
                "1",
                "-an",
                "-c:v",
                "png",
                "-y",
                str(p),
            ],
            check=True,
        )
        im = Image.open(p).convert("RGB")
        im.thumbnail((640, 360))
        x = (i % 3) * 640
        y = (i // 3) * 390
        sheet.paste(im, (x, y))
        d.text((x + 10, y + 364), f"{role} {t}s", fill="black")
    sheet.save(OUT / f"{role}-contact.jpg")
