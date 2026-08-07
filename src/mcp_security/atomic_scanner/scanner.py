"""Parse an MCP tool into the atomic operations it performs.

**Why a third method.** The framework already scores tool impact two ways: an
LLM reading the tool JSON, and `static_scoring.static_impact`, which matches
tiered verb patterns over the name and description. This module answers a
different question — *which operations does this tool perform?* — and derives the
impact tier afterwards, as ``max(ladder_tier)`` over the operations it found.

**Deliberately independent.** It shares no pattern table with `static_impact`.
Where that module scans prose for tier verbs, this one reads the tool the way a
developer names things:

1. **The name is a sentence.** `github_create_pull_request` is
   verb(`create`) + object(`pull_request`), with a service namespace in front.
   Tokenising the name and looking up the verb lemma is the primary signal.
2. **The schema is a contract.** A `content`/`body` parameter means data flows
   IN; a `query` parameter means the caller composes the operation; an array
   parameter means one call covers many targets.
3. **The annotations are a declaration.** `readOnlyHint` does not merely bound a
   tier — it makes every write operation impossible, so those hits are dropped.
4. **The description is the fallback**, consulted only for tools whose name says
   nothing (`super_option_tool`), because prose is where the other module lives
   and agreement there would be a shared blind spot rather than corroboration.

A tool performs a SET of operations, and the set is the useful output: a tool
that both READs and DELETEs is more interesting than its maximum alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .taxonomy import ladder_tier, load_taxonomy

# --- name morphology --------------------------------------------------------
# Service namespaces get stripped so `slack_list_channels` reads as
# `list channels`. Kept broad: MCP servers namespace heavily and inconsistently.
_NAMESPACES = (
    "slack",
    "github",
    "gh",
    "gdrive",
    "drive",
    "redis",
    "pg",
    "postgres",
    "git",
    "brave",
    "puppeteer",
    "mcp",
    "api",
    "tool",
    "data",
    "portfolio",
    "technical",
    "performance",
    "agents",
    "research",
    "journal",
    "watchlist",
    "equity",
    "derivatives",
    "economy",
    "fixedincome",
    "crypto",
    "etf",
    "index",
    "news",
    "regulators",
    "currency",
    "commodity",
)

# --- verb lemma -> atomic operation ----------------------------------------
# One entry per surface form. This is a VOCABULARY, not a tier table: the tier
# comes from the taxonomy csv, so re-ranking an operation is a data edit.
_VERB_OPS: dict[str, str] = {
    # no effect
    "ping": "NO_EFFECT",
    "health": "NO_EFFECT",
    "healthcheck": "NO_EFFECT",
    "heartbeat": "NO_EFFECT",
    "echo": "NO_EFFECT",
    "whoami": "NO_EFFECT",
    "version": "NO_EFFECT",
    "noop": "NO_EFFECT",
    "convert": "NO_EFFECT",
    # enumerate
    "list": "LIST",
    "ls": "LIST",
    "enumerate": "LIST",
    "index": "LIST",
    "catalog": "LIST",
    "browse": "LIST",
    "dir": "LIST",
    "tree": "LIST",
    "glob": "LIST",
    "walk": "LIST",
    "discover": "LIST",
    "inventory": "LIST",
    # about-ness
    "describe": "METADATA",
    "stat": "METADATA",
    "info": "METADATA",
    "metadata": "METADATA",
    "schema": "METADATA",
    "status": "METADATA",
    "exists": "METADATA",
    "count": "METADATA",
    "size": "METADATA",
    "availability": "METADATA",
    "freebusy": "METADATA",
    "profile": "METADATA",
    # consumption state — a write that changes no content
    "mark": "STATE_TOGGLE",
    "star": "STATE_TOGGLE",
    "unstar": "STATE_TOGGLE",
    "pin": "STATE_TOGGLE",
    "unpin": "STATE_TOGGLE",
    "mute": "STATE_TOGGLE",
    "unmute": "STATE_TOGGLE",
    "flag": "STATE_TOGGLE",
    "follow": "STATE_TOGGLE",
    "unfollow": "STATE_TOGGLE",
    "watch": "STATE_TOGGLE",
    "unwatch": "STATE_TOGGLE",
    "react": "STATE_TOGGLE",
    "acknowledge": "STATE_TOGGLE",
    # content in
    "read": "READ",
    "cat": "READ",
    "get": "READ",
    "fetch": "READ",
    "retrieve": "READ",
    "download": "READ",
    "export": "READ",
    "dump": "READ",
    "view": "READ",
    "show": "READ",
    "open": "READ",
    "preview": "READ",
    "inspect": "READ",
    "history": "READ",
    "log": "READ",
    "diff": "READ",
    "blame": "READ",
    "screenshot": "READ",
    "analyze": "READ",
    "analyse": "READ",
    "analysis": "READ",
    "summarize": "READ",
    "summarise": "READ",
    "summary": "READ",
    "compare": "READ",
    "calculate": "READ",
    "compute": "READ",
    "simulate": "READ",
    "backtest": "READ",
    "forecast": "READ",
    "screen": "READ",
    "evaluate": "READ",
    "report": "READ",
    "navigate": "READ",
    "parse": "READ",
    # targeted discovery
    "search": "SEARCH",
    "find": "SEARCH",
    "lookup": "SEARCH",
    "grep": "SEARCH",
    "query": "SEARCH",
    "filter": "SEARCH",
    # bring into existence
    "create": "CREATE",
    "add": "CREATE",
    "new": "CREATE",
    "make": "CREATE",
    "mkdir": "CREATE",
    "insert": "CREATE",
    "register": "CREATE",
    "draft": "CREATE",
    "provision": "CREATE",
    "allocate": "CREATE",
    "clone": "CREATE",
    "fork": "CREATE",
    "duplicate": "CREATE",
    "copy": "CREATE",
    "snapshot": "CREATE",
    "init": "CREATE",
    "initialize": "CREATE",
    "initialise": "CREATE",
    "install": "CREATE",
    "upload": "CREATE",
    "import": "CREATE",
    "branch": "CREATE",
    # data in, on top of what exists
    "write": "WRITE",
    "append": "WRITE",
    "post": "WRITE",
    "comment": "WRITE",
    "reply": "WRITE",
    "save": "WRITE",
    "store": "WRITE",
    "put": "WRITE",
    "record": "WRITE",
    "commit": "WRITE",
    "stage": "WRITE",
    "push": "WRITE",
    # change what is there
    "update": "MODIFY",
    "edit": "MODIFY",
    "modify": "MODIFY",
    "patch": "MODIFY",
    "set": "MODIFY",
    "amend": "MODIFY",
    "revise": "MODIFY",
    "adjust": "MODIFY",
    "annotate": "MODIFY",
    "tag": "MODIFY",
    "label": "MODIFY",
    "rename": "MODIFY",
    "close": "MODIFY",
    "reopen": "MODIFY",
    "archive": "MODIFY",
    "unarchive": "MODIFY",
    "restore": "MODIFY",
    "enable": "MODIFY",
    "disable": "MODIFY",
    "activate": "MODIFY",
    "deactivate": "MODIFY",
    "pause": "MODIFY",
    "resume": "MODIFY",
    "schedule": "MODIFY",
    "reschedule": "MODIFY",
    "accept": "MODIFY",
    "decline": "MODIFY",
    "rsvp": "MODIFY",
    "respond": "MODIFY",
    "vote": "MODIFY",
    "submit": "MODIFY",
    # relocate
    "move": "MOVE",
    "mv": "MOVE",
    "relocate": "MOVE",
    "sync": "MOVE",
    "mirror": "MOVE",
    # authorization
    "grant": "ACCESS_CHANGE",
    "revoke": "ACCESS_CHANGE",
    "permit": "ACCESS_CHANGE",
    "authorize": "ACCESS_CHANGE",
    "authorise": "ACCESS_CHANGE",
    "share": "ACCESS_CHANGE",
    "unshare": "ACCESS_CHANGE",
    "permissions": "ACCESS_CHANGE",
    # membership
    "join": "MEMBERSHIP",
    "leave": "MEMBERSHIP",
    "invite": "MEMBERSHIP",
    "subscribe": "MEMBERSHIP",
    "unsubscribe": "MEMBERSHIP",
    "assign": "MEMBERSHIP",
    "unassign": "MEMBERSHIP",
    "membership": "MEMBERSHIP",
    # settings
    "configure": "CONFIGURE",
    "config": "CONFIGURE",
    "setting": "CONFIGURE",
    "settings": "CONFIGURE",
    "manage": "CONFIGURE",
    "optimize": "CONFIGURE",
    "optimise": "CONFIGURE",
    # live UI
    "click": "INTERACT",
    "fill": "INTERACT",
    "hover": "INTERACT",
    "select": "INTERACT",
    "scroll": "INTERACT",
    "press": "INTERACT",
    # artifact production
    "train": "BUILD",
    "generate": "READ",
    "build": "BUILD",
    "compile": "BUILD",
    "render": "BUILD",
    # structural
    "alter": "SCHEMA_MODIFY",
    "migrate": "SCHEMA_MODIFY",
    # destroy
    "delete": "DELETE",
    "remove": "DELETE",
    "rm": "DELETE",
    "unlink": "DELETE",
    "destroy": "DELETE",
    "drop": "DELETE",
    "purge": "DELETE",
    "wipe": "DELETE",
    "erase": "DELETE",
    "truncate": "DELETE",
    "clear": "DELETE",
    "flush": "DELETE",
    "evict": "DELETE",
    "reset": "DELETE",
    "prune": "DELETE",
    "discard": "DELETE",
    "expire": "DELETE",
    "invalidate": "DELETE",
    "terminate": "DELETE",
    "kill": "DELETE",
    "cancel": "DELETE",
    "uninstall": "DELETE",
    "deprovision": "DELETE",
    "revert": "DELETE",
    "rollback": "DELETE",
    # replace wholesale
    "overwrite": "OVERWRITE",
    "replace": "OVERWRITE",
    # execution
    "execute": "EXECUTE",
    "exec": "EXECUTE",
    "eval": "EXECUTE",
    "invoke": "EXECUTE",
    # `run`/`execute` are re-decided by object in _ops_from_tokens: a command is
    # EXECUTE, a backtest is a computation. They stay in the map so the lookup
    # reaches them at all.
    "run": "EXECUTE",
    "trigger": "EXECUTE",
    "dispatch": "EXECUTE",
    # publication
    "deploy": "PUBLISH",
    "release": "PUBLISH",
    "publish": "PUBLISH",
    "merge": "PUBLISH",
    "rebase": "PUBLISH",
    # send outward
    "send": "BROADCAST",
    "email": "BROADCAST",
    "notify": "BROADCAST",
    "broadcast": "BROADCAST",
    "announce": "BROADCAST",
    "forward": "BROADCAST",
    "sms": "BROADCAST",
    "webhook": "BROADCAST",
    # money
    "buy": "TRANSACT",
    "sell": "TRANSACT",
    "trade": "TRANSACT",
    "charge": "TRANSACT",
    "refund": "TRANSACT",
    "payout": "TRANSACT",
    "withdraw": "TRANSACT",
    "deposit": "TRANSACT",
    "settle": "TRANSACT",
    "pay": "TRANSACT",
    "order": "TRANSACT",
}

# Operations that cannot happen on a tool declaring readOnlyHint: true.
_WRITE_OPS = frozenset(
    {
        "CREATE",
        "WRITE",
        "MODIFY",
        "MOVE",
        "DELETE",
        "OVERWRITE",
        "SCHEMA_MODIFY",
        "EXECUTE",
        "PUBLISH",
        "BROADCAST",
        "TRANSACT",
        "ACCESS_CHANGE",
        "MEMBERSHIP",
        "CONFIGURE",
        "INTERACT",
        "BUILD",
        "STATE_TOGGLE",
    }
)

# Some name tokens are objects that read like verbs. `trade` in
# `journal_add_trade` is what was added, not what was done; `order` in
# `get_order_book` is a market-data noun. A verb in the FIRST token position is
# the action; the same word later is only the action when nothing else claimed
# that role.
_OBJECT_ONLY_IF_LATE = frozenset(
    {
        "trade",
        "order",
        "share",
        "index",
        "log",
        "report",
        "screen",
        # nouns that name what came back, not what was done:
        # `conversations_replies`, `get_pull_request_comments`, `list_commits`
        "reply",
        "comment",
        "commit",
        "post",
        "record",
        "watch",
        "star",
        "flag",
        "tag",
        "label",
        # `list_branches` / `list_releases`: the object, not the act
        "branch",
        "release",
        "forward",
        "install",
    }
)

# `get`/`fetch`/`show` mean "something comes back" — they name no operation of
# their own. They contribute READ only when nothing more specific was found, so
# `get_file_info` is METADATA (from `info`) rather than READ.
_GENERIC_READ_VERBS = frozenset({"get", "fetch", "retrieve", "show", "view", "open"})

# Objects that make even a read a non-event: the answer is about the service.
_NO_EFFECT_OBJECTS = frozenset({"time", "clock", "uptime", "version", "ping", "health"})

# Enumerating CONTAINERS returns a catalog of names — metadata, not content.
# Searching for `code` or `issues` returns the substance and stays SEARCH.
_CONTAINER_OBJECTS = frozenset(
    {
        "file",
        "files",
        "directory",
        "directories",
        "folder",
        "folders",
        "repository",
        "repositories",
        "repo",
        "repos",
        "channel",
        "channels",
        "calendar",
        "calendars",
        "table",
        "tables",
        "database",
        "databases",
        "bucket",
        "buckets",
        "workspace",
        "workspaces",
    }
)

_SEP = re.compile(r"[_\-.\s]+")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _tokens(name: str) -> tuple[list[str], int]:
    """(word tokens, how many namespace tokens were stripped).

    The offset matters: stripping `journal` from `journal_trade_review` would
    otherwise promote `trade` to first position and turn a journal entry into a
    money movement.
    """
    words = [w.lower() for w in _SEP.split(_CAMEL.sub(" ", name)) if w]
    stripped = 0
    while len(words) > 1 and words[0] in _NAMESPACES:
        words = words[1:]
        stripped += 1
    return words, stripped


# Words whose -s is part of the word. Stripping it turns `news` into `new`
# (CREATE) and `status` into `statu`; the first cost two finance tools a tier.
_NEVER_LEMMATISE = frozenset(
    {"news", "status", "address", "process", "access", "business", "analysis", "series", "class"}
)


def _singular(word: str) -> str:
    """Crude lemma: strip a plural/3rd-person -s and common verb endings."""
    if word in _NEVER_LEMMATISE:
        return word
    for suffix, keep in (("ies", "y"), ("es", ""), ("s", ""), ("ing", ""), ("ed", "")):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            candidate = word[: -len(suffix)] + keep
            if candidate in _VERB_OPS:
                return candidate
    return word


@dataclass
class AtomicVerdict:
    """The operations one tool performs, and the impact tier they imply."""

    tool_name: str
    operations: set[str] = field(default_factory=set)
    #: (operation, what matched) — the audit trail
    evidence: list[tuple[str, str]] = field(default_factory=list)
    tool_impact: int = 1
    max_op: str = "NO_EFFECT"
    dropped_by_readonly: set[str] = field(default_factory=set)
    is_bulk: bool = False
    source: str = "name"

    @property
    def reasoning(self) -> str:
        ops = ", ".join(sorted(self.operations)) or "none"
        trail = "; ".join(f"{op} <- {why}" for op, why in self.evidence)
        return f"ops[{ops}] -> max {self.max_op} = tier {self.tool_impact} ({trail})"


def _params(tool) -> dict:
    schema = getattr(tool, "input_schema", None) or getattr(tool, "parameters", None) or {}
    return schema.get("properties", {}) if isinstance(schema, dict) else {}


def _ops_from_tokens(words: list[str], where: str, offset: int = 0) -> list[tuple[str, str]]:
    """Every verb token that maps to an operation, in order.

    Two things happen beyond the lookup, both about telling the ACT from the
    OBJECT — the same distinction a reader makes without noticing:

    * a late `trade`/`comment`/`commit` is what the tool acted on, not what it
      did (`list_commits` lists, it does not commit);
    * a generic `get`/`fetch` yields READ only if no specific operation was
      found, so `get_file_info` is METADATA and `get_current_time` is NO_EFFECT.
    """
    specific: list[tuple[str, str]] = []
    generic: list[tuple[str, str]] = []
    lemmas = [_singular(w) for w in words]
    for position, (word, lemma) in enumerate(zip(words, lemmas, strict=True)):
        if lemma in _NO_EFFECT_OBJECTS:
            specific.append(("NO_EFFECT", f"{where}:{word}"))
            continue
        op = _VERB_OPS.get(lemma)
        if op is None:
            continue
        if lemma in _OBJECT_ONLY_IF_LATE and position + offset > 0:
            continue
        if lemma in {"run", "execute", "exec"}:
            is_command = any(lem in _EXECUTION_OBJECTS for lem in lemmas)
            specific.append(
                ("EXECUTE", f"{where}:{word} over a command")
                if is_command
                else ("READ", f"{where}:{word} (computation, not a command)")
            )
            continue
        if lemma in _GENERIC_READ_VERBS:
            generic.append((op, f"{where}:{word} (generic)"))
            continue
        # enumerating containers is a catalog, not their contents
        if op in {"SEARCH", "LIST"} and any(lem in _CONTAINER_OBJECTS for lem in lemmas):
            specific.append(("LIST", f"{where}:{word} over a container"))
            continue
        specific.append((op, f"{where}:{word}"))
    if specific:
        return specific
    return generic


# `run`/`execute` name a computation as often as a command. The OBJECT decides:
# `run_query` executes, `run_backtest` computes.
_EXECUTION_OBJECTS = frozenset(
    {"command", "cmd", "script", "code", "shell", "query", "sql", "job", "program", "javascript"}
)


def _ops_from_schema(tool) -> list[tuple[str, str]]:
    """Operations implied by the parameter contract itself."""
    found: list[tuple[str, str]] = []
    for pname in _params(tool):
        low = pname.lower()
        if low in {"cmd", "command", "script", "code", "shell"}:
            found.append(("EXECUTE", f"param:{pname}"))
        elif low in {"content", "contents", "body", "text", "data", "value"}:
            # data flowing IN is a write; the verb decides create-vs-modify
            found.append(("WRITE", f"param:{pname}"))
        elif low in {"recipients", "to", "cc", "bcc", "channel_id_to"}:
            found.append(("BROADCAST", f"param:{pname}"))
    return found


def classify(tool) -> AtomicVerdict:
    """Parse one tool into its atomic operations and derive the impact tier."""
    name = getattr(tool, "name", "") or ""
    description = getattr(tool, "description", "") or ""
    read_only = getattr(tool, "read_only_hint", None)

    words, offset = _tokens(name)
    hits = _ops_from_tokens(words, "name", offset)
    source = "name"

    # The description is a FALLBACK only: prose is where static_impact lives, and
    # reading it here by default would turn corroboration into a shared blind spot.
    if not hits:
        first = re.split(r"(?<=[.!?])\s", description.strip())[0] if description else ""
        hits = _ops_from_tokens(_tokens(first)[0], "desc")
        source = "description" if hits else "none"

    # A `write_*` tool replaces the target's contents — the convention the
    # original toollist rules encode as "write_ prefix => OVERWRITE + WRITE".
    if words and words[0] in {"write", "overwrite", "put"}:
        hits.append(("OVERWRITE", f"name:{words[0]}_* replaces contents"))
    lowered = re.sub(r"[_\-.\s]+", "_", name.lower())
    if "create_or_update" in lowered or "or_overwrite" in lowered or "upsert" in lowered:
        hits.append(("OVERWRITE", "name: create-or-update in one call"))

    hits += _ops_from_schema(tool)

    # A read-only tool cannot perform a write operation, whatever it is called.
    dropped = {op for op, _ in hits if read_only is True and op in _WRITE_OPS}
    kept = [(op, why) for op, why in hits if op not in dropped]
    if read_only is True and not kept:
        kept = [("READ", "readOnlyHint=true with no read verb")]

    operations = {op for op, _ in kept}
    if not operations:
        # Nothing at all was recognised. A tool that names no operation is
        # assumed to read content — the same conservative default the ladder uses.
        operations = {"READ"}
        kept = [("READ", "no operation recognised (default)")]
        source = "default"

    taxonomy = load_taxonomy()
    max_op = max(operations, key=lambda op: (taxonomy[op].ladder_tier, taxonomy[op].severity))
    is_bulk = any(
        isinstance(spec, dict) and spec.get("type") == "array" for spec in _params(tool).values()
    )
    return AtomicVerdict(
        tool_name=name,
        operations=operations,
        evidence=kept,
        tool_impact=ladder_tier(max_op),
        max_op=max_op,
        dropped_by_readonly=dropped,
        is_bulk=is_bulk,
        source=source,
    )


def classify_all(tools) -> dict[str, AtomicVerdict]:
    """Every tool in a registry, keyed by tool name."""
    return {tool.name: classify(tool) for tool in tools}
