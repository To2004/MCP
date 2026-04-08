"""MCP Attack Testbed — multi-step scenario runner."""

from __future__ import annotations

import asyncio
import fnmatch
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from tests.testbed.harness.scorer_bridge import score  # noqa: E402
from tests.testbed.harness.server_manager import install_server, load_profile, server_session  # noqa: E402


SCENARIOS_DIR = Path(__file__).parent.parent / "attack_scenarios"

_PLACEHOLDER_RE = re.compile(r"\{[^}]+\}")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_scenarios(path: str | Path) -> list[dict[str, Any]]:
    """Load all scenario JSON files from *path*.

    Args:
        path: Directory containing ``*.json`` scenario files.

    Returns:
        List of parsed scenario dicts, one per file.
    """
    path = Path(path)
    scenarios: list[dict[str, Any]] = []
    for json_file in sorted(path.glob("*.json")):
        scenarios.append(json.loads(json_file.read_text()))
    return scenarios


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_damage(response_text: str, damage_indicator: str | None) -> bool:
    """Return True if *response_text* matches the *damage_indicator* regex.

    Args:
        response_text: The tool response as a plain string.
        damage_indicator: A regex pattern to search for, or None.

    Returns:
        True if the pattern is found in response_text, False otherwise.
    """
    if not damage_indicator:
        return False
    return bool(re.search(damage_indicator, response_text, re.IGNORECASE))


def _response_to_text(response: Any) -> str:
    """Extract plain text from an MCP tool response.

    Args:
        response: A ``mcp.types.CallToolResult``, a ``requests.Response``,
            or any value that will be cast to str.

    Returns:
        The response body as a plain string.
    """
    if hasattr(response, "text"):
        return response.text
    if hasattr(response, "content"):
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)
    return str(response)


def _interpolate_args(args: dict[str, Any], captured: dict[str, str]) -> dict[str, Any]:
    """Replace ``{var}`` placeholders in string arg values with captured values.

    Args:
        args: The step's raw args dict, possibly containing ``{var}`` strings.
        captured: Dict of variable names to their captured response snippets.

    Returns:
        A new args dict with all placeholders substituted.
    """
    result: dict[str, Any] = {}
    for key, value in args.items():
        if isinstance(value, str):
            for var_name, var_value in captured.items():
                value = value.replace(f"{{{var_name}}}", var_value)
            remaining = _PLACEHOLDER_RE.findall(value)
            if remaining:
                value = f"[UNRESOLVED:{','.join(remaining)}]" + value
        result[key] = value
    return result


def _find_tool_stdio(tool_name: str, tools: list[Any]) -> Any | None:
    """Return the first tool whose name matches *tool_name* as a glob pattern.

    Args:
        tool_name: Glob pattern (e.g. ``"read*"`` or ``"*admin*"``).
        tools: List of MCP Tool objects from ``session.list_tools()``.

    Returns:
        The first matching Tool object, or None.
    """
    for tool in tools:
        if fnmatch.fnmatch(tool.name, tool_name):
            return tool
    return None


def _find_tool_http(tool_name: str, tools_data: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the first tool dict whose name matches *tool_name* as a glob pattern.

    Args:
        tool_name: Glob pattern (e.g. ``"read*"`` or ``"*admin*"``).
        tools_data: List of tool dicts from the JSON-RPC ``tools/list`` response.

    Returns:
        The first matching tool dict, or None.
    """
    for tool in tools_data:
        if fnmatch.fnmatch(tool["name"], tool_name):
            return tool
    return None


def _make_result(
    server_name: str,
    scenario: dict[str, Any],
    step: dict[str, Any],
    tool_name: str,
    args: dict[str, Any],
    resp_text: str,
    damage: bool,
    error: str | None,
    scores: dict[str, Any],
    latency_ms: float,
) -> dict[str, Any]:
    """Build a standardised result dict for one scenario step.

    Args:
        server_name: Name of the server under test.
        scenario: The parent scenario dict (provides id and category).
        step: The step dict (provides step number).
        tool_name: The resolved tool name that was called.
        args: The arguments passed to the tool.
        resp_text: Full response text (snippet stored in result).
        damage: Whether the damage indicator matched.
        error: Exception string if the call failed, else None.
        scores: Dict from scorer_bridge.score().
        latency_ms: Wall-clock call latency in milliseconds.

    Returns:
        A result dict matching the standard testbed result schema.
    """
    return {
        "server": server_name,
        "template_id": scenario["id"],
        "category": scenario["category"],
        "tool": tool_name,
        "payload_label": f"step_{step['step']}",
        "payload_type": "malicious",
        "args": args,
        "response_snippet": resp_text[:300],
        "damage_detected": damage,
        "error": error,
        "score": scores,
        "latency_ms": latency_ms,
    }


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------


async def _run_scenario_stdio(
    session: Any,
    scenario: dict[str, Any],
    server_name: str,
    mode: str,
) -> list[dict[str, Any]]:
    """Execute a scenario against an already-initialised stdio ClientSession.

    Args:
        session: An initialised :class:`mcp.ClientSession`.
        scenario: A loaded scenario dict.
        server_name: Name of the server under test.
        mode: ``"attack"`` (execute only) or ``"eval"`` (execute + score).

    Returns:
        List of result dicts, one per step.
    """
    tools_result = await session.list_tools()
    tools = tools_result.tools
    captured: dict[str, str] = {}
    results: list[dict[str, Any]] = []

    for step in scenario.get("steps", []):
        pattern = step["tool"]
        tool = _find_tool_stdio(pattern, tools)

        if tool is None:
            results.append(_make_result(
                server_name, scenario, step,
                tool_name=pattern,
                args=step.get("args", {}),
                resp_text=f"no tool matched pattern '{pattern}'",
                damage=False,
                error=f"no tool matched pattern '{pattern}'",
                scores={},
                latency_ms=0.0,
            ))
            continue

        args = _interpolate_args(step.get("args", {}), captured)
        desc = tool.description or ""

        t0 = time.perf_counter()
        try:
            resp = await session.call_tool(tool.name, args)
            resp_text = _response_to_text(resp)
            error = None
        except Exception as exc:
            resp_text = str(exc)
            error = str(exc)
        latency_ms = (time.perf_counter() - t0) * 1000

        if "capture" in step:
            captured[step["capture"]] = resp_text[:300]

        damage = (
            _check_damage(resp_text, scenario.get("damage_indicator"))
            if step.get("damage_check", False)
            else False
        )
        scores = score(tool.name, args, desc, resp_text) if mode == "eval" else {}

        results.append(_make_result(
            server_name, scenario, step,
            tool_name=tool.name,
            args=args,
            resp_text=resp_text,
            damage=damage,
            error=error,
            scores=scores,
            latency_ms=latency_ms,
        ))

    return results


def _run_scenario_http(
    profile: dict[str, Any],
    scenario: dict[str, Any],
    server_name: str,
    mode: str,
) -> list[dict[str, Any]]:
    """Execute a scenario against an HTTP MCP server via raw JSON-RPC calls.

    Args:
        profile: Server profile dict containing at minimum ``base_url`` and ``name``.
        scenario: A loaded scenario dict.
        server_name: Name of the server under test.
        mode: ``"attack"`` (execute only) or ``"eval"`` (execute + score).

    Returns:
        List of result dicts, one per step.
    """
    base_url = profile["base_url"]

    try:
        tools_resp = requests.post(
            base_url,
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
            timeout=10,
        )
        tools_data: list[dict[str, Any]] = tools_resp.json().get("result", {}).get("tools", [])
    except Exception:
        return []

    captured: dict[str, str] = {}
    results: list[dict[str, Any]] = []

    for step in scenario.get("steps", []):
        pattern = step["tool"]
        tool_data = _find_tool_http(pattern, tools_data)

        if tool_data is None:
            results.append(_make_result(
                server_name, scenario, step,
                tool_name=pattern,
                args=step.get("args", {}),
                resp_text=f"no tool matched pattern '{pattern}'",
                damage=False,
                error=f"no tool matched pattern '{pattern}'",
                scores={},
                latency_ms=0.0,
            ))
            continue

        tool_name = tool_data["name"]
        desc = tool_data.get("description", "")
        args = _interpolate_args(step.get("args", {}), captured)

        t0 = time.perf_counter()
        try:
            resp = requests.post(
                base_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": args},
                    "id": 2,
                },
                timeout=5,
            )
            resp_text = json.dumps(resp.json().get("result", resp.text))
            error = None
        except Exception as exc:
            resp_text = str(exc)
            error = str(exc)
        latency_ms = (time.perf_counter() - t0) * 1000

        if "capture" in step:
            captured[step["capture"]] = resp_text[:300]

        damage = (
            _check_damage(resp_text, scenario.get("damage_indicator"))
            if step.get("damage_check", False)
            else False
        )
        scores = score(tool_name, args, desc, resp_text) if mode == "eval" else {}

        results.append(_make_result(
            server_name, scenario, step,
            tool_name=tool_name,
            args=args,
            resp_text=resp_text,
            damage=damage,
            error=error,
            scores=scores,
            latency_ms=latency_ms,
        ))

    return results


async def run_scenario(
    scenario: dict[str, Any],
    profile: dict[str, Any],
    server_name: str,
    mode: str,
) -> list[dict[str, Any]]:
    """Execute a single multi-step scenario against a server.

    Opens a shared session for the entire scenario so all steps share context.
    Tool arguments may reference values captured from prior steps using
    ``{variable_name}`` syntax.

    Args:
        scenario: A loaded scenario dict (see SCENARIOS_DIR README for schema).
        profile: Server profile dict from :func:`server_manager.load_profile`.
        server_name: Name of the server under test.
        mode: ``"attack"`` (execute only) or ``"eval"`` (execute + score).

    Returns:
        List of result dicts, one per step, in step order.
    """
    async with server_session(profile) as handle:
        transport = profile.get("transport", "stdio")
        if transport == "http":
            return _run_scenario_http(handle, scenario, server_name, mode)
        else:
            return await _run_scenario_stdio(handle, scenario, server_name, mode)


async def run_server_scenarios(
    server_name: str,
    mode: str,
) -> list[dict[str, Any]]:
    """Run all compatible scenarios against one server.

    Loads the server profile and all scenarios, filters by transport
    compatibility, and runs each matching scenario in order.

    Args:
        server_name: Profile filename stem (without ``.json``).
        mode: ``"attack"`` or ``"eval"``.

    Returns:
        Accumulated list of result dicts from all scenario steps.
    """
    profile = load_profile(server_name)
    install_server(profile)
    scenarios = load_scenarios(SCENARIOS_DIR)
    transport = profile.get("transport", "stdio")

    all_results: list[dict[str, Any]] = []
    for scenario in scenarios:
        supported = scenario.get("transport_support", [])
        if transport not in supported:
            continue
        print(f"  [scenario] {scenario['id']}")
        results = await run_scenario(scenario, profile, server_name, mode)
        for r in results:
            print(
                f"    [{r['category']}/{r['template_id']}] "
                f"{r['tool']}({r['payload_label']!r}) -> "
                f"{'DAMAGE [+]' if r['damage_detected'] else 'no damage'}"
                f"{'  ERR' if r['error'] else ''}"
            )
        all_results.extend(results)

    return all_results
