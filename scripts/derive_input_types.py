"""Type one server's tool inputs with the LLM, using the markdown as prompt.

Tool definitions come from ``mcp_catalogs`` — live-captured catalogs only, with
no fallback: a server without a capture is not typed.

``docs/standards/input-typing.md`` is both the human spec and the prompt: it is
sent verbatim with ``{tool_json}`` replaced by the tool's definition. Unlike
``param_scoring``, the tool JSON carries the **full input schema** — ``enum``,
``minimum``, ``maximum``, ``format`` — because the typing questions cannot be
answered from a bare ``{"type": "string"}``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp_catalogs import CATALOGS, REPO as CAT_REPO, SERVERS, load_tools  # noqa: E402
from mcp_security.llm.ollama_client import query_ollama  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
PROMPT_PATH = REPO / "docs" / "standards" / "input-typing.md"
# Every run is archived as its own numbered folder under the experiment, holding
# the results *and* the prompt that produced them — the prompt changes per run,
# so results are only interpretable beside it.
V10 = REPO / "reports" / "experiments" / "v10"


def _run_dir() -> Path:
    """This run's folder. The sbatch script pins one for all servers via the
    environment; a bare invocation takes the next free number."""
    pinned = os.environ.get("MCP_INPUT_TYPES_OUT")
    if pinned:
        return Path(pinned)
    used = [int(d.name[3:]) for d in V10.glob("run*") if d.name[3:].isdigit()]
    return V10 / f"run{max(used, default=0) + 1}"


OUT_DIR = _run_dir()

logger = logging.getLogger("derive_input_types")

# Live-captured catalogs: the servers' real tool surfaces, with the schema
# constraints (enum, pattern, minItems, …) the typing questions depend on.
def _load_prompt() -> str:
    """The prompt text for this run, read once.

    ``_prompt_for`` used to re-read the file per tool, so an edit part-way
    through a run would silently split it across two prompts. One read per run
    is what makes the snapshot below honest.
    """
    md = PROMPT_PATH.read_text(encoding="utf-8")
    # Everything after the prompt section is guidance for the caller, not the
    # model: drop it so the tool definition is the last thing the model reads.
    md = md.split("## Notes for the caller")[0].rstrip()
    if "{tool_json}" not in md:
        raise SystemExit("prompt file has no {tool_json} placeholder")
    return md


def _prompt_for(template: str, tool: dict) -> str:
    return template.replace("{tool_json}", json.dumps(tool, indent=1))


def _snapshot_prompt(text: str) -> str:
    """Write the run's prompt beside its results; return its digest.

    The prompt changes from run to run, so results are only interpretable next
    to the exact text that produced them.
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(text.encode()).hexdigest()
    tmp = OUT_DIR / f".prompt-{os.getpid()}.tmp"
    tmp.write_text(f"<!-- sha256: {digest} · source: {PROMPT_PATH.relative_to(REPO)} -->\n\n{text}")
    # Servers run concurrently and write the same text; replace is atomic.
    tmp.replace(OUT_DIR / "prompt-AS-RUN.md")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server", required=True, choices=SERVERS)
    ap.add_argument("--shard", default="0/1", help="i/n — type only every n-th tool")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s %(message)s")

    template = _load_prompt()
    digest = _snapshot_prompt(template)
    logger.info("prompt %s… (%d chars)", digest[:12], len(template))

    i, n = (int(x) for x in args.shard.split("/"))
    tools = [t for k, t in enumerate(load_tools(args.server)) if k % n == i]
    logger.info("%s: typing %d tool(s) [shard %s]", args.server, len(tools), args.shard)

    results, failed, no_schema = [], [], []
    for tool in tools:
        name = tool["tool_name"]
        props = (tool["input_schema"] or {}).get("properties", {})
        if not props:
            # A tool with no declared inputs is a fact about the tool. Asking the
            # model about it invites it to invent the inputs it expects.
            logger.info("  -- %s declares no inputs; not sent to the model", name)
            no_schema.append(name)
            results.append({"tool_name": name, "arguments": [], "declared_arguments": 0,
                            "no_declared_schema": True})
            continue
        logger.info("  -> %s (%d argument(s))", name, len(props))
        reply = query_ollama(_prompt_for(template, tool))
        if not isinstance(reply, dict) or "arguments" not in reply:
            logger.warning("     no usable JSON for %s", name)
            failed.append(name)
            continue
        # Paths may be nested (files[].path); keep only those rooted in a
        # declared argument, so the model cannot add ones the tool lacks.
        # NB: not named ``args`` — that is the argparse namespace in this scope.
        arg_rows = [a for a in reply["arguments"] if isinstance(a, dict)
                    and str(a.get("path", "")).split(".")[0].split("[")[0] in props]
        results.append({"tool_name": name, "arguments": arg_rows,
                        "declared_arguments": len(props)})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = args.server if n == 1 else f"{args.server}.shard{i}"
    out = OUT_DIR / f"{stem}.json"
    catalog = CATALOGS[args.server]
    out.write_text(json.dumps({"server": args.server,
                               "catalog": {
                                   "path": str(catalog.path.relative_to(CAT_REPO)),
                                   "sha256": hashlib.sha256(
                                       catalog.path.read_bytes()).hexdigest(),
                                   "package": catalog.package,
                                   "captured": catalog.captured,
                               },
                               "prompt_sha256": digest,
                               "prompt": "prompt-AS-RUN.md",
                               "slurm_job": os.environ.get("SLURM_JOB_ID", ""),
                               "tools": results, "failed": failed,
                               "no_declared_schema": no_schema}, indent=2))
    logger.info("wrote %s (%d tool(s), %d failed, %d schemaless)",
                out, len(results), len(failed), len(no_schema))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
