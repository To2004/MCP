"""Deterministic fallback for the static-scoring pipeline.

The pipeline prefers the local LLM, but the model is not always reachable (the
GPU node may be down, or the scan runs on the login node). These heuristics let
the pipeline still emit a complete, defensible table offline, derived from two
trustworthy signals: the server's self-declared tool annotations and the
security team's fixed sensitivity anchors in :mod:`mcp_security.sensitivity`.

Every value produced here is conservative (ties broken upward) and every table
built from it is flagged ``needs_human_review`` so a fallback table is never
mistaken for a model-reviewed one.
"""

from __future__ import annotations

from mcp_security.sensitivity import (
    DB_COLUMN_ANCHOR,
    FILETYPE_SENSITIVITY,
    SLACK_CHANNEL_ANCHOR,
    band_of,
)

from .registry import AssetSpec, ServerRegistry, ToolSpec

# Risk band (Critical/High/Medium/Low) → 1-5 sensitivity scale.
_BAND_TO_SENSITIVITY = {4: 5, 3: 4, 2: 3, 1: 2}

# Semantic escalation for asset *names/descriptions* the column/extension anchors
# miss (e.g. a table called ``api_keys`` whose column is just ``key``, or a
# ``.pem`` file type absent from FILETYPE_SENSITIVITY). Substring match against
# the asset id, description, and tags; the highest hit wins. Keeps the offline
# fallback from under-scoring crown-jewel assets.
_NAME_SENSITIVITY: dict[str, int] = {
    # Tier 5 — regulated/PII/financial/secrets, per scoring-reference.md's
    # sensitivity-5 row ("Financial records, PII, payslip data"). The crown jewels.
    "api_key": 5,
    "apikey": 5,
    "secret": 5,
    "credential": 5,
    "password": 5,
    "private_key": 5,
    "token": 5,
    ".pem": 5,
    ".key": 5,
    ".pfx": 5,
    ".p12": 5,
    ".env": 5,
    "ssn": 5,
    "credit_card": 5,
    "card_number": 5,
    "dob": 5,
    # Regulated PII — HIPAA medical records.
    "patient": 5,
    "medical": 5,
    "prescription": 5,
    "diagnosis": 5,
    "hipaa": 5,
    "health": 5,
    "xray": 5,
    "x-ray": 5,
    "intake": 5,
    # Financial / payslip records.
    "salary": 5,
    "payroll": 5,
    "invoice": 5,
    "financ": 5,
    "amount": 5,
    "payment": 5,
    "billing": 5,
    # Tier 4 — restricted business data, per scoring-reference.md's sensitivity-4
    # row ("Audit logs, source code, email"). Sensitive, but not crown-jewel.
    "employee": 4,
    "customer": 4,
    "email": 4,
    "grant": 4,
    "contract": 4,
    "classification": 4,
    "confidential": 4,
    "client": 4,
    "case": 4,
    "legal": 4,
    "privile": 4,
    ".sql": 4,
    ".c": 4,
    ".cpp": 4,
    ".h": 4,
    ".py": 4,
    ".js": 4,
    ".ts": 4,
    ".go": 4,
    ".java": 4,
    ".rb": 4,
}

# Tokens that force the maximum tool-impact tier (irreversible / destructive).
_DESTRUCTIVE_TOKENS = (
    "delete",
    "drop",
    "remove",
    "wipe",
    "overwrite",
    "exec",
    "shell",
    "truncate",
    "destroy",
    "revoke",
    "grant",
    "chmod",
)
# Tokens for recoverable state changes (tier 2) — includes messaging verbs so a
# slack-style ``post_message``/``reply``/``add_reaction`` is not mistaken for read-only.
_MUTATING_TOKENS = (
    "write",
    "edit",
    "insert",
    "update",
    "move",
    "rename",
    "create",
    "set",
    "post",
    "send",
    "reply",
    "react",
    "comment",
    "publish",
    "add",
)


def _text(tool: ToolSpec) -> str:
    return f"{tool.name} {tool.description}".lower()


def tool_impact(tool: ToolSpec) -> tuple[int, bool, str]:
    """Return ``(impact 1-3, irreversible, reasoning)`` for a tool.

    Read-only annotation pins tier 1; destructive tokens or a destructive
    annotation escalate toward tier 3; reversibility ties break upward.
    """
    text = _text(tool)
    if tool.read_only_hint is True and tool.destructive_hint is not True:
        return 1, False, "read_only_hint set; cannot change state"
    if any(tok in text for tok in _DESTRUCTIVE_TOKENS):
        return 3, True, "name/description implies an irreversible or access-changing action"
    if tool.destructive_hint is True:
        # Overwrite-style writes are clobbers (3); line edits are recoverable (2).
        if "overwrite" in text or "completely" in text:
            return 3, True, "destructive_hint set and operation overwrites existing state"
        return 2, False, "destructive_hint set but change is scoped/recoverable"
    if any(tok in text for tok in _MUTATING_TOKENS):
        return 2, False, "state-changing but generally recoverable"
    return 1, False, "no mutating capability detected"


def asset_sensitivity(asset: AssetSpec) -> tuple[int, list[str], str]:
    """Return ``(sensitivity 1-5, drivers, reasoning)`` from the fixed anchors.

    Filesystem assets key on extension; sqlite assets escalate to the most
    sensitive column anchor any of their columns matches.
    """
    drivers: list[str] = []
    best = 1
    for tag in asset.tags:
        if tag.startswith("ext:"):
            level = FILETYPE_SENSITIVITY.get(tag.split(":", 1)[1])
            if level:
                best = max(best, _BAND_TO_SENSITIVITY[band_of(level)])
                drivers.append(f"{tag} → {level}")
        elif tag.startswith("column:"):
            col = tag.split(":", 1)[1]
            level = DB_COLUMN_ANCHOR.get(col)
            if level:
                best = max(best, _BAND_TO_SENSITIVITY[band_of(level)])
                drivers.append(f"{col} → {level}")
        elif tag.startswith("channel:"):  # slack-style channel privacy
            level = SLACK_CHANNEL_ANCHOR.get(tag.split(":", 1)[1])
            if level:
                best = max(best, _BAND_TO_SENSITIVITY[band_of(level)])
                drivers.append(f"{tag} → {level}")
    # Semantic escalation: scan the asset's own name/description/tags for the
    # crown-jewel keywords the exact-match anchors above can miss.
    haystack = f"{asset.asset_id} {asset.description} {' '.join(asset.tags)}".lower()
    for keyword, value in _NAME_SENSITIVITY.items():
        if keyword in haystack and value > best:
            best = value
            drivers.append(f"name match {keyword!r} → {value}")
    reasoning = "; ".join(drivers) if drivers else "no anchor matched; defaulted to lowest tier"
    return best, drivers, reasoning


def blast_radius(tool: ToolSpec, asset: AssetSpec, sensitivity: int) -> tuple[int, str]:
    """Return ``(blast 0-5, rationale)`` for one (tool, asset) pair.

    Read-only tools are a narrow touch (1); mutating tools scale with their
    impact; a dangerous asset (sensitivity ≥ 4) escalates the reach by one,
    capped at 5 — mirroring the inferred ``dangerous_classes`` escalation.
    """
    impact, _, _ = tool_impact(tool)
    if impact == 1:
        base = 1
        why = "read-only touch"
    elif impact == 2:
        base = 2
        why = "scoped, recoverable modification"
    else:
        base = 5
        why = "clobber/destroy or irreversible action"
    if sensitivity >= 4 and base < 5:
        return min(base + 1, 5), f"{why}; +1 escalation for a dangerous asset class"
    return base, why


def domain_profile(registry: ServerRegistry) -> dict:
    """A per-kind inferred-domain profile, used when the LLM is unavailable."""
    templates = {
        "filesystem": {
            "mcp_kind": "filesystem",
            "asset_meaning": "a class of file the server can read or write, by type",
            "blast_radius_meaning": "from reading one file to overwriting or destroying many",
            "dangerous_classes": ["holds secrets/keys", "executable", "holds source code"],
            "irreversible_actions": ["overwrite", "delete", "move", "execute"],
            "worked_example": "write_file on a .pem = critical: clobbers key material irreversibly",
        },
        "sqlite": {
            "mcp_kind": "SQL database",
            "asset_meaning": "a table, sensitive in proportion to the columns it holds",
            "blast_radius_meaning": "from a scoped SELECT to a mass UPDATE/DELETE across rows",
            "dangerous_classes": ["holds secrets/API keys", "holds PII at scale", "financial"],
            "irreversible_actions": ["delete", "drop", "mass update"],
            "worked_example": "write_query on api_keys = critical: can wipe credentials irreversibly",
        },
        "slack": {
            "mcp_kind": "team messaging workspace",
            "asset_meaning": "a channel, sensitive in proportion to its privacy and audience",
            "blast_radius_meaning": "from reading one message to broadcasting to a private channel",
            "dangerous_classes": ["private/exec channels", "HR/PII channels", "incident channels"],
            "irreversible_actions": ["post to a wide audience", "leak private-channel content"],
            "worked_example": "post_message to exec-private = high: injects content into a "
            "restricted, high-trust channel",
        },
    }
    profile = templates.get(
        registry.kind,
        {
            "mcp_kind": registry.kind,
            "asset_meaning": "a category of protected object the server reaches",
            "blast_radius_meaning": "from a narrow read to an irreversible bulk action",
            "dangerous_classes": ["holds secrets", "irreversibly mutable"],
            "irreversible_actions": ["delete", "overwrite", "execute"],
            "worked_example": "a destructive tool on a secret-holding asset = critical",
        },
    )
    profile.update({"confidence": 0.6, "needs_human_review": True})
    return profile
