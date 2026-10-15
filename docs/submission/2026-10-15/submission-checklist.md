# PawTwin submission checklist

Prepared **15 October 2026**. The proposed primary route is **Alexa+ simulated experience built with Codex-assisted development**. The demonstrated runtime is `local_rules` and SQLite. This checklist does not establish participant eligibility or organizer acceptance.

The published deadline is **23 October 2026 at 12:00 PDT**, equivalent to **24 October 2026 at 03:00 Asia/Shanghai**. Recheck the submission portal before final submission. [Official rules](https://amazonappdev2026.devpost.com/rules)

## Local materials

- [x] Fresh English project description with the standard Devpost sections: [project-description.en.md](project-description.en.md).
- [x] English setup, capability matrix and two-account walkthrough: [judge-guide.en.md](judge-guide.en.md).
- [x] Product Feedback draft tied to recorded developer use and friction: [product-feedback.en.md](product-feedback.en.md).
- [x] Historical 14 October baseline identified as `6342b96`; its recorded results are 447 backend passed, 1 skipped, 21 live AWS deselected and 115 browser passed with zero retries. This is not the final identity of the later working tree.
- [x] Current English-first interface, fictional sample labels and local/simulated boundaries are recorded.
- [x] Active final film, matching captions and poster identified: **PawTwin-hackathon-submission-2026-10-15.en.mp4**, 142.379 seconds, 1920 × 1080, 30 fps, 51 cues; [production record](final-video-production.md).
- [x] Active MP4/SRT/poster hashes match the [delivery record](../../evidence/submission-video-2026-10-15/fullfilm-01/delivery.json). Full-stream decode, encoded-frame review and technical audio checks are recorded in [verification.json](../../evidence/submission-video-2026-10-15/fullfilm-01/verification.json).
- [x] Final-film scenes match the current description; caregiver/vet-card/deletion features are distinguished from the filmed sequence. Earlier 150/170-second films and their documents are historical references.
- [ ] Complete human playback/listening of the active 142.379-second film, including narration, caption timing and music balance.
- [x] Final repaired verification passed **495 backend tests**, with 1 skipped and 21 live AWS deselected; **122 browser tests**, four isolated services and zero retries. Ruff, contracts, TypeScript and production build passed; [consolidated verification](../../evidence/submission-repairs-2026-10-15/verification.json).
- [x] Complete runnable repaired source frozen locally. **PawTwin-source-2026-10-15.final.zip**, its external JSON manifest and [release-source.json](release-source.json) bind the application identity; the external manifest records the exact final Git commit.
- [x] Current materials archive **PawTwin-submission-materials-2026-10-15.final.zip** includes the final film, source ZIP, matching source manifest, text and Word document. CRC, member hashes, links and film/source identity passed [archive preflight](../../evidence/submission-repairs-2026-10-15/archive-preflight.json). The canonical archives repeat these checks after documentation activation.
- [x] New editable document **PawTwin-submission-2026-10-15.final.en.docx** generated and all six Word/Poppler-rendered pages visually reviewed; [final document QA](document-final-qa.json) records its SHA-256 and the unavailable canonical LibreOffice renderer. The original [document QA record](document-qa.json) applies only to the preserved original DOCX.

Local preparation and archive validation are complete; human film listening and all external fields below remain participant tasks. The final external archive manifests identify the canonical files and their exact hashes. GitHub publication, video upload and Devpost submission remain separate.

## Required external submission fields

| Field or action | Current state | Participant action |
| --- | --- | --- |
| Devpost entry, track and team | Pending | Select the track, verify names/team details and complete the entry. |
| Eligibility and rights | Pending | Confirm residence/age/employment exclusions, team eligibility and rights to source, assets and music. Do not infer eligibility from this package. |
| GitHub repository URL | Not supplied | Publish the complete runnable source/assets/setup or grant the prescribed private reviewer access without charge through judging. |
| Public repository license | Not selected | If public, choose and include an open-source license and verify rights. |
| Private repository reviewer access | Not granted in this preparation | If private, follow the current organizer list and confirm access/invitations remain valid. |
| Public YouTube or Vimeo video URL | Not supplied | Upload an English demonstration under three minutes and verify public judge access. |
| English description | Local draft complete | Review and paste the final copy into Devpost. |
| Product Feedback | Participant-review draft | Confirm actual tool/API/SDK use, onboarding experience and Yes/No reuse reasons for each; upload the completed document. |
| AI or agentic tool declaration | Recorded Codex development evidence; declaration pending | Describe the development tool separately from the `local_rules` runtime and review its evidence. Do not claim preapproved track acceptance. |
| Source and setup access test | Local evidence available | Test the exact shared repository/package from a clean checkout and verify all required files and instructions. |
| Final submission | Not performed | Complete, review and submit the Devpost entry before the deadline. |

The simulation route does not require Alexa hardware or public App hosting, and its permitted technology paths are described in the rules and FAQ. Live AWS/Bedrock/AgentCore validation is not a mandatory local-simulation prerequisite. An **AWS Builder** bonus claim requires actual qualifying use; adapter imports/offline tests do not establish it. [Official rules](https://amazonappdev2026.devpost.com/rules), [overview](https://amazonappdev2026.devpost.com/) and [FAQ](https://amazonappdev2026.devpost.com/details/faqs)

## Review before publishing

- Confirm the video, description, source and setup refer to the same delivered version.
- Use the 142.379-second `PawTwin-hackathon-submission-2026-10-15.en.mp4` and matching final archives; check the local freeze identity in `release-source.json` rather than treating historical commit `6342b96` as the final source.
- Preserve “fictional”, “Demo sample”, “local_rules”, simulator and manual-care labels. Do not describe confirmed SQLite memory as AgentCore extraction, simulated receipts as hardware operation or recorded manual completion as a measured household benefit.
- Preserve the Pet Concierge preset/scenario and simulated-trace labels. Miso/Luna examples do not establish live inference, actual tracking or diagnosis.
- Do not expose passwords, active invitations, caregiver tokens, session traces, `.env` files, user databases or backups in source or video.
- Verify missing measurements/intake remain unknown and the visit card contains no invented diagnosis.
- Check repository permissions and the exact public video link while signed out.
- Complete personal feedback and eligibility fields before describing the package as ready to submit.

## Optional future work

Live cloud/model testing, real Alexa integration, hardware, production deployment and household trials remain separate future work. No such action is completed by the local submission-material preparation.
