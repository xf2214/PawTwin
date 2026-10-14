# PawTwin — current hackathon rule check

Checked on **3 October 2026**, Asia/Shanghai, by reading the official event rules, overview, FAQ and organizer update. Candidate event: **Build, Ship, Shape: Amazon Developer Hackathon 2026**. The event is still in its submission period: deadline **23 October 2026, 12:00 PDT**, equivalent to **24 October 2026, 03:00 Asia/Shanghai**. This does not confirm this participant's registration or eligibility. [Official rules, Dates and Eligibility](https://amazonappdev2026.devpost.com/rules)

## Candidate route and unresolved technical gate

Alexa+ permits a simulated web experience; an actual device and deployment are unnecessary. [Official FAQ](https://amazonappdev2026.devpost.com/details/faqs) The alternative must still use AI/agentic tools, but has no prescribed framework/SDK/MCP surface. [Official track description](https://amazonappdev2026.devpost.com/)

**Assessment, not an organizer ruling:** PawTwin has working shared context and confirmation workflows, but [pet_context.py](../../backend/pawtwin/pet_context.py) currently answers with keyword rules (`local_rules`, no request ID); [family_api.py](../../backend/pawtwin/family_api.py) takes proposal type/title/time from the owner. Do not assert this alone guarantees technical eligibility or Stage One acceptance. Validate actual AI/agentic capability or obtain an organizer interpretation before final track claims.

AWS Builder is optional and requires documented actual AWS-tool use; Kiro Crew has a standalone development-tool exception. [Official mini-challenge description](https://amazonappdev2026.devpost.com/) No verified Kiro use, real inference, AgentCore retrieval, true DynamoDB table, cloud deployment or new-household cloud layer exists in the current evidence. Legacy adapters and offline tests are preparation, not a completed mini-challenge claim.

## Requirement-to-delivery check

The official overview lists required source, description, video, tool feedback and track declarations. [Submission checklist](https://amazonappdev2026.devpost.com/) English or English translations are required. [Official language rule](https://amazonappdev2026.devpost.com/rules)

| Item | Current evidence / release gate |
|---|---|
| Working source and setup instructions | Local source and [English judge guide](judge-guide.en.md) exist. Package the uncommitted extension as well as baseline `31da349` |
| Project description | [English draft](project-description.en.md) prepared; review final claims and links |
| GitHub access | No remote URL verified. Public route needs a chosen open-source license; private route needs both Devpost and Amazon reviewer access. No license or sharing change was made |
| Final video | A **170.019-second local English review MP4** is now built, with narration, burned-in captions and actual replay clips. Complete human playback/pronunciation review and a public YouTube/Vimeo URL remain release gates; local raw captures and the local MP4 do not supply the required public URL |
| English documentation | English project/testing/feedback drafts and interface glossary prepared; the app itself is Chinese. Translate any other submitted material |
| Tool feedback | [Evidence-based feedback draft](product-feedback.en.md) prepared. Contributor must confirm proposed reuse choices; untested AWS/SDK experiences remain unclaimed |
| Track declaration | Alexa+ simulation is the candidate; suitability remains unresolved. AWS Builder has no qualifying evidence claim |
| New/significant work in event window | Local September–October implementation history exists; final source package and description must identify the actual submitted updates |
| Eligibility and rights | Age/residence/conflict checks, team representative, registration and asset rights require participant confirmation; do not infer them from a local checkout |
| Judge access through judging | Final code/video access must remain available; hosted private access, if used, needs testing instructions |
| Optional friction log | [Local evidence-backed entries](product-feedback.en.md) exist. No invented Amazon-service incident or household feedback |
| Optional Open Source challenge | Not established: no authorized open-source license/public contribution URL or GitHub identity supplied |

Private-repository reviewers are `testing@devpost.com`, `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth` and `emersonsklar`. Invitations need acceptance and expire after seven days. [Organizer's access instructions](https://amazonappdev2026.devpost.com/updates/46456-got-an-idea) These instructions are preparation only; this pass did not send invitations or publish source.

## Required evidence and optional work

The FAQ confirms a locally runnable repo plus demonstration video can be sufficient for hosting access. [Official Alexa+ judging FAQ](https://amazonappdev2026.devpost.com/details/faqs) Therefore the new family cloud layer and a public App are not blanket prerequisites for preparing the simulated entry. Real-family trial evidence would strengthen the project's impact argument but is not a listed mandatory material. The empty trial template must stay empty until actual participants and observations exist.

Gated Alexa+ add-on development tools are unavailable to hackathon participants according to the FAQ; their availability must not be treated as a failed PawTwin runtime integration. [Official tooling FAQ](https://amazonappdev2026.devpost.com/details/faqs) Real AWS operation remains a separate, authorized technical workstream; no chargeable call is needed to reproduce these local materials.

Technical implementation, design, potential impact and idea quality receive equal weight. The current local engineering evidence supports implementation/design; measured household benefit and actual AI/agentic reasoning remain weak. Optional friction logs may receive a discretionary bonus of up to 10%. [Organizer's judging guidance](https://amazonappdev2026.devpost.com/updates/46456-got-an-idea), [official bonus rule](https://amazonappdev2026.devpost.com/rules)

## Final review order

1. Confirm candidate-track technical suitability, participant eligibility, registration and rights.
2. Refresh local verification and package the actual extension source and assets.
3. Review the English drafts and contributor tool-feedback choices; watch/listen to the [local English review video](../evidence/submission-video-2026-10-03/local-review-02/pawtwin-local-review.en.mp4), finalize it for the actual technical evidence, and provide its public URL after publication authorization.
4. Select a license/public route or private reviewer route, then perform authorized sharing/publication and test the final links.
5. Re-read the live official rules before submitting. Submit only when separately authorized; this rule check is not a submission.

This material pass changed documentation only. No license choice, cloud resource, repository push, invitation, publication or competition submission is implied.
