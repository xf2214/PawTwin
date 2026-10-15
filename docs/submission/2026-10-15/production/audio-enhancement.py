"""Artifact-only natural narration and original understated music.

Requires isolated dependencies, never application dependencies:
  <root>/.cache/submission-video/audio-study-20261015/deps
  edge-tts==7.3.1; miniaudio==1.71

Narration uses a third-party client of Microsoft's online Edge speech service.
Only public fictional narration is transmitted. Application cloud_calls remain
separate: producing this artifact is an online narration operation.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
DEPS = ROOT / ".cache/submission-video/audio-study-20261015/deps"
VOICE = "en-US-JennyNeural"
VOICE_RATE = "-2%"
SAMPLE_RATE = 22050
BPM = 88.0
PRIMARY_SOURCES = {
    "edge_tts": "https://github.com/rany2/edge-tts",
    "mp3_decoder": "https://github.com/irmen/pyminiaudio",
    "online_voice_privacy": "https://learn.microsoft.com/en-us/microsoft-edge/privacy-whitepaper/",
}


def _dependencies():
    if not DEPS.is_dir():
        raise FileNotFoundError(
            f"Isolated artifact dependencies are missing: {DEPS}. "
            "Install pinned edge-tts==7.3.1 miniaudio==1.71 there only."
        )
    if str(DEPS) not in sys.path:
        sys.path.insert(0, str(DEPS))
    import edge_tts
    import miniaudio

    return edge_tts, miniaudio


def _json_new(path: Path, value) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def write_wave(path: Path, samples: np.ndarray, rate: int) -> None:
    if path.exists():
        raise FileExistsError(path)
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(rate)
        target.writeframes(np.asarray(samples, dtype="<i2").tobytes())


def sample_stats(samples: np.ndarray, rate: int) -> dict:
    if not len(samples):
        raise ValueError("Empty audio")
    x = samples.astype(np.float64) / 32768
    peak = float(np.abs(x).max())
    rms = float(np.sqrt(np.mean(x * x)))
    return {
        "duration_seconds": len(samples) / rate,
        "sample_rate": rate,
        "channels": 1,
        "bits_per_sample": 16,
        "sample_count": len(samples),
        "peak_dbfs": 20 * math.log10(max(peak, 1e-12)),
        "rms_dbfs": 20 * math.log10(max(rms, 1e-12)),
        "clipped_samples": int((np.abs(samples.astype(np.int32)) >= 32767).sum()),
        "dc_offset": float(x.mean()),
    }


def decode_mp3(source: Path, target: Path) -> dict:
    _, miniaudio = _dependencies()
    decoded = miniaudio.decode_file(
        str(source),
        output_format=miniaudio.SampleFormat.SIGNED16,
        nchannels=1,
        sample_rate=SAMPLE_RATE,
    )
    samples = np.asarray(decoded.samples, dtype="<i2").copy()
    if decoded.nchannels != 1 or decoded.sample_rate != SAMPLE_RATE or not len(samples):
        raise ValueError("Unexpected MP3 decode format")
    write_wave(target, samples, SAMPLE_RATE)
    return sample_stats(samples, SAMPLE_RATE)


def synthesize(texts: list[str], output: Path, log: Path) -> list[Path]:
    """Generate one 22,050 Hz mono PCM16 WAV per public narration sentence.

    This explicitly performs network requests. No local or provider fallback is
    automatic, and existing artifacts are never replaced.
    """
    edge_tts, miniaudio = _dependencies()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    log = Path(log)
    paths = [output / f"voice-{i:02d}.wav" for i in range(len(texts))]
    mp3s: list[Path] = []
    provenance = output / "narration-provenance.json"
    for path in [*paths, provenance]:
        if path.exists():
            raise FileExistsError(path)
    if any(output.glob("tts-source-*-attempt-*.mp3")):
        raise FileExistsError("Existing synthesis attempts require a new output directory")
    if not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("Narration sentences must be nonempty strings")

    async def generate():
        voices = await asyncio.wait_for(edge_tts.list_voices(), timeout=45)
        matches = [voice for voice in voices if voice["ShortName"] == VOICE]
        if len(matches) != 1:
            raise RuntimeError(f"Expected live natural voice is unavailable: {VOICE}")
        for index, text in enumerate(texts):
            public_text = text.replace("PawTwin", "Paw Twin")
            for attempt in range(1, 4):
                source = output / f"tts-source-{index:02d}-attempt-{attempt:02d}.mp3"
                if source.exists():
                    raise FileExistsError(source)
                try:
                    await asyncio.wait_for(
                        edge_tts.Communicate(
                            public_text, VOICE, rate=VOICE_RATE, volume="+0%", pitch="+0Hz"
                        ).save(str(source)),
                        timeout=90,
                    )
                    break
                except Exception as error:
                    with log.open("a", encoding="utf-8") as stream:
                        stream.write(
                            f"Public narration {index}, attempt {attempt} failed: "
                            f"{type(error).__name__}; attempt retained\n"
                        )
                    if attempt == 3:
                        raise RuntimeError(
                            f"Online narration {index} failed after three retained attempts"
                        ) from None
                    await asyncio.sleep(1)
            decode_mp3(source, paths[index])
            mp3s.append(source)
            with log.open("a", encoding="utf-8") as stream:
                stream.write(f"Online public narration {index + 1}/{len(texts)}: {VOICE}\n")
            print(f"Natural narration {index + 1}/{len(texts)}", flush=True)
        return matches[0]

    metadata = asyncio.run(generate())
    _json_new(
        provenance,
        {
            "provider": "Microsoft Edge online speech service via third-party edge-tts client",
            "official_azure_sdk": False,
            "voice": metadata,
            "rate": VOICE_RATE,
            "edge_tts_version": edge_tts.__version__,
            "miniaudio_version": miniaudio.__version__,
            "isolated_dependencies": str(DEPS),
            "source_urls": PRIMARY_SOURCES,
            "text_scope": "User-authorized public fictional demonstration narration only",
            "application_cloud_calls": "Separate artifact narration; application calls unchanged",
            "billable_resources_created": 0,
            "credentials_used": False,
            "sentences": [
                {
                    "index": i,
                    "text": text,
                    "wav": paths[i].name,
                    "mp3_sha256": hashlib.sha256(mp3s[i].read_bytes()).hexdigest(),
                }
                for i, text in enumerate(texts)
            ],
        },
    )
    return paths


def _add(target, note, start, rate):
    at = round(start * rate)
    count = min(len(note), len(target) - at)
    if count > 0:
        target[at : at + count] += note[:count]


def _pluck(midi, rate):
    t = np.arange(round(2.4 * rate)) / rate
    hz = 440 * 2 ** ((midi - 69) / 12)
    envelope = (1 - np.exp(-t * 95)) * np.exp(-t * 2.4)
    note = np.sin(2 * np.pi * hz * t)
    note += 0.24 * np.sin(2 * np.pi * hz * 2 * t) * np.exp(-t * 4)
    note += 0.06 * np.sin(2 * np.pi * hz * 3 * t) * np.exp(-t * 7)
    return note * envelope


def original_music(duration: float, rate: int) -> np.ndarray:
    """Original deterministic pluck/pad/percussion; float mono, max -22 dBFS."""
    n = round(duration * rate)
    if rate <= 0 or duration <= 0 or n <= 0:
        raise ValueError("Music requires a positive sample rate and duration")
    result = np.zeros(n)
    beat = 60 / BPM
    chords = [
        (48, 55, 60, 62, 64),
        (45, 52, 55, 60, 64),
        (41, 48, 52, 57, 60),
        (43, 50, 55, 57, 62),
    ]
    for bar in range(math.ceil(duration / (8 * beat))):
        base = bar * 8 * beat
        notes = chords[bar % len(chords)]
        for position, degree in [(0, 0), (1.5, 2), (3, 4), (4, 1), (5.5, 3), (7, 2)]:
            _add(result, 0.06 * _pluck(notes[degree] + 12, rate), base + position * beat, rate)
        t = np.arange(round(8.2 * beat * rate)) / rate
        envelope = np.minimum(t, 1) * np.minimum((t[-1] - t) / 1.3, 1)
        pad = sum(np.sin(2 * np.pi * 440 * 2 ** ((midi - 69) / 12) * t) for midi in notes[:3])
        _add(result, 0.008 * pad * envelope, base, rate)
    rng = np.random.default_rng(20261015)
    for i in range(math.ceil(duration / beat)):
        t = np.arange(round(0.18 * rate)) / rate
        kick = np.sin(2 * np.pi * (54 * t + 0.8 * (1 - np.exp(-t * 28))))
        if i % 2 == 0:
            _add(result, 0.018 * kick * np.exp(-t * 28), i * beat, rate)
        t = np.arange(round(0.05 * rate)) / rate
        noise = rng.normal(0, 1, len(t))
        noise -= np.concatenate([[0], noise[:-1].copy()])
        _add(result, 0.0015 * noise * np.exp(-t * 60), (i + 0.5) * beat, rate)
    delay = round(beat * 0.75 * rate)
    if 0 < delay < n:
        result[delay:] += result[:-delay].copy() * 0.17
    peak = float(np.abs(result).max())
    if peak:
        result *= 10 ** (-22 / 20) / peak
    t = np.arange(n) / rate
    result *= np.minimum(t / 2, 1) * np.minimum((duration - t) / 2, 1)
    return result


def _cue_duck(cues, n, rate):
    duck = np.ones(n)
    under_voice = 10 ** (-6 / 20)
    for cue in cues:
        start, end = float(cue["start"]), float(cue["end"])
        if not (
            math.isfinite(start) and math.isfinite(end) and 0 <= start <= end <= n / rate + 1 / rate
        ):
            raise ValueError(f"Invalid voice cue {start}, {end}")
        lo, hi = round(start * rate), min(n, round(end * rate))
        duck[lo:hi] = np.minimum(duck[lo:hi], under_voice)
        attack_start = max(0, lo - round(0.12 * rate))
        release_end = min(n, hi + round(0.32 * rate))
        if lo > attack_start:
            duck[attack_start:lo] = np.minimum(
                duck[attack_start:lo], np.linspace(1, under_voice, lo - attack_start)
            )
        if release_end > hi:
            duck[hi:release_end] = np.minimum(
                duck[hi:release_end], np.linspace(under_voice, 1, release_end - hi)
            )
    return duck


def mix_with_music(samples, rate, cues, music_path: Path | None = None):
    """Return (PCM16 mix, QA stats); optionally save ducked stem plus QA JSON."""
    samples = np.asarray(samples)
    if samples.ndim != 1 or samples.dtype.kind != "i" or samples.dtype.itemsize != 2:
        raise ValueError("Expected mono PCM16 narration")
    if rate <= 0 or not len(samples):
        raise ValueError("Expected positive rate and nonempty narration")
    cues = list(cues)
    duration = len(samples) / rate
    voice = samples.astype(np.float64) / 32768
    peak = float(np.abs(voice).max())
    active = np.abs(voice) > 0.008
    active_rms = float(np.sqrt(np.mean(voice[active] ** 2))) if active.any() else 0
    gain = min(1.55, 0.78 / peak, 0.125 / active_rms) if peak and active_rms else 1
    bed = original_music(duration, rate) * _cue_duck(cues, len(samples), rate)
    # With no cues, conservatively duck the whole bed whenever voice is present.
    if not cues and active.any():
        bed *= 10 ** (-6 / 20)
    mixed = voice * gain + bed
    mixed_peak = float(np.abs(mixed).max())
    safety_gain = min(1, 0.90 / mixed_peak) if mixed_peak else 1
    mixed *= safety_gain
    output = np.round(mixed * 32767).astype("<i2")
    stem = np.round(bed * 32767).astype("<i2")
    stats = {
        "composition": (
            "Original 88 BPM deterministic sine electric-piano pluck, "
            "warm pad and muted synthesized percussion"
        ),
        "chords": ["Cadd9", "Am7", "Fmaj7", "Gsus2"],
        "music_seed": 20261015,
        "stock_audio_or_recordings": False,
        "bpm": BPM,
        "music_peak_limit_between_cues_dbfs": -22,
        "music_peak_limit_under_voice_dbfs": -28,
        "intro_outro_fade_seconds": 2,
        "voice_gain": gain,
        "mix_safety_gain": safety_gain,
        "cue_count": len(cues),
        "narration_before_mix": sample_stats(samples, rate),
        "music_stem": sample_stats(stem, rate),
        "mixed_audio": sample_stats(output, rate),
        "human_listening_review": "not_performed",
    }
    if len(output) != len(samples) or stats["mixed_audio"]["clipped_samples"]:
        raise ValueError("Mixed audio length or clipping check failed")
    if music_path is not None:
        music_path = Path(music_path)
        qa_path = music_path.with_name(music_path.stem + ".qa.json")
        if music_path.exists() or qa_path.exists():
            raise FileExistsError(music_path)
        write_wave(music_path, stem, rate)
        _json_new(qa_path, stats)
    return output, stats


def mix_voice(samples, rate, cues, duration, *, music_path: Path | None = None):
    """Compatible mixer API; requires the exact full-video narration length."""
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Expected a positive finite duration")
    if len(samples) != round(duration * rate):
        raise ValueError("Narration length must equal requested video duration")
    return mix_with_music(samples, rate, cues, music_path)[0]
