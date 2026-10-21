# PawTwin — Developer Friction Log

Prepared: 21 October 2026  
Project: [PawTwin](https://github.com/xf2214/PawTwin)

This log records four issues encountered while developing and verifying PawTwin. Each entry identifies the task, steps, expected and actual results, project impact, workaround or fix, validation and an actionable suggestion.

Dates refer to the supporting development records. Test counts are historical results from those records, not claims that the suites were rerun when this document was prepared. Severity reflects the effect on this project's workflow: **High** blocked a complete verification workflow; **Medium** disrupted testing or its isolation and had a bounded workaround or fix.

These entries concern local configuration, project scripts and application test integration. They do not establish an outage or defect in an AWS service. The documented prototype uses local rules and an Alexa-style browser simulator; live AWS and Alexa integrations remain unverified.

## Summary

| ID | Issue | Tools or API involved | Recorded date | Severity | Recorded outcome |
| --- | --- | --- | --- | --- | --- |
| FL-01 | Multiple runtime paths broke CI startup | PowerShell, GitHub Actions | 17 October 2026 | High | Launcher fixed; regression added |
| FL-02 | Browser revision mismatch prevented test startup | Playwright | 17 October 2026 | Medium | Rerun with installed Chrome passed |
| FL-03 | Developer configuration leaked into local tests | pytest, optional AWS SDK path | 14 October 2026 | Medium | Explicit fixture isolation; regression checks passed |
| FL-04 | Expanded browser tests reached registration limits | Playwright, PawTwin registration API | 21 October 2026 | Medium | Five isolated shards passed |

## FL-01 — Multiple runtime paths broke CI startup

**Recorded date:** 17 October 2026  
**Severity:** High — blocked the Linux verification workflow.  
**Issue ownership:** PawTwin's runtime-discovery script.

**Task attempted:** Run the project's verification workflow in GitHub Actions on Ubuntu and Windows.

**Steps taken:**
1. Publish the source and run the cross-platform workflow.
2. Let the project's PowerShell launcher discover Node using `Get-Command node`.
3. Use the discovered executable to run the development checks.

**Expected result:** Discovery selects one executable according to PATH precedence, and verification continues.

**Actual result:** On Linux, discovery returned both the setup-node installation and `/usr/local/bin/node`. Our script read the results as an array and treated them as one executable path, causing startup to fail.

**Workaround or fix:** Select the first application result before reading its path, preserving PATH precedence. Add a subprocess regression that supplies two matching Node executables and checks actual runtime and npm resolution.

**Recorded validation:** The regression reproduced the combined-path failure before the fix. After the fix, 50 targeted tests passed, static and whitespace checks passed, and the local preflight selected a working Node/npm pair. These are the checks recorded for this repair; this entry does not report a new CI run.

**Actionable suggestion:** Cross-platform starter scripts should explicitly handle multiple executable matches, print the selected path and test this condition. This would make runtime-discovery failures easier to diagnose before a full workflow starts.

**Evidence:** [Publication and CI repair record](../evidence/github-publication-2026-10-17.md), [runtime-discovery script](../../scripts/node-runtime.ps1), [original CI attempt](https://github.com/xf2214/PawTwin/actions/runs/38999098136).

## FL-02 — Browser revision mismatch prevented test startup

**Recorded date:** 17 October 2026  
**Severity:** Medium — browser verification could not start until the environment was corrected.  
**Issue ownership:** Local browser installation and test configuration.

**Task attempted:** Run the browser regression suite before source publication.

**Steps taken:**
1. Build the frontend and start the project's browser-test runner.
2. Attempt to launch the browser expected by the installed Playwright test package.
3. Inspect the launch failure before changing the application tests.

**Expected result:** A compatible browser launches and executes the test scenarios.

**Actual result:** The installed Playwright browser revision did not match the current test package, so browser launch failed before the scenarios could run.

**Workaround or fix:** Set `PAWTWIN_BROWSER_EXECUTABLE` to an installed Google Chrome executable and rerun against an isolated local test service. Keep application assertions and retry settings unchanged.

**Recorded validation:** All 122 browser tests passed across four fresh services, with zero retries.

**Actionable suggestion:** Add a preflight report showing the browser revision expected by the test package, the executable selected and the exact installation or configuration command needed. Report a browser-launch failure separately from an application assertion failure.

**Evidence:** [Publication verification record](../evidence/github-publication-2026-10-17.md), [Playwright configuration](../../frontend/playwright.config.ts), [browser-test runner](../../scripts/test-e2e.ps1).

## FL-03 — Developer configuration leaked into local tests

**Recorded date:** 14 October 2026  
**Severity:** Medium — undermined local test isolation and reproducibility.  
**Issue ownership:** PawTwin's test-fixture configuration.

**Task attempted:** Keep local backend tests on the explicitly selected local response path when a developer configuration file is present.

**Steps taken:**
1. Review local test fixtures that construct application settings.
2. Exercise them with a temporary `.env` file selecting the optional Bedrock response path.
3. Add a guard that fails if a local test tries to initialize the cloud client.

**Expected result:** Local fixtures ignore unrelated developer configuration, return local-rule responses and do not initialize an AWS client.

**Actual result:** Some fixtures implicitly loaded `.env`, allowing developer model settings to affect local test execution and potentially select the Bedrock path. The record does not establish that a live AWS request or charge occurred.

**Workaround or fix:** Explicitly disable dotenv loading in the affected local fixtures with `_env_file=None`. Use temporary configuration files and cloud-client guards for regression checks, without reading or modifying a developer's actual settings.

**Recorded validation:** Six test modules received explicit isolation. Ten regression cases checked configuration isolation, including local chat responses and cloud-client rejection.

**Actionable suggestion:** Provide a dedicated local-test configuration entry point that disables implicit configuration-file loading. Add an environment-contamination regression and a guard against unintended cloud-client initialization.

**Evidence:** [14 October review and repair record](../reviews/current-version-2026-10-14.md), [configuration-isolation regressions](../../tests/test_local_fixture_isolation.py).

## FL-04 — Expanded browser tests reached registration limits

**Recorded date:** 21 October 2026  
**Severity:** Medium — interrupted complete browser verification.  
**Issue ownership:** Test workload and service isolation; the application limit remained in force.

**Task attempted:** Run the expanded account-isolation and response-provenance browser scenarios.

**Steps taken:**
1. Add the new scenarios to the browser suite.
2. Run the existing four-shard setup, creating test accounts through the normal registration API.
3. Inspect later registration failures and compare them with the service's registration limit.

**Expected result:** Each scenario obtains its test accounts and completes without exhausting the service's registration allowance.

**Actual result:** The expanded scenarios exceeded the existing allowance in the four-shard run. Later registration requests returned HTTP 429 and interrupted verification.

**Workaround or fix:** Increase the runner to five shards, each using a fresh isolated service and database. Preserve production registration limits and keep retries disabled.

**Recorded validation:** All 129 browser tests passed across the five shards: 26, 28, 25, 37 and 13 tests, with zero retries.

**Actionable suggestion:** Document account-creation budgets for end-to-end suites and provide a fresh-service fixture for each shard. Classify registration throttling separately in test reports so it can be distinguished from a failed business-workflow assertion.

**Evidence:** [21 October verification record](../evidence/github-update-2026-10-21.md), [isolated browser-test runner](../../scripts/test-e2e.ps1).

## Scope of the results

The fixes and workarounds above were validated as described in the dated evidence. This document does not claim live AWS inference, AgentCore memory extraction, real Alexa access, physical-device operation or production deployment. The older [engineering friction record](product-feedback.en.md#evidence-backed-friction-log) remains available as historical context.

