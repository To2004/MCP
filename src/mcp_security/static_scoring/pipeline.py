"""The static (design-time) misuse-scoring pipeline.

Given a :class:`~mcp_security.static_scoring.registry.ServerRegistry`, this
module produces the static risk table — the same JSON shape as
``reports/samples/payment_static_table.json``: an inferred domain profile, the
three scoring primitives (tool impact, asset sensitivity, per-pair blast
radius), the multiplied ``cells`` matrix with risk bands, per-app baselines, and
a judge cross-check summary.

Each stage prefers the local LLM (Qwen2.5 via Ollama, using the templates in
:mod:`.prompts`) and degrades to the deterministic heuristics in
:mod:`.fallback` whenever the model is unreachable or returns something
unusable. A table built with any fallback in play is flagged
``needs_human_review`` so it is never mistaken for a fully model-reviewed one.

Risk formula (matches the payment reference table)::

    score = asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass

from mcp_security.llm.ollama_client import query_ollama

from . import fallback, prompts, server_profiles, static_impact
from .registry import ServerRegistry, ToolSpec

logger = logging.getLogger(__name__)

FORMULA = "asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact"
# five_level_v2_desc drops the sensitivity primitive entirely: how much an asset
# matters comes from the organization's written description instead of a separately
# scored 1-5 number, so the cell is the two tool-side factors alone.
FORMULA_NO_SENS = "blast_radius * likelihood(1.0) * tool_impact"
LIKELIHOOD = 1.0
BANDS = ("low", "medium", "high", "critical")

# Max tool-impact value per experiment mode -> score_max = 5(sens) * 5(blast) * this.
# hybrid uses the geometric-mean formula (score = sens*5*sqrt(blast*impact)), whose
# max is 5*5*sqrt(5*5) = 125 = 25*5, so the same 25*_IMPACT_MAX rule gives 125.
_IMPACT_MAX = {
    "baseline": 3,
    "five_level": 5,
    "five_level_v2": 5,
    "five_level_v2_na": 5,
    "cia": 6,
    "hybrid": 5,
    "hybrid_na": 5,
    "five_level_v2_ctx": 5,
    "five_level_v2_desc": 5,
    "five_level_v2_ult": 5,
    "five_level_v2_ult_tools": 5,
    "five_level_v2_ult_leanimp": 5,
    "five_level_v2_ult_struct": 5,
    "five_level_v2_ult_imponly": 5,
    "five_level_v2_ult_nodom": 5,
    "five_level_v2_v4": 5,
    "five_level_v2_v4_static": 5,
    "five_level_v2_v5": 5,
    "five_level_v2_v5r": 5,
    "five_level_v2_v5r_noflags": 5,
    "five_level_v2_v5r_keyflags": 5,
    "five_level_v2_v5r_selfassess": 5,
    "five_level_v2_v5r_twostage": 5,
    "five_level_v2_v5r_lowfloor": 5,
    "five_level_v2_v5r_scope": 5,
    "five_level_v2_v5r_naregister": 5,
    "five_level_v2_v5r_naprompt": 5,
    "five_level_v2_v5r_nona": 5,
    "five_level_v2_v5r_nacombo": 5,
    "five_level_v2_v5r_sensiso": 5,
    "five_level_v2_v5r_sensnist": 5,
    "five_level_v2_v5r_senscis": 5,
    "five_level_v2_v7_iso": 5,
    "five_level_v2_v7_nist": 5,
    "five_level_v2_v7_cis": 5,
}
# Ablation variants of the ult mode — same profile-sensitivity machinery, one
# prompt-context lever each:
#   _tools   -> the FULL tool registry rides along in every impact & blast prompt
#               (base ult shows it only to domain inference).
#   _leanimp -> the org description is withheld from the tool-impact stage
#               (impact should be pure action-type; the description stays in
#               domain inference, blast, and baselines).
#   _struct  -> the model sees a STRUCTURED-ONLY profile view (fact line +
#               per-asset table + CIA ordering, no prose); sensitivity parsing
#               is unchanged since the table survives the transformation.
_ULT_VARIANT_OPTIONS: dict[str, dict] = {
    "five_level_v2_ult": {},
    "five_level_v2_ult_tools": {"tools_in_prompts": True},
    "five_level_v2_ult_leanimp": {"desc_in_impact": False},
    "five_level_v2_ult_struct": {"desc_scheme": "struct"},
    # v3 prompt-importance arms:
    #   _imponly -> the IMPACT stage sees the profile PROSE only (no asset
    #               table): action-type needs the org context, not the asset
    #               inventory. Blast keeps the full profile.
    #   _nodom   -> NO inferred-domain stage at all: the org description alone
    #               fronts every prompt (the profile spec is meant to carry
    #               content_unit, hubs and irreversible actions itself).
    "five_level_v2_ult_imponly": {"impact_desc_scheme": "prose"},
    "five_level_v2_ult_nodom": {"no_domain": True},
    # v4: short standards-grounded prompts. Impact sees the TOOL ONLY (no
    # preamble at all); blast sees everything plus the sibling tool/asset lists.
    "five_level_v2_v4": {"v4_prompts": True, "impact_bare": True, "blast_peers": True},
    # v4-static: identical, except tool impact is computed DETERMINISTICALLY from
    # the tool's own declaration (static_impact.py) with no LLM call at all.
    "five_level_v2_v4_static": {
        "v4_prompts": True,
        "impact_bare": True,
        "blast_peers": True,
        "static_impact": True,
    },
    # v5: the policy-grade arm. Same v4 blast (full context + sibling lists) and
    # the same deterministic assembly, but the two ends change:
    #   * sensitivity is DERIVED by the model from the org's classification
    #     policy (classify -> map) instead of read off a per-asset table, so the
    #     organization supplies no numbers at all;
    #   * tool impact is the deterministic ladder FIRST and the v4 impact prompt
    #     only where the ladder cannot tell (static_impact_fallback).
    "five_level_v2_v5": {
        "v4_prompts": True,
        "impact_bare": True,
        "blast_peers": True,
        "static_impact": True,
        "static_impact_fallback": True,
    },
    # v5r: same arm, rewritten prompts and rules. Impact is classified by
    # OPERATION TYPE (read / write / remove) with scoped writes sharing tier 3
    # with content reads; open-world leaves the ladder; annotation hints stop
    # bounding anything. Domain inference drops to three fields and the blast
    # DISCIPLINE block loses the rules that were fitted to single tools.
    "five_level_v2_v5r": {
        "v4_prompts": True,
        "impact_bare": True,
        "blast_peers": True,
        "static_impact": True,
        "static_impact_fallback": True,
        "v5r_prompts": True,
        # The behavioral baseline is a runtime primitive: it describes what normal
        # use looks like, which only means something once there is a call to
        # compare against. Nothing in the static score consumes it, so it moves
        # wholesale to the dynamic stage.
        "no_baselines": True,
        # Which register flags reach the model. "all" is v5r as first run.
        "asset_flags": "all",
    },
    # The flag ablation. Identical to v5r except for what the register is allowed
    # to assert. A flag is the organization stating a CONCLUSION (`hub` = reaching
    # this reaches other systems) where the rest of the register states facts —
    # and that conclusion is the blast question, so a flag lets the org answer what
    # blast is meant to derive. An org may also simply not supply one.
    #
    #   _noflags  -> no flag reaches the model; tier 5 must be argued from the
    #                asset's own description, and the route is free text.
    #   _keyflags -> only the three flags that ever changed a score survive
    #                (`hub`, `population`, `self-sufficient`).
    "five_level_v2_v5r_noflags": {
        "v4_prompts": True,
        "impact_bare": True,
        "blast_peers": True,
        "static_impact": True,
        "static_impact_fallback": True,
        "v5r_prompts": True,
        "no_baselines": True,
        "asset_flags": "none",
    },
    "five_level_v2_v5r_keyflags": {
        "v4_prompts": True,
        "impact_bare": True,
        "blast_peers": True,
        "static_impact": True,
        "static_impact_fallback": True,
        "v5r_prompts": True,
        "no_baselines": True,
        "asset_flags": "key",
    },
    # The synthesis: no flag reaches the model, but the three escape CONCEPTS
    # survive as questions it asks of the asset's description, with the answer
    # quoted back from the organization's own words. The scaffold guides the
    # reasoning; the register still supplies the facts; nobody hands over a
    # conclusion.
    "five_level_v2_v5r_selfassess": {
        "v4_prompts": True,
        "impact_bare": True,
        "blast_peers": True,
        "static_impact": True,
        "static_impact_fallback": True,
        "v5r_prompts": True,
        "no_baselines": True,
        "asset_flags": "none",
        "blast_prompt": "selfassess",
    },
    # selfassess + the model is told a DYNAMIC stage exists, so it scores the
    # structural case and leaves the request-dependent specifics to runtime.
    "five_level_v2_v5r_twostage": {
        "v4_prompts": True,
        "impact_bare": True,
        "blast_peers": True,
        "static_impact": True,
        "static_impact_fallback": True,
        "v5r_prompts": True,
        "no_baselines": True,
        "asset_flags": "none",
        "blast_prompt": "selfassess",
        "two_stage_framing": True,
    },
    # selfassess + every floor lowered a tier, and any floor below 3 removed.
    "five_level_v2_v5r_lowfloor": {
        "v4_prompts": True,
        "impact_bare": True,
        "blast_peers": True,
        "static_impact": True,
        "static_impact_fallback": True,
        "v5r_prompts": True,
        "no_baselines": True,
        "asset_flags": "none",
        "blast_prompt": "selfassess",
        "floors": "low",
    },
    # Blast tiers by ORGANIZATIONAL SCOPE (individual -> group -> several groups
    # -> org-wide -> beyond), Q1-Q4 kept, and NO floors at all.
    "five_level_v2_v5r_scope": {
        "v4_prompts": True, "impact_bare": True, "blast_peers": True,
        "static_impact": True, "static_impact_fallback": True,
        "v5r_prompts": True, "no_baselines": True,
        "asset_flags": "none", "blast_prompt": "scope", "floors": "none",
    },
    # scope + the register DECIDES relevance: no model call for an undeclared
    # pair, no N/A option for a declared one.
    "five_level_v2_v5r_naregister": {
        "v4_prompts": True, "impact_bare": True, "blast_peers": True,
        "static_impact": True, "static_impact_fallback": True,
        "v5r_prompts": True, "no_baselines": True,
        "asset_flags": "none", "blast_prompt": "scope", "floors": "none",
        "relevance": "register",
    },
    # scope + the model is shown what the register says and must justify
    # contradicting it.
    "five_level_v2_v5r_naprompt": {
        "v4_prompts": True, "impact_bare": True, "blast_peers": True,
        "static_impact": True, "static_impact_fallback": True,
        "v5r_prompts": True, "no_baselines": True,
        "asset_flags": "none", "blast_prompt": "scope", "floors": "none",
        "relevance": "prompt",
    },
    # scope + no gate at all: every pair gets 1-5.
    "five_level_v2_v5r_nona": {
        "v4_prompts": True, "impact_bare": True, "blast_peers": True,
        "static_impact": True, "static_impact_fallback": True,
        "v5r_prompts": True, "no_baselines": True,
        "asset_flags": "none", "blast_prompt": "scope", "floors": "none",
        "relevance": "none",
    },
    # The union: the register settles a pair it declares, the model decides where
    # the register is silent, and N/A is named as the costlier error.
    "five_level_v2_v5r_nacombo": {
        "v4_prompts": True, "impact_bare": True, "blast_peers": True,
        "static_impact": True, "static_impact_fallback": True,
        "v5r_prompts": True, "no_baselines": True,
        "asset_flags": "none", "blast_prompt": "scope", "floors": "none",
        "relevance": "combo",
    },
    # nacombo + the sensitivity stage speaks ISO/IEC 27001:2022 A.5.12's own classification language.
    "five_level_v2_v5r_sensiso": {
        "v4_prompts": True, "impact_bare": True, "blast_peers": True,
        "static_impact": True, "static_impact_fallback": True,
        "v5r_prompts": True, "no_baselines": True,
        "asset_flags": "none", "blast_prompt": "scope", "floors": "none",
        "relevance": "combo", "sens_scheme": "iso",
    },
    # nacombo + the sensitivity stage speaks NIST FIPS 199 / SP 800-60's own classification language.
    "five_level_v2_v5r_sensnist": {
        "v4_prompts": True, "impact_bare": True, "blast_peers": True,
        "static_impact": True, "static_impact_fallback": True,
        "v5r_prompts": True, "no_baselines": True,
        "asset_flags": "none", "blast_prompt": "scope", "floors": "none",
        "relevance": "combo", "sens_scheme": "nist",
    },
    # nacombo + the sensitivity stage speaks CIS Controls v8.1 Control 3's own classification language.
    "five_level_v2_v5r_senscis": {
        "v4_prompts": True, "impact_bare": True, "blast_peers": True,
        "static_impact": True, "static_impact_fallback": True,
        "v5r_prompts": True, "no_baselines": True,
        "asset_flags": "none", "blast_prompt": "scope", "floors": "none",
        "relevance": "combo", "sens_scheme": "cis",
    },
    # v7 — the framework-NATIVE arms. Identical to nacombo in every stage except
    # sensitivity, and identical to the v5r sens* arms in configuration. What
    # differs is the DOCUMENT: these read a register the organization wrote in its
    # own framework's shape (--policy-doc), which carries native columns, an
    # authorization column and no flags. So a v7-vs-v5r delta isolates the policy
    # document, and a v7-vs-nacombo delta isolates document plus prompt together.
    "five_level_v2_v7_iso": {
        "v4_prompts": True, "impact_bare": True, "blast_peers": True,
        "static_impact": True, "static_impact_fallback": True,
        "v5r_prompts": True, "no_baselines": True,
        "asset_flags": "none", "blast_prompt": "scope", "floors": "none",
        "relevance": "combo", "sens_scheme": "v7_iso",
    },
    "five_level_v2_v7_nist": {
        "v4_prompts": True, "impact_bare": True, "blast_peers": True,
        "static_impact": True, "static_impact_fallback": True,
        "v5r_prompts": True, "no_baselines": True,
        "asset_flags": "none", "blast_prompt": "scope", "floors": "none",
        "relevance": "combo", "sens_scheme": "v7_nist",
    },
    "five_level_v2_v7_cis": {
        "v4_prompts": True, "impact_bare": True, "blast_peers": True,
        "static_impact": True, "static_impact_fallback": True,
        "v5r_prompts": True, "no_baselines": True,
        "asset_flags": "none", "blast_prompt": "scope", "floors": "none",
        "relevance": "combo", "sens_scheme": "v7_cis",
    },
}
# Modes that use the geometric-mean formula score = sens * 5 * sqrt(blast * impact).
_SQRT_MODES = {"hybrid", "hybrid_na"}
# Modes whose blast stage may mark a (tool, asset) pair N/A (affects_asset=false),
# so the cell is not scored (blast None -> band "na").
_NA_MODES = {
    "hybrid_na",
    "five_level_v2_na",
    "five_level_v2_ctx",
    "five_level_v2_desc",
    *_ULT_VARIANT_OPTIONS,
}
# Modes that do NOT score asset sensitivity: the asset axis stays (blast is still
# per tool x asset), but no sensitivity stage runs and the score is blast * impact.
# These modes REQUIRE the registry to carry an org description -- without it the
# scan would price reach with nothing saying what the assets are worth.
_NO_SENS_MODES = {"five_level_v2_desc"}
# Modes that put the org description in front of every stage.
_DESC_MODES = {"five_level_v2_desc", *_ULT_VARIANT_OPTIONS}
# Modes whose asset sensitivity is DERIVED from the org's written policy: the
# normal LLM sensitivity stage runs, but against a classification policy that
# states adverse impact per class and carries no numbers, so the model classifies
# then maps rather than inventing a severity. These modes still get the ult
# deterministic assembly and the v5 bands.
_POLICY_SENS_MODES = {
    "five_level_v2_v5",
    "five_level_v2_v5r",
    "five_level_v2_v5r_noflags",
    "five_level_v2_v5r_keyflags",
    "five_level_v2_v5r_selfassess",
    "five_level_v2_v5r_twostage",
    "five_level_v2_v5r_lowfloor",
    "five_level_v2_v5r_scope",
    "five_level_v2_v5r_naregister",
    "five_level_v2_v5r_naprompt",
    "five_level_v2_v5r_nona",
    "five_level_v2_v5r_nacombo",
    "five_level_v2_v5r_sensiso",
    "five_level_v2_v5r_sensnist",
    "five_level_v2_v5r_senscis",
    "five_level_v2_v7_iso",
    "five_level_v2_v7_nist",
    "five_level_v2_v7_cis",
}
# The three register flags that ever changed a score. Everything else in the
# vocabulary was written and never read.
KEY_ASSET_FLAGS = frozenset({"hub", "population", "self-sufficient"})
# Modes whose asset sensitivity comes from the org profile's per-asset table
# (parsed from the description) instead of an LLM stage: the number is the
# organization's own, logged and challengeable, and the LLM scores only reach
# and action type.
_PROFILE_SENS_MODES = set(_ULT_VARIANT_OPTIONS) - _POLICY_SENS_MODES
# Modes that run the deterministic assembly passes (bulk twins, alias twins,
# gated blast floor, blast roof) and band on the 0-125 v5 thresholds. Both
# sensitivity provenances qualify — the assembly keys on the NUMBER, not on where
# the number came from.
_ASSEMBLY_MODES = _PROFILE_SENS_MODES | _POLICY_SENS_MODES
# The ult mode's deterministic gated blast floor (the floor-gated experiment
# folded into the scan): a mutating call (impact >= gate) on a sensitive asset
# can never be priced as a pinpoint touch.
ULT_FLOORS = {5: 4, 4: 3}
ULT_GATE_IMPACT_MIN = 4
# v3: the impact-keyed twin of the sensitivity floors, one tier lower (user-set):
# an irreversible tool (impact 5) is never a pinpoint consequence (blast >= 3),
# a write tool (impact 4) never below a narrow slice (blast >= 2) — regardless of
# the asset's sensitivity. The effective floor per cell is the max of both keys.
ULT_IMPACT_FLOORS = {5: 3, 4: 2}
# v5r replaces both of the above with three UNGATED rules, stated by the analyst:
#
#     asset sensitivity 5  ->  blast >= 4
#     asset sensitivity 4  ->  blast >= 3
#     tool impact       5  ->  blast >= 3
#
# The difference from the ult floors is the gate. Theirs only fired on a mutating
# call (impact >= 4), which is why `create-event` (impact 3) on a sensitivity-5
# calendar kept blast 1 and scored 5x1x3 = 15: a pinpoint touch of a Restricted
# asset. Ungating says that reaching a crown-jewel asset at all is never a
# pinpoint consequence, whatever the verb. The impact-4 -> blast 2 rule is gone
# with the gate; only impact 5 keeps a floor of its own.
V5R_FLOORS = {5: 4, 4: 3}
V5R_IMPACT_FLOORS = {5: 3}
V5R_GATE_IMPACT_MIN = 1  # ungated: every scored cell is eligible
# v5r removes the blast ROOF entirely. A roof can only ever under-score, it was
# written to trim over-reads the old prompt produced, and the floors now set the
# lower bound explicitly — so capping on top of them just fights the rubric.
V5R_ROOF: dict = {}
# The lowered-floor arm: every floor drops a tier, and any that lands below 3 is
# removed rather than kept as a weak nudge. Only the crown-jewel rule survives.
V5R_LOW_FLOORS = {5: 3}
V5R_LOW_IMPACT_FLOORS: dict[int, int] = {}
# Sensitivity handed to the deterministic blast fallback when no sensitivity stage
# ran (offline smoke runs only; a strict scan raises before it can be used).
_NEUTRAL_SENSITIVITY = 3
# v5 hand-off threshold between the deterministic impact ladder and the model.
# static_impact.classify() reports 0.35 when NO tier verb matched and it fell
# through to its annotation/default branch — the one case where the rules do not
# know rather than disagree. Anything at or above this had real verb evidence, so
# the rules answer and the model is not called. Raising it hands more tools to
# the LLM; lowering it below 0.35 disables the fallback entirely.
STATIC_IMPACT_MIN_CONFIDENCE = 0.5


class ProfileCoverageError(ValueError):
    """Raised when the org profile's asset table does not cover every registry asset.

    Profile-sensitivity modes take each asset's value from the organization's own
    table; an uncovered asset would have to be guessed, so the scan refuses to run
    and names exactly what is missing.
    """


class LLMUnavailableError(RuntimeError):
    """Raised in strict (LLM-only) mode when the model cannot score a record.

    Strict mode is used by the live scanner, which must never substitute a
    hardcoded heuristic for the model's judgement: if the model is unreachable
    or returns something unusable, the scan fails loudly instead of fabricating.
    """


# Score cutoffs on the multiplied score (max scale 5*4*3 = 60).
BAND_THRESHOLDS = {"medium": 8, "high": 24}
# A decision below this confidence is counted as needing human review.
REVIEW_CONFIDENCE = 0.7


def band_label(sensitivity: int, blast: int, impact: int) -> str:
    """Deterministic operational band for one (asset, tool) cell.

    A pure function of the three primitives (impact 1-3, sensitivity 1-5, blast
    1-5) — so the band is fully reproducible and a straight function of
    the score. The score is an *upper bound* (likelihood pinned to 1.0), so we do
    not band on the raw number alone; instead explicit **security floors** encode
    the judgement an independent reviewer used to add on top:

    * **critical** — an *irreversible* action (impact 3) that destroys
      RESTRICTED-or-worse data (sensitivity ≥ 4) *at scale* (blast ≥ 4): mass,
      unrecoverable loss.
    * **high** — any irreversible op on sensitive data (impact 3 ∧ sensitivity ≥
      3), a write to a crown jewel (impact 2 ∧ sensitivity 5), a broad/mass read
      of restricted data (impact 1 ∧ sensitivity ≥ 4 ∧ blast ≥ 4 = exfiltration),
      or a high raw score.
    * **medium — floors:** ANY irreversible op is at least medium (destroying even
      trivial data is still a state change), and reading restricted-or-worse data
      is at least medium (confidentiality), plus any middling score.
    * **low** — routine reads / narrow reach of ordinary data.

    These floors were derived by measuring where an LLM reviewer systematically
    disagreed with the old formula (it up-rated irreversible ops on trivial data,
    reads of restricted data, and mass destruction of restricted data) — folding
    that judgement into the deterministic rule instead of a per-scan override.
    """
    score = sensitivity * blast * impact
    # critical — irreversible mass destruction of restricted-or-worse data.
    if impact == 3 and sensitivity >= 4 and blast >= 4:
        return "critical"
    # high — irreversible op on sensitive data, a crown-jewel write, a broad read
    # of restricted data (mass exfiltration), or a high raw score.
    if (
        (impact == 3 and sensitivity >= 3)
        or (impact == 2 and sensitivity == 5)
        or (impact == 1 and sensitivity >= 4 and blast >= 4)
        or score >= BAND_THRESHOLDS["high"]
    ):
        return "high"
    # medium — irreversibility floor (any impact-3 op), confidentiality floor
    # (any read of restricted+ data), or a middling score.
    if impact == 3 or (impact == 1 and sensitivity >= 4) or score >= BAND_THRESHOLDS["medium"]:
        return "medium"
    return "low"


# Score cutoffs for the sensitivity-free scale (max 5*5 = 25). Kept at the same
# fractions of the maximum as BAND_THRESHOLDS on the 60-point scale (13% / 40%), so
# a desc-mode band means the same share of the worst case as a normal-mode one.
BAND_THRESHOLDS_NO_SENS = {"medium": 4, "high": 10}


def band_label_no_sens(blast: int, impact: int) -> str:
    """Operational band for one cell when sensitivity is not scored.

    The sensitivity-based floors of :func:`band_label` cannot apply here, so the
    same judgements are re-expressed against the two primitives that remain. Impact
    is the five_level_v2 action ladder (4 = write/modify, 5 = delete/destroy) and
    blast is coverage (4 = the whole asset, 5 = consequences escape it):

    * **critical** — destruction (impact 5) whose reach is total or systemic
      (blast >= 4): mass, unrecoverable loss.
    * **high** — any destructive op (impact 5, even pinpoint — irreversibility is
      its own floor), a write whose reach is total or systemic (impact 4 ∧ blast
      >= 4), a systemic-reach call of any kind (blast 5 — the consequences left
      the asset), or a high raw score.
    * **medium** — any state change (impact >= 4), any total-coverage call
      (blast >= 4, which is mass disclosure when the op only reads), or a
      middling score.
    * **low** — narrow reads and metadata.
    """
    score = blast * impact
    if impact == 5 and blast >= 4:
        return "critical"
    if (
        impact == 5
        or (impact == 4 and blast >= 4)
        or blast == 5
        or score >= BAND_THRESHOLDS_NO_SENS["high"]
    ):
        return "high"
    if impact >= 4 or blast >= 4 or score >= BAND_THRESHOLDS_NO_SENS["medium"]:
        return "medium"
    return "low"


# Score cutoffs for the ult scale (max sens*blast*impact = 5*5*5 = 125). The band
# is a PURE function of the score — no categorical overrides — so a cell's band is
# always explainable from its number alone (score/125). Cutoffs are round fractions
# of the maximum: medium >= ~13%, high >= 40%, critical >= 80%.
BAND_THRESHOLDS_V5 = {"medium": 17, "high": 50, "critical": 100}


def band_label_v5(sensitivity: int, blast: int, impact: int) -> str:
    """Operational band for the 5-level ladder — a PURE function of the score.

    The score is ``sensitivity * blast * impact`` on the 0-125 scale, and the
    band is a straight threshold on that number, nothing else: severity enters
    the SCORE (via the primitives and the deterministic blast floors), never the
    band. This keeps a band fully explainable from its own cell — 45/125 is
    ``medium`` because 45 < 50, full stop, not because of any per-case rule.

    * **critical** — score >= 100 (80% of the maximum).
    * **high**     — 50 <= score < 100.
    * **medium**   — 17 <= score < 50.
    * **low**      — score < 17.
    """
    score = sensitivity * blast * impact
    if score >= BAND_THRESHOLDS_V5["critical"]:
        return "critical"
    if score >= BAND_THRESHOLDS_V5["high"]:
        return "high"
    if score >= BAND_THRESHOLDS_V5["medium"]:
        return "medium"
    return "low"


# One alias declaration: "DEPRECATED: Use read_text_file instead." in a tool's
# description marks it as a twin of the named canonical tool.
_ALIAS_RE = re.compile(r"DEPRECATED:?\s*Use\s+`?([A-Za-z0-9_\-]+)`?")


def alias_twin_map(tools) -> dict[str, str]:
    """``{deprecated_tool: canonical_tool}`` for tools whose description names a twin.

    Only pairs whose canonical tool actually exists in the registry are kept —
    a dangling DEPRECATED pointer is not an alias, just prose.
    """
    names = {t.name for t in tools}
    twins: dict[str, str] = {}
    for tool in tools:
        match = _ALIAS_RE.search(tool.description or "")
        if match and match.group(1) in names and match.group(1) != tool.name:
            twins[tool.name] = match.group(1)
    return twins


def apply_alias_twins(
    blast: dict[str, int | None], twins: dict[str, str], asset_ids
) -> tuple[dict[str, int | None], list[dict]]:
    """Give both members of each alias pair the max blast per asset.

    Closes the alias-arbitrage hole (a deprecated `read_file` priced below its
    canonical `read_text_file` for the identical operation). When one twin is
    N/A and the other scored, the scored value propagates to both — an N/A-vs-
    scored split on the same operation IS the arbitrage. Both-N/A stays N/A.
    Returns ``(new_blast, fixups)``; fixups record only the changed cells.
    """
    new_blast = dict(blast)
    fixups: list[dict] = []
    for deprecated, canonical in twins.items():
        for asset in asset_ids:
            values = [new_blast.get(f"{name}|{asset}") for name in (deprecated, canonical)]
            scored = [v for v in values if v is not None]
            if not scored:
                continue
            best = max(scored)
            for name, old in zip((deprecated, canonical), values):
                if old != best:
                    new_blast[f"{name}|{asset}"] = best
                    fixups.append(
                        {
                            "tool": name,
                            "asset": asset,
                            "twin": canonical if name == deprecated else deprecated,
                            "from": old,
                            "to": best,
                        }
                    )
    return new_blast, fixups


def apply_gated_floor(
    blast: dict[str, int | None],
    sensitivity: dict[str, int],
    impacts: dict[str, int],
    *,
    floors: dict[int, int],
    gate_impact_min: int,
    impact_floors: dict[int, int] | None = None,
) -> tuple[dict[str, int | None], int]:
    """Raise mutating cells to the sensitivity- and impact-keyed blast floors.

    The floor-gated experiment folded into assembly: cells with tool impact >=
    ``gate_impact_min`` get ``max(blast, sens_floor, impact_floor)`` where the
    sensitivity floor comes from ``floors[asset_sensitivity]`` and (v3) the
    impact floor from ``impact_floors[tool_impact]`` — the symmetric twin, one
    tier lower, so destruction is never pinpoint and a write is never below a
    narrow slice regardless of the asset. Never lowers, never touches N/A.
    Returns ``(new_blast, raised_count)``.
    """
    impact_floors = impact_floors or {}
    new_blast: dict[str, int | None] = dict(blast)
    raised = 0
    for key, value in blast.items():
        if value is None:
            continue
        tool, asset = key.split("|", 1)
        if impacts[tool] < gate_impact_min:
            continue
        floor = max(floors.get(sensitivity[asset], 1), impact_floors.get(impacts[tool], 1))
        if value < floor:
            new_blast[key] = floor
            raised += 1
    return new_blast, raised


# The rubric's tier-5 escape routes (5b hub-cascade, 5c complete-population) are
# only available to assets carrying one of these flags; a read of any OTHER asset
# reaches at most tier 4 (full coverage), never 5.
ULT_ESCAPE_FLAGS = frozenset({"hub", "population", "self-sufficient"})
# Default roof config (mirror of the floors, but CAPPING). Deliberately narrow —
# a roof under-scores if it is wrong, so it only trims where the rubric already
# forbids the higher tier:
#   read_cap 4  -> an impact<=3 op (read/metadata/liveness) on an asset with NO
#                  escape flag cannot systemically escape, so blast <= 4.
#   sens_caps   -> a public/ephemeral asset (sens 1) cannot host an escape route
#                  either, so its reads cap at 4 as well.
# CRUCIALLY every roof applies ONLY to impact <= 3 cells: a write or delete
# (impact 4-5) is never capped, so a roof can never under-score a mutation.
ULT_ROOF = {"read_cap": 4, "sens_caps": {1: 4}, "combined_cap": None}


def apply_blast_roof(
    blast: dict[str, int | None],
    sensitivity: dict[str, int],
    impacts: dict[str, int],
    asset_flags: dict[str, tuple[str, ...]],
    *,
    read_cap: int | None = None,
    sens_caps: dict[int, int] | None = None,
    combined_cap: tuple[int, int, int] | None = None,
    max_capped_impact: int = 3,
) -> tuple[dict[str, int | None], list[dict]]:
    """Cap blast for low-consequence cells — the careful mirror of the floors.

    SAFETY INVARIANT: only ``impact <= max_capped_impact`` (default 3: reads,
    metadata, liveness) cells are ever capped, so a write or delete's reach is
    never reduced — a roof cannot under-score a mutation. Within that band:

    - ``read_cap``: a cell whose asset has NO escape flag (hub / population /
      self-sufficient) caps here (the rubric: a non-escaping read reaches tier 4
      at most). An asset WITH an escape flag is exempt — it can legitimately
      disclose wholesale (5b/5c).
    - ``sens_caps`` ``{sensitivity: max_blast}``: additional cap by asset value.
    - ``combined_cap`` ``(max_sens, max_impact, cap)``: when the asset is at most
      ``max_sens`` AND the tool at most ``max_impact``, blast caps at ``cap``
      (a trivial action on a trivial asset has trivial reach).

    Never raises; never touches N/A; never caps below 1. Returns
    ``(blast, fixups)`` recording only the changed cells.
    """
    sens_caps = sens_caps or {}
    new_blast: dict[str, int | None] = dict(blast)
    fixups: list[dict] = []
    for key, value in blast.items():
        if value is None:
            continue
        tool, asset = key.split("|", 1)
        impact = impacts[tool]
        if impact > max_capped_impact:
            continue  # never cap a mutation
        sens = sensitivity[asset]
        flags = set(asset_flags.get(asset, ()))
        caps: list[int] = []
        if read_cap is not None and not (flags & ULT_ESCAPE_FLAGS):
            caps.append(read_cap)
        if sens in sens_caps:
            caps.append(sens_caps[sens])
        if combined_cap and sens <= combined_cap[0] and impact <= combined_cap[1]:
            caps.append(combined_cap[2])
        if not caps:
            continue
        cap = max(1, min(caps))
        if value > cap:
            new_blast[key] = cap
            fixups.append(
                {"tool": tool, "asset": asset, "field": "blast_roof", "from": value, "to": cap}
            )
    return new_blast, fixups


# Bulk-variant detection: a pluralized twin ("create-event" -> "create-events")
# or a multiple/bulk/batch token whose removal leaves the singular's name
# ("read_multiple_files" -> "read_file").
_BULK_TOKENS = {"multiple", "bulk", "batch"}


def _name_tokens(name: str) -> list[str]:
    return re.split(r"[_\-]", name.lower())


def bulk_twin_map(tools) -> dict[str, str]:
    """``{bulk_tool: singular_tool}`` for bulk/batch variants of a singular twin.

    Two detections, both name-based (documented limitation: array-typed
    parameters without a naming signal are not caught):
    - pluralization: identical tokens except the last, which gains "s"/"es";
    - bulk token: dropping a multiple/bulk/batch token leaves a token list
      equal to the singular's, allowing the last token to de-pluralize
      (read_multiple_files -> read_file).
    """
    by_tokens = {tuple(_name_tokens(t.name)): t.name for t in tools}
    twins: dict[str, str] = {}
    for tool in tools:
        tokens = _name_tokens(tool.name)
        candidates: list[list[str]] = []
        # pluralized last token: create-events -> create-event.
        last = tokens[-1]
        for suffix in ("es", "s"):
            if last.endswith(suffix) and len(last) > len(suffix):
                candidates.append(tokens[:-1] + [last[: -len(suffix)]])
        # bulk token dropped, with and without de-pluralizing the last token.
        if _BULK_TOKENS & set(tokens):
            stripped = [t for t in tokens if t not in _BULK_TOKENS]
            candidates.append(stripped)
            s_last = stripped[-1]
            for suffix in ("es", "s"):
                if s_last.endswith(suffix) and len(s_last) > len(suffix):
                    candidates.append(stripped[:-1] + [s_last[: -len(suffix)]])
        for cand in candidates:
            singular = by_tokens.get(tuple(cand))
            if singular and singular != tool.name:
                twins[tool.name] = singular
                break
    return twins


def apply_bulk_impact(
    impacts: dict[str, int], bulk_twins: dict[str, str]
) -> tuple[dict[str, int], list[dict]]:
    """Enforce impact(bulk) >= impact(singular); returns (impacts, fixups)."""
    new_impacts = dict(impacts)
    fixups: list[dict] = []
    for bulk, singular in bulk_twins.items():
        if new_impacts.get(bulk, 0) < new_impacts.get(singular, 0):
            fixups.append(
                {
                    "tool": bulk,
                    "twin": singular,
                    "field": "impact",
                    "from": new_impacts[bulk],
                    "to": new_impacts[singular],
                }
            )
            new_impacts[bulk] = new_impacts[singular]
    return new_impacts, fixups


def apply_bulk_blast(
    blast: dict[str, int | None], bulk_twins: dict[str, str], asset_ids
) -> tuple[dict[str, int | None], list[dict]]:
    """Enforce blast(bulk) > blast(singular) per asset, post-floor.

    One call touching many items must price above one touching one: the bulk
    twin's blast is raised to the singular's, and when the two are EQUAL
    (typically because a floor lifted the singular) the bulk gets +1 (cap 5).
    N/A cells pass through; returns (blast, fixups).
    """
    new_blast = dict(blast)
    fixups: list[dict] = []
    for bulk, singular in bulk_twins.items():
        for asset in asset_ids:
            b, s = new_blast.get(f"{bulk}|{asset}"), new_blast.get(f"{singular}|{asset}")
            if b is None or s is None:
                continue
            target = min(5, s + 1) if b <= s else b
            if target != b:
                fixups.append(
                    {
                        "tool": bulk,
                        "asset": asset,
                        "twin": singular,
                        "field": "blast",
                        "from": b,
                        "to": target,
                    }
                )
                new_blast[f"{bulk}|{asset}"] = target
    return new_blast, fixups


def _clamp(value: object, low: int, high: int, default: int) -> int:
    """Coerce an LLM value to an int in ``[low, high]``; ``default`` on failure."""
    try:
        return max(low, min(high, int(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


@dataclass
class _Proposal:
    """One primitive decision a proposer made, retained for the judge stage.

    ``field`` is the name the judge echoes back (``tool_impact`` /
    ``sensitivity`` / ``blast_radius``); ``low``/``high`` bound the valid range
    used to clamp the judge's independent value.
    """

    field: str
    key: str
    item_json: dict
    proposed_json: dict
    value: int
    low: int
    high: int
    confidence: float


class StaticScorer:
    """Runs the six-stage pipeline over one server registry.

    Parameters
    ----------
    use_llm:
        When ``True`` (default) each stage calls the local model first and only
        falls back on failure. When ``False`` the pipeline is fully
        deterministic — useful offline and in tests.
    """

    def __init__(
        self,
        registry: ServerRegistry,
        *,
        use_llm: bool = True,
        strict: bool = False,
        impact_mode: str = "baseline",
    ) -> None:
        self.registry = registry
        self.use_llm = use_llm
        # impact_mode selects the tool-impact experiment:
        #   "baseline"   -> current 1-3 damage-ceiling rubric (max score 75)
        #   "five_level" -> 1-5 metadata..destroy-all scale (max score 125)
        #   "cia"        -> base(1-3) + one point per violated C/I/A facet (max 150)
        #   "five_level_v2_desc" -> the org's written profile in front of every
        #                           stage, and NO asset-sensitivity primitive
        if impact_mode not in _IMPACT_MAX:
            raise ValueError(f"unknown impact_mode {impact_mode!r}; choose {list(_IMPACT_MAX)}")
        self.impact_mode = impact_mode
        # Description-driven modes read the organization's own profile of the server.
        # Refuse to run without one: a desc scan that silently fell back to the plain
        # rubric would be indistinguishable from a normal scan in the artifact.
        self.org_description = (registry.description or "").strip()
        if impact_mode in _DESC_MODES and not self.org_description:
            raise ValueError(
                f"impact_mode {impact_mode!r} requires registry.description "
                f"(the organization's written profile of {registry.server!r})"
            )
        # Ult ablation levers (empty dict for every non-ult mode).
        self._ult_opts = _ULT_VARIANT_OPTIONS.get(impact_mode, {})
        if self._ult_opts.get("desc_scheme") == "struct":
            # The model sees only the structured statements; the asset table
            # survives, so sensitivity parsing below is unaffected.
            self.org_description = server_profiles.structured_profile_view(self.org_description)
        # Sensitivity-free modes skip stage 2 entirely; the score is blast * impact.
        # Profile-sens modes also skip stage 2, but a sensitivity primitive still
        # exists — the org's own number, parsed from the description's asset table.
        self.score_sensitivity = (
            impact_mode not in _NO_SENS_MODES and impact_mode not in _PROFILE_SENS_MODES
        )
        self.profile_sensitivity: dict[str, int] = {}
        if impact_mode in _PROFILE_SENS_MODES:
            self.profile_sensitivity = server_profiles.parse_asset_table(self.org_description)
            missing = server_profiles.missing_asset_rows(
                self.profile_sensitivity, [a.asset_id for a in registry.assets]
            )
            if missing:
                raise ProfileCoverageError(
                    f"{registry.server}: {len(missing)} registry asset(s) have no row in "
                    f"the org profile's '| Asset | Sens. | ... |' table: {missing}. Add a "
                    "row for each to the server's section in docs/mcp-tools/"
                    "server-profiles.md and re-run. (Generated homing assets can differ "
                    "between runs — offline --no-llm smoke runs may generate different "
                    "asset names than a GPU scan did.)"
                )
        # Per-tool CIA breakdown (only populated in impact_mode="cia"), for the report.
        self._tool_cia: dict[str, dict] = {}
        # Bands are always the deterministic band_label of the primitives — a pure,
        # reproducible function of the score. The former opt-in LLM band stage and
        # primitive-override judge were removed from the scan path: they made bands
        # non-reproducible ("numbers move on re-scan") and inflated `critical`, while
        # their useful signal is now folded into band_label's floors and the proposer
        # prompts. The judge() method below is retained for evaluation only and is
        # never called during a scan.
        # strict = LLM-only: never fall back to the deterministic heuristics; raise
        # LLMUnavailableError instead. Implies use_llm. Used by the scanner so its
        # scores are always the model's, never a hardcoded table or anchor.
        self.strict = strict
        if strict and not use_llm:
            raise ValueError("strict mode is LLM-only and requires use_llm=True")
        self._used_fallback = False
        self._proposals: list[_Proposal] = []
        # Tier-5 escape route per blast cell (five_level_v2_na): "a"/"b"/"c" or "none".
        self._blast_escape: dict[str, str] = {}
        # Per-cell quoted justification for a tier-5 escape (v5r scope arms).
        self._blast_escape_evidence: dict[str, str] = {}
        # Per-tool understanding profiles (five_level_v2_ctx): built once per tool,
        # injected into every blast decision for that tool.
        self._tool_profiles: dict[str, dict] = {}
        # v4-static / v5: per-tool deterministic impact verdicts (evidence for audit).
        self._static_impacts: dict[str, dict] = {}
        # v5: which scorer decided each tool's impact — "static_ladder" or
        # "llm_fallback". Empty in every mode that has only one impact scorer.
        self._impact_source: dict[str, str] = {}
        self._overrides: dict[tuple[str, str], int] = {}
        self._domain_confidence = 0.6
        self.domain_profile: dict = {}

    # -- LLM plumbing --------------------------------------------------------
    def _ask(self, prompt: str) -> dict | None:
        """Query the model, marking fallback usage when it does not answer."""
        if not self.use_llm:
            return None
        result = query_ollama(prompt)
        if result is None:
            if self.strict:
                raise LLMUnavailableError(
                    "local LLM returned no answer; strict mode forbids a fallback score"
                )
            self._used_fallback = True
        return result

    def _strict_fail(self, stage: str, key: str) -> None:
        """In strict mode, abort rather than accept a fabricated value."""
        if self.strict:
            raise LLMUnavailableError(
                f"local LLM gave no usable {stage} for {key!r}; "
                "strict mode forbids a fallback score"
            )

    def _proposer_prompt(
        self, task: str, user: str, *, with_desc: bool = True, org_desc: str | None = None
    ) -> str:
        """Assemble preamble + task + user message for a proposer stage.

        When the registry carries an organizational description, the desc preamble
        is used so every proposer stage — impact, blast, baselines — sees it.
        ``with_desc=False`` (the _leanimp ablation's impact stage) falls back to
        the plain preamble even when a description exists; ``org_desc`` overrides
        the description text for one stage (the _imponly ablation's prose-only
        impact view). The _nodom ablation uses the description-only preamble —
        no inferred domain profile exists in that arm.
        """
        description = self.org_description if org_desc is None else org_desc
        if description and with_desc and self._ult_opts.get("no_domain"):
            preamble = prompts._PROPOSER_BASE_DESC_ONLY.format(org_description=description)
        elif description and with_desc:
            preamble = prompts._PROPOSER_BASE_DESC.format(
                org_description=description,
                domain_profile=json.dumps(self.domain_profile, indent=2),
            )
        else:
            preamble = prompts._PROPOSER_BASE.format(
                domain_profile=json.dumps(self.domain_profile, indent=2)
            )
        return f"{preamble}\n{task}\n\n{user}"

    def _tools_context_block(self) -> str:
        """The full-registry context block the _tools ablation appends to prompts."""
        return (
            "\n\nFull tool registry of this server (context for RELATIVE judgement "
            "only — score the one tool/pair asked about):\n"
            + json.dumps(self.registry.tools_json_compact())
        )

    # -- Stage 0: domain inference ------------------------------------------
    def infer_domain(self) -> dict:
        # _nodom ablation: no inference stage at all — the org description is the
        # single source of context, so the "domain profile" is an explicit stub
        # (deliberate design, not a fallback: model_reviewed stays true).
        if self._ult_opts.get("no_domain"):
            self.domain_profile = {
                "mcp_kind": self.registry.kind,
                "source": "org_description_only (no inferred-domain stage in this arm)",
            }
            self._domain_confidence = 1.0
            return self.domain_profile
        tools_json = json.dumps(self.registry.tools_json_compact(), indent=2)
        assets_json = json.dumps(self.registry.assets_json(), indent=2)
        # v5r: three fields, tools only. The seven fields removed (hubs, dangerous
        # classes, irreversible actions, asset/blast meanings, worked example)
        # either duplicate what the org's policy states outright or were prose no
        # stage consumed — and every one of them was re-serialized into every
        # later prompt via the preamble.
        if self._ult_opts.get("v5r_prompts"):
            prompt = (
                prompts.DOMAIN_INFERENCE_SYSTEM_V5R
                + "\n\n"
                + prompts.DOMAIN_INFERENCE_USER_V5R.format(tools_json=tools_json)
            )
            result = self._ask(prompt)
            if not isinstance(result, dict) or "mcp_kind" not in result:
                self._strict_fail("domain inference", self.registry.server)
                self._used_fallback = True
                result = fallback.domain_profile(self.registry)
            self.domain_profile = result
            self._domain_confidence = float(result.get("confidence", 0.6))
            return result
        if self.org_description:
            user = prompts.DOMAIN_INFERENCE_USER_DESC.format(
                org_description=self.org_description,
                tools_json=tools_json,
                assets_json=assets_json,
            )
        else:
            user = prompts.DOMAIN_INFERENCE_USER.format(
                tools_json=tools_json, assets_json=assets_json
            )
        prompt = prompts.DOMAIN_INFERENCE_SYSTEM + "\n\n" + user
        result = self._ask(prompt)
        if not isinstance(result, dict) or "mcp_kind" not in result:
            self._strict_fail("domain inference", self.registry.server)
            self._used_fallback = True
            result = fallback.domain_profile(self.registry)
        self.domain_profile = result
        self._domain_confidence = float(result.get("confidence", 0.6))
        return result

    # -- Stage 1: tool impact -----------------------------------------------
    def score_tools(self) -> dict[str, int]:
        impacts: dict[str, int] = {}
        hi = _IMPACT_MAX[self.impact_mode]
        for tool in self.registry.tools:
            fb_impact, fb_irrev, fb_reason = fallback.tool_impact(tool)
            item = tool.to_prompt_json()
            impact, proposed, conf = self._score_one_impact(tool, item, fb_impact, fb_reason)
            impacts[tool.name] = impact
            self._proposals.append(
                _Proposal("tool_impact", tool.name, item, proposed, impact, 1, hi, conf)
            )
        return impacts

    def _score_one_impact(self, tool, item, fb_impact, fb_reason):
        """Score one tool's impact under the active impact_mode; returns (impact, proposed, conf)."""
        if self.impact_mode == "cia":
            return self._score_cia_impact(tool, item, fb_impact, fb_reason)
        if self._ult_opts.get("static_impact"):
            # v4-static / v5: deterministic ladder from the tool's own declaration.
            verdict = (
                static_impact.classify_by_operation(tool)
                if self._ult_opts.get("v5r_prompts")
                else static_impact.classify(tool)
            )
            record = {
                "tool_impact": verdict.tool_impact,
                "reasoning": verdict.reasoning,
                "evidence": verdict.evidence,
                "is_bulk": verdict.is_bulk,
                "confidence": verdict.confidence,
            }
            # v5: the ladder abstains when no tier verb fired at all. Record what
            # it would have said (so the hand-off is auditable) and let the v4
            # impact prompt below decide instead.
            abstains = (
                self._ult_opts.get("static_impact_fallback", False)
                and verdict.confidence < STATIC_IMPACT_MIN_CONFIDENCE
            )
            if not abstains:
                self._static_impacts[tool.name] = {**record, "source": "static_ladder"}
                self._impact_source[tool.name] = "static_ladder"
                return (
                    verdict.tool_impact,
                    {
                        "tool_name": tool.name,
                        "reasoning": verdict.reasoning,
                        "tool_impact": verdict.tool_impact,
                        "source": "static_ladder",
                    },
                    1.0,
                )
            self._static_impacts[tool.name] = {
                **record,
                "source": "llm_fallback",
                "abstained": True,
                "abstain_reason": (
                    f"static confidence {verdict.confidence} < {STATIC_IMPACT_MIN_CONFIDENCE}: "
                    "no tier verb matched, so the ladder would have used its default"
                ),
                "static_would_have_said": verdict.tool_impact,
            }
            self._impact_source[tool.name] = "llm_fallback"
        if self._ult_opts.get("v4_prompts"):
            # v4/v5r: the tool JSON alone — no preamble, no profile, no domain.
            # v5r carries its own ladder (operation type; scoped write shares
            # tier 3) and its own return schema is identical, so only the task
            # text differs.
            if self._ult_opts.get("v5r_prompts"):
                template = (
                    prompts.TOOL_IMPACT_TASK_V5R_TWOSTAGE
                    if self._ult_opts.get("two_stage_framing")
                    else prompts.TOOL_IMPACT_TASK_V5R
                )
                prompt = template.format(tool_json=json.dumps(item))
            else:
                prompt = (
                    prompts.TOOL_IMPACT_TASK_V4
                    + "\n\n"
                    + prompts.TOOL_IMPACT_USER_V4.format(tool_json=json.dumps(item))
                )
            result = self._ask(prompt)
            if isinstance(result, dict) and "tool_impact" in result:
                impact = _clamp(result["tool_impact"], 1, 5, fb_impact)
                if tool.name in self._static_impacts:  # v5 hand-off: log what the model said
                    self._static_impacts[tool.name]["tool_impact"] = impact
                    self._static_impacts[tool.name]["llm_reasoning"] = result.get("reasoning", "")
                return impact, result, float(result.get("confidence", 0.7))
            self._strict_fail("tool_impact", tool.name)
            self._used_fallback = True
            return fb_impact, _fallback_proposed(fb_impact, fb_reason, 0.6), 0.6
        if self.impact_mode == "five_level":
            task, user, hi = prompts.TOOL_IMPACT_TASK_5LEVEL, prompts.TOOL_IMPACT_USER_5LEVEL, 5
        elif self.impact_mode in _PROFILE_SENS_MODES:
            # v3: the 5-level ladder + the bulk-vs-singular border rule.
            task, user, hi = prompts.TOOL_IMPACT_TASK_5LEVEL_V3, prompts.TOOL_IMPACT_USER_5LEVEL, 5
        elif self.impact_mode in (
            "five_level_v2",
            "five_level_v2_na",
            "five_level_v2_ctx",
            "five_level_v2_desc",
        ):
            task, user, hi = prompts.TOOL_IMPACT_TASK_5LEVEL_V2, prompts.TOOL_IMPACT_USER_5LEVEL, 5
        elif self.impact_mode in ("hybrid", "hybrid_na"):
            task, user, hi = prompts.TOOL_IMPACT_TASK_HYBRID, prompts.TOOL_IMPACT_USER_HYBRID, 5
        else:
            task, user, hi = prompts.TOOL_IMPACT_TASK, prompts.TOOL_IMPACT_USER, 3
        user_msg = user.format(tool_json=json.dumps(item))
        if self._ult_opts.get("tools_in_prompts"):
            user_msg += self._tools_context_block()
        # _imponly: the impact stage sees the profile's prose only — the asset
        # table is inventory, not action-type context.
        impact_desc = (
            server_profiles.prose_profile_view(self.org_description)
            if self._ult_opts.get("impact_desc_scheme") == "prose"
            else None
        )
        result = self._ask(
            self._proposer_prompt(
                task,
                user_msg,
                with_desc=self._ult_opts.get("desc_in_impact", True),
                org_desc=impact_desc,
            )
        )
        if isinstance(result, dict) and "tool_impact" in result:
            impact = _clamp(result["tool_impact"], 1, hi, fb_impact)
            return impact, result, float(result.get("confidence", 0.7))
        if self.strict:
            self._strict_fail("tool_impact", tool.name)  # raises; never fabricates
        self._used_fallback = True
        conf = 0.85 if _has_annotation(tool) else 0.6
        return fb_impact, _fallback_proposed(fb_impact, fb_reason, conf), conf

    def _score_cia_impact(self, tool, item, fb_impact, fb_reason):
        """CIA experiment: base = the UNCHANGED baseline impact call; CIA facets = a
        SEPARATE call. Final impact = base + one point per violated C/I/A objective."""
        item_json = json.dumps(item)
        base_res = self._ask(
            self._proposer_prompt(
                prompts.TOOL_IMPACT_TASK, prompts.TOOL_IMPACT_USER.format(tool_json=item_json)
            )
        )
        flags_res = self._ask(
            self._proposer_prompt(
                prompts.CIA_FLAGS_TASK, prompts.CIA_FLAGS_USER.format(tool_json=item_json)
            )
        )
        have_base = isinstance(base_res, dict) and "tool_impact" in base_res
        have_flags = isinstance(flags_res, dict) and "violates_confidentiality" in flags_res
        if have_base and have_flags:
            base = _clamp(base_res["tool_impact"], 1, 3, fb_impact)
            c = bool(flags_res.get("violates_confidentiality"))
            i = bool(flags_res.get("violates_integrity"))
            a = bool(flags_res.get("violates_availability"))
            impact = base + c + i + a
            self._tool_cia[tool.name] = {"base": base, "C": c, "I": i, "A": a, "impact": impact}
            return impact, base_res, float(base_res.get("confidence", 0.7))
        if self.strict:
            self._strict_fail("tool_impact/cia", tool.name)  # raises; never fabricates
        self._used_fallback = True
        conf = 0.85 if _has_annotation(tool) else 0.6
        self._tool_cia[tool.name] = {
            "base": fb_impact,
            "C": False,
            "I": False,
            "A": False,
            "impact": fb_impact,
        }
        return fb_impact, _fallback_proposed(fb_impact, fb_reason, conf), conf

    # -- Stage 2: asset sensitivity -----------------------------------------
    def score_assets(self) -> dict[str, int]:
        # With a written org policy/profile in the registry, sensitivity is a
        # CLASSIFY-then-map decision against that document (the policy scheme of
        # docs/standards/mcp-policy-spec.md) rather than a judgement from the
        # generic anchors alone. No shipped mode runs this stage without a
        # description except the plain ones, so the branch is the whole switch.
        task = prompts.ASSET_TASK_POLICY if self.org_description else prompts.ASSET_TASK
        if self.org_description and self._ult_opts.get("v5r_prompts"):
            scheme = self._ult_opts.get("sens_scheme")
            if scheme:
                # The organization's classification vocabulary, spoken back to it.
                task = {
                    "iso": prompts.ASSET_TASK_POLICY_ISO,
                    "nist": prompts.ASSET_TASK_POLICY_NIST,
                    "cis": prompts.ASSET_TASK_POLICY_CIS,
                    # v7: the same standard, but read against a register written
                    # in that standard's own shape.
                    "v7_iso": prompts.ASSET_TASK_POLICY_V7_ISO,
                    "v7_nist": prompts.ASSET_TASK_POLICY_V7_NIST,
                    "v7_cis": prompts.ASSET_TASK_POLICY_V7_CIS,
                }[scheme]
            elif self._ult_opts.get("two_stage_framing"):
                task = prompts.ASSET_TASK_POLICY_V5R_TWOSTAGE
            else:
                task = prompts.ASSET_TASK_POLICY_V5R
        user = prompts.ASSET_USER_POLICY if self.org_description else prompts.ASSET_USER
        sens: dict[str, int] = {}
        for asset in self.registry.assets:
            fb_sens, fb_drivers, fb_reason = fallback.asset_sensitivity(asset)
            item = asset.to_prompt_json()
            result = self._ask(
                self._proposer_prompt(task, user.format(asset_json=json.dumps(item)))
            )
            if isinstance(result, dict) and "sensitivity" in result:
                value = _clamp(result["sensitivity"], 1, 5, fb_sens)
                proposed, conf = result, float(result.get("confidence", 0.7))
            elif self.strict:
                self._strict_fail("sensitivity", asset.asset_id)  # raises; never fabricates
            else:
                self._used_fallback = True
                value = fb_sens
                conf = 0.9 if fb_drivers else 0.5
                proposed = _fallback_proposed(value, fb_reason, conf)
            sens[asset.asset_id] = value
            self._proposals.append(
                _Proposal("sensitivity", asset.asset_id, item, proposed, value, 1, 5, conf)
            )
        return sens

    # -- Stage 2.5: per-tool understanding (five_level_v2_ctx only) ----------
    def profile_tools(self) -> dict[str, dict]:
        """Build an understanding profile per tool (role, reach, why it matters).

        Runs once per tool; the profile is injected into every blast decision for
        that tool so reach is judged with the tool's meaning in view. In strict
        mode a missing profile aborts (a profile-less blast would silently degrade
        the experiment back to the plain rubric).
        """
        tools_json = json.dumps(self.registry.tools_json_compact())
        for tool in self.registry.tools:
            result = self._ask(
                self._proposer_prompt(
                    prompts.TOOL_CONTEXT_TASK,
                    prompts.TOOL_CONTEXT_USER.format(
                        tool_json=json.dumps(tool.to_prompt_json()), tools_json=tools_json
                    ),
                )
            )
            if isinstance(result, dict) and "single_call_reach" in result:
                self._tool_profiles[tool.name] = result
            else:
                self._strict_fail("tool_profile", tool.name)
                self._used_fallback = True
                self._tool_profiles[tool.name] = {}
        return self._tool_profiles

    # -- Stage 3: blast radius (per tool×asset pair) ------------------------
    def score_blast(
        self, sensitivity: dict[str, int] | None, impacts: dict[str, int] | None = None
    ) -> dict[str, int | None]:
        # hybrid/hybrid_na redefine blast as "reach of consequences". hybrid_na also
        # lets the model mark a pair N/A (affects_asset=false) -> value is None.
        if self.impact_mode == "hybrid_na":
            blast_task, blast_user = prompts.BLAST_TASK_CONSEQUENCES_NA, prompts.BLAST_USER_NA
        elif self.impact_mode == "five_level_v2_desc":
            # Same coverage + N/A rubric, plus the note that no sensitivity factor
            # exists in this run and value comes from the org description instead.
            blast_task, blast_user = prompts.BLAST_TASK_NA_DESC, prompts.BLAST_USER_NA
        elif self._ult_opts.get("v4_prompts"):
            # v4/v5: CVSS vulnerable-vs-subsequent rubric; peers ride in the user
            # msg. v5 names the policy's asset register as the escape-sanctioning
            # artifact, since it has no per-asset sensitivity table to point at.
            if self._ult_opts.get("v5r_prompts"):
                # v5r states the floors in the prompt AND enforces them in
                # assembly, so the model's own number already respects them.
                # With no flags there is no closed route list, so tier 5 has to be
                # argued from the register's description and named in free text.
                if self._ult_opts.get("blast_prompt") == "scope":
                    relevance = self._ult_opts.get("relevance")
                    blast_user = prompts.BLAST_USER_V5R_SCOPE
                    if relevance == "register":
                        blast_task = prompts.BLAST_TASK_V5R_SCOPE_NAREGISTER
                    elif relevance == "prompt":
                        blast_task = prompts.BLAST_TASK_V5R_SCOPE_NAPROMPT
                        blast_user = prompts.BLAST_USER_V5R_SCOPE_NAPROMPT
                    elif relevance == "none":
                        blast_task = prompts.BLAST_TASK_V5R_SCOPE_NONA
                    elif relevance == "combo":
                        blast_task = prompts.BLAST_TASK_V5R_SCOPE_NACOMBO
                        blast_user = prompts.BLAST_USER_V5R_SCOPE_NACOMBO
                    else:
                        blast_task = prompts.BLAST_TASK_V5R_SCOPE
                elif self._ult_opts.get("blast_prompt") == "selfassess":
                    blast_user = prompts.BLAST_USER_V5R_SELFASSESS
                    if self._ult_opts.get("two_stage_framing"):
                        blast_task = prompts.BLAST_TASK_V5R_SELFASSESS_TWOSTAGE
                    elif self._ult_opts.get("floors") == "low":
                        blast_task = prompts.BLAST_TASK_V5R_SELFASSESS_LOWFLOOR
                    else:
                        blast_task = prompts.BLAST_TASK_V5R_SELFASSESS_FLOORED
                elif self._ult_opts.get("asset_flags") == "none":
                    blast_task = prompts.BLAST_TASK_V5R_NOFLAGS_FLOORED
                    blast_user = prompts.BLAST_USER_V5R_NOFLAGS
                else:
                    blast_task = prompts.BLAST_TASK_V5R_FLOORED
                    blast_user = prompts.BLAST_USER_V5R
            elif self.impact_mode in _POLICY_SENS_MODES:
                blast_task = prompts.BLAST_TASK_V5
                blast_user = prompts.BLAST_USER_V4
            else:
                blast_task = prompts.BLAST_TASK_V4
                blast_user = prompts.BLAST_USER_V4
        elif self.impact_mode in _PROFILE_SENS_MODES:
            # Coverage + N/A rubric + profile-sens note + v3 bulk-parameter note.
            blast_task, blast_user = prompts.BLAST_TASK_NA_PROFILE_V3, prompts.BLAST_USER_NA
        elif self.impact_mode == "five_level_v2_na":
            blast_task, blast_user = prompts.BLAST_TASK_NA, prompts.BLAST_USER_NA
        elif self.impact_mode == "five_level_v2_ctx":
            # Same rubric as _na; the user message carries the tool's understanding.
            blast_task, blast_user = prompts.BLAST_TASK_NA, prompts.BLAST_USER_NA_CTX
            if not self._tool_profiles:
                self.profile_tools()
        elif self.impact_mode == "hybrid":
            blast_task, blast_user = prompts.BLAST_TASK_CONSEQUENCES, prompts.BLAST_USER
        else:
            blast_task, blast_user = prompts.BLAST_TASK, prompts.BLAST_USER
        # The register's Tools cell, recovered from the asset tags the driver
        # wrote. This is the organization's own statement of what reaches what —
        # the `relevance` arms consult it instead of leaving the gate to the model.
        declared = {
            asset.asset_id: {t.split(":", 1)[1] for t in asset.tags if t.startswith("tool:")}
            for asset in self.registry.assets
        }
        relevance = self._ult_opts.get("relevance")
        blast: dict[str, int | None] = {}
        for tool in self.registry.tools:
            for asset in self.registry.assets:
                # The deterministic fallback keys off sensitivity; with no sensitivity
                # stage it gets the neutral mid-tier. Strict (LLM-only) scans never
                # reach the fallback anyway — it exists for offline smoke runs.
                if relevance == "register" and tool.name not in declared.get(asset.asset_id, ()):
                    # The organization does not list this tool against this asset,
                    # so the pair is N/A without spending a model call on it.
                    blast[f"{tool.name}|{asset.asset_id}"] = None
                    self._blast_escape[f"{tool.name}|{asset.asset_id}"] = "none"
                    continue
                fb_sens = sensitivity[asset.asset_id] if sensitivity else _NEUTRAL_SENSITIVITY
                fb_blast, fb_reason = fallback.blast_radius(tool, asset, fb_sens)
                item = {"tool": tool.to_prompt_json(), "asset": asset.to_prompt_json()}
                fmt: dict[str, str] = {
                    "tool_json": json.dumps(tool.to_prompt_json()),
                    "asset_json": json.dumps(asset.to_prompt_json()),
                }
                if self.impact_mode == "five_level_v2_ctx":
                    fmt["tool_profile"] = json.dumps(self._tool_profiles.get(tool.name, {}))
                if relevance in ("prompt", "combo"):
                    listed = sorted(declared.get(asset.asset_id, ()))
                    fmt["register_tools"] = ", ".join(listed) if listed else "none"
                if self._ult_opts.get("v5r_prompts"):
                    fmt["tool_impact"] = str(impacts.get(tool.name, "unknown") if impacts else "?")
                    fmt["asset_sensitivity"] = str(
                        sensitivity.get(asset.asset_id, "unknown") if sensitivity else "?"
                    )
                if self._ult_opts.get("blast_peers"):
                    fmt["peer_tools"] = json.dumps(
                        [t.name for t in self.registry.tools if t.name != tool.name]
                    )
                    fmt["peer_assets"] = json.dumps(
                        [a.asset_id for a in self.registry.assets if a.asset_id != asset.asset_id]
                    )
                user_msg = blast_user.format(**fmt)
                if self._ult_opts.get("tools_in_prompts"):
                    user_msg += self._tools_context_block()
                result = self._ask(self._proposer_prompt(blast_task, user_msg))
                na = (
                    relevance not in ("register", "none")
                    and self.impact_mode in _NA_MODES
                    and isinstance(result, dict)
                    and (
                        result.get("affects_asset") is False
                        or result.get("blast_radius") is None  # null blast -> N/A cell
                    )
                )
                if na:
                    value, conf = None, float(result.get("confidence", 0.7))  # N/A cell
                    proposed = result
                elif isinstance(result, dict) and "blast_radius" in result:
                    value = _clamp(result["blast_radius"], 1, 5, fb_blast)
                    proposed, conf = result, float(result.get("confidence", 0.7))
                elif self.strict:
                    self._strict_fail("blast_radius", f"{tool.name}|{asset.asset_id}")  # raises
                else:
                    self._used_fallback = True
                    value = fb_blast
                    conf = 0.8
                    proposed = _fallback_proposed(value, fb_reason, conf)
                key = f"{tool.name}|{asset.asset_id}"
                blast[key] = value
                # Record the model's own escape route verbatim (audit only, no
                # correction): the model decides both the tier and its route.
                self._blast_escape[key] = (
                    result.get("escape", "none") if isinstance(result, dict) else "none"
                )
                # The quoted words the model cited for a tier-5 route. Without
                # this the evidence the rubric demands is generated and thrown
                # away, so a 5 cannot be checked without re-running the scan.
                evidence = (
                    result.get("escape_evidence", "") if isinstance(result, dict) else ""
                )
                if evidence:
                    self._blast_escape_evidence[key] = evidence
                self._proposals.append(
                    _Proposal("blast_radius", key, item, proposed, value or 0, 1, 5, conf)
                )
        return blast

    # -- Judge cross-check (EVALUATION ONLY — never called during a scan) ----
    def judge(self) -> dict:
        """Run the independent reviewer over every proposal.

        **Evaluation-only.** This is NOT part of a production scan (``build_table``
        never calls it): its band-level corrections are folded into
        :func:`band_label`'s floors and its skepticism into the proposer prompts,
        so a single pass stands alone. It remains callable so an evaluation can
        measure how often an independent reviewer agrees with the base model — run
        the proposer stages first (they populate ``self._proposals``), then call
        this. For each primitive decision the judge re-derives the value from the
        same domain profile and compares, recording any disagreement.
        """
        overrides: dict[tuple[str, str], int] = {}
        disagreements: list[dict] = []
        reviewed = 0
        if self.use_llm:
            for p in self._proposals:
                verdict = self._judge_one(p)
                if verdict is None:  # model unreachable for this record
                    continue
                reviewed += 1
                judged = _clamp(verdict.get("judged_value"), p.low, p.high, p.value)
                # Agreement is decided HERE, not self-reported. The judge scored the
                # item blind (it never saw p.value), so an exact match is meaningful
                # rather than an anchoring artifact of being shown the answer.
                if judged != p.value:
                    overrides[(p.field, p.key)] = judged
                    disagreements.append(
                        {
                            "field": p.field,
                            "key": p.key,
                            "proposed": p.value,
                            "judged": judged,
                            "reasoning": str(verdict.get("reasoning", ""))[:300],
                        }
                    )
        self._overrides = overrides

        if reviewed == 0:
            # No model verdicts (offline, or model went down): we cannot do an
            # independent review, so flag low-confidence proposals instead.
            flagged = sum(1 for p in self._proposals if p.confidence < REVIEW_CONFIDENCE)
            return {
                "total_records": len(self._proposals),
                "flagged_for_review": flagged,
                "judge_ran": False,
                "overridden": 0,
            }
        return {
            "total_records": len(self._proposals),
            "reviewed": reviewed,
            "flagged_for_review": len(disagreements),
            "judge_ran": True,
            "overridden": len(overrides),
            "disagreements": disagreements,
        }

    def _judge_one(self, proposal: _Proposal) -> dict | None:
        """Ask the judge to score one item BLIND and return its verdict.

        The judge gets the same scoring rules and item as the proposer but is NOT
        shown the proposer's answer, so its value is anchor-free. Agreement is then
        computed by the caller by comparing the two values — this keeps the measured
        agreement rate honest instead of inflated by the judge seeing the answer.
        """
        rules = {
            "tool_impact": prompts.TOOL_IMPACT_TASK,
            "sensitivity": prompts.ASSET_TASK,
            "blast_radius": prompts.BLAST_TASK,
        }.get(proposal.field, "")
        prompt = (
            prompts.JUDGE_SYSTEM.format(
                domain_profile=json.dumps(self.domain_profile, indent=2),
                scoring_rules=rules,
            )
            + "\n\n"
            + prompts.JUDGE_USER.format(
                field_name=proposal.field,
                item_key=proposal.key,
                item_json=json.dumps(proposal.item_json, indent=2),
            )
        )
        result = query_ollama(prompt)
        return result if isinstance(result, dict) and "judged_value" in result else None

    # -- Stage 4: baselines --------------------------------------------------
    def build_baselines(self) -> dict[str, dict]:
        """Expected/normal operations per consuming app — a RUNTIME primitive.

        Nothing in the static score multiplies this: the cell is
        ``sensitivity x blast x impact``, and a baseline only becomes meaningful
        when there is an actual call to compare against it. v5r therefore drops
        the stage entirely and leaves it to the dynamic scorer, which is the
        stage that can observe a deviation. Keeping it here cost a full
        policy-bearing prompt per app for a value the static table never used.
        """
        if self._ult_opts.get("no_baselines"):
            return {}
        baselines: dict[str, dict] = {}
        for app_id, purpose in self.registry.apps.items():
            user = prompts.BASELINE_USER.format(
                app_json=json.dumps({"app_id": app_id, "purpose": purpose})
            )
            result = self._ask(self._proposer_prompt(prompts.BASELINE_TASK, user))
            if isinstance(result, dict) and "expected_tools" in result:
                baselines[app_id] = result
            elif self.strict:
                self._strict_fail("baseline", app_id)  # raises; never fabricates
            else:
                self._used_fallback = True
                baselines[app_id] = _fallback_baseline(app_id, purpose, self.registry)
        return baselines

    # -- Assembly ------------------------------------------------------------
    def build_table(self, version: str) -> dict:
        """Run all stages and assemble the final static table dict."""
        profile = self.infer_domain()
        impacts = self.score_tools()
        # Sensitivity-free modes skip stage 2: the organization's written profile
        # already states how severe each asset is, so no 1-5 number is derived.
        # Profile-sens modes also skip stage 2 but carry the org's OWN numbers.
        if self.score_sensitivity:
            sensitivity = self.score_assets()
        elif self.impact_mode in _PROFILE_SENS_MODES:
            sensitivity = self.profile_sensitivity
        else:
            sensitivity = None
        blast = self.score_blast(sensitivity, impacts)
        baselines = self.build_baselines()

        # Deterministic assembly passes (five_level_v2_ult): the model's verbatim
        # blast is preserved as blast_radius_raw, then alias twins are unified and
        # the gated sensitivity floor applied — in that order, so the floor sees
        # the aliased value.
        profile_sens_mode = self.impact_mode in _PROFILE_SENS_MODES
        policy_sens_mode = self.impact_mode in _POLICY_SENS_MODES
        # The assembly keys on the sensitivity NUMBER, not on who produced it, so
        # the policy arm gets the same deterministic passes and the same bands.
        assembly_mode = self.impact_mode in _ASSEMBLY_MODES
        blast_raw: dict[str, int | None] = {}
        impacts_raw: dict[str, int] = {}
        alias_twins: dict[str, str] = {}
        alias_fixups: list[dict] = []
        bulk_twins: dict[str, str] = {}
        bulk_fixups: list[dict] = []
        roof_fixups: list[dict] = []
        asset_flags: dict[str, tuple[str, ...]] = {}
        floor_raised = 0
        # Which floor/roof configuration this mode runs. v5r replaces the gated
        # ult floors with three ungated rules and drops the roof entirely.
        v5r_assembly = policy_sens_mode and self._ult_opts.get("v5r_prompts")
        if v5r_assembly and self._ult_opts.get("floors") == "none":
            floors, impact_floors = {}, {}
            gate, roof = V5R_GATE_IMPACT_MIN, V5R_ROOF
        elif v5r_assembly and self._ult_opts.get("floors") == "low":
            floors, impact_floors = V5R_LOW_FLOORS, V5R_LOW_IMPACT_FLOORS
            gate, roof = V5R_GATE_IMPACT_MIN, V5R_ROOF
        elif v5r_assembly:
            floors, impact_floors = V5R_FLOORS, V5R_IMPACT_FLOORS
            gate, roof = V5R_GATE_IMPACT_MIN, V5R_ROOF
        else:
            floors, impact_floors = ULT_FLOORS, ULT_IMPACT_FLOORS
            gate, roof = ULT_GATE_IMPACT_MIN, ULT_ROOF
        if assembly_mode:
            blast_raw = dict(blast)
            impacts_raw = dict(impacts)
            asset_ids = [a.asset_id for a in self.registry.assets]
            # Escape flags per asset (from the profile tags "flag:<name>"), for
            # the roof's flag-aware read cap.
            asset_flags = {
                a.asset_id: tuple(t.split(":", 1)[1] for t in a.tags if t.startswith("flag:"))
                for a in self.registry.assets
            }
            # v3 order: bulk IMPACT dominance first (the floors gate on impact),
            # then alias unification, then the gated floors (sens-keyed + the
            # impact-5 minimum), then bulk BLAST dominance, then the roof caps.
            bulk_twins = bulk_twin_map(self.registry.tools)
            impacts, bulk_impact_fixups = apply_bulk_impact(impacts, bulk_twins)
            alias_twins = alias_twin_map(self.registry.tools)
            blast, alias_fixups = apply_alias_twins(blast, alias_twins, asset_ids)
            blast, floor_raised = apply_gated_floor(
                blast,
                sensitivity,
                impacts,
                floors=floors,
                gate_impact_min=gate,
                impact_floors=impact_floors,
            )
            blast, bulk_blast_fixups = apply_bulk_blast(blast, bulk_twins, asset_ids)
            bulk_fixups = bulk_impact_fixups + bulk_blast_fixups
            # Roofs LAST, and only where a roof exists. v5r has none: a cap can
            # only under-score, and the floors now state the lower bound outright.
            if roof:
                blast, roof_fixups = apply_blast_roof(
                    blast,
                    sensitivity,
                    impacts,
                    asset_flags,
                    read_cap=roof["read_cap"],
                    sens_caps=roof["sens_caps"],
                    combined_cap=roof["combined_cap"],
                )

        # The judge never runs in a scan: its band-level corrections live in
        # band_label's floors and its skepticism in the proposer prompts, so a
        # single pass stands alone. judge() remains callable for evaluation only.
        crosscheck = {"judge_ran": False, "note": "judge not run in scans (evaluation-only)"}

        # Blast radius is the model's own coverage judgment (LLM-only). A None blast
        # is an N/A cell (an _NA_MODES run where the tool does not act on this asset)
        # -> score None, band "na". band_label is a pure function of primitives otherwise.
        use_sqrt = self.impact_mode in _SQRT_MODES
        bands: dict[str, dict[str, str]] = {}
        cells: dict[str, dict[str, float | None]] = {}
        for asset in self.registry.assets:
            s = sensitivity[asset.asset_id] if sensitivity else None
            brow: dict[str, str] = {}
            crow: dict[str, float | None] = {}
            for tool in self.registry.tools:
                br = blast[f"{tool.name}|{asset.asset_id}"]
                i = impacts[tool.name]
                if br is None:  # N/A — tool does not affect this asset
                    crow[tool.name] = None
                    brow[tool.name] = "na"
                elif s is None:  # no sensitivity primitive: the cell is blast x impact
                    crow[tool.name] = round(br * LIKELIHOOD * i, 2)
                    brow[tool.name] = band_label_no_sens(br, i)
                elif assembly_mode:
                    # 5-level ladder with the org's sensitivity: v5 band floors.
                    crow[tool.name] = round(s * br * LIKELIHOOD * i, 2)
                    brow[tool.name] = band_label_v5(s, br, i)
                elif use_sqrt:
                    # geometric mean of the two tool-side factors: one weak factor no
                    # longer annihilates the cell. Max stays 5*5*sqrt(5*5) = 125.
                    crow[tool.name] = round(s * 5 * (br * i) ** 0.5, 2)
                    brow[tool.name] = band_label(s, br, i)
                else:
                    crow[tool.name] = round(s * br * LIKELIHOOD * i, 2)
                    brow[tool.name] = band_label(s, br, i)
            bands[asset.asset_id] = brow
            cells[asset.asset_id] = crow

        if self._used_fallback:
            profile["needs_human_review"] = True

        no_sens = sensitivity is None
        return {
            "version": version,
            "server": self.registry.server,
            "mcp_kind": profile.get("mcp_kind", self.registry.kind),
            "model_reviewed": not self._used_fallback,
            "inferred_profile": profile,
            "formula": FORMULA_NO_SENS if no_sens else FORMULA,
            "band_thresholds": (
                BAND_THRESHOLDS_NO_SENS
                if no_sens
                else BAND_THRESHOLDS_V5
                if assembly_mode
                else BAND_THRESHOLDS
            ),
            "tool_impact": impacts,
            "impact_mode": self.impact_mode,
            # Without the sensitivity factor the ceiling is blast(5) x impact(5) = 25.
            "score_max": (
                5 * _IMPACT_MAX[self.impact_mode] if no_sens else 25 * _IMPACT_MAX[self.impact_mode]
            ),
            "tool_cia": self._tool_cia,
            # Empty in sensitivity-free modes: the asset axis is still there (blast is
            # per tool x asset), but no sensitivity was scored. `sensitivity_scored`
            # makes that explicit so a reader never mistakes {} for "no assets".
            "sensitivity_scored": not no_sens,
            # Where the sensitivity numbers came from: the org profile's table
            # (profile-sens modes), the LLM classifying against the org's written
            # policy (policy-sens modes), a plain LLM stage, or nowhere.
            "sensitivity_source": (
                "org_profile"
                if profile_sens_mode
                else "none"
                if no_sens
                else "llm_policy_class"
                if policy_sens_mode
                else "llm"
            ),
            "org_description_used": bool(self.org_description),
            # Hash of the profile text the model actually saw, so the scoring
            # input has provenance in the artifact it produced.
            "profile_sha256": (
                hashlib.sha256(self.org_description.encode("utf-8")).hexdigest()
                if self.org_description
                else None
            ),
            "asset_ids": [a.asset_id for a in self.registry.assets],
            "asset_sensitivity": {} if no_sens else sensitivity,
            "blast_radius": blast,
            # Ult-mode audit trail: the model's verbatim blast plus every
            # deterministic adjustment (alias unification, gated floor).
            "blast_radius_raw": blast_raw,
            "tool_impact_raw": impacts_raw,
            "alias_twins": alias_twins,
            "alias_fixups": alias_fixups,
            "bulk_twins": bulk_twins,
            "bulk_fixups": bulk_fixups,
            "asset_flags": asset_flags,
            # v5r runs no roof, so this is {} and `roof_fixups` stays empty.
            "blast_roof": (
                {**roof, "capped_cells": len(roof_fixups)} if assembly_mode and roof else {}
            ),
            "roof_fixups": roof_fixups,
            "blast_floor": (
                {
                    "gate_impact_min": gate,
                    "floors": {str(k): v for k, v in floors.items()},
                    "impact_floors": {str(k): v for k, v in impact_floors.items()},
                    "raised_cells": floor_raised,
                }
                if assembly_mode
                else {}
            ),
            # Human-readable manifest of every deterministic rule this scan applied
            # (the rules are code, not prompts — this makes them visible in outputs).
            "deterministic_rules": (
                [
                    (
                        "sensitivity = LLM classification against the org POLICY "
                        "(classify -> map; the org supplies no numbers)"
                        if policy_sens_mode
                        else "sensitivity = org profile table (never LLM-scored)"
                    ),
                    *(
                        [
                            "tool impact = deterministic ladder (static_impact.py); the "
                            f"v4 impact prompt decides only where the ladder abstains "
                            f"(confidence < {STATIC_IMPACT_MIN_CONFIDENCE})"
                        ]
                        if self._ult_opts.get("static_impact_fallback")
                        else []
                    ),
                    "bulk twin impact: impact(bulk) >= impact(singular)",
                    "alias twins (DEPRECATED -> canonical): max blast per asset",
                    (
                        "blast floor, UNGATED: "
                        + ", ".join(
                            [f"sens {k} -> blast >= {v}" for k, v in sorted(floors.items())]
                            + [
                                f"impact {k} -> blast >= {v}"
                                for k, v in sorted(impact_floors.items())
                            ]
                        )
                        if v5r_assembly
                        else f"gated blast floor (impact >= {gate}): sens 5 -> blast >= "
                        f"{floors[5]}, sens 4 -> blast >= {floors[4]}"
                    ),
                    *(
                        []
                        if v5r_assembly
                        else [
                            f"impact-keyed floor (one tier lower): impact 5 -> blast >= "
                            f"{impact_floors[5]}, impact 4 -> blast >= {impact_floors[4]}"
                        ]
                    ),
                    "bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)",
                    *(
                        ["blast roof: REMOVED in this mode (a cap can only under-score)"]
                        if not roof
                        else [
                            f"blast roof (impact <= 3 only, never a mutation): non-escaping "
                            f"read caps at {roof['read_cap']}, sens-1 caps at "
                            f"{roof['sens_caps'].get(1)} — assets flagged "
                            f"{'/'.join(sorted(ULT_ESCAPE_FLAGS))} are exempt"
                        ]
                    ),
                    "bands: band_label_v5 — pure score thresholds on the 0-125 "
                    "scale (low <17, medium 17-49, high 50-99, critical >=100); "
                    "no categorical overrides, so a band is explainable from its "
                    "own score",
                ]
                if assembly_mode
                else []
            ),
            "blast_escape": self._blast_escape,
            "blast_escape_evidence": self._blast_escape_evidence,
            "ult_variant_options": self._ult_opts,
            "tool_profiles": self._tool_profiles,
            "static_impacts": self._static_impacts,
            # v5 hand-off ledger: which scorer decided each tool's impact.
            "tool_impact_source": self._impact_source,
            "cells": cells,
            "bands": bands,
            "band_distribution": _band_distribution(bands),
            "baselines": baselines,
            "crosscheck_summary": crosscheck,
        }


def _band_distribution(bands: dict[str, dict[str, str]]) -> dict[str, int]:
    """Count cells per band — the risk pyramid for this server (gate workload).

    ``na`` counts pairs the tool does not affect (excluded from the risk pyramid).
    """
    dist = {"low": 0, "medium": 0, "high": 0, "critical": 0, "na": 0}
    for row in bands.values():
        for band in row.values():
            dist[band] = dist.get(band, 0) + 1
    return dist


def _fallback_proposed(value: int, reasoning: str, confidence: float) -> dict:
    """Wrap a deterministic decision as a proposal the judge can still review."""
    return {
        "value": value,
        "reasoning": reasoning,
        "confidence": confidence,
        "source": "deterministic_fallback",
    }


def _has_annotation(tool: ToolSpec) -> bool:
    return any(
        h is not None for h in (tool.read_only_hint, tool.destructive_hint, tool.idempotent_hint)
    )


def _fallback_baseline(app_id: str, purpose: str, registry: ServerRegistry) -> dict:
    """A minimal, conservative baseline when the model is unavailable."""
    read_tools = [t.name for t in registry.tools if fallback.tool_impact(t)[0] == 1]
    return {
        "app_id": app_id,
        "purpose": purpose,
        "expected_tools": read_tools,
        "expected_flows": [{"pattern": "read within remit", "normal_sensitivity_max": 3}],
        "anomalous_patterns": [
            "mutating a high-sensitivity asset",
            "bulk export of sensitive data",
        ],
        "confidence": 0.5,
        "reasoning": "deterministic fallback: read-only tools assumed normal",
    }


def build_static_table(
    registry: ServerRegistry,
    *,
    use_llm: bool = True,
    strict: bool = False,
    version: str = "static-0000-00-00",
    impact_mode: str = "baseline",
) -> dict:
    """Convenience entry point: score ``registry`` and return the table dict.

    Pass ``use_llm=False`` for a fully deterministic run. Pass ``strict=True`` for
    the LLM-only mode the scanner uses: any unanswered record raises
    :class:`LLMUnavailableError` instead of falling back to a heuristic. Tests
    that exercise the LLM path monkeypatch
    ``mcp_security.static_scoring.pipeline.query_ollama``.

    The scan never runs the judge; bands are always the deterministic
    :func:`band_label` (or :func:`band_label_no_sens` in a sensitivity-free mode).
    :meth:`StaticScorer.judge` remains for evaluation only.
    """
    return StaticScorer(
        registry, use_llm=use_llm, strict=strict, impact_mode=impact_mode
    ).build_table(version)
