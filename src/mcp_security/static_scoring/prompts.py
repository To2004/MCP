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
BLAST_TASK = _BLAST_COVERAGE_BODY + (
    "\nIf the tool does not act on this asset at all, blast = 1."
)

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
