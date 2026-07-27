"""Generate a generic affected-asset for a tool from its name + description only.

Some servers ship tools we have no curated asset model for. This module asks the
LLM: given ONE tool's name and description — and nothing else — name the generic
asset class the tool reads or changes (``channels_list`` -> ``channel-directory``).
The model is deliberately given **no organizational context**: it never sees the
org's real asset list (contracts, repo names, channel names), because at
generation time we don't know the org. Pure utility tools (clock, color palette)
must yield no asset rather than an invented one.

This stage is intentionally **separate from the normal scanner prompt chain**
(:mod:`mcp_security.static_scoring.prompts`): nothing here is injected into the
regular scan prompts sent to Ollama. Run it standalone::

    uv run python -m mcp_security.scanner.asset_gen --eval           # LLM check
    uv run python -m mcp_security.scanner.asset_gen --eval --no-llm  # heuristic smoke

The prompt is few-shot "trained" on a fixed slice of the curated tool->asset
list (:data:`FEW_SHOT`) and checked against the held-out remainder
(:data:`GROUND_TRUTH`); the two sets never overlap.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.static_scoring.registry import AssetSpec

logger = logging.getLogger(__name__)

# Tool-name tokens that mark a pure utility tool: no organizational state at all.
_UTILITY_TOKENS = {"time", "color", "colors", "ping", "health", "version", "echo"}
# Leading/trailing verb tokens stripped by the heuristic to find the state noun.
_VERB_TOKENS = {
    "list",
    "search",
    "find",
    "get",
    "read",
    "describe",
    "access",
    "create",
    "update",
    "delete",
    "remove",
    "add",
    "write",
    "push",
    "merge",
    "fork",
    "post",
    "reply",
    "send",
    "insert",
    "respond",
    "manage",
    "mark",
}
# Verbs whose target is the *catalog of objects*, not the objects' contents.
_CATALOG_VERBS = {"list", "search"}


@dataclass
class GeneratedAsset:
    """The generator's answer for one tool. ``asset_id is None`` = utility tool."""

    tool: str
    asset_id: str | None
    description: str
    kind: str  # "mutable-state" | "read-surface" | "none"
    source: str  # "llm" | "heuristic"

    def to_asset_spec(self) -> AssetSpec | None:
        if self.asset_id is None:
            return None
        return AssetSpec(
            asset_id=self.asset_id,
            description=f"generated from tool description: {self.description}",
            tags=(f"kind:{self.kind}", "source:generated"),
        )


# --- few-shot "training" slice + held-out ground truth ------------------------
# (tool, description, expected asset_id or None, kind). FEW_SHOT goes into the
# prompt; GROUND_TRUTH is the held-out check set. Keep them disjoint.
FEW_SHOT: list[tuple[str, str, str | None, str]] = [
    ("create_event", "Create an event with attendees.", "event-records", "mutable-state"),
    ("search_repositories", "Search repositories.", "repository-catalog", "read-surface"),
    ("slack_get_user_profile", "Get a user's detailed profile.", "user-directory", "read-surface"),
    ("push_files", "Push multiple files in one commit.", "branch-heads", "mutable-state"),
    ("get-current-time", "Get the current time.", None, "none"),
    (
        "send_email_invite",
        "Email an invite to external attendees.",
        "outbound-invite-email",
        "mutable-state",
    ),
]

GROUND_TRUTH: list[tuple[str, str, str | None, str]] = [
    ("slack_list_channels", "List channels in the workspace.", "channel-directory", "read-surface"),
    (
        "slack_get_channel_history",
        "Get recent messages from a channel.",
        "channel-messages",
        "read-surface",
    ),
    (
        "slack_get_thread_replies",
        "Get all replies in a message thread.",
        "channel-messages",
        "read-surface",
    ),
    ("slack_get_users", "List users in the workspace.", "user-directory", "read-surface"),
    ("slack_post_message", "Post a new message to a channel.", "channel-messages", "mutable-state"),
    (
        "slack_add_reaction",
        "Add a reaction emoji to a message.",
        "message-reactions",
        "mutable-state",
    ),
    (
        "list_calendars",
        "List the calendars the agent can access.",
        "calendar-directory",
        "read-surface",
    ),
    ("get_event", "Read one event's full details.", "event-records", "read-surface"),
    (
        "find_free_slot",
        "Find a free time slot across attendees.",
        "free-busy-availability",
        "read-surface",
    ),
    ("update_event", "Modify an existing event.", "event-records", "mutable-state"),
    ("delete_all_events", "Delete every event on a calendar.", "event-records", "mutable-state"),
    ("list-colors", "List the available event color palette.", None, "none"),
    ("get_issue", "Read an issue and its comments.", "issues-and-comments", "read-surface"),
    ("create_issue", "Open a new issue.", "issues-and-comments", "mutable-state"),
    (
        "merge_pull_request",
        "Merge a pull request into the base branch.",
        "pull-requests-and-reviews",
        "mutable-state",
    ),
    (
        "fork_repository",
        "Fork a repository to another account.",
        "org-external-copies",
        "mutable-state",
    ),
]


# --- prompt -------------------------------------------------------------------
_PROMPT_HEADER = """\
You name the ASSET a software tool affects, from the tool's name and description ALONE.

An asset is the generic class of state the tool reads or changes: a catalog of
objects, a collection of records, a stream of messages, an outbound side effect.

RULES:
- You know NOTHING about the organization using the tool. Use only generic domain
  nouns taken from the tool itself (channels, events, users, repositories) —
  NEVER invent organization-specific assets such as contract files, customer
  tables, project names or department data.
- asset_id is kebab-case. A tool that lists or searches objects affects the
  catalog of those objects (e.g. "channel-directory", "repository-catalog"); a
  tool that reads or edits the objects' contents affects the records themselves
  (e.g. "event-records", "channel-messages").
- kind is "mutable-state" if the tool changes the asset, "read-surface" if it
  only exposes it.
- A pure utility tool that touches no organizational state at all (current time,
  color palette, health check) gets {"asset_id": null, "kind": "none"}.

Respond with ONE JSON object:
{"asset_id": str | null, "description": str, "kind": "mutable-state" | "read-surface" | "none"}

EXAMPLES:
"""


def build_prompt(tool_name: str, description: str) -> str:
    """Assemble the few-shot prompt for one tool. Contains no org context."""
    shots = []
    for name, desc, asset, kind in FEW_SHOT:
        answer = {
            "asset_id": asset,
            "description": desc if asset else "no organizational state",
            "kind": kind,
        }
        shots.append(f"Tool: {name} — {desc}\n{json.dumps(answer)}")
    return (
        _PROMPT_HEADER
        + "\n\n".join(shots)
        + f"\n\nNow the real tool.\nTool: {tool_name} — {description}\n"
    )


# --- heuristic fallback (offline smoke only, never a real generation) ---------
def _tokens(name: str) -> list[str]:
    return [t for t in name.lower().replace("-", "_").split("_") if t]


def _singular(token: str) -> str:
    return token[:-1] if token.endswith("s") and len(token) > 3 else token


def _heuristic(tool_name: str, description: str) -> GeneratedAsset:
    """Verb-stripping fallback: crude but deterministic, for offline smoke runs."""
    tokens = _tokens(tool_name)
    if set(tokens) & _UTILITY_TOKENS:
        return GeneratedAsset(tool_name, None, "no organizational state", "none", "heuristic")
    verbs = [t for t in tokens if t in _VERB_TOKENS]
    nouns = [t for t in tokens if t not in _VERB_TOKENS] or tokens
    noun = "-".join(_singular(t) for t in nouns)
    catalog = bool(set(verbs) & _CATALOG_VERBS)
    asset_id = f"{noun}-directory" if catalog else f"{noun}-records"
    read_only_verbs = _CATALOG_VERBS | {"get", "read", "describe", "find", "access"}
    kind = "read-surface" if not verbs or set(verbs) <= read_only_verbs else "mutable-state"
    return GeneratedAsset(tool_name, asset_id, description, kind, "heuristic")


# --- generation ---------------------------------------------------------------
def generate_asset(tool_name: str, description: str, *, use_llm: bool = True) -> GeneratedAsset:
    """Generate the affected asset for one tool from its name + description only."""
    if use_llm:
        reply = query_ollama(build_prompt(tool_name, description))
        if reply is not None and "asset_id" in reply:
            asset_id = reply.get("asset_id")
            kind = str(reply.get("kind", "read-surface"))
            if asset_id is None or kind == "none":
                return GeneratedAsset(tool_name, None, "no organizational state", "none", "llm")
            return GeneratedAsset(
                tool_name, str(asset_id), str(reply.get("description", description)), kind, "llm"
            )
        logger.warning("asset_gen: LLM gave no usable answer for %s; using heuristic", tool_name)
    return _heuristic(tool_name, description)


def generate_assets(
    tools: list[tuple[str, str]], *, use_llm: bool = True
) -> dict[str, GeneratedAsset]:
    """Generate one affected asset per ``(tool_name, description)``, keyed by tool."""
    return {name: generate_asset(name, desc, use_llm=use_llm) for name, desc in tools}


# --- evaluation against the curated list --------------------------------------
# Interchangeable catalog-ish tokens: "channel-catalog" ~ "channel-directory".
_TOKEN_SYNONYMS = {"catalog": "directory", "listing": "directory", "index": "directory"}


def _norm_token(token: str) -> str:
    token = _singular(token)
    return _TOKEN_SYNONYMS.get(token, token)


def close_match(expected: str | None, got: str | None) -> bool:
    """Exact id, containment, or >=50% token overlap counts as 'something close'."""
    if expected is None or got is None:
        return expected == got
    if expected == got:
        return True
    a = {_norm_token(t) for t in expected.split("-")}
    b = {_norm_token(t) for t in got.split("-")}
    if a <= b or b <= a:
        return True
    return len(a & b) / len(a | b) >= 0.5


def evaluate(*, use_llm: bool = True) -> dict:
    """Check the generator on the held-out curated list; return per-tool results."""
    results = []
    for name, desc, expected, _kind in GROUND_TRUTH:
        gen = generate_asset(name, desc, use_llm=use_llm)
        results.append(
            {
                "tool": name,
                "expected": expected,
                "generated": gen.asset_id,
                "kind": gen.kind,
                "source": gen.source,
                "match": close_match(expected, gen.asset_id),
            }
        )
    n_match = sum(r["match"] for r in results)
    return {"results": results, "n": len(results), "n_match": n_match}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", action="store_true", help="run the held-out check")
    parser.add_argument("--no-llm", action="store_true", help="heuristic smoke mode")
    args = parser.parse_args()
    if not args.eval:
        parser.error("nothing to do: pass --eval")
    report = evaluate(use_llm=not args.no_llm)
    for r in report["results"]:
        flag = "ok " if r["match"] else "MISS"
        print(
            f"{flag} {r['tool']:28} expected={r['expected']}  got={r['generated']} ({r['source']})"
        )
    print(f"\n{report['n_match']}/{report['n']} close matches")


if __name__ == "__main__":
    main()
