# Static-scoring prompts — experiment `five_level_v2_v5` (with org description)

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

## 1 · Tool impact — FALLBACK ONLY

EXPERIMENT V5: tool impact is the deterministic ladder (`static_impact.py`) FIRST. This prompt is sent only for a tool where the ladder abstains — no tier verb matched, so it would have had to use its default (static confidence < 0.5). Sent bare, exactly as in v4.

```text
You are classifying one MCP tool. Output ONLY valid JSON,
no prose, no fences.

TASK: Assign TOOL IMPACT (1-5) -- what ONE call DOES, judged from the tool's
description and parameters alone. Not how much it touches (that is scored
separately), not how valuable the target is.

The ladder follows the MCP annotation vocabulary (read-only / destructive /
open-world) and CVSS integrity-and-availability loss:
  1 NO EFFECT      the caller learns only that the service is reachable, or facts
                   about its own session (ping, health, version, whoami, clock).
  2 METADATA       read-only, and returns only about-ness: names, ids, counts,
                   sizes, timestamps, permissions, schema, a listing. OR changes
                   only about-ness: mark read, star, pin, mute, pure rename.
  3 CONTENT READ   read-only, and returns the substance itself (bodies, values,
                   file contents, message text, search results with content).
                   Nothing changes; what was seen cannot be unseen.
  4 REVERSIBLE WRITE  modifies state in a way the system itself can undo: create,
                   append, partial/field edit, move, membership or permission
                   change (grant AND revoke), a message posted where it can still
                   be edited or deleted.
  5 IRREVERSIBLE OR OPEN-WORLD  no path back from inside the system: delete, wipe,
                   drop, purge, or a COMPLETE overwrite that replaces an item's
                   entire content; executes code; moves money; OR crosses the
                   system boundary (email/SMS/webhook/public post/external invite),
                   which is unrecallable once sent.

RULES
- Score the DESCRIPTION and PARAMETERS, never the name. Annotation hints
  (readOnlyHint, destructiveHint, openWorldHint) are HINTS ONLY -- corroborating
  evidence, never overriding a description that says otherwise.
- A tool spanning tiers takes the HIGHEST it can reach.
- Scoped edit (leaves the rest intact, reconstructable) = 4. Full overwrite of an
  item's entire content = 5. A tool that can do either takes 5.
- A bulk/batch variant takes AT LEAST its singular twin's tier.
```

## 1 · Tool impact — return schema (fallback only)

```text
Tool:
{tool_json}

Return JSON (reason first): {{"tool_name": str, "reasoning": str,
"tool_impact": 1-5, "confidence": 0.0-1.0}}
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
TASK: Assign BLAST RADIUS (1-5) for ONE (tool, asset) pair --
HOW FAR the consequences of one call reach. This is the CVSS v4.0 question: does
the impact stay inside this asset (the "vulnerable system"), or does it reach
systems, identities and data beyond it (a "subsequent system")?

Sensitivity is scored separately from the organization's classification
policy and is ALREADY multiplied into the score. Do NOT price value here. Blast prices REACH ONLY.

  1 ONE ITEM      a single item among many; one subject. The asset as a whole is
                  untouched.
  2 NARROW SLICE  a few items or one small bounded scope; a handful of subjects.
                  The overwhelming majority of the asset is unaffected.
  3 BROAD CUT     most of the asset, or several whole scopes in one call --
                  serious but still PARTIAL; a substantial part survives.
  4 TOTAL, CONTAINED   essentially everything the asset holds (CVSS "total loss
                  ... all information within the Vulnerable System"), including
                  the whole of a single-item asset -- but the consequences STOP at
                  the asset's boundary. Full coverage of an ordinary asset is 4.
  5 ESCAPES       CVSS Subsequent System impact: the consequences do NOT stay
                  constrained to this asset. Award 5 only via a route the
                  ORGANIZATION'S ASSET REGISTER sanctions with a Flags entry, and name it:
                  (a) hub -- the asset is flagged `hub`: other systems
                      authenticate against it, load config from it, or deploy
                      from it, and one call discloses, corrupts or removes it
                      wholesale.
                  (b) population -- the asset is flagged `population` (or
                      `self-sufficient`) and one call reaches its ENTIRE set of
                      subjects at once.
                  (c) irreversible-total -- the whole asset is destroyed with no
                      path back, so nothing remains to restore.

DISCIPLINE
- If the asset carries NO escape flag in the register, the ceiling is 4. Do not
  infer a population or hub escape from prose adjectives.
- Reading a listing, names, or metadata is reconnaissance: it exposes no contents
  and removes nothing, so it cannot exceed the metadata tier.
- Reach is RELATIVE TO THIS ASSET: touching the only item of a single-item asset
  is 100% of it. Physical size is a red herring.
- CONSISTENCY: the sibling lists below are the SAME server. The same kind of call
  on two comparable assets must not differ by more than one tier without a reason
  you can state in one sentence.

RELEVANCE FIRST: does this tool act on this asset AT ALL? If it operates only on
a different class, set affects_asset=false and blast_radius=null (N/A, not a low
score).
```

## 3 · Blast radius — return schema

```text
Tool: {tool_json}
Asset: {asset_json}
Other tools on this server: {peer_tools}
Other assets on this server: {peer_assets}

Return JSON: {{"tool_name": str, "asset_id": str, "affects_asset": bool,
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
