# Repository publication

The source repository is [xf2214/PawTwin](https://github.com/xf2214/PawTwin). Its public development branch is `main`. The original local checkout uses `chore/bootstrap`; publishing that branch to `main` preserves the existing commit history without renaming or replacing the local working branch.

## Repository contents

The repository contains runnable application code, lockfiles, configuration templates, tests, documentation and dated synthetic demonstration evidence. The English [README](../README.md) and [Chinese README](../README.zh-CN.md) are the current entry points. The [previous README](../README.history.zh-CN.md) is retained verbatim as historical context.

Private `.env` files, credentials, SQLite databases, household data, dependencies, build output, browser traces and generated deployment state are excluded. Some older synthetic demonstration media remain in history and evidence. New large render intermediates are ignored. No single existing Git blob exceeds GitHub's 100 MiB file limit.

The application remains the local rules/SQLite/web-simulator prototype described in the README. GitHub publication is source access, not a hosted application, live AWS validation, video publication or Devpost submission.

## Dated documents and media

`docs/STATUS.md`, `docs/TASKBOARD.md`, reviews and evidence retain their original dates. Statements such as “no remote”, “not pushed” or historical test counts describe those runs. They are not the current repository publication status.

Some historical submission documents link to sibling MP4, ZIP, SRT or Word files outside this repository. Those files remain in the local delivery workspace and are not needed to run or test the source. There is no public final-film URL recorded here. Consult the current README before following historical local ports or setup instructions.

## Checks and workflow

The baseline Actions workflow runs on Ubuntu and Windows for pushes and pull requests, with read-only repository permissions. It checks locked dependencies, backend tests, lint, contracts, frontend types/build and isolated browser regression. The ECR image workflow stays manually triggered and is not part of ordinary source publication.

Local verification for this publication is recorded in [the 17 October publication record](evidence/github-publication-2026-10-17.md). Remote workflow results are visible in [GitHub Actions](https://github.com/xf2214/PawTwin/actions).

## License and feedback

The owner selected the [MIT license](../LICENSE) on 17 October 2026. Dependency licenses remain separate. Use the [contribution guide](../CONTRIBUTING.md), issue templates and [security reporting instructions](../SECURITY.md) for feedback.
