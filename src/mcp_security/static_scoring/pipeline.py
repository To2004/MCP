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
# Score cutoffs on the multiplied score (max scale 5*4*3 = 60).
BAND_THRESHOLDS = {"medium": 8, "high": 24}
# A decision below this confidence is counted as needing human review.
REVIEW_CONFIDENCE = 0.7


def band_label(sensitivity: int, blast: int, impact: int) -> str:
    """Operational band for one (asset, tool) cell — a security-gate calibration.

    The static score is an *upper-bound* (likelihood pinned to 1.0), so banding
    on the raw number alone makes too many cells critical and a gate that blocks
    them would stop legitimate work. Instead we reserve the top band the way a
    reviewer would, per ``docs/standards/scoring-reference.md``:

    * **critical** — only the catastrophes you must hard-gate: an *irreversible*
      action (impact 3 / Irreversibility ×3) that destroys a *crown-jewel*
      asset (sensitivity 5 = regulated / PII / secrets) at departmental-or-wider
      reach (blast ≥ 3). These cannot be reconstituted.
    * **high** — serious but recoverable or sub-crown-jewel: any irreversible op
      on restricted business data (sensitivity ≥ 4), or a high raw score. Watch
      and throttle, don't block.
    * **medium / low** — routine; let it through. Reads stay low regardless of
      sensitivity (they don't change state), so normal work is not gated.

    Confidentiality matters too: a read (impact 1) can't *destroy* anything, but
    reading a crown-jewel still leaks it. So reads carry a floor — a narrow read
    of regulated/PII/secret data is never "nothing" (medium), and a broad read of
    sensitive data is mass exfiltration (high). Routine reads of ordinary data
    stay low, so normal work still flows.

    This yields a risk pyramid (~1-2% critical) instead of a flat alarm.
    """
    score = sensitivity * blast * impact
    # critical — irreversible destruction of a crown-jewel asset at scale.
    if impact == 3 and sensitivity == 5 and blast >= 3:
        return "critical"
    # high — irreversible op on restricted+ data, a high raw score, or a *broad*
    # read of sensitive data (mass exfiltration of regulated/PII/secrets).
    if (
        (impact == 3 and sensitivity >= 4)
        or score >= BAND_THRESHOLDS["high"]
        or (impact == 1 and sensitivity >= 4 and blast >= 3)
    ):
        return "high"
    # medium — middling score, or any read of a crown-jewel (confidentiality
    # floor: reading a secret / PII record is never simply "low").
    if score >= BAND_THRESHOLDS["medium"] or (impact == 1 and sensitivity == 5):
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

    def __init__(self, registry: ServerRegistry, *, use_llm: bool = True) -> None:
        self.registry = registry
        self.use_llm = use_llm
        self._used_fallback = False
        self._proposals: list[_Proposal] = []
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
            self._used_fallback = True
        return result

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
                tools_json=json.dumps(self.registry.tools_json(), indent=2),
                assets_json=json.dumps(self.registry.assets_json(), indent=2),
            )
        )
        result = self._ask(prompt)
        if not isinstance(result, dict) or "mcp_kind" not in result:
            self._used_fallback = True
            result = fallback.domain_profile(self.registry)
        self.domain_profile = result
        self._domain_confidence = float(result.get("confidence", 0.6))
        return result

    # -- Stage 1: tool impact -----------------------------------------------
    def score_tools(self) -> dict[str, int]:
        impacts: dict[str, int] = {}
        for tool in self.registry.tools:
            fb_impact, fb_irrev, fb_reason = fallback.tool_impact(tool)
            item = tool.to_prompt_json()
            result = self._ask(
                self._proposer_prompt(
                    prompts.TOOL_IMPACT_TASK,
                    prompts.TOOL_IMPACT_USER.format(tool_json=json.dumps(item)),
                )
            )
            if isinstance(result, dict) and "tool_impact" in result:
                impact = _clamp(result["tool_impact"], 1, 3, fb_impact)
                proposed, conf = result, float(result.get("confidence", 0.7))
            else:
                self._used_fallback = True
                impact = fb_impact
                conf = 0.85 if _has_annotation(tool) else 0.6
                proposed = _fallback_proposed(impact, fb_reason, conf)
            impacts[tool.name] = impact
            self._proposals.append(
                _Proposal("tool_impact", tool.name, item, proposed, impact, 1, 3, conf)
            )
        return impacts

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
    def score_blast(self, sensitivity: dict[str, int]) -> dict[str, int]:
        blast: dict[str, int] = {}
        for tool in self.registry.tools:
            for asset in self.registry.assets:
                fb_blast, fb_reason = fallback.blast_radius(
                    tool, asset, sensitivity[asset.asset_id]
                )
                item = {"tool": tool.to_prompt_json(), "asset": asset.to_prompt_json()}
                result = self._ask(
                    self._proposer_prompt(
                        prompts.BLAST_TASK,
                        prompts.BLAST_USER.format(
                            tool_json=json.dumps(tool.to_prompt_json()),
                            asset_json=json.dumps(asset.to_prompt_json()),
                        ),
                    )
                )
                if isinstance(result, dict) and "blast_radius" in result:
                    value = _clamp(result["blast_radius"], 0, 4, fb_blast)
                    proposed, conf = result, float(result.get("confidence", 0.7))
                else:
                    self._used_fallback = True
                    value = fb_blast
                    conf = 0.8
                    proposed = _fallback_proposed(value, fb_reason, conf)
                key = f"{tool.name}|{asset.asset_id}"
                blast[key] = value
                self._proposals.append(
                    _Proposal("blast_radius", key, item, proposed, value, 0, 4, conf)
                )
        return blast

    # -- Stage 5: judge cross-check -----------------------------------------
    def judge(self) -> dict:
        """Run the independent reviewer over every proposal (stage 5).

        For each primitive decision the judge re-derives the value from the same
        domain profile and compares. A disagreement is recorded and the judge's
        value overrides the proposer's — implementing the ``JUDGE_*`` templates
        from the registry's prompt set. Returns the cross-check summary; with no
        model available the judge cannot run and we fall back to flagging
        low-confidence proposals.
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
                agree = bool(verdict.get("agree", judged == p.value))
                if not agree or judged != p.value:
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
        """Ask the judge to independently re-derive one proposal's value."""
        prompt = (
            prompts.JUDGE_SYSTEM.format(domain_profile=json.dumps(self.domain_profile, indent=2))
            + "\n\n"
            + prompts.JUDGE_USER.format(
                field_name=proposal.field,
                item_key=proposal.key,
                item_json=json.dumps(proposal.item_json, indent=2),
                proposed_json=json.dumps(proposal.proposed_json),
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

        # Stage 5: judge, then apply its overrides before the cells are derived
        # so the matrix reflects the reviewed values, not the first proposals.
        crosscheck = self.judge()
        for (field, key), value in self._overrides.items():
            if field == "tool_impact":
                impacts[key] = value
            elif field == "sensitivity":
                sensitivity[key] = value
            elif field == "blast_radius":
                blast[key] = value

        cells: dict[str, dict[str, float]] = {}
        bands: dict[str, dict[str, str]] = {}
        for asset in self.registry.assets:
            row: dict[str, float] = {}
            brow: dict[str, str] = {}
            s = sensitivity[asset.asset_id]
            for tool in self.registry.tools:
                br = blast[f"{tool.name}|{asset.asset_id}"]
                i = impacts[tool.name]
                row[tool.name] = round(s * br * LIKELIHOOD * i, 2)
                brow[tool.name] = band_label(s, br, i)
            cells[asset.asset_id] = row
            bands[asset.asset_id] = brow

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
            "asset_sensitivity": sensitivity,
            "blast_radius": blast,
            "cells": cells,
            "bands": bands,
            "band_distribution": _band_distribution(bands),
            "baselines": baselines,
            "crosscheck_summary": crosscheck,
        }


def _band_distribution(bands: dict[str, dict[str, str]]) -> dict[str, int]:
    """Count cells per band — the risk pyramid for this server (gate workload)."""
    dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for row in bands.values():
        for band in row.values():
            dist[band] += 1
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
    version: str = "static-0000-00-00",
) -> dict:
    """Convenience entry point: score ``registry`` and return the table dict.

    Pass ``use_llm=False`` for a fully deterministic run. Tests that exercise the
    LLM path monkeypatch ``mcp_security.static_scoring.pipeline.query_ollama``.
    """
    return StaticScorer(registry, use_llm=use_llm).build_table(version)
