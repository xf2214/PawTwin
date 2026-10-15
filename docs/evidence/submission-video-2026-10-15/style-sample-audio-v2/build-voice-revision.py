"""Retime the approved sample around one continuous public fictional narration.

Retains every source PCM sample. Only inserts pauses between complete phrases
when normal-speed UI playback needs a result hold. No time or pitch processing.
"""

import importlib.util
import json
import math
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
APP = HERE.parent / "pawtwin-app"
OUT = APP / "docs/evidence/submission-video-2026-10-15/style-sample-audio-v2"
AUDIO = OUT / "audio/story-take"
BIN = HERE / "node_modules/@remotion/compositor-win32-x64-msvc"
RATE = 48000
FPS = 30


def run(args):
    return subprocess.run(
        [str(a) for a in args], check=True, capture_output=True, text=True, encoding="utf-8"
    )


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def wav(path, x, channels=1):
    assert np.isfinite(x).all() and np.abs(x).max() < 1
    with wave.open(str(path), "wb") as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(np.round(x * 32767).astype("<i2").tobytes())


def clean(s):
    return re.sub("[^a-z]", "", s.lower())


def main():
    with wave.open(str(AUDIO / "narration-continuous.wav"), "rb") as f:
        assert (f.getnchannels(), f.getsampwidth(), f.getframerate()) == (1, 2, RATE)
        raw = np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.float64) / 32768
    data = json.loads((AUDIO / "narration-words.json").read_text(encoding="utf-8-sig"))
    words = data["words"]

    def find(phrase):
        wanted = clean(phrase)
        for i in range(len(words)):
            text = ""
            for j in range(i, len(words)):
                text += clean(words[j]["text"])
                if text == wanted:
                    return i
                if len(text) > len(wanted):
                    break
        raise ValueError(phrase)

    indices = [
        find(p)
        for p in ["Meet Mochi", "Emma knows", "Later Alex", "Our scripted", "Less repeating"]
    ]
    # Play the two actual operations at 1x, with a short genuine result hold.
    minimum = [0, 6.95, 6.6, 8.2]
    inserts = []
    for section in range(1, 4):
        left = indices[section]
        right = indices[section + 1]
        span = words[right]["start"] - words[left]["start"]
        extra = max(0, minimum[section] - span)
        if extra > 0.8:
            raise ValueError(
                "Narration too short for natural pacing; "
                "revise wording instead of adding long silence"
            )
        if extra > 0.0001:
            before = words[right - 1]["end"]
            after = words[right]["start"]
            assert after >= before and after - before > 0.04
            at = (before + after) / 2
            inserts.append(
                {
                    "before_word": words[right]["text"],
                    "at_source_seconds": at,
                    "added_seconds": extra,
                    "source_phrase_gap": after - before,
                }
            )
    lead = 0.4

    def shift(t):
        return lead + t + sum(v["added_seconds"] for v in inserts if t >= v["at_source_seconds"])

    edited = []
    pos = 0
    for item in inserts:
        cut = round(item["at_source_seconds"] * RATE)
        edited.extend([raw[pos:cut], np.zeros(round(item["added_seconds"] * RATE))])
        pos = cut
    edited.append(raw[pos:])
    speech = np.concatenate([np.zeros(round(lead * RATE)), *edited])
    for word in words:
        word["source_start"] = word["start"]
        word["source_end"] = word["end"]
        word["start"] = shift(word["source_start"])
        word["end"] = shift(word["source_end"])
    boundaries = [0] + [round((words[i]["start"] - 0.15) * FPS) for i in indices[1:]]
    duration_frames = math.ceil(max(len(speech) / RATE, words[-1]["end"] + 1.05) * FPS)
    duration = duration_frames / FPS
    narration = np.zeros(round(duration * RATE))
    narration[: len(speech)] = speech
    # Reuse the original local composition, resynthesized at delivery rate and
    # duration. A constant quiet bed avoids phrase-by-phrase volume pumping.
    music_path = (
        APP / "docs/evidence/submission-video-2026-10-15/style-sample-01/audio/build-style-audio.py"
    )
    spec = importlib.util.spec_from_file_location("sample_music", music_path)
    music_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(music_module)
    music_module.RATE = RATE
    music_module.DURATION = duration
    music = music_module.compose_music()
    active = np.abs(narration) > 0.008
    voice_rms = np.sqrt(np.mean(narration[active] ** 2))
    music_rms = np.sqrt(np.mean(music**2))
    gain = min(
        voice_rms * 10 ** (-23 / 20) / music_rms,
        np.abs(narration).max() * 10 ** (-21 / 20) / np.abs(music).max(),
    )
    music *= gain
    mixture = narration + music
    safety = min(1, 0.88 / np.abs(mixture).max())
    mixture *= safety
    wav(AUDIO / "narration-edited.wav", narration)
    wav(AUDIO / "music-quiet.wav", music)
    wav(AUDIO / "mix-pre-normalize.stereo.wav", np.column_stack([mixture, mixture]), 2)
    # Meter the actual stereo layout and normalize that layout, avoiding a
    # subsequent mono-to-stereo +3 LU level change.
    source = AUDIO / "mix-pre-normalize.stereo.wav"
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
    measured = json.loads(re.search(r'\{\s*"input_i".*?\}', first, re.S).group(0))
    (AUDIO / "normalization-pass1.log").write_text(first, encoding="utf-8")
    filt = (
        "loudnorm=I=-16:TP=-1.8:LRA=9:linear=true:measured_I={input_i}:"
        "measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:"
        "offset={target_offset}:print_format=json"
    ).format(**measured)
    final = AUDIO / "soundtrack-v2.stereo.wav"
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
    (AUDIO / "normalization-pass2.log").write_text(second, encoding="utf-8")
    (HERE / "public/soundtrack-v2.stereo.wav").write_bytes(final.read_bytes())
    phrases = [
        "Meet Mochi.",
        "Care is a team effort.",
        "Emma knows the little things,",
        "like that favorite feather toy.",
        "She confirms the detail once,",
        "and it stays with the family.",
        "Later, Alex starts a fresh conversation.",
        "That same confirmed memory is already there,",
        "with its source.",
        "Our scripted concierge preview explores",
        "everyday questions for Miso and Luna,",
        "from food preferences to illustrative activity records.",
        "Less repeating.",
        "More caring.",
    ]
    starts = [find(p) for p in phrases]
    cues = []
    for n, (text, i) in enumerate(zip(phrases, starts, strict=False)):
        j = starts[n + 1] if n + 1 < len(starts) else len(words)
        cues.append(
            {
                "text": text,
                "startMs": round(words[i]["start"] * 1000),
                "endMs": round(words[j - 1]["end"] * 1000 + 80),
                "timestampMs": None,
                "confidence": None,
            }
        )
    save_json(AUDIO / "captions-remotion.json", cues)
    save_json(HERE / "src/voice-revision-captions.json", cues)
    plan = {
        "fps": FPS,
        "durationInFrames": duration_frames,
        "durationSeconds": duration,
        "boundariesInFrames": boundaries,
        "misoSeconds": 4.5,
        "narrationWords": words,
        "insertedPauses": inserts,
        "leadSeconds": lead,
        "sourceVoiceSampleCount": len(raw),
        "sourceVoiceSamplesPreserved": True,
        "timeStretch": False,
        "pitchProcessing": False,
        "musicRelativeActiveVoiceRmsDb": float(
            20 * np.log10(np.sqrt(np.mean(music**2)) / voice_rms)
        ),
        "humanListeningReview": "pending",
    }
    save_json(OUT / "timing-plan.json", plan)
    save_json(
        HERE / "src/voice-revision-plan.json",
        {
            k: plan[k]
            for k in [
                "fps",
                "durationInFrames",
                "durationSeconds",
                "boundariesInFrames",
                "misoSeconds",
            ]
        },
    )
    print(json.dumps({k: v for k, v in plan.items() if k != "narrationWords"}, indent=2))


if __name__ == "__main__":
    main()
