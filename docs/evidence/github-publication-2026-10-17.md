# GitHub source publication — 17 October 2026

## Scope

The owner authorized upload to the existing public [xf2214/PawTwin](https://github.com/xf2214/PawTwin) repository, repository description and documentation improvements, and explicitly selected MIT licensing. The local baseline was `05c4a2f8f8ef8c6c3d7c85395a93c006fdefe114` on `chore/bootstrap`, with a clean worktree and no remote configured.

The publication retains the existing Git history and the original local branch. English/Chinese READMEs replace the chronological root entry; `README.history.zh-CN.md` matches the original README blob `feea604b4e826f930387c176e4e582f4dc9f2eeb` exactly. Community instructions and Issue/PR templates were added. Application behavior, dependencies and user data were not changed.

The source exporter now retains the MIT license, public documentation and the screenshot referenced by the README. A regression test first failed on the missing archive entries and is required to pass before publication. Existing dated source/media archives are preserved rather than overwritten.

## Publication review

A read-only independent audit inspected all 37 existing commits, 1,567 historical paths and 1,548 unique reachable blobs. It found no real `.env`, database/data directory, credential/private-key file, dependency tree, browser trace ZIP or storage-state file. Strong credential, JWT, long Bearer and session-cookie patterns had zero matches; this is a pattern scan, not image/video OCR. Fixed password literals are local test/demo fixtures. Four historical MP4 blobs are below 28 MB each; no blob exceeds 100 MiB.

Historical evidence retains local filesystem paths and normal Git author metadata. Screenshots, sample identities and demonstration media are documented as synthetic. No history rewrite was needed. No new font binary or third-party media was added.

## Verification

- `./scripts/verify.ps1`: 495 backend passed, 1 skipped, 21 live-AWS deselected; Ruff, generated contracts, TypeScript and production build passed before the exporter update.
- `uv lock --check`: passed; dependency locks unchanged.
- The first browser attempt could not launch because the installed Playwright browser revision did not match the current test package. The rerun uses installed Google Chrome through `PAWTWIN_BROWSER_EXECUTABLE` on isolated test port `8871`; application assertions and retry settings are unchanged.
- After the exporter update, `uv run --frozen pytest`: **496 passed, 1 skipped, 21 live-AWS deselected** in 56.77 seconds. The source-release suite has **49 passing tests**; full Ruff and `git diff --check` pass.
- **66 local links** in the new public entry documents resolve. The archived README matches the original Git blob. An actual source archive passed CRC, retained exact license/Chinese README bytes, and selected 504 files.
- Application identity remains `1ce9d0ba3c2221d58268f4704dd417d955edf3e35387e42644f4986791ca96be`, matching the existing release record. No application code or dependency changed.
- `PAWTWIN_E2E_PORT=8871` and the installed Chrome executable with `./scripts/test-e2e.ps1`: **122 browser tests passed** (32 + 37 + 23 + 30), four fresh services, zero retries. Final process exit code was 0.

Existing warnings: Starlette/AnyIO deprecation and a Vite bundle above 500 kB. Live AWS tests are deselected by default; the explicit running-service-kill test remains skipped. These results do not establish cloud, production or real-household validation.

## Repository configuration

The public repository description and nine topics were set. Issues remain enabled, the unused Wiki is disabled, merged branches can be deleted automatically, and private vulnerability reporting is enabled. The baseline CI is retained for Ubuntu/Windows. The ECR image workflow remains manual and was not invoked.

Push permission was verified with `git push --dry-run origin HEAD:refs/heads/main`. GitHub Actions is enabled. The final remote commit, rendered README, detected license and workflow outcome are checked through GitHub after upload; current results are available from the repository and its Actions page. Source publication does not publish the final film, deploy AWS resources, send messages, or submit the competition.

## First upload and remote CI portability repair

The first upload, `809cbcdae9e3dee376f43dbb10b18821f02a1f74`, was verified against remote `main`; the remote README blob matched the local commit, GitHub detected MIT, and all 1,576 remote files were listed without a truncated tree or sensitive runtime-path match. The rendered README returned HTTP 200 and contained the quick start, prototype boundary and screenshot. Description/topics and private vulnerability reporting were read back successfully.

The [first remote workflow](https://github.com/xf2214/PawTwin/actions/runs/38999098136) exposed an existing Linux launcher defect: `Get-Command node` returned both the setup-node installation and `/usr/local/bin/node`. Reading `.Source` produced an array, which PowerShell then treated as one invalid executable path. The fix selects the first application, preserving PATH precedence; npm discovery already does this. This changes runtime discovery only, not product behavior.

A subprocess regression returns two Node matches and checks actual discovery, version execution and npm resolution. It reproduced the same invalid combined-path failure before the fix. Afterward **50 targeted tests passed**, full Ruff and whitespace checks passed, and the local runtime preflight selected Node 24/npm successfully without an AWS call. An independent reviewer confirmed the cause and fix. The follow-up push reruns the full Ubuntu/Windows matrix; its current result is visible on [Actions](https://github.com/xf2214/PawTwin/actions).
