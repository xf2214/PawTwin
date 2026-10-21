# PawTwin

**Shared pet care, with context that stays with your household.**

[English](README.md) · [简体中文](README.zh-CN.md) · [Reviewer walkthrough](docs/submission/2026-10-15/judge-guide.en.md) · [Feature guide](docs/FEATURES.md)

[![Baseline checks](https://github.com/xf2214/PawTwin/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/xf2214/PawTwin/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

PawTwin brings pet profiles, shared care tasks, observations, confirmed preferences and growth records into one household workspace. Its Alexa-style web simulator shows how saved context can support a care conversation: review the sources, confirm a proposed task, and let another household member record completion.

![PawTwin product page with illustrative tablet and phone interfaces](docs/evidence/i18n-2026-10-14/product-en.png)

*Recorded interface preview; the product-page examples use fictional pets and illustrative data.*

> **Current scope:** a runnable local prototype with FastAPI, React and SQLite. Household conversations use local rules; Alexa and device interactions are simulations. Live AWS inference, AgentCore memory, real Alexa, hardware and production deployment have not been verified.

## What you can try

- **Care together:** local accounts, household invitations, roles, several pet profiles, care plans and completion records.
- **Keep context with its source:** observations and explicitly confirmed pet preferences, shared by the app and the text-based Alexa simulator.
- **Review before acting:** care requests become reviewable proposals; explicit confirmation creates a manual-care task.
- **Follow recorded growth:** measured weights, source-backed summaries, daily/weekly reports and missing-data labels.
- **Hand off carefully:** expiring, revocable, single-pet read-only caregiver access and printable/offline visit cards.
- **Explore the experience:** a product showcase, English/Chinese interface, pixel pet home and a scripted Pet Concierge preview.

The original workbench also demonstrates approval, hard limits, idempotency and simulated device receipts for the fictional pet Mochi. Recording a task as complete is a household record, not independent evidence that physical care occurred.

## Quick start

Install **Git**, **Python 3.12**, **uv**, **Node.js 24 with npm**, and **PowerShell 7** for the scripts below. Local use does not require an AWS account, Docker or AWS CLI.

```powershell
git clone https://github.com/xf2214/PawTwin.git
cd PawTwin
./scripts/setup.ps1
./scripts/verify.ps1
./scripts/dev-home.ps1 -Port 8000 -DatabasePath ./data/local-demo.db
```

Open **http://127.0.0.1:8000/#app/home**, register a local account with a password of at least 12 characters, then create or join a household. The first visit defaults to English; use **English / Chinese** in the header to switch. User-authored names and records keep their original text.

The launcher explicitly selects local rules and simulated services. Records persist in the chosen database and its adjacent `<DatabasePath>.family.db`; sessions are held in process memory, so sign in again after restarting the server. An unset database path in other launch methods may use in-memory storage.

| Local address | Experience |
| --- | --- |
| `http://127.0.0.1:8000/` | Product showcase with fictional examples |
| `http://127.0.0.1:8000/#app/home` | Household application |
| `http://127.0.0.1:8000/#alexa` | Typed-request Alexa web simulator |
| `http://127.0.0.1:8000/#workbench` | Original approval/device simulation workbench |
| `http://127.0.0.1:8000/#workbench/concierge` | Scripted Pet Concierge demonstration |

The workbench's default local demo passphrase is **`local-demo-passphrase`**. Enter it on the workbench sign-in screen. If `PAWTWIN_DEMO_PASSPHRASE` is set, use that value instead; keep any replacement private. See [configuration source](backend/pawtwin/config.py). Household registration uses a separate account flow. Local addresses require a running server; no hosted app or public video URL is provided here.

For development, run `./scripts/dev-backend.ps1` and `./scripts/dev-frontend.ps1` in separate terminals. Vite serves port `5173` and proxies `/api` to `8000`. Configuration options are in [.env.example](.env.example); never commit a real `.env`. On Windows, `PAWTWIN_NODE_DIR` can point to a compatible Node installation.

## Try the populated demonstration

To explore saved profiles, growth records, care plans, confirmed preferences,
reports and workbench outcomes, start a **separate, fresh local demo**:

```powershell
./scripts/dev-home.ps1 -Port 8861 -DatabasePath ./data/showcase-demo.db
```

Keep that terminal running. From another terminal in the repository, run:

```powershell
uv run --frozen python scripts/seed_demo.py --base-url http://127.0.0.1:8861 --state-dir data/portable-demo-state
```

Open **http://127.0.0.1:8861/#workbench**, sign in with the public default demo
passphrase shown on the page, then use **Household app** to view Mochi and Miso.
The importer saves English **fictional demo samples** through the existing APIs;
reports are calculated from those records. Dates follow the household day. It
refuses existing user records, cloud targets and a journal belonging to another
instance. Keep the ignored state directory for replay; rerunning a completed
import makes no business writes. Custom demo passphrases fail closed. See the
[demo walkthrough](docs/DEMO.md) for counts, scenarios and limitations. Databases
and session files are not distributed through GitHub.

## Verify the project

```powershell
./scripts/verify.ps1
uv lock --check
$env:PAWTWIN_E2E_PORT = '8001' # choose an unused port
./scripts/test-e2e.ps1 -InstallBrowser
```

`verify.ps1` runs backend tests, Ruff, generated-contract checks, TypeScript and the production build. Browser regression builds first, then runs five shards with fresh isolated services. Omit `-InstallBrowser` after installing Chromium, or set `PAWTWIN_BROWSER_EXECUTABLE` to an existing compatible Chromium executable. Default tests exclude billable live AWS checks.

GitHub Actions runs the baseline and browser suite on Ubuntu and Windows. The separate ECR image workflow is manual and requires separately authorized AWS configuration; ordinary pushes do not deploy the application.

## Repository guide

| Path | Contents |
| --- | --- |
| [backend/pawtwin/](backend/pawtwin/) | FastAPI, household storage, policy, workflows and optional adapters |
| [frontend/](frontend/) | React/TypeScript app, product showcase and Playwright scenarios |
| [contracts/](contracts/) | Generated OpenAPI and domain schemas |
| [tests/](tests/) | Backend, policy, isolation and recovery tests |
| [scripts/](scripts/) | Setup, launch, verification, export and optional cloud tooling |
| [infra/](infra/) | Optional deployment configuration and plans |
| [docs/](docs/) | Feature guides, architecture notes, dated evidence and submission preparation |

- [Features and usage](docs/FEATURES.md) · [Current implementation status](docs/STATUS.md) · [Taskboard](docs/TASKBOARD.md)
- [English reviewer setup and walkthrough](docs/submission/2026-10-15/judge-guide.en.md)
- [Repository publication notes and evidence](docs/REPOSITORY.md)
- [Agent collaboration contract](AGENTS.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)
- [Historical Chinese development log](README.history.zh-CN.md): preserved from the previous README; its dates, test totals, local ports and “not published” statements describe those historical runs.

Historical production records may reference MP4, ZIP or Word deliverables kept outside this Git repository. Those files are not runtime dependencies. Source publication does not establish video publication or competition submission.

## Capability boundaries

Local accounts and pet records are persisted in SQLite. Confirmed family preferences are application records, not verified AgentCore-extracted memory. Optional cloud adapters and offline adapter tests are included, but configuration or a passing local test does not establish a live cloud connection. The family cloud data layer remains unavailable.

The simulator accepts typed requests and keeps its conversation in page memory. Pet Concierge examples use preset replies and illustrative activity traces. Sensors, actuators and the PawLink wearable are simulated or conceptual. Growth reports and visit cards summarize recorded information; they do not provide clinical diagnoses or validated animal-language translation.

## License

[MIT](LICENSE) © 2026 xf2214. Third-party packages retain their own licenses. See [contribution guidelines](CONTRIBUTING.md) before sending a change.
