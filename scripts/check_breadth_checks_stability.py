"""Forward/reversed stability test for experiment 1: forced checks, label derived in code.

Prompt: `reports/experiments/dynamic_layer/v6/breadth_prompt_checks.md`. The model answers
five yes/no checks (C1..C5) for every parameter instead of picking one `resource_role`
label directly; this script derives the label as the LOWEST check that came back "Y" and
logs `multi_y` (more than one check answered yes) separately, since that is exactly the
population v3's single-shot label was silently collapsing.

Same forward/reversed methodology as v2/v3/v4: ask about a tool's parameters in schema
order, then again with the schema reversed, compare `kind` and the DERIVED
`resource_role`.

NOTE: the original design for this experiment prefilled the assistant turn with
``{"inputs": [`` to force immediate valid JSON. That does not work against Ollama's
``/api/generate`` without ``raw: true`` plus the model's own chat-template tokens --
without ``raw``, Ollama wraps the prompt in the chat template and generates a FRESH
reply regardless of what is appended to the prompt text, so the appended prefix just
became trailing user text and every reply came back malformed when stitched to it (a
first full run scored 0/24 tools, 100% failure, confirming this). Dropped in favor of
the same plain, non-prefilled call ``query_ollama`` that v2/v3/v4 already use
successfully.

    sbatch scripts/check_breadth_checks_stability.sbatch
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.static_scoring.registry import ToolSpec

REPO = Path(__file__).resolve().parents[1]
PROMPT_DOC = REPO / "reports" / "experiments" / "dynamic_layer" / "v6" / "breadth_prompt_checks.md"
OUT = REPO / "reports" / "experiments" / "breadth_spec" / "breadth_checks_stability.json"
IN_USE = ("github_real", "slack_real", "calendar_real")
HELD_OUT = ("filesystem", "sqlite", "maverick", "openbb", "sec_edgar", "yahoo_finance",
            "finance_tools")

KIND_VALUES = {"count", "magnitude", "range", "not_size"}
CHECK_ORDER = ["no_data_effect", "shapes_output", "sizes_amount", "alters_reach", "names_resource"]
ROLE_ORDER = {name: i + 1 for i, name in enumerate(CHECK_ORDER)}
CHECKS_RE = re.compile(r"^[YN]{5}$")
RETRIES = 1


def load_prompt_template() -> str:
    text = PROMPT_DOC.read_text()
    match = re.search(r"```text\n(.*?)\n```", text, re.DOTALL)
    if not match:
        raise ValueError(f"no ```text fence found in {PROMPT_DOC}")
    return match.group(1)


def _properties(tool: ToolSpec) -> dict[str, dict]:
    props = (tool.input_schema or {}).get("properties")
    return props if isinstance(props, dict) else {}


def _params_block(tool: ToolSpec) -> str:
    props = _properties(tool)
    return "\n".join(
        f"- {name} (declared type: {props[name].get('type') or 'unspecified'}): "
        f"{str(props[name].get('description') or '')[:200]}"
        for name in props
    )


def _fill(template: str, tool: ToolSpec) -> str:
    """Substitute placeholders without ``str.format`` -- the prompt's JSON examples and
    reply schema use single braces (unescaped), so ``.format`` raises on them."""
    return (template.replace("{tool}", tool.name)
                     .replace("{desc}", (tool.description or "")[:300])
                     .replace("{params}", _params_block(tool)))


def derive(item: dict) -> bool:
    """Mutates ``item`` with a derived ``resource_role`` and ``multi_y``; ``False`` if
    the checks string is unusable (bad shape, or all-N -- never defaulted silently)."""
    checks = item.get("checks")
    if not isinstance(checks, str) or not CHECKS_RE.match(checks):
        return False
    ys = [i for i, c in enumerate(checks) if c == "Y"]
    if not ys:
        return False
    item["resource_role"] = CHECK_ORDER[ys[0]]
    item["multi_y"] = len(ys) > 1
    return True


def _entries(template: str, tool: ToolSpec, model: str) -> dict[str, dict] | None:
    prompt = _fill(template, tool)
    wanted = set(_properties(tool))
    for _ in range(1 + RETRIES):
        reply = query_ollama(prompt, model=model)
        if not isinstance(reply, dict) or not isinstance(reply.get("inputs"), list):
            continue
        out: dict[str, dict] = {}
        ok = True
        for item in reply["inputs"]:
            if not isinstance(item, dict):
                ok = False
                break
            name, kind = item.get("name"), item.get("kind")
            if (name not in wanted or kind not in KIND_VALUES
                    or item.get("external_effect") not in ("yes", "no") or not derive(item)):
                ok = False
                break
            out[name] = {"kind": kind, "resource_role": item["resource_role"],
                        "multi_y": item["multi_y"], "external_effect": item["external_effect"]}
        if ok and set(out) == wanted:
            return out
    return None


def _reversed_schema(tool: ToolSpec) -> ToolSpec:
    schema = dict(tool.input_schema or {})
    props = schema.get("properties") or {}
    schema["properties"] = dict(reversed(list(props.items())))
    return ToolSpec(name=tool.name, description=tool.description, input_schema=schema)


def load_catalog(path: Path) -> list[ToolSpec]:
    raw = json.loads(path.read_text())
    entries = raw["tools"] if isinstance(raw, dict) and "tools" in raw else raw
    return [ToolSpec(name=e["name"], description=e.get("description", "") or "",
                     input_schema=e.get("input_schema") or e.get("inputSchema") or {})
            for e in entries]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen2.5:32b")
    parser.add_argument("--held-out", action="store_true")
    parser.add_argument("--per-catalog", type=int, default=8)
    args = parser.parse_args(argv)

    template = load_prompt_template()
    wanted = HELD_OUT if args.held_out else IN_USE
    catalogs = [p for p in
                sorted((REPO / "reports" / "tool_lists").glob("*.json"))
                + sorted((REPO / "reports" / "scan_finance" / "tool_lists").glob("*.json"))
                if any(p.stem.startswith(h) for h in wanted)]
    random.Random(20260814).shuffle(catalogs)  # same seed as v2/v3/v4

    results: list[dict] = []
    print(f"{'catalog':<18}{'tool':<28}{'inputs':>7}{'kind agree':>11}{'role agree':>11}{'multi_y':>9}",
          flush=True)
    for path in catalogs:
        tools = sorted(load_catalog(path),
                       key=lambda t: -len((t.input_schema or {}).get("properties") or {}))
        for tool in [t for t in tools
                     if len((t.input_schema or {}).get("properties") or {}) >= 3][:args.per_catalog]:
            forward = _entries(template, tool, args.model)
            backward = _entries(template, _reversed_schema(tool), args.model)
            if not forward or not backward:
                print(f"{path.stem:<18}{tool.name:<28}{'':>7}{'n/a':>11}{'n/a':>11}{'':>9}", flush=True)
                continue
            names = sorted(set(forward) & set(backward))

            kind_matches = sum(1 for n in names if forward[n]["kind"] == backward[n]["kind"])
            role_matches = sum(1 for n in names
                               if forward[n]["resource_role"] == backward[n]["resource_role"])
            deltas = [abs(ROLE_ORDER[forward[n]["resource_role"]]
                         - ROLE_ORDER[backward[n]["resource_role"]])
                     for n in names if forward[n]["resource_role"] != backward[n]["resource_role"]]
            multi_y_count = sum(1 for n in names if forward[n]["multi_y"] or backward[n]["multi_y"])
            kind_rate = kind_matches / len(names)
            role_rate = role_matches / len(names)
            results.append({
                "catalog": path.stem, "tool": tool.name, "inputs": len(names),
                "kind_agree": round(kind_rate, 3), "role_agree": round(role_rate, 3),
                "role_deltas": deltas, "multi_y_count": multi_y_count,
                "forward": {n: forward[n] for n in names},
                "backward": {n: backward[n] for n in names},
            })
            print(f"{path.stem:<18}{tool.name:<28}{len(names):>7}{kind_rate:>11.2f}"
                  f"{role_rate:>11.2f}{multi_y_count:>9}", flush=True)

    kind_rates = [r["kind_agree"] for r in results]
    role_rates = [r["role_agree"] for r in results]
    all_deltas = [d for r in results for d in r["role_deltas"]]
    summary = {
        "tools": len(results),
        "mean_kind_agree": round(statistics.fmean(kind_rates), 3) if kind_rates else None,
        "mean_role_agree": round(statistics.fmean(role_rates), 3) if role_rates else None,
        "median_role_agree": round(statistics.median(role_rates), 3) if role_rates else None,
        "identical": sum(1 for r in results if r["role_agree"] == 1.0),
        "mean_role_delta_when_disagreeing": (
            round(statistics.fmean(all_deltas), 3) if all_deltas else None),
        "total_multi_y": sum(r["multi_y_count"] for r in results),
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=1))
    print(f"\n{len(results)} tools  mean kind agree {summary['mean_kind_agree']}  "
          f"mean role agree {summary['mean_role_agree']}  "
          f"median {summary['median_role_agree']}  "
          f"identical {summary['identical']}  "
          f"mean |delta| when wrong {summary['mean_role_delta_when_disagreeing']}  "
          f"total multi_y {summary['total_multi_y']}",
          flush=True)
    print(f"written to {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
