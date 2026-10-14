# PawTwin current local demonstration runbook

Prepared 11 October 2026 for the current product page, household App and independent Alexa web simulator. This run uses local accounts, SQLite, confirmed database memory and local rule answers. It invokes no cloud service, microphone, Alexa platform or physical device.

## Reproducible preparation

Install Python 3.12, uv and compatible Node/npm (Node 24 recommended). From the actual current source directory:

```powershell
./scripts/setup.ps1
./scripts/preflight.ps1
./scripts/verify.ps1
./scripts/dev-home.ps1 -Port 8807 -DatabasePath ./data/judge-demo-2026-10-11.db
```

Use a fresh named database for another clean run; preserve any existing user database. Keep the server terminal open and open `http://127.0.0.1:8807/`. The same server serves the built UI and API. Local `/readyz` is degraded; `/healthz` establishes process liveness. Family records use the companion `.family.db`; restarting requires signing in again.

Use two separate browser profiles or contexts for the owner and carer. Create independent local accounts (passwords at least 12 characters), create a household and join with its actual invitation. An account's family display label does not grant administrator permission. Set Asia/Shanghai for the demonstration; browser-local care times and household report dates must refer to the same intended day.

## Actual walkthrough

1. Open the product page. Its device/room illustrations and cases are labelled previews; the following App actions are actual local operations.
2. In the owner's App Growth section, record weight demo samples of 1.20 kg at 2026-09-25 12:00 and 1.35 kg at 2026-10-02 12:00. Generate the 2 October weekly report. Check 150 g, 12.5%, seven actual days; expand record IDs/version and preserve unrecorded intake.
3. In Assistant, save `喜欢羽毛棒，饭后先休息` as a candidate. In the carer's independent `/#alexa`, ask `它喜欢什么`. The candidate must not appear. The owner explicitly confirms the memory.
4. Sign the carer into a fresh authenticated session and open `/#alexa`. Ask the same question; inspect the source record ID, `local_rules` label and absent real model request. Click New session, verify the transcript is empty, then ask again. Household memory remains; this is current-record reuse, not cloud extraction or persistent chat history.
5. In the owner's `/#alexa`, enter `安排陪玩`. Inspect the actual rule draft for `陪 Mochi 玩耍`, select an explicit care time (already due for the staged demonstration), and prepare the proposal. **No task exists before confirmation.** Explicitly confirm manual care. It is arranged and awaiting a person, with no device execution.
6. In the carer's App Care section, sync the shared record, claim the task and record completion. Open Household activity to see the completing person. The automated evidence additionally checks `completed_by`, occurrence ID and `manual_care` provenance.
7. Return to `/#alexa`, ask `最近完成了什么`, and inspect the actual occurrence source. The owner generates today's daily report, which counts one manual completion.
8. Delete the confirmed memory in the owner's Assistant. Start a new Alexa page session in the carer's context and ask again. The new answer omits the preference and deleted source; historical replies are not rewritten.

## 2:50 presentation

Show the product introduction briefly, then records/report sources, owner memory confirmation, the carer's shared-context answer/new session, owner draft/time/preparation/confirmation, carer completion, simulator result/daily report, deletion and the scope card. Omit registration typing and long waits from the review edit. The original `/#workbench` approval/simulated-actuator workflow is a separate optional appendix, not the manual-care execution shown here.

The current renderer targets 170 seconds using complete actual screenshots. It generates exact scene/subtitle timecodes from full offline narration lengths; it does not reuse old raw-video seek positions. Raw dual-account videos remain available for checking the original actions. AWS account review has cleared, but this local capture supplies no live AWS/model/AgentCore/Alexa/hardware evidence.

## Capture and rebuild

After the main browser suite finishes, use a new directory on an unused port:

```powershell
./scripts/capture-demo.ps1 -Port 8813 -OutputDirectory docs/evidence/hackathon-capture/2026-10-11-final
# Separate Windows production environment with installed NumPy/Pillow:
& '<installed production Python>' scripts/render-submission-video.py `
  --capture docs/evidence/hackathon-capture/2026-10-11-final `
  --output docs/evidence/submission-video-2026-10-11/local-review-01
```

Do not overwrite a nonempty capture/video directory. The automated rehearsal saves fourteen actual PNGs, silent owner/carer WebM, API evidence, report JSON, logs and hashes. Screenshot elapsed milliseconds are test timestamps, not exact video seek positions. The renderer requires Windows SAPI, English voice/fonts and Media Foundation; see the [production guide](video-build-guide.md).

Verify the actual MP4 duration/codecs, decoded frames, captions, decoded AAC statistics and manifests. Record complete human viewing/listening separately; automated checks do not perform it. Public video/source access, contributor feedback/rights/eligibility and final submission remain release gates. Never replace the old capture or video while refreshing this version.
