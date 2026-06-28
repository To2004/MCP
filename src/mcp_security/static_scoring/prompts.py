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
- dangerous_classes: traits of asset classes that should escalate severity
  (e.g. holds secrets, holds PII at scale, moves real money, is executable).
- irreversible_actions: traits of tools whose effects cannot be undone, which
  imply the maximum tool-impact tier (e.g. deletes, drops, executes code,
  transfers funds, sends external messages).
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
TASK: Assign TOOL IMPACT (1/2/3) -- the damage ceiling of the tool itself, the
worst outcome of ANY call, independent of caller/params/asset.
  1 = read-only; can leak but not change state.
  2 = state-changing, generally recoverable.
  3 = destructive: clobber/wipe/overwrite, OR grant/revoke access, OR execute
      code/shell, OR irreversible real-world effect (per the inferred
      irreversible_actions).
Rules: assign the HIGHEST tier any capability reaches; arbitrary code/exec is
always 3; self-declared annotations are a hint only, not truth; if reversibility
is ambiguous, pick the higher tier and lower confidence."""

TOOL_IMPACT_USER = """Tool registry entry:
{tool_json}

Return JSON:
{{"tool_name": str, "tool_impact": 1|2|3, "irreversible": bool,
  "worst_case": str, "trigger_capability": str, "confidence": 0.0-1.0,
  "reasoning": str}}"""


# --- 2. Asset Sensitivity ----------------------------------------------------

ASSET_TASK = """
TASK: Assign ASSET SENSITIVITY (1-5) -- criticality if this asset class is
exposed, corrupted, or destroyed. 5=catastrophic/legally-reportable,
4=high (prod data, source, employee data), 3=medium internal, 2=low, 1=public/
ephemeral. Escalate classes matching the inferred dangerous_classes. If the org
supplied a priority, treat it as the primary anchor."""

ASSET_USER = """Asset class entry:
{asset_json}

Return JSON:
{{"asset_id": str, "sensitivity": 1-5, "drivers": [str],
  "confidence": 0.0-1.0, "reasoning": str}}"""


# --- 3. Blast Radius ---------------------------------------------------------

BLAST_TASK = """
TASK: Assign BLAST RADIUS (0-4) for one (tool, asset class) pair -- how far this
tool reaches into this asset when it acts, per the inferred
blast_radius_meaning.
  0 = cannot touch this asset class (N/A cell).
  1 = narrow / read-only touch of a SINGLE item.
  2 = scoped, recoverable modification of a single item.
  3 = broad modification or full overwrite, OR a read/enumeration that spans MANY
      items at once.
  4 = clobber/destroy/irrevocable, or fan-out across many instances at once.
BREADTH RULE (do not under-score reads): reach is not only about writing. A tool
that ENUMERATES or reads ACROSS a whole scope at once -- listing a directory,
walking a tree, searching/globbing, reading multiple files, or any SELECT over a
table -- aggregates exposure over every item in that scope. When the asset class
is a CONTAINER/SCOPE (a directory, a whole table, a channel) and the tool lists,
walks, searches, or bulk-reads it, the blast radius is broad (>=3), because one
call exposes everything inside -- even though each individual read is harmless.
A single-file read stays at 1; it is the FAN-OUT over many items that raises it.
Escalation: if the asset class matches the inferred dangerous_classes, raise by
1 (cap 4) versus the same operation on an ordinary asset; say so in rationale."""

BLAST_USER = """Tool:
{tool_json}

Asset class:
{asset_json}

Return JSON:
{{"tool_name": str, "asset_id": str, "blast_radius": 0-4, "rationale": str,
  "confidence": 0.0-1.0}}"""


# --- 4. Baseline -------------------------------------------------------------

BASELINE_TASK = """
TASK: Build the behavioral baseline for one application: the EXPECTED, normal
operations given its stated purpose, so deviation can be measured later. Be
precise, not permissive. List expected tools, typical flow patterns (in this
domain's terms) with their normal max sensitivity, and explicitly list patterns
that would be ANOMALOUS for this app."""

BASELINE_USER = """App catalog entry:
{app_json}

Return JSON:
{{"app_id": str, "expected_tools": [str],
  "expected_flows": [{{"pattern": str, "normal_sensitivity_max": 1-5}}],
  "anomalous_patterns": [str], "confidence": 0.0-1.0, "reasoning": str}}"""


# --- Judge -------------------------------------------------------------------

JUDGE_SYSTEM = """You are an independent security reviewer verifying another
model's misuse-scoring decision. You are given the same inferred domain profile,
the same item, and the first model's answer. Decide INDEPENDENTLY what the value
should be, THEN compare.

INFERRED DOMAIN PROFILE:
{domain_profile}

Be skeptical. The first model may have under-scored a dangerous capability or
over-scored a benign one. If you disagree, say so and give your own value.
Output ONLY valid JSON, no prose, no fences."""

JUDGE_USER = """Decision under review: {field_name} for "{item_key}"

Item:
{item_json}

First model's answer:
{proposed_json}

Independently determine the correct {field_name}, then return JSON:
{{"agree": bool, "judged_value": <your independent value for {field_name}>,
  "reasoning": str, "confidence": 0.0-1.0}}"""


# --- 5. Risk band (LLM decides the band, replacing a hardcoded policy) --------

BAND_TASK = """
TASK: Assign a RISK BAND to each (asset, tool) pair on THIS asset --
low | medium | high | critical -- expressing how much a security gate should
worry about that operation here. Decide with security judgement for this domain,
NOT a fixed numeric threshold.
Principles:
  - critical: irreversible destruction, or mass exfiltration, of a crown-jewel
    asset (regulated / PII / secrets / financial). The ops you hard-gate. Rare.
  - high: serious but recoverable; an irreversible op on restricted data; or a
    broad read of sensitive data (mass leak). A bulk read / enumeration / listing
    / search / tree-walk over a SENSITIVE scope (a directory or table holding
    restricted, PII, secret or financial data) is HIGH -- one call leaks the whole
    scope -- even though a single-item read of the same data is only medium.
  - medium: a narrow read of a crown-jewel (one record leaks); a moderate change
    to internal data; an enumeration/listing over an ORDINARY scope.
  - low: routine operations on ordinary / public data. A read can leak but never
    destroys, so reads are never critical. Do NOT default an enumeration over a
    sensitive scope to low just because listing is "read-only" -- judge it by what
    the whole scope exposes (see blast radius).
You are given each tool's impact (1 read, 2 recoverable, 3 destructive), its
blast radius into this asset (0-4) and a raw score -- use them as evidence, but
the band is your judgement, not a formula."""

BAND_USER = """Asset (with its sensitivity 1-5):
{asset_json}

Tools acting on this asset (each with impact, blast, raw_score):
{tools_json}

Return JSON:
{{"asset_id": str, "bands": {{"<tool_name>": "low|medium|high|critical"}},
  "reasoning": str}}"""
