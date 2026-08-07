# Static-scoring prompts — experiment `five_level_v2_na` (with org description)

Every prompt this experiment's scan sent to the local LLM, verbatim from `src/mcp_security/static_scoring/prompts.py`. Generated -- do not hand-edit; edit the templates and re-run `scripts/dump_scoring_prompts.py`.

Risk formula: `score = asset_sensitivity × blast_radius × likelihood(1.0) × tool_impact`, score_max = 125. The **tool-impact** and **blast** stages vary by experiment; asset sensitivity is shared.

This run carries an **organizational description** (a profile or a policy) in the registry, so the domain-inference user message and the shared proposer preamble below are their `_DESC` variants: the org's text is placed in front of EVERY stage, including asset sensitivity. `{org_description}` is where that document's section for the scanned server is substituted verbatim.


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

Carries the org's description, the tool registry and a sample of asset classes into the stage above.

```text
ORGANIZATION'S OWN DESCRIPTION of this MCP server
-- who deploys it, what agents are supposed to use it for, which assets it holds
and how severe each one is, and which of confidentiality / integrity / availability
carries the loss:
{org_description}

Tool registry (all tools):
{tools_json}

Sample asset classes:
{assets_json}

Ground mcp_kind, dangerous_classes and dependency_hubs in the description above
where it speaks to them; ground irreversible_actions in the TOOL REGISTRY only --
the description does not license an action no tool here can perform.

Return JSON:
{{"mcp_kind": str, "asset_meaning": str, "blast_radius_meaning": str,
  "content_unit": str, "contents_definition": str, "dependency_hubs": [str],
  "dangerous_classes": [str], "irreversible_actions": [str],
  "worked_example": str, "confidence": 0.0-1.0, "needs_human_review": bool}}
```

## Shared proposer preamble

Prepended to every primitive stage — impact, SENSITIVITY, blast, baselines. Injects the org's description (authoritative for IMPORTANCE) alongside the inferred domain profile (authoritative for CAPABILITY).

```text
You are a security classifier for an MCP gateway. Two
descriptions of this server are given below. The ORGANIZATION'S DESCRIPTION is
written by the people who deploy it and is authoritative for CONTEXT: who runs the
server, what agents are supposed to do with it, how severe each asset is, and which
of confidentiality / integrity / availability carries the loss. The INFERRED DOMAIN
PROFILE is derived from the tool registry and is authoritative for MECHANICS: what
the tools can actually do. Use both. Where they disagree about CAPABILITY trust the
inferred profile; where they disagree about IMPORTANCE trust the organization.

ORGANIZATION'S DESCRIPTION OF THIS MCP SERVER:
{org_description}

INFERRED DOMAIN PROFILE:
{domain_profile}

Output ONLY valid JSON, no prose, no fences.
```

## 1 · Tool impact — task

EXPERIMENT A2+N/A: generalized 5-level action ladder (1 liveness/ping · 2 metadata · 3 read/observe · 4 write/modify incl. move · 5 delete/destroy). The blast stage also marks pairs the tool does not affect as N/A. score_max = 125.

```text
TASK: Assign TOOL IMPACT (1-5) -- the KIND of action one call performs,
independent of the asset's sensitivity and of HOW MUCH it touches (reach is priced
by blast; never raise impact because a call touches more items). Each tier is a
CLASS OF ACTION -- what the caller gains, what changes, and whether the system can
undo it. Operations in parentheses are examples, not the definition: place a tool
by which description fits, grounded in the inferred mcp_kind and
irreversible_actions.
FIRST read the tool's full DESCRIPTION -- capabilities, side effects, warnings --
and score what it CAN do, not what its NAME suggests. Names understate: when the
description names a stronger capability than the verb implies, score the stronger.
  1 = LIVENESS -- the system only says "I am here". Nothing about the data is
      touched or revealed; the caller learns only that the service is reachable or
      facts about its own session (ping, health, echo, time/version, whoami/auth).
      Misused, it yields nothing that being connected did not already give.
  2 = METADATA -- the shape of the data, never its substance. The caller learns
      what exists and how it is organized (names, ids, counts, sizes, types,
      timestamps, permissions, schema, a listing) OR changes only such about-ness:
      consumption-state and labels (mark read/unread, star, pin, mute, a PURE
      in-place rename). Content is neither exposed nor altered; the worst misuse is
      reconnaissance or mislabeling, both correctable.
  3 = READ CONTENT -- the substance is disclosed, nothing changes. The caller SEES
      actual bodies and values (read, get, fetch, export, search returning
      contents) and cannot alter them. What was seen cannot be unseen, but the data
      keeps its integrity and availability -- the system is afterwards exactly as
      before.
  4 = RECOVERABLE WRITE -- state changes, and the system itself can undo it.
      Something new comes into existence (item, container, empty record), an
      existing item takes a SCOPED change leaving most content intact (append,
      partial/line edit, update), data is RELOCATED (a MOVE leaves its source
      container -- more than a relabel), or a message is posted INSIDE the system
      where it can still be edited or deleted. CONTROL-PLANE writes live here:
      grant OR revoke a permission, change membership, role, account, config --
      GRANT and REVOKE both 4 unless irreversible (then 5). The prior state stays
      reconstructable from within the system.
  5 = IRREVERSIBLE / BOUNDARY-CROSSING -- no path back from inside the system, per
      irreversible_actions. Existing content is DESTROYED wholesale
      (delete/wipe/drop/purge, or a COMPLETE overwrite replacing ALL of an item's
      content -- the name survives, the data does not); CODE or a caller-supplied
      EXPRESSION is EXECUTED / EVALUATED (arbitrary python/numpy/shell/query/
      template -- an evaluator is code execution even if the tool is named
      "calculate" or "eval"); MONEY
      moves; a message is SENT BEYOND THE BOUNDARY (email, SMS, webhook, public
      post, external invite -- unrecallable once sent); or STANDING external access
      is granted irreversibly. Afterwards the system's own controls cannot restore
      the prior world.
BORDERLINE ACTIONS -- decide the SAME way every time, from the DESCRIPTION:
  - SCOPED EDIT vs FULL OVERWRITE: an edit that changes SPECIFIC parts and leaves
    the rest intact -- line-based edits, field updates, appends, anything that
    returns a diff or is otherwise reconstructable -- is 4, even on a whole or
    sensitive file, because the prior state survives in the diff/backup. Only a
    COMPLETE overwrite that replaces an item's ENTIRE content in one shot, with
    nothing to reconstruct from, is 5. A tool that can create-new OR fully-overwrite
    takes 5; a tool that only makes scoped edits is 4.
  - MOVE vs RENAME: relocation between locations/scopes is a structural write -> 4
    (moving a container relocates all under it); a PURE in-place relabel is 2. A
    tool that can both move AND rename scores 4.
  - CREATE vs no-op: making a new item or container, even empty, is 4; a call that
    only checks or reports is 1-2.
  - CODE / EXPRESSION EVALUATION: a tool that EVALUATES or INTERPRETS caller-
    supplied input -- an arbitrary math / python / numpy expression, formula,
    template, query language, or shell/script -- IS code execution -> 5, even when
    framed as "just a calculator", "just math", or "just a query". The evaluator is
    the capability; a mild name ("calculate", "eval", "run") does NOT lower it. Only
    a FIXED, non-programmable computation over declared numeric parameters (no
    free-form expression string) stays at its data tier.
  - JOIN / LEAVE / GRANT / REVOKE own access: joining, leaving, granting, or
    revoking a membership, role, or channel is a recoverable control-plane write ->
    4 -- access can normally be re-granted or rejoined. It is 5 only when the change
    is IRREVERSIBLE: it destroys access with no re-grant path, or grants STANDING
    external access that cannot be pulled back.
WORKED EXAMPLES from an UNRELATED domain (a print-server MCP) -- learn the SHAPE,
not the nouns:
  - printer_status ("is the printer online") -> 1: reveals nothing about a document.
  - list_print_queue ("queued jobs with owner and page count") -> 2: attributes,
    not document contents.
  - download_job_document ("returns the document behind a job") -> 3: substance
    disclosed, queue unchanged.
  - submit_print_job ("adds a document to the queue") -> 4: new state, undone by
    cancelling the job.
  - purge_queue ("permanently deletes all jobs") -> 5: unrecoverable from within.
  - update_firmware ("uploads and runs a firmware image") -> 5: executes code --
    the mild verb "update" understates it; the DESCRIPTION sets the tier.
A tool spanning tiers takes the HIGHEST it reaches. In your reasoning, name the
single capability that sets the tier, then score. Reason first.
```

## 1 · Tool impact — return schema

```text
Tool registry entry:
{tool_json}

Return JSON (reason BEFORE you score):
{{"tool_name": str, "reasoning": str, "tool_impact": 1-5, "confidence": 0.0-1.0}}
```

## 2 · Asset sensitivity (1-5) — task

CLASSIFY the asset against the org policy (register → recognition rules → default class), then MAP that class's adverse-impact definition onto the absolute 1-5 scale.

```text
TASK: Assign ASSET SENSITIVITY (1-5) -- how bad an incident is if THIS asset is
exposed, corrupted or destroyed. Judge what it CHARACTERISTICALLY holds, not the
worst thing it could conceivably hold.

The ORGANIZATION'S POLICY above is authoritative. Work in two steps:
  1 CLASSIFY. Find this asset in the policy's asset register -- its Description
    states what it holds. No row? Apply the policy's recognition rules. Still
    undecided? Use the policy's stated default class.
  2 MAP that class's adverse-impact definition onto the tiers below (severe /
    serious / limited adverse effect).

  5 CROWN JEWEL  exposure alone is an emergency -- exploitable or legally
                 reportable the moment it leaks (live credentials, PHI, card data,
                 privileged or money-moving records); OR a control plane: losing it
                 rewires what every other tool can reach (auth/scope configuration,
                 access-control state), so the damage is not one asset but all of
                 them.
  4 RESTRICTED   serious lasting harm one step removed: damages customers, staff or
                 the company's position, but is not instantly weaponizable.
  3 INTERNAL     disruptive and embarrassing but recoverable; meant to stay in-org.
  2 ROUTINE      low-value internal material; exposure is a shrug.
  1 PUBLIC       already published or disposable -- no confidentiality left to lose.

RULES
- ABSOLUTE scale, never relative to the other assets here. A whole server sitting
  at one tier is expected and correct; do NOT spread scores to manufacture contrast.
- CONTAINER: takes the tier of the most sensitive thing it CHARACTERISTICALLY
  holds -- its typical payload, not a conceivable one.
- METADATA-ONLY: an asset holding only about-ness -- names, ids, counts, listings,
  schema, read/RSVP state, with no bodies -- is reconnaissance, not disclosure:
  cap it at 2. Exception: the policy says those names themselves identify people,
  deals or candidates.
- AGGREGATION: if one asset holds the WHOLE population of a class, or the policy
  names a combination that reveals more than its parts, raise one tier.
- PUBLIC OVERRIDE: already-public data is 1 whatever its topic. "Financial" is not
  "confidential".
- Torn between two adjacent tiers on NON-public secrets, PII, money-moving or
  regulated records: take the HIGHER. Never for public data.
```

## 2 · Asset sensitivity — return schema

```text
Asset class entry:
{asset_json}

Return JSON (classify BEFORE you score -- emit these keys in this exact order):
{{"asset_id": str, "policy_class": str, "reasoning": str,
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

RELEVANCE (answer this FIRST): does this tool ACT ON this asset class AT ALL? A
tool that operates only on a DIFFERENT class -- a mail-sender against a DNS-zone
asset, an image resizer against an audio store, a writer for shard A against shard
B -- does NOT affect this asset: set affects_asset=false, blast_radius to null (do
NOT invent a number), escape to "none", and the cell is N/A (not scored, it renders
as "na" in the table). ONLY when affects_asset=true do you give a blast_radius of
1-5. Relevance is decided ONCE here -- never also fold "doesn't touch" into a
blast_radius=1; a non-touching pair is N/A, not a low score.
```

## 3 · Blast radius — return schema

```text
Tool:
{tool_json}

Asset class:
{asset_json}

Return JSON (relevance FIRST, then reasoning, then escape route, score LAST). Emit
blast_radius as null when affects_asset is false, else an integer 1-5; escape is
"a", "b", or "c" when a tier-5 route fired, else "none":
{{"tool_name": str, "asset_id": str, "affects_asset": bool,
  "coverage_reasoning": str, "escape": "a|b|c|none",
  "blast_radius": "1-5 or null", "confidence": 0.0-1.0}}
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
