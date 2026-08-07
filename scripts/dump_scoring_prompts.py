"""Dump the static-scoring LLM prompts to a reviewable markdown file.

Regenerates a reviewable copy of the exact prompt templates the pipeline sends to
the model, from :mod:`mcp_security.static_scoring.prompts`, so the copy never
drifts from what actually runs.

The tool-impact stage differs per EXPERIMENT (``--impact-mode``); everything else
(domain inference, sensitivity, coverage blast, baseline) is shared. So each
experiment's prompt set is exactly: the shared stages + that mode's impact prompt.

``--org-desc`` swaps the two stages that change when the registry carries an
organizational description (a profile or a policy): the domain-inference user
message and the proposer preamble, both of which then carry that text into every
stage — which is exactly how the policy reaches the sensitivity decision.

    uv run python scripts/dump_scoring_prompts.py                       # baseline -> docs/
    uv run python scripts/dump_scoring_prompts.py --impact-mode five_level \\
        --out reports/experiments/five_level/scoring-prompts.md
    uv run python scripts/dump_scoring_prompts.py --impact-mode five_level_v2_na \\
        --org-desc --out reports/experiments/staticscanner/scoring-prompts.md
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
        (
            "TOOL_IMPACT_TASK",
            "1 · Tool impact — task",
            "BASELINE: 1-3 damage-ceiling rubric (read / recoverable write / destructive). "
            "score_max = 75.",
        ),
        ("TOOL_IMPACT_USER", "1 · Tool impact — return schema", ""),
    ],
    "five_level": [
        (
            "TOOL_IMPACT_TASK_5LEVEL",
            "1 · Tool impact — task",
            "EXPERIMENT A: a 5-level action×coverage ladder (1 metadata · 2 read-one · "
            "3 read-all/edit-one · 4 write-all · 5 delete-all). score_max = 125.",
        ),
        ("TOOL_IMPACT_USER_5LEVEL", "1 · Tool impact — return schema", ""),
    ],
    "five_level_v2": [
        (
            "TOOL_IMPACT_TASK_5LEVEL_V2",
            "1 · Tool impact — task",
            "EXPERIMENT A2: a 5-level action-type ladder (1 no-op/ping · 2 metadata · "
            "3 read · 4 write/edit · 5 delete). score_max = 125.",
        ),
        ("TOOL_IMPACT_USER_5LEVEL", "1 · Tool impact — return schema", ""),
    ],
    "five_level_v2_na": [
        (
            "TOOL_IMPACT_TASK_5LEVEL_V2",
            "1 · Tool impact — task",
            "EXPERIMENT A2+N/A: generalized 5-level action ladder (1 liveness/ping · "
            "2 metadata · 3 read/observe · 4 write/modify incl. move · 5 delete/destroy). "
            "The blast stage also marks pairs the tool does not affect as N/A. score_max = 125.",
        ),
        ("TOOL_IMPACT_USER_5LEVEL", "1 · Tool impact — return schema", ""),
    ],
    "five_level_v2_ctx": [
        (
            "TOOL_IMPACT_TASK_5LEVEL_V2",
            "1 · Tool impact — task",
            "EXPERIMENT CTX: same generalized 5-level ladder + N/A as five_level_v2_na; "
            "a per-tool UNDERSTANDING stage runs before blast and its profile is injected "
            "into every blast decision for that tool. score_max = 125.",
        ),
        ("TOOL_IMPACT_USER_5LEVEL", "1 · Tool impact — return schema", ""),
        (
            "TOOL_CONTEXT_TASK",
            "2.5 · Tool understanding — task (ctx only)",
            "Runs once per tool: role in this MCP, single-call reach, consequence "
            "carriers, worst realistic misuse. Not a scoring stage.",
        ),
        ("TOOL_CONTEXT_USER", "2.5 · Tool understanding — return schema", ""),
    ],
    "five_level_v2_ult": [
        (
            "TOOL_IMPACT_TASK_5LEVEL_V3",
            "1 · Tool impact — task",
            "EXPERIMENT ULT (also the `pure` run): generalized 5-level ladder + N/A. "
            "Sensitivity is NOT an LLM stage — it comes from the org profile's per-asset "
            "table. Deterministic assembly adds the alias-twin pass, the gated blast "
            "floor, and band_label_v5. score_max = 125.",
        ),
        ("TOOL_IMPACT_USER_5LEVEL", "1 · Tool impact — return schema", ""),
        (
            "DOMAIN_INFERENCE_USER_DESC",
            "0b · Domain inference user (desc variant — used here)",
            "Replaces the plain domain-inference user message: the org's written profile "
            "is authoritative for context; the registry for capability.",
        ),
        (
            "_PROPOSER_BASE_DESC",
            "Shared proposer preamble (desc variant — used here)",
            "Replaces the plain preamble on every stage: org description (authoritative "
            "for IMPORTANCE) + inferred profile (authoritative for CAPABILITY).",
        ),
    ],
    "five_level_v2_v4": [
        (
            "TOOL_IMPACT_TASK_V4",
            "1 · Tool impact — task",
            "EXPERIMENT V4: the short standards-grounded ladder (MCP annotation "
            "vocabulary + CVSS integrity/availability loss). Sent BARE — no proposer "
            "preamble, no org profile, no inferred domain: impact is a property of the "
            "action alone. Sensitivity comes from the org profile's table, not an LLM "
            "stage. score_max = 125.",
        ),
        ("TOOL_IMPACT_USER_V4", "1 · Tool impact — return schema", ""),
    ],
    "five_level_v2_v4_static": [
        (
            "TOOL_IMPACT_TASK_V4",
            "1 · Tool impact — NOT SENT in this arm (shown for reference)",
            "EXPERIMENT V4-STATIC: tool impact is computed DETERMINISTICALLY by "
            "`src/mcp_security/static_scoring/static_impact.py` — the ladder below "
            "expressed as rules — so no impact prompt reaches the model at all. The text "
            "is reproduced here because the rules implement it.",
        ),
    ],
    "five_level_v2_v5": [
        (
            "TOOL_IMPACT_TASK_V4",
            "1 · Tool impact — FALLBACK ONLY",
            "EXPERIMENT V5: tool impact is the deterministic ladder "
            "(`static_impact.py`) FIRST. This prompt is sent only for a tool where the "
            "ladder abstains — no tier verb matched, so it would have had to use its "
            "default (static confidence < 0.5). Sent bare, exactly as in v4.",
        ),
        ("TOOL_IMPACT_USER_V4", "1 · Tool impact — return schema (fallback only)", ""),
    ],
    "five_level_v2_v5r": [
        (
            "TOOL_IMPACT_TASK_V5R",
            "1 · Tool impact — FALLBACK ONLY (operation-type ladder)",
            "EXPERIMENT V5R: impact is the deterministic ladder in static_impact."
            "classify_by_operation() FIRST — read / write / remove, with scoped writes "
            "sharing tier 3 with content reads. This prompt is sent only where the rules "
            "abstain. Open-world left the ladder (a channel is not an operation) and "
            "annotation hints no longer bound anything.",
        ),
    ],
    "cia": [
        (
            "TOOL_IMPACT_TASK",
            "1 · Tool impact — BASE task (identical to baseline)",
            "EXPERIMENT B base: the UNCHANGED 1-3 baseline rubric, scored in its OWN call "
            "so the base equals the baseline experiment exactly.",
        ),
        ("TOOL_IMPACT_USER", "1 · Tool impact — BASE return schema", ""),
        (
            "CIA_FLAGS_TASK",
            "1b · CIA-triad flags — task (SEPARATE call)",
            "Final impact = base + one point per violated objective (C/I/A). score_max = 150.",
        ),
        ("CIA_FLAGS_USER", "1b · CIA-triad flags — return schema", ""),
    ],
    "hybrid": [
        (
            "TOOL_IMPACT_TASK_HYBRID",
            "1 · Tool impact — task",
            "EXPERIMENT HYBRID: action-type only (1 metadata/no-op · 2 content read · "
            "3 create/scoped write · 4 destructive/admin/external-send · 5 mass-destructive); "
            "coverage lives in blast. Formula = sens×5×√(blast×impact), score_max = 125.",
        ),
        ("TOOL_IMPACT_USER_HYBRID", "1 · Tool impact — return schema", ""),
    ],
    "hybrid_na": [
        (
            "TOOL_IMPACT_TASK_HYBRID",
            "1 · Tool impact — task",
            "EXPERIMENT HYBRID+N/A: same action-type impact as hybrid; the blast stage "
            "additionally marks pairs the tool does not affect as N/A (not scored).",
        ),
        ("TOOL_IMPACT_USER_HYBRID", "1 · Tool impact — return schema", ""),
    ],
}

# Blast task/schema per mode. hybrid uses reach-of-consequences; hybrid_na adds N/A.
_BLAST_ATTR = {
    "hybrid": "BLAST_TASK_CONSEQUENCES",
    "hybrid_na": "BLAST_TASK_CONSEQUENCES_NA",
    "five_level_v2_na": "BLAST_TASK_NA",
    "five_level_v2_ctx": "BLAST_TASK_NA",
    "five_level_v2_ult": "BLAST_TASK_NA_PROFILE_V3",
    "five_level_v2_v4": "BLAST_TASK_V4",
    "five_level_v2_v4_static": "BLAST_TASK_V4",
    "five_level_v2_v5": "BLAST_TASK_V5",
    "five_level_v2_v5r": "BLAST_TASK_V5R_FLOORED",
    "five_level_v2_v5r_keyflags": "BLAST_TASK_V5R_FLOORED",
    "five_level_v2_v5r_noflags": "BLAST_TASK_V5R_NOFLAGS_FLOORED",
    "five_level_v2_v5r_selfassess": "BLAST_TASK_V5R_SELFASSESS_FLOORED",
    "five_level_v2_v5r_twostage": "BLAST_TASK_V5R_SELFASSESS_TWOSTAGE",
    "five_level_v2_v5r_lowfloor": "BLAST_TASK_V5R_SELFASSESS_LOWFLOOR",
    "five_level_v2_v5r_scope": "BLAST_TASK_V5R_SCOPE",
    "five_level_v2_v5r_naregister": "BLAST_TASK_V5R_SCOPE_NAREGISTER",
    "five_level_v2_v5r_naprompt": "BLAST_TASK_V5R_SCOPE_NAPROMPT",
    "five_level_v2_v5r_nona": "BLAST_TASK_V5R_SCOPE_NONA",
    "five_level_v2_v5r_nacombo": "BLAST_TASK_V5R_SCOPE_NACOMBO",
    "five_level_v2_v5r_senscis": "BLAST_TASK_V5R_SCOPE_NACOMBO",
    "five_level_v2_v5r_sensnist": "BLAST_TASK_V5R_SCOPE_NACOMBO",
    "five_level_v2_v5r_sensiso": "BLAST_TASK_V5R_SCOPE_NACOMBO",
}
_BLAST_USER_ATTR = {
    "hybrid_na": "BLAST_USER_NA",
    "five_level_v2_na": "BLAST_USER_NA",
    "five_level_v2_ctx": "BLAST_USER_NA_CTX",
    "five_level_v2_ult": "BLAST_USER_NA",
    "five_level_v2_v4": "BLAST_USER_V4",
    "five_level_v2_v4_static": "BLAST_USER_V4",
    "five_level_v2_v5": "BLAST_USER_V4",
    "five_level_v2_v5r": "BLAST_USER_V5R",
    "five_level_v2_v5r_keyflags": "BLAST_USER_V5R",
    "five_level_v2_v5r_noflags": "BLAST_USER_V5R_NOFLAGS",
    "five_level_v2_v5r_selfassess": "BLAST_USER_V5R_SELFASSESS",
    "five_level_v2_v5r_twostage": "BLAST_USER_V5R_SELFASSESS",
    "five_level_v2_v5r_lowfloor": "BLAST_USER_V5R_SELFASSESS",
    "five_level_v2_v5r_scope": "BLAST_USER_V5R_SCOPE",
    "five_level_v2_v5r_naregister": "BLAST_USER_V5R_SCOPE",
    "five_level_v2_v5r_naprompt": "BLAST_USER_V5R_SCOPE_NAPROMPT",
    "five_level_v2_v5r_nona": "BLAST_USER_V5R_SCOPE",
    "five_level_v2_v5r_nacombo": "BLAST_USER_V5R_SCOPE_NACOMBO",
    "five_level_v2_v5r_senscis": "BLAST_USER_V5R_SCOPE_NACOMBO",
    "five_level_v2_v5r_sensnist": "BLAST_USER_V5R_SCOPE_NACOMBO",
    "five_level_v2_v5r_sensiso": "BLAST_USER_V5R_SCOPE_NACOMBO",
}
# Modes whose sensitivity comes from the org's own table, so no LLM stage exists.
_PROFILE_SENS = {"five_level_v2_v4", "five_level_v2_v4_static"}
# Modes that removed the evaluation-only judge from the scan path.
_NO_JUDGE = _PROFILE_SENS | {
    "five_level_v2_v5",
    "five_level_v2_v5r",
    "five_level_v2_v5r_keyflags",
    "five_level_v2_v5r_noflags",
    "five_level_v2_v5r_selfassess",
    "five_level_v2_v5r_twostage",
}


# Arms whose SENSITIVITY stage speaks a named classification scheme rather than
# the generic classify-then-map prompt.
_SENS_ATTR = {
    "five_level_v2_v5r_sensiso": "ASSET_TASK_POLICY_ISO",
    "five_level_v2_v5r_sensnist": "ASSET_TASK_POLICY_NIST",
    "five_level_v2_v5r_senscis": "ASSET_TASK_POLICY_CIS",
}

_V5R_VARIANTS = (
    "five_level_v2_v5r_keyflags",
    "five_level_v2_v5r_noflags",
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
)


def _normalize(impact_mode: str) -> str:
    """Ult variant arms share the ult prompt set; v4/v5 arms keep their own."""
    if impact_mode.startswith("five_level_v2_ult"):
        return "five_level_v2_ult"
    if impact_mode in _V5R_VARIANTS:
        return "five_level_v2_v5r"
    return impact_mode


def _profile_sens(impact_mode: str) -> bool:
    """True when the org supplies the sensitivity number, so no LLM stage runs."""
    return impact_mode.startswith("five_level_v2_ult") or impact_mode in _PROFILE_SENS


def _judge_runs(impact_mode: str) -> bool:
    return not (impact_mode.startswith("five_level_v2_ult") or impact_mode in _NO_JUDGE)


def _sections(impact_mode: str, *, org_desc: bool = False) -> list[tuple[str, str, str]]:
    """Shared stages + the impact stage(s) selected by ``impact_mode``.

    ``org_desc`` renders the variants used when the registry carries an
    organizational description: the domain-inference user message and the
    proposer preamble both carry that text, so every downstream stage sees it.
    """
    impact_mode_key = _normalize(impact_mode)
    # The ult modes already declare their own desc variants in _IMPACT_SECTIONS.
    desc = org_desc and not impact_mode.startswith("five_level_v2_ult")
    return [
        (
            "DOMAIN_INFERENCE_SYSTEM_V5R" if impact_mode.startswith("five_level_v2_v5r")
            else "DOMAIN_INFERENCE_SYSTEM",
            "0 · Domain inference (system)",
            "Runs once over the whole registry. Infers mcp_kind (plus content_unit / "
            "contents_definition) and defines what the primitives mean HERE.",
        ),
        (
            "DOMAIN_INFERENCE_USER_V5R"
            if impact_mode.startswith("five_level_v2_v5r")
            else "DOMAIN_INFERENCE_USER_DESC" if desc else "DOMAIN_INFERENCE_USER",
            "0 · Domain inference (user)",
            "Carries the org's description, the tool registry and a sample of asset "
            "classes into the stage above."
            if desc
            else "Carries the tool registry and a sample of asset classes into the stage above.",
        ),
        (
            "_PROPOSER_BASE_DESC" if desc else "_PROPOSER_BASE",
            "Shared proposer preamble",
            "Prepended to every primitive stage — impact, SENSITIVITY, blast, baselines. "
            "Injects the org's description (authoritative for IMPORTANCE) alongside the "
            "inferred domain profile (authoritative for CAPABILITY)."
            if desc
            else "Prepended to every primitive stage; injects the inferred domain profile.",
        ),
        *_IMPACT_SECTIONS[impact_mode_key],
        *(
            []  # ult/v4: sensitivity comes from the org table — no LLM stage exists
            if _profile_sens(impact_mode)
            else [
                (
                    _SENS_ATTR.get(impact_mode)
                    or (
                        "ASSET_TASK_POLICY_V5R"
                        if impact_mode.startswith("five_level_v2_v5r")
                        else "ASSET_TASK_POLICY" if desc else "ASSET_TASK"
                    ),
                    "2 · Asset sensitivity (1-5) — task",
                    "CLASSIFY the asset against the org policy (register → recognition "
                    "rules → default class), then MAP that class's adverse-impact "
                    "definition onto the absolute 1-5 scale."
                    if desc
                    else "Criticality of the asset by what it CHARACTERISTICALLY holds "
                    "(absolute scale).",
                ),
                (
                    "ASSET_USER_POLICY" if desc else "ASSET_USER",
                    "2 · Asset sensitivity — return schema",
                    "",
                ),
            ]
        ),
        (
            # blast differs BETWEEN the v5r variants, so look it up by the raw
            # mode first; the normalized key only covers the shared families.
            _BLAST_ATTR.get(impact_mode, _BLAST_ATTR.get(impact_mode_key, "BLAST_TASK")),
            "3 · Blast radius (1-5) — task",
            "Reach of ONE call: coverage of the asset (items, subjects, and — via the "
            "dependency_hub / dangerous_class traits — fallout that escapes it). N/A modes "
            "also mark pairs the tool does not act on as N/A (not scored).",
        ),
        (
            _BLAST_USER_ATTR.get(
                impact_mode, _BLAST_USER_ATTR.get(impact_mode_key, "BLAST_USER")
            ),
            "3 · Blast radius — return schema",
            "",
        ),
        *(
            []  # v5r: the behavioral baseline is a RUNTIME primitive and moved to
            # the dynamic stage; no static cell consumes it.
            if impact_mode.startswith("five_level_v2_v5r")
            else [
                (
                    "BASELINE_TASK",
                    "4 · Behavioral baseline — task",
                    "Per-application expected/normal operations, so runtime deviation can "
                    "be measured.",
                ),
                ("BASELINE_USER", "4 · Behavioral baseline — return schema", ""),
            ]
        ),
        *(
            []  # ult/v4/v5: the evaluation-only judge is removed from these runs
            if not _judge_runs(impact_mode)
            else [
                (
                    "JUDGE_SYSTEM",
                    "Judge (system) — evaluation only",
                    "NOT run in a production scan; measures independent-reviewer agreement only.",
                ),
                (
                    "JUDGE_USER",
                    "Judge (user) — evaluation only",
                    "Carries the item into the blinded judge; the proposer's answer is withheld.",
                ),
            ]
        ),
    ]


def _header(impact_mode: str, *, org_desc: bool = False) -> str:
    max_ = {
        "baseline": 75,
        "five_level": 125,
        "five_level_v2": 125,
        "five_level_v2_na": 125,
        "cia": 150,
        "hybrid": 125,
        "hybrid_na": 125,
        "five_level_v2_ctx": 125,
        "five_level_v2_ult": 125,
        "five_level_v2_v4": 125,
        "five_level_v2_v4_static": 125,
        "five_level_v2_v5": 125,
        "five_level_v2_v5r_keyflags": 125,
    "five_level_v2_v5r_noflags": 125,
    "five_level_v2_v5r_twostage": 125,
    "five_level_v2_v5r_lowfloor": 125,
    "five_level_v2_v5r_selfassess": 125,
    "five_level_v2_v5r": 125,
    }[_normalize(impact_mode)]
    # hybrid/hybrid_na use the geometric-mean formula; every other mode uses the
    # plain product. Render whichever THIS mode actually scores with, so the header
    # can never disagree with the pipeline.
    sqrt_modes = {"hybrid", "hybrid_na"}
    formula = (
        "score = asset_sensitivity × 5 × √(blast_radius × tool_impact)"
        if impact_mode in sqrt_modes
        else "score = asset_sensitivity × blast_radius × likelihood(1.0) × tool_impact"
    )
    desc_note = (
        "\n\nThis run carries an **organizational description** (a profile or a policy) "
        "in the registry, so the domain-inference user message and the shared proposer "
        "preamble below are their `_DESC` variants: the org's text is placed in front of "
        "EVERY stage, including asset sensitivity. `{org_description}` is where that "
        "document's section for the scanned server is substituted verbatim.\n"
        if org_desc
        else ""
    )
    return (
        f"# Static-scoring prompts — experiment `{impact_mode}`"
        f"{' (with org description)' if org_desc else ''}\n\n"
        "Every prompt this experiment's scan sent to the local LLM, verbatim from "
        "`src/mcp_security/static_scoring/prompts.py`. Generated -- do not hand-edit; "
        "edit the templates and re-run `scripts/dump_scoring_prompts.py`.\n\n"
        f"Risk formula: `{formula}`, score_max = {max_}. The **tool-impact** and "
        f"**blast** stages vary by experiment; asset sensitivity is shared.{desc_note}\n"
    )


def build_markdown(impact_mode: str, *, org_desc: bool = False) -> str:
    """Render this experiment's prompt templates into one reviewable markdown doc."""
    parts = [_header(impact_mode, org_desc=org_desc)]
    for attr, title, note in _sections(impact_mode, org_desc=org_desc):
        template = getattr(prompts, attr)
        body = f"{note}\n\n" if note else ""
        parts.append(f"## {title}\n\n{body}```text\n{template.strip()}\n```\n")
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--impact-mode",
        default="baseline",
        choices=list(_IMPACT_SECTIONS)
        + list(_V5R_VARIANTS)
        + ["five_level_v2_ult_imponly", "five_level_v2_ult_nodom"],
    )
    parser.add_argument("--out", type=Path, default=None, help="output path (default: docs/)")
    parser.add_argument(
        "--org-desc", action="store_true",
        help="render the variants used when the registry carries an org description "
             "(profile or policy): desc domain-inference user + desc proposer preamble",
    )
    args = parser.parse_args(argv)
    out = args.out or DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_markdown(args.impact_mode, org_desc=args.org_desc), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
