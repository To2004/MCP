"""Forward/reversed stability test for experiment 2: explained levels, one direct pick.

Prompt: `reports/experiments/dynamic_layer/v6/breadth_prompt_categories.md`. Same three
rubric fixes as experiment 1 (creation-call rule, sharpened list tie-breaker,
`external_effect` split out) and the same de-fitted examples, but the model picks ONE
`resource_role` label directly from five explained levels -- no forced five-question
checklist, no code-side derivation. This is the control for experiment 1: if experiment
1 clearly wins, forcing every check was the part doing the work; if they land close
together, the rubric fixes alone were enough.

Same forward/reversed methodology as v2/v3/v4/checks.

NOTE: this was originally written to prefill the assistant turn with ``{"inputs": [``,
same as the checks experiment. That does not work against Ollama's ``/api/generate``
without ``raw: true`` -- see `check_breadth_checks_stability.py` for the diagnosis (a
first run of both experiments this way scored 0/24 tools each, 100% failure). Dropped
in favor of the plain, non-prefilled ``query_ollama`` call v2/v3/v4 already use.

    sbatch scripts/check_breadth_categories_stability.sbatch
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
PROMPT_DOC = (REPO / "reports" / "experiments" / "dynamic_layer" / "v6"
              / "breadth_prompt_categories.md")
OUT = REPO / "reports" / "experiments" / "breadth_spec" / "breadth_categories_stability.json"
IN_USE = ("github_real", "slack_real", "calendar_real")
HELD_OUT = ("filesystem", "sqlite", "maverick", "openbb", "sec_edgar", "yahoo_finance",
            "finance_tools")

KIND_VALUES = {"count", "magnitude", "range", "not_size"}
ROLE_ORDER = {
    "no_data_effect": 1, "shapes_output": 2, "sizes_amount": 3,
    "alters_reach": 4, "names_resource": 5,
}
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
    return (template.replace("{tool}", tool.name)
                     .replace("{desc}", (tool.description or "")[:300])
                     .replace("{params}", _params_block(tool)))


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
            name, kind, role = item.get("name"), item.get("kind"), item.get("resource_role")
            ext = item.get("external_effect")
            if name not in wanted or kind not in KIND_VALUES or role not in ROLE_ORDER or ext not in ("yes", "no"):
                ok = False
                break
            out[name] = {"kind": kind, "resource_role": role, "external_effect": ext}
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
    random.Random(20260814).shuffle(catalogs)  # same seed as v2/v3/v4/checks

    results: list[dict] = []
    print(f"{'catalog':<18}{'tool':<28}{'inputs':>7}{'kind agree':>11}{'role agree':>11}",
          flush=True)
    for path in catalogs:
        tools = sorted(load_catalog(path),
                       key=lambda t: -len((t.input_schema or {}).get("properties") or {}))
        for tool in [t for t in tools
                     if len((t.input_schema or {}).get("properties") or {}) >= 3][:args.per_catalog]:
            forward = _entries(template, tool, args.model)
            backward = _entries(template, _reversed_schema(tool), args.model)
            if not forward or not backward:
                print(f"{path.stem:<18}{tool.name:<28}{'':>7}{'n/a':>11}{'n/a':>11}", flush=True)
                continue
            names = sorted(set(forward) & set(backward))

            kind_matches = sum(1 for n in names if forward[n]["kind"] == backward[n]["kind"])
            role_matches = sum(1 for n in names
                               if forward[n]["resource_role"] == backward[n]["resource_role"])
            deltas = [abs(ROLE_ORDER[forward[n]["resource_role"]]
                         - ROLE_ORDER[backward[n]["resource_role"]])
                     for n in names if forward[n]["resource_role"] != backward[n]["resource_role"]]
            kind_rate = kind_matches / len(names)
            role_rate = role_matches / len(names)
            results.append({
                "catalog": path.stem, "tool": tool.name, "inputs": len(names),
                "kind_agree": round(kind_rate, 3), "role_agree": round(role_rate, 3),
                "role_deltas": deltas,
                "forward": {n: forward[n] for n in names},
                "backward": {n: backward[n] for n in names},
            })
            print(f"{path.stem:<18}{tool.name:<28}{len(names):>7}{kind_rate:>11.2f}"
                  f"{role_rate:>11.2f}", flush=True)

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
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=1))
    print(f"\n{len(results)} tools  mean kind agree {summary['mean_kind_agree']}  "
          f"mean role agree {summary['mean_role_agree']}  "
          f"median {summary['median_role_agree']}  "
          f"identical {summary['identical']}  "
          f"mean |delta| when wrong {summary['mean_role_delta_when_disagreeing']}",
          flush=True)
    print(f"written to {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
