# PawTwin submission readiness implementation plan

> For agentic workers: use the verification and debugging workflows for each bounded repair. Preserve the complete dirty checkout; no branch changes, reset, cloud calls or publication.

**Goal:** Check the candidate Build, Ship, Shape entry against current official requirements, repair verified blockers, and deliver a current, reproducible local demo and review package.

**Architecture:** Retain the existing product, App, Alexa web simulator and workbench. Separate local execution evidence from optional Bedrock wiring and unverified cloud deployment. Final external publication and participant declarations require the user's decisions.

**Tech stack:** Existing FastAPI/Python 3.12/SQLite/React/TypeScript/Playwright; existing offline video renderer and source exporter.

**Requirements:** User request on 2026-10-11; `AGENTS.md`, current source and https://amazonappdev2026.devpost.com/rules.

## Ownership and baseline

- Baseline: `31da349`, `chore/bootstrap`, plus all existing modified and untracked files.
- Coordinator: this plan, evidence/status/board/index documents, final validation and artifact inspection.
- Coordinator after technical_audit findings: serialized security repairs in `api.py`, `workflow.py`, repository protocol/adapters and corresponding tests. No model/schema/lock changes without coordination.
- demo_audit: `frontend/e2e/demo-rehearsal.spec.ts`, `scripts/capture-demo.ps1`, `scripts/render-submission-video.py`, `scripts/export-review-source.py`, demo/source/video guides. No product UI/API changes.
- rules_audit: dated rules checklist, `project-description.en.md`, `judge-guide.en.md`, `product-feedback.en.md`. No shared status/index files.
- All workers share the complete existing checkout with disjoint write paths; no baseline is copied from HEAD, which omits current work.

## Task 1: Reproduce and repair hard-policy/authentication defects

- [x] Prove the observed cross-run quota race with deterministic, independent file-backed connections; write the regression before production changes.
- [x] Prevent execution beyond hard limits with an atomic persisted owner/pet reservation or equally safe storage operation. Cover unknown receipt/restart/idempotency paths; fail closed in unsupported adapters.
- [x] Prove spoofed forwarded-client-IP rotation bypasses the configured login limit; define and enforce the trusted proxy boundary and cover family authentication.
- [x] Run relevant regressions, then independent code review and the full baseline.

## Task 2: Refresh demonstrable product evidence

- [x] Update the existing two-account rehearsal to include the current product page and independent `/#alexa` entry.
- [x] Exercise unconfirmed/confirmed/deleted memory, source IDs, Alexa draft → prepared proposal → explicit confirmation → carer completion → current report.
- [x] Record new isolated local evidence without touching user data. Keep every simulated/local label and old capture.
- [x] Rebuild a current English video under 180 seconds. Derive replay cut points from current evidence or use accurate screenshots; remove stale account-review statements.
- [x] Inspect decoded video frames, captions, metadata and audio statistics; distinguish automated inspection from human full listening.

## Task 3: Current submission materials and reproducibility

- [x] Recheck official deadline, track requirements, source access/license, video, tool feedback, eligibility and rights; map each gate to evidence.
- [x] Refresh English project/architecture, new simulator controls, judge steps and actual-tool feedback. State whether each capability is wired, offline-tested, actually invoked or unverified.
- [x] Include current code, captures and logs in a new non-destructive source archive; verify CRC, per-file hashes and current required files.
- [x] Run final local baseline/browser verification and open the runnable demo for review.
- [x] Record remaining external gates explicitly: eligibility/registration, actual AI/agentic-tool evidence, repository sharing/license, public video and formal submission.

## Review focus

- Two different pending runs sharing one feeding quota, including separate repository connections.
- Unknown execution receipts or process interruption must not release uncertain quota.
- Caller-controlled forwarded-header prefixes cannot change rate-limit identity.
- Re-recorded video narration must describe current displayed actions and measured source evidence.
- Passing local tests never upgrades real AWS/Alexa/hardware or participant eligibility claims.
