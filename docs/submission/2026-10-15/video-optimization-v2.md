# PawTwin optimized English demonstration

Prepared 15 October 2026. [Watch the optimized video](../../../../PawTwin-demo-2026-10-15.en.v2.mp4). [Separate subtitles](../../../../PawTwin-demo-2026-10-15.en.v2.srt). The previous version is preserved.

The revised film follows Know Mochi, Plan Together and Hand Off Clearly. It replaces the permanent proof sidebar with a large application viewport, short headings, actor labels, smooth editorial camera movement and restrained crossfades. Fourteen chapters connect the fictional household's records, confirmed memory, manual care and results, with brief controlled sharing and visit-card examples.

## Completed production and checks

| Property | Previous version | Optimized version |
| --- | --- | --- |
| Actual duration | 170.0185 seconds | 150.2583 seconds |
| UI pane before overlays | About 42 percent of frame pixels | About 77 percent of frame pixels |
| Normal-speed real UI excerpts including reading holds | 58.8 seconds | About 101.8 seconds |
| Source recording | 1280 by 720 | Native 1920 by 1080 |
| Output | 1080p H.264 AAC at 15 fps | 1080p H.264 AAC at 24 fps |
| Narration | Offline SAPI voice | JennyNeural English narration |
| Music | None | Original 88 BPM synthesized music with speech ducking |
| Captions | 26 complete sentences | 28 aligned cues with at most two lines |

The new [actual capture](../../evidence/hackathon-cinematic-capture-2026-10-15/attempt-03-native1920/demo-evidence.json) includes real report generation, candidate-to-confirmed preference, care proposal preparation and confirmation, and Alex's task claim/completion. Native-frame checks confirm the recordings contain full 1920 by 1080 content without padding. Idle waits are edited out using explicit source ranges; retained clips play at normal speed. Camera crops and transitions are presentation effects over actual source pixels. No clicks, typing, app results, pet reactions or hardware operations were fabricated.

[Finished-video checks](../../evidence/submission-video-2026-10-15/cinematic-01/verification.json) confirm H.264/AAC, 1920 by 1080, 150.2583 seconds, all narration fits, and 57 frames decoded from the finished MP4. Actual decoded audio has zero clipped samples, a -2.163 dBFS peak and a 150.2563-second duration. All fourteen sampled scene views and critical memory/completion/report/visit/outro frames were reviewed. Independent review found no major evidence cropping or actor/state inconsistency. Peripheral page edges are intentionally outside some editorial closeups.

**Full human playback and listening remain unperformed.** Check the complete video before public upload, including pronunciation, pacing and music balance. This production has not uploaded or submitted the video.

## Narration and application boundaries

Natural narration was generated with the third-party [edge-tts client](https://github.com/rany2/edge-tts) and Microsoft's online speech service using only the public fictional English script. Local MP3 decoding used [miniaudio](https://github.com/irmen/pyminiaudio). No account credentials, real household data, paid resources or app cloud integration were involved. Saved narration can be used for offline re-rendering. Voice-generation metadata and QA are stored with the video evidence.

This online video-production narration is separate from the application. The demonstrated App remains local accounts, SQLite and `local_rules`; its Alexa page is a text web simulation. No live AWS, AgentCore, Alexa endpoint or physical device integration is established. Weights and household identities are fictional. Recorded manual completion does not independently prove physical care, and the visit card is information for review rather than a diagnosis.

## Reproduction

Use the repository's existing Windows native encoder, production Python with NumPy/Pillow, and the saved Jenny WAVs. The synthesis and MP3-decoder packages are isolated under `.cache/submission-video/audio-study-20261015/deps`; their versions are recorded in `production/audio-dependencies.lock.txt`. Application dependencies and source code were unchanged.

```powershell
& '<production Python>' docs/submission/2026-10-15/production/render-cinematic.py `
  --capture docs/evidence/hackathon-cinematic-capture-2026-10-15/attempt-03-native1920 `
  --audio .cache/submission-video/cinematic-audio-20261015 `
  --ffmpeg '<existing installed FFmpeg supporting PNG>' `
  --output docs/evidence/submission-video-2026-10-15/new-cinematic-edit
```

Output directories must be new and empty. A rebuild or editorial change requires fresh duration, caption, codec, audio and actual-frame checks. The source timings, source hashes, original music stem and provider metadata are retained in the production evidence.
