# PawTwin — local demonstration guide

Draft, 3 October 2026. This is a reproducible local demo, not a submitted entry or evidence of cloud deployment.

## Project description

PawTwin helps a household coordinate care around each pet's own records. Family members use independent local accounts to share profiles, photos, observations, care tasks and measured growth. A pet context connects these facts to confirmed preferences so the App and a labelled Alexa web simulator answer from the same information.

Members can claim, transfer and complete care with version checks. Growth reports calculate actual measurements and preserve missing data. A proposed care plan becomes a manual task only after explicit confirmation. The Mochi actuator demo retains its separate approval, limits and success/failure/unknown receipts.

The current extension uses local SQLite, salted password hashes, rule-based answers and owner-confirmed database memory. It does not use Cognito, AgentCore extraction, a real Alexa endpoint or real hardware. New family cloud storage and model inference remain unfinished; existing AWS adapter code is not deployment evidence.

## Three-minute walkthrough

The [timed Chinese presentation plan](PawTwin_展示方案_2026-10-03.md) provides the three-minute script, a five-minute live variant, staging data and recovery steps. Stage the two accounts before recording.

1. Start the built frontend with `scripts/dev-home.ps1`; open `/#app`. Register two demonstration accounts in separate browser profiles. Create a household, invite the second account and choose a family label. Show that a label does not change permissions.
2. Add a pet and record two genuinely entered demonstration measurements. Identify them as demo data when presenting them. A sample is 1.20 kg on September 25 and 1.35 kg on October 2: the change is 150 g, 12.5%, across seven actual days. Generate a report that contains both records and display its source IDs and time window.
3. Save “likes a feather toy” as a candidate memory. Confirm it. Ask about preferences in a new response from the second member's labelled Alexa simulator. Point out the shared context and the local-rule label.
4. Select the play-care type, enter the proposal, explicitly confirm it, then use the second account to claim and complete the resulting manual task. Show the real author. The owner chooses the type, title and time in this version.
5. Generate today's daily report and show one completed manual care occurrence. Delete the confirmed memory, refresh the second account, then ask again to show that the new answer stops using the deleted text.
6. Close with real/simulated/unimplemented boundaries. Include only measured test results and actual video footage. Never invent family feedback, a model request ID or a cloud login.

For the extended live demonstration, optionally open the old Mochi actuator workbench in a third, independent session using the original demonstration household. Show an approval-gated simulated action and its receipt. Keep actual intake separate from dispensed grams; a failed or unknown receipt must not be described as completed. A new household's Mochi profile does not inherit device execution permissions.

## Acceptance evidence

The latest local recheck is 284 passed backend tests, 1 skipped and 21 live tests deselected; 27 browser tests passed with no retries. It includes a two-account rehearsal with source IDs, 150 g / 12.5% / seven-day arithmetic, confirmed memory sharing, care completion and a daily report update. See [the fresh check report](../evidence/functional-check-2026-10-03.md). The [earlier implementation evidence](../evidence/extension-local-2026-10-03.md) and [independent review](../reviews/EXT-local-review-2026-10-03.md) remain historical; no new independent review was conducted in this recheck.
The backend computes arithmetic, sources and permissions. It does not diagnose a pet, predict proven hunger or translate animal language.

## Trial record template — unfilled

Invite 3–5 real households only after the access route, consent and data handling are ready. No household has been recorded as participating by this development session.

| Household pseudonym | Date / build | Care handoff before / after | Repeated questions | Preference reused correctly | Failure / feedback | Evidence permission |
|---|---|---|---|---|---|---|
| To be collected | | | | | | |

Record observations and timing rather than promises. Keep identifiable information and credentials out of public materials. Evaluate the real model separately with actual inputs, outputs, request IDs, latency and failures when it is connected.

Video recording, public access checks, final event eligibility and submission are pending. Recheck the chosen event's official rules before publishing or submitting; the older planning snapshot is not a current rules check.
