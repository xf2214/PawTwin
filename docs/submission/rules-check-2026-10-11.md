# PawTwin — submission rule check, 11 October 2026

Checked on **11 October 2026**, Asia/Shanghai, against the live official rules, overview and FAQ for **Build, Ship, Shape: Amazon Developer Hackathon**. This is a readiness assessment; participant registration, eligibility and final track selection remain unconfirmed.

## Dates and candidate route

The submission deadline is **23 October 2026, 12:00 PDT**, equivalent to **24 October 2026, 03:00 Asia/Shanghai**. Judging is **9–20 November 2026**, with winners expected around **3 December 2026**. [Official dates and eligibility](https://amazonappdev2026.devpost.com/rules)

Alexa+ offers a simulated web-experience route built using any AI or agentic tool, with no prescribed framework, SDK or MCP surface. The simulation is exempt from the runtime-technology-hook requirement; its source and functioning experience must still be demonstrated. The alternative integration route is a working Agent Skill or self-hosted MCP server using at least MCP 2025-11-25 over Streamable HTTP. The participant has not selected a final route by this document. [Official track and submission checklist](https://amazonappdev2026.devpost.com/)

**Assessment:** PawTwin's independent `/#alexa` page is a functioning local simulator with shared records, care drafts and explicit confirmation. Its default backend is `local_rules`. An optional family Bedrock path is wired and has offline injected-client tests; a live invocation is not recorded in the reviewed evidence. Record the actual AI/agentic tools used and their evidence, or obtain organizer clarification where needed, before asserting track acceptance. The rules do not prescribe a mandatory live Bedrock call for the simulation route.

The [11 October simulator record](../evidence/alexa-simulator-2026-10-11.md) documents Codex-assisted implementation and independent review. [Tool feedback](product-feedback.en.md) records this development use without calling it in-product model inference. Include the source/flow and actual-tool evidence in the selected simulation submission; final organizer acceptance remains outside a local code audit.

AWS Builder is optional and needs documented AWS-tool use; Kiro Crew can qualify as a development tool without an additional runtime service. Open Source is another optional challenge with its own contribution URL, repository, GitHub identity and contribution description. Neither challenge is established by an unused adapter or a local archive. [Official mini challenges](https://amazonappdev2026.devpost.com/)

## Requirement-to-evidence checklist

| Requirement or gate | Current evidence and next action |
|---|---|
| Functioning source and setup | Current dirty checkout includes the family App, website, simulator and backend-service wiring. Publish the complete reviewed source rather than baseline `31da349` alone. See [judge guide](judge-guide.en.md). |
| Project description | [Current English description](project-description.en.md) explains the product, architecture and capability boundaries. Confirm final claims against the final capture. |
| GitHub access | No remote URL or reviewer access is verified here. Choose public with an open-source license, or private with reviewer access. This document does not choose a license or publish source. |
| Demo video | The [current English review MP4](../evidence/submission-video-2026-10-11/local-review-01/pawtwin-local-review.en.mp4) exists and lasts **170.0185034 seconds**, under three minutes. It edits 14 actual current screenshots with English narration/captions; the two raw account WebMs are retained separately. Metadata, decoded frames, caption fit and audio levels are checked; the contact sheet has been visually reviewed. Full human playback/listening and a public YouTube/Vimeo URL remain gates. |
| English or translation | English description, testing instructions and tool feedback are supplied. The Chinese interface has an English control glossary; translate any additional submitted materials and ensure the final video has English narration/captions or an English translation. |
| Actual-tool feedback | [Feedback draft](product-feedback.en.md) separates local use, offline tests and unverified services. The contributor must supply or confirm personal onboarding experience and Yes/No reuse answers. |
| Track declarations | Alexa+ simulation is a candidate. Actual AI/agentic-tool evidence and the participant's final primary/mini-challenge choices remain gates. |
| Registration, eligibility and rights | Participant must confirm joining the event, age/residence eligibility, conflicts, team representative authority and ownership/permission for submitted assets. Do not infer these facts from the checkout. |
| Access through judging | Keep source/video freely available to judges through the judging period. A private hosted site, if supplied, also needs private testing login instructions. |
| Current reproducibility | Full backend/static/build verification and the dedicated capture have passed as recorded below. The final full browser run passed 42 tests in 1.4 minutes with zero retries; complete-source export status is recorded by the coordinator. The coordinator's final record is `docs/evidence/submission-readiness-2026-10-11.md`; the intended archive is `../pawtwin-review-2026-10-11.zip` from the project root. |

Source, description, video, feedback, track declarations, English/translation and judge testing access are required submission fields. [Official submission, language and testing requirements](https://amazonappdev2026.devpost.com/rules)

## Repository access and hosting

For a private GitHub repository, provide access for `testing@devpost.com` and the listed reviewer accounts: `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth` and `emersonsklar`. Invitations require acceptance and expire after seven days; check their validity around submission. The public route requires an open-source license. [Official repository instructions](https://amazonappdev2026.devpost.com/), [private-repository FAQ](https://amazonappdev2026.devpost.com/details/faqs)

A locally runnable repository plus demo video is sufficient for the Alexa+ judging hosting requirement. Physical Alexa hardware and a public App deployment are unnecessary. Gated Alexa+ add-on tooling is unavailable to hackathon participants; its absence should not be described as a PawTwin account failure. [Official Alexa+ FAQ](https://amazonappdev2026.devpost.com/details/faqs)

## Current evidence boundary

The current product uses local accounts and SQLite in one application instance. No new-household cloud identity, distributed storage, production deployment, real hardware interaction or measured household outcome is established. The user has reported that AWS account review passed; **live validation is not recorded**, so the old account-review blocker must not be presented as current fact.

The latest 11 October `scripts/verify.ps1` passed **393 backend tests**, with **one skipped and 21 live AWS tests deselected**; Ruff, generated contracts, TypeScript and the production build passed. The dedicated current capture passed **one rehearsal in 39.7 seconds**, producing [schema-2 API/UI evidence](../evidence/hackathon-capture/2026-10-11-final/demo-evidence.json), 14 screenshots and two account WebMs. The final full browser run passed **42 tests in 1.4 minutes with zero retries**; source-export verification is tracked in the coordinator record; skipped/excluded tests do not count as passed or as real AWS validation.

## Release order

1. Complete source-export verification and human full video listening; retain previous captures and user data.
2. Confirm actual AI/agentic-tool evidence, eligibility/registration, rights, tool feedback and final track choices.
3. Decide public license or private reviewer access; authorize repository sharing and public video upload, then test the final links.
4. Recheck official rules and submit only with explicit authorization.

This pass changes documentation only. No cloud call, resource creation, license grant, invitation, repository push, video upload or competition submission is performed.
