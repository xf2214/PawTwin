# PawTwin English submission package

Updated on 15 October 2026 for local participant review. The proposed entry follows the Alexa+ simulated-experience route. All demonstrated household identities, pet measurements and care events are fictional samples. No repository publication, video upload or competition submission is performed by this preparation.

## Active materials and final film

- [English project description for Devpost](project-description.en.md)
- [English reviewer setup and walkthrough](judge-guide.en.md)
- [Product Feedback draft for participant verification](product-feedback.en.md)
- [Final media production feedback and historical tool notes](video-feedback-addendum.en.md)
- [Remaining submission checklist](submission-checklist.md)
- [Final English demonstration MP4](../../../../PawTwin-hackathon-submission-2026-10-15.en.mp4)
- [Matching English subtitles](../../../../PawTwin-hackathon-submission-2026-10-15.en.srt)
- [Matching film poster](../../../../PawTwin-hackathon-submission-2026-10-15.en.poster.png)
- [Final film production record and review limits](final-video-production.md)

The active film is **142.379 seconds, 1920 × 1080, 30 fps, H.264/AAC**, with 51 caption cues. Its SHA-256 is `47c412da677666bc49d16b39d20d4bfed1ec619b1d2b46cda496ad9a86e6cbe5`. The [verification](../../evidence/submission-video-2026-10-15/fullfilm-01/verification.json) and [delivery record](../../evidence/submission-video-2026-10-15/fullfilm-01/delivery.json) identify the MP4, SRT and poster. Full-stream decode, encoded-frame review and technical audio checks passed. **Complete human playback/listening is still pending.**

The film follows Emma and Alex caring for Mochi: a candidate preference becomes confirmed memory, a fresh Alexa text simulator conversation reads its source, Emma explicitly confirms a manual-care task, Alex records completion from his account, and a daily report cites that saved care record. It then presents the scripted Miso/Luna Pet Concierge examples and states the local prototype boundary. Caregiver access, the visit card, growth calculations and memory deletion remain additional runnable features described in the judge guide; they are not presented as scenes in this final film.

## Source freeze and final package

The complete repaired working tree, including the 15 October Pet Concierge additions, is the source to freeze. **`6342b96` is the 14 October audited baseline, not the identity of the current working tree.** Final local source identity and consolidated checks are recorded by the finalization step in [release-source.json](release-source.json) and [repair verification](../../evidence/submission-repairs-2026-10-15/verification.json).

| Final deliverable | Preparation status |
| --- | --- |
| [Runnable source ZIP](../../../../PawTwin-source-2026-10-15.final.zip) | Prepared by finalization step; verify identity against `release-source.json` and the matching external JSON manifest. |
| [Submission materials ZIP](../../../../PawTwin-submission-materials-2026-10-15.final.zip) | Prepared by finalization step; contains the final film and matching current text. |
| [Editable English submission document](../../../../PawTwin-submission-2026-10-15.final.en.docx) | Generated locally; six-page hidden Word/Poppler render reviewed on every page. See [new document QA](document-final-qa.json) for its hash and canonical-renderer limitation. |

These planned names identify the active finalization outputs. Their existence, hashes, archive CRC, source identity and combined repair verification must be established by the finalization records; this document alone does not mark those checks complete. Original media, DOCX files and earlier archives are preserved.

## Scope and release status

Local account permissions, SQLite records, confirmed per-pet memory, manual-care tasks and arithmetic run in the application. The family conversation backend is `local_rules`; the Alexa entry is a text web simulator. The product page and `/#workbench/concierge` also contain a fictional, preset Pet Concierge preview. Its replies and illustrative activity traces do not invoke a runtime model, track an animal or provide a diagnosis, and it does not read private family records or create care tasks.

Cloud inference, AgentCore memory, real Alexa and hardware are not demonstrated. A recorded manual completion does not independently verify physical care. The visit card presents saved background information without a diagnosis.

Repository/source access for judges, public YouTube/Vimeo upload, participant Product Feedback confirmation, eligibility and rights declarations, and final Devpost submission remain pending external steps. The current repair scope is local only.

## Official references

- [Event submission page](https://amazonappdev2026.devpost.com/)
- [Official rules](https://amazonappdev2026.devpost.com/rules)
- [Official FAQ](https://amazonappdev2026.devpost.com/details/faqs)

The existing 15 October rules review records a deadline of 23 October 2026 at noon PDT, which is **24 October 2026 at 03:00 in Beijing**. No rules recheck was performed during this local material synchronization. Recheck the official event pages immediately before submission. The participant remains responsible for eligibility, track choice and declarations.

## Historical deliveries

The following records describe earlier films and remain historical references:

- [150.2583-second v2 film](../../../../PawTwin-demo-2026-10-15.en.v2.mp4), [its subtitles](../../../../PawTwin-demo-2026-10-15.en.v2.srt) and [v2 production record](video-optimization-v2.md).
- [Earlier approximately 170-second film](../../../../PawTwin-demo-2026-10-15.en.mp4) and [its production record](video-production.md).
- [Previous v2 materials ZIP](../../../../PawTwin-submission-materials-2026-10-15.v2.zip) and [original English DOCX](../../../../PawTwin-submission-2026-10-15.en.docx).
- [V2 scene story](production/story.cinematic.en.json); earlier tool notes are retained in the historical section of the production feedback addendum.

Their scene descriptions, technical figures and document QA records do not describe the active final film or establish QA of the new final DOCX. Existing 3 October and 12 October materials also remain preserved.
