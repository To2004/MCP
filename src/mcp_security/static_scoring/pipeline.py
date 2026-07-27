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

import json
import logging
from dataclasses import dataclass

from mcp_security.llm.ollama_client import query_ollama

from . import fallback, prompts
from .registry import ServerRegistry, ToolSpec

logger = logging.getLogger(__name__)

FORMULA = "asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact"
LIKELIHOOD = 1.0
BANDS = ("low", "medium", "high", "critical")

# Max tool-impact value per experiment mode -> score_max = 5(sens) * 5(blast) * this.
# hybrid uses the geometric-mean formula (score = sens*5*sqrt(blast*impact)), whose
# max is 5*5*sqrt(5*5) = 125 = 25*5, so the same 25*_IMPACT_MAX rule gives 125.
_IMPACT_MAX = {
    "baseline": 3, "five_level": 5, "five_level_v2": 5, "five_level_v2_na": 5, "cia": 6,
    "hybrid": 5, "hybrid_na": 5,
}
# Modes that use the geometric-mean formula score = sens * 5 * sqrt(blast * impact).
_SQRT_MODES = {"hybrid", "hybrid_na"}
# Modes whose blast stage may mark a (tool, asset) pair N/A (affects_asset=false),
# so the cell is not scored (blast None -> band "na").
_NA_MODES = {"hybrid_na", "five_level_v2_na"}


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
    if (
        impact == 3
        or (impact == 1 and sensitivity >= 4)
        or score >= BAND_THRESHOLDS["medium"]
    ):
        return "medium"
    return "low"


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
        self, registry: ServerRegistry, *, use_llm: bool = True, strict: bool = False,
        impact_mode: str = "baseline",
    ) -> None:
        self.registry = registry
        self.use_llm = use_llm
        # impact_mode selects the tool-impact experiment:
        #   "baseline"   -> current 1-3 damage-ceiling rubric (max score 75)
        #   "five_level" -> 1-5 metadata..destroy-all scale (max score 125)
        #   "cia"        -> base(1-3) + one point per violated C/I/A facet (max 150)
        if impact_mode not in _IMPACT_MAX:
            raise ValueError(f"unknown impact_mode {impact_mode!r}; choose {list(_IMPACT_MAX)}")
        self.impact_mode = impact_mode
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

    def _proposer_prompt(self, task: str, user: str) -> str:
        """Assemble preamble + task + user message for a proposer stage."""
        preamble = prompts._PROPOSER_BASE.format(
            domain_profile=json.dumps(self.domain_profile, indent=2)
        )
        return f"{preamble}\n{task}\n\n{user}"

    # -- Stage 0: domain inference ------------------------------------------
    def infer_domain(self) -> dict:
        prompt = (
            prompts.DOMAIN_INFERENCE_SYSTEM
            + "\n\n"
            + prompts.DOMAIN_INFERENCE_USER.format(
                tools_json=json.dumps(self.registry.tools_json_compact(), indent=2),
                assets_json=json.dumps(self.registry.assets_json(), indent=2),
            )
        )
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
        if self.impact_mode == "five_level":
            task, user, hi = prompts.TOOL_IMPACT_TASK_5LEVEL, prompts.TOOL_IMPACT_USER_5LEVEL, 5
        elif self.impact_mode in ("five_level_v2", "five_level_v2_na"):
            task, user, hi = prompts.TOOL_IMPACT_TASK_5LEVEL_V2, prompts.TOOL_IMPACT_USER_5LEVEL, 5
        elif self.impact_mode in ("hybrid", "hybrid_na"):
            task, user, hi = prompts.TOOL_IMPACT_TASK_HYBRID, prompts.TOOL_IMPACT_USER_HYBRID, 5
        else:
            task, user, hi = prompts.TOOL_IMPACT_TASK, prompts.TOOL_IMPACT_USER, 3
        result = self._ask(self._proposer_prompt(task, user.format(tool_json=json.dumps(item))))
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
            "base": fb_impact, "C": False, "I": False, "A": False, "impact": fb_impact
        }
        return fb_impact, _fallback_proposed(fb_impact, fb_reason, conf), conf

    # -- Stage 2: asset sensitivity -----------------------------------------
    def score_assets(self) -> dict[str, int]:
        sens: dict[str, int] = {}
        for asset in self.registry.assets:
            fb_sens, fb_drivers, fb_reason = fallback.asset_sensitivity(asset)
            item = asset.to_prompt_json()
            result = self._ask(
                self._proposer_prompt(
                    prompts.ASSET_TASK,
                    prompts.ASSET_USER.format(asset_json=json.dumps(item)),
                )
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

    # -- Stage 3: blast radius (per tool×asset pair) ------------------------
    def score_blast(self, sensitivity: dict[str, int]) -> dict[str, int | None]:
        # hybrid/hybrid_na redefine blast as "reach of consequences". hybrid_na also
        # lets the model mark a pair N/A (affects_asset=false) -> value is None.
        if self.impact_mode == "hybrid_na":
            blast_task, blast_user = prompts.BLAST_TASK_CONSEQUENCES_NA, prompts.BLAST_USER_NA
        elif self.impact_mode == "five_level_v2_na":
            blast_task, blast_user = prompts.BLAST_TASK_NA, prompts.BLAST_USER_NA
        elif self.impact_mode == "hybrid":
            blast_task, blast_user = prompts.BLAST_TASK_CONSEQUENCES, prompts.BLAST_USER
        else:
            blast_task, blast_user = prompts.BLAST_TASK, prompts.BLAST_USER
        blast: dict[str, int | None] = {}
        for tool in self.registry.tools:
            for asset in self.registry.assets:
                fb_blast, fb_reason = fallback.blast_radius(
                    tool, asset, sensitivity[asset.asset_id]
                )
                item = {"tool": tool.to_prompt_json(), "asset": asset.to_prompt_json()}
                result = self._ask(
                    self._proposer_prompt(
                        blast_task,
                        blast_user.format(
                            tool_json=json.dumps(tool.to_prompt_json()),
                            asset_json=json.dumps(asset.to_prompt_json()),
                        ),
                    )
                )
                na = (
                    self.impact_mode in _NA_MODES
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
        sensitivity = self.score_assets()
        blast = self.score_blast(sensitivity)
        baselines = self.build_baselines()

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
            s = sensitivity[asset.asset_id]
            brow: dict[str, str] = {}
            crow: dict[str, float | None] = {}
            for tool in self.registry.tools:
                br = blast[f"{tool.name}|{asset.asset_id}"]
                i = impacts[tool.name]
                if br is None:  # N/A — tool does not affect this asset
                    crow[tool.name] = None
                    brow[tool.name] = "na"
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

        return {
            "version": version,
            "server": self.registry.server,
            "mcp_kind": profile.get("mcp_kind", self.registry.kind),
            "model_reviewed": not self._used_fallback,
            "inferred_profile": profile,
            "formula": FORMULA,
            "band_thresholds": BAND_THRESHOLDS,
            "tool_impact": impacts,
            "impact_mode": self.impact_mode,
            "score_max": 25 * _IMPACT_MAX[self.impact_mode],
            "tool_cia": self._tool_cia,
            "asset_sensitivity": sensitivity,
            "blast_radius": blast,
            "blast_escape": self._blast_escape,
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
    :func:`band_label`. :meth:`StaticScorer.judge` remains for evaluation only.
    """
    return StaticScorer(
        registry, use_llm=use_llm, strict=strict, impact_mode=impact_mode
    ).build_table(version)
