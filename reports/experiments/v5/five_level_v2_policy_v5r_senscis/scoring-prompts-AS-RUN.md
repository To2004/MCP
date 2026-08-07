# Static-scoring prompts — experiment `five_level_v2_v5r_senscis` (with org description)

Every prompt this experiment's scan sent to the local LLM, verbatim from `src/mcp_security/static_scoring/prompts.py`. Generated -- do not hand-edit; edit the templates and re-run `scripts/dump_scoring_prompts.py`.

Risk formula: `score = asset_sensitivity × blast_radius × likelihood(1.0) × tool_impact`, score_max = 125. The **tool-impact** and **blast** stages vary by experiment; asset sensitivity is shared.

This run carries an **organizational description** (a profile or a policy) in the registry, so the domain-inference user message and the shared proposer preamble below are their `_DESC` variants: the org's text is placed in front of EVERY stage, including asset sensitivity. `{org_description}` is where that document's section for the scanned server is substituted verbatim.


## 0 · Domain inference (system)

Runs once over the whole registry. Infers mcp_kind (plus content_unit / contents_definition) and defines what the primitives mean HERE.

```text
You are calibrating a risk scorer for one MCP server.
From the tool registry alone, say what this server is and what "one item" means
here. Nothing else — the deploying organization supplies the rest.

Output ONLY valid JSON, no prose, no fences.

- mcp_kind: what system this MCP fronts (filesystem, SQL database, calendar,
  chat workspace, source repository, cloud infra, ...).
- content_unit: what ONE item concretely is here — a file, a row, a message, an
  event, a record.
- contents_definition: one sentence — what counts as an item's CONTENTS (bodies,
  values, message text) as opposed to METADATA about it (ids, counts, sizes,
  timestamps, permissions, schema).

Set needs_human_review=true, and confidence below 0.7, if the registry is too
sparse to tell.
```

## 0 · Domain inference (user)

Carries the org's description, the tool registry and a sample of asset classes into the stage above.

```text
Tools:
{tools_json}

Return JSON: {{"mcp_kind": str, "content_unit": str, "contents_definition": str,
"confidence": 0.0-1.0, "needs_human_review": bool}}
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

## 1 · Tool impact — FALLBACK ONLY (operation-type ladder)

EXPERIMENT V5R: impact is the deterministic ladder in static_impact.classify_by_operation() FIRST — read / write / remove, with scoped writes sharing tier 3 with content reads. This prompt is sent only where the rules abstain. Open-world left the ladder (a channel is not an operation) and annotation hints no longer bound anything.

```text
You are classifying one MCP tool. Output ONLY valid JSON,
no prose, no fences.

TASK: Assign TOOL IMPACT (1-5) — what OPERATION one call performs, judged from
the tool's description and parameters. Not how much it touches (blast radius
scores that), not how valuable the target is (sensitivity scores that).

Ask only: does it read, does it write, or does it remove?

  1 NO EFFECT      the caller learns only that the service is reachable, or facts
                   about its own session: ping, health, version, clock, whoami.
  2 METADATA       returns or changes only about-ness — names, ids, counts, sizes,
                   timestamps, permissions, schema, a listing; or consumption
                   state: mark read, star, pin, mute, rename.
  3 CONTENT READ or LIMITED WRITE
                   returns the substance itself (bodies, values, message text), OR
                   writes a bounded amount and leaves the rest of the item
                   untouched: append a line, add a comment or a reply, set one
                   named field, post a short message. HTTP calls this PATCH; CVSS
                   calls it "the amount of modification is limited".
  4 WRITE          the ordinary write: the caller supplies what the item says.
                   Create a record with its fields, update an event, write a file,
                   overwrite content. HTTP calls this PUT; CVSS calls it a total
                   loss of integrity for that item.
  5 REMOVAL or EXECUTION
                   no path back from inside the system: delete, wipe, drop, purge,
                   truncate; or it executes code, runs a command, or moves money.

RULES
- Score the DESCRIPTION and PARAMETERS, never the name alone.
- The CHANNEL is not the operation. Sending mail, posting externally or invoking a
  webhook creates a message — that is a write. Whether a specific call actually
  leaves the organization is a runtime fact, scored elsewhere.
- Annotation hints (readOnlyHint, destructiveHint, idempotentHint) are HINTS. They
  may corroborate; they never bound the answer. If a hint contradicts the
  description, follow the description and say so in your reasoning.
- A write is an ordinary write (4) unless the declaration says the amount is
  bounded (3). If it does not say, judge from the parameters: a single
  content/body field is a whole write; named optional fields are a patch.
- A tool that can do two of these takes the more consequential one.

Tool:
{tool_json}

Return JSON (reason first): {{"tool_name": str, "reasoning": str,
"tool_impact": 1-5, "confidence": 0.0-1.0}}
```

## 2 · Asset sensitivity (1-5) — task

CLASSIFY the asset against the org policy (register → recognition rules → default class), then MAP that class's adverse-impact definition onto the absolute 1-5 scale.

```text
TASK: Assign ASSET SENSITIVITY (1-5) starting from the organization's data
classification scheme, in the spirit of CIS Critical Security Control 3.

Work in three steps.

  1 SORT BY SENSITIVITY using the organization's own scheme (CIS Safeguard 3.7).
    Its scheme may be COARSE — CIS requires only enough levels to tell sensitive
    data from other data, so an organization may give you two classes where this
    scale has five. That is normal. Do not refuse to score because the scheme is
    thin.

  2 REFINE with the policy's recognition rules and the asset's own description.
    Where the scheme is coarse, the description carries the detail: what the
    asset characteristically holds, who it is about, and what depends on it. Ask
    what this data IS, then where it falls between the classes the org named.

  3 MAP onto the scale below.

  5 CROWN JEWEL  exposure alone is an emergency — exploitable or legally
                 reportable the moment it leaks; OR a control plane, where losing
                 it rewires what every other tool can reach.
  4 RESTRICTED   serious lasting harm one step removed: damages customers, staff
                 or the organization's position, but is not instantly weaponizable.
  3 INTERNAL     disruptive and embarrassing but recoverable; meant to stay in-org.
  2 ROUTINE      low-value internal material; exposure is a shrug.
  1 PUBLIC       already published or disposable — no confidentiality left to lose.

RULES
- ABSOLUTE scale, never relative to the other assets here. A whole server sitting
  at one tier is expected; do NOT spread scores to manufacture contrast.
- CONTAINER: takes the tier of the most sensitive thing it CHARACTERISTICALLY
  holds — its typical payload, not a conceivable one.
- AGGREGATION: if one asset holds the WHOLE population of a class, or the policy
  names a combination that reveals more than its parts, raise one tier.
- PUBLISHED, NOT TOPIC: data the organization has already published has no
  confidentiality left to lose and is 1, however sensitive its subject sounds.
- A COARSE SCHEME IS NOT A LOW SCORE. If the organization only distinguishes
  "sensitive" from "other", an asset in the sensitive class still spans 3-5 here
  and the description decides which. Do not collapse everything sensitive to one
  tier.
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
TASK: Assign BLAST RADIUS (1-5) for ONE (tool, asset) pair —
HOW FAR the consequences of one call PROPAGATE. What the asset is worth is scored
separately and already multiplied in; price the SPREAD of the consequence only.

COUNT SUBJECTS AND SYSTEMS, NOT ITEMS, and count them in ORGANIZATIONAL SCOPE.
How many rows a call touches is a weak proxy and often the wrong one. Reading ONE
password file touches one item and reaches every system that password opens.
Ask: after this call, WHO is different, and how far across the organization do
they sit?

  1 ONE PERSON OR ITEM   the consequence stops at a single subject, or a single
                         item nothing and nobody depends on. A colour palette, a
                         scratch record, one person's own state.
  2 ONE GROUP            the people or systems attached to what the call touched,
                         within one team or one bounded scope — the attendees of
                         an event, the members of a channel, the consumers of one
                         record. **This is the normal case for a call that touches
                         real organizational data. Start here and move for a
                         reason.**
  3 SEVERAL GROUPS       the consequence crosses team or scope boundaries — an
                         event spanning several teams, a set of channels, records
                         belonging to more than one part of the organization.
  4 ORGANIZATION-WIDE    essentially everyone or everything this asset serves,
                         at once — but the consequence still stops at the
                         organization's boundary.
  5 BEYOND               the consequence does not stay inside this asset or the
                         organization. It reaches systems, identities or people
                         outside it, or it cannot be contained once it starts.

BEFORE AWARDING 5, ask these four questions of the asset's own description. Answer
each yes or no, and for any yes QUOTE the words in the description that support
it. A 5 with no quotable support is not a 5 — say so and score 4.

  Q1 LOAD-BEARING   Do other systems depend on this to function — do they
                    authenticate against it, load configuration from it, or deploy
                    from it? Then reaching it reaches them.
  Q2 PORTABLE       Is what this call RETURNS usable on its own somewhere else — a
                    credential, a key, a token? Then the consequence leaves with
                    the data even though one item was touched.
  Q3 WHOLE SET      Does one call reach the ENTIRE population of subjects this
                    asset covers, rather than some of them?
  Q4 NOTHING LEFT   Is the asset destroyed outright, with nothing remaining to
                    restore from?

Do NOT award a tier because the material is confidential, executive or otherwise
sensitive. How valuable it is has already been scored and multiplied into this
cell. Score only how far the consequence travels.

Reach is relative to THIS asset: touching the only item of a single-item asset is
all of it.

RELEVANCE. The organization's register lists which tools it believes reach this
asset; that list is given below. Use it like this:

  * IF THE REGISTER LISTS THIS TOOL — relevance is settled. The organization is
    not guessing about its own surface. Score the reach; do not return null.
  * IF THE REGISTER DOES NOT LIST IT — you decide, but silence is not evidence of
    absence. Registers are written by hand and miss shared surfaces. Ask whether
    this tool genuinely reaches this asset, not whether somebody wrote it down.

N/A IS THE MORE EXPENSIVE MISTAKE. A wrong low score stays in the matrix where a
reviewer can see it and argue with it. A wrong N/A deletes the cell — nobody ever
looks at it again, and a real consequence goes unrecorded. They are not
symmetric. So:

  * return null ONLY when the tool operates on a genuinely different class of
    thing and could not touch this asset by any route;
  * when you are unsure, score 1 — "one person or item" — rather than null. An
    over-scored 1 costs almost nothing; a wrongly hidden cell costs everything.
```

## 3 · Blast radius — return schema

```text
Tool: {tool_json}
Asset: {asset_json}
The organization's register says these tools reach this asset: {register_tools}
Already decided for this pair — tool impact: {tool_impact} · asset sensitivity: {asset_sensitivity}
Other tools on this server: {peer_tools}
Other assets on this server: {peer_assets}

Return JSON: {{"tool_name": str, "asset_id": str, "affects_asset": bool,
"coverage_reasoning": str,
"escape": "EXACTLY ONE of these five strings: Q1, Q2, Q3, Q4, none",
"escape_evidence": "the words quoted from the asset description, or empty",
"blast_radius": "1-5 or null", "confidence": 0.0-1.0}}
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
