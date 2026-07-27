"""Prompt templates for the static (design-time) misuse-scoring pipeline.

Each stage of :mod:`mcp_security.static_scoring.pipeline` formats one of these
templates and sends it to the local LLM (Qwen2.5 via Ollama). The templates are
domain-agnostic: stage 0 infers the server's domain from its registry, and every
later stage is anchored to that inferred profile so the same code scores a
payment processor, a filesystem, or a SQL database without per-kind branches.
"""

# --- 0. Domain inference (run once over the whole registry) ------------------

DOMAIN_INFERENCE_SYSTEM = """You are a security analyst bootstrapping a misuse-
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
  on, whose wholesale disclosure, corruption, or removal cascades BEYOND the asset
  itself (e.g. credentials/keys/password stores, auth or infra configuration,
  CI/CD pipeline definitions, DNS zones, package manifests). List traits, not names.
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
domain with confidence (then confidence < 0.7)."""

DOMAIN_INFERENCE_USER = """Tool registry (all tools):
{tools_json}

Sample asset classes:
{assets_json}

Return JSON:
{{"mcp_kind": str, "asset_meaning": str, "blast_radius_meaning": str,
  "content_unit": str, "contents_definition": str, "dependency_hubs": [str],
  "dangerous_classes": [str], "irreversible_actions": [str],
  "worked_example": str, "confidence": 0.0-1.0, "needs_human_review": bool}}"""


# --- Shared preamble for proposers ------------------------------------------

_PROPOSER_BASE = """You are a security classifier for an MCP gateway. The domain
was inferred from the server's registry and is described below; trust it as the
ground truth for what assets and reach mean here.

INFERRED DOMAIN PROFILE:
{domain_profile}

Output ONLY valid JSON, no prose, no fences."""


# --- 1. Tool Impact ----------------------------------------------------------

TOOL_IMPACT_TASK = """
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
  "tool_impact": 2, "confidence": 0.85}"""

TOOL_IMPACT_USER = """Tool registry entry:
{tool_json}

Return JSON (reason BEFORE you score -- emit these keys in this exact order):
{{"tool_name": str, "trigger_capability": str, "worst_case": str,
  "irreversible": bool, "reasoning": str, "tool_impact": 1|2|3,
  "confidence": 0.0-1.0}}"""


# --- 1b. Tool Impact — EXPERIMENT A: 5-level scale ---------------------------

TOOL_IMPACT_TASK_5LEVEL = """
TASK: Assign TOOL IMPACT (1-5) -- the severity of what ONE call of this tool can
do, on this 5-level scale (independent of the asset's sensitivity):
  1 = METADATA observation only: no content disclosure and no meaningful state
      change (stat, list filenames/ids, check existence, size/type/timestamps,
      free/busy, describe schema).
  2 = READ ONE item: discloses the contents of a single item (read one row, get
      one event, fetch one file's contents).
  3 = READ ALL, or EDIT ONE: discloses an entire asset's contents (read-all,
      export, dump), OR makes a scoped recoverable change to one item (edit one
      row, update one record).
  4 = WRITE / EDIT ALL: modifies or overwrites the whole asset (bulk write,
      overwrite-all, mass update).
  5 = DELETE / DESTROY ALL: deletes, wipes, drops, or irreversibly changes the
      entire asset (delete-all, drop, wipe, destroy).
Judge the REALISTIC worst outcome per the inferred mcp_kind. A tool that reaches
several tiers takes the HIGHEST. Reason first, then score."""

TOOL_IMPACT_USER_5LEVEL = """Tool registry entry:
{tool_json}

Return JSON (reason BEFORE you score):
{{"tool_name": str, "reasoning": str, "tool_impact": 1-5, "confidence": 0.0-1.0}}"""


# --- 1b'. Tool Impact — EXPERIMENT A2: 5-level action-type ladder ------------

TOOL_IMPACT_TASK_5LEVEL_V2 = """
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
several tiers takes the HIGHEST. Reason first, then score."""

# Schema is identical to EXPERIMENT A (a single tool_impact 1-5), so this reuses
# TOOL_IMPACT_USER_5LEVEL for the return schema.


# --- 1c. Tool Impact — EXPERIMENT B: base + CIA-triad violations -------------

# CIA experiment: the BASE impact is scored by the STANDARD TOOL_IMPACT_TASK above
# (unchanged, its own call — so the base equals the baseline experiment exactly). A
# SEPARATE call flags which CIA-triad objectives the tool violates; the pipeline then
# sets final impact = base + one point per violated objective.
CIA_FLAGS_TASK = """
TASK: Flag which CIA-triad security objectives this tool VIOLATES. This is scored
SEPARATELY and does NOT change the tool_impact number -- only mark the objectives.
Mark true for EACH the tool can cause:
  confidentiality (C): the tool DISCLOSES data -- any read/list/search/export that
      returns contents violates C.
  integrity (I): the tool MODIFIES or corrupts data -- writes, edits, overwrites,
      deletes change the data's correctness.
  availability (A): the tool can make data or functionality UNAVAILABLE -- delete,
      wipe, drop, revoke, disable.
A pure read violates only C; a write violates I (and often A); a delete violates I
and A. Reason first, then mark C/I/A."""

CIA_FLAGS_USER = """Tool registry entry:
{tool_json}

Return JSON (reason BEFORE you flag):
{{"tool_name": str, "reasoning": str, "violates_confidentiality": bool,
  "violates_integrity": bool, "violates_availability": bool, "confidence": 0.0-1.0}}"""


# --- 1d. Tool Impact — EXPERIMENT HYBRID: action-type only (coverage -> blast) -

TOOL_IMPACT_TASK_HYBRID = """
TASK: Assign TOOL IMPACT (1-5) -- the KIND of action the tool performs (its action
type), independent of the asset's sensitivity AND of coverage (blast prices how
much/how far separately, so do NOT raise impact for touching more items):
  1 = METADATA / NO-OP: reads only metadata ABOUT data, not the data itself (list
      ids/names, existence, sizes/timestamps, free/busy, status, describe schema),
      or a pure no-op (ping, whoami, get time).
  2 = CONTENT READ: reads or returns the actual CONTENTS of data (read, get,
      search returning bodies, export) -- ANY scope; blast prices how much.
  3 = CREATE / SCOPED WRITE: creates new items or makes a scoped, recoverable
      change (create, add, post-internal, update, edit, append).
  4 = DESTRUCTIVE / ADMIN / EXTERNAL SEND: deletes or overwrites existing data, OR
      changes privilege / membership / account / permission / config, OR sends
      content OUTSIDE the system (email, webhook, public post) -- irreversible.
  5 = MASS-DESTRUCTIVE: wipes, drops, or irreversibly destroys an entire store or
      many assets at once.
Judge the REALISTIC worst outcome per the inferred mcp_kind. A tool that reaches
several tiers takes the HIGHEST (a create-or-update tool that can also delete is 4).
Reason first, then score."""

# Schema is a single tool_impact 1-5, so this reuses TOOL_IMPACT_USER_5LEVEL.


# --- 2. Asset Sensitivity ----------------------------------------------------

ASSET_TASK = """
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
HIGHER tier -- under-scoring a crown jewel is the costlier error."""

ASSET_USER = """Asset class entry:
{asset_json}

Return JSON (reason BEFORE you score -- emit these keys in this exact order):
{{"asset_id": str, "drivers": [str], "reasoning": str,
  "sensitivity": 1-5, "confidence": 0.0-1.0}}"""


# --- 3. Blast Radius ---------------------------------------------------------

BLAST_TASK = """
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
Reason FIRST about what fraction one call reaches, THEN give the number."""

BLAST_USER = """Tool:
{tool_json}

Asset class:
{asset_json}

Return JSON (reason about the fraction FIRST, blast_radius LAST):
{{"tool_name": str, "asset_id": str, "coverage_reasoning": str,
  "blast_radius": 1-5, "confidence": 0.0-1.0}}"""


# --- 3b. Blast Radius — reach-of-consequences variant (hybrid experiment) -----

BLAST_TASK_CONSEQUENCES = """
TASK: Assign BLAST RADIUS (1-5) for one (tool, asset class) pair -- the REACH of the
consequences of ONE call: everything that becomes exposed, changed, broken, or
reachable as a result, counting BOTH what the call directly touches AND what its
effects propagate to through dependencies. Direct coverage sets the floor; dependency
fallout can raise it, never lower it.
  1 = PINPOINT: one item among very many, OR metadata only (ids, names, sizes,
      timestamps, existence, free/busy, schema) with no contents; consequences end
      at that item. Also 1 if the tool does not really touch this asset.
  2 = NARROW: a small part of the asset (a few items, one scope); no effect beyond
      the touched items.
  3 = BROAD: a large part of the asset, or several scopes in one call; effects
      still contained within this asset.
  4 = TOTAL: essentially the ENTIRE asset -- read-all / search-all / export /
      bulk-modify / delete-all, or the whole of a single-item asset; consequences
      fill the asset but STOP at its boundary.
  5 = SYSTEMIC: consequences ESCAPE the asset and reach the wider system. Two ways:
      (a) the action is total AND unrecoverable in this domain (wipe, drop,
          overwrite-all with no undo), or
      (b) the asset is a DEPENDENCY HUB (per the inferred dependency_hubs) and the
          call can disclose, corrupt, or remove it wholesale -- deleting OR leaking
          a password file is 5, not 4, even though it is "one file", because
          everything that authenticates through it is affected.
DECISION PROCEDURE -- answer these in order in your reasoning:
  (1) COVERAGE: what fraction of THIS asset does one call directly touch?
  (2) CONTAINMENT: do the effects stay inside the touched items (keep the coverage
      tier) or fill the asset (raise toward 4)?
  (3) PROPAGATION: can the effect cross the asset boundary -- break, expose, or
      grant access to things OUTSIDE this asset? Count only FUNCTIONAL dependencies
      (systems stop working, credentials unlock other assets, configs redirect
      behavior) -- NOT "the data is important"; importance is priced by
      sensitivity, never by blast.
Reason FIRST through the three steps, THEN give the number."""


# --- 4. Baseline -------------------------------------------------------------

BASELINE_TASK = """
TASK: Build the behavioral baseline for one application: the EXPECTED, normal
operations given its stated purpose, so deviation can be measured later. Be
precise, not permissive. List expected tools, typical flow patterns (in this
domain's terms) with their normal max sensitivity, and explicitly list patterns
that would be ANOMALOUS for this app."""

BASELINE_USER = """App catalog entry:
{app_json}

Return JSON (state your reasoning FIRST -- emit these keys in this exact order):
{{"app_id": str, "reasoning": str, "expected_tools": [str],
  "expected_flows": [{{"pattern": str, "normal_sensitivity_max": 1-5}}],
  "anomalous_patterns": [str], "confidence": 0.0-1.0}}"""


# --- Judge (EVALUATION ONLY) -------------------------------------------------
# The judge does NOT run in a production scan. Its band-level corrections are
# folded into the deterministic band_label() floors and its skepticism into the
# proposer tasks above, so a single pass stands alone. These templates remain for
# the evaluation-only crosscheck (StaticScorer.judge()) that measures how often an
# independent reviewer agrees with the base model.

JUDGE_SYSTEM = """You are an independent security reviewer scoring one misuse-
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
Output ONLY valid JSON, no prose, no fences."""

JUDGE_USER = """Decision to make: {field_name} for "{item_key}"

Item:
{item_json}

Determine the correct {field_name} from the rules and the item ALONE, then return
JSON (reason FIRST, value LAST):
{{"reasoning": str, "judged_value": <your value for {field_name}>,
  "confidence": 0.0-1.0}}"""

# NOTE: The former LLM band stage (BAND_TASK/BAND_USER) was removed. Bands are now
# assigned solely by the deterministic band_label() in pipeline.py -- reproducible
# and immune to the critical-band inflation the LLM band stage produced.
