# PawTwin English demonstration video

Prepared on 15 October 2026. The [delivered MP4](../../../../PawTwin-demo-2026-10-15.en.mp4) follows a fictional family caring for Mochi using the current English interface. It combines actual local UI operations and their recorded results.

## Completed production

- Duration: **170.0185034 seconds**, under three minutes.
- Format: **1920 by 1080**, H.264 video and mono AAC audio.
- Narration: offline English Windows SAPI; **26 aligned, burned-in caption sentences**, with [separate SRT](../../../../PawTwin-demo-2026-10-15.en.srt).
- Scenes: 13. **12 normal-speed WebM excerpts total 58.8 seconds**; the remaining time holds actual result screenshots. This is an edited presentation, not a continuous recording.
- Sources: [successful current capture](../../evidence/hackathon-capture/2026-10-15-english/attempt-05/demo-evidence.json), 17 English screenshots and three role-specific WebM recordings. Clip ranges are bound to source SHA-256 hashes. Earlier unsuccessful production rehearsals remain separate.
- Story: shared Today view, sourced growth arithmetic, confirmed preference, another account's new Alexa simulator conversation, reviewable care draft, explicit confirmation, Alex's recorded completion, daily report, temporary read-only caregiver view and visit-card snapshot.

## Verification and review limits

[Mechanical verification](../../evidence/submission-video-2026-10-15/family-story-01/verification.json) confirms actual codecs, dimensions and duration, every sentence fits, captions have no overflow, and **49 frames were decoded from the finished MP4**. Decoded audio lasts 170.0165 seconds, peaks at -5.188 dBFS and has zero clipped samples.

Actual decoded views of all 13 scenes were inspected, together with source clip calibration and selected replay boundaries. The [visual review](../../evidence/submission-video-2026-10-15/family-story-01/visual-review.json) records that inspection. The six-page Word document was reviewed page by page through hidden Word PDF export and bundled Poppler. The canonical LibreOffice renderer was unavailable; the alternative render is recorded in [document QA](document-qa.json).

**Complete human playback and listening remain to be done before public upload.** Mechanical checks and sampled frames do not establish pronunciation, natural pacing or a full listening review. No video was uploaded by this workflow.

The demonstrated backend is local rules with SQLite and local accounts. Alexa is a text web simulator. Devices are simulated; cloud/model integrations remain unverified. Fictional measurements stay labelled, and recorded completion does not independently prove physical care. A visit card is background information, not a diagnosis.

## Rebuild

Use Windows Python 3.12 with NumPy and Pillow, an existing FFmpeg supporting PNG decoding, an installed en-US SAPI voice, Windows Media Foundation and Segoe UI fonts. These video-production dependencies are separate from the application's lock. No voice, media or cloud service is downloaded or invoked by the renderer.

From the repository root, create source-bound clip ranges and inspect their decoded calibration frames:

```powershell
& '<production Python>' docs/submission/2026-10-15/production/calibrate-clips.py `
  --capture docs/evidence/hackathon-capture/2026-10-15-english/attempt-05 `
  --ffmpeg '<existing FFmpeg executable>' `
  --output .cache/submission-video/new-calibration
```

Render into a **new, empty output directory**:

```powershell
& '<production Python>' docs/submission/2026-10-15/production/render-video.py `
  --capture docs/evidence/hackathon-capture/2026-10-15-english/attempt-05 `
  --clip-map .cache/submission-video/new-calibration/clip-map.json `
  --ffmpeg '<existing FFmpeg executable>' `
  --output docs/evidence/submission-video-2026-10-15/new-edit
```

The helper reuses the established native offline encoder and refuses a nonempty output directory. A change to voice, scenes or replay ranges requires a new fit, codec, audio and frame review. This machine's Playwright FFmpeg lacks a JPEG encoder; calibration explicitly requests PNG.

Application code was not changed for this production. A fresh backend run returned **447 passed, 1 skipped and 21 live AWS tests deselected in 52.49 seconds**. The full browser audit remains the 14 October result of 115 passed with zero retries; the new English production walkthrough is a separate successful isolated capture.
