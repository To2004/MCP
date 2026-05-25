"""Classify atomic ops from a live MCP tool entry (name + description + schema).

These rules emphasise structural signals — name prefixes, schema shapes — over
keywords in prose. They run independently from readme_rules and may disagree.
"""

from __future__ import annotations

from .rules_base import Confidence, RuleHit

_NAME_PREFIX_OPS: dict[tuple[str, ...], str] = {
    ("list_", "ls_"): "LIST",
    ("search_", "find_", "web_search", "local_search"): "SEARCH",
    ("delete_", "remove_", "drop_", "destroy_"): "DELETE",
    ("move_", "rename_"): "MOVE",
}

_BARE_NAME_OPS: dict[str, str] = {
    "list": "LIST",
    "ls": "LIST",
    "search": "SEARCH",
    "find": "SEARCH",
    "delete": "DELETE",
    "remove": "DELETE",
    "drop": "DELETE",
    "destroy": "DELETE",
    "move": "MOVE",
    "rename": "MOVE",
}

_METADATA_NAME_KEYWORDS = ("info", "stat", "schema", "profile", "metadata", "size")
_FREEFORM_SQL_NAMES = (
    "write_query",
    "exec_query",
    "execute_query",
    "sql_exec",
    "run_sql",
)
_SQL_WORST_CASE_OPS = ("EXECUTE", "DELETE", "OVERWRITE", "SCHEMA_MODIFY", "WRITE")

# Service namespaces that often prefix tool names (slack_*, github_*, etc.).
# When stripped, the remaining name resembles the standard tool name and the
# prefix-based rules can match.
_SERVICE_NAMESPACES = (
    "slack_",
    "github_",
    "gh_",
    "gdrive_",
    "drive_",
    "redis_",
    "pg_",
    "postgres_",
    "git_",
    "brave_",
    "puppeteer_",
)


def _strip_namespace(name: str) -> str:
    lower = name.lower()
    for prefix in _SERVICE_NAMESPACES:
        if lower.startswith(prefix):
            return lower[len(prefix) :]
    return lower


def _by_name_prefix(name: str) -> list[RuleHit]:
    """LIST / SEARCH / DELETE / MOVE detection from name prefix or bare name.

    Also strips service namespaces (slack_, github_, ...) so namespaced names
    like `slack_list_channels` still match the `list_` rule, and recognises
    bare names like `list`, `search`, `delete`.
    """
    hits: list[RuleHit] = []
    candidates = {name.lower(), _strip_namespace(name)}
    seen_ops: set[str] = set()
    for cand in candidates:
        for prefixes, op in _NAME_PREFIX_OPS.items():
            for pfx in prefixes:
                if cand.startswith(pfx) or cand == pfx.rstrip("_"):
                    if op in seen_ops:
                        continue
                    seen_ops.add(op)
                    hits.append(
                        RuleHit(
                            rule_id=f"toollist.{op.lower()}.name_prefix",
                            atomic_op=op,
                            confidence=Confidence.HIGH,
                            matched_on=f"name_prefix:{pfx}",
                        )
                    )
                    break
    for cand in candidates:
        if cand in _BARE_NAME_OPS:
            op = _BARE_NAME_OPS[cand]
            if op in seen_ops:
                continue
            seen_ops.add(op)
            hits.append(
                RuleHit(
                    rule_id=f"toollist.{op.lower()}.bare_name",
                    atomic_op=op,
                    confidence=Confidence.HIGH,
                    matched_on=f"name:{cand}",
                )
            )
    return hits


def _read_or_metadata(name: str, desc: str) -> list[RuleHit]:
    """READ vs METADATA disambiguation via name pattern."""
    lower = name.lower()
    stripped = _strip_namespace(name)
    hits: list[RuleHit] = []
    desc_lower = desc.lower()
    read_prefix = ("read_", "get_", "fetch_", "view_", "show_", "open_")
    read_bare = {"fetch", "get", "read", "view", "show", "query", "open"}
    read_suffix = ("_read", "_get", "_fetch", "_show", "_log")
    looks_read = (
        stripped.startswith(read_prefix)
        or lower.startswith(read_prefix)
        or any(lower.endswith(s) for s in read_suffix)
        or any(lower.endswith(s) for s in ("_diff", "_diff_staged", "_diff_unstaged"))
        or stripped in read_bare
        or lower in read_bare
        or "shows the" in desc_lower
        or "shows changes" in desc_lower
        or "shows differences" in desc_lower
        or "navigates the" in desc_lower
        or "returns the commit log" in desc_lower
        or "prints" in desc_lower
        or "takes a screenshot" in desc_lower
        or "captures" in desc_lower
    )
    if looks_read:
        if any(kw in lower for kw in _METADATA_NAME_KEYWORDS):
            hits.append(
                RuleHit(
                    rule_id="toollist.metadata.name_pattern",
                    atomic_op="METADATA",
                    confidence=Confidence.HIGH,
                    matched_on=f"name_prefix+metadata_kw:{lower}",
                )
            )
        else:
            hits.append(
                RuleHit(
                    rule_id="toollist.read.name_prefix",
                    atomic_op="READ",
                    confidence=Confidence.HIGH,
                    matched_on=f"name:{lower}",
                )
            )
    if "describe_" in lower or lower.endswith("_info") or lower.endswith("_stat"):
        if not any(h.atomic_op == "METADATA" for h in hits):
            hits.append(
                RuleHit(
                    rule_id="toollist.metadata.describe",
                    atomic_op="METADATA",
                    confidence=Confidence.HIGH,
                    matched_on="name_pattern:describe/info/stat",
                )
            )
    return hits


def _write_create_overwrite(name: str, desc: str) -> list[RuleHit]:
    """WRITE / OVERWRITE / CREATE / SCHEMA_MODIFY / MODIFY detection.

    Considers both the literal name and the namespace-stripped form so
    `git_create_branch` is recognised as `create_branch`.
    """
    lower_options = {name.lower(), _strip_namespace(name)}
    hits: list[RuleHit] = []
    desc_lower = desc.lower()
    lower = name.lower()
    any_write = any(
        c.startswith("write_") for c in lower_options
    ) or "overwrites" in desc_lower
    if any_write:
        hits.append(
            RuleHit(
                rule_id="toollist.overwrite.write_or_keyword",
                atomic_op="OVERWRITE",
                confidence=Confidence.HIGH,
                matched_on="name_prefix:write_ or desc:overwrites",
            )
        )
        hits.append(
            RuleHit(
                rule_id="toollist.write.write_prefix",
                atomic_op="WRITE",
                confidence=Confidence.HIGH,
                matched_on="name_prefix:write_",
            )
        )
    elif any(
        c.startswith(("insert_", "append_", "add_", "create_", "post_", "commit"))
        for c in lower_options
    ):
        if not any(c.startswith("create_") and "directory" in c for c in lower_options):
            hits.append(
                RuleHit(
                    rule_id="toollist.write.write_prefix",
                    atomic_op="WRITE",
                    confidence=Confidence.HIGH,
                    matched_on=f"name_prefix:{lower.split('_')[0]}_",
                )
            )
    if any(c.startswith("create_") for c in lower_options) and (
        "table" in lower
        or "table" in desc_lower
        or "schema" in desc_lower
    ):
        hits.append(
            RuleHit(
                rule_id="toollist.schema_modify.create_table",
                atomic_op="SCHEMA_MODIFY",
                confidence=Confidence.HIGH,
                matched_on="name+desc:create_table",
            )
        )
    if any(c.startswith("create_") for c in lower_options) and not (
        "table" in lower or "table" in desc_lower or "schema" in desc_lower
    ):
        hits.append(
            RuleHit(
                rule_id="toollist.create.create_prefix",
                atomic_op="CREATE",
                confidence=Confidence.HIGH,
                matched_on="name_prefix:create_",
            )
        )
    if any(c.startswith("edit_") for c in lower_options) or "find-and-replace" in desc_lower:
        hits.append(
            RuleHit(
                rule_id="toollist.modify.edit_prefix",
                atomic_op="MODIFY",
                confidence=Confidence.HIGH,
                matched_on="name_prefix:edit_ or desc:find-and-replace",
            )
        )
    if any(c.startswith("update_") for c in lower_options) or "updates" in desc_lower:
        hits.append(
            RuleHit(
                rule_id="toollist.modify.update_prefix",
                atomic_op="MODIFY",
                confidence=Confidence.MEDIUM,
                matched_on="name_prefix:update_ or desc:updates",
            )
        )
    if any(c in {"set", "put"} or c.startswith(("set_", "put_")) for c in lower_options):
        hits.append(
            RuleHit(
                rule_id="toollist.overwrite.set",
                atomic_op="OVERWRITE",
                confidence=Confidence.MEDIUM,
                matched_on="name:set/put",
            )
        )
        hits.append(
            RuleHit(
                rule_id="toollist.write.set",
                atomic_op="WRITE",
                confidence=Confidence.MEDIUM,
                matched_on="name:set/put",
            )
        )
    if "records" in desc_lower and "step" in desc_lower:
        hits.append(
            RuleHit(
                rule_id="toollist.write.records",
                atomic_op="WRITE",
                confidence=Confidence.MEDIUM,
                matched_on="desc:records a step",
            )
        )
    if (
        "git_add" in lower
        or "git_add" in _strip_namespace(name).replace(_strip_namespace(name), name.lower())
    ):
        hits.append(
            RuleHit(
                rule_id="toollist.write.git_add",
                atomic_op="WRITE",
                confidence=Confidence.HIGH,
                matched_on="name:git_add",
            )
        )
    if any(c.startswith(("checkout", "reset", "init")) or c == "init" for c in lower_options):
        hits.append(
            RuleHit(
                rule_id="toollist.modify.git_state",
                atomic_op="MODIFY",
                confidence=Confidence.MEDIUM,
                matched_on="name:checkout/reset/init",
            )
        )
    return hits


def _broadcast(name: str, desc: str) -> list[RuleHit]:
    """BROADCAST detection from messaging-shaped names/descs."""
    lower = name.lower()
    desc_lower = desc.lower()
    if (
        "post_message" in lower
        or lower.endswith("_post_message")
        or "reply_to_thread" in lower
        or "send_email" in lower
        or "add_reaction" in lower
        or "post a message" in desc_lower
        or "sends an email" in desc_lower
        or "posts a comment" in desc_lower
    ):
        return [
            RuleHit(
                rule_id="toollist.broadcast.post_or_send",
                atomic_op="BROADCAST",
                confidence=Confidence.HIGH,
                matched_on="name/desc:post|send|reply|reaction",
            )
        ]
    return []


def _freeform_sql(name: str, desc: str, schema: dict) -> list[RuleHit]:
    """Worst-case ops for tools accepting freeform SQL strings."""
    lower = name.lower()
    desc_lower = desc.lower()
    hits: list[RuleHit] = []
    is_sql_exec = (
        lower in _FREEFORM_SQL_NAMES
        or ("query" in lower and ("write" in lower or "exec" in lower))
        or "non-select sql" in desc_lower
        or ("any" in desc_lower and "sql" in desc_lower)
    )
    if not is_sql_exec:
        return hits
    schema_has_query = (
        isinstance(schema, dict)
        and isinstance(schema.get("properties"), dict)
        and "query" in schema["properties"]
    )
    confidence = Confidence.HIGH if schema_has_query else Confidence.MEDIUM
    for op in _SQL_WORST_CASE_OPS:
        hits.append(
            RuleHit(
                rule_id=f"toollist.{op.lower()}.freeform_sql_worst_case",
                atomic_op=op,
                confidence=confidence,
                matched_on=f"name+schema:freeform_sql:{lower}",
            )
        )
    return hits


def _explicit_execute(name: str, desc: str) -> list[RuleHit]:
    """EXECUTE detection from shell-shaped names/descs and workflow triggers."""
    lower = name.lower()
    stripped = _strip_namespace(name)
    desc_lower = desc.lower()
    if (
        lower.startswith(("exec_", "run_", "shell_", "spawn_", "evaluate", "eval_"))
        or stripped.startswith(("exec_", "run_", "shell_", "spawn_", "evaluate", "eval_"))
        or lower in {"execute", "exec", "shell", "evaluate"}
        or stripped in {"execute", "exec", "shell", "evaluate"}
        or "shell command" in desc_lower
        or "arbitrary code" in desc_lower
        or "arbitrary javascript" in desc_lower
        or "subprocess" in desc_lower
        or lower.endswith("_trigger")
        or stripped.endswith("_trigger")
        or "trigger" in lower
        or "triggers a" in desc_lower
        or "workflow_dispatch" in desc_lower
        or "evaluates" in desc_lower
    ):
        return [
            RuleHit(
                rule_id="toollist.execute.shell_pattern",
                atomic_op="EXECUTE",
                confidence=Confidence.HIGH,
                matched_on="name/desc:shell|exec|trigger",
            )
        ]
    return []


def _create_directory(name: str, desc: str) -> list[RuleHit]:
    """CREATE detection for the special-case create_directory tool family."""
    lower = name.lower()
    if (lower.startswith("create_") and "directory" in lower) or lower.startswith(
        ("mkdir_", "make_directory")
    ):
        return [
            RuleHit(
                rule_id="toollist.create.directory",
                atomic_op="CREATE",
                confidence=Confidence.HIGH,
                matched_on=f"name:{lower}",
            )
        ]
    return []


def _push_merge_fork(name: str, desc: str) -> list[RuleHit]:
    """Source-control specific patterns: push/merge/fork land or duplicate code."""
    lower = name.lower()
    desc_lower = desc.lower()
    hits: list[RuleHit] = []
    if lower.startswith("push_") or "pushes" in desc_lower:
        hits.append(
            RuleHit(
                rule_id="toollist.write.push",
                atomic_op="WRITE",
                confidence=Confidence.HIGH,
                matched_on="name/desc:push",
            )
        )
    if lower.startswith("merge_") or " merges " in f" {desc_lower} ":
        hits.append(
            RuleHit(
                rule_id="toollist.write.merge",
                atomic_op="WRITE",
                confidence=Confidence.HIGH,
                matched_on="name/desc:merge",
            )
        )
    if lower.startswith("fork_") or "forks a" in desc_lower:
        hits.append(
            RuleHit(
                rule_id="toollist.create.fork",
                atomic_op="CREATE",
                confidence=Confidence.HIGH,
                matched_on="name/desc:fork",
            )
        )
    return hits


def _tree(name: str, desc: str) -> list[RuleHit]:
    """LIST detection for tree-shaped recursive directory tools."""
    lower = name.lower()
    desc_lower = desc.lower()
    if (
        "_tree" in lower
        or "directory_tree" in lower
        or "recursive tree" in desc_lower
    ):
        return [
            RuleHit(
                rule_id="toollist.list.tree",
                atomic_op="LIST",
                confidence=Confidence.HIGH,
                matched_on="name/desc:tree",
            )
        ]
    return []


def _list_suffix(name: str, desc: str) -> list[RuleHit]:
    """LIST detection for names ending in `_list` (e.g. actions_list)."""
    lower = name.lower()
    if lower.endswith("_list") or lower == "list":
        return [
            RuleHit(
                rule_id="toollist.list.suffix",
                atomic_op="LIST",
                confidence=Confidence.HIGH,
                matched_on="name_suffix:_list",
            )
        ]
    return []


def _star_dismiss(name: str, desc: str) -> list[RuleHit]:
    """Light-write / social-action patterns: star, dismiss, mark."""
    lower = name.lower()
    if lower.startswith(("star_", "unstar_")):
        return [
            RuleHit(
                rule_id="toollist.modify.star",
                atomic_op="MODIFY",
                confidence=Confidence.LOW,
                matched_on=f"name_prefix:{lower.split('_')[0]}_",
            )
        ]
    if lower.startswith("dismiss_") or lower.startswith("mark_"):
        return [
            RuleHit(
                rule_id="toollist.modify.dismiss",
                atomic_op="MODIFY",
                confidence=Confidence.MEDIUM,
                matched_on=f"name_prefix:{lower.split('_')[0]}_",
            )
        ]
    return []


def _dom_interaction(name: str, desc: str) -> list[RuleHit]:
    """MODIFY detection for browser DOM actions (puppeteer-style)."""
    desc_lower = desc.lower()
    if (
        "clicks an element" in desc_lower
        or "fills a form" in desc_lower
        or "selects an option from a dropdown" in desc_lower
        or "hovers the cursor" in desc_lower
        or "scrolls the page" in desc_lower
    ):
        return [
            RuleHit(
                rule_id="toollist.modify.dom_interaction",
                atomic_op="MODIFY",
                confidence=Confidence.MEDIUM,
                matched_on="desc:dom_interaction",
            )
        ]
    return []


def classify_from_toollist(
    tool_name: str, description: str, input_schema: dict
) -> list[RuleHit]:
    """Run all tool-list rules against a single tool and return collected hits.

    Multiple rules can fire and the same atomic op can be tagged by more than
    one rule. Hits are de-duplicated by (rule_id, atomic_op).
    """
    seen: set[tuple[str, str]] = set()
    out: list[RuleHit] = []
    rule_results: list[list[RuleHit]] = [
        _by_name_prefix(tool_name),
        _read_or_metadata(tool_name, description),
        _write_create_overwrite(tool_name, description),
        _broadcast(tool_name, description),
        _freeform_sql(tool_name, description, input_schema),
        _explicit_execute(tool_name, description),
        _create_directory(tool_name, description),
        _push_merge_fork(tool_name, description),
        _tree(tool_name, description),
        _star_dismiss(tool_name, description),
        _list_suffix(tool_name, description),
        _dom_interaction(tool_name, description),
    ]
    for batch in rule_results:
        for hit in batch:
            key = (hit.rule_id, hit.atomic_op)
            if key in seen:
                continue
            seen.add(key)
            out.append(hit)
    return out
