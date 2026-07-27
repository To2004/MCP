"""Dump the static-scoring LLM prompts to a reviewable markdown file.

Regenerates a reviewable copy of the exact prompt templates the pipeline sends to
the model, from :mod:`mcp_security.static_scoring.prompts`, so the copy never
drifts from what actually runs.

The tool-impact stage differs per EXPERIMENT (``--impact-mode``); everything else
(domain inference, sensitivity, coverage blast, baseline) is shared. So each
experiment's prompt set is exactly: the shared stages + that mode's impact prompt.

    uv run python scripts/dump_scoring_prompts.py                       # baseline -> docs/
    uv run python scripts/dump_scoring_prompts.py --impact-mode five_level \\
        --out reports/experiments/five_level/scoring-prompts.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mcp_security.static_scoring import prompts

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "docs" / "standards" / "scoring-prompts.md"

# The impact stage(s) per experiment mode — a list of (attr, title, note). CIA has
# TWO: the baseline impact prompt (unchanged) plus a separate CIA-flags prompt.
_IMPACT_SECTIONS = {
    "baseline": [
        ("TOOL_IMPACT_TASK", "1 · Tool impact — task",
         "BASELINE: 1-3 damage-ceiling rubric (read / recoverable write / destructive). "
         "score_max = 75."),
        ("TOOL_IMPACT_USER", "1 · Tool impact — return schema", ""),
    ],
    "five_level": [
        ("TOOL_IMPACT_TASK_5LEVEL", "1 · Tool impact — task",
         "EXPERIMENT A: a 5-level action×coverage ladder (1 metadata · 2 read-one · "
         "3 read-all/edit-one · 4 write-all · 5 delete-all). score_max = 125."),
        ("TOOL_IMPACT_USER_5LEVEL", "1 · Tool impact — return schema", ""),
    ],
    "five_level_v2": [
        ("TOOL_IMPACT_TASK_5LEVEL_V2", "1 · Tool impact — task",
         "EXPERIMENT A2: a 5-level action-type ladder (1 no-op/ping · 2 metadata · "
         "3 read · 4 write/edit · 5 delete). score_max = 125."),
        ("TOOL_IMPACT_USER_5LEVEL", "1 · Tool impact — return schema", ""),
    ],
    "five_level_v2_na": [
        ("TOOL_IMPACT_TASK_5LEVEL_V2", "1 · Tool impact — task",
         "EXPERIMENT A2+N/A: generalized 5-level action ladder (1 liveness/ping · "
         "2 metadata · 3 read/observe · 4 write/modify incl. move · 5 delete/destroy). "
         "The blast stage also marks pairs the tool does not affect as N/A. score_max = 125."),
        ("TOOL_IMPACT_USER_5LEVEL", "1 · Tool impact — return schema", ""),
    ],
    "cia": [
        ("TOOL_IMPACT_TASK", "1 · Tool impact — BASE task (identical to baseline)",
         "EXPERIMENT B base: the UNCHANGED 1-3 baseline rubric, scored in its OWN call "
         "so the base equals the baseline experiment exactly."),
        ("TOOL_IMPACT_USER", "1 · Tool impact — BASE return schema", ""),
        ("CIA_FLAGS_TASK", "1b · CIA-triad flags — task (SEPARATE call)",
         "Final impact = base + one point per violated objective (C/I/A). score_max = 150."),
        ("CIA_FLAGS_USER", "1b · CIA-triad flags — return schema", ""),
    ],
    "hybrid": [
        ("TOOL_IMPACT_TASK_HYBRID", "1 · Tool impact — task",
         "EXPERIMENT HYBRID: action-type only (1 metadata/no-op · 2 content read · "
         "3 create/scoped write · 4 destructive/admin/external-send · 5 mass-destructive); "
         "coverage lives in blast. Formula = sens×5×√(blast×impact), score_max = 125."),
        ("TOOL_IMPACT_USER_HYBRID", "1 · Tool impact — return schema", ""),
    ],
    "hybrid_na": [
        ("TOOL_IMPACT_TASK_HYBRID", "1 · Tool impact — task",
         "EXPERIMENT HYBRID+N/A: same action-type impact as hybrid; the blast stage "
         "additionally marks pairs the tool does not affect as N/A (not scored)."),
        ("TOOL_IMPACT_USER_HYBRID", "1 · Tool impact — return schema", ""),
    ],
}

# Blast task/schema per mode. hybrid uses reach-of-consequences; hybrid_na adds N/A.
_BLAST_ATTR = {
    "hybrid": "BLAST_TASK_CONSEQUENCES",
    "hybrid_na": "BLAST_TASK_CONSEQUENCES_NA",
    "five_level_v2_na": "BLAST_TASK_NA",
}
_BLAST_USER_ATTR = {"hybrid_na": "BLAST_USER_NA", "five_level_v2_na": "BLAST_USER_NA"}


def _sections(impact_mode: str) -> list[tuple[str, str, str]]:
    """Shared stages + the impact stage(s) selected by ``impact_mode``."""
    return [
        ("DOMAIN_INFERENCE_SYSTEM", "0 · Domain inference (system)",
         "Runs once over the whole registry. Infers mcp_kind (plus content_unit / "
         "contents_definition) and defines what the primitives mean HERE."),
        ("DOMAIN_INFERENCE_USER", "0 · Domain inference (user)",
         "Carries the tool registry and a sample of asset classes into the stage above."),
        ("_PROPOSER_BASE", "Shared proposer preamble",
         "Prepended to every primitive stage; injects the inferred domain profile."),
        *_IMPACT_SECTIONS[impact_mode],
        ("ASSET_TASK", "2 · Asset sensitivity (1-5) — task",
         "Criticality of the asset by what it CHARACTERISTICALLY holds (absolute scale)."),
        ("ASSET_USER", "2 · Asset sensitivity — return schema", ""),
        (_BLAST_ATTR.get(impact_mode, "BLAST_TASK"), "3 · Blast radius (1-5) — task",
         "Reach of ONE call: coverage of the asset (items, subjects, and — via the "
         "dependency_hub / dangerous_class traits — fallout that escapes it). N/A modes "
         "also mark pairs the tool does not act on as N/A (not scored)."),
        (_BLAST_USER_ATTR.get(impact_mode, "BLAST_USER"), "3 · Blast radius — return schema", ""),
        ("BASELINE_TASK", "4 · Behavioral baseline — task",
         "Per-application expected/normal operations, so runtime deviation can be measured."),
        ("BASELINE_USER", "4 · Behavioral baseline — return schema", ""),
        ("JUDGE_SYSTEM", "Judge (system) — evaluation only",
         "NOT run in a production scan; measures independent-reviewer agreement only."),
        ("JUDGE_USER", "Judge (user) — evaluation only",
         "Carries the item into the blinded judge; the proposer's answer is withheld."),
    ]


def _header(impact_mode: str) -> str:
    max_ = {"baseline": 75, "five_level": 125, "five_level_v2": 125, "five_level_v2_na": 125,
            "cia": 150, "hybrid": 125, "hybrid_na": 125}[impact_mode]
    # hybrid/hybrid_na use the geometric-mean formula; every other mode uses the
    # plain product. Render whichever THIS mode actually scores with, so the header
    # can never disagree with the pipeline.
    sqrt_modes = {"hybrid", "hybrid_na"}
    formula = (
        "score = asset_sensitivity × 5 × √(blast_radius × tool_impact)"
        if impact_mode in sqrt_modes
        else "score = asset_sensitivity × blast_radius × likelihood(1.0) × tool_impact"
    )
    return (
        f"# Static-scoring prompts — experiment `{impact_mode}`\n\n"
        "Every prompt this experiment's scan sent to the local LLM, verbatim from "
        "`src/mcp_security/static_scoring/prompts.py`. Generated -- do not hand-edit; "
        "edit the templates and re-run `scripts/dump_scoring_prompts.py`.\n\n"
        f"Risk formula: `{formula}`, score_max = {max_}. The **tool-impact** and "
        "**blast** stages vary by experiment; asset sensitivity is shared.\n"
    )


def build_markdown(impact_mode: str) -> str:
    """Render this experiment's prompt templates into one reviewable markdown doc."""
    parts = [_header(impact_mode)]
    for attr, title, note in _sections(impact_mode):
        template = getattr(prompts, attr)
        body = f"{note}\n\n" if note else ""
        parts.append(f"## {title}\n\n{body}```text\n{template.strip()}\n```\n")
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--impact-mode", default="baseline", choices=list(_IMPACT_SECTIONS))
    parser.add_argument("--out", type=Path, default=None, help="output path (default: docs/)")
    args = parser.parse_args(argv)
    out = args.out or DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_markdown(args.impact_mode), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
