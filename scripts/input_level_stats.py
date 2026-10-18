"""Statistics of a v13 run's tool inputs, written as ``<run>/input-statistics.md``.

How many inputs each server and tool has and keeps, why the others were
dropped (by the program, before asking, or by the model), what the kept ones
are (rule kind, what they decide, where their levels come from), which input
names recur across tools and whether they are treated alike, and which kept
inputs the 3,000 real labelled calls actually use.

Usage::

    uv run python scripts/input_level_stats.py --run reports/experiments/v13/run21
"""

from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from evaluate_input_rules import load_aliases, score_server  # noqa: E402
from policy_context import POLICY_SECTIONS  # noqa: E402

SERVERS = ("github", "slack", "calendar", "filesystem", "sqlite")
#: Servers with real labelled calls (``scripts/evaluate_input_rules.py``).
CORPUS_SERVERS = ("github", "slack", "calendar")
#: An input name is "common" when this many tools of one server, or more, have it.
COMMON_MIN_TOOLS = 3
TOP = 15

#: Drop reasons, in the order they are tested: (category, who decides, fragments
#: of the reason text). The program's own reasons are fixed strings; the model's
#: are free text, grouped by the words they use.
DROP_REASONS = (
    ("Fewer than five possible values", "program", ("fewer than five possible values; decided",)),
    ("Paging, sorting or a time zone", "program", ("paging, sorting or a time zone",)),
    ("Record number the policy cannot tell apart", "program", ("a record number:",)),
    ("Id not in the policy's register", "program", ("an id: only the id",)),
    ("A label next to the main content", "model", ("label next to the main content",)),
    ("Only narrows the call", "model", ("narrow",)),
    ("A record inside an asset another input picked", "model",
     ("record inside", "is a record", "sha", "commit id")),
    ("Needs facts nobody has (who a person is)", "model", ("opaque", "depends on who")),
    ("Metadata, tags or custom properties", "model",
     ("metadata", "extended propert", "custom propert", "labels", "label is")),
    ("Presentation, display or reminders", "model",
     ("presentation", "presented", "format", "fields", "reminder", "mime", "icon", "color")),
    ("Bookkeeping", "model", ("bookkeeping", "idempotency", "duplicate")),
    ("Fewer than five values (model)", "model", ("fewer than five",)),
)
OTHER_REASON = ("Does not touch an asset (other)", "model")


def drop_reason(reason: str) -> tuple[str, str]:
    """(category, who decided) for one dropped input's reason text."""
    text = reason.casefold()
    for category, who, fragments in DROP_REASONS:
        if any(f in text for f in fragments):
            return category, who
    return OTHER_REASON


def input_name(path: str) -> str:
    """The input's own name: the last part of its path, list markers removed."""
    return path.replace("[]", "").rsplit(".", 1)[-1]


def level_source(rule: dict) -> str:
    """Where a kept rule's levels come from."""
    kind = rule.get("kind")
    if kind == "email":
        return "policy: the email ladder"
    if kind == "register":
        return "scan: the policy's asset register" if rule.get("assets") else "agent: name words"
    return "agent"


def load_run(run_dir: Path) -> list[dict]:
    """One row per tool input of every server in the run."""
    rows = []
    for server in SERVERS:
        path = run_dir / f"{server}.json"
        if not path.exists():
            continue
        for tool in json.loads(path.read_text())["tools"]:
            for arg in tool["arguments"]:
                rows.append({"server": server, "tool": tool["tool_name"], **arg})
    return rows


def _table(header: list[str], body: list[list[object]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in body]
    return lines + [""]


def totals_section(rows: list[dict], tools_by_server: dict[str, int]) -> list[str]:
    """Inputs, kept, no rule, dropped by the program and by the model, per server."""
    body = []
    for server in [*SERVERS, "all"]:
        part = [r for r in rows if server in ("all", r["server"])]
        if not part:
            continue
        program = sum(r["status"] == "null" and drop_reason(r.get("reason", ""))[1] == "program"
                      for r in part)
        null = sum(r["status"] == "null" for r in part)
        tools = (sum(tools_by_server.values()) if server == "all"
                 else tools_by_server.get(server, 0))
        body.append([server, tools, len(part), sum(r["status"] == "rule" for r in part),
                     sum(r["status"] in ("broken", "unanswered") for r in part),
                     program, null - program])
    return ["## Totals", "",
            "Kept means a rule that reaches all five levels. No rule: the model was asked, but "
            "its rule never passed the check, so the input adds no level.", "",
            *_table(["server", "tools", "inputs", "kept", "no rule", "dropped by the program",
                     "dropped by the model"], body)]


def per_tool_section(rows: list[dict]) -> list[str]:
    """How many inputs a tool has and keeps; the largest tools; tools that keep none."""
    by_tool: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_tool[(r["server"], r["tool"])].append(r)
    body = []
    for server in SERVERS:
        tools = [v for (s, _), v in by_tool.items() if s == server]
        if not tools:
            continue
        sizes = [len(v) for v in tools]
        kept = [sum(r["status"] == "rule" for r in v) for v in tools]
        body.append([server, len(tools), min(sizes), statistics.median(sizes), max(sizes),
                     round(statistics.mean(kept), 1), max(kept),
                     sum(k == 0 for k in kept)])
    largest = sorted(by_tool.items(), key=lambda kv: -len(kv[1]))[:TOP]
    big = [[s, f"`{t}`", len(v), sum(r["status"] == "rule" for r in v),
            ", ".join(f"`{r['path']}`" for r in v if r["status"] == "rule")[:160] or "–"]
           for (s, t), v in largest]
    none = sorted(f"{s} `{t}`" for (s, t), v in by_tool.items()
                  if not any(r["status"] == "rule" for r in v))
    return ["## Inputs per tool", "",
            *_table(["server", "tools with inputs", "fewest inputs", "median", "most",
                     "kept per tool (mean)", "most kept", "tools keeping none"], body),
            f"The {TOP} tools with the most inputs:", "",
            *_table(["server", "tool", "inputs", "kept", "kept inputs"], big),
            f"Tools that keep no input ({len(none)}): " + ", ".join(none) + ".", ""]


def drop_section(rows: list[dict]) -> list[str]:
    """Why each dropped input was dropped, with examples."""
    groups: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for r in rows:
        if r["status"] == "null":
            groups[drop_reason(r.get("reason", ""))].append(r)
    total = sum(len(v) for v in groups.values())
    body = [[category, who, len(v), f"{100 * len(v) / total:.0f}%",
             ", ".join(f"`{r['tool']}.{r['path']}`" for r in v[:3])]
            for (category, who), v in sorted(groups.items(), key=lambda kv: -len(kv[1]))]
    broken = [r for r in rows if r["status"] in ("broken", "unanswered")]
    lines = ["## Why inputs were dropped", "",
             f"{total} inputs were dropped. The program decides some before asking the model "
             "(switches and short choice lists, paging, record numbers); the model's reasons are "
             "free text, grouped here by the words they use.", "",
             *_table(["reason", "decided by", "inputs", "share", "examples"], body)]
    if broken:
        lines += [f"Kept as important but with no rule ({len(broken)}): the model never filled "
                  "every level.", "",
                  *_table(["server", "input", "what failed"],
                          [[r["server"], f"`{r['tool']}.{r['path']}`",
                            r.get("reason", "").removeprefix("the rule never passed the check: ")
                            [:110]] for r in broken])]
    return lines


def kept_section(rows: list[dict]) -> list[str]:
    """What the kept inputs are: rule kind, what they decide, where their levels come from."""
    kept = [r for r in rows if r["status"] == "rule"]
    kinds = collections.Counter(r["rule"]["kind"] for r in kept)
    measures = collections.Counter(r["rule"].get("measure") for r in kept
                                   if r["rule"]["kind"] == "ranges")
    effects = collections.Counter(r.get("effect") or "decided by the program" for r in kept)
    sources = collections.Counter(level_source(r["rule"]) for r in kept)
    extras = [
        ["text rules with the program's credential words at 5",
         sum(any(isinstance(g, dict) and g.get("added_by") for g in r["rule"].get("groups") or [])
             for r in kept)],
        ["asset-name rules raising an asset the policy prohibits (`overrides`)",
         sum(bool(r["rule"].get("overrides")) for r in kept)],
        ["rules with a level for a left-out input (`when_absent`)",
         sum(r.get("when_absent") is not None for r in kept)],
        ["rules rated at the server's default when left out (at most 3)",
         sum(r.get("schema_default") is not None for r in kept)],
    ]
    nested = sum("." in r["path"] or "[]" in r["path"] for r in kept)
    return ["## What the kept inputs are", "",
            f"{len(kept)} inputs kept; {nested} of them nested inside another input "
            "(`files[].path`, `attendees[].email`).", "",
            *_table(["rule kind", "inputs"], [[k, n] for k, n in kinds.most_common()]),
            *_table(["number rule measures", "inputs"],
                    [[m, n] for m, n in measures.most_common()]),
            *_table(["what the input decides (`effect`)", "inputs"],
                    [[e, n] for e, n in effects.most_common()]),
            *_table(["where the levels come from", "inputs"],
                    [[s, n] for s, n in sources.most_common()]),
            *_table(["also", "inputs"], extras)]


def common_section(rows: list[dict]) -> list[str]:
    """Input names many tools share, and whether they are kept and ruled alike."""
    by_name: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_name[(r["server"], input_name(r["path"]))].append(r)
    common = [(k, v) for k, v in by_name.items()
              if len({r["tool"] for r in v}) >= COMMON_MIN_TOOLS]
    common.sort(key=lambda kv: (-len({r["tool"] for r in kv[1]}), kv[0]))
    body = []
    for (server, name), v in common:
        kept = [r for r in v if r["status"] == "rule"]
        kinds = collections.Counter(r["rule"]["kind"] for r in kept)
        dropped = collections.Counter(drop_reason(r.get("reason", ""))[0]
                                      for r in v if r["status"] == "null")
        no_rule = sum(r["status"] in ("broken", "unanswered") for r in v)
        outcomes = len(kinds) + (1 if dropped else 0) + (1 if no_rule else 0)
        body.append([server, f"`{name}`", len({r["tool"] for r in v}), len(v), len(kept),
                     no_rule, ", ".join(f"{k} {n}" for k, n in kinds.most_common()) or "–",
                     ", ".join(f"{k} {n}" for k, n in dropped.most_common()) or "–",
                     "yes" if outcomes <= 1 else "no"])
    return ["## Common input names", "",
            f"Names that {COMMON_MIN_TOOLS} or more tools of one server share; a tool can have a "
            "name twice (`account` and `events[].account`), so inputs can outnumber tools. "
            "*Treated alike*: every input with the name is kept with the same rule kind, or "
            "every one is dropped.", "",
            *_table(["server", "name", "tools", "inputs", "kept", "no rule", "rule kinds",
                     "dropped because", "treated alike"], body)]


def real_calls_section(run_dir: Path, rows: list[dict]) -> list[str]:
    """Which kept inputs the real labelled calls use, and which set a call's level."""
    aliases = load_aliases()
    seen: collections.Counter = collections.Counter()
    setter: collections.Counter = collections.Counter()
    calls = 0
    for server in CORPUS_SERVERS:
        if not (run_dir / f"{server}.json").exists() or server not in POLICY_SECTIONS:
            continue
        for call in score_server(run_dir, server, aliases, ())["calls"]:
            calls += 1
            for path, (_level, matched) in call["inputs"].items():
                if not str(matched).startswith("absent"):
                    seen[(server, call["tool"], path)] += 1
            for path in call["set_by"]:
                setter[(server, call["tool"], path)] += 1
    kept = [r for r in rows if r["status"] == "rule" and r["server"] in CORPUS_SERVERS]
    unused = sum((r["server"], r["tool"], r["path"]) not in seen for r in kept)
    body = [[s, f"`{t}.{p}`", n, seen[(s, t, p)]] for (s, t, p), n in setter.most_common(TOP)]
    return ["## Kept inputs in the real calls", "",
            f"{calls} real labelled calls on {', '.join(CORPUS_SERVERS)}. Of their {len(kept)} kept "
            f"inputs, {len(kept) - unused} appear with a value in at least one call and {unused} "
            "never do: the corpus uses few tools and few arguments per tool.", "",
            f"The {TOP} inputs that most often set a call's level (the highest input level of "
            "the call). An input can set it while left out, through its level for a left-out "
            "input: a Slack search with no channel filter scores 4.", "",
            *_table(["server", "input", "calls whose level it sets", "calls where it has a value"],
                    body)]


def render(run_dir: Path) -> str:
    """The whole report as markdown."""
    rows = load_run(run_dir)
    tools = collections.Counter()
    for server in SERVERS:
        path = run_dir / f"{server}.json"
        if path.exists():
            tools[server] = len(json.loads(path.read_text())["tools"])
    lines = [f"# Tool Input Statistics: {run_dir.name}", "",
             f"Counts over the {len(rows)} tool inputs of {run_dir.name}'s five catalogs. "
             "Generated by `scripts/input_level_stats.py`; do not edit by hand.", ""]
    lines += totals_section(rows, tools) + per_tool_section(rows) + drop_section(rows)
    lines += kept_section(rows) + common_section(rows) + real_calls_section(run_dir, rows)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--run", type=Path, required=True, help="a v13 run folder")
    args = ap.parse_args()
    out = args.run / "input-statistics.md"
    out.write_text(render(args.run))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
