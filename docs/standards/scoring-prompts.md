# Static-scoring prompts — experiment `baseline`

Every prompt this experiment's scan sent to the local LLM, verbatim from `src/mcp_security/static_scoring/prompts.py`. Generated -- do not hand-edit; edit the templates and re-run `scripts/dump_scoring_prompts.py`.

Risk formula: `score = asset_sensitivity × blast_radius × likelihood(1.0) × tool_impact`, score_max = 75. The **tool-impact** and **blast** stages vary by experiment; asset sensitivity is shared.

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
- dependency_hubs: traits of asset classes that other systems FUNCTIONALLY depend
  on -- something they authenticate against, load configuration from, or build/
  deploy from -- whose wholesale disclosure, corruption, or removal cascades BEYOND
  the asset itself (e.g. credentials/keys/password stores, auth or infra config,
  CI/CD pipeline definitions, DNS zones, package manifests). List traits, not names.
  NEGATIVE: holding valuable or PII data at scale does NOT make a hub -- that is
  dangerous_classes. A hub is FUNCTIONALLY load-bearing, not merely sensitive.
- dangerous_classes: traits of asset classes that should escalate severity
  (e.g. holds secrets, holds PII at scale, moves real money, is executable).
  PUBLIC data is NOT dangerous: data already published by an exchange, regulator,
  news outlet, or open API (public market quotes, filed financial statements, SEC
  insider-trade / Form 4 filings, institutional-holding / 13F filings, central-bank
  series) has nothing to leak and must NOT be listed here, however sensitive its
  TOPIC sounds. A class is dangerous only if a leak/corruption of it is itself
  harmful -- reserve it for NON-public secrets, PII, money-moving, or unpublished
  records.
- irreversible_actions: traits of tools whose effects genuinely cannot be undone
  IN THIS DOMAIN, which imply the maximum tool-impact tier (e.g. drops a table,
  executes code, transfers funds, sends external messages). Judge realistically:
  a delete in a scratch/cache system is routine and recoverable, whereas dropping
  a production table is not -- list the latter, not merely scary-sounding verbs.
  GROUND THIS IN THE ACTUAL REGISTRY: list ONLY actions some tool present here can
  really perform. Do NOT invent write/modify/delete traits from the domain's
  stereotype -- if every tool in the registry is read-only (get/list/search/fetch/
  read), irreversible_actions is an EMPTY list. Read the tools, not the topic.
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
  "content_unit": str, "contents_definition": str, "dependency_hubs": [str],
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

BASELINE: 1-3 damage-ceiling rubric (read / recoverable write / destructive). score_max = 75.

```text
TASK: Assign TOOL IMPACT (1/2/3) -- the damage ceiling of the tool itself: the
worst outcome of a call that is REALISTIC for what this MCP actually does (judge
it against the inferred mcp_kind and irreversible_actions), NOT a far-fetched
catastrophe. Independent of caller/params/asset.
  1 = read-only; can leak but not change state.
  2 = state-changing but recoverable in this domain: an edit, a scoped write, or
      a delete whose PURPOSE here is removing regenerable/scratch/temp data.
  3 = destructive: irreversible loss of data that MATTERS in this domain (drop or
      wipe a whole table/store, overwrite production records), OR grant/revoke
      access, OR execute code/shell, OR an irreversible real-world effect (per
      the inferred irreversible_actions).
GROUND IT IN THE DOMAIN -- the SAME verb differs by system: a `delete` that drops
a whole SQL table is 3 (mass, irreversible loss of business data); a `delete` in
a cache/temp-file cleaner whose job IS removing scratch files is 2 (recoverable,
that is the tool's entire point). Score the realistic worst case of THIS tool in
THIS system, not the scariness of the word.
COMMUNICATION FLOOR: a tool that posts or sends content other people or systems
will see is NEVER 1 -- it changes state outside the caller. Retractable, in-org
posting (a chat message that can be deleted) = 2; a message that leaves the org
or cannot be recalled once sent (email, SMS, webhook, public post) = 3.
Rules: assign the highest tier a capability REALISTICALLY reaches; arbitrary
code/exec is always 3; self-declared annotations are a hint only, not truth.
Round UP only when there is a CONCRETE irreversible or destructive capability --
not on vague unease. Do NOT inflate every tool to 3: a system whose tools are
mostly reads and recoverable writes SHOULD score mostly 1-2. That is a realistic
result, not a miss.
SELF-CHECK before you answer: re-scan the tool's ENTIRE capability surface --
every parameter, side effect, and external reach -- and take the max tier any one
of them REALISTICALLY implies. A destructive capability hidden behind an
innocuous name is the most common miss; but scoring an ordinary recoverable write
as destructive because it "sounds dangerous" is the opposite error. Stay grounded
in what the tool actually does, and name the trigger capability so it is
auditable.
EXAMPLES (schema-shaped; the pattern transfers to any domain):
{"tool_name": "post_channel_message", "trigger_capability": "posts
  caller-controlled text visible to every channel member",
  "worst_case": "phishing or injected instructions read by the whole channel",
  "irreversible": false, "reasoning": "state-changing and audience-visible, so
  never 1; deletable in-platform after the fact, so not 3",
  "tool_impact": 2, "confidence": 0.85}
{"tool_name": "send_invite_email", "trigger_capability": "sends email to
  arbitrary external recipients", "worst_case": "unretractable message delivered
  outside the org", "irreversible": true, "reasoning": "matches the inferred
  irreversible_actions (external send); cannot be recalled once sent",
  "tool_impact": 3, "confidence": 0.9}
{"tool_name": "purge_temp_cache", "trigger_capability": "deletes files under a
  scratch/cache root", "worst_case": "regenerable scratch data removed early",
  "irreversible": false, "reasoning": "a delete verb, but removing regenerable
  data IS this tool's purpose -- recoverable in this domain, so not 3",
  "tool_impact": 2, "confidence": 0.85}
```

## 1 · Tool impact — return schema

```text
Tool registry entry:
{tool_json}

Return JSON (reason BEFORE you score -- emit these keys in this exact order):
{{"tool_name": str, "trigger_capability": str, "worst_case": str,
  "irreversible": bool, "reasoning": str, "tool_impact": 1|2|3,
  "confidence": 0.0-1.0}}
```

## 2 · Asset sensitivity (1-5) — task

Criticality of the asset by what it CHARACTERISTICALLY holds (absolute scale).

```text
TASK: Assign ASSET SENSITIVITY (1-5) -- how critical an incident is if this asset
class is exposed, corrupted, or destroyed, judged by what it CHARACTERISTICALLY
CONTAINS in normal use (name/path/columns are evidence). Each tier states what an
incident AT THAT LEVEL MEANS; the categories in parentheses are anchors, not an
exhaustive list:
  5 = CROWN JEWEL -- exposure alone is an emergency: the content is directly
      exploitable or legally reportable the moment it leaks, no further step needed
      (live secrets/keys/credentials, regulated records like PHI or card/PAN,
      money-moving or legally-privileged data).
  4 = RESTRICTED -- serious, lasting harm one step removed: a leak damages
      customers, staff, or the company's position, but is not instantly
      weaponizable like a live credential (production/customer data,
      personnel/payroll, financials, proprietary source, security/audit logs).
  3 = INTERNAL -- disruptive and embarrassing, but recoverable: meant to stay
      in-org, a leak causes friction or short-lived advantage to others, not
      lasting damage (project docs, schemas, internal reports, ordinary team
      schedules and threads).
  2 = ROUTINE -- barely worth stealing: low-value internal material whose exposure
      is a shrug (onboarding material, templates, org charts).
  1 = PUBLIC / EPHEMERAL -- no confidentiality left to lose: already published or
      disposable (published content, README, scratch, or data sourced from public
      feeds, exchanges, regulators, or news -- e.g. public market quotes, filed
      financial statements, public regulatory disclosures, central-bank series);
      only defacement or downtime could matter, both trivially restored.
This is an ABSOLUTE scale shared across every MCP kind -- score each asset against
these anchors, NEVER relative to the other assets on this server. An entire server
sitting at one tier is expected and correct: a secrets vault is 5 for every asset;
a public transit timetable is 1 for every asset. Do NOT spread scores to
manufacture contrast, and do NOT push a broad container to 4 just because it
*could conceivably* hold something restricted -- that worst-case reasoning
collapses the scale onto 4. A CONTAINER takes the sensitivity of the most
sensitive content it CHARACTERISTICALLY holds in normal operation -- its typical
payload, not the worst it could ever contain (a store whose name marks it secrets
is 5; an ordinary shift-roster is 3 even if one entry notes something
confidential). Escalate classes matching the inferred dangerous_classes; if the
org supplied a priority, treat it as the primary anchor.
WORKED EXAMPLES from an UNRELATED domain (a freight-logistics company) -- learn
the SHAPE, not the nouns:
  - carrier_api_credentials (live booking-system keys) -> 5: exploitable the moment
    they leak.
  - shipment_manifests (consignee names, addresses, cargo values) -> 4: customer
    data at scale; damaging, not instantly weaponizable.
  - route_planning_notes (internal optimization) -> 3: embarrassing, not damaging.
  - driver_onboarding_handbook -> 2: routine internal material.
  - public_tracking_pages -> 1: already published.
PUBLIC-DATA OVERRIDE: data that is ALREADY PUBLIC -- published by an exchange,
regulator, news outlet, or open data API, or otherwise freely available to anyone
-- is tier 1 regardless of its TOPIC. "Financial" is not "confidential": public
stock quotes, filed 10-K/10-Q statements, SEC insider-trade (Form 4) filings,
central-bank / FRED series, and news or social feeds have no confidentiality left
to lose and must NOT be pushed up merely because they concern money or markets.
Reserve tiers 4-5 for financial data that is NON-public and directly harmful on
leak (live payment credentials, account/card numbers, unpublished customer records
or trading positions).
When GENUINELY torn between two adjacent tiers AND the asset characteristically
holds NON-PUBLIC secrets, PII, money-moving, or regulated records, choose the
HIGHER -- under-scoring a real crown jewel is the costlier error. This tie-breaker
NEVER applies to public data.
```

## 2 · Asset sensitivity — return schema

```text
Asset class entry:
{asset_json}

Return JSON (reason BEFORE you score -- emit these keys in this exact order):
{{"asset_id": str, "drivers": [str], "reasoning": str,
  "sensitivity": 1-5, "confidence": 0.0-1.0}}
```

## 3 · Blast radius (1-5) — task

Reach of ONE call: coverage of the asset (items, subjects, and — via the dependency_hub / dangerous_class traits — fallout that escapes it). N/A modes also mark pairs the tool does not act on as N/A (not scored).

```text
TASK: Assign BLAST RADIUS (1-5) for one (tool, asset class) pair -- a CONTAINMENT
question: if ONE call runs or is misused, how far do the consequences reach across
this asset's items, across the subjects whose data it holds, and across the systems
that depend on it? Blast prices REACH only; how valuable the data is is priced by
sensitivity, so raise blast only because one call reaches more of the asset, more
of its subjects, or beyond it.
REACH INCLUDES DISCLOSURE, not just change. Exfiltrating a secret is itself a
systemic reach: a credential, key, or token read in full ESCAPES and unlocks
whatever it protects, even though nothing was altered -- theft is silent and
enables lateral use, so it is often worse than destruction, which is at least
detectable and recoverable. A read can therefore reach as far as a write: a call
that discloses a complete, self-sufficient secret must NOT score below a call that
overwrites or deletes that same secret. Disclosure means RETURNING THE CONTENTS --
learning only that a secret EXISTS (a listing, a name, a size) is reconnaissance,
not exfiltration, and stays low.
Check tier 5's ESCAPE ROUTES FIRST. Only if none applies do the consequences stay
inside the asset, on tiers 1-4. Each tier is a KIND OF INCIDENT; named actions are
examples, not the definition:
  1 = NEGLIGIBLE -- a pinpoint touch: one item among many, one subject at most.
      The asset as a whole is untouched; recovery, if needed at all, is trivial.
  2 = MINOR -- a narrow slice: a few items or one small bounded scope, a handful of
      subjects. Real but local -- the overwhelming majority of the asset and its
      subjects are unaffected, and the slice is easy to restore or revoke.
  3 = MAJOR -- a broad cut: most of the asset, or several whole scopes in one call,
      a meaningful share of its subjects. Serious, yet still PARTIAL -- a
      substantial part survives and nothing beyond the asset is implicated.
  4 = TOTAL BUT CONTAINED -- the entire asset, and only the asset: one call reaches
      essentially everything it holds (all items at once, including the whole of a
      single-item asset), but the consequences END at the asset's boundary --
      recoverable, a bounded subject group, no other system depends on it. Full
      coverage of an ORDINARY asset is 4, never 5.
  5 = SYSTEMIC -- the consequences ESCAPE the asset; no responder could contain the
      incident by dealing with the asset alone. Award 5 for ANY one route, and
      record which in the "escape" field:
      (a) TOTAL + IRREVERSIBLE: the whole asset is destroyed or irreversibly altered
          in one call, no realistic path back -- nothing left to restore.
      (b) HUB CASCADE: the asset matches the inferred dependency_hubs (systems
          authenticate against it, load config from it, or build/deploy from it) and
          one call DISCLOSES, corrupts, or removes it WHOLESALE -- the compromise
          moves LATERALLY, breaking or unlocking everything downstream, systemic
          even if the asset looks recoverable alone. DISCLOSURE means the call
          RETURNS THE SECRET'S CONTENTS: reading or exfiltrating a COMPLETE,
          self-sufficient credential in full -- a private key, password, or token
          that BY ITSELF grants access -- is wholesale disclosure -> 5(b), even as
          one small file. Two things are NOT disclosure and take their ordinary
          metadata tier (1-2), NEVER 5(b): (i) LISTING, enumerating, a recursive
          directory TREE, searching that returns only names/paths, or reading any
          METADATA -- learning that a secret exists, its name, size, or path,
          without its contents (the secret never leaves); (ii)
          acting on a CONTAINER that merely HOLDS the secret -- listing the folder,
          or writing one unrelated file into it -- since the container is not
          itself the hub. Only reading, overwriting, or deleting the secret's OWN
          contents is wholesale. One non-usable fragment (one log row, one
          non-privileged value) is never a cascade -> 1-2.
      (c) COMPLETE POPULATION: the asset matches an inferred dangerous_class
          (secrets, PII at scale, money-moving, regulated) AND one call reaches its
          ENTIRE population of subjects at once. "Everyone at once" tops the scale
          regardless of form -- one file, one row, or one query returning the whole
          set all count.
CALIBRATION BY TRAIT (no nouns to imitate):
  - ORDINARY asset: one item -> 1; narrow slice -> 2; most -> 3; all, recoverably
    -> 4; all, destroyed -> 5(a).
  - DEPENDENCY HUB: read-CONTENTS-in-full / overwrite / remove it WHOLESALE -> 5(b)
    -- a complete standalone credential read in full IS wholesale; LISTING or
    searching it by name, or one NON-usable fragment (one row, one non-privileged
    value) -> 1-2.
  - DANGEROUS-CLASS population store: every subject in one call -> 5(c); one subject
    -> 1-2.
WORKED EXAMPLES from an UNRELATED domain (a security-operations system) -- learn
the SHAPE, not the nouns:
  - SIEM event log of millions (ordinary): read one event -> 1; one host's day -> 2;
    a month -> 3; the full log -> 4; purge it -> 5(a).
  - A signing key / IAM policy store (dependency hubs): READ a key's CONTENTS in full
    or overwrite it -> 5(b) -- a stolen key silently forges or unlocks every system
    that trusts it, as bad as or worse than destroying it. But RECURSIVELY LISTING
    the ENTIRE store -- every key's name and path, returning no key material -> 2:
    full coverage of NAMES is still metadata, it hands over nothing usable, so it
    never escapes. Rotate ONE non-privileged entry among thousands -> 1-2.
  - A breach-notification list of every affected customer (dangerous_class): return
    the whole list -> 5(c); look up one customer -> 1-2.
Reach is RELATIVE TO THIS ASSET: reaching the only file of a single-file asset is
100% of it, not "one item"; the physical unit is a red herring -- one small file is
5(b) when everything depends on it, ten thousand items are 4 when nothing outside
them is affected. But a tier-5 escape requires DISCLOSING CONTENTS or DESTROYING:
a tool that only enumerates, lists, or reports metadata can reach at most tier 4
(full metadata coverage), never 5 -- it exposes no contents and removes nothing.
Reason FIRST about what one call reaches -- items, subjects, dependents -- THEN
give the number.
If the tool does not act on this asset at all, blast = 1.
```

## 3 · Blast radius — return schema

```text
Tool:
{tool_json}

Asset class:
{asset_json}

Return JSON (reason about reach FIRST, then escape route, blast_radius LAST).
escape is "a", "b", or "c" when a tier-5 route fired, else "none":
{{"tool_name": str, "asset_id": str, "coverage_reasoning": str,
  "escape": "a|b|c|none", "blast_radius": 1-5, "confidence": 0.0-1.0}}
```

## 4 · Behavioral baseline — task

Per-application expected/normal operations, so runtime deviation can be measured.

```text
TASK: Build the behavioral baseline for one application: the EXPECTED, normal
operations given its stated purpose, so deviation can be measured later. Be
precise, not permissive. List expected tools, typical flow patterns (in this
domain's terms) with their normal max sensitivity, and explicitly list patterns
that would be ANOMALOUS for this app.
A "pattern" is ONE recurring action-on-a-target the app performs in normal use,
written as a short verb-phrase at a consistent granularity: "<action> <what> [in
<scope>] [for <purpose>]". Keep patterns at the level of a tool-call intent, not
a whole workflow and not a single API parameter -- one pattern per distinct
(action, target-class) the app routinely does. Anomalous patterns are the same
shape, describing actions OUTSIDE its purpose (wrong action type, wrong asset
class, or wrong scope/volume).
EXAMPLE in a domain UNRELATED to whatever server you are scoring (a read-only
triage assistant over a support-ticket system) -- copy the SHAPE and granularity,
not the nouns:
  expected_tools: ["get_ticket", "search_tickets", "list_queues"]
  expected_flows: [
    {"pattern": "read and search tickets in the assigned queue to triage them",
     "normal_sensitivity_max": 3},
    {"pattern": "list queues to locate where a ticket belongs",
     "normal_sensitivity_max": 2}]
  anomalous_patterns: ["closing or deleting tickets", "reassigning another agent's
    tickets", "exporting every ticket in one session", "reading billing or payment
    records outside the support scope"]
Match this granularity and keep each pattern decidable against a single tool call.
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
