# PawTwin English competition demonstration — 12 October 2026

The new [demonstration MP4](../../../PawTwin-demo-2026-10-12.en.mp4) is **170.0185034 seconds**, 1920×1080 H.264/AAC, 27,572,560 bytes. It has English offline SAPI narration and 26 burned-in English caption sentences. [Separate SRT](../../../PawTwin-demo-2026-10-12.en.srt) and [poster](../../../PawTwin-demo-2026-10-12.poster.jpg) are provided.

## Presentation

Thirteen scenes follow the actual product page, sourced weight report, owner-confirmed memory, a second account's independent Alexa simulator, new session, play draft/time, pending proposal, explicit confirmation, carer completion/activity, simulator result, daily report, deleted-memory reply and the local scope card.

Eight visually calibrated WebM excerpts provide **18.4 seconds at normal speed**; the remainder uses their actual result screenshots and readable English explanations. The source is the [11 October two-account capture](../evidence/hackathon-capture/2026-10-11-final/demo-evidence.json). This is an edited demonstration, not a continuous 170-second screen recording. No mock result replaces the source UI/API evidence, and screenshot test elapsed times were not used as raw-video seek positions.

## Verification and scope

- [Production/codec/audio inspection](../evidence/submission-video-2026-10-12/english-demo-03/verification.json): duration under 180 seconds; all sentences fit; subtitles have no overflow; 37 actual decoded frames, including start/middle/end for each replay; decoded AAC has no clipped samples, peak −5.164 dBFS.
- [Exact output timeline](../evidence/submission-video-2026-10-12/english-demo-03/timeline.json), [source ranges and SHA binding](../evidence/submission-video-2026-10-12/english-demo-03/clip-map.json), [source manifest](../evidence/submission-video-2026-10-12/english-demo-03/source-manifest.json), [delivery metadata](../evidence/submission-video-2026-10-12/english-demo-03/delivery.json).
- Actual decoded scene and replay frames were visually inspected. The [visual review](../evidence/submission-video-2026-10-12/english-demo-03/visual-review.json) records the bounded review; complete human playback/listening remains unperformed.
- Local accounts, confirmed SQLite memory and rule-based care drafts are working prototype operations. Alexa and devices are simulated; weights and household identities are fictional demonstration samples. This video does not establish live AWS/model/Alexa/hardware integration or real-household outcomes.
- SHA-256: `98e0d78fbb86d25f38085d5234e1ee476fc742d1a39e0d41bbf88e2a8abbd691`. The earlier 11 October MP4 remains unchanged.

The file is ready for participant review. Full listening, public YouTube/Vimeo upload, source access, personal feedback/rights/eligibility and final competition submission are separate steps; this task has not uploaded or submitted it.

## Rebuild

Use installed Python 3.12 with NumPy/Pillow, Windows SAPI en-US voice/fonts/Media Foundation, and an existing FFmpeg executable. From the actual project root, target a **new** output directory:

```powershell
& '<installed production Python>' scripts/render-submission-video.py `
  --capture docs/evidence/hackathon-capture/2026-10-11-final `
  --clip-map docs/evidence/submission-video-2026-10-12/english-demo-03/clip-map.json `
  --demo-edit `
  --output docs/evidence/submission-video-2026-10-12/rebuild-01
```

The renderer preserves the still-image path when no clip map is supplied. Each raw directory and decoded-frame filename includes its scene number. Large frame QA requests are batched to stay within Windows process command-line limits. It checks source hashes, refuses invalid/out-of-bounds times and nonempty output directories, and does not install tools or call cloud services. Production attempts and trimmed preliminary edits are retained in the ignored audit cache; `english-demo-03` is the reviewed delivery.
