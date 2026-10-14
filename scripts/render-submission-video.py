"""Offline English PawTwin edit from actual capture attachments; no downloads."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import io
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import uuid
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PS = (
    Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
)
FFMPEG: Path | None = None
WIDTH, HEIGHT, FPS = 1920, 1080, 15
DEMO_EDIT = False
FONT_ROOT = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"


def ps_quote(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def run_ps(code: str, log: Path) -> str:
    encoded = base64.b64encode(code.encode("utf-16le")).decode("ascii")
    result = subprocess.run(
        [str(PS), "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded], capture_output=True
    )
    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")
    with log.open("a", encoding="utf-8") as stream:
        stream.write(stdout + stderr)
    if result.returncode:
        raise RuntimeError(f"Windows media operation failed ({result.returncode}); see {log}")
    return stdout


ASYNC_PS = r"""
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$operationMethod=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetGenericArguments().Length -eq 1 -and
    $_.GetParameters().Length -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1
function Wait-Operation($operation,$type) {
    $task=$operationMethod.MakeGenericMethod($type).Invoke($null,@($operation))
    $task.GetAwaiter().GetResult()
}
$progressMethod=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetGenericArguments().Length -eq 1 -and
    $_.GetParameters().Length -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncActionWithProgress`1'
} | Select-Object -First 1
function Wait-Progress($operation) {
    $task=$progressMethod.MakeGenericMethod([double]).Invoke($null,@($operation))
    $task.GetAwaiter().GetResult()
}
$storageType=[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
"""


def synthesize(texts: list[str], output: Path, log: Path) -> list[Path]:
    items = [
        {"text": text, "path": str(output / f"voice-{index:02d}.wav")}
        for index, text in enumerate(texts)
    ]
    data = base64.b64encode(json.dumps(items, ensure_ascii=False).encode("utf-8")).decode("ascii")
    code = (
        r"""
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Add-Type -AssemblyName System.Speech
$voice=New-Object System.Speech.Synthesis.SpeechSynthesizer
$english=$voice.GetInstalledVoices() | Where-Object {
    $_.Enabled -and $_.VoiceInfo.Culture.Name -eq 'en-US'
} | Select-Object -First 1
if(-not $english){throw 'An installed en-US SAPI voice is required; no voice is downloaded.'}
$voice.SelectVoice($english.VoiceInfo.Name)
$voice.Rate=1
$voice.Volume=90
$bits=[System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen
$channels=[System.Speech.AudioFormat.AudioChannel]::Mono
$format=New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(22050,$bits,$channels)
"""
        + f"$data='{data}'\n"
        + "$items=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($data))"
        + " | ConvertFrom-Json\n"
        + r"""
foreach($item in $items){
    $voice.SetOutputToWaveFile($item.path,$format)
    $voice.Speak($item.text)
    $voice.SetOutputToNull()
}
Write-Output ('SAPI voice: '+$english.VoiceInfo.Name)
$voice.Dispose()
"""
    )
    run_ps(code, log)
    return [Path(item["path"]) for item in items]


def read_wave(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as source:
        if source.getsampwidth() != 2 or source.getnchannels() != 1:
            raise ValueError("Expected mono, 16-bit PCM narration")
        return np.frombuffer(
            source.readframes(source.getnframes()), dtype="<i2"
        ).copy(), source.getframerate()


def write_wave(path: Path, samples: np.ndarray, rate: int) -> None:
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(rate)
        target.writeframes(np.asarray(samples, dtype="<i2").tobytes())


def riff_chunk(kind: bytes, data: bytes) -> bytes:
    return kind + struct.pack("<I", len(data)) + data + (b"\0" if len(data) % 2 else b"")


def riff_list(kind: bytes, data: bytes) -> bytes:
    return riff_chunk(b"LIST", kind + data)


def write_avi(path: Path, images, frame_count: int, audio: np.ndarray, rate: int) -> None:
    """Write standard AVI with real MJPEG frames and interleaved PCM narration."""
    block_align, audio_rate = 2, rate * 2
    avih = struct.pack(
        "<14I",
        round(1_000_000 / FPS),
        8_000_000,
        0,
        0x10,
        frame_count,
        0,
        2,
        WIDTH * HEIGHT * 3,
        WIDTH,
        HEIGHT,
        0,
        0,
        0,
        0,
    )
    video_header = struct.pack(
        "<4s4sIHH8I4h",
        b"vids",
        b"MJPG",
        0,
        0,
        0,
        0,
        1,
        FPS,
        0,
        frame_count,
        WIDTH * HEIGHT * 3,
        0xFFFFFFFF,
        0,
        0,
        0,
        WIDTH,
        HEIGHT,
    )
    bitmap = struct.pack(
        "<IiiHH4sIiiII", 40, WIDTH, HEIGHT, 1, 24, b"MJPG", WIDTH * HEIGHT * 3, 0, 0, 0, 0
    )
    audio_header = struct.pack(
        "<4s4sIHH8I4h",
        b"auds",
        b"\0" * 4,
        0,
        0,
        0,
        0,
        block_align,
        audio_rate,
        0,
        len(audio),
        audio_rate,
        0xFFFFFFFF,
        block_align,
        0,
        0,
        0,
        0,
    )
    audio_format = struct.pack("<HHIIHHH", 1, 1, rate, audio_rate, block_align, 16, 0)
    header = riff_list(
        b"hdrl",
        riff_chunk(b"avih", avih)
        + riff_list(b"strl", riff_chunk(b"strh", video_header) + riff_chunk(b"strf", bitmap))
        + riff_list(b"strl", riff_chunk(b"strh", audio_header) + riff_chunk(b"strf", audio_format)),
    )
    index = []
    with path.open("xb") as stream:
        stream.write(b"RIFF\0\0\0\0AVI " + header)
        movi_start = stream.tell()
        stream.write(b"LIST\0\0\0\0movi")
        for frame_index, jpeg in enumerate(images):
            if frame_index >= frame_count:
                raise ValueError("Too many generated frames")
            for kind, flags, payload in (
                (b"00dc", 0x10, jpeg),
                (
                    b"01wb",
                    0,
                    audio[round(frame_index * rate / FPS) : round((frame_index + 1) * rate / FPS)]
                    .astype("<i2")
                    .tobytes(),
                ),
            ):
                index.append(
                    struct.pack("<4sIII", kind, flags, stream.tell() - movi_start - 8, len(payload))
                )
                stream.write(riff_chunk(kind, payload))
        if len(index) != frame_count * 2:
            raise ValueError("Missing generated frames")
        movi_end = stream.tell()
        stream.write(riff_chunk(b"idx1", b"".join(index)))
        end = stream.tell()
        stream.seek(movi_start + 4)
        stream.write(struct.pack("<I", movi_end - movi_start - 8))
        stream.seek(4)
        stream.write(struct.pack("<I", end - 8))


def winrt(name: str, assembly: str) -> str:
    return f"[{name},{assembly},ContentType=WindowsRuntime]"


def transcode(source: Path, target: Path, log: Path, *, audio_only=False) -> dict:
    if target.exists():
        raise FileExistsError(target)
    target.touch()
    profile_type = winrt("Windows.Media.MediaProperties.MediaEncodingProfile", "Windows.Media")
    quality_name = "AudioEncodingQuality" if audio_only else "VideoEncodingQuality"
    quality_type = winrt("Windows.Media.MediaProperties." + quality_name, "Windows.Media")
    profile = (
        "$profileType::CreateWav($qualityType::High)"
        if audio_only
        else ("$profileType::CreateMp4($qualityType::HD1080p)")
    )
    prepared_type = winrt("Windows.Media.Transcoding.PrepareTranscodeResult", "Windows.Media")
    properties_type = winrt("Windows.Storage.FileProperties.VideoProperties", "Windows.Storage")
    code = (
        ASYNC_PS
        + rf"""
$source=Wait-Operation ($storageType::GetFileFromPathAsync({ps_quote(source)})) $storageType
$target=Wait-Operation ($storageType::GetFileFromPathAsync({ps_quote(target)})) $storageType
$profileType={profile_type}
$qualityType={quality_type}
$preparedType={prepared_type}
$propertiesType={properties_type}
$profile={profile}
"""
    )
    if not audio_only:
        code += (
            f"$profile.Video.Width={WIDTH}; $profile.Video.Height={HEIGHT}\n"
            f"$profile.Video.FrameRate.Numerator={FPS}; $profile.Video.FrameRate.Denominator=1\n"
            "$profile.Video.Bitrate=4000000\n"
            "$profile.Audio.ChannelCount=1; $profile.Audio.SampleRate=44100\n"
            "$profile.Audio.Bitrate=96000\n"
        )
    else:
        code += (
            "$profile.Audio.ChannelCount=1; $profile.Audio.SampleRate=44100\n"
            "$profile.Audio.BitsPerSample=16\n"
        )
    code += r"""
$transcoder=New-Object Windows.Media.Transcoding.MediaTranscoder
$transcoder.HardwareAccelerationEnabled=$false
$operation=$transcoder.PrepareFileTranscodeAsync($source,$target,$profile)
$prepared=Wait-Operation $operation $preparedType
if(-not $prepared.CanTranscode){throw ('Cannot transcode: '+$prepared.FailureReason)}
Wait-Progress ($prepared.TranscodeAsync())
$properties=Wait-Operation ($target.Properties.GetVideoPropertiesAsync()) $propertiesType
$actual=Wait-Operation ($profileType::CreateFromFileAsync($target)) $profileType
[ordered]@{
    duration_seconds=$properties.Duration.TotalSeconds
    width=$properties.Width
    height=$properties.Height
    bitrate=$properties.Bitrate
    video_codec=$actual.Video.Subtype
    audio_codec=$actual.Audio.Subtype
    audio_channels=$actual.Audio.ChannelCount
    audio_sample_rate=$actual.Audio.SampleRate
    audio_bitrate=$actual.Audio.Bitrate
} | ConvertTo-Json -Compress
"""
    stdout = run_ps(code, log)
    lines = [line for line in stdout.splitlines() if line.startswith("{")]
    if not lines or target.stat().st_size == 0:
        raise RuntimeError("Native transcoder did not provide an output/metadata")
    return json.loads(lines[-1])


def font(size: int, bold=False):
    return ImageFont.truetype(str(FONT_ROOT / ("segoeuib.ttf" if bold else "segoeui.ttf")), size)


def extract_frames(source: Path, items: list[tuple[float, Path]], log: Path) -> None:
    """Decode actual H.264 output through installed Windows MediaComposition."""
    # Large WinRT frame payloads exceed Windows' 32K process command-line
    # limit when encoded as UTF-16/base64. Bound each invocation, preserving
    # the caller's unique paths and times without re-encoding the video.
    if len(items) > 8:
        for offset in range(0, len(items), 8):
            extract_frames(source, items[offset : offset + 8], log)
        return
    payload = base64.b64encode(
        json.dumps([{"time": time, "path": str(path)} for time, path in items]).encode()
    ).decode()
    code = (
        ASYNC_PS
        + rf"""
$file=Wait-Operation ($storageType::GetFileFromPathAsync({ps_quote(source)})) $storageType
$clipType=[Windows.Media.Editing.MediaClip,Windows.Media.Editing,ContentType=WindowsRuntime]
$clip=Wait-Operation ($clipType::CreateFromFileAsync($file)) $clipType
$compositionType=[Windows.Media.Editing.MediaComposition,Windows.Media.Editing,ContentType=WindowsRuntime]
$composition=New-Object $compositionType
$references=@(
    "$env:WINDIR\System32\WinMetadata\Windows.Foundation.winmd",
    "$env:WINDIR\System32\WinMetadata\Windows.Media.winmd",
    ([Reflection.Assembly]::Load(
        'System.Runtime, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a'
    ).Location),
    ([System.WindowsRuntimeSystemExtensions].Assembly.Location)
)
$provider=New-Object Microsoft.CSharp.CSharpCodeProvider
$parameters=New-Object System.CodeDom.Compiler.CompilerParameters
$parameters.GenerateInMemory=$true
foreach($reference in $references){{ [void]$parameters.ReferencedAssemblies.Add($reference) }}
$helper=@'
public static class ClipCollection {{
    public static void Add(Windows.Media.Editing.MediaComposition composition,
                           Windows.Media.Editing.MediaClip clip) {{
        composition.Clips.Add(clip);
    }}
}}
'@
$compiled=$provider.CompileAssemblyFromSource($parameters,$helper)
if($compiled.Errors.HasErrors){{throw ($compiled.Errors | Out-String)}}
$add=$compiled.CompiledAssembly.GetType('ClipCollection').GetMethod('Add')
[void]$add.Invoke($null,@($composition.PSObject.BaseObject,$clip.PSObject.BaseObject))
$items=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{payload}')) | ConvertFrom-Json
foreach($item in $items){{
    $precision=[Windows.Media.Editing.VideoFramePrecision]::NearestFrame
    $imageType=[Windows.Graphics.Imaging.ImageStream,Windows.Graphics,ContentType=WindowsRuntime]
    $operation=$composition.GetThumbnailAsync(
        [TimeSpan]::FromSeconds($item.time),1920,1080,$precision
    )
    $image=Wait-Operation $operation $imageType
    $stream=[System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($image)
    $target=[IO.File]::Open($item.path,[IO.FileMode]::CreateNew)
    $stream.CopyTo($target)
    $target.Dispose(); $stream.Dispose(); $image.Dispose()
}}
Write-Output ('Decoded actual MP4 frames: '+$items.Count)
"""
    )
    run_ps(code, log)


def wrapped(draw, text, x, y, max_width, text_font, fill, leading=1.35):
    words = text.split()
    line = ""
    for word in words:
        trial = (line + " " + word).strip()
        if line and draw.textlength(trial, font=text_font) > max_width:
            draw.text((x, y), line, font=text_font, fill=fill)
            y += round(text_font.size * leading)
            line = word
        else:
            line = trial
    if line:
        draw.text((x, y), line, font=text_font, fill=fill)
        y += round(text_font.size * leading)
    return y


def compose(
    screenshot: Image.Image,
    title: str,
    subtitle: str,
    bullets: list[str],
    narration: str,
    number: int,
    total: int,
) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#F4F3EB")
    draw = ImageDraw.Draw(image)
    draw.text((64, 28), "PAWTWIN  /  HOME TOGETHER", font=font(23, True), fill="#4D6B50")
    draw.text((64, 68), title, font=font(46, True), fill="#243E31")
    draw.text((64, 130), subtitle, font=font(24), fill="#66705E")
    draw.rounded_rectangle(
        (64, 185, 1320, 893), radius=18, fill="#FFFFFF", outline="#D8DECF", width=2
    )
    view = screenshot.convert("RGB")
    view.thumbnail((1242, 694), Image.Resampling.LANCZOS)
    image.paste(view, (64 + (1256 - view.width) // 2, 192 + (694 - view.height) // 2))
    draw.rounded_rectangle((1350, 185, 1856, 893), radius=18, fill="#E5EEDD")
    draw.text((1384, 218), "WHAT THIS PROVES", font=font(22, True), fill="#4D6B50")
    y = 273
    for bullet in bullets:
        y = wrapped(draw, bullet, 1384, y, 436, font(31, True), "#2A4534") + 28
    draw.rounded_rectangle((64, 918, 1856, 1032), radius=16, fill="#243E31")
    bottom = wrapped(draw, narration, 92, 935, 1736, font(26), "#FFFFFF", leading=1.28)
    if bottom > 1020:
        raise ValueError(f"Subtitle overflow: {narration}")
    draw.text(
        (64, 1044),
        (
            "LOCAL PROTOTYPE  |  WEB SIMULATION  |  FICTIONAL DEMONSTRATION DATA"
            if DEMO_EDIT
            else "LOCAL REVIEW DEMO  |  local_rules  |  ENGLISH SAPI VOICE  |  AWS UNVERIFIED"
        ),
        font=font(17),
        fill="#67735F",
    )
    draw.text((1780, 1040), f"{number:02d}/{total:02d}", font=font(22, True), fill="#4D6B50")
    return image


def jpeg_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90, subsampling=2)
    return buffer.getvalue()


def extract_raw_sequence(source: Path, start: float, duration: float, target: Path, log: Path):
    if FFMPEG is None:
        raise RuntimeError("A replay needs installed FFmpeg; provide --ffmpeg. No download occurs.")
    target.mkdir(parents=True)
    command = [
        str(FFMPEG),
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(start),
        "-i",
        str(source),
        "-t",
        str(duration),
        "-r",
        str(FPS),
        "-an",
        "-c:v",
        "png",
        "-f",
        "image2",
        str(target / "frame-%04d.png"),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    with log.open("a", encoding="utf-8") as stream:
        stream.write("Raw clip decode: " + " ".join(command) + "\n" + result.stderr)
    if result.returncode:
        raise RuntimeError(f"Actual capture decode failed: {source}")
    frames = sorted(target.glob("frame-*.png"))
    if len(frames) < round(duration * FPS) - 1:
        raise RuntimeError("Actual capture did not provide the requested clip duration")
    return frames


def contact_sheet(frames: list[tuple[str, Path]], output: Path):
    sheet = Image.new("RGB", (1280, math.ceil(len(frames) / 2) * 438), "#F4F3EB")
    draw = ImageDraw.Draw(sheet)
    for index, (label, path) in enumerate(frames):
        view = Image.open(path).convert("RGB")
        view.thumbnail((640, 400))
        x, y = (index % 2) * 640, (index // 2) * 438
        sheet.paste(view, (x, y))
        draw.text((x + 10, y + 402), label, font=font(22), fill="#243E31")
    sheet.save(output)


STORY = [
    {
        "title": "One pet. A shared daily story.",
        "subtitle": "Actual product page / Interface illustrations are labelled",
        "source": "00-product.png",
        "proofs": ["Current product page", "Shared household care", "Local demonstration"],
        "sentences": [
            "Paw Twin gives family members one shared pet record for everyday care.",
            (
                "The product page introduces the idea; this review then follows two "
                "separate accounts with fictional demonstration data."
            ),
        ],
    },
    {
        "title": "Start with records people can inspect.",
        "subtitle": "Actual weekly report / Fictional measurement samples",
        "source": "02-growth.png",
        "proofs": ["1.20 to 1.35 kg", "150 g / 12.5% / 7 days", "Source IDs and missing intake"],
        "sentences": [
            (
                "The owner records sample weights of one point two and one point three "
                "five kilograms, seven days apart."
            ),
            (
                "The report calculates a hundred fifty gram increase, shows its sources, "
                "and keeps unrecorded intake unknown."
            ),
        ],
    },
    {
        "title": "An owner confirms the shared memory.",
        "subtitle": "Actual owner confirmation / Database memory",
        "source": "08-memory-confirmed.png",
        "proofs": [
            "Candidate cannot be reused",
            "Explicit owner confirmation",
            "Confirmed database memory",
        ],
        "sentences": [
            (
                "The owner saves a preference candidate: Mochi likes a feather toy and "
                "rests after meals."
            ),
            (
                "The other account cannot use the candidate; explicit confirmation makes "
                "it available as database memory."
            ),
        ],
    },
    {
        "title": "A second account sees the same context.",
        "subtitle": "Actual independent Alexa web simulator / Source details",
        "source": "03-assistant.png",
        "proofs": [
            "Separate authenticated account",
            "Confirmed preference source",
            "Local rules / no model call",
        ],
        "sentences": [
            "The carer opens the independent Alexa web simulator and asks what Mochi likes.",
            (
                "Its actual reply cites the confirmed record and shows local rules, with "
                "no live model request."
            ),
        ],
    },
    {
        "title": "A new page session reads current records.",
        "subtitle": "Actual new-session result / Shared records persist",
        "source": "13-alexa-new-session.png",
        "proofs": ["Transcript cleared", "Record retained", "New answer reads current context"],
        "sentences": [
            "Starting a new session clears the page conversation, while household records remain.",
            (
                "The next question reads the current confirmed preference again; this is "
                "not cloud memory extraction."
            ),
        ],
    },
    {
        "title": "A request becomes a reviewable draft.",
        "subtitle": "Actual Alexa care draft / Selected browser-local time",
        "source": "09-alexa-draft.png",
        "proofs": ["Request: arrange play", "Rule-generated draft", "No task yet"],
        "sentences": [
            "The owner asks the simulator to arrange play and checks its rule-generated draft.",
            (
                "The owner selects a specific time; asking or preparing the draft does "
                "not create a task."
            ),
        ],
    },
    {
        "title": "Preparation still requires confirmation.",
        "subtitle": "Actual prepared proposal / No task before confirmation",
        "source": "10-alexa-pending.png",
        "proofs": ["Current context version", "Selected time", "Explicit confirmation required"],
        "sentences": [
            "Preparing the proposal preserves the draft and its current context version.",
            "The local check verifies that no care task exists at this stage.",
        ],
    },
    {
        "title": "Confirmation creates manual care.",
        "subtitle": "Actual confirmed result / Waiting for a person",
        "source": "11-alexa-confirmed.png",
        "proofs": ["Confirmed proposal", "One shared manual task", "No device execution"],
        "sentences": [
            "Only explicit owner confirmation creates the shared manual care task.",
            (
                "The visible result says it is arranged and awaiting a person, without "
                "executing a feeder."
            ),
        ],
    },
    {
        "title": "A second person completes the handoff.",
        "subtitle": "Actual carer task result / Actor checked in evidence",
        "source": "04-care.png",
        "proofs": ["Carer claims task", "Carer records completion", "Manual-care provenance"],
        "sentences": [
            "The carer claims the task and records completion through the second account.",
            (
                "Household activity and captured evidence identify that account; this "
                "does not prove physical care occurred."
            ),
        ],
    },
    {
        "title": "The simulator sees the completed result.",
        "subtitle": "Actual latest-completion answer / Shared occurrence source",
        "source": "12-alexa-result.png",
        "proofs": ["Same household record", "Completed task title", "Occurrence source ID"],
        "sentences": [
            "Back in the simulator, the carer asks what was recently completed.",
            "The answer names the manual care record and cites the actual completion occurrence.",
        ],
    },
    {
        "title": "Close the loop with the daily report.",
        "subtitle": "Actual daily report after completion / Unknown remains unknown",
        "source": "05-daily.png",
        "proofs": ["1 manual completion", "Report sources", "Intake remains unrecorded"],
        "sentences": [
            "The owner generates today’s report, which counts one completed manual care task.",
            "Measured intake remains unrecorded, and the report does not invent a health outcome.",
        ],
    },
    {
        "title": "Delete a memory. Check a new answer.",
        "subtitle": "Actual new Alexa answer after deletion",
        "source": "06-deleted-memory.png",
        "proofs": [
            "Confirmed preference deleted",
            "New answer omits it",
            "Deleted source ID absent",
        ],
        "sentences": [
            "After the owner deletes the preference, the carer asks again in a fresh page session.",
            "The next answer no longer cites that record; previous replies remain historical.",
        ],
    },
    {
        "title": "A verified local loop. Live work remains.",
        "subtitle": "Local English review / No publication or submission",
        "source": "01-home.png",
        "proofs": [
            "Local rules / SQLite",
            "Alexa and hardware simulated",
            "Live integration unverified",
        ],
        "sentences": [
            (
                "This capture uses local accounts, database memory, rule drafts, and "
                "confirmed manual tasks."
            ),
            (
                "The AWS account review has cleared, but this demo makes no live model, "
                "Alexa, hardware, or cloud deployment claim."
            ),
        ],
    },
]


def srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def sample_stats(samples: np.ndarray, rate: int) -> dict:
    values = samples.astype(np.int32)
    peak = int(np.max(np.abs(values)))
    rms = float(np.sqrt(np.mean(values.astype(np.float64) ** 2)))
    nonzero = np.flatnonzero(values)
    return {
        "duration_seconds": len(samples) / rate,
        "sample_rate": rate,
        "peak_pcm16": peak,
        "peak_dbfs": round(20 * math.log10(peak / 32768), 3) if peak else None,
        "rms_dbfs": round(20 * math.log10(rms / 32768), 3) if rms else None,
        "clipped_samples": int(np.count_nonzero(np.abs(values) >= 32767)),
        "last_nonzero_seconds": int(nonzero[-1]) / rate if len(nonzero) else None,
    }


def write_manifest(output: Path) -> None:
    manifest = output / "sha256-manifest.json"
    files = [
        {
            "path": str(path.relative_to(output)),
            "size": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(output.rglob("*"))
        if path.is_file() and path != manifest
    ]
    manifest.write_text(json.dumps({"files": files}, indent=2), encoding="utf-8")


def build_review(source: Path, output: Path, scratch: Path, log: Path, evidence: dict):
    duration = 170.0
    sentences = [text for scene in STORY for text in scene["sentences"]]
    waves = synthesize(sentences, scratch, log)
    voice_samples = [read_wave(path) for path in waves]
    if {rate for _, rate in voice_samples} != {22050}:
        raise ValueError("Unexpected SAPI sample format")
    rate = 22050
    voice_lengths = [len(samples) / rate for samples, _ in voice_samples]
    minimums = []
    for index in range(len(STORY)):
        minimums.append(sum(voice_lengths[index * 2 : index * 2 + 2]) + 1.25)
    if sum(minimums) >= duration:
        raise ValueError(f"Narration needs {sum(minimums):.2f}s; refuse to truncate it")
    extra = (duration - sum(minimums)) / len(STORY)
    audio = np.zeros(round(duration * rate), dtype="<i2")
    timeline, subtitles = [], []
    cursor = 0.0
    for scene_index, (scene, minimum) in enumerate(zip(STORY, minimums, strict=True)):
        end = round((cursor + minimum + extra) * FPS) / FPS
        if scene_index == len(STORY) - 1:
            end = duration
        start = cursor
        voice_cursor = start + 0.35
        cues = []
        for sentence_index, text in enumerate(scene["sentences"]):
            samples, _ = voice_samples[scene_index * 2 + sentence_index]
            voice_end = voice_cursor + len(samples) / rate
            offset = round(voice_cursor * rate)
            audio[offset : offset + len(samples)] = samples
            cue = {"start": voice_cursor, "end": voice_end, "text": text}
            cues.append(cue)
            subtitles.append(cue)
            voice_cursor = voice_end + 0.2
        if cues[-1]["end"] > end - 0.5:
            raise ValueError("A scene would cut off its final sentence")
        timeline.append(
            {
                "number": scene_index + 1,
                "start": start,
                "end": end,
                "title": scene["title"],
                "source": scene["source"],
                "clip": scene.get("clip"),
                "proofs": scene["proofs"],
                "cues": cues,
            }
        )
        cursor = end
    write_wave(output / "narration.en.wav", audio, rate)
    (output / "narration.en.txt").write_text(
        "\n\n".join(scene["title"] + "\n" + " ".join(scene["sentences"]) for scene in STORY),
        encoding="utf-8",
    )
    (output / "captions.en.srt").write_text(
        "\n\n".join(
            f"{index + 1}\n{srt_time(cue['start'])} --> {srt_time(cue['end'])}\n{cue['text']}"
            for index, cue in enumerate(subtitles)
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "timeline.json").write_text(
        json.dumps(
            {
                "title": "PawTwin local English review demo",
                "duration_seconds": duration,
                "source_capture": str(source.relative_to(ROOT)),
                "source_captured_at": evidence["captured_at"],
                "backend": "local_rules",
                "cloud_calls": 0,
                "presentation": (
                    "Actual WebM operation clips with actual screenshot result holds"
                    if any(scene.get("clip") for scene in STORY)
                    else "Complete actual current screenshots; no guessed WebM replay cuts"
                ),
                "replays": [
                    {
                        "scene": item["number"],
                        "role": item["clip"]["role"],
                        "source_start": item["clip"]["start"],
                        "source_duration": item["clip"]["duration"],
                        "output_start": item["start"],
                        "output_visible_duration": min(
                            item["clip"]["duration"], item["end"] - item["start"]
                        ),
                        "speed": 1.0,
                    }
                    for item in timeline
                    if item["clip"]
                ],
                "screenshot_timing_boundary": evidence.get("timing_boundary"),
                "scenes": timeline,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    clip_frames = {}
    for index, scene in enumerate(STORY):
        if clip := scene.get("clip"):
            clip_frames[index] = extract_raw_sequence(
                source / (clip["role"] + ".webm"),
                clip["start"],
                clip["duration"],
                scratch / f"{index + 1:02d}-{clip['role']}-frames",
                log,
            )
    frame_dir = output / "review-frames"
    frame_dir.mkdir()
    prepared = []
    for scene_index, scene in enumerate(STORY):
        image = Image.open(source / scene["source"]).convert("RGB")
        prepared.append(image)
        preview = compose(
            image,
            scene["title"],
            scene["subtitle"],
            scene["proofs"],
            scene["sentences"][0],
            scene_index + 1,
            len(STORY),
        )
        preview.save(frame_dir / f"planned-{scene_index + 1:02d}.png")
    print("Planned duration: 170s. Real source frames and English captions prepared.", flush=True)

    def frames():
        scene_index, jpeg_cache = 0, {}
        for frame_index in range(round(duration * FPS)):
            time = frame_index / FPS
            while time >= timeline[scene_index]["end"] and scene_index < len(STORY) - 1:
                scene_index += 1
            scene, item = STORY[scene_index], timeline[scene_index]
            caption = scene["sentences"][-1]
            for cue in item["cues"]:
                if time < cue["end"]:
                    caption = cue["text"]
                    break
            local_frame = round((time - item["start"]) * FPS)
            raw = clip_frames.get(scene_index)
            if raw and 0 <= local_frame < len(raw):
                image = Image.open(raw[local_frame]).convert("RGB")
                yield jpeg_bytes(
                    compose(
                        image,
                        scene["title"],
                        scene["subtitle"],
                        scene["proofs"],
                        caption,
                        scene_index + 1,
                        len(STORY),
                    )
                )
            else:
                key = (scene_index, caption)
                if key not in jpeg_cache:
                    jpeg_cache[key] = jpeg_bytes(
                        compose(
                            prepared[scene_index],
                            scene["title"],
                            scene["subtitle"],
                            scene["proofs"],
                            caption,
                            scene_index + 1,
                            len(STORY),
                        )
                    )
                yield jpeg_cache[key]

    avi = scratch / "intermediate.avi"
    write_avi(avi, frames(), round(duration * FPS), audio, rate)
    print("Intermediate frames and narration assembled. Encoding native H.264/AAC.", flush=True)
    mp4 = output / "pawtwin-local-review.en.mp4"
    metadata = transcode(avi, mp4, log)
    if not 165 <= metadata["duration_seconds"] <= 175:
        raise ValueError("Actual MP4 is outside the requested 2:45–2:55 window")
    if metadata["video_codec"] != "H264" or metadata["audio_codec"] != "AAC":
        raise ValueError("Unexpected actual output codecs")
    decoded = scratch / "decoded-audio.wav"
    transcode(mp4, decoded, log, audio_only=True)
    decoded_samples, decoded_rate = read_wave(decoded)
    actual_items = [
        (item["cues"][0]["start"] + 1.0, frame_dir / f"actual-{item['number']:02d}.jpg")
        for item in timeline
    ]
    for index in clip_frames:
        clip = STORY[index]["clip"]
        visible = min(clip["duration"], timeline[index]["end"] - timeline[index]["start"])
        for tag, offset in (
            ("start", min(0.15, visible / 4)),
            ("middle", visible / 2),
            ("end", max(0, visible - 0.15)),
        ):
            actual_items.append(
                (
                    timeline[index]["start"] + offset,
                    frame_dir / f"actual-replay-{index + 1:02d}-{clip['role']}-{tag}.jpg",
                )
            )
    extract_frames(mp4, actual_items, log)
    contact_sheet(
        [
            (f"Scene {index + 1:02d} / {seconds:.2f}s", path)
            for index, (seconds, path) in enumerate(actual_items)
        ],
        frame_dir / "actual-contact-sheet.png",
    )
    stats = sample_stats(decoded_samples, decoded_rate)
    if stats["clipped_samples"] or abs(stats["duration_seconds"] - duration) > 0.1:
        raise ValueError("Actual decoded audio is clipped or has an unexpected duration")
    verification = {
        "actual_mp4": metadata,
        "source_wav": sample_stats(audio, rate),
        "actual_decoded_aac": stats,
        "sentence_count": len(sentences),
        "all_sentences_fit": True,
        "subtitle_overflow": False,
        "actual_frame_count": len(actual_items),
        "human_audio_review": "not_performed",
        "picture_review": "actual decoded frames require visual review",
        "source_backend": evidence["backend"],
        "source_cloud_calls": evidence["cloud_calls"],
        "presentation": (
            "Actual WebM operation clips with actual screenshot result holds"
            if clip_frames
            else "Actual current screenshot edit; raw WebM retained separately"
        ),
        "replay_scene_count": len(clip_frames),
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "pillow_version": Image.__version__,
    }
    (output / "verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    (output / "source-manifest.json").write_text(
        json.dumps(
            {
                "capture": str(source.relative_to(ROOT)),
                "files": [
                    {
                        "path": path.name,
                        "size": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                    for path in sorted(source.iterdir())
                    if path.is_file()
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    write_manifest(output)
    print(
        json.dumps({"output": str(output), "metadata": metadata, "decoded_audio": stats}),
        flush=True,
    )


def main():
    global FFMPEG, DEMO_EDIT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture", type=Path, default=ROOT / "docs/evidence/hackathon-capture/2026-10-11-final"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--clip-map",
        type=Path,
        help="Visually calibrated WebM source ranges, bound to source SHA-256",
    )
    parser.add_argument("--demo-edit", action="store_true", help="Use public-facing demo labels")
    parser.add_argument(
        "--ffmpeg",
        type=Path,
        help="Installed FFmpeg executable for optional raw replay decoding",
    )
    args = parser.parse_args()
    DEMO_EDIT = args.demo_edit
    if DEMO_EDIT:
        STORY[0]["sentences"][1] = (
            "Here, two separate household accounts use fictional demonstration data "
            "to record, confirm, and hand over care."
        )
        STORY[4]["sentences"][1] = (
            "The next question reads the same confirmed preference, "
            "with its source available for inspection."
        )
        STORY[8]["sentences"][1] = (
            "The shared activity log identifies who recorded completion, "
            "so the next family member can check the handoff."
        )
        STORY[10]["sentences"] = [
            "The daily report now counts one completed manual care task.",
            "Actual intake remains unrecorded, and the report does not invent a health outcome.",
        ]
        STORY[-1]["title"] = "Shared care, with a clear boundary."
        STORY[-1]["subtitle"] = "Working local prototype / Platform integrations not shown"
        STORY[-1]["sentences"][1] = (
            "Alexa and devices are simulated here, while the shared records, "
            "confirmations, and report calculations run locally."
        )
    if args.ffmpeg:
        FFMPEG = args.ffmpeg.resolve()
        if not FFMPEG.is_file():
            parser.error("--ffmpeg must name an existing installed executable")
    else:
        installed = shutil.which("ffmpeg")
        candidates = sorted(
            (Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright").glob(
                "ffmpeg-*/ffmpeg-win64.exe"
            )
        )
        FFMPEG = Path(installed) if installed else (candidates[-1] if candidates else None)
    if os.name != "nt":
        parser.error("This offline encoder requires Windows SAPI and Media Foundation")
    source = args.capture.resolve()
    clip_map = None
    if args.clip_map:
        clip_map = json.loads(args.clip_map.read_text(encoding="utf-8-sig"))
        known_sources = {scene["source"]: scene for scene in STORY}
        seen = set()
        for item in clip_map["clips"]:
            name, role = item["scene_source"], item["role"]
            if name not in known_sources or name in seen or role not in {"owner", "carer"}:
                raise ValueError("Clip map has an invalid or duplicate scene/role")
            seen.add(name)
            if not (math.isfinite(item["start"]) and math.isfinite(item["duration"])):
                raise ValueError("Clip times must be finite")
            if item["start"] < 0 or item["duration"] <= 0:
                raise ValueError("Clip map has invalid times")
            raw = source / f"{role}.webm"
            if hashlib.sha256(raw.read_bytes()).hexdigest() != clip_map["sources"][role]["sha256"]:
                raise ValueError("Clip map source hash does not match actual WebM")
            if item["start"] + item["duration"] > clip_map["sources"][role]["duration_seconds"]:
                raise ValueError("Clip range exceeds inspected WebM duration")
            known_sources[name]["clip"] = {
                "role": role,
                "start": item["start"],
                "duration": item["duration"],
            }
    build_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    output = (
        args.output or ROOT / "docs/evidence/submission-video-2026-10-11" / build_id
    ).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Refusing a nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    scratch = ROOT / ".cache/submission-video" / build_id
    scratch.mkdir(parents=True)
    log = output / "build.log"
    log.write_text("Offline source: " + str(source) + "\n", encoding="utf-8")
    if clip_map:
        (output / "clip-map.json").write_text(
            json.dumps(clip_map, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    evidence = json.loads((source / "demo-evidence.json").read_text(encoding="utf-8-sig"))
    if evidence["backend"] != "local_rules" or evidence["cloud_calls"] != 0:
        raise ValueError("This edit requires the labelled local-rules capture")
    if not args.smoke:
        if evidence.get("schema_version") != 2 or not evidence.get("alexa_care"):
            raise ValueError("Current edit requires the refreshed independent Alexa rehearsal")
        missing = [scene["source"] for scene in STORY if not (source / scene["source"]).is_file()]
        if missing:
            raise FileNotFoundError(f"Current capture screenshots missing: {missing}")
    if args.smoke:
        text = "Paw Twin. An offline video encoding check."
        waves = synthesize([text], scratch, log)
        samples, rate = read_wave(waves[0])
        duration = max(3, math.ceil(len(samples) / rate) + 1)
        audio = np.zeros(duration * rate, dtype="<i2")
        audio[: len(samples)] = samples
        write_wave(output / "narration.wav", audio, rate)
        screenshot = Image.open(source / "02-growth.png")
        frame = compose(
            screenshot,
            "Offline encoder check",
            "Actual capture: " + source.name,
            ["Real source screenshot", "SAPI English voice", "Native H.264 / AAC"],
            text,
            1,
            1,
        )
        frame.save(output / "review-frame.png")
        avi = scratch / "intermediate.avi"
        frame_count = duration * FPS
        jpeg = jpeg_bytes(frame)
        write_avi(avi, (jpeg for _ in range(frame_count)), frame_count, audio, rate)
        metadata = transcode(avi, output / "encoder-smoke.mp4", log)
        decoded = scratch / "decoded.wav"
        transcode(output / "encoder-smoke.mp4", decoded, log, audio_only=True)
        decoded_samples, decoded_rate = read_wave(decoded)
        metadata["decoded_audio_duration"] = len(decoded_samples) / decoded_rate
        metadata["decoded_audio_peak"] = int(np.max(np.abs(decoded_samples.astype(np.int32))))
        (output / "verification.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(json.dumps({"output": str(output), "metadata": metadata}))
    else:
        build_review(source, output, scratch, log, evidence)


if __name__ == "__main__":
    main()
