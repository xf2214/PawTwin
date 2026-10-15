"""Independent read-only PCM, provenance, schedule and caption checks."""

import hashlib
import json
import re
import wave
from pathlib import Path

import numpy as np

p = Path(__file__).resolve().parent
rate = 22050
qa = json.loads((p / "audio-qa.json").read_text(encoding="utf-8"))
timeline = json.loads((p / "timeline.json").read_text(encoding="utf-8"))
provenance = json.loads((p / "narration-provenance.json").read_text(encoding="utf-8"))
captions = json.loads((p / "captions-cues.json").read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wav(path):
    with wave.open(str(path), "rb") as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, rate), path.name
        frames = w.getnframes()
        x = np.frombuffer(w.readframes(frames), dtype="<i2")
    assert len(x) == frames and len(x) > 0, path.name
    assert not np.any(np.abs(x.astype(np.int32)) >= 32767), path.name
    return x


waves = {file.name: wav(file) for file in sorted(p.glob("*.wav"))}
assert len(waves) == 20
for name, stats in qa["stems"].items():
    x = waves[name]
    assert len(x) == 661500 and stats["sample_count"] == 661500
    assert sha(p / name) == stats["sha256"]
    peak = 20 * np.log10(np.abs(x.astype(np.float64) / 32768).max())
    assert abs(peak - stats["peak_dbfs"]) < 1e-9
assert qa["human_listening_review"] == "not_performed"
assert qa["no_time_compression"] and qa["no_speech_truncation"]
assert len(provenance["cues"]) == len(timeline["cues"]) == len(captions["cues"]) == 6
assert len(captions["words"]) == 41
previous_end = 0
for source, edit, caption in zip(
    provenance["cues"], timeline["cues"], captions["cues"], strict=False
):
    raw = waves[source["wav"]]
    trimmed = waves[edit["wav"]]
    assert np.array_equal(raw[: len(trimmed)], trimmed)
    assert np.all(raw[len(trimmed) :] == 0)
    assert sha(p / source["wav"]) == source["wav_sha256"]
    assert sha(p / source["mp3"]) == source["mp3_sha256"]
    assert edit["start"] >= previous_end and edit["end"] <= 30
    previous_end = edit["end"]
    assert caption["text"] == source["text"]
    assert edit["start"] <= caption["start"] < caption["end"] <= edit["end"]
    assert caption["end"] <= source["target_end"]
    words = [word for word in captions["words"] if word["cue_id"] == source["id"]]
    actual_text = " ".join(word["text"] for word in words)

    def clean(s):
        return re.sub(r"[^a-z0-9 ]", "", s.lower())

    assert clean(actual_text) == clean(source["text"])
    previous_word_end = edit["start"]
    for word in words:
        assert previous_word_end <= word["start"] < word["end"] <= edit["end"]
        previous_word_end = word["end"]

print(
    json.dumps(
        {
            "result": "PASS",
            "pcm_wav_files": len(waves),
            "full_length_stems": len(qa["stems"]),
            "full_stem_duration_seconds": 30,
            "sample_rate": rate,
            "channels": 1,
            "bits_per_sample": 16,
            "clipped_samples_all_wavs": 0,
            "sentence_cues": 6,
            "provider_word_cues": 41,
            "all_raw_source_hashes_match": True,
            "all_edit_trims_exact_digital_zero_only": True,
            "all_caption_speech_ends_inside_requested_end_windows": True,
            "closing_wav_start_seconds": timeline["cues"][-1]["start"],
            "combined_peak_dbfs": qa["stems"]["combined-narration-music-30s.wav"]["peak_dbfs"],
            "human_listening_review": "not_performed",
        },
        indent=2,
    )
)
