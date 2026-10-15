"""Artifact-only PawTwin 30-second style-sample audio; no app/runtime changes.

Run with the production Python runtime and `synthesize`, then `mix`.
Online speech sends only the six approved fictional sentences. Music/accents are
original deterministic local synthesis, without recordings or downloaded music.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import math
import sys
import wave
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
HELPER_PATH = ROOT / "docs/submission/2026-10-15/production/audio-enhancement.py"
spec = importlib.util.spec_from_file_location("pawtwin_audio_helper", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
RATE = 22050
DURATION = 30.0
VOICE = "en-US-JennyNeural"
VOICE_RATE = "-2%"
EDIT_START_OVERRIDES = {6: 26.95}
CUES = [
    {
        "id": 1,
        "start": 0.4,
        "target_end": 3.8,
        "text": "Care feels easier when everyone knows your pet.",
    },
    {"id": 2, "start": 4.4, "target_end": 9.8, "text": "Emma confirms what Mochi loves."},
    {
        "id": 3,
        "start": 10.9,
        "target_end": 15.8,
        "text": "Alex starts fresh. The same context comes along.",
    },
    {
        "id": 4,
        "start": 16.5,
        "target_end": 20.2,
        "text": "And everyday questions can start there, too.",
    },
    {
        "id": 5,
        "start": 20.8,
        "target_end": 26.7,
        "text": "These scripted previews explore food questions and activity records.",
    },
    {"id": 6, "start": 27.2, "target_end": 29.8, "text": "Less repeating. More caring."},
]


def new_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_wav(path):
    with wave.open(str(path), "rb") as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1, 2, RATE)
        return np.frombuffer(audio.readframes(audio.getnframes()), dtype="<i2").copy()


def as_pcm(samples):
    if not np.isfinite(samples).all() or np.max(np.abs(samples)) >= 0.999:
        raise ValueError("Unsafe float audio")
    return np.round(np.asarray(samples) * 32767).astype("<i2")


async def make_voice():
    edge_tts, miniaudio = helper._dependencies()
    voices = await asyncio.wait_for(edge_tts.list_voices(), timeout=45)
    selected = [voice for voice in voices if voice["ShortName"] == VOICE]
    if len(selected) != 1:
        raise RuntimeError("Expected natural voice unavailable")
    generated = []
    for cue in CUES:
        index = cue["id"]
        target = OUT / f"voice-{index:02d}.wav"
        boundaries_path = OUT / f"voice-{index:02d}.words.json"
        if target.exists() or boundaries_path.exists():
            raise FileExistsError(target)
        words = []
        source = None
        for attempt in range(1, 4):
            candidate = OUT / f"tts-source-{index:02d}-attempt-{attempt:02d}.mp3"
            if candidate.exists():
                raise FileExistsError(candidate)
            words = []
            try:

                async def stream_to_file(candidate_path, cue_text, word_metadata):
                    with candidate_path.open("xb") as audio:
                        client = edge_tts.Communicate(
                            cue_text,
                            VOICE,
                            rate=VOICE_RATE,
                            volume="+0%",
                            pitch="+0Hz",
                            boundary="WordBoundary",
                        )
                        async for chunk in client.stream():
                            if chunk["type"] == "audio":
                                audio.write(chunk["data"])
                            elif chunk["type"] == "WordBoundary":
                                start = chunk["offset"] / 10_000_000
                                word_metadata.append(
                                    {
                                        "text": chunk["text"],
                                        "start": start,
                                        "end": start + chunk["duration"] / 10_000_000,
                                        "offset_100ns": chunk["offset"],
                                        "duration_100ns": chunk["duration"],
                                    }
                                )

                await asyncio.wait_for(stream_to_file(candidate, cue["text"], words), timeout=90)
                if not words or candidate.stat().st_size < 100:
                    raise RuntimeError("Missing audio or word metadata")
                source = candidate
                break
            except Exception as exc:
                with (OUT / "generation.log").open("a", encoding="utf-8") as log:
                    log.write(
                        f"cue {index}, attempt {attempt}: {type(exc).__name__}; source retained\n"
                    )
                if attempt == 3:
                    raise RuntimeError(
                        f"Cue {index} failed after three retained attempts"
                    ) from None
                await asyncio.sleep(1)
        stats = helper.decode_mp3(source, target)
        new_json(
            boundaries_path,
            {
                "source": "Microsoft Edge provider WordBoundary metadata",
                "units": "seconds relative to full untrimmed WAV",
                "timing_review": "provider timing only; no human listening alignment performed",
                "text": cue["text"],
                "words": words,
            },
        )
        generated.append(
            {
                **cue,
                "wav": target.name,
                "mp3": source.name,
                "duration_seconds": stats["duration_seconds"],
                "window_seconds": cue["target_end"] - cue["start"],
                "window_overrun_seconds": max(
                    0, stats["duration_seconds"] - (cue["target_end"] - cue["start"])
                ),
                "speech_start_seconds": words[0]["start"],
                "speech_end_seconds": words[-1]["end"],
                "word_count": len(words),
                "stats": stats,
                "wav_sha256": sha256(target),
                "mp3_sha256": sha256(source),
            }
        )
        print(
            json.dumps(
                {
                    k: generated[-1][k]
                    for k in [
                        "id",
                        "duration_seconds",
                        "window_seconds",
                        "window_overrun_seconds",
                        "speech_end_seconds",
                    ]
                }
            ),
            flush=True,
        )
    new_json(
        OUT / "narration-provenance.json",
        {
            "generated_utc": datetime.now(UTC).isoformat(),
            "provider": "Microsoft Edge online speech service via third-party edge-tts client",
            "official_azure_sdk": False,
            "voice": selected[0],
            "rate": VOICE_RATE,
            "edge_tts_version": edge_tts.__version__,
            "miniaudio_version": miniaudio.__version__,
            "sample_rate": RATE,
            "channels": 1,
            "format": "PCM signed 16-bit WAV",
            "silence_trimmed": False,
            "time_stretch_or_speed_compression": False,
            "isolated_dependencies": str(helper.DEPS),
            "source_urls": helper.PRIMARY_SOURCES,
            "text_scope": (
                "Six user-approved public fictional PawTwin style-sample narration sentences only"
            ),
            "credentials_used": False,
            "billable_resources_created": 0,
            "application_cloud_calls": "Unchanged; online artifact speech operation is separate",
            "human_listening_review": "not_performed",
            "cues": generated,
        },
    )


def add(target, note, start):
    at = round(start * RATE)
    if at < 0:
        raise ValueError("Negative note")
    count = min(len(note), len(target) - at)
    if count > 0:
        target[at : at + count] += note[:count]


def pluck(midi, length=2.6):
    t = np.arange(round(length * RATE)) / RATE
    hz = 440 * 2 ** ((midi - 69) / 12)
    attack = 1 - np.exp(-t * 70)
    note = np.sin(2 * np.pi * hz * t) * np.exp(-t * 2.35)
    note += 0.17 * np.sin(2 * np.pi * 2 * hz * t) * np.exp(-t * 3.8)
    note += 0.035 * np.sin(2 * np.pi * 3 * hz * t) * np.exp(-t * 6)
    return attack * note


def compose_music():
    n = round(DURATION * RATE)
    bed = np.zeros(n)
    beat = 60 / 84
    # An original six-phrase variation; this does not loop the v2 music stem.
    phrases = [
        (0.0, (48, 55, 59, 62, 64)),
        (5.0, (45, 52, 55, 60, 64)),
        (10.0, (41, 48, 52, 57, 60)),
        (15.0, (48, 55, 59, 62, 64)),
        (20.0, (43, 50, 55, 57, 62)),
        (25.0, (48, 55, 59, 62, 64)),
    ]
    for at, chord in phrases:
        for position, degree in [(0.0, 2), (1.5, 4), (3.5, 3), (5.5, 1)]:
            add(bed, 0.04 * pluck(chord[degree] + 12), at + position * beat)
        t = np.arange(round(5.6 * RATE)) / RATE
        env = np.clip(t / 1.25, 0, 1) * np.clip((5.6 - t) / 1.7, 0, 1)
        pad = sum(np.sin(2 * np.pi * 440 * 2 ** ((midi - 69) / 12) * t) for midi in chord[:3])
        add(bed, 0.0045 * pad * env, at)
    # Sparse low warm punctuation rather than a percussive beat.
    for at, midi in [(0.0, 48), (10.0, 41), (20.0, 43), (25.0, 48)]:
        add(bed, 0.018 * pluck(midi, 3.7), at)
    delay = round(0.31 * RATE)
    bed[delay:] += 0.13 * bed[:-delay].copy()
    bed *= 10 ** (-24 / 20) / np.max(np.abs(bed))
    t = np.arange(n) / RATE
    bed *= np.clip(t / 1.1, 0, 1) * np.clip((DURATION - t) / 2.15, 0, 1)
    bed -= bed.mean()
    return bed


def compose_accents():
    full = np.zeros(round(DURATION * RATE))
    rng = np.random.default_rng(2026101501)
    events = []
    for index, at in enumerate([10.35, 20.43, 26.93], start=1):
        t = np.arange(round(0.24 * RATE)) / RATE
        noise = rng.normal(0, 1, len(t))
        # Smoothed noise with a quiet rounded sine makes a soft edit tap.
        noise = np.convolve(noise, np.ones(17) / 17, mode="same")
        env = (1 - np.exp(-t * 220)) * np.exp(-t * 40)
        tap = (0.18 * noise + np.sin(2 * np.pi * (690 + index * 70) * t)) * env
        tap *= 10 ** (-36 / 20) / np.max(np.abs(tap))
        target = OUT / f"edit-accent-{index:02d}.wav"
        helper.write_wave(target, as_pcm(tap), RATE)
        add(full, tap, at)
        events.append(
            {"id": index, "start": at, "duration_seconds": len(tap) / RATE, "wav": target.name}
        )
    return full, events


def duck_for(cues):
    duck = np.ones(round(DURATION * RATE))
    floor = 10 ** (-8 / 20)
    for cue in cues:
        lo = max(0, round((cue["start"] - 0.025) * RATE))
        hi = min(len(duck), round((cue["end"] + 0.04) * RATE))
        attack = max(0, lo - round(0.16 * RATE))
        release = min(len(duck), hi + round(0.36 * RATE))
        duck[lo:hi] = np.minimum(duck[lo:hi], floor)
        duck[attack:lo] = np.minimum(duck[attack:lo], np.linspace(1, floor, lo - attack))
        duck[hi:release] = np.minimum(duck[hi:release], np.linspace(floor, 1, release - hi))
    return duck


def mix():
    provenance = json.loads((OUT / "narration-provenance.json").read_text(encoding="utf-8"))
    narration = np.zeros(round(DURATION * RATE))
    captions = []
    word_cues = []
    gains = []
    timing = []
    for cue in provenance["cues"]:
        raw_pcm = read_wav(OUT / cue["wav"])
        nonzero = np.flatnonzero(raw_pcm)
        # Remove only exact digital-zero padding, retaining 100 ms after the last
        # nonzero sample. Raw provider-decode WAVs remain untouched beside edits.
        keep = min(len(raw_pcm), int(nonzero[-1]) + 1 + round(0.1 * RATE))
        pcm = raw_pcm[:keep]
        if np.any(raw_pcm[keep:] != 0):
            raise ValueError("Attempted to trim nonzero narration")
        edit_name = f"voice-{cue['id']:02d}.edit.wav"
        helper.write_wave(OUT / edit_name, pcm, RATE)
        samples = pcm.astype(np.float64) / 32768
        start = float(EDIT_START_OVERRIDES.get(cue["id"], cue["start"]))
        end = start + len(samples) / RATE
        if end > DURATION:
            raise ValueError(f"Cue {cue['id']} exceeds 30 seconds: {end}; retiming required")
        words = json.loads((OUT / f"voice-{cue['id']:02d}.words.json").read_text(encoding="utf-8"))[
            "words"
        ]
        speech_start = start + words[0]["start"]
        speech_end = start + words[-1]["end"]
        # One gain per cue; no dynamics compression, time stretch, or truncation.
        active = np.abs(samples) > 0.008
        active_rms = np.sqrt(np.mean(samples[active] ** 2))
        gain = min(1.7, 10 ** (-5.5 / 20) / np.max(np.abs(samples)), 10 ** (-20 / 20) / active_rms)
        at = round(start * RATE)
        if np.any(narration[at : at + len(samples)] != 0):
            raise ValueError("Narration cues overlap")
        narration[at : at + len(samples)] = samples * gain
        gains.append(
            {"id": cue["id"], "linear_gain": float(gain), "gain_db": float(20 * math.log10(gain))}
        )
        captions.append(
            {
                "id": cue["id"],
                "start": round(speech_start, 6),
                "end": round(speech_end, 6),
                "text": cue["text"],
            }
        )
        word_cues.extend(
            {
                "cue_id": cue["id"],
                "text": w["text"],
                "start": round(start + w["start"], 6),
                "end": round(start + w["end"], 6),
            }
            for w in words
        )
        timing.append(
            {
                "id": cue["id"],
                "wav": edit_name,
                "raw_wav": cue["wav"],
                "requested_start": cue["start"],
                "start": start,
                "end": end,
                "duration_seconds": len(samples) / RATE,
                "raw_duration_seconds": len(raw_pcm) / RATE,
                "digital_zero_tail_removed_seconds": (len(raw_pcm) - len(pcm)) / RATE,
                "target_end": cue["target_end"],
                "speech_start": speech_start,
                "speech_end": speech_end,
                "raw_window_overrun_seconds": cue["window_overrun_seconds"],
            }
        )
    music = compose_music()
    accents, accent_events = compose_accents()
    ducked_music = music * duck_for(captions)
    combined = narration + ducked_music + accents
    peak = np.max(np.abs(combined))
    safety = min(1, 10 ** (-3 / 20) / peak)
    combined *= safety
    stems = {
        "narration-30s.wav": narration,
        "music-original-30s.wav": music,
        "music-ducked-30s.wav": ducked_music,
        "edit-accents-30s.wav": accents,
        "combined-narration-music-30s.wav": combined,
    }
    qa = {}
    for name, samples in stems.items():
        pcm = as_pcm(samples)
        helper.write_wave(OUT / name, pcm, RATE)
        qa[name] = {**helper.sample_stats(pcm, RATE), "sha256": sha256(OUT / name)}
        if qa[name]["clipped_samples"] != 0 or qa[name]["duration_seconds"] != DURATION:
            raise ValueError("Audio QA failure")
    new_json(
        OUT / "captions-cues.json",
        {
            "duration_seconds": DURATION,
            "timing_source": (
                "Microsoft Edge provider WordBoundary timestamps offset by scheduled cue WAV starts"
            ),
            "human_listening_alignment": "not_performed",
            "cues": captions,
            "words": word_cues,
        },
    )
    new_json(
        OUT / "timeline.json",
        {
            "duration_seconds": DURATION,
            "sample_rate": RATE,
            "cues": timing,
            "edit_accents": accent_events,
        },
    )
    new_json(
        OUT / "audio-qa.json",
        {
            "duration_seconds": DURATION,
            "sample_rate": RATE,
            "channels": 1,
            "bits_per_sample": 16,
            "voice": VOICE,
            "voice_rate": VOICE_RATE,
            "narration_gain_per_cue": gains,
            "no_time_compression": True,
            "no_speech_truncation": True,
            "raw_wavs_silence_trimmed": False,
            "edit_wavs_and_mix_trim": (
                "Only trailing exact digital zero samples removed, with 100 ms zero tail retained; "
                "no nonzero samples removed"
            ),
            "cue_start_override": {
                "6": {
                    "requested": 27.2,
                    "edit": 26.95,
                    "reason": (
                        "Natural closing phrase plus 100 ms digital-zero tail needs 3.0326 s; "
                        "preserve voice speed and complete phrase within 30 s"
                    ),
                }
            },
            "music": {
                "composition": (
                    "Original sparse warm harmonic plucks and sine pad; "
                    "six-phrase Cmaj9, Am7, Fmaj7, Cmaj9, Gsus2, Cmaj9 variation"
                ),
                "bpm": 84,
                "stock_audio_or_recordings": False,
                "external_downloads": False,
                "peak_limit_dbfs": -24,
                "voice_duck_db": -8,
                "duck_attack_seconds": 0.16,
                "duck_release_seconds": 0.36,
            },
            "accents": {
                "composition": "Three original synthesized smoothed-noise and soft sine transients",
                "seed": 2026101501,
                "individual_peak_dbfs": -36,
                "events": accent_events,
            },
            "safety_gain": float(safety),
            "human_listening_review": "not_performed",
            "caption_timing_review": "Provider metadata only; no human alignment review",
            "stems": qa,
        },
    )
    print(json.dumps({"timing": timing, "qa": qa}, indent=2), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"synthesize", "mix"}:
        raise SystemExit("Expected synthesize or mix")
    if sys.argv[1] == "synthesize":
        asyncio.run(make_voice())
    else:
        mix()
