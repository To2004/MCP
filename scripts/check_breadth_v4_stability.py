"""Forward/reversed stability test for the v4 idea: v3's labels, chunked into small calls.

Same labels, rubric, tie-breakers and examples as v3
(`reports/experiments/dynamic_layer/v4/breadth_prompt.md`) -- this only changes how many
parameters get a FULL VERDICT generated in one reply. v3 asked about every parameter of
a tool in one reply; the two biggest tools (28, 31 inputs) were also its two weakest
scores, and its own error sizes got bigger, not smaller, versus v2 -- both signatures of
batch-prompting degradation ("context bleeding" between items answered in the same
reply), not of rubric ambiguity.

This script asks about at most `--chunk-size` parameters per model call instead of the
whole tool at once. Each call still sees the FULL list of the tool's OTHER parameter
NAMES (context only, not to be labelled) -- v3's own rubric needs to know whether a
sibling parameter names the resource to tell `sizes_amount` from `names_resource`, so
that one piece of cross-parameter knowledge is kept even though full verdicts are not
batched together.

The prompt text is read straight out of
`reports/experiments/dynamic_layer/v5/breadth_prompt.md` (the fenced ```text block), the
same way `check_breadth_v3_stability.py` reads v3's.

    sbatch scripts/check_breadth_v4_stability.sbatch
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
PROMPT_DOC = REPO / "reports" / "experiments" / "dynamic_layer" / "v5" / "breadth_prompt.md"
OUT = REPO / "reports" / "experiments" / "breadth_spec" / "breadth_v4_stability.json"
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


def _param_line(name: str, props: dict[str, dict]) -> str:
    return (f"- {name} (declared type: {props[name].get('type') or 'unspecified'}): "
            f"{str(props[name].get('description') or '')[:200]}")


def _fill(template: str, tool: ToolSpec, chunk_names: list[str], other_names: list[str]) -> str:
    """Substitute placeholders without ``str.format`` -- the prompt's JSON examples and
    reply schema use single braces (unescaped), so ``.format`` raises on them."""
    props = _properties(tool)
    params_block = "\n".join(_param_line(n, props) for n in chunk_names)
    other_block = ", ".join(other_names) if other_names else "none -- this tool has no others"
    return (template.replace("{tool}", tool.name)
                     .replace("{desc}", (tool.description or "")[:300])
                     .replace("{other_params}", other_block)
                     .replace("{params}", params_block))


def _chunks(names: list[str], size: int) -> list[list[str]]:
    return [names[i:i + size] for i in range(0, len(names), size)]


def _ask_chunk(template: str, tool: ToolSpec, chunk_names: list[str], other_names: list[str],
               model: str) -> dict[str, dict] | None:
    prompt = _fill(template, tool, chunk_names, other_names)
    wanted = set(chunk_names)
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
            if name not in wanted or kind not in KIND_VALUES or role not in ROLE_ORDER:
                ok = False
                break
            out[name] = {"kind": kind, "resource_role": role}
        if ok and set(out) == wanted:
            return out
    return None


def _entries(template: str, tool: ToolSpec, model: str, chunk_size: int) -> dict[str, dict] | None:
    """``{param_name: {"kind":..., "resource_role":...}}`` over ALL chunks, or ``None``
    if any chunk failed -- a partial tool is never merged, same policy as v2/v3."""
    all_names = list(_properties(tool))
    out: dict[str, dict] = {}
    for chunk in _chunks(all_names, chunk_size):
        others = [n for n in all_names if n not in chunk]
        result = _ask_chunk(template, tool, chunk, others, model)
        if result is None:
            return None
        out.update(result)
    return out


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
    parser.add_argument("--per-catalog", type=int, default=8,
                        help="tools sampled per catalog -- same default as v2/v3, for a "
                             "direct compare")
    parser.add_argument("--chunk-size", type=int, default=6,
                        help="max parameters labelled in one model call")
    args = parser.parse_args(argv)

    template = load_prompt_template()
    wanted = HELD_OUT if args.held_out else IN_USE
    catalogs = [p for p in
                sorted((REPO / "reports" / "tool_lists").glob("*.json"))
                + sorted((REPO / "reports" / "scan_finance" / "tool_lists").glob("*.json"))
                if any(p.stem.startswith(h) for h in wanted)]
    random.Random(20260814).shuffle(catalogs)  # same seed as v2/v3

    results: list[dict] = []
    print(f"{'catalog':<18}{'tool':<28}{'inputs':>7}{'chunks':>7}{'kind agree':>11}{'role agree':>11}",
          flush=True)
    for path in catalogs:
        tools = sorted(load_catalog(path),
                       key=lambda t: -len((t.input_schema or {}).get("properties") or {}))
        for tool in [t for t in tools
                     if len((t.input_schema or {}).get("properties") or {}) >= 3][:args.per_catalog]:
            n_chunks = len(_chunks(list(_properties(tool)), args.chunk_size))
            forward = _entries(template, tool, args.model, args.chunk_size)
            backward = _entries(template, _reversed_schema(tool), args.model, args.chunk_size)
            if not forward or not backward:
                print(f"{path.stem:<18}{tool.name:<28}{'':>7}{n_chunks:>7}{'n/a':>11}{'n/a':>11}",
                      flush=True)
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
                "chunks": n_chunks,
                "kind_agree": round(kind_rate, 3), "role_agree": round(role_rate, 3),
                "role_deltas": deltas,
                "forward": {n: forward[n] for n in names},
                "backward": {n: backward[n] for n in names},
            })
            print(f"{path.stem:<18}{tool.name:<28}{len(names):>7}{n_chunks:>7}{kind_rate:>11.2f}"
                  f"{role_rate:>11.2f}", flush=True)

    kind_rates = [r["kind_agree"] for r in results]
    role_rates = [r["role_agree"] for r in results]
    all_deltas = [d for r in results for d in r["role_deltas"]]
    summary = {
        "chunk_size": args.chunk_size,
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
