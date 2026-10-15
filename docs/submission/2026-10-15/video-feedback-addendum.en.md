# PawTwin final video production feedback addendum

Updated 15 October 2026 for **PawTwin-hackathon-submission-2026-10-15.en.mp4**, the active 142.379-second film. Confirm first-hand onboarding and a Yes or No reuse answer with a reason for each used tool before submitting Product Feedback. Recorded technical results do not supply those personal responses.

## Active final film

| Tool | Recorded purpose and result | Limitation and participant field |
| --- | --- | --- |
| Remotion and Chromium | Rendered actual local UI clips, scripted Pet Concierge scenes and timed captions at 1920 × 1080, 30 fps. | A rendered story does not establish live Alexa, runtime model inference, tracking or real household outcomes. Personal onboarding/reuse pending. |
| edge-tts 7.3.1 | Generated one continuous `en-US-AvaMultilingualNeural` narration take at provider rate −10%, with 324 word boundaries; the retained source take is 140.904 seconds. | Third-party client for an online speech interface, not an Azure SDK or Alexa integration. Fictional narration was transmitted for synthesis. Personal onboarding/reuse pending. |
| NumPy | Built the final soundtrack with original locally synthesized sparse harmonic plucks and pad; audio evidence records no post-speech time/pitch processing or edited internal pauses. | Original music still requires participant rights confirmation and complete listening for balance. Personal reuse pending. |
| Pillow | Inspected/composed encoded-frame review material and the matching poster in the verification workflow. | Frame review does not replace watching the complete film. Personal reuse pending. |
| FFmpeg and ffprobe through the recorded Remotion media path | Full-stream decode, stream probe, encoded-frame extraction and encoded-audio checks passed. Encoded stereo measures −16.01 LUFS and −1.82 dBTP with zero clipped samples. | Technical audio review is not full human listening. Personal onboarding/reuse pending. |

Final narration has 51 matching, nonoverlapping caption cues. The final source UI plays at 1×. **Complete human playback/listening was not performed; no upload or competition submission occurred.**

Evidence: [final film record](final-video-production.md), [final take provenance](../../evidence/submission-video-2026-10-15/fullfilm-01/audio/calm-take/provenance.json), [audio production](../../evidence/submission-video-2026-10-15/fullfilm-01/audio-production.json), [encoded verification](../../evidence/submission-video-2026-10-15/fullfilm-01/verification.json) and [delivery hashes](../../evidence/submission-video-2026-10-15/fullfilm-01/delivery.json).

## Historical cinematic v2 production

The following dated records describe the preserved **PawTwin-demo-2026-10-15.en.v2.mp4**, approximately 150 seconds, rather than the active final film:

| Tool | Actual purpose and observed result | Limitation and onboarding evidence | Participant reuse answer |
| --- | --- | --- | --- |
| edge-tts 7.3.1 | Generated 28 English JennyNeural narration cues successfully without retries. Live voice listing and local PCM checks were verified. | Third-party client for an online Edge speech interface; not a supported Azure SDK integration. Public fictional narration was transmitted to Microsoft's service. Installed only in a separate artifact cache. Network availability is required for new synthesis. | Pending Yes or No and reason |
| miniaudio 1.71 | Decoded the locally generated narration MP3s into mono 22050 Hz PCM16 WAVs. Duration and clipping checks passed. | Added because the existing Playwright FFmpeg lacked audio decoding and the native media path rejected standalone MP3. Isolated artifact dependency; no app dependency change. | Pending Yes or No and reason |
| NumPy and Pillow | Composed source-preserving camera movement, transitions, subtitles and original deterministic 88 BPM music. | Editorial effects improve presentation; they do not establish application capability or physical care. Actual source and finished frames still need review. | Pending Yes or No and reason |
| Playwright and Chromium | Recorded fresh native 1920 by 1080 actual English UI operations and API evidence in an isolated fictional household. | A trial with a smaller CSS viewport produced padded output despite a 1920 recording container. The final recording uses a real 1920 viewport, verified through actual decoded frames. | Pending Yes or No and reason |
| Windows Media Foundation and installed FFmpeg | Encoded H.264/AAC and decoded source/finished frames for verification. | The installed Playwright FFmpeg only supported the required video/PNG path; audio conversion used a separate local decoder. Full human listening remains outstanding. | Pending Yes or No and reason |

SAPI was used for the earlier approximately 170-second video. Cinematic v2 used JennyNeural; the active final film uses the continuous Ava take identified above. Preserve those distinctions when completing the [Product Feedback draft](product-feedback.en.md), and verify personal responses for every tool included in the actual-use list. Online narration generation does not establish an AWS Builder claim or live Alexa use.

Primary tool references: [edge-tts](https://github.com/rany2/edge-tts), [miniaudio](https://github.com/irmen/pyminiaudio), [Microsoft Edge privacy information](https://learn.microsoft.com/en-us/microsoft-edge/privacy-whitepaper/).
