# Current local English review video

The 2026-10-11 edit uses the refreshed actual two-account capture, keeps the old 10/03 edits unchanged, and targets 170 seconds. It is a local review artifact; no video is uploaded or submitted by these scripts.

The produced [current review MP4](../evidence/submission-video-2026-10-11/local-review-01/pawtwin-local-review.en.mp4) is 170.0185034 seconds, 1920×1080 H.264/AAC and 26,165,692 bytes. Its 26 full sentences fit, captions do not overflow, and decoded AAC has zero clipped samples (peak −5.203 dBFS). The [13-scene actual decoded contact sheet](../evidence/submission-video-2026-10-11/local-review-01/review-frames/actual-contact-sheet.png) and detailed frames were visually inspected; [visual-review.json](../evidence/submission-video-2026-10-11/local-review-01/visual-review.json) records that bounded inspection. Full human listening/playback remains unperformed.

## Source and claims

Default source: `docs/evidence/hackathon-capture/2026-10-11-final/`. Required evidence has schema version 2, `backend=local_rules`, zero cloud calls and the actual Alexa draft, proposal and confirmation results. The edit uses complete actual PNG screenshots from the current product page, App, independent Alexa simulator, manual-care result and report. Silent owner/carer WebM recordings remain as source artifacts. This edit does **not** reuse the old 7.6/8.6-second replay cuts or claim its still screenshots are realtime video.

Each scene and subtitle has exact generated output seconds in `timeline.json` and `captions.en.srt`. Capture screenshot timestamps are test elapsed milliseconds, not raw WebM seek positions. Weights are fictional demo samples. Memory is owner-confirmed SQLite data, care drafts use local rules, confirmation creates manual tasks, and the Alexa entry is a text web simulation. Account review has cleared; live integration remains unverified by this local capture.

## Windows production prerequisites

This is a Windows offline production workflow, separate from the portable local App setup. Use an installed Python 3.12 environment with NumPy and Pillow, Windows PowerShell 5.1, Windows Media Foundation/Media Runtime, an installed en-US SAPI voice, and Segoe UI fonts. NumPy/Pillow are **not** project-lock dependencies. The script does not install packages or download voices. The current Codex bundled runtime can be located with `load_workspace_dependencies`; its personal absolute path is not a requirement for another machine.

```powershell
# Use the actual installed production Python, not a guessed personal path.
& '<installed Python with NumPy and Pillow>' scripts/render-submission-video.py `
  --capture docs/evidence/hackathon-capture/2026-10-11-final `
  --output docs/evidence/submission-video-2026-10-11/current-review
```

Existing nonempty output directories are refused. A complete sentence is never truncated to fit the timeline. `--smoke` produces a separate short native-encoder check. Current still-image edits do not need FFmpeg. Optional replay decoding can use `--ffmpeg '<existing executable>'`; otherwise the renderer checks installed PATH and existing Playwright `ffmpeg-*` folders. It does not install FFmpeg. Voice differences may change timing; a build is accepted only when every sentence fits.

## Outputs and review

The deliverables are `pawtwin-local-review.en.mp4` (1920×1080, H.264/AAC), complete narration WAV/text, burned-in English captions/SRT, timeline, planned and actual decoded review frames, source/file hash manifests, `verification.json`, and `build.log`. The build measures actual codecs, 165–175-second duration, decoded AAC duration/peak/clipping, sentence fit and subtitle overflow. Large intermediates stay in ignored `.cache/submission-video/`.

These mechanical checks do not establish complete human playback, pronunciation or listening review. `human_audio_review=not_performed` remains accurate until a person completes that review; record their actual findings separately. Public YouTube/Vimeo access, English material review, repository access/rights and competition submission remain external gates. The App's browser speech synthesis is a separate unreviewed feature, not the SAPI narration or real Alexa voice integration.

Historical artifacts and the original video guide's source ranges remain recoverable in Git/old timelines under `submission-video-2026-10-03/local-review-01` and `local-review-02`; current rebuilds use the new capture only.
