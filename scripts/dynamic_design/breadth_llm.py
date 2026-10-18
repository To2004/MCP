"""LLM pass over tool inputs: classify BREADTH TYPE where the schema cannot say.

The deterministic pass (``breadth_spec.py``) reads the JSON Schema. It is exact when
the schema is honest, and blind when it is not — a list declared as a delimited
string, a quantity declared as a string, a query language whose breadth lives in its
own syntax. This pass asks a local model the same question over the same parameters,
so the two can be compared and the model's marginal contribution measured rather than
assumed.

Design constraints, both deliberate:

* **The prompt names no parameter from any server in the corpus.** Categories are
  described by function only. Concrete examples are the main channel by which a
  prompt memorises the set it will be measured on, so there are none.
* **The model cannot invent an identifier.** It receives the exact parameter list and
  its reply is accepted only if it classifies those names and no others. A reply that
  renames anything is rejected whole rather than partially merged.

Servers are split into a development set (already inspected while writing the
deterministic rules, so no longer usable as evidence) and a held-out set. Both are
classified; the report keeps them apart.

Run on a GPU node via ``scripts/dynamic_design/breadth_llm.sbatch``, or locally
against a reachable Ollama::

    OLLAMA_HOST=http://127.0.0.1:11500 python3 scripts/dynamic_design/breadth_llm.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "dynamic_design"))

from breadth_spec import classify, parameters  # noqa: E402

from mcp_security.llm.ollama_client import query_ollama  # noqa: E402

TOOL_LISTS = REPO / "reports" / "tool_lists"
OUT = REPO / "reports" / "experiments" / "breadth_spec"

# Split kept explicit: the deterministic rules were written while looking at the first
# three, which disqualifies them as an evaluation set for either pass.
DEV = {"github": "github_real", "slack": "slack_real", "calendar": "calendar_real"}
HELD_OUT = {"filesystem": "filesystem", "sqlite": "sqlite"}

VALID_KINDS = {"none", "count", "magnitude", "range"}

# No parameter name from any scanned server appears below, by design.
PROMPT = """You are classifying the input parameters of one API tool.

For each parameter decide ONE thing: if a caller supplied a different value, could \
that value alone make the call cover MORE of the system — more items touched, more \
data returned, more work done? Classify how that "more" is expressed.

Categories:

- "count": the value is a collection of items, and what matters is HOW MANY items it \
holds. This includes a collection encoded inside a single string with a separator.
- "magnitude": the value is a single number, and a larger number means the call \
returns more data or does more work. This includes a number written as text, with or \
without a unit suffix.
- "range": the value is one endpoint of an interval, and the SIZE of the interval \
between it and its partner parameter is what matters.
- "none": the value selects or names a particular thing, switches a mode on or off, \
or is free-form content. Changing it may change WHICH thing is touched, or what is \
written, but not HOW MUCH is covered.

Judge the meaning, not the declared type: a declared type is often wider or narrower \
than what the parameter really carries. A value that identifies something is "none" \
even when it happens to be numeric — one identifier is not larger than another.

Also report a ceiling ONLY if the parameter's own description or schema states an \
explicit maximum. Never estimate one, and never infer one from what seems reasonable: \
if no maximum is stated, use null.

Tool: {tool}
Description: {desc}

Parameters:
{params}

Reply with ONLY a JSON object. Classify every parameter listed above exactly once, \
using its name exactly as written:
{{"inputs": [{{"name": <parameter name>, "kind": "none|count|magnitude|range", \
"stated_ceiling": <number or null>, "why": "<one short clause>"}}]}}"""


def _param_lines(props: dict) -> str:
    lines = []
    for name, spec in props.items():
        declared = spec.get("type") or "unspecified"
        desc = str(spec.get("description") or "").replace("\n", " ")[:200]
        lines.append(f"- {name} (declared type: {declared}): {desc}")
    return "\n".join(lines)


def classify_tool_llm(tool: dict, model: str) -> tuple[list[dict] | None, float]:
    """Model classification for one tool's parameters, and the seconds it took.

    Returns ``(None, elapsed)`` when the reply is unusable — unreachable model,
    malformed JSON, an unknown name, an invalid kind, or incomplete coverage. A
    partial answer is never merged: it would silently mix model output with the
    deterministic default and make the comparison meaningless.
    """
    props = parameters(tool)
    if not props:
        return [], 0.0
    prompt = PROMPT.format(
        tool=tool.get("name", ""),
        desc=str(tool.get("description") or "")[:300],
        params=_param_lines(props),
    )
    started = time.monotonic()
    reply = query_ollama(prompt, model=model)
    elapsed = time.monotonic() - started
    if not isinstance(reply, dict) or not isinstance(reply.get("inputs"), list):
        return None, elapsed

    out: list[dict] = []
    seen: set[str] = set()
    for entry in reply["inputs"]:
        if not isinstance(entry, dict):
            return None, elapsed
        name, kind = entry.get("name"), entry.get("kind")
        if name not in props or name in seen or kind not in VALID_KINDS:
            return None, elapsed
        ceiling = entry.get("stated_ceiling")
        if not isinstance(ceiling, (int, float)) or isinstance(ceiling, bool):
            ceiling = None
        out.append({"name": name, "kind": kind, "ceiling": ceiling,
                    "why": str(entry.get("why", ""))[:140]})
        seen.add(name)
    if seen != set(props):
        return None, elapsed
    return out, elapsed


def run_server(kind: str, stem: str, model: str) -> dict:
    raw = json.loads((TOOL_LISTS / f"{stem}.json").read_text())
    tools = raw["tools"] if isinstance(raw, dict) else raw

    per_tool: dict[str, dict] = {}
    failures: list[str] = []
    total_s = 0.0
    for tool in tools:
        name = tool["name"]
        llm, elapsed = classify_tool_llm(tool, model)
        total_s += elapsed
        det = {c["name"]: c for c in (classify(n, s) for n, s in parameters(tool).items())}
        if llm is None:
            failures.append(name)
            per_tool[name] = {"llm": None, "deterministic": det}
            print(f"  {kind}/{name}: LLM reply unusable ({elapsed:.1f}s)", flush=True)
            continue
        per_tool[name] = {"llm": {e["name"]: e for e in llm}, "deterministic": det}
        print(f"  {kind}/{name}: {len(llm)} inputs ({elapsed:.1f}s)", flush=True)

    return {"server": kind, "model": model, "tools": per_tool,
            "failed_tools": failures, "llm_seconds": round(total_s, 1)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen2.5:32b")
    parser.add_argument("--only", help="one server key")
    args = parser.parse_args(argv)

    targets = {**DEV, **HELD_OUT}
    if args.only:
        targets = {args.only: targets[args.only]}
    OUT.mkdir(parents=True, exist_ok=True)

    for kind, stem in targets.items():
        split = "dev" if kind in DEV else "held-out"
        print(f"\n=== {kind} ({split}) ===", flush=True)
        result = run_server(kind, stem, args.model)
        result["split"] = split
        (OUT / f"{kind}_llm.json").write_text(json.dumps(result, indent=1))
        print(f"  -> {OUT / f'{kind}_llm.json'}  ({result['llm_seconds']}s, "
              f"{len(result['failed_tools'])} unusable)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
