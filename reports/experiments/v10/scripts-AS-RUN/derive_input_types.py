"""Type one server's tool inputs with the LLM, using the markdown as prompt.

``docs/standards/input-typing.md`` is both the human spec and the prompt: it is
sent verbatim with ``{tool_json}`` replaced by the tool's definition. Unlike
``param_scoring``, the tool JSON carries the **full input schema** — ``enum``,
``minimum``, ``maximum``, ``format`` — because the typing questions cannot be
answered from a bare ``{"type": "string"}``.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_security.llm.ollama_client import query_ollama  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
PROMPT_PATH = REPO / "docs" / "standards" / "input-typing.md"
OUT_DIR = REPO / "reports" / "input_types"

logger = logging.getLogger("derive_input_types")

TOOLLISTS = {
    "github": REPO / "reports" / "live_run" / "github_real_toollist.json",
    "slack": REPO / "reports" / "live_run" / "slack_real_toollist.json",
}


def _load_tools(server: str) -> list[dict]:
    """Tool definitions with their full input schema, newest source per server."""
    if server in TOOLLISTS:
        raw = json.loads(TOOLLISTS[server].read_text())["tools"]
        return [
            {
                "tool_name": t["name"],
                "description": t.get("description", ""),
                "input_schema": t.get("input_schema") or t.get("inputSchema") or {},
            }
            for t in raw
        ]
    if server == "calendar":
        from mcp_security.static_scoring.registry import load_calendar_registry

        return [
            {
                "tool_name": t.name,
                "description": t.description,
                "input_schema": t.input_schema or {},
                "annotations": {
                    "read_only_hint": t.read_only_hint,
                    "destructive_hint": t.destructive_hint,
                },
            }
            for t in load_calendar_registry().tools
        ]
    raise SystemExit(f"unknown server {server!r}")


def _param_key(name: str, spec: dict) -> tuple:
    """Identity of a parameter across the tools of one server."""
    return (name, (spec.get("description") or "").strip(), spec.get("type"))


def _prompt_for(tool: dict) -> str:
    md = PROMPT_PATH.read_text(encoding="utf-8")
    # Everything after the prompt section is guidance for the caller, not the
    # model: drop it so the tool definition is the last thing the model reads.
    md = md.split("## Notes for the caller")[0].rstrip()
    if "{tool_json}" not in md:
        raise SystemExit("prompt file has no {tool_json} placeholder")
    return md.replace("{tool_json}", json.dumps(tool, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server", required=True, choices=["github", "slack", "calendar"])
    ap.add_argument("--shard", default="0/1", help="i/n — type only every n-th tool")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s %(message)s")

    i, n = (int(x) for x in args.shard.split("/"))
    tools = [t for k, t in enumerate(_load_tools(args.server)) if k % n == i]
    logger.info("%s: typing %d tool(s) [shard %s]", args.server, len(tools), args.shard)

    results, failed, no_schema = [], [], []
    typed: dict[tuple, dict] = {}  # parameter identity -> the answer, reused across tools
    for tool in tools:
        name = tool["tool_name"]
        props = (tool["input_schema"] or {}).get("properties", {})
        if not props:
            # A tool with no declared inputs is a fact about the tool. Asking the
            # model about it invites it to invent the parameters it expects.
            logger.info("  -- %s declares no inputs; not sent to the model", name)
            no_schema.append(name)
            results.append({"tool_name": name, "parameters": [],
                            "declared_parameters": 0, "no_declared_schema": True})
            continue

        known = {p: k for p, spec in props.items()
                 if (k := _param_key(p, spec if isinstance(spec, dict) else {})) in typed}
        todo = [p for p in props if p not in known]
        if todo:
            ask = dict(tool)
            ask["type_these"] = todo
            logger.info("  -> %s (%d declared, %d new, %d reused)",
                        name, len(props), len(todo), len(known))
            reply = query_ollama(_prompt_for(ask))
            if not isinstance(reply, dict) or "parameters" not in reply:
                logger.warning("     no usable JSON for %s", name)
                failed.append(name)
                continue
            fresh = [p for p in reply["parameters"] if isinstance(p, dict)
                     and p.get("name") in todo]
            for p in fresh:
                spec = props.get(p["name"])
                typed[_param_key(p["name"], spec if isinstance(spec, dict) else {})] = p
        else:
            logger.info("  -- %s (%d declared, all reused)", name, len(props))
            fresh = []

        params = []
        for p_name in props:
            spec = props[p_name] if isinstance(props[p_name], dict) else {}
            answer = typed.get(_param_key(p_name, spec))
            if answer is None:
                continue
            answer = dict(answer)
            answer["reused"] = p_name in known
            params.append(answer)
        results.append({"tool_name": name, "parameters": params,
                        "declared_parameters": len(props)})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = args.server if n == 1 else f"{args.server}.shard{i}"
    out = OUT_DIR / f"{stem}.json"
    out.write_text(json.dumps({"server": args.server, "tools": results,
                               "failed": failed, "no_declared_schema": no_schema,
                               "distinct_parameters": len(typed)}, indent=2))
    logger.info("wrote %s (%d tool(s), %d distinct param(s), %d failed, %d schemaless)",
                out, len(results), len(typed), len(failed), len(no_schema))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
