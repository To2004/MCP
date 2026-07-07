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
is ambiguous, pick the higher tier and lower confidence.
SELF-CHECK before you answer: re-scan the tool's ENTIRE capability surface --
every parameter, side effect, and external reach -- and take the max tier any one
of them implies. A destructive capability hidden behind an innocuous name or a
read-only-looking annotation is the single most common miss; do not under-score
it. When unsure between two tiers, the higher tier is the safer error here."""

TOOL_IMPACT_USER = """Tool registry entry:
{tool_json}

Return JSON:
{{"tool_name": str, "tool_impact": 1|2|3, "irreversible": bool,
  "worst_case": str, "trigger_capability": str, "confidence": 0.0-1.0,
  "reasoning": str}}"""


# --- 2. Asset Sensitivity ----------------------------------------------------

ASSET_TASK = """
TASK: Assign ASSET SENSITIVITY (1-5) -- criticality if this asset class is
exposed, corrupted, or destroyed. Use these ANCHORS, judged by what the asset
CONTAINS (its name/path/columns are evidence of content):
  5 = crown jewel: secrets/keys/credentials, regulated records (PHI, card/PAN
      data), money-moving or legally-privileged data. Exposure alone is
      reportable or directly exploitable.
  4 = restricted business data: production/customer data, personnel/payroll,
      financials, proprietary source code, security/audit logs. Serious harm,
      but not immediately exploitable like a live credential.
  3 = internal working data: project docs, schemas, internal reports -- meant to
      stay inside the org, embarrassing but recoverable if leaked.
  2 = routine/low-value internal: onboarding material, templates, org charts.
  1 = public or ephemeral: published content, README, scratch data.
A CONTAINER inherits the sensitivity of the most sensitive content it plausibly
holds (a directory named secrets/ is 5, not 3). Escalate classes matching the
inferred dangerous_classes. If the org supplied a priority, treat it as the
primary anchor. When torn between two adjacent tiers and the asset could hold
secrets, PII, financial, or regulated data, choose the HIGHER tier --
under-scoring a crown jewel is the costlier error."""

ASSET_USER = """Asset class entry:
{asset_json}

Return JSON:
{{"asset_id": str, "sensitivity": 1-5, "drivers": [str],
  "confidence": 0.0-1.0, "reasoning": str}}"""


# --- 3. Blast Radius ---------------------------------------------------------

BLAST_TASK = """
TASK: Assign BLAST RADIUS (1-5) for one (tool, asset class) pair -- how far this
tool reaches into this asset when it acts, per the inferred
blast_radius_meaning. Every pair has at least reach 1 -- there is no "N/A" cell:
if a tool only barely relates to an asset, that is still a minimal touch = 1.
  1 = narrow / read-only touch of a SINGLE item (the minimum).
  2 = scoped, recoverable modification of a single item.
  3 = broad modification of several items in one scope.
  4 = full overwrite, OR a read/enumeration that spans MANY items at once.
  5 = clobber/destroy/irrevocable, or fan-out across many instances at once.
BREADTH RULE (do not under-score reads): reach is not only about writing. A tool
that ENUMERATES or reads ACROSS a whole scope at once -- listing a directory,
walking a tree, searching/globbing, reading multiple files, or any SELECT over a
table -- aggregates exposure over every item in that scope. When the asset class
is a CONTAINER/SCOPE (a directory, a whole table, a channel) and the tool lists,
walks, searches, or bulk-reads it, the blast radius is broad (>=4), because one
call exposes everything inside -- even though each individual read is harmless.
BREADTH LIMITS (do not over-score either -- both conditions must hold):
  a) The ASSET must itself be the container being swept. If the asset is a
     SINGLE item (one file, one record), reads of it stay narrow (1) even when
     the tool is bulk-capable -- the fan-out belongs to the container's own cell,
     not to this one.
  b) The tool must actually EXPOSE the contents. A metadata-only operation --
     stat/info on a path, describing a schema, listing allowed roots -- returns
     one record ABOUT the asset (name, size, permissions), not what is inside
     it. That is blast 2 on a container, 1 on a single item, NEVER 4+, no matter
     how sensitive the asset: sensitivity is already priced into the score.
ONE-CALL RULE: blast measures what a SINGLE call reaches. A tool whose input
names ONE item (one path, one id, one file) reaches one item per call -- even
when the asset is a container, that call touches ONE thing inside it (blast 1,
or 2 if it writes). Only a tool that enumerates, walks, searches, or bulk-reads
MANY items in ONE call sweeps the container (>=4). Do not score a container
cell by imagining many repeated calls.
WORKED CONTRAST (apply this pattern): on a secrets/ directory,
  walk/read the tree      = 5  (bulk content sweep of a dangerous scope, one call)
  stat / file info        = 2  (one metadata record, no contents)
  list allowed root names = 2  (names only, no contents)
  read ONE file (by path) = 1  (single item per call -- even though the asset
                                is the directory; the walk cell carries the sweep)
Escalation: if the asset class matches the inferred dangerous_classes AND the
operation already reaches beyond a single item (blast >= 2 before escalation),
raise by 1 (cap 5) versus the same operation on an ordinary asset; say so in
rationale. A narrow single-item touch stays 1 even on a dangerous asset -- the
asset's value lives in sensitivity, not in reach."""

BLAST_USER = """Tool:
{tool_json}

Asset class:
{asset_json}

Return JSON:
{{"tool_name": str, "asset_id": str, "blast_radius": 1-5, "rationale": str,
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


# --- Judge (EVALUATION ONLY) -------------------------------------------------
# The judge does NOT run in a production scan. Its band-level corrections are
# folded into the deterministic band_label() floors and its skepticism into the
# proposer tasks above, so a single pass stands alone. These templates remain for
# the evaluation-only crosscheck (StaticScorer.judge()) that measures how often an
# independent reviewer agrees with the base model.

JUDGE_SYSTEM = """You are an independent security reviewer verifying another
model's misuse-scoring decision. You are given the same inferred domain profile,
the SAME SCORING RULES the first model was instructed to follow, the same item,
and the first model's answer. Apply the scoring rules yourself, INDEPENDENTLY,
to decide what the value should be -- THEN compare. You are checking whether the
rules were applied correctly, not substituting different rules of your own.

INFERRED DOMAIN PROFILE:
{domain_profile}

SCORING RULES FOR THIS DECISION:
{scoring_rules}

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

# NOTE: The former LLM band stage (BAND_TASK/BAND_USER) was removed. Bands are now
# assigned solely by the deterministic band_label() in pipeline.py -- reproducible
# and immune to the critical-band inflation the LLM band stage produced.
