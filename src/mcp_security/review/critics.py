"""A panel of persona-critic LLMs that adversarially critique the pipeline.

Where :mod:`.judge` checks fixed correctness claims and :mod:`.advisor` suggests
next steps, the **critics** are opinionated characters — each a different kind of
skeptic with its own lens and voice — told to find what is weak, wrong, or
over-sold. Diversity is the point: a red-teamer, a statistician, an SRE, a security
architect and a minimalist see different flaws, so together they cover more failure
modes than one reviewer (or one identical reviewer run five times) ever could.

Each critic reads the same evidence digest (measured results + key design facts)
and returns structured critiques. The caller (the human, or a synthesis step)
turns the union of their critiques into an improvement plan.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama

from .verify import RANKED_CSV, SCAN_DIR, run_verification, to_markdown as verify_to_markdown

REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL = REPO_ROOT / "reports" / "evaluation"


@dataclass(frozen=True)
class Critic:
    """One opinionated reviewer: a name, a personality, and the lens it judges by."""

    key: str
    name: str
    persona: str


# Five deliberately different characters. The persona text sets voice AND the
# specific failure modes each one is expert at spotting, so their critiques diverge.
CRITICS: tuple[Critic, ...] = (
    Critic(
        "red_teamer", "Vera, the red-teamer",
        "You are Vera, a ruthless offensive-security red-teamer. You assume every "
        "control is bypassable and it's your job to show how. You are cynical, "
        "concrete, and allergic to hand-waving. For THIS work you hunt: how an "
        "attacker games the static scanner (benign-looking tools, novel asset "
        "names, path tricks that dodge resolution), how a malicious call scores "
        "LOW and slips the gate, and where the threat model (servers protected FROM "
        "agents) is inverted or has blind spots. You care about evasion, not vibes.",
    ),
    Critic(
        "statistician", "Klaus, the statistician",
        "You are Klaus, a pedantic quantitative methodologist. You distrust every "
        "number until its denominator, sampling and independence are justified. For "
        "THIS work you attack: agreement metrics computed on tiny overlapping cell "
        "sets, circularity between the scanner and its own LLM-generated ground "
        "truth, an inter-rater 'ceiling' used to excuse low accuracy, bands derived "
        "non-deterministically, and any claim of improvement without a significance "
        "test or confidence interval. You demand effect sizes, not anecdotes.",
    ),
    Critic(
        "sre", "Mona, the SRE",
        "You are Mona, a battle-scarred site-reliability engineer who has to OPERATE "
        "this in production. You judge by what breaks at 3am. For THIS work you "
        "attack: a 1-hour LLM scan that must rerun whenever a file changes, "
        "non-reproducibility across GPUs/model versions, the false-positive rate of "
        "a gate that marks routine reads HIGH (it will be turned off), unresolved "
        "calls silently dropped, latency at request time, and the lack of a cheap "
        "deterministic fast-path. You care about cost, drift, and operability.",
    ),
    Critic(
        "architect", "Ada, the security architect",
        "You are Ada, a systems security architect who threat-models for a living. "
        "You judge coverage and composition. For THIS work you attack: what the "
        "scanner does NOT score (multi-step call chains, data flow between tools, "
        "time-of-check/time-of-use, cross-asset aggregation), single-cell scoring "
        "that misses an attack spread over many low cells, the abstract calendar/"
        "repo asset models vs real per-instance sensitivity, and whether the score "
        "formula's primitives actually compose into real-world risk. You see the "
        "whole kill-chain, not one call.",
    ),
    Critic(
        "minimalist", "Sam, the minimalist",
        "You are Sam, an Occam's-razor skeptic who believes most complexity is "
        "unjustified. You judge whether the machinery earns its keep. For THIS work "
        "you attack: whether a 32B LLM is needed at all when a tiny rule table "
        "(write+secret = high) might match it, whether directory-scope assets and "
        "parameter escalation add accuracy or just surface area, whether 85%-fragile "
        "cut-points mean the bands are noise, and which moving parts could be deleted "
        "with no measurable loss. Demand that every component justify its existence.",
    ),
)

CRITIC_SYSTEM = """{persona}

You are reviewing a defensive MCP (Model Context Protocol) security pipeline. It
statically scans an MCP server's tools and assets with a local LLM to build a risk
matrix (tool_impact 1-3 x asset_sensitivity 1-5 x blast_radius 0-4 -> score ->
band), derives input-parameter magnitude cutoffs, then ranks captured agent tool
calls against that matrix so a gateway could throttle/deny risky calls BEFORE
execution. Threat model: the MCP server is the protected asset; the agent is the
threat. Scoring is local-LLM-only (Qwen2.5), no hardcoded per-asset values.

Stay in character. Be specific and harsh but technically fair — cite the actual
numbers/design in the evidence. Do NOT rubber-stamp; your value is finding what is
weak. Each critique must be ACTIONABLE (name a concrete fix).

Output ONLY valid JSON, no prose, no fences:
{{"persona": "{name}",
  "headline": "one-sentence harshest verdict in your voice",
  "critiques": [
    {{"issue": "what is wrong/weak/oversold",
      "severity": "low|medium|high|critical",
      "why_it_matters": "the concrete consequence",
      "concrete_fix": "a specific change that would address it"}}
  ]}}"""

CRITIC_USER = """EVIDENCE (measured results + design facts):
{digest}

Return your critique JSON, in character."""


def _digest() -> str:
    """Compact evidence pack: measured results + the design facts critics attack."""
    parts: list[str] = ["## Deterministic self-checks", verify_to_markdown(run_verification())]

    for name in ("scanner_vs_human.md", "scanner_accuracy.md", "formula_sensitivity.md"):
        path = EVAL / name
        if path.exists():
            # Keep each report's head — the headline numbers the critics need.
            parts.append(f"## {name}\n" + "\n".join(path.read_text("utf-8").splitlines()[:18]))

    if SCAN_DIR.exists():
        lines = ["## Scans (band distributions)"]
        for p in sorted(SCAN_DIR.glob("*.json")):
            if p.stem.endswith("_params"):
                continue
            d = json.loads(p.read_text("utf-8"))
            lines.append(f"- {p.stem}: kind={d.get('server_kind')} "
                         f"assets={len(d.get('asset_sensitivity', {}))} "
                         f"bands={d.get('band_distribution')}")
        parts.append("\n".join(lines))

    if RANKED_CSV.exists():
        rows = list(csv.DictReader(RANKED_CSV.open(encoding="utf-8")))
        scored = [r for r in rows if r["scorable"] == "True"]
        esc = sum(1 for r in scored if r["param_band"] and r["final_band"] != r["band"])
        parts.append(f"## Ranked corpus\n- {len(rows)} calls, {len(scored)} scored, "
                     f"{len(rows) - len(scored)} unresolved, {esc} param-escalated\n"
                     f"- scored bands: {dict(Counter(r['final_band'] for r in scored))}")

    parts.append(
        "## Design facts (fair game to attack)\n"
        "- Scan is strict LLM-only (Qwen2.5:32b), ~1h for the filesystem servers; "
        "bands are LLM-decided per cell, not thresholded.\n"
        "- Ground truth for accuracy is the scanner's OWN LLM tables (partly "
        "circular); a separate 10-rater human/framework panel gives ~50% exact "
        "inter-rater agreement (filesystem).\n"
        "- Formula score=sensitivity*blast*impact; ~85% of cells flip band under a "
        "+/-1 input perturbation.\n"
        "- Calls are scored one (tool,asset) cell at a time; multi-step chains and "
        "cross-call aggregation are NOT modelled.\n"
        "- Calendar/github/slack assets are coarse scopes (a whole calendar/repo/"
        "channel), not per-event/per-file instances."
    )
    return "\n\n".join(parts)


def run_critic(critic: Critic, digest: str | None = None) -> dict:
    """Run one critic against the evidence; return its structured critique."""
    prompt = CRITIC_SYSTEM.format(persona=critic.persona, name=critic.name) + "\n\n" + \
        CRITIC_USER.format(digest=digest if digest is not None else _digest())
    result = query_ollama(prompt)
    if not isinstance(result, dict) or "critiques" not in result:
        return {"persona": critic.name, "headline": "(no usable answer from model)",
                "critiques": [], "key": critic.key}
    result["key"] = critic.key
    return result


def run_panel(critics: tuple[Critic, ...] = CRITICS) -> list[dict]:
    """Run every critic over a shared evidence digest; return one record each."""
    digest = _digest()
    return [run_critic(c, digest) for c in critics]


_SEV = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def to_markdown(records: list[dict]) -> str:
    """Render the panel's critiques, grouped by persona, worst-first within each."""
    n = sum(len(r.get("critiques", [])) for r in records)
    sev_counts: Counter = Counter(
        c.get("severity", "?") for r in records for c in r.get("critiques", []))
    lines = [
        "# Persona-critic panel",
        "",
        "Five opinionated LLM reviewers, each with a different personality and lens, "
        "told to find what is weak. Their critiques are the raw material for the "
        "improvement plan.",
        "",
        f"**{len(records)} critics · {n} critiques** "
        f"({', '.join(f'{k}:{v}' for k, v in sorted(sev_counts.items(), key=lambda x: _SEV.get(x[0], 9)))})",
        "",
    ]
    for r in records:
        lines += [f"## {r.get('persona', '?')}", "", f"> {r.get('headline', '')}", ""]
        for c in sorted(r.get("critiques", []), key=lambda c: _SEV.get(c.get("severity"), 9)):
            lines += [
                f"- **[{c.get('severity', '?')}] {c.get('issue', '')}**",
                f"    - *why:* {c.get('why_it_matters', '')}",
                f"    - *fix:* {c.get('concrete_fix', '')}",
            ]
        lines.append("")
    return "\n".join(lines)
