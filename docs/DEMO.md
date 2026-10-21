# Populated local demonstration

This walkthrough creates fictional usage records in a new local demo instance.
It does not import anyone's household database or start cloud services.

After the README setup/build steps, start a separate fresh database:

```powershell
./scripts/dev-home.ps1 -Port 8861 -DatabasePath ./data/showcase-demo.db
```

In a second terminal at the repository root:

```powershell
uv run --frozen python scripts/seed_demo.py --base-url http://127.0.0.1:8861 --state-dir data/portable-demo-state
```

Use the public default local demo passphrase displayed at
`http://127.0.0.1:8861/#workbench`. The service must use that default gate;
customized gates fail closed. Select **Household app** from the same signed-in
preview to inspect the demo household. Registering an independent account creates
its own household and does not copy these records.

## What to demonstrate

| Page | Saved examples |
| --- | --- |
| Today | Mochi and Miso profiles; pet selector; pending, claimed, overdue and completed care |
| Care | 13 plans, five manual demo completions, recurring water/walk/brush examples |
| Growth | Seven weight samples and three distinct diet facts per pet; six diaries and four observations |
| Twin | Three confirmed database preferences and one candidate per pet; ask about saved records and review cited sources |
| Reports | Eight current daily/weekly reports, computed from the actual stored sample records |
| Workbench history | Six runs: approved meal, recent-feeding block, missing feeding time, owner decline, simulated feeder failure and approved play |
| Workbench settings | Three owner feedback notes; saved local text is not extracted cloud memory |

All new authored sample content is English and explicitly fictional. The
measurements use `demo_sample`; clinical visit cards exclude them unless you
choose to include demonstration samples. Meal amounts are display examples,
not feeding recommendations. Actual intake, food offered, remaining food and
simulated dispensing retain their separate meanings.

Manual completion timestamps are the real server times of the demonstration.
Historical measurement times and diary event dates are fictional. Previous-day
reports therefore do not invent historical completed care. The background worker
retains superseded versions; the report screen shows current versions.

App and Alexa-style chat responses are not saved conversation transcripts.
Preferences, measurements, tasks and reports persist in SQLite. You can confirm a
candidate, complete a due task or ask a new question through the ordinary flows.
Workbench sensors and devices are software simulations; the play receipt does
not create a household manual-care task.

## Safe replay

The importer accepts an explicit HTTP loopback URL, verifies the local SQLite /
local-rules / simulated-device configuration and the exact demo administrator,
and requires the untouched starter household and workbench. It does not clear or
replace records in an existing account. Run it before adding your own demo edits.

The journal is written below the ignored `data/` directory and binds to its
original instance and household day. Keep it to resume an interrupted import or
replay a completed one. Completed replay performs no business writes. Externally
changed records, facts, runs, another instance's journal or an expired proposal
cause refusal for manual review. Source-controlled dated evidence is never used
as the new instance's journal.

For another fresh demonstration, choose another unused port, database filename
and empty state directory. The tool does not start, stop or delete services or
databases. Preserve any existing demo you want to keep.

The [20 October snapshot](evidence/demo-usage-2026-10-20.md) records an earlier
local installation. Its fixed date, run IDs and external backup paths are
historical evidence; use the portable command above for a new installation.
