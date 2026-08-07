"""Enrich a scan with per-tool atomic-operation flags and an input-risk ranking.

Two deterministic (no-LLM) additions layered on top of the existing scan:

* **atomic-op flag** — every tool is classified into the project's atomic-op
  taxonomy (``presentations/heatmap_byhand/csv/atomic_operations.csv``:
  EXECUTE/DELETE/OVERWRITE/… ranked by severity) using the existing
  :mod:`mcp_security.atomic_ops` rule classifier. Answers "what does this tool
  fundamentally *do*, and how dangerous is that verb".
* **input ranking** — each tool's input parameters are ranked by how much they
  can amplify risk (a free-form query/command, a list whose length is breadth, a
  destructive flag, a magnitude count, …), so an operator sees which input to
  watch first, from the tool's own schema.

Both are attached to the scan table (``tool_atomic_ops``, ``tool_input_ranking``)
so they ship inside ``reports/scan/<server>.json`` alongside the risk matrix.
"""

from __future__ import annotations

from dataclasses import dataclass

from mcp_security.atomic_ops import toollist_rules
from mcp_security.atomic_ops.classifier import DEFAULT_TAXONOMY, _to_op_set_and_severities
from mcp_security.atomic_ops.taxonomy import AtomicOp, load_taxonomy
from mcp_security.llm.ollama_client import query_ollama
from mcp_security.static_scoring.registry import ToolSpec

# Input-risk heuristic, most-amplifying first. Each rule matches on the parameter
# name (substring) and/or JSON-schema type, and assigns a 1–5 risk with a reason.
# A parameter takes the first (highest) rule it matches.


@dataclass(frozen=True)
class _InputRule:
    risk: int
    reason: str
    name_hints: tuple[str, ...] = ()
    types: tuple[str, ...] = ()
    trigger: str | None = (
        None  # best-effort critical condition (the rules can't know exact numbers)
    )


_INPUT_RULES: tuple[_InputRule, ...] = (
    _InputRule(
        5,
        "free-form query/command — unbounded reach; the whole payload is attacker-controlled",
        name_hints=("query", "sql", "command", "cmd", "script", "code", "expression", "filter"),
        trigger="unbounded / no bound on scope",
    ),
    _InputRule(
        4,
        "list/array — risk scales with its length (bulk reach, mass fan-out)",
        types=("array",),
        trigger="large list (bulk fan-out)",
    ),
    _InputRule(
        4,
        "payload content — injection / exfiltration / poisoning vector",
        name_hints=(
            "content",
            "body",
            "data",
            "payload",
            "text",
            "message",
            "blocks",
            "attachments",
        ),
    ),
    _InputRule(
        4,
        "escalating flag — flips the call to a wider/irreversible mode",
        name_hints=(
            "recursive",
            "force",
            "all",
            "confirm",
            "overwrite",
            "permanent",
            "cascade",
            "hard",
        ),
        trigger="flag set true",
    ),
    _InputRule(
        3,
        "magnitude/count — larger value means broader effect",
        name_hints=(
            "limit",
            "count",
            "max",
            "depth",
            "size",
            "number",
            "amount",
            "quantity",
            "n_",
            "per_page",
            "days",
        ),
        trigger="large value",
    ),
    _InputRule(
        2,
        "names the target resource — selects what the op touches",
        name_hints=(
            "path",
            "file",
            "repo",
            "owner",
            "channel",
            "calendar",
            "table",
            "branch",
            "id",
            "name",
            "url",
            "email",
            "recipient",
            "user",
            "event",
            "issue",
            "pull",
        ),
    ),
)
_DEFAULT_INPUT_RULE = _InputRule(1, "minor / structural parameter")


# Verb -> atomic-op fallback, most-severe first, matched as substrings of the
# (namespace-stripped, underscore-normalised) tool name. Used only when the rule
# classifier finds nothing, so EVERY tool still gets a best-effort flag.
_VERB_OPS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("execute", "exec", "invoke", "eval", "shell"), "EXECUTE"),
    (("delete", "remove", "drop", "destroy", "purge", "wipe", "clear"), "DELETE"),
    (("overwrite", "replace", "merge"), "OVERWRITE"),
    (
        (
            "send",
            "post",
            "publish",
            "broadcast",
            "invite",
            "email",
            "message",
            "notify",
            "reply",
            "share",
        ),
        "BROADCAST",
    ),
    (
        (
            "update",
            "edit",
            "modify",
            "patch",
            "mark",
            "rename",
            "respond",
            "manage",
            "leave",
            "set",
        ),
        "MODIFY",
    ),
    (("move", "transfer", "rename"), "MOVE"),
    (
        ("create", "add", "new", "insert", "push", "upload", "write", "join", "fork", "make"),
        "CREATE",
    ),
    (("search", "find", "query", "lookup"), "SEARCH"),
    (("list", "enumerate"), "LIST"),
    (
        (
            "describe",
            "info",
            "status",
            "meta",
            "freebusy",
            "current",
            "colors",
            "unread",
            "_me",
            "profile",
        ),
        "METADATA",
    ),
    (
        (
            "read",
            "get",
            "fetch",
            "download",
            "view",
            "show",
            "history",
            "content",
            "reties",
            "replies",
        ),
        "READ",
    ),
)
_FALLBACK_DEFAULT_OP = "READ"


@dataclass(frozen=True)
class AtomicFlag:
    """One tool's atomic-operation classification."""

    atomic_ops: list[str]
    primary_op: str
    severity: int
    severity_label: str
    source: str  # "rules" (the toollist classifier) or "verb-fallback"


def _verb_fallback_op(name: str) -> str:
    """Infer an atomic op from a tool name when the rule classifier found nothing."""
    lowered = name.lower().replace("-", "_")
    for hints, op in _VERB_OPS:
        if any(h in lowered for h in hints):
            return op
    return _FALLBACK_DEFAULT_OP


def _sev_for(op: str, taxonomy: list[AtomicOp]) -> tuple[int, str]:
    for entry in taxonomy:
        if entry.name == op:
            return entry.severity, entry.severity_label
    return 0, ""


def _classify_one(tool: ToolSpec, taxonomy: list[AtomicOp], op_rank: dict[str, int]) -> AtomicFlag:
    # Normalise hyphenated names (e.g. calendar `create-event`) for the rule set.
    norm_name = tool.name.replace("-", "_")
    hits = toollist_rules.classify_from_toollist(norm_name, tool.description, tool.input_schema)
    ops, sev, label = _to_op_set_and_severities(hits, taxonomy)
    if ops:
        primary = min(ops, key=lambda o: op_rank.get(o, 999))
        return AtomicFlag(sorted(ops), primary, sev, label, "rules")
    # Fallback: infer the verb so no tool is left unflagged.
    op = _verb_fallback_op(tool.name)
    sev, label = _sev_for(op, taxonomy)
    return AtomicFlag([op], op, sev, label, "verb-fallback")


def classify_tools_atomic(
    tools: list[ToolSpec], taxonomy: list[AtomicOp] | None = None
) -> dict[str, dict]:
    """Flag every tool with its atomic operation(s) + max severity from the taxonomy."""
    tax = taxonomy or load_taxonomy(DEFAULT_TAXONOMY)
    op_rank = {op.name: op.rank for op in tax}
    result: dict[str, dict] = {}
    for t in tools:
        flag = _classify_one(t, tax, op_rank)
        result[t.name] = {
            "atomic_ops": flag.atomic_ops,
            "primary_op": flag.primary_op,
            "severity": flag.severity,
            "severity_label": flag.severity_label,
            "source": flag.source,
        }
    return result


def _input_risk(param: dict) -> _InputRule:
    name = param.get("name", "").lower()
    ptype = str(param.get("type", "")).lower()
    for rule in _INPUT_RULES:
        if rule.types and ptype in rule.types:
            return rule
        if rule.name_hints and any(h in name for h in rule.name_hints):
            return rule
    return _DEFAULT_INPUT_RULE


def _rank_inputs_deterministic(tool: ToolSpec) -> list[dict]:
    """Rule-based ranking of a tool's inputs (the LLM-off / fallback path)."""
    ranked = [
        {
            "name": p["name"],
            "type": p.get("type", "any"),
            "required": p.get("required", False),
            "risk": (rule := _input_risk(p)).risk,
            "critical_trigger": rule.trigger,
            "reason": rule.reason,
        }
        for p in tool.parameters()
    ]
    ranked.sort(key=lambda r: (r["risk"], r["required"]), reverse=True)
    return ranked


_INPUT_RANK_PROMPT = """You are a security analyst reviewing one MCP tool's inputs \
for how they could be abused against the server.

Tool: {tool}
Description: {desc}
Input parameters:
{params}

For EVERY parameter, do two things:
1. rank how much its *value* can amplify the call's risk to the server — a
   free-form query/command or a payload the caller fully controls, a list whose
   length is breadth (bulk fan-out), a destructive or scope-widening flag, and a
   large magnitude/count are high; a parameter that merely names the target or is
   a fixed enum/structural field is low. Judge intent, not just the name.
2. if the parameter carries a MAGNITUDE (a money amount, a count, a list length,
   a row limit, a recursion depth, …), give the concrete value/condition at which
   the call should be treated as CRITICAL — e.g. "amount >= 100000",
   ">= 20 recipients", "unbounded (no LIMIT)". If it has no such threshold, use null.

Output ONLY a JSON object, every parameter listed exactly once:
{{"ranking": [{{"name": <parameter name>, "risk": <integer 1-5, 5=most amplifying>,
"critical_trigger": <string threshold or null>, "reason": "<one short clause>"}}]}}"""


def _rank_inputs_llm(tool: ToolSpec) -> list[dict] | None:
    """LLM ranking of a tool's inputs; None if the model is unreachable or unusable.

    Returns None (so the caller falls back to the deterministic ranking) unless the
    model returns a well-formed ranking covering *every* parameter exactly once.
    """
    params = tool.parameters()
    if not params:
        return []
    param_lines = "\n".join(
        f"- {p['name']} ({p.get('type', 'any')}"
        f"{', required' if p.get('required') else ''}): {(p.get('description') or '')[:90]}"
        for p in params
    )
    prompt = _INPUT_RANK_PROMPT.format(
        tool=tool.name, desc=(tool.description or "")[:200], params=param_lines
    )
    resp = query_ollama(prompt)
    if not isinstance(resp, dict) or not isinstance(resp.get("ranking"), list):
        return None
    by_name = {p["name"]: p for p in params}
    ranked: list[dict] = []
    seen: set[str] = set()
    for entry in resp["ranking"]:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if name not in by_name or name in seen:
            continue
        try:
            risk = max(1, min(5, int(entry.get("risk"))))
        except (TypeError, ValueError):
            continue
        trigger = entry.get("critical_trigger")
        ranked.append(
            {
                "name": name,
                "type": by_name[name].get("type", "any"),
                "required": by_name[name].get("required", False),
                "risk": risk,
                "critical_trigger": str(trigger)[:80] if trigger else None,
                "reason": str(entry.get("reason", ""))[:140],
            }
        )
        seen.add(name)
    if len(ranked) != len(params):  # must cover every parameter to be trusted
        return None
    ranked.sort(key=lambda r: (r["risk"], r["required"]), reverse=True)
    return ranked


def rank_tool_inputs(tools: list[ToolSpec], *, use_llm: bool = False) -> dict[str, dict]:
    """Rank each tool's inputs by risk. LLM when ``use_llm``, else the rule heuristic.

    Each tool maps to ``{"source": "llm"|"rules"|"rules-fallback", "inputs": [...]}``
    so the provenance of the ranking is explicit (an LLM ranking that failed
    degrades to the deterministic rules, tagged ``rules-fallback``).
    """
    ranking: dict[str, dict] = {}
    for tool in tools:
        inputs = None
        source = "rules"
        if use_llm:
            inputs = _rank_inputs_llm(tool)
            source = "llm" if inputs is not None else "rules-fallback"
        if inputs is None:
            inputs = _rank_inputs_deterministic(tool)
        ranking[tool.name] = {"source": source, "inputs": inputs}
    return ranking


def enrich_scan(table: dict, tools: list[ToolSpec], *, use_llm: bool = False) -> dict:
    """Attach ``tool_atomic_ops`` and ``tool_input_ranking`` to a scan table in place.

    The atomic-op flag is always the deterministic taxonomy match; the input
    ranking uses the LLM when ``use_llm`` is set (falling back to the rules).
    """
    table["tool_atomic_ops"] = classify_tools_atomic(tools)
    table["tool_input_ranking"] = rank_tool_inputs(tools, use_llm=use_llm)
    return table
