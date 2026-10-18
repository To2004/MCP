"""Optional LLM escalation stage: read the call's actual (normalized) input.

The static rubric scores a tool's general capability, not the specific intent
in its arguments (see ``reports/severity_eval/severity_analysis.md``): it rates
``echo 'Y3Vyb...' | base64 -d | bash`` as low because ``echo``/``bash`` are
unremarkable tools, missing the reverse shell in the payload. This stage
decodes common obfuscation and asks the local model to read the *decoded*
intent. It is an escalator only, and degrades to "no opinion" (``None``) if the
local model is unreachable — never fabricates a verdict, matching
:mod:`mcp_security.llm.ollama_client`'s no-cloud-fallback rule.
"""

from __future__ import annotations

import base64
import binascii
import re

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.param_scoring.combine import BANDS

# `=` padding is non-word, so a trailing \b would clip it off before a space;
# use base64-alphabet-aware lookaround instead so padding is captured too.
_BASE64_RE = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{16,}={0,2}(?![A-Za-z0-9+/=])")
_HEX_RE = re.compile(r"\b(?:[0-9A-Fa-f]{2}){8,}\b")
# `VAR=value` assignments followed by a `$VAR` use, e.g. `CMD=rm; ARGS='-rf /'; $CMD $ARGS`.
_SHELL_ASSIGN_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)=(['\"]?)([^;'\"\s]+)\2")

_VALID_BANDS = set(BANDS)

_JUDGE_PROMPT_TEMPLATE = """You are a security analyst reviewing one MCP tool call for malicious intent.

Tool: {tool}
Normalized arguments (obfuscation already decoded where detected): {args}

Classify the actual intent behind this call. Reply with ONLY a JSON object:
{{"band": "low|medium|high|critical", "reason": "<one sentence>"}}

"low"/"medium" = ordinary or unremarkable use. "high"/"critical" = evidence of
exfiltration, destructive action, privilege escalation, or obfuscated intent.
"""


def _try_base64_decode(token: str) -> str | None:
    try:
        decoded = base64.b64decode(token, validate=True)
    except (binascii.Error, ValueError):
        return None
    try:
        text = decoded.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text if text.isprintable() else None


def _try_hex_decode(token: str) -> str | None:
    try:
        decoded = bytes.fromhex(token)
    except ValueError:
        return None
    try:
        text = decoded.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text if text.isprintable() else None


def _expand_shell_vars(text: str) -> str:
    """Inline simple `VAR=value; ... $VAR ...` assignments so a judge sees the literal command."""
    assignments: dict[str, str] = {}
    for match in _SHELL_ASSIGN_RE.finditer(text):
        name, _quote, value = match.groups()
        assignments[name] = value
    expanded = text
    for name, value in assignments.items():
        expanded = re.sub(rf"\${{?{re.escape(name)}\}}?", value, expanded)
    return expanded


def normalize_value(value: str) -> str:
    """Decode base64/hex tokens and expand simple shell variable assignments in ``value``."""
    normalized = value
    for token in set(_BASE64_RE.findall(value)):
        decoded = _try_base64_decode(token)
        if decoded is not None:
            normalized = normalized.replace(token, f"{token} [decoded: {decoded}]")
    for token in set(_HEX_RE.findall(value)):
        decoded = _try_hex_decode(token)
        if decoded is not None:
            normalized = normalized.replace(token, f"{token} [decoded: {decoded}]")
    return _expand_shell_vars(normalized)


def normalize_args(args: dict) -> dict:
    """Apply :func:`normalize_value` to every string argument value."""
    return {
        key: normalize_value(value) if isinstance(value, str) else value
        for key, value in args.items()
    }


def judge_call(tool: str, args: dict) -> tuple[str, str] | None:
    """Ask the local model to classify a call's normalized intent.

    Returns ``(band, reason)``, or ``None`` if the model is unreachable or
    returns an unusable response — callers must not escalate on ``None``.
    """
    normalized = normalize_args(args)
    prompt = _JUDGE_PROMPT_TEMPLATE.format(tool=tool, args=normalized)
    response = query_ollama(prompt)
    if response is None:
        return None
    band = response.get("band")
    reason = response.get("reason", "")
    if band not in _VALID_BANDS:
        return None
    return band, reason
