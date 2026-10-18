"""Type one server's tool inputs with the LLM, using the markdown as prompt.

v11: unlike v10's ``derive_input_types.py`` (one exclusive class per
argument), each argument gets a stacked feature vector
(``docs/standards/tool-input-features.md``). Tool operation context
(``mcp_security.atomic_ops``, rule-based, no LLM) and per-argument
structural facts (``input_feature_facts.py``, pure Python) are computed once
and handed to the model as given facts -- never re-derived by it.

Large tools are classified in more than one batch (see ``_BATCH_SIZE``) --
run5 found that a 57-fact tool's full prompt+reply routinely exceeded a
16384-token context, and raising that context globally caused a severe,
separately-confirmed regression (VRAM/KV-cache pressure forcing Ollama into
CPU offload, turning a 49-second call into 20 minutes). Batching stays
inside the context size already proven safe. Cross-argument composites
(``docs/standards/tool-input-features-composites.md``) are asked in one
extra call over the *whole* tool's arguments after all batches finish, so a
composite spanning two different batches (e.g. an argument in batch 1 paired
with one in batch 3) is never missed.
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

from input_feature_facts import facts_for  # noqa: E402
from mcp_catalogs import CATALOGS, REPO as CAT_REPO, load_tools  # noqa: E402
from mcp_security.atomic_ops.classifier import DEFAULT_TAXONOMY  # noqa: E402
from mcp_security.atomic_ops.taxonomy import load_taxonomy  # noqa: E402
from mcp_security.atomic_ops.toollist_rules import classify_from_toollist  # noqa: E402
from mcp_security.llm.ollama_client import query_ollama  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
PROMPT_PATH = REPO / "docs" / "standards" / "tool-input-features.md"
COMPOSITES_PROMPT_PATH = REPO / "docs" / "standards" / "tool-input-features-composites.md"
V11 = REPO / "reports" / "experiments" / "v11"
_RETRIES = 2  # shape-only retry: reformats well, a wrong-but-valid answer would not.
# 1 retry left a handful of small, structurally ordinary tools (push_files,
# create_issue, ...) failing across otherwise-clean runs with no size or
# content cause found -- occasional malformed-JSON generation, not a batching
# problem. A 3rd attempt is cheap for tools this small; raised to 2 (3
# attempts total) rather than chasing a root cause with diminishing returns.
_BATCH_SIZE = 20  # facts per classify call; see module docstring.

_REQUIRED_ARG_KEYS = {
    "path", "orderable", "selects_population", "expands_reach",
    "composes_new_content", "references_existing", "provenance",
    "commits_change", "scope_multiplier", "track_rarity",
    "track_concentration", "track_temporal_pattern", "reason", "confidence",
}
_COMPOSITE_SUMMARY_KEYS = (
    "path", "orderable", "selects_population", "expands_reach",
    "composes_new_content", "references_existing", "commits_change",
    "scope_multiplier",
)


def _run_dir() -> Path:
    """This run's folder. The sbatch script pins one for all servers via the
    environment; a bare invocation takes the next free number."""
    pinned = os.environ.get("MCP_INPUT_FEATURES_OUT")
    if pinned:
        return Path(pinned)
    used = [int(d.name[3:]) for d in V11.glob("run*") if d.name[3:].isdigit()]
    return V11 / f"run{max(used, default=0) + 1}"


OUT_DIR = _run_dir()

logger = logging.getLogger("derive_input_features")


def _load_prompt() -> str:
    """The prompt text for this run, read once (see derive_input_types.py's
    identical rationale: one read makes the sha256 snapshot honest)."""
    md = PROMPT_PATH.read_text(encoding="utf-8")
    md = md.split("## Notes for the caller")[0].rstrip()
    for placeholder in ("{tool_context_json}", "{structural_facts_json}", "{tool_json}"):
        if placeholder not in md:
            raise SystemExit(f"prompt file has no {placeholder} placeholder")
    return md


def _load_composites_prompt() -> str:
    md = COMPOSITES_PROMPT_PATH.read_text(encoding="utf-8")
    for placeholder in ("{tool_summary_json}", "{argument_flags_json}"):
        if placeholder not in md:
            raise SystemExit(f"composites prompt file has no {placeholder} placeholder")
    return md


def _tool_context(name: str, description: str, input_schema: dict, taxonomy) -> dict:
    """Rule-based atomic-op tags for this tool -- reused, never re-derived by the LLM.

    ``atomic_ops.toollist_rules`` matches ``snake_case`` prefixes
    (``create_``, ``delete_``, ...); calendar's real catalog is
    ``kebab-case`` (``create-event``). Normalizing hyphens to underscores
    here -- not inside the shared classifier -- is what makes the existing
    rules fire on this catalog; confirmed by testing that every calendar
    tool otherwise comes back with zero atomic-op tags.
    """
    hits = classify_from_toollist(name.replace("-", "_"), description, input_schema)
    severities = {op.name: (op.severity, op.severity_label) for op in taxonomy}
    ops = sorted({h.atomic_op for h in hits})
    pairs = [severities[o] for o in ops if o in severities]
    max_sev, label = (max(pairs, key=lambda p: p[0]) if pairs else (0, ""))
    return {"atomic_ops": ops, "max_severity": max_sev, "severity_label": label}


def _tool_summary(tool: dict) -> dict:
    return {"tool_name": tool["tool_name"], "description": tool.get("description", "")}


def _prompt_for(template: str, tool_context: dict, facts_batch: dict, tool: dict) -> str:
    """Fill the classify prompt's three placeholders.

    ``{tool_json}`` is name + description only, not the full ``input_schema``
    -- every schema-derived fact (type, bounds, enum, format, description) is
    already in ``facts_batch``. Sending both was what made ``create-event``'s
    prompt+reply too large for a modest context window; the model's real
    job needs facts once, not the raw schema *and* a summary of it.
    """
    text = template.replace("{tool_context_json}", json.dumps(tool_context, indent=1))
    text = text.replace("{structural_facts_json}", json.dumps(facts_batch, indent=1))
    text = text.replace("{tool_json}", json.dumps(_tool_summary(tool), indent=1))
    return text


def _snapshot(text: str, path_source: Path, filename: str) -> str:
    """Write a run's prompt beside its results; return its digest."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(text.encode()).hexdigest()
    tmp = OUT_DIR / f".{filename}-{os.getpid()}.tmp"
    tmp.write_text(f"<!-- sha256: {digest} · source: {path_source.relative_to(REPO)} -->\n\n{text}")
    tmp.replace(OUT_DIR / filename)
    return digest


def _batched(facts: dict, size: int) -> list[dict]:
    """Split ``{path: facts}`` into ordered chunks of at most ``size`` entries."""
    items = list(facts.items())
    return [dict(items[i:i + size]) for i in range(0, len(items), size)] or [{}]


def _valid_classify_reply(reply, props: dict) -> bool:
    """All-or-nothing shape check, mirroring scanner/breadth.py's retry template.

    A blank ``reason`` is a quality problem, not a shape violation -- gating
    the whole batch's reply on it (tried, then reverted) cost tools their
    entire result over one skipped field each, while the prompt's own rule
    against blank reasons already fixed it in every batch that otherwise
    succeeded. Missing reasons are recorded per-tool instead (see
    ``main()``), not silenced by discarding the whole reply.
    """
    if not isinstance(reply, dict) or not isinstance(reply.get("arguments"), list):
        return False
    for a in reply["arguments"]:
        if not isinstance(a, dict) or not _REQUIRED_ARG_KEYS.issubset(a.keys()):
            return False
        root = str(a.get("path", "")).split(".")[0].split("[")[0]
        if root not in props:
            return False
    return True


def _classify_batch(template: str, tool_context: dict, facts_batch: dict, tool: dict, props: dict):
    prompt = _prompt_for(template, tool_context, facts_batch, tool)
    for attempt in range(1 + _RETRIES):
        reply = query_ollama(prompt)
        if _valid_classify_reply(reply, props):
            return reply["arguments"]
        logger.warning("     attempt %d: no usable JSON for %s (batch of %d)",
                        attempt + 1, tool["tool_name"], len(facts_batch))
    return None


def _classify_tool(template: str, tool_context: dict, facts: dict, tool: dict, props: dict):
    """Classify every declared argument, batching if there are many.

    A single batch (the common case) behaves exactly as before. Multiple
    batches each get the full ``tool_context`` but only their own slice of
    facts, matching the prompt's instruction to describe only what it was
    shown. If any batch fails after retries, the whole tool is reported
    failed -- a partial ledger would be silently incomplete, which this
    project's ``no_declared_schema``/``failed`` conventions elsewhere always
    avoid by being explicit instead.
    """
    batches = _batched(facts, _BATCH_SIZE)
    if len(batches) > 1:
        logger.info("     %s: %d facts split into %d batches",
                    tool["tool_name"], len(facts), len(batches))
    all_args = []
    for batch in batches:
        args = _classify_batch(template, tool_context, batch, tool, props)
        if args is None:
            return None
        all_args.extend(args)
    return all_args


def _valid_composites_reply(reply) -> bool:
    return isinstance(reply, dict) and isinstance(reply.get("composites"), list)


def _composites_for(composites_template: str, tool: dict, tool_context: dict, arg_rows: list[dict]):
    """One extra call per tool, over the whole (possibly multi-batch) argument
    list, so a composite spanning two batches is never missed. A failure here
    does not fail the tool -- composites are a bonus signal, not core
    classification, and gating on them would throw away otherwise-good work."""
    summary = [{k: a.get(k) for k in _COMPOSITE_SUMMARY_KEYS} for a in arg_rows]
    text = composites_template.replace("{tool_summary_json}", json.dumps(_tool_summary(tool), indent=1))
    text = text.replace("{argument_flags_json}", json.dumps(summary, indent=1))
    for attempt in range(1 + _RETRIES):
        reply = query_ollama(text)
        if _valid_composites_reply(reply):
            return reply["composites"]
        logger.warning("     attempt %d: no usable composites JSON for %s",
                        attempt + 1, tool["tool_name"])
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server", required=True, choices=list(CATALOGS))
    ap.add_argument("--shard", default="0/1", help="i/n -- type only every n-th tool")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s %(message)s")

    template = _load_prompt()
    digest = _snapshot(template, PROMPT_PATH, "prompt-AS-RUN.md")
    logger.info("prompt %s... (%d chars)", digest[:12], len(template))
    composites_template = _load_composites_prompt()
    composites_digest = _snapshot(composites_template, COMPOSITES_PROMPT_PATH,
                                   "composites-prompt-AS-RUN.md")

    taxonomy = load_taxonomy(DEFAULT_TAXONOMY)

    i, n = (int(x) for x in args.shard.split("/"))
    tools = [t for k, t in enumerate(load_tools(args.server)) if k % n == i]
    logger.info("%s: typing %d tool(s) [shard %s]", args.server, len(tools), args.shard)

    results, failed, no_schema = [], [], []
    for tool in tools:
        name = tool["tool_name"]
        props = (tool["input_schema"] or {}).get("properties", {})
        if not props:
            logger.info("  -- %s declares no inputs; not sent to the model", name)
            no_schema.append(name)
            results.append({"tool_name": name, "arguments": [], "composites": [],
                            "declared_arguments": 0, "no_declared_schema": True})
            continue
        tool_context = _tool_context(name, tool.get("description", ""), tool["input_schema"], taxonomy)
        facts = facts_for(tool["input_schema"])
        logger.info("  -> %s (%d argument(s), ops=%s)", name, len(props), tool_context["atomic_ops"])
        args_out = _classify_tool(template, tool_context, facts, tool, props)
        if args_out is None:
            failed.append(name)
            continue
        # Paths may be nested (files[].path); keep only those rooted in a
        # declared argument, so the model cannot add ones the tool lacks.
        arg_rows = [a for a in args_out if isinstance(a, dict)
                    and str(a.get("path", "")).split(".")[0].split("[")[0] in props]
        empty_reasons = [a["path"] for a in arg_rows if not str(a.get("reason", "")).strip()]
        if empty_reasons:
            logger.warning("     %s: blank reason on %s", name, empty_reasons)
        composites = _composites_for(composites_template, tool, tool_context, arg_rows)
        results.append({"tool_name": name, "tool_context": tool_context,
                        "arguments": arg_rows, "composites": composites,
                        "declared_arguments": len(props), "empty_reasons": empty_reasons})

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
                               "composites_prompt_sha256": composites_digest,
                               "composites_prompt": "composites-prompt-AS-RUN.md",
                               "slurm_job": os.environ.get("SLURM_JOB_ID", ""),
                               "tools": results, "failed": failed,
                               "no_declared_schema": no_schema}, indent=2))
    logger.info("wrote %s (%d tool(s), %d failed, %d schemaless)",
                out, len(results), len(failed), len(no_schema))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
