"""Render a run's input rules as the five levels of every kept input (v12 and v13).

One row per kept input: what the rule reads in the value, which values land on
each level from 1 to 5, what happens when the input is left out, and where the
levels come from:

- ``scan``: an asset's 1 to 5 sensitivity from the v5 scan, which is what a
  ``register`` rule returns for a value that names that asset;
- ``policy``: the organization's policy (v12: a baseline row, a special-value
  rule; v13: the address lists the ``email`` ladder reads);
- ``schema``: bounds the tool's own schema states (v12 only);
- ``agent``: the model's own judgement (v12 calls it ``inferred``).

A rule records one source, so every level of a non-``register`` row shares it.

Usage::

    python3 scripts/render_input_rule_levels.py --run reports/experiments/v13/run1
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_security.input_rules import register_table  # noqa: E402

LEVELS = (1, 2, 3, 4, 5)
LEVEL_NAMES = {1: "1 safest", 2: "2 safe", 3: "3 ordinary", 4: "4 high", 5: "5 critical"}
OUTPUT_NAME = "rule-levels.md"
EMPTY_CELL = "–"
#: stage 2 ``source`` value -> the wording shown in the table
SOURCE_LABELS = {
    "policy": "policy",
    "register": "policy",
    "schema": "schema",
    "inferred": "agent",
    "": "agent",  # v13 rows carry no source: everything but asset levels is the agent's
}
#: The ``email`` kind's fixed ladder (``mcp_security.input_rules.EMAIL_LEVELS``), in words.
EMAIL_CELLS = {
    1: "own domain (policy)",
    2: "partner domain (policy)",
    3: "no readable domain",
    4: "another organization (policy: outside is unusual)",
    5: "personal mailbox (gmail, outlook...), or a domain the policy flags",
}
#: ``ranges`` measure -> (what the number is, unit after it)
MEASURES = {
    "value": ("the number itself", ""),
    "length": ("length (items or characters)", ""),
    "hour_of_day": ("hour of day", " h"),
    "weekday": ("weekday, 0 = Monday", ""),
    "span_hours": ("hours between it and `{with}`", " h"),
    "hours_from_now": ("hours from now (negative is the past)", " h"),
}
KIND_LABELS = {
    "register": "asset name",
    "keywords": "text contains",
    "values": "fixed value",
    "domain": "email or URL domain",
    "email": "email address",
}


def _cell(text: object) -> str:
    """Make a value safe inside a markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ")


def _num(x: float | int) -> str:
    return f"{x:g}"


def _range_label(lo: float | None, hi: float | None, unit: str) -> str:
    if lo is not None and hi is not None:
        return f"{_num(lo)} to {_num(hi)}{unit}"
    if hi is not None:
        return f"below {_num(hi)}{unit}"
    if lo is not None:
        return f"{_num(lo)}{unit} and up"
    return "any"


def _value_text(value: object) -> str:
    return json.dumps(value) if isinstance(value, bool) or value is None else str(value)


def kind_label(rule: dict) -> str:
    """What the rule reads in the value, in words."""
    if rule["kind"] == "ranges":
        what, _ = MEASURES.get(rule.get("measure", ""), (str(rule.get("measure")), ""))
        return "number: " + what.format(**{"with": rule.get("with", "?")})
    return KIND_LABELS[rule["kind"]]


def levels_of(rule: dict, assets: dict[str, int]) -> dict[int, list[str]]:
    """Which values land on each level 1 to 5 under one rule.

    ``assets`` are the assets the tool can reach with their scanned level, the
    table a ``register`` rule looks a value up in at run time."""
    cells: dict[int, list[str]] = collections.defaultdict(list)
    kind = rule["kind"]
    if kind == "ranges":
        _, unit = MEASURES.get(rule.get("measure", ""), ("", ""))
        for r in rule["ranges"]:
            cells[r["level"]].append(_range_label(r.get("min"), r.get("max"), unit))
        cells[rule["default"]].append("unreadable or uncovered (default)")
    elif kind == "register":
        overrides = {o["asset"]: o["level"] for o in rule.get("overrides") or []}
        for asset, level in sorted(register_table(rule, assets).items()):
            if asset in overrides:
                continue
            cells[level].append(f"{asset} (scan)")
        for asset, level in overrides.items():
            cells[level].append(f"{asset} (policy override)")
        for g in rule.get("groups") or []:
            cells[g["level"]].append("name has " + ", ".join(g["contains"]))
        cells[rule["default"]].append("any other name (default)")
    elif kind == "keywords":
        for g in rule["groups"]:
            if g.get("added_by"):
                cells[g["level"]].append("credential words (program)")
                continue
            cells[g["level"]].append(", ".join(g["contains"]))
        cells[rule["default"]].append("anything else (default)")
    elif kind == "values":
        for e in rule["values"]:
            cells[e["level"]].append(_value_text(e["value"]))
        cells[rule["default"]].append("any other value (default)")
    elif kind == "domain":
        cells[rule["internal"]].append("inside the organization")
        cells[rule["external"]].append("outside the organization, or unknown")
    elif kind == "email":
        for level, text in EMAIL_CELLS.items():
            cells[level].append(text)
    return cells


def source_of(row: dict, assets: dict[str, int]) -> str:
    """Where the row's levels come from, in words.

    A ``register`` rule on a tool with no asset list returns only its default."""
    rule, source = row["rule"], SOURCE_LABELS.get(row.get("source", ""), str(row.get("source")))
    if rule["kind"] == "email":
        return "policy, address"
    if rule["kind"] != "register":
        return source
    if not register_table(rule, assets):
        return "agent (no asset list)"
    parts = ["scan"]
    if rule.get("overrides"):
        parts.append("policy overrides")
    if rule.get("groups"):
        parts.append("agent name words")
    return ", ".join(parts)


def reachable_assets(tool: dict) -> dict[str, int]:
    """The assets a tool can reach, with their scanned level from the policy slice."""
    return {
        a["asset"]: a["scanned_level"]
        for a in tool.get("policy_slice", {}).get("assets_this_tool_can_reach", [])
        if isinstance(a.get("scanned_level"), int)
    }


def render_tool_rows(tool: dict) -> list[str]:
    """One table row per input of this tool that stage 1 kept."""
    assets = reachable_assets(tool)
    rows = []
    for arg in tool["arguments"]:
        if not arg.get("important"):
            continue
        name = f"`{tool['tool_name']}.{arg['path']}`"
        rule = arg.get("rule")
        if not isinstance(rule, dict):
            blanks = " | ".join([EMPTY_CELL] * len(LEVELS))
            rows.append(f"| {name} | no rule written | {blanks} | {EMPTY_CELL} | {EMPTY_CELL} |")
            continue
        cells = levels_of(rule, assets)
        level_cells = " | ".join(
            _cell("; ".join(cells[lv])) if cells.get(lv) else EMPTY_CELL for lv in LEVELS
        )
        absent = arg.get("when_absent")
        absent_text = str(absent) if absent is not None else "adds nothing"
        rows.append(
            f"| {name} | {_cell(kind_label(rule))} | {level_cells} | "
            f"{absent_text} | {source_of(arg, assets)} |"
        )
    return rows


def render_server(data: dict) -> str:
    """The section for one server: counts by source, then the table."""
    kept = [(t, a) for t in data["tools"] for a in t["arguments"] if a.get("important")]
    with_rule = [(t, a) for t, a in kept if isinstance(a.get("rule"), dict)]
    sources = collections.Counter(source_of(a, reachable_assets(t)) for t, a in with_rule)
    policy = data.get("policy_section") or "none"
    header = " | ".join(LEVEL_NAMES[lv] for lv in LEVELS)
    lines = [
        f"## {data['server']}",
        "",
        f"Policy: `{policy}`. {len(kept)} inputs kept, {len(with_rule)} with a rule. "
        "Levels from: " + ", ".join(f"{k} {v}" for k, v in sources.most_common()) + ".",
        "",
        f"| Input | Reads | {header} | If left out | Levels from |",
        "|" + "---|" * (len(LEVELS) + 4),
    ]
    for tool in data["tools"]:
        lines += render_tool_rows(tool)
    return "\n".join(lines)


def render_run(run_dir: Path) -> str:
    """The whole document for every server of a run that has stage 2 output."""
    servers = sorted(
        p.stem
        for p in run_dir.glob("*.json")
        if not p.name.startswith("eval_") and not p.name.endswith(".importance.json")
    )
    sections = [render_server(json.loads((run_dir / f"{s}.json").read_text())) for s in servers]
    intro = [
        f"# Input Rule Levels: {run_dir.name}",
        "",
        "Every kept input, and which of its values land on each level from 1 to 5 at "
        "run time. Generated by `scripts/render_input_rule_levels.py`; do not edit by hand.",
        "",
        "## How to read it",
        "",
        "- **Reads**: what the rule looks at in the value: a number (and which number), an "
        "asset name, words the text contains, a fixed value, or an email or URL domain.",
        "- **Levels**: 1 safest, 2 safe, 3 ordinary, 4 high, 5 critical; an ordinary call "
        "gets 1 to 3. `(default)` marks the level a value gets when nothing more specific "
        "matches.",
        "- **If left out**: the level when the call omits the input; `adds nothing` means "
        "omitting it does not raise the call.",
        "- **Levels from**: `scan` each asset's scanned sensitivity, which a `register` rule "
        "returns for a value naming that asset; `agent name words` name fragments the agent "
        "added for the levels no asset reaches; `policy` the organization's policy (v12 tables, "
        "or the address lists of the email ladder); `policy overrides` assets the policy raises "
        "above their scanned level (v12); `schema` the tool's own bounds (v12); `agent` the "
        "agent's own judgement.",
        "- A `register` row lists every asset the tool can reach, including abstract ones "
        "(a directory, a record set) that a value rarely names. Opaque ids (`C0BL...`) match "
        "only through the deployment's id table, otherwise they take the default.",
    ]
    return "\n".join(intro) + "\n\n" + "\n\n".join(sections) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--run", type=Path, required=True, help="a v12 or v13 run folder")
    parser.add_argument("--out", type=Path, help=f"output file (default <run>/{OUTPUT_NAME})")
    args = parser.parse_args()
    out = args.out or args.run / OUTPUT_NAME
    out.write_text(render_run(args.run))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
