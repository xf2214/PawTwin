# Contributing to PawTwin

Thanks for helping improve shared pet care. Start with the [README](README.md), [feature guide](docs/FEATURES.md) and [current status](docs/STATUS.md). Agent-assisted changes must also follow [AGENTS.md](AGENTS.md).

## Propose a change

Use an issue for reproducible bugs or a focused feature proposal. Describe the user problem, affected experience and expected result. For security findings, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

Create a branch from `main` and keep each pull request focused. Preserve the separation between the public showcase, household app and original simulation workbench. Keep English/Chinese system text aligned and preserve user-authored text.

## Develop and check

Use Python 3.12, uv, Node 24/npm and PowerShell 7. Install locked dependencies with `./scripts/setup.ps1`; avoid unrelated dependency updates.

```powershell
./scripts/verify.ps1
uv lock --check
$env:PAWTWIN_E2E_PORT = '8001'
./scripts/test-e2e.ps1 -InstallBrowser
git diff --check
```

Use an unused browser-test port. Omit `-InstallBrowser` when Chromium is already available. Browser tests create isolated services; do not run them against another person's preview or data. Live AWS markers are excluded by default and require separate authorization and budget.

Python models are the contract source. When changing them, regenerate with `uv run --frozen python scripts/export_contracts.py` and include the resulting contract changes. Add meaningful regression coverage for permissions, state transitions, stale context, concurrency, hard limits or side effects. Documentation-only changes need link and consistency checks rather than tests that compare prose.

## Preserve the product boundaries

- Model text and retrieved context never grant access, approve actions or override hard limits.
- Explicit confirmation is required before creating proposed care tasks or approving simulated feeding.
- Keep local rules, scripted examples, simulations and live cloud evidence labeled accurately.
- Do not include real household data, photos, passwords, tokens, `.env`, databases, browser traces or deployment state in commits and reports.
- Never introduce AWS calls, resource creation, deployment or publishing as an automatic side effect of local setup or testing.

In the pull request, explain the user-visible result, relevant checks and any remaining limits. Use synthetic data in screenshots. Code contributions are provided under the repository's [MIT license](LICENSE); third-party material must retain its applicable notices.
