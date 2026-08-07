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


# Same inference, but the deploying organization supplied a written description of
# this server (five_level_v2_desc experiment). The description is authoritative for
# WHO runs the server and WHAT it is for; the registry stays authoritative for what
# the tools can actually do, so the model cannot invent an irreversible action the
# tool set cannot perform.
DOMAIN_INFERENCE_USER_DESC = """ORGANIZATION'S OWN DESCRIPTION of this MCP server
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
  "worked_example": str, "confidence": 0.0-1.0, "needs_human_review": bool}}"""


# --- Shared preamble for proposers ------------------------------------------

_PROPOSER_BASE = """You are a security classifier for an MCP gateway. The domain
was inferred from the server's registry and is described below; trust it as the
ground truth for what assets and reach mean here.

INFERRED DOMAIN PROFILE:
{domain_profile}

Output ONLY valid JSON, no prose, no fences."""

# Preamble when the deploying organization supplied a written profile of the server
# (five_level_v2_desc). EVERY proposer stage sees it, so the org's stated severity
# and CIA emphasis is in view for tool impact, blast radius and baselines alike.
_PROPOSER_BASE_DESC = """You are a security classifier for an MCP gateway. Two
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

Output ONLY valid JSON, no prose, no fences."""


# Preamble with the org description ONLY — no inferred domain profile at all
# (five_level_v2_ult_nodom): the profile spec carries content unit, hubs
# (flags), and irreversible actions itself, so the description is the single
# source of context.
_PROPOSER_BASE_DESC_ONLY = """You are a security classifier for an MCP gateway.
The organization that deploys this server describes it below; trust that
description as the ground truth for what the server is for, what its assets
hold and how severe each one is, which items are load-bearing hubs or whole
populations (the flags), what one content item is, and which actions cannot be
undone here.

ORGANIZATION'S DESCRIPTION OF THIS MCP SERVER:
{org_description}

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
single capability that sets the tier, then score. Reason first."""

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
      ids/names, existence, sizes/timestamps, free/busy, status, describe schema);
      a pure no-op (ping, whoami, get time); OR changes ONLY consumption/view state
      about content (mark read/unread, star, pin, mute, notification settings) --
      state about who has SEEN data is metadata, not data.
  2 = CONTENT READ: reads or returns the actual CONTENTS of data (read, get,
      search returning bodies, export) -- ANY scope; blast prices how much.
  3 = CREATE / SCOPED WRITE: creates new items or makes a scoped, recoverable
      change (create, add, post-internal, update, edit, append).
  4 = DESTRUCTIVE / ADMIN / EXTERNAL SEND: deletes or overwrites existing data, OR
      changes privilege / membership / account / permission / config, OR sends
      content OUTSIDE the system (email, webhook, public post) -- irreversible.
  5 = MASS-DESTRUCTIVE: wipes, drops, or irreversibly destroys an entire store or
      many assets at once.
JUDGE BY WHAT THE TOOL RETURNS OR CHANGES, NOT ITS VERB:
  - A list/get/search tool whose response includes item CONTENTS (bodies, titles,
    message text, code, cell values) is a CONTENT READ (2), even if the verb is
    "list". If it returns only ids/names/counts/timestamps, it is tier 1.
  - A tool that only reads the CALLER'S OWN state (whoami, own profile, own
    memberships) is tier 1 regardless of its noun.
Judge the REALISTIC worst outcome per the inferred mcp_kind. A tool that reaches
several tiers takes the HIGHEST (a create-or-update tool that can also delete is 4).
SELF-CHECK before you answer: name the single capability that sets the tier
(trigger_capability) and the realistic worst_case, then score. Reason first."""

TOOL_IMPACT_USER_HYBRID = """Tool registry entry:
{tool_json}

Return JSON (reason BEFORE you score -- emit these keys in this exact order):
{{"tool_name": str, "trigger_capability": str, "worst_case": str,
  "irreversible": bool, "reasoning": str, "tool_impact": 1-5,
  "confidence": 0.0-1.0}}"""


# --- 2. Asset Sensitivity ----------------------------------------------------

ASSET_TASK = """
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
NEVER applies to public data."""

ASSET_USER = """Asset class entry:
{asset_json}

Return JSON (reason BEFORE you score -- emit these keys in this exact order):
{{"asset_id": str, "drivers": [str], "reasoning": str,
  "sensitivity": 1-5, "confidence": 0.0-1.0}}"""

# Sensitivity when the ORGANIZATION SUPPLIED A WRITTEN POLICY (the policy scheme of
# docs/standards/mcp-policy-spec.md: a classification table of class x adverse-impact
# definition, an asset register, and recognition rules -- but no numbers). The model's
# job shrinks from "invent a severity" to "classify, then map the class onto the
# scale", which is how FIPS 199 / SP 800-60 and the university standards (Stanford,
# Berkeley P1-P4) actually work: the org defines classes by adverse effect, the
# categorizer assigns the level, and aggregation adjusts it.
ASSET_TASK_POLICY = """
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
  regulated records: take the HIGHER. Never for public data."""

ASSET_USER_POLICY = """Asset class entry:
{asset_json}

Return JSON (classify BEFORE you score -- emit these keys in this exact order):
{{"asset_id": str, "policy_class": str, "reasoning": str,
  "sensitivity": 1-5, "confidence": 0.0-1.0}}"""


# --- 3. Blast Radius ---------------------------------------------------------

# Shared COVERAGE rubric body, used by every blast variant below. It says NOTHING
# about metadata (the metadata-vs-content distinction lives in tool_impact, not
# blast) and NOTHING about whether the tool applies to the asset -- that is either
# the non-N/A "doesn't act -> 1" line or the N/A relevance gate, appended per mode.
_BLAST_COVERAGE_BODY = """
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
give the number."""

# Non-N/A modes (baseline / five_level / five_level_v2) have no relevance gate, so
# a tool that does not act on this asset scores the floor.
BLAST_TASK = _BLAST_COVERAGE_BODY + ("\nIf the tool does not act on this asset at all, blast = 1.")

BLAST_USER = """Tool:
{tool_json}

Asset class:
{asset_json}

Return JSON (reason about reach FIRST, then escape route, blast_radius LAST).
escape is "a", "b", or "c" when a tier-5 route fired, else "none":
{{"tool_name": str, "asset_id": str, "coverage_reasoning": str,
  "escape": "a|b|c|none", "blast_radius": 1-5, "confidence": 0.0-1.0}}"""


# --- 3b. Blast Radius — reach-of-consequences variant (hybrid experiment) -----

BLAST_TASK_CONSEQUENCES = """
TASK: Assign BLAST RADIUS (1-5) for one (tool, asset class) pair -- the REACH of the
consequences of ONE call: everything that becomes exposed, changed, broken, or
reachable as a result, counting BOTH what the call directly touches AND what its
effects propagate to through dependencies. Direct coverage sets the floor; dependency
fallout can raise it, never lower it.
  1 = PINPOINT: one item among very many, OR metadata only (ids, names, sizes,
      timestamps, existence, free/busy, schema) with no contents; consequences end
      at that item. State ABOUT content (read markers, seen/unseen, flags, mute)
      is metadata -> PINPOINT. Also 1 if the tool does not really touch this asset.
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
          call discloses, corrupts, or removes it WHOLESALE -- deleting OR leaking
          a password file is 5, not 4, even though it is "one file", because
          everything that authenticates through it is affected. WHOLESALE means the
          call touches ALL OR MOST of the hub in one call; ONE SLICE of a hub (one
          PR's diff, one config key, one credential) takes the coverage tier, NOT 5.
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


# --- 3c. Blast Radius — reach-of-consequences + N/A (hybrid_na experiment) -----

_NA_RELEVANCE = """
RELEVANCE (answer this FIRST): does this tool ACT ON this asset class AT ALL? A
tool that operates only on a DIFFERENT class -- a mail-sender against a DNS-zone
asset, an image resizer against an audio store, a writer for shard A against shard
B -- does NOT affect this asset: set affects_asset=false, blast_radius to null (do
NOT invent a number), escape to "none", and the cell is N/A (not scored, it renders
as "na" in the table). ONLY when affects_asset=true do you give a blast_radius of
1-5. Relevance is decided ONCE here -- never also fold "doesn't touch" into a
blast_radius=1; a non-touching pair is N/A, not a low score."""

BLAST_TASK_CONSEQUENCES_NA = BLAST_TASK_CONSEQUENCES + "\n" + _NA_RELEVANCE

# Plain COVERAGE blast + the N/A relevance gate (five_level_v2_na experiment). Built
# from the shared coverage BODY (not BLAST_TASK) so the non-N/A "doesn't act -> 1"
# line is NOT included -- relevance is handled solely by the gate below, so the two
# never double-encode the same judgment.
BLAST_TASK_NA = _BLAST_COVERAGE_BODY + "\n" + _NA_RELEVANCE

# --- 3e. Blast Radius — description-driven, no sensitivity (five_level_v2_desc) --
# In this mode asset sensitivity is NOT scored as a separate primitive: the score is
# blast x impact, and how much the asset matters comes from the organization's own
# written description in the preamble. The coverage body tells the model that
# "how valuable the data is is priced by sensitivity" -- that sentence is false here
# (there is no sensitivity factor), so this note corrects it explicitly rather than
# leaving the model to reconcile a rubric that references a primitive nobody scores.
_NO_SENS_NOTE = """
NO SEPARATE SENSITIVITY SCORE IN THIS RUN. The rubric above says value is "priced
by sensitivity" -- in this run there is no sensitivity factor at all: the final
score is blast_radius x tool_impact only. This does NOT mean you should smuggle
value into blast. Blast still prices REACH and REACH ALONE -- how much of the asset,
how many of its subjects, and what beyond it one call touches. What the asset is
worth is already stated in the ORGANIZATION'S DESCRIPTION above; use that
description to decide two things and nothing else:
  (1) WHICH ASSETS ARE DEPENDENCY HUBS or DANGEROUS-CLASS POPULATIONS here -- the
      description names them and says why -- since those are what open the tier-5
      escape routes (b) and (c);
  (2) WHOSE data and WHICH dependents an asset actually carries, so "reach across
      subjects and dependents" is judged against the real organization rather than
      guessed from the asset's name.
An asset the organization calls critical does NOT get a higher blast for a pinpoint
touch: one record read from a crown-jewel store is still tier 1-2 reach. Conversely
an asset the organization calls routine still scores 4 when one call takes all of
it. Severity enters through impact and through the description, never by inflating
coverage."""

BLAST_TASK_NA_DESC = _BLAST_COVERAGE_BODY + "\n" + _NA_RELEVANCE + "\n" + _NO_SENS_NOTE

# five_level_v2_ult: sensitivity IS a factor again, but it comes from the org's own
# per-asset table in the description rather than from an LLM stage. The note keeps
# blast pure reach (the desc experiment showed value otherwise leaks into blast:
# read-one-file scored blast 5 on payslips vs 1 on README with identical coverage).
_PROFILE_SENS_NOTE = """
SENSITIVITY IS SUPPLIED SEPARATELY IN THIS RUN. Each asset's 1-5 sensitivity is
taken directly from the organization's own per-asset table in the description
above and multiplied into the final score (sensitivity x blast x impact) -- you
do not score it, and you must NOT price it again here. Blast prices REACH and
REACH ALONE: how much of the asset, how many of its subjects, and what beyond it
one call touches. Do NOT raise blast because the description calls an asset
critical -- a pinpoint touch of a crown jewel is still tier 1-2 reach, and a
routine asset fully covered is still 4. Use the description only to know WHICH
assets are dependency hubs or dangerous-class populations (tier-5 escape routes b
and c) and WHOSE data an asset carries when judging reach across subjects."""

BLAST_TASK_NA_PROFILE = _BLAST_COVERAGE_BODY + "\n" + _NA_RELEVANCE + "\n" + _PROFILE_SENS_NOTE

# v3 (ult/pure): explicit bulk-vs-singular guidance. The impact stage scores one
# tool in isolation, so nothing otherwise forces `create-events` to price at or
# above `create-event`; these notes teach the rule, and a deterministic bulk-twin
# pass in assembly backstops it.
_BULK_IMPACT_NOTE = """
  - BULK vs SINGULAR VARIANTS: a tool that performs the same operation on MANY
    items in one call (a pluralized twin, a "multiple"/"bulk"/"batch" variant, an
    array-of-items parameter) takes AT LEAST its singular twin's tier — and when
    the bulk description drops a safety the singular has (skips confirmation,
    conflict or duplicate detection, validation), that loss of recoverability
    signals the HIGHER tier."""

_ARRAY_REACH_NOTE = """
BULK PARAMETERS: a tool whose call accepts an ARRAY of items (event lists, file
lists, batch ids) reaches MANY items in one call by construction — its reach is
never tier 1, and it must not price below its singular twin on the same asset."""

TOOL_IMPACT_TASK_5LEVEL_V3 = TOOL_IMPACT_TASK_5LEVEL_V2 + _BULK_IMPACT_NOTE

BLAST_TASK_NA_PROFILE_V3 = (
    _BLAST_COVERAGE_BODY
    + "\n"
    + _NA_RELEVANCE
    + "\n"
    + _PROFILE_SENS_NOTE
    + "\n"
    + _ARRAY_REACH_NOTE
)

BLAST_USER_NA = """Tool:
{tool_json}

Asset class:
{asset_json}

Return JSON (relevance FIRST, then reasoning, then escape route, score LAST). Emit
blast_radius as null when affects_asset is false, else an integer 1-5; escape is
"a", "b", or "c" when a tier-5 route fired, else "none":
{{"tool_name": str, "asset_id": str, "affects_asset": bool,
  "coverage_reasoning": str, "escape": "a|b|c|none",
  "blast_radius": "1-5 or null", "confidence": 0.0-1.0}}"""


# --- 3d. Blast Radius — context-first (five_level_v2_ctx experiment) ----------
# The model first builds an UNDERSTANDING of each tool (its role in this MCP, what
# one call can reach, why it matters) in a separate per-tool stage; that profile is
# then injected into every blast decision for the tool. Hypothesis: coverage blast
# under-scores pinpoint mutations (create/delete one event) because the scorer never
# considers what the touched item MEANS to the asset's subjects.

TOOL_CONTEXT_TASK = """
TASK: Build a security UNDERSTANDING of ONE tool in the context of this whole MCP
server -- you are NOT scoring anything yet. A later stage will judge how far one
call of this tool reaches; your job is to give that stage the context it needs to
judge well. Study the tool's description and parameters AGAINST the full tool
registry and the inferred domain profile, then explain:
- role: what this tool is FOR in this server's normal workflow, and how central it
  is relative to the other tools (is it the main read? the only destructive op?).
- single_call_reach: concretely, the MOST one call can touch given its parameters
  -- how many items, which scopes, whose data; note parameters that widen reach
  (bulk lists, recurrence scopes, wildcards, "all" flags).
- consequence_carriers: WHO and WHAT actually feel the effect of one call -- the
  people behind the items (an event's attendees, a channel's members, a file's
  consumers), downstream systems, and whether the effect is visible or silent.
- worst_realistic_misuse: the single worst thing ONE misused call realistically
  does in this domain, and what it takes to recover from it.
- importance: why this tool matters (or does not) for protecting this server --
  one or two sentences.
Ground every statement in the description and domain profile; do not invent
capabilities the description does not support."""

TOOL_CONTEXT_USER = """Tool to understand:
{tool_json}

Full tool registry of this server (for relative context):
{tools_json}

Return JSON:
{{"tool_name": str, "role": str, "single_call_reach": str,
  "consequence_carriers": str, "worst_realistic_misuse": str,
  "importance": str, "confidence": 0.0-1.0}}"""

# Same rubric as BLAST_TASK_NA; the user message additionally carries the tool's
# understanding profile so reach is judged with the tool's meaning in view.
BLAST_USER_NA_CTX = """Tool:
{tool_json}

TOOL UNDERSTANDING (from a prior analysis of this MCP and this tool; trust it as
context): {tool_profile}

Asset class:
{asset_json}

Judge reach WITH this understanding in view: consequences count for every subject
and dependent the call's effects actually touch (attendees, members, consumers --
per consequence_carriers), not only the raw item count; a silent or hard-to-notice
effect reaches further than a visible one. The rubric's tiers still decide the
number.

Return JSON (relevance FIRST, then reasoning, then escape route, score LAST). Emit
blast_radius as null when affects_asset is false, else an integer 1-5; escape is
"a", "b", or "c" when a tier-5 route fired, else "none":
{{"tool_name": str, "asset_id": str, "affects_asset": bool,
  "coverage_reasoning": str, "escape": "a|b|c|none",
  "blast_radius": "1-5 or null", "confidence": 0.0-1.0}}"""


# --- 4. Baseline -------------------------------------------------------------

BASELINE_TASK = """
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
Match this granularity and keep each pattern decidable against a single tool call."""

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


# --- v4: standards-grounded, short-form prompts -------------------------------
# Rewritten against published standards instead of hand-grown prose; see
# reports/experiments/v4/scoring-prompts.md for the sources and the rationale.
#   impact -> the MCP tool-annotation vocabulary (readOnly / destructive /
#             openWorld), scored from the tool JSON ALONE (no org profile, no
#             inferred domain profile: the v3 `imponly` arm showed the asset
#             table left 12/13 impacts unchanged).
#   blast  -> CVSS v4.0's Vulnerable-System vs Subsequent-System split, which
#             replaced the retired "Scope" metric for exactly the inconsistency
#             reason we hit; a tier-5 escape now requires a FLAG in the org
#             table, and the sibling tool/asset lists ride along so reach is
#             judged comparatively rather than one blind cell at a time.

TOOL_IMPACT_TASK_V4 = """You are classifying one MCP tool. Output ONLY valid JSON,
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
- A bulk/batch variant takes AT LEAST its singular twin's tier."""

TOOL_IMPACT_USER_V4 = """Tool:
{tool_json}

Return JSON (reason first): {{"tool_name": str, "reasoning": str,
"tool_impact": 1-5, "confidence": 0.0-1.0}}"""


BLAST_TASK_V4 = """TASK: Assign BLAST RADIUS (1-5) for ONE (tool, asset) pair --
HOW FAR the consequences of one call reach. This is the CVSS v4.0 question: does
the impact stay inside this asset (the "vulnerable system"), or does it reach
systems, identities and data beyond it (a "subsequent system")?

Sensitivity is supplied separately by the organization's table and is ALREADY
multiplied into the score. Do NOT price value here. Blast prices REACH ONLY.

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
                  ORGANIZATION'S TABLE sanctions, and name it:
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
- If the asset carries NO escape flag in the table, the ceiling is 4. Do not
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
score)."""

BLAST_USER_V4 = """Tool: {tool_json}
Asset: {asset_json}
Other tools on this server: {peer_tools}
Other assets on this server: {peer_assets}

Return JSON: {{"tool_name": str, "asset_id": str, "affects_asset": bool,
"coverage_reasoning": str, "escape": "a|b|c|none",
"blast_radius": "1-5 or null", "confidence": 0.0-1.0}}"""


# v5: the same rubric as V4, retargeted at a POLICY-grade organization. Two
# statements in V4 name an artifact the policy arm does not have -- the org's
# per-asset sensitivity TABLE. Here sensitivity is derived by the sensitivity
# stage from the classification policy, and the escape routes are sanctioned by
# the asset register's Flags column instead. Everything else is V4 verbatim, so a
# v4-vs-v5 diff stays attributable to the inputs rather than to the rubric.
BLAST_TASK_V5 = (
    BLAST_TASK_V4.replace(
        "Sensitivity is supplied separately by the organization's table and is ALREADY\n"
        "multiplied into the score.",
        "Sensitivity is scored separately from the organization's classification\n"
        "policy and is ALREADY multiplied into the score.",
    )
    .replace(
        "Award 5 only via a route the\n                  ORGANIZATION'S TABLE sanctions",
        "Award 5 only via a route the\n                  ORGANIZATION'S ASSET REGISTER sanctions"
        " with a Flags entry",
    )
    .replace(
        "- If the asset carries NO escape flag in the table, the ceiling is 4.",
        "- If the asset carries NO escape flag in the register, the ceiling is 4.",
    )
)


# ===========================================================================
# v5r — shorter prompts, classified by OPERATION TYPE
# ===========================================================================
#
# What changed and why (audit: reports/experiments/v5/PROMPT_ROLES.md):
#
# * **Domain inference loses seven of its ten fields.** `dependency_hubs`,
#   `dangerous_classes` and `irreversible_actions` asked the model to infer what
#   the organization now STATES: hubs are the register's `Flags` column,
#   dangerous classes are the classification table, prohibited/irreversible
#   operations are the policy's operation limits. Inferring them alongside the
#   policy invited the two to disagree. `asset_meaning`, `blast_radius_meaning`
#   and `worked_example` were prose no stage consumed, re-serialized into every
#   later prompt. What survives is what blast actually needs: what this system is
#   and what one item is here.
# * **The finance paragraph is gone.** "SEC insider-trade / Form 4 filings,
#   institutional-holding / 13F filings, central-bank series" was a list of one
#   domain's document types inside a domain-agnostic prompt, written to stop
#   over-scoring on the finance corpus. The clause that generalizes — already
#   published data has nothing left to leak — lives in the sensitivity rubric,
#   where the decision is actually made.
# * **Open-world leaves the impact ladder.** Whether a call leaves the
#   organization is a channel, not an operation; "it is an email" says nothing
#   about read / write / remove. Sending creates a message, so it is a write.
#   The dynamic stage prices boundary crossing, where the recipient is known.
# * **Annotation hints stop bounding anything.** The protocol's own guidance is
#   that hints "are not guaranteed to faithfully describe tool behavior"; a
#   server must not be the authority on its own risk score.
# * **The blast DISCIPLINE block loses three of its four lines** — a ceiling
#   written to kill one v3 over-read, a sentence using impact vocabulary
#   ("cannot exceed the metadata tier") that has no referent among the blast
#   tiers, and a consistency instruction the model cannot follow because each
#   cell is scored in its own call. Consistency is enforced deterministically by
#   the alias-twin pass instead.

DOMAIN_INFERENCE_SYSTEM_V5R = """You are calibrating a risk scorer for one MCP server.
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
sparse to tell."""

DOMAIN_INFERENCE_USER_V5R = """Tools:
{tools_json}

Return JSON: {{"mcp_kind": str, "content_unit": str, "contents_definition": str,
"confidence": 0.0-1.0, "needs_human_review": bool}}"""


TOOL_IMPACT_TASK_V5R = """You are classifying one MCP tool. Output ONLY valid JSON,
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
"tool_impact": 1-5, "confidence": 0.0-1.0}}"""


BLAST_TASK_V5R = """TASK: Assign BLAST RADIUS (1-5) for ONE (tool, asset) pair —
HOW FAR the consequences of one call PROPAGATE. What the asset is worth is scored
separately and already multiplied in; price the SPREAD of the consequence only.

COUNT SUBJECTS AND SYSTEMS, NOT ITEMS. How many rows a call touches is a weak
proxy and often the wrong one. Reading ONE password file touches one item and
compromises every system that password opens — that is a 5, not a 1. Creating ONE
calendar event touches one item and reaches everyone invited to it. Ask: after
this call, who and what is different?

  1 ALMOST NOBODY  the consequence stops at one item that nothing and nobody
                   depends on. A colour palette, a scratch record, a static list.
                   If a person or a system is meaningfully affected, this is not 1.
  2 A FEW          a handful of subjects, or one small bounded scope.
  3 A GROUP        the people or systems attached to what the call touched — the
                   attendees of an event, the members of a channel, the consumers
                   of a record. **This is the normal case for a call that touches
                   real organizational data. Start here and move for a reason.**
  4 THE WHOLE SET  everyone or everything this asset covers, at once — but the
                   consequence still stops at the asset's boundary.
  5 BEYOND         the consequence does not stay inside this asset. Award 5 only
                   via a route the organization's register sanctions, and name it:
                   (a) hub — the asset is flagged `hub`: other systems
                       authenticate against it, load configuration from it, or
                       deploy from it, so changing or reading it reaches them too;
                   (b) self-sufficient — the asset is flagged `self-sufficient`:
                       what this call returns is usable ON ITS OWN elsewhere (a
                       credential, a key, a token), so the consequence LEAVES with
                       the data even though only one item was touched;
                   (c) population — the asset is flagged `population` and one call
                       reaches its ENTIRE set of subjects at once;
                   (d) irreversible-total — the asset is destroyed outright, with
                       nothing left to restore.

Reach is relative to THIS asset: touching the only item of a single-item asset is
all of it.

RELEVANCE FIRST: does this tool act on this asset at all? If it operates only on a
different class, set affects_asset=false and blast_radius=null — N/A, not a low
score."""


# The floors, stated to the model rather than only applied to its answer. The
# deterministic pass in pipeline.apply_gated_floor still enforces them — this just
# stops the model producing a number that is about to be overwritten, which made
# `blast_radius_raw` and `blast_radius` disagree on ~9 cells per server and gave
# the reasoning trail nothing to say about the correction.
#
# The two numbers the floors key on are known before blast runs (sensitivity is
# scored in stage 2, impact in stage 1), so they are handed over as FACTS. The
# risk this accepts: a model that can see the sensitivity may anchor reach on
# value, which is exactly the separation the rubric otherwise enforces — hence
# the explicit "these are inputs, not things to re-judge".
_BLAST_FLOORS_V5R = """
FLOORS — the organization sets these; they are minimums, not targets. The two
numbers below are already decided, so do not re-judge them:
  * asset sensitivity 5  ->  blast radius is at least 4
  * asset sensitivity 4  ->  blast radius is at least 3
  * tool impact 5        ->  blast radius is at least 3
Reaching a crown-jewel asset at all is never a pinpoint consequence, and an
irreversible call is never a pinpoint consequence, whatever the verb. Above the
floor, judge reach on the evidence as usual. If a floor and your own reading
disagree, take the floor and say so in one clause."""

BLAST_TASK_V5R_FLOORED = BLAST_TASK_V5R + "\n" + _BLAST_FLOORS_V5R

BLAST_USER_V5R = """Tool: {tool_json}
Asset: {asset_json}
Already decided for this pair — tool impact: {tool_impact} · asset sensitivity: {asset_sensitivity}
Other tools on this server: {peer_tools}
Other assets on this server: {peer_assets}

Return JSON: {{"tool_name": str, "asset_id": str, "affects_asset": bool,
"coverage_reasoning": str, "escape": "a|b|c|d|none",
"blast_radius": "1-5 or null", "confidence": 0.0-1.0}}"""


# The sensitivity stage is the one that measured well (100 % within one tier), so
# v5r changes exactly one line: the worked finance example comes out. "Financial
# is not confidential" is an argument with the finance corpus; the principle that
# generalizes is that publication, not topic, decides.
ASSET_TASK_POLICY_V5R = ASSET_TASK_POLICY.replace(
    '- PUBLIC OVERRIDE: already-public data is 1 whatever its topic. "Financial" is not\n'
    '  "confidential".',
    "- PUBLISHED, NOT TOPIC: data the organization has already published has no\n"
    "  confidentiality left to lose and is 1, however sensitive its subject sounds.",
)


# ===========================================================================
# v5r flag ablation — two arms
# ===========================================================================
#
# The register's `Flags` column is the organization asserting a CONCLUSION
# (`hub` = reaching this reaches other systems) where the rest of the register
# states FACTS. That conclusion is the blast question, so a flag lets the org
# answer what blast is supposed to derive — and an org may simply not supply it.
#
#   noflags  — no flags reach the model at all. Tier 5 has to be argued from the
#              register's own description, and the route is named in free text
#              instead of being chosen from a closed list.
#   keyflags — flags kept, but only the three that ever changed a score
#              (`hub`, `population`, `self-sufficient`). `metadata-only` was
#              written 12 times and read by nothing, `public` is derivable from
#              "already published", and `completeness-is-the-asset` has never
#              been used at all.
#
# Neither arm shows the model a TOOL capability flag. Those were always computed
# for the rules' own use and never entered a prompt; the model reads the
# parameters directly, which is what the impact rubric already tells it to do.

BLAST_TASK_V5R_NOFLAGS = (
    BLAST_TASK_V5R[: BLAST_TASK_V5R.index("  5 BEYOND")]
    + """  5 BEYOND         the consequence does not stay inside this asset. The
                   register does not label which assets these are, so argue it
                   from the asset's own description and say which of these it is:
                   - it is load-bearing for other systems: they authenticate
                     against it, load configuration from it, or deploy from it,
                     so reaching it reaches them;
                   - what this call returns is usable ON ITS OWN elsewhere (a
                     credential, a key, a token), so the consequence leaves with
                     the data even though only one item was touched;
                   - one call reaches the ENTIRE set of subjects the asset covers;
                   - the asset is destroyed outright, with nothing left to restore.
                   If the description does not support one of these, it is not a 5.

Reach is relative to THIS asset: touching the only item of a single-item asset is
all of it.

RELEVANCE FIRST: does this tool act on this asset at all? If it operates only on a
different class, set affects_asset=false and blast_radius=null — N/A, not a low
score."""
)

BLAST_TASK_V5R_NOFLAGS_FLOORED = BLAST_TASK_V5R_NOFLAGS + "\n" + _BLAST_FLOORS_V5R

# Same payload as BLAST_USER_V5R, except `escape` is prose: with no closed flag
# vocabulary there are no letters to pick from, so the model states the reason and
# a reader can check it against the description.
BLAST_USER_V5R_NOFLAGS = """Tool: {tool_json}
Asset: {asset_json}
Already decided for this pair — tool impact: {tool_impact} · asset sensitivity: {asset_sensitivity}
Other tools on this server: {peer_tools}
Other assets on this server: {peer_assets}

Return JSON: {{"tool_name": str, "asset_id": str, "affects_asset": bool,
"coverage_reasoning": str,
"escape": "one short clause naming why the consequence leaves this asset, or none",
"blast_radius": "1-5 or null", "confidence": 0.0-1.0}}"""


# ---------------------------------------------------------------------------
# A third blast variant: the flag CONCEPTS survive, the flag LABELS do not.
# ---------------------------------------------------------------------------
#
# `noflags` removed the register's Flags column and left tier 5 defined only as
# "argue it from the description". That throws away something worth keeping: the
# three flags were not arbitrary, they name the three ways a consequence actually
# escapes an asset — load-bearing, portable, whole-population. What was wrong was
# the ORG asserting them per asset, not the concepts themselves.
#
# So here the concepts become QUESTIONS the model asks of the description, and
# the evidence has to be quoted back from the organization's own words. The
# scaffold guides the reasoning; the register still supplies the facts; nobody
# hands over a conclusion.
#
# Kept separate from BLAST_TASK_V5R and BLAST_TASK_V5R_NOFLAGS — both remain as
# run, so the three arms stay comparable.

BLAST_TASK_V5R_SELFASSESS = (
    BLAST_TASK_V5R[: BLAST_TASK_V5R.index("  5 BEYOND")]
    + """  5 BEYOND         the consequence does not stay inside this asset.

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

The organization does not label which assets these are. It describes them, and a
description that says "the reach of every other tool", "one record per person" or
"usable alone" is answering one of these questions whether or not it uses the
word.

Reach is relative to THIS asset: touching the only item of a single-item asset is
all of it.

RELEVANCE FIRST: does this tool act on this asset AT ALL? If it operates only on a
different class, set affects_asset=false and blast_radius=null — N/A, not a low
score."""
)

BLAST_TASK_V5R_SELFASSESS_FLOORED = BLAST_TASK_V5R_SELFASSESS + "\n" + _BLAST_FLOORS_V5R

# The escape field carries the question that was answered yes, plus the quote —
# so a reviewer can check the claim against the register without rerunning.
BLAST_USER_V5R_SELFASSESS = """Tool: {tool_json}
Asset: {asset_json}
Already decided for this pair — tool impact: {tool_impact} · asset sensitivity: {asset_sensitivity}
Other tools on this server: {peer_tools}
Other assets on this server: {peer_assets}

Return JSON: {{"tool_name": str, "asset_id": str, "affects_asset": bool,
"coverage_reasoning": str,
"escape": "Q1|Q2|Q3|Q4|none",
"escape_evidence": "the words quoted from the asset description, or empty",
"blast_radius": "1-5 or null", "confidence": 0.0-1.0}}"""
