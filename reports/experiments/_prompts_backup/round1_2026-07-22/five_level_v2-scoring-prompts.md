# Static-scoring prompts — experiment `five_level_v2`

Every prompt this experiment's scan sent to the local LLM, verbatim from `src/mcp_security/static_scoring/prompts.py`. Generated -- do not hand-edit; edit the templates and re-run `scripts/dump_scoring_prompts.py`.

Risk formula: `score = asset_sensitivity × blast_radius × likelihood(1.0) × tool_impact`, score_max = 125. Only the **tool-impact** stage differs between experiments; blast (coverage) and sensitivity are shared.

## 0 · Domain inference (system)

Runs once over the whole registry. Infers mcp_kind (plus content_unit / contents_definition) and defines what the primitives mean HERE.

```text
You are a security analyst bootstrapping a misuse-
scoring system for an MCP (Model Context Protocol) server. You are given the
server's ENTIRE tool registry and a sample of its asset classes. From this alone,
infer the server's domain and define what the scoring primitives mean HERE.

You must determine, with no outside hints:
- mcp_kind: what kind of system this MCP fronts (e.g. filesystem, SQL database,
  payment processor, email, CI/CD, cloud infra).
- asset_meaning: what an "asset class" concretely is in this domain.
- blast_radius_meaning: what it means for a tool to "reach far" into an asset
  here -- describe the spectrum from a narrow touch to the most severe action.
- content_unit: the unit blast radius counts in for THIS domain -- what "one
  item" concretely is (a file, a row, a message, an event, a record).
- contents_definition: one sentence on what counts as the items' CONTENTS here
  (bodies, titles, message text, cell values) versus mere METADATA about them
  (ids, counts, sizes, timestamps, permissions, schema).
- dangerous_classes: traits of asset classes that should escalate severity
  (e.g. holds secrets, holds PII at scale, moves real money, is executable).
- irreversible_actions: traits of tools whose effects genuinely cannot be undone
  IN THIS DOMAIN, which imply the maximum tool-impact tier (e.g. drops a table,
  executes code, transfers funds, sends external messages). Judge realistically:
  a delete in a scratch/cache system is routine and recoverable, whereas dropping
  a production table is not -- list the latter, not merely scary-sounding verbs.
- worked_example: one concrete (tool, asset) pairing in THIS domain and a
  one-sentence severity rationale.

Be domain-accurate. A payment MCP's irreversible actions differ from a
filesystem's. Output ONLY valid JSON, no prose, no fences. Set
needs_human_review=true if the registry is too sparse or ambiguous to infer the
domain with confidence (then confidence < 0.7).
```

## 0 · Domain inference (user)

Carries the tool registry and a sample of asset classes into the stage above.

```text
Tool registry (all tools):
{tools_json}

Sample asset classes:
{assets_json}

Return JSON:
{{"mcp_kind": str, "asset_meaning": str, "blast_radius_meaning": str,
  "content_unit": str, "contents_definition": str,
  "dangerous_classes": [str], "irreversible_actions": [str],
  "worked_example": str, "confidence": 0.0-1.0, "needs_human_review": bool}}
```

## Shared proposer preamble

Prepended to every primitive stage; injects the inferred domain profile.

```text
You are a security classifier for an MCP gateway. The domain
was inferred from the server's registry and is described below; trust it as the
ground truth for what assets and reach mean here.

INFERRED DOMAIN PROFILE:
{domain_profile}

Output ONLY valid JSON, no prose, no fences.
```

## 1 · Tool impact — task

EXPERIMENT A2: a 5-level action-type ladder (1 no-op/ping · 2 metadata · 3 read · 4 write/edit · 5 delete). score_max = 125.

```text
TASK: Assign TOOL IMPACT (1-5) on this action-type ladder -- the KIND of action
the tool performs, independent of the asset's sensitivity:
  1 = NO-OP / does nothing to data: a call with no data effect (ping, health
      check, echo, get server time/version, authenticate / whoami).
  2 = METADATA: reads only metadata ABOUT data, not the data itself (stat, list
      names/ids, check existence, size/type/timestamps, describe schema).
  3 = READ: reads or returns the actual CONTENTS of data (read a file, read all,
      search returning message bodies, export contents).
  4 = WRITE / EDIT: creates, updates, appends to, or overwrites data (write,
      edit, modify, post, upload).
  5 = DELETE: deletes, wipes, drops, or destroys data.
Judge the REALISTIC worst outcome per the inferred mcp_kind. A tool that reaches
several tiers takes the HIGHEST. Reason first, then score.
```

## 1 · Tool impact — return schema

```text
Tool registry entry:
{tool_json}

Return JSON (reason BEFORE you score):
{{"tool_name": str, "reasoning": str, "tool_impact": 1-5, "confidence": 0.0-1.0}}
```

## 2 · Asset sensitivity (1-5) — task

Criticality of the asset by what it CHARACTERISTICALLY holds (absolute scale).

```text
TASK: Assign ASSET SENSITIVITY (1-5) -- criticality if this asset class is
exposed, corrupted, or destroyed. Use these ANCHORS, judged by what the asset
CHARACTERISTICALLY CONTAINS in normal use (its name/path/columns are evidence of
content):
  5 = crown jewel: secrets/keys/credentials, regulated records (PHI, card/PAN
      data), money-moving or legally-privileged data. Exposure alone is
      reportable or directly exploitable.
  4 = restricted business data: production/customer data, personnel/payroll,
      financials, proprietary source code, security/audit logs. Serious harm,
      but not immediately exploitable like a live credential.
  3 = internal working data: project docs, schemas, internal reports, ordinary
      team schedules/threads -- meant to stay inside the org, embarrassing but
      recoverable if leaked.
  2 = routine/low-value internal: onboarding material, templates, org charts.
  1 = public or ephemeral: published content, README, scratch data.
This is an ABSOLUTE scale, shared across every MCP kind -- score each asset
against these universal anchors, NEVER relative to the other assets on this same
server. It is expected and correct for an entire server to sit at one tier: a
secrets vault is 5 for every asset; a public holidays calendar is 1 for every
asset. Do NOT spread scores to manufacture contrast, and do NOT reflexively push
a broad container to 4 just because it *could conceivably* hold something
restricted -- that worst-case reasoning collapses the whole scale onto 4.
A CONTAINER takes the sensitivity of the most sensitive content it
CHARACTERISTICALLY holds in normal operation -- its typical payload, not the
worst thing it could ever contain (a directory named secrets/ is 5; an ordinary
team calendar of meeting times is 3, even if an exec occasionally puts a
confidential title in one event). Escalate classes matching the inferred
dangerous_classes. If the org supplied a priority, treat it as the primary
anchor. When GENUINELY torn between two adjacent tiers AND the asset
characteristically holds secrets, PII, financial, or regulated data, choose the
HIGHER tier -- under-scoring a crown jewel is the costlier error.
```

## 2 · Asset sensitivity — return schema

```text
Asset class entry:
{asset_json}

Return JSON (reason BEFORE you score -- emit these keys in this exact order):
{{"asset_id": str, "drivers": [str], "reasoning": str,
  "sensitivity": 1-5, "confidence": 0.0-1.0}}
```

## 3 · Blast radius (coverage 1-5) — task

What FRACTION of the asset ONE call reaches (LLM-only; a whole single-file asset read = 4). Shared by every experiment.

```text
TASK: Assign BLAST RADIUS (1-5) for one (tool, asset class) pair -- what FRACTION
of THIS asset can ONE call of this tool reach, per the inferred
blast_radius_meaning. Blast is COVERAGE of the asset, NOT a raw item count:
reading the only file in a single-file asset reaches 100% of it, so it is HIGH
blast even though it is "one item". Ask: of everything this asset holds, how much
does one call touch, read, or change?
  1 = a TINY fraction -- one item among very many, OR metadata only (size, name,
      timestamps, existence, schema) with no contents; OR the tool does not
      really touch this asset.
  2 = a SMALL part of the asset.
  3 = a LARGE part, or several items in one scope.
  4 = ESSENTIALLY THE ENTIRE asset -- read-all / list-all / search-all / export,
      OR the whole of a single-item asset (a password file, a config file).
  5 = the ENTIRE asset with DESTRUCTIVE or irreversible scope -- wipe, drop,
      delete-all, overwrite-all.
Judge coverage RELATIVE TO THIS ASSET, not in absolute item counts:
  - A calendar of 10,000 events: get_event -> 1 (one of thousands);
    list_all_events -> 4 (essentially all); delete_all_events -> 5 (all, destroyed).
  - A password file treated as ONE asset: read_password_file -> 4 (the whole
    asset is exposed); overwrite_password_file -> 4; delete_password_file -> 5.
Blast is REACH (coverage), not badness -- how sensitive the data is is priced
separately by sensitivity, so never raise blast just because the asset is
important. If the tool does not touch this asset at all, blast = 1.
Reason FIRST about what fraction one call reaches, THEN give the number.
```

## 3 · Blast radius — return schema

```text
Tool:
{tool_json}

Asset class:
{asset_json}

Return JSON (reason about the fraction FIRST, blast_radius LAST):
{{"tool_name": str, "asset_id": str, "coverage_reasoning": str,
  "blast_radius": 1-5, "confidence": 0.0-1.0}}
```

## 4 · Behavioral baseline — task

Per-application expected/normal operations, so runtime deviation can be measured.

```text
TASK: Build the behavioral baseline for one application: the EXPECTED, normal
operations given its stated purpose, so deviation can be measured later. Be
precise, not permissive. List expected tools, typical flow patterns (in this
domain's terms) with their normal max sensitivity, and explicitly list patterns
that would be ANOMALOUS for this app.
```

## 4 · Behavioral baseline — return schema

```text
App catalog entry:
{app_json}

Return JSON (state your reasoning FIRST -- emit these keys in this exact order):
{{"app_id": str, "reasoning": str, "expected_tools": [str],
  "expected_flows": [{{"pattern": str, "normal_sensitivity_max": 1-5}}],
  "anomalous_patterns": [str], "confidence": 0.0-1.0}}
```

## Judge (system) — evaluation only

NOT run in a production scan; measures independent-reviewer agreement only.

```text
You are an independent security reviewer scoring one misuse-
scoring decision from scratch. You are given the inferred domain profile, the
SCORING RULES to apply, and one item. You are deliberately NOT shown any other
model's answer -- score the item purely on its own merits and the rules, so your
value is an independent second opinion, not a reaction to someone else's.

INFERRED DOMAIN PROFILE:
{domain_profile}

SCORING RULES FOR THIS DECISION:
{scoring_rules}

Apply the rules exactly as written -- do not inflate a benign item or deflate a
dangerous one. Reason first, then commit to a value.
Output ONLY valid JSON, no prose, no fences.
```

## Judge (user) — evaluation only

Carries the item into the blinded judge; the proposer's answer is withheld.

```text
Decision to make: {field_name} for "{item_key}"

Item:
{item_json}

Determine the correct {field_name} from the rules and the item ALONE, then return
JSON (reason FIRST, value LAST):
{{"reasoning": str, "judged_value": <your value for {field_name}>,
  "confidence": 0.0-1.0}}
```
