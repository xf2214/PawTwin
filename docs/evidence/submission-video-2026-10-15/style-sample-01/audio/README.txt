PawTwin style sample 01 — 30-second audio assets

Use combined-narration-music-30s.wav for the Remotion preview. It already includes
the scheduled natural narration, ducked original music and three quiet original
edit accents. Do not add the music or accent stems again on top of this mix.

Format: 22,050 Hz, mono, signed PCM16 WAV; all full-length stems are exactly
30.000000 seconds (661,500 samples). Combined peak is -5.484 dBFS and it has zero
clipped samples. PCM peak/RMS checks are mechanical evidence, not listening QA.

Voice: en-US-JennyNeural, -2% speaking rate, Microsoft Edge online speech service
via isolated edge-tts 7.3.1; decoded by miniaudio 1.71. Only the six approved
public fictional sentences were sent online. No API keys or billable resources
were used. This artifact speech operation does not connect the application to
AWS, a model or Alexa. See narration-provenance.json for live voice metadata,
source hashes, the exact sent script, dependencies and source URLs.

The untouched voice-01.wav through voice-06.wav retain their full decoded tails.
The corresponding .edit.wav files remove only exact trailing digital zeros and
retain 100 ms of zero after the last nonzero sample. No nonzero samples were
removed, no speech was cut, and no time stretch or speed compression was applied.

Raw durations / edit durations (seconds):
  1: 3.528027 / 2.904082
  2: 2.952018 / 2.319955
  3: 5.064036 / 4.441406
  4: 3.576009 / 2.954875
  5: 4.872018 / 4.243265
  6: 3.648027 / 3.032562

The first five edit WAVs start at the requested 0.4, 4.4, 10.9, 16.5 and 20.8 s.
Cue 6 starts at 26.95 s (requested 27.2 s) so the complete natural closing line
fits the 30-second sample. Provider speech ends at 29.717833 s; the edit WAV ends
at 29.982562 s. timeline.json records all requested and actual times.

captions-cues.json contains sentence cues and 41 provider word-boundary cues,
offset to the 30-second timeline. These are provider timestamps, not manually
listened or force-aligned timings. voice-XX.words.json preserves source offsets.

Music: original locally synthesized 84 BPM sparse warm harmonic plucks and sine
pad; a new six-phrase variation rather than a loop of the v2 video music. No
downloaded/stock audio or recordings. Music peaks at -24 dBFS and ducks by 8 dB
for speech with smooth attack/release. Three synthesized edit accents peak at
-36 dBFS, scheduled at 10.35, 20.43 and 26.93 s. All stems are available separately.

audio-qa.json records PCM sample counts, peaks, RMS, DC offsets, hashes, gains,
duck settings and the explicit not_performed human-listening status. The helper
build-style-audio.py is artifact-only; it uses the existing isolated dependencies
without changing application dependencies or global installations. Its commands
create new assets and intentionally refuse to replace existing output files.

Human listening review and final editorial approval have not been performed.
