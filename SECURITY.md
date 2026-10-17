# Security

PawTwin is a local prototype. The maintained development line is `main`; historical snapshots do not receive separate security backports. Local test results do not establish production or cloud security readiness.

## Report a vulnerability

Use GitHub's private [Report a vulnerability](https://github.com/xf2214/PawTwin/security/advisories/new) flow for this repository. Do not put credentials, household records, private photos or working access tokens in a public issue or pull request.

Include the affected commit, setup, reproduction steps using synthetic data, expected/observed behavior and likely impact. Redact identifiers and secrets from logs. There is no guaranteed response time or bug bounty program.

## Local operation

- Use the supplied launcher on `127.0.0.1` with a dedicated local database.
- Keep private configuration out of Git. `.env.example` is a template, not a credential store.
- Household sessions are process-local. SQLite data persists only when using a file path; protect and back up the associated files outside the repository.
- The built-in workbench demo gate is public local test configuration. It is not suitable for a publicly reachable service.
- Do not treat a recorded manual completion, model reply or retrieved memory as permission to execute an action.

Cloud deployment, proxy trust, TLS, credentials, resource budgets and operational monitoring require their own review. Consult [AGENTS.md](AGENTS.md) and [current status](docs/STATUS.md) before changing these boundaries.
