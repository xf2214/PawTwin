"""Build the complete film's continuous soundtrack, captions and source timing."""

import json
import math
import re
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent / "pawtwin-app/docs/evidence/submission-video-2026-10-15/fullfilm-01"
AUDIO = EVIDENCE / "audio/calm-take"
BIN = HERE / "node_modules/@remotion/compositor-win32-x64-msvc"
RATE = 48000
FPS = 30
LEAD = 0.6


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(args):
    return subprocess.run(
        [str(a) for a in args], check=True, capture_output=True, text=True, encoding="utf-8"
    )


def clean(s):
    return re.sub("[^a-z0-9]", "", s.lower())


def writewav(path, x, channels=1):
    assert np.isfinite(x).all() and np.abs(x).max() < 1
    with wave.open(str(path), "wb") as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(np.round(x * 32767).astype("<i2").tobytes())


data = json.loads((AUDIO / "narration-words.json").read_text(encoding="utf-8-sig"))
words = data["words"]
text = data["text"]


def find(phrase):
    wanted = clean(phrase)
    for i in range(len(words)):
        value = ""
        for j in range(i, len(words)):
            value += clean(words[j]["text"])
            if value == wanted:
                return i
            if len(value) > len(wanted):
                break
    raise ValueError(phrase)


def onset(phrase):
    return words[find(phrase)]["start"] + LEAD


def frame(t):
    return round(t * FPS)


anchors = {
    k: onset(p)
    for k, p in {
        "handoff": "Today Alex",
        "memory": "Emma adds",
        "memoryCheck": "She checks",
        "context": "Alex opens",
        "contextReply": "The reply uses",
        "draft": "Next Emma",
        "onlyConfirm": "Only her explicit",
        "complete": "Alex claims",
        "history": "His name",
        "report": "When Emma generates",
        "concierge": "Our scripted Pet",
        "miso": "Miso s example",
        "luna": "Luna s example",
        "preset": "These replies",
        "implementation": "The working prototype",
        "benefit": "For this family",
        "closing": "PawTwin Less repeating",
    }.items()
}
duration_frames = math.ceil(max(words[-1]["end"] + LEAD + 1.25, 140.904 + LEAD) * FPS)
duration = duration_frames / FPS
assert duration < 180
b = {k: frame(v - 0.12) for k, v in anchors.items()}
b["opening"] = 0
b["confirm"] = b["draft"] + frame(8.25)
b["proof"] = max(b["context"] + frame(6.05), b["contextReply"])
b["historyShot"] = b["complete"] + frame(10.7)
memory_delay = max(
    0,
    min(anchors["memoryCheck"] - anchors["memory"] - 1.5, (b["context"] - b["memory"]) / FPS - 7.1),
)
assert (b["complete"] - b["confirm"]) / FPS >= 10
assert (b["report"] - b["complete"]) / FPS >= 15.8
assert (b["concierge"] - b["report"]) / FPS >= 7.8
plan = {
    "fps": FPS,
    "durationInFrames": duration_frames,
    "durationSeconds": duration,
    "boundaries": b,
    "anchorSeconds": anchors,
    "memoryPlayAfter": round(memory_delay * FPS) / FPS,
    "sourceNarrationSeconds": 140.904,
    "leadingSeconds": LEAD,
    "trailingAfterLastWordSeconds": duration - (words[-1]["end"] + LEAD),
    "narrationContinuous": True,
    "insertedInternalPauses": [],
    "speechTimeStretch": False,
    "voice": "en-US-AvaMultilingualNeural",
    "providerRate": "-10%",
    "sceneDark": [
        "handoff",
        "context",
        "proof",
        "complete",
        "implementation",
        "benefit",
        "closing",
    ],
}
save(HERE / "src/fullfilm-plan.json", plan)
save(EVIDENCE / "timing-plan.json", plan)

# Match original punctuation to provider word timing through normalized character
# positions, so multiword provider boundaries do not change the submitted text.
tokens = list(re.finditer(r"\S+", text))
provider = "".join(clean(w["text"]) for w in words)
assert provider == clean(text), "Provider text mismatch"
word_spans = []
position = 0
for w in words:
    end = position + len(clean(w["text"]))
    word_spans.append((position, end, w))
    position = end
original = []
position = 0
for token in tokens:
    end = position + len(clean(token.group()))
    original.append((position, end, token.group()))
    position = end
groups = []
current = []
for token in original:
    length = len(" ".join(t[2] for t in current + [token]))
    if current and length > 57:
        groups.append(current)
        current = []
    current.append(token)
    phrase = " ".join(t[2] for t in current)
    if re.search(r"[.!?]$", token[2]) or (len(phrase) > 30 and re.search(r"[,;:]$", token[2])):
        groups.append(current)
        current = []
if current:
    groups.append(current)
cues = []
for group in groups:
    lo, hi = group[0][0], group[-1][1]
    matching = [w for start, end, w in word_spans if end > lo and start < hi]
    cues.append(
        {
            "text": " ".join(t[2] for t in group),
            "startMs": round((matching[0]["start"] + LEAD) * 1000),
            "endMs": round((matching[-1]["end"] + LEAD) * 1000 + 70),
            "timestampMs": None,
            "confidence": None,
        }
    )
for c, n in zip(cues, cues[1:], strict=False):
    c["endMs"] = min(c["endMs"], n["startMs"] - 1)
assert all(c["startMs"] < c["endMs"] for c in cues)
save(HERE / "src/fullfilm-captions.json", cues)
save(EVIDENCE / "captions-remotion.json", cues)

with wave.open(str(AUDIO / "narration-continuous.wav"), "rb") as f:
    assert (f.getnchannels(), f.getsampwidth(), f.getframerate()) == (1, 2, RATE)
    raw = np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.float64) / 32768
n = round(duration * RATE)
voice = np.zeros(n)
at = round(LEAD * RATE)
voice[at : at + len(raw)] = raw
# Original restrained instrumental bed, with sparse plucks and a soft harmonic
# pad. Its level stays constant under the continuous voice; no clause pumping.
music = np.zeros(n)
chords = [
    (48, 55, 59, 62, 64),
    (45, 52, 55, 60, 64),
    (41, 48, 52, 57, 60),
    (48, 55, 59, 62, 64),
    (43, 50, 55, 57, 62),
]


def add(sound, t):
    i = round(t * RATE)
    count = min(len(sound), n - i)
    if count > 0:
        music[i : i + count] += sound[:count]


def pluck(midi):
    t = np.arange(round(3.6 * RATE)) / RATE
    hz = 440 * 2 ** ((midi - 69) / 12)
    return (1 - np.exp(-t * 60)) * (
        np.sin(2 * np.pi * hz * t) * np.exp(-t * 2)
        + 0.12 * np.sin(4 * np.pi * hz * t) * np.exp(-t * 3)
    )


for phrase, start in enumerate(np.arange(0, duration, 6)):
    chord = chords[phrase % len(chords)]
    t = np.arange(round(6.8 * RATE)) / RATE
    envelope = np.clip(t / 1.7, 0, 1) * np.clip((6.8 - t) / 2.0, 0, 1)
    pad = sum(np.sin(2 * np.pi * 440 * 2 ** ((m - 69) / 12) * t) for m in chord[:3])
    add(0.005 * pad * envelope, float(start))
    for offset, degree in [(0, 2), (1.8, 4), (4.2, 3)]:
        add(0.04 * pluck(chord[degree] + 12), float(start + offset))
delay = round(0.31 * RATE)
music[delay:] += 0.12 * music[:-delay].copy()
t = np.arange(n) / RATE
music *= np.clip(t / 1.3, 0, 1) * np.clip((duration - t) / 2.0, 0, 1)
active = np.abs(voice) > 0.008
vrms = np.sqrt(np.mean(voice[active] ** 2))
mrms = np.sqrt(np.mean(music**2))
gain = min(
    vrms * 10 ** (-23 / 20) / mrms, np.abs(voice).max() * 10 ** (-21 / 20) / np.abs(music).max()
)
music *= gain
mix = voice + music
mix *= min(1, 0.88 / np.abs(mix).max())
writewav(AUDIO / "narration-timeline.wav", voice)
writewav(AUDIO / "original-music.wav", music)
source = AUDIO / "mix.stereo.wav"
writewav(source, np.column_stack([mix, mix]), 2)
first = run(
    [
        BIN / "ffmpeg.exe",
        "-hide_banner",
        "-i",
        source,
        "-af",
        "loudnorm=I=-16:TP=-1.8:LRA=9:print_format=json",
        "-f",
        "null",
        "-",
    ]
).stderr
(AUDIO / "normalize-pass1.log").write_text(first, encoding="utf-8")
meter = json.loads(re.search(r'\{\s*"input_i".*?\}', first, re.S).group(0))
filt = (
    "loudnorm=I=-16:TP=-1.8:LRA=9:linear=true:measured_I={input_i}:"
    "measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:"
    "offset={target_offset}:print_format=json"
).format(**meter)
final = AUDIO / "soundtrack-fullfilm.stereo.wav"
second = run(
    [
        BIN / "ffmpeg.exe",
        "-hide_banner",
        "-y",
        "-i",
        source,
        "-af",
        filt,
        "-ar",
        RATE,
        "-ac",
        2,
        "-c:a",
        "pcm_s16le",
        final,
    ]
).stderr
(AUDIO / "normalize-pass2.log").write_text(second, encoding="utf-8")
shutil.copyfile(final, HERE / "public/fullfilm/soundtrack.stereo.wav")
save(
    EVIDENCE / "audio-production.json",
    {
        "continuousSourceTake": True,
        "providerRate": "-10%",
        "sourceWords": len(words),
        "postSpeechTimeOrPitchProcessing": False,
        "internalEditedPauses": 0,
        "sourceSamplePositionsRetained": len(raw),
        "music": "Original locally synthesized sparse harmonic plucks and pad",
        "externalMusicDownloads": False,
        "musicRmsRelativeToActiveVoiceDb": float(20 * np.log10(np.sqrt(np.mean(music**2)) / vrms)),
        "stereoNormalizationTargetLufs": -16,
        "truePeakTargetDbtp": -1.8,
        "humanListeningReview": "not_performed",
    },
)
print(
    json.dumps(
        {
            "durationSeconds": duration,
            "frames": duration_frames,
            "boundaries": {k: round(v / FPS, 3) for k, v in b.items()},
            "memoryPlayAfter": plan["memoryPlayAfter"],
            "captionCues": len(cues),
        },
        indent=2,
    )
)
