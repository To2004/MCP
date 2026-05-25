# Atomic-Op Taxonomy — Changes Log

This file tracks any modifications to `atomic_operations.csv` and the
decisions made by the classifier during heatmap generation. The csv has a
hard rule: do not edit existing rows. Only append new ops with rank >= 14.

## Entries

- 2026-05-24 — Backup created at `atomic_operations_backup.csv` before any
  classifier work begins. No taxonomy rows modified.

- 2026-05-24 — Decision: did NOT add a new `COMPUTE` atomic op for pure-function
  tools (e.g., `everything.echo`, `everything.add`, `time.convert_time`,
  `everything.getTinyImage`). Reason: in our threat model (MCP server =
  protected asset, agents = threat), a tool that returns a computed value
  without side effects carries zero risk to the server. Leaving these rows
  blank in the heatmap correctly reflects "no atomic op applies → no risk to
  classify". They show up in `Coverage.toollist_unclassified` for
  transparency.

- 2026-05-24 — Decision: `everything.sampleLLM` and `everything.printEnv` left
  to default rule outcomes. `printEnv` is now READ via the "prints" desc rule
  (matches `prints` in description). `sampleLLM` has external token-cost
  side effects but does not damage server state — left unclassified.

- 2026-05-24 — Decision: puppeteer DOM-interaction tools (`click`, `fill`,
  `select`, `hover`) tagged as MODIFY at medium confidence. Rationale: these
  modify the state of a remote page the agent is automating. The MCP server
  here is the puppeteer process; an agent driving it can take user-visible
  actions on third-party sites. MODIFY captures the integrity violation.

- 2026-05-24 — Decision: `actions_run_trigger` (and any `_trigger` suffix /
  "triggers a workflow" desc) tagged as EXECUTE. Rationale: triggers a CI
  workflow that runs with the repository's secrets — effectively arbitrary
  code execution under the agent's control. Severity 5 is appropriate.

- 2026-05-24 — Decision: `write_query` (and any freeform-SQL tool whose
  schema accepts a single `query` string) tagged with the worst-case op set
  EXECUTE+DELETE+OVERWRITE+SCHEMA_MODIFY+WRITE. Rationale: the input is
  arbitrary SQL with no parameterization; the agent can pass DROP TABLE,
  DELETE FROM, CREATE TABLE, INSERT, or `;` to chain statements.
