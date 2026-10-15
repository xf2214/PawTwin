# PawTwin

## Elevator pitch

PawTwin helps a family share one traceable care record for each pet. Confirmed preferences, manual care tasks and measured growth stay connected across the household App and a labelled Alexa text simulator.

## Inspiration

Pet care is often a handoff. One person remembers a preference, another handles playtime, and someone else prepares information for a visit. Separate messages make it difficult to see which record is current and who actually completed a task.

We explored that problem through **Mochi, a fictional household pet**. A family member records that Mochi likes a feather toy and rests after meals. Another member should be able to consult the same confirmed preference, take over a care task and leave an accountable completion record. This story illustrates the product hypothesis; it is not a real household trial or a measured customer outcome.

## What it does

The working local App supports independent accounts, household invitations, permission roles and several pet profiles. Its Today, Care, Growth, Twin and Family sections connect daily care with the pet's saved context. Display names such as “Dad” describe a member without changing their permission role.

The owner saves a preference as a candidate and explicitly confirms it. The App and Alexa text simulator then read the same per-pet records and expose the source IDs used in an answer. A new simulator session clears the page conversation while keeping household records. Deleted or expired memories stop appearing in new answers.

In the simulator, “plan playtime” creates a rule-based care draft. The member selects a time, prepares the proposal and explicitly confirms it. Confirmation creates a **manual care task**. A second family member claims the task and records its completion. Reports show that manual completion record and its sources; an arrangement alone is never counted as completed care. The recorded completion does not independently verify a physical action.

Growth records preserve timestamps, units and source labels. Daily and weekly reports calculate changes from saved records and retain missing values. A temporary, revocable caregiver link provides a limited read-only view for one pet. A visit information card can be previewed, printed or exported as an offline HTML file, without adding a diagnosis or inventing missing measurements.

The separate product website uses clearly labelled fictional examples. It does not read private household records.

A scripted **Pet Concierge** preview on the product website and in the workbench explores context with two other fictional pets. Miso's food question is shown alongside a preset profile and preference; Luna's example pairs illustrative activity records with observation guidance. The displayed replies and traces are fixed scenarios. They do not run a model, track a real animal, diagnose a condition, read private family records or create care tasks.

## How we built it

We built a Windows-reproducible, single-instance prototype with Python 3.12, FastAPI/Uvicorn, Pydantic, SQLite and a React/TypeScript/Vite frontend. Server-side membership, roles, pet scope, sessions and CSRF checks control access. Version and expiry checks protect care confirmations from stale context. A background worker produces persistent reports using the household's time zone.

Codex assisted bounded implementation, test execution and independent review, as recorded in the repository's development evidence. The demonstrated family assistant uses **`local_rules` with SQLite**. Its memory is owner-confirmed application data. The Alexa experience accepts typed speech-like requests in a browser; it has no live Alexa endpoint, microphone input or demonstrated physical device connection.

Optional Bedrock, Strands, AgentCore Memory and DynamoDB adapters have preparation or offline-test evidence. That evidence does not establish a live AWS invocation. The original Mochi workbench separately demonstrates owner approval, hard limits and success/failure/unknown receipts with simulated sensors and an actuator. Family manual care does not execute that actuator.

## Challenges

Shared care required careful handling of asynchronous state. Review reproduced delayed responses from one account appearing after a switch to another, invitation state surviving logout, and unsaved measurement fields following a pet switch. The fixes invalidate old responses and reset protected drafts at the relevant account or pet boundary.

We also needed confirmations to refer to the records actually reviewed. Server-held proposal versions and expiry checks reject stale confirmation. Tests distinguish scheduling from completion, preserve historical authors and sources, and check that failed report generation can recover. English interface support preserves user-entered names and notes instead of translating them as interface labels.

## Accomplishments

The local prototype connects confirmed memory, a second account, a care draft, explicit confirmation, manual completion and a source-backed report in one workflow. Caregiver access and the visit card extend the same records into a controlled handoff.

The **14 October historical audit** at commit **`6342b96`** passed **447 backend tests**, with **1 skipped and 21 live AWS tests deselected**, and **115 browser tests across four independent services with zero retries**. Ruff, generated-contract checks, TypeScript and the production build also passed in that audit. The 15 October working tree includes additional Pet Concierge work; `6342b96` must not be used as its final source identity.

A subsequent 15 October component audit returned **447 backend passed / 1 skipped / 21 deselected** and **122 browser passed** before the final repair/freeze. The repaired release's whole-tree checks and source identity are established separately in the [consolidated repair verification](../../evidence/submission-repairs-2026-10-15/verification.json) and [source release record](release-source.json), prepared by the finalization step. Earlier component results do not establish that final verification has completed. These local checks do not establish cloud, hardware or real-world effectiveness.

The active English film is **142.379 seconds at 1920 × 1080 and 30 fps**, with matching subtitles and poster. It shows the Mochi preference, simulator, explicit confirmation, Alex's recorded completion and daily report, followed by the labelled Miso/Luna scripted preview. Its mechanical video/audio checks passed; complete human playback/listening and public upload remain pending. Caregiver access, the visit card and memory deletion are additional runnable features, not scenes claimed for this film. See the [final film production record](final-video-production.md).

## What we learned

A useful pet context needs an identifiable source and a clear review status. A saved preference is usable only after confirmation, an answer grants no permission, and a task becomes completed only when a member records the action. Measurements, food offered, dispensing and actual intake also need separate meanings.

The review process showed why successful demonstrations need negative cases: switching account during a delayed read, changing a source before confirmation, revoking access and receiving an unknown device result. Those cases shaped the workflow as much as the happy path.

## What's next

We want to evaluate the workflow with consenting households before making claims about adoption or care outcomes. Technical next steps include reducing the frontend bundle, assessing accessibility across browsers and devices, and separately validating any chosen cloud/model integration. Real Alexa or hardware work would require its own integration and safety evidence.

For this entry, the proposed route is an **Alexa+ simulated experience built with Codex-assisted development**. Final track selection remains the participant's decision; acceptance is subject to organizer review. The local runtime remains labelled `local_rules` and SQLite.

## Review references

- [Judge setup and walkthrough](judge-guide.en.md)
- [Product Feedback participant-review draft](product-feedback.en.md)
- [Submission checklist](submission-checklist.md)
- [Final source identity](release-source.json) and [consolidated repair verification](../../evidence/submission-repairs-2026-10-15/verification.json), prepared by the finalization step
- [Historical 14 October source audit](../../reviews/current-version-2026-10-14.md), [backend log](../../evidence/current-version-2026-10-14/verify.txt) and [browser log](../../evidence/current-version-2026-10-14/e2e.txt)
- [English interface evidence](../../evidence/i18n-2026-10-14.md) and [15 October Pet Concierge evidence](../../evidence/workbench-concierge-2026-10-15.md)
- [Active final film](../../../../PawTwin-hackathon-submission-2026-10-15.en.mp4) and [film verification](../../evidence/submission-video-2026-10-15/fullfilm-01/verification.json)
- [Official rules](https://amazonappdev2026.devpost.com/rules)
