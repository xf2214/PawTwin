# PawTwin final English film production record

Updated 15 October 2026. This is the active film record for the current local English materials. Earlier `PawTwin-demo-2026-10-15.en.mp4` and `.en.v2.mp4` deliveries, their subtitles, production notes and archives remain unchanged as historical versions.

## Active delivery

| File | Size in bytes | SHA-256 |
| --- | --- | --- |
| [MP4](../../../../PawTwin-hackathon-submission-2026-10-15.en.mp4) | 10,522,694 | `47c412da677666bc49d16b39d20d4bfed1ec619b1d2b46cda496ad9a86e6cbe5` |
| [English SRT](../../../../PawTwin-hackathon-submission-2026-10-15.en.srt) | 3,879 | `ba0206992fb335f6dbc143c45e43119a2e0d8d67d9b994c2082577a45bc92d27` |
| [Poster PNG](../../../../PawTwin-hackathon-submission-2026-10-15.en.poster.png) | 379,627 | `0714251a5970a4e5cbf60360bbe4046b0625d266ad0eee568e020b5f163f0949` |

The film is **142.379 seconds**, **1920 × 1080**, **30 fps**, H.264 video with AAC stereo audio and **51 caption cues**. The three file hashes were rechecked during this material synchronization and match [delivery.json](../../evidence/submission-video-2026-10-15/fullfilm-01/delivery.json).

## Story and application evidence

The [final narration](../../evidence/submission-video-2026-10-15/fullfilm-01/narration.en.txt) and actual local UI clips follow this sequence:

1. Emma knows Mochi's feather-toy preference and quiet rest after meals; Alex is taking over care.
2. Emma saves the preference as a candidate, reviews it and explicitly confirms it.
3. Alex opens a fresh Alexa text simulator conversation; its reply cites the confirmed preference's source.
4. Emma requests a playtime draft, chooses a time, prepares a proposal and explicitly confirms it. Only that confirmation creates a shared manual-care task.
5. Alex claims the task from his own account and records completion; his identity and result remain in the saved household history.
6. Emma generates the daily report, which includes the saved care record. The narration states that this does not independently verify physical care.
7. Scripted Pet Concierge examples show fictional Miso's profile/preference and Luna's illustrative activity records. Replies and traces are presets, with no live model inference, actual tracking or diagnosis.
8. The closing boundary identifies SQLite, local rules and the Alexa text web simulator; live cloud inference and real Alexa integration are not demonstrated.

The film does not claim to demonstrate caregiver-link revocation, the visit information card, measured growth calculations or memory deletion. Those supported application features have separate steps and evidence in the [judge guide](judge-guide.en.md). The preset Pet Concierge UI does not read private family records or create care tasks.

## Recorded technical verification

The existing [fullfilm verification](../../evidence/submission-video-2026-10-15/fullfilm-01/verification.json) records:

- Full-stream decode passed; 4,271 video frames; under 180 seconds.
- 51 cues match the complete narration, with no caption overlap.
- 48 actual encoded frames were inspected; an independent reviewer checked 14 critical frames. A report-title crop was corrected before rendering.
- Actual encoded stereo audio is approximately 142.379 seconds, **−16.01 LUFS**, **−1.82 dBTP**, with **zero clipped samples**; the technical review found no duration truncation.
- Source UI playback speed is 1×. Previous deliveries were hash-verified unchanged.

These are mechanical checks and recorded frame/audio technical reviews. **Complete human playback/listening was not performed.** A participant still needs to watch and listen to the entire final film, judge narration clarity and music balance, and confirm caption timing before publication. No upload or competition submission was performed.

## Production and source records

The active production directory is `docs/evidence/submission-video-2026-10-15/fullfilm-01/`. It retains the [production plan](../../evidence/submission-video-2026-10-15/fullfilm-01/production-plan.json), [timing plan](../../evidence/submission-video-2026-10-15/fullfilm-01/timing-plan.json), [audio production](../../evidence/submission-video-2026-10-15/fullfilm-01/audio-production.json), [asset hashes](../../evidence/submission-video-2026-10-15/fullfilm-01/sha256-manifest.json), [build helper](../../evidence/submission-video-2026-10-15/fullfilm-01/build-fullfilm.py), [render helper](../../evidence/submission-video-2026-10-15/fullfilm-01/render-fullfilm.ps1) and [verification helper](../../evidence/submission-video-2026-10-15/fullfilm-01/verify-fullfilm.py). Production evidence describes the existing film; lint repair does not itself rerender or reapprove media.

The final source and materials archive names are `PawTwin-source-2026-10-15.final.zip` and `PawTwin-submission-materials-2026-10-15.final.zip`. They and their external JSON manifests are **prepared by the finalization step**. The same step supplies [release-source.json](release-source.json), [consolidated repair verification](../../evidence/submission-repairs-2026-10-15/verification.json) and the new editable `PawTwin-submission-2026-10-15.final.en.docx`. Check those records for actual generation, source identity, archive validation and document QA. Historical baseline `6342b96` does not identify the later complete working tree.
