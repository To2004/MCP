"""Give every v5r arm folder a README that states exactly what that arm changes.

The four long documents -- ``README.md``, ``STATIC_RULES.md``, ``PROMPT_ROLES.md``
and ``GROUNDING.md`` -- describe the v5r method and are shared by every arm; they
live once at ``reports/experiments/v5/``. Copying ~1000 lines into thirteen
folders would guarantee they drift apart. Instead each arm folder gets a short
README that links to those four and spells out its own delta.

The delta is read out of ``_ULT_VARIANT_OPTIONS`` rather than written by hand, so
it cannot disagree with the configuration the scan actually ran under.

Run:  uv run python scripts/write_arm_readmes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mcp_security.static_scoring.pipeline import _ULT_VARIANT_OPTIONS  # noqa: E402

V5 = REPO_ROOT / "reports" / "experiments" / "v5"
BASE_MODE = "five_level_v2_v5r"
SHARED_DOCS = ("README.md", "STATIC_RULES.md", "PROMPT_ROLES.md", "GROUNDING.md")

# What each option value means, in the words the arm was asked for.
OPTION_PROSE: dict[tuple[str, object], str] = {
    ("asset_flags", "none"): "the register's `Flags` column is withheld — the model reads the "
    "tool's own parameters and the policy prose instead",
    ("asset_flags", "key"): "only the flags judged important are shown; the rest are withheld",
    ("blast_prompt", "selfassess"): "the blast prompt asks the flag *concepts* as questions "
    "(hub? population? self-sufficient?) without ever naming a flag",
    ("blast_prompt", "scope"): "blast is a scope ladder — 2 one group, 3 several groups, "
    "4 org-wide, 5 beyond the org",
    ("floors", "low"): "the sensitivity/impact floors are each lowered by one, and anything "
    "that would land below 3 is dropped",
    ("floors", "none"): "no floors at all — sensitivity never pushes blast up, so the two "
    "primitives stay independent",
    ("relevance", "register"): "a tool×asset pair is scored only when the policy register homes "
    "that tool on that asset",
    ("relevance", "prompt"): "the prompt itself asks whether the pair is reachable, and N/A is "
    "framed as a lower-severity problem rather than no problem",
    ("relevance", "none"): "no relevance gate — every pair is scored",
    ("relevance", "combo"): "register homing *and* the prompt's own reachability question, with "
    "N/A framed as a lower-severity problem that is still a problem",
    ("two_stage_framing", True): "the model is told it is the static stage and a dynamic scanner "
    "runs later, so it should give the direction rather than the last word",
    ("sens_scheme", "iso"): "asset sensitivity is derived through ISO/IEC 27001 A.5.12's four "
    "criteria (legal requirements, value, criticality, sensitivity to disclosure or modification)",
    ("sens_scheme", "nist"): "asset sensitivity is derived through the FIPS 199 / SP 800-60 "
    "confidentiality–integrity–availability triple, reduced by high-water mark",
    ("sens_scheme", "cis"): "the org is assumed to publish only a coarse scheme, which the model "
    "must refine — a coarse scheme is not a licence to score low",
}


def arm_modes() -> dict[str, dict[str, object]]:
    """Every v5r arm mode, keyed by the short arm name."""
    return {
        mode.removeprefix(f"{BASE_MODE}_"): options
        for mode, options in _ULT_VARIANT_OPTIONS.items()
        if mode.startswith(f"{BASE_MODE}_")
    }


def render(arm: str, options: dict[str, object], base: dict[str, object]) -> str:
    """The arm's README: its delta from v5r, its lineage, and links to the shared docs."""
    delta = {key: value for key, value in options.items() if base.get(key) != value}
    lines = [
        f"# v5r · `{arm}` arm",
        "",
        f"Impact mode `{BASE_MODE}_{arm}`. Everything about the method — the scoring formula, "
        "the static impact ladder, what each prompt is for, and the standards the rubrics are "
        "grounded in — is shared with every other arm and documented once, one level up:",
        "",
    ]
    lines += [f"- [`../{doc}`](../{doc})" for doc in SHARED_DOCS]
    lines += [
        "",
        "The prompts **as this arm actually ran them** are in "
        "[`scoring-prompts-AS-RUN.md`](scoring-prompts-AS-RUN.md) in this folder.",
        "",
        "## What this arm changes",
        "",
    ]
    if not delta:
        lines.append("Nothing — this is the v5r baseline.")
    else:
        lines += ["| option | value | what it means |", "|---|---|---|"]
        for key, value in delta.items():
            prose = OPTION_PROSE.get((key, value), "—")
            lines.append(f"| `{key}` | `{value}` | {prose} |")
    lines += [
        "",
        "## Contents",
        "",
        "| file | what it holds |",
        "|---|---|",
        "| `<server>.json` | the full artifact: every primitive, its reasoning, and its provenance |",
        "| `<server>.md` | the same scan as a readable report |",
        "| `<server>_matrix.csv` | the tool × asset score matrix |",
        "| `scoring-prompts-AS-RUN.md` | every prompt this arm sent, rendered |",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    modes = arm_modes()
    base = _ULT_VARIANT_OPTIONS[BASE_MODE]
    written = 0
    for arm, options in sorted(modes.items()):
        folder = V5 / f"five_level_v2_policy_v5r_{arm}"
        if not folder.is_dir():
            print(f"  (no folder for arm {arm!r}; skipped)")
            continue
        # The no-flags arm has a hand-written review package README; keep it.
        target = folder / "README.md"
        if arm == "noflags" and target.exists():
            print(f"  (kept hand-written README for {arm!r})")
            continue
        target.write_text(render(arm, options, base), encoding="utf-8")
        written += 1
        print(f"[ok] {target.relative_to(REPO_ROOT)}")
    print(f"\n{written} arm README(s) written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
