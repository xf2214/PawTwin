# Submission repair implementation plan

User-approved scope: resolve readiness items 1, 2 and 3 from the current audit.
Preserve current application behavior, original media, databases and historical deliveries.

## Ownership and execution

- lint_repair: only Python files under `docs/evidence/submission-video-2026-10-15/`;
  fix the 216 reported Ruff diagnostics without excluding files or rendering media.
- material_sync: only the four current English package entry/description/guide/checklist
  Markdown files and a new final-video production note under `docs/submission/2026-10-15/`.
- Coordinator: source export, final package tooling, tests, status/evidence, local Git freeze,
  final archive validation and remote setup when a destination is provided.
- Final reviewer: read-only review of repairs, source exclusions and archive consistency.

The working tree contains the intended 15 October application changes. Work serially in
these disjoint paths in this checkout; a new checkout from HEAD would omit those changes.
Do not reset, discard, overwrite original deliverables, create cloud resources or submit
Devpost. GitHub destination/visibility is missing and has been requested while local work continues.

## Tasks and acceptance

1. Snapshot editable source and hash original output files outside the checkout.
2. Repair video scripts; require whole-tree Ruff and Python compilation to pass.
3. Make the 142.379-second final film and its subtitles/poster/verification the active
   delivery, while retaining earlier 150/170-second versions as historical files.
4. Export a complete runnable source package including current concierge components,
   tests, contracts, lockfiles and current instructions. Exclude credentials, user data,
   browser traces, dependencies, build/cache output and private runtime records.
5. Package matching current materials and validate ZIP CRC, hashes, links, final video
   identity and source identity. Use new versioned names and refuse overwrites.
6. Run baseline verification, full browser tests, archive checks and an independent
   final review. Commit the complete repaired source locally. Publish only to the
   user-specified repository; keep missing account/access prerequisites explicit.

Remaining outside these repairs: complete human listening, public video upload,
personal Product Feedback, eligibility/rights declarations and Devpost submission.

## Execution result

Completed local code gates on16October:495backend tests,1skipped,21live-AWS deselected;122browser tests with zero retries; Ruff/contracts/TypeScript/build passed.48release-helper tests passed. Clean extracted application setup/build/API checks passed, and24original outputs retain their hashes. Archive preflight passed CRC/member hashes/41standalone links and single active142.379-second film. The actual final Git commit is recorded by the external canonical archive manifests. User requested local work only; external publication and participant fields remain separate.
