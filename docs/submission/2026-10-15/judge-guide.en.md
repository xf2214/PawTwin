# PawTwin judge guide

Updated 15 October 2026 for the complete repaired local working tree, including the Pet Concierge additions. The historical audited baseline is **`6342b96`**; the final source identity belongs in [release-source.json](release-source.json), prepared by the finalization step. This guide reproduces the household workflow with English interface text, local rules and SQLite. AWS credentials, Alexa hardware and a public hosted App are not required for this local demonstration. Repository/source access and a public video link remain external submission steps; the current work is local only.

## Capability matrix

| Capability | Demonstrated scope | Boundary |
| --- | --- | --- |
| Accounts and households | Local accounts, invitations, roles and several pet profiles | One application instance; no cloud identity |
| Pet memory | Owner-confirmed SQLite preferences shared across App and simulator | No demonstrated AgentCore extraction or live model memory |
| Care handoff | Draft, explicit confirmation, claim and authenticated manual completion | Family records do not actuate a device |
| Growth and reports | Timestamped measurements, source labels and deterministic daily/weekly calculations | Demo samples are fictional; no diagnosis or inferred intake |
| Caregiver access | One-pet read-only link with expiry and revocation | No membership, write, approval or device permission |
| Visit card | Preview, browser print and offline HTML export | Saved information; downloaded copies do not update automatically |
| Alexa experience | Independent typed-request browser simulator | No live Alexa endpoint or microphone input |
| Pet Concierge preview | Fictional Miso/Luna profiles, preset replies and illustrative activity traces on the product page and workbench | No runtime model, actual tracking, diagnosis, private family-data reads or task creation |
| Original workbench | Approval and hard limits with simulated receipts | Sensors and Mochi actuator are simulated |
| Optional AWS paths | Adapter wiring and offline tests | Live Bedrock, AgentCore and DynamoDB not demonstrated |

## Setup and build

The tested workflow targets Windows/PowerShell. Install Git, Python **3.12**, `uv`, and a compatible Node.js/npm runtime. Node **24** is recommended; the runtime helper accepts Node 20.19+, 22.12+ or newer supported majors. Initial locked dependency and browser installation needs network access. Docker and AWS CLI are optional.

From the project root:

```powershell
./scripts/setup.ps1
./scripts/preflight.ps1
./scripts/verify.ps1
./scripts/dev-home.ps1 -Port 8860 -DatabasePath ./data/judge-demo-20261015.db
```

`verify.ps1` also builds the frontend. Keep the server terminal open. Use a fresh disposable database filename for each clean rehearsal and an unused port; do not reset an existing database or stop an unrelated service. If Node selection needs to be explicit, pass `-NodeDirectory <directory>` to setup/verification or set `PAWTWIN_NODE_DIR` for the process.

Open [the local App](http://127.0.0.1:8860/#app/home). The first visit defaults to English; **English / 中文** switches interface language. Saved user text remains in its original language. Entry points are `/` for the product website, `/#app/home` for the household App, `/#alexa` for the simulator, `/#workbench` for the optional device demonstration and `/#workbench/concierge` for the scripted Pet Concierge preview. The workbench keeps its existing demo-login protection; use the local setup instructions for access and do not include credentials in public materials.

The launcher binds only to `127.0.0.1`, pins family `local_rules` and workbench `local_fake`, disables photo recognition and uses `--no-proxy-headers`. Family records are stored in `<DatabasePath>.family.db`; the original receipt store uses `<DatabasePath>`. Records survive restart, but the server restart requires another login. `/healthz` should respond `{"status":"live"}`. A degraded local `/readyz` is not a cloud-readiness claim.

## Family care walkthrough

Use **two independent browser profiles or contexts**. Tabs in one profile share login cookies. Keep passwords, invitation tokens and caregiver tokens out of public footage. All accounts and records below are fictional staging data.

1. In the owner profile, register a unique local account with a password of at least 12 characters. Create a household and select Mochi. Use the same browser and household time zone for the example; Asia/Shanghai matches the recorded rehearsal.
2. In Family, generate a carer invitation. Register a second account in the other profile and join with the invitation. A family display label such as “Dad” does not grant administrator permission.
3. In Twin, save “Likes a feather toy and rests after meals” as candidate memory. Ask the simulator **“What does it like?”** before confirmation. The candidate must not be presented as confirmed memory. Confirm it in the owner profile, start a new simulator session in the carer profile and ask again. Inspect the source record ID and `local_rules` label. No live model request ID is expected.
4. In the owner's simulator, enter **“plan playtime”**. Inspect the draft and choose a concrete due time. Prepare the pending proposal, then explicitly confirm the manual-care arrangement. Drafting and preparation alone must not create a care task; confirmation must create one manual task. No device executes.
5. In the second profile's Care section, refresh, claim that task and record its completion for this fictional example. In the owner's Growth reports, generate a daily report for the household-local date. In a fresh database, expect one manual completion and its source record. The automated rehearsal also checks the authenticated completing user; the completion record does not independently verify a physical action.

Steps 3–5 form the recorded family-care sequence in the active [142.379-second final film](../../../../PawTwin-hackathon-submission-2026-10-15.en.mp4). The film then shows the scripted Pet Concierge preview and the local/simulator boundary. Account registration and invitation are setup requirements rather than claimed film scenes. See [final video production](final-video-production.md) for the exact scene scope and verification limits.

The simulator keeps at most 20 turns in page memory. New session, refresh, leaving the page, switching pet or account clears the conversation. Household records remain. Natural-language dates are not parsed; select the time in the draft. If context changes or expires, ask again rather than confirming an old proposal. An uncertain connection is not a completed task: inspect persisted task status before retrying.

## Additional runnable features

The following checks are supported by the application but are not claimed as scenes in the active final film:

1. Delete the confirmed memory. Ask a fresh question in the other profile. The new answer must stop citing that record. Earlier replies remain historical snapshots.
2. Add two **Demo sample** weights: 1.20 kg at 25 September 2026 12:00 and 1.35 kg at 2 October 2026 12:00. Generate the 2 October weekly report. Expect 150 g, 12.5% and seven elapsed days. The earlier measurement is the comparison baseline before the weekly window. Missing intake remains “not recorded.”
3. Create a short-lived, one-pet read-only caregiver link in Family, view it in an independent context, then revoke it and revisit. The view must become invalid. In Growth, preview/export the visit card. Demo measurements are excluded by default; including them requires an explicit choice and retains their demo source label.
4. Open the product page's Pet Concierge section or `/#workbench/concierge`. Inspect Miso's food/preference scenario, Luna's illustrative activity scenario and the new-session/context comparison. Confirm the fictional/preset/simulated labels in English and Chinese. These displays are scripted UI examples; they do not use live inference, observe a real animal, diagnose a condition, read household records or create a care task.

## Reproduce the checks

In another terminal from the project root, use an unused test port:

```powershell
./scripts/verify.ps1
$env:PAWTWIN_E2E_PORT = '8861'
./scripts/test-e2e.ps1 -InstallBrowser
```

Omit `-InstallBrowser` after Chromium is installed. Alternatively set `PAWTWIN_BROWSER_EXECUTABLE` to an existing compatible Chromium executable. The script rebuilds once and runs four shards against fresh isolated services; it does not weaken account-registration limits or reuse the file-backed judge database.

Historical 14 October results at `6342b96` are **447 backend passed / 1 skipped / 21 live AWS deselected**, and **115 browser passed / 0 retries**. Ruff, generated contracts, TypeScript and production build passed in that historical audit. The skipped test is `test_kill_a_running_server_mid_analysis_then_relaunch`; successful process-reopen tests do not replace that unexecuted service-kill case. The suite covers local account isolation, roles, stale confirmation, report sources, delayed response handling, revocation and simulated receipt outcomes.

A later 15 October component audit recorded **447 backend passed / 1 skipped / 21 deselected** and **122 browser passed**. Those runs preceded the final lint/package repairs. The [consolidated repair verification](../../evidence/submission-repairs-2026-10-15/verification.json), prepared by the finalization step, must establish the repaired whole-tree result, archive checks and remaining limits. The [source release record](release-source.json) and matching external source manifest must identify the exact final ZIP and local freeze commit. This guide does not substitute earlier component results for that final verification.

## Review evidence

- [Final source identity](release-source.json) and [consolidated repair verification](../../evidence/submission-repairs-2026-10-15/verification.json), prepared by the finalization step
- [Historical 14 October audit](../../reviews/current-version-2026-10-14.md), [backend verification](../../evidence/current-version-2026-10-14/verify.txt) and [browser verification](../../evidence/current-version-2026-10-14/e2e.txt)
- [English interface verification](../../evidence/i18n-2026-10-14.md)
- [Two-account rehearsal source](../../../frontend/e2e/demo-rehearsal.spec.ts)
- [Caregiver and visit-card evidence](../../evidence/platform-2026-10-12.md)
- [Product-page Pet Concierge evidence](../../evidence/pet-concierge-2026-10-15.md) and [workbench Pet Concierge evidence](../../evidence/workbench-concierge-2026-10-15.md)
- [Active final-film production record](final-video-production.md), [mechanical verification](../../evidence/submission-video-2026-10-15/fullfilm-01/verification.json) and [delivery hashes](../../evidence/submission-video-2026-10-15/fullfilm-01/delivery.json)
- [Official rules](https://amazonappdev2026.devpost.com/rules) and [organizer FAQ](https://amazonappdev2026.devpost.com/details/faqs)

Browser verification was on Windows/Chromium. Remote Linux CI, production deployment, real household trials, live AWS inference, Alexa hardware and physical actuator behavior are not established by this guide.
