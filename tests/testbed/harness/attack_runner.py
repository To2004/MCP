"""MCP Attack Testbed — attack execution harness."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

# Ensure project root is on sys.path when the script is run directly
_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from tests.testbed.harness.scorer_bridge import score  # noqa: E402
from tests.testbed.harness.server_manager import install_server, load_profile, server_session  # noqa: E402
from tests.testbed.harness.tool_matcher import load_templates, match  # noqa: E402


RESULTS_DIR = Path(__file__).parent.parent / "results"
SERVERS_DIR = Path(__file__).parent.parent / "servers"


def _check_damage(response_text: str, damage_indicator: str | None) -> bool:
    """Return True if response_text matches the damage_indicator regex.

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
    """Extract plain text from an MCP tool response or raw requests.Response.

    Args:
        response: Either a ``requests.Response``, an ``mcp.types.CallToolResult``,
            or any other value that will be cast to str.

    Returns:
        The response body as a plain string.
    """
    if hasattr(response, "text"):
        return response.text  # requests.Response
    if hasattr(response, "content"):
        # mcp.types.CallToolResult
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)
    return str(response)


def _build_args(tool: Any, value: Any) -> dict[str, Any]:
    """Build a tool arguments dict from a payload value.

    Uses the first string parameter from inputSchema if available,
    otherwise uses ``{"input": value}`` as a fallback.

    Args:
        tool: An MCP Tool object with an ``inputSchema`` attribute.
        value: The payload value to assign to the first parameter.

    Returns:
        A dict mapping the first parameter name to *value*.
    """
    schema = getattr(tool, "inputSchema", {}) or {}
    props = schema.get("properties", {})
    if props:
        first_param = next(iter(props))
        return {first_param: value}
    return {"input": value}


async def _run_stdio_scenario(
    session: Any,
    template: dict[str, Any],
    mode: str,
    trials: int,
) -> list[dict[str, Any]]:
    """Run attack template against an already-initialised stdio session.

    Args:
        session: An initialised :class:`mcp.ClientSession`.
        template: A loaded attack template dict.
        mode: ``"attack"`` (execute only) or ``"eval"`` (execute + score).
        trials: Number of times to repeat each payload.

    Returns:
        List of result dicts, one per (payload, trial) combination.
    """
    tools_result = await session.list_tools()
    tools = tools_result.tools
    pairs = match(tools, [template])

    results: list[dict[str, Any]] = []
    for tool, tmpl in pairs:
        desc = tool.description or ""

        # Run malicious payloads
        for payload_entry in tmpl.get("payloads", []):
            label = payload_entry.get("label", "unknown")
            value = payload_entry.get("value", "")
            args = _build_args(tool, value)

            for _ in range(trials):
                t0 = time.perf_counter()
                try:
                    resp = await session.call_tool(tool.name, args)
                    resp_text = _response_to_text(resp)
                    error = None
                except Exception as exc:
                    resp_text = str(exc)
                    error = str(exc)
                latency_ms = (time.perf_counter() - t0) * 1000

                damage = _check_damage(resp_text, tmpl.get("damage_indicator"))
                scores = score(tool.name, args, desc, resp_text) if mode == "eval" else {}

                results.append({
                    "server": None,  # filled in by caller
                    "template_id": tmpl["id"],
                    "category": tmpl["category"],
                    "tool": tool.name,
                    "payload_label": label,
                    "payload_type": "malicious",
                    "args": args,
                    "response_snippet": resp_text[:300],
                    "damage_detected": damage,
                    "error": error,
                    "score": scores,
                    "latency_ms": latency_ms,
                })

        # Run benign payload
        benign = tmpl.get("benign_payload")
        if benign is not None:
            args = _build_args(tool, benign)
            t0 = time.perf_counter()
            try:
                resp = await session.call_tool(tool.name, args)
                resp_text = _response_to_text(resp)
                error = None
            except Exception as exc:
                resp_text = str(exc)
                error = str(exc)
            latency_ms = (time.perf_counter() - t0) * 1000
            scores = score(tool.name, args, desc, resp_text) if mode == "eval" else {}
            results.append({
                "server": None,
                "template_id": tmpl["id"],
                "category": tmpl["category"],
                "tool": tool.name,
                "payload_label": "benign",
                "payload_type": "benign",
                "args": args,
                "response_snippet": resp_text[:300],
                "damage_detected": False,
                "error": error,
                "score": scores,
                "latency_ms": latency_ms,
            })

    return results


def _run_http_scenario(
    profile: dict[str, Any],
    template: dict[str, Any],
    mode: str,
    trials: int,
) -> list[dict[str, Any]]:
    """Run attack template against an HTTP (DVMCP) server.

    Sends raw JSON-RPC 2.0 requests directly via ``requests`` because DVMCP
    uses HTTP POST rather than the stdio MCP transport.

    Args:
        profile: Server profile dict containing at minimum ``base_url`` and ``name``.
        template: A loaded attack template dict.
        mode: ``"attack"`` (execute only) or ``"eval"`` (execute + score).
        trials: Number of times to repeat each payload.

    Returns:
        List of result dicts, one per (tool, payload, trial) combination.
    """
    base_url = profile["base_url"]

    # Discover tools via tools/list
    tools_resp = requests.post(
        base_url,
        json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
        timeout=10,
    )
    tools_data = tools_resp.json().get("result", {}).get("tools", [])

    # Filter tools matching template keywords
    keywords = template.get("match_rules", {}).get("tool_name_contains", [])
    matching_tools = [
        t for t in tools_data
        if "*" in keywords or any(kw.lower() in t["name"].lower() for kw in keywords)
    ]

    results: list[dict[str, Any]] = []
    for tool_data in matching_tools:
        tool_name = tool_data["name"]
        desc = tool_data.get("description", "")

        for payload_entry in template.get("payloads", []):
            value = payload_entry.get("value", "")
            label = payload_entry.get("label", str(value)[:30])

            # Build args using the first property from inputSchema
            input_schema = tool_data.get("inputSchema", {})
            props = input_schema.get("properties", {})
            if props:
                first_param = next(iter(props))
                args: dict[str, Any] = {first_param: value}
            else:
                args = {"input": value}

            for _ in range(trials):
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
                damage = _check_damage(resp_text, template.get("damage_indicator"))
                scores = score(tool_name, args, desc, resp_text) if mode == "eval" else {}
                results.append({
                    "server": profile["name"],
                    "template_id": template["id"],
                    "category": template["category"],
                    "tool": tool_name,
                    "payload_label": label,
                    "payload_type": "malicious",
                    "args": args,
                    "response_snippet": resp_text[:300],
                    "damage_detected": damage,
                    "error": error,
                    "score": scores,
                    "latency_ms": latency_ms,
                })

        # Benign payload
        benign = template.get("benign_payload")
        if benign is not None:
            props = tool_data.get("inputSchema", {}).get("properties", {})
            first_param = next(iter(props)) if props else "input"
            benign_args: dict[str, Any] = {first_param: benign}
            t0 = time.perf_counter()
            try:
                resp = requests.post(
                    base_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": benign_args},
                        "id": 3,
                    },
                    timeout=5,
                )
                resp_text = json.dumps(resp.json().get("result", resp.text))
                error = None
            except Exception as exc:
                resp_text = str(exc)
                error = str(exc)
            latency_ms = (time.perf_counter() - t0) * 1000
            scores = score(tool_name, benign_args, desc, resp_text) if mode == "eval" else {}
            results.append({
                "server": profile["name"],
                "template_id": template["id"],
                "category": template["category"],
                "tool": tool_name,
                "payload_label": "benign",
                "payload_type": "benign",
                "args": benign_args,
                "response_snippet": resp_text[:300],
                "damage_detected": False,
                "error": error,
                "score": scores,
                "latency_ms": latency_ms,
            })

    return results


async def run_server(
    server_name: str,
    mode: str,
    trials: int,
    template_filter: str | None,
) -> list[dict[str, Any]]:
    """Run all matching attack templates against one server.

    Args:
        server_name: Profile filename stem (without ``.json``).
        mode: ``"attack"`` or ``"eval"``.
        trials: Repeat count per payload.
        template_filter: If set, only run the template whose id matches this value.

    Returns:
        List of result dicts from every template run against the server.
    """
    profile = load_profile(server_name)
    install_server(profile)
    templates = load_templates()
    if template_filter:
        templates = [t for t in templates if t["id"] == template_filter]

    all_results: list[dict[str, Any]] = []

    if profile["transport"] == "http":
        for template in templates:
            results = _run_http_scenario(profile, template, mode, trials)
            all_results.extend(results)
    else:
        async with server_session(profile) as session:
            for template in templates:
                results = await _run_stdio_scenario(session, template, mode, trials)
                for r in results:
                    r["server"] = server_name
                all_results.extend(results)

    return all_results


def format_result(result: dict[str, Any]) -> str:
    """Format a single result dict as a human-readable line.

    Args:
        result: A result dict produced by :func:`run_server`.

    Returns:
        A formatted string such as::

            [C2/path_traversal] read_file("../../etc/passwd") -> DAMAGE [+]  score: N/A
    """
    if result["payload_type"] == "benign":
        damage_str = "[benign] safe [ok]"
    elif result["damage_detected"]:
        damage_str = "DAMAGE [+]"
    else:
        damage_str = "no damage"

    score_val = result.get("score", {}).get("combined")
    score_str = f"score: {score_val:.1f}" if score_val is not None else "score: N/A"

    return (
        f"[{result['category']}/{result['template_id']}] "
        f"{result['tool']}({result['payload_label']!r}) -> {damage_str}  {score_str}"
    )


def print_results(results: list[dict[str, Any]]) -> None:
    """Print a human-readable summary of results to stdout.

    Args:
        results: List of result dicts from :func:`run_server`.
    """
    for r in results:
        print(format_result(r))


def save_results(
    results: list[dict[str, Any]],
    output_path: Path | None,
    server_name: str,
) -> Path:
    """Save results to a JSON file and return the path used.

    Args:
        results: List of result dicts to serialise.
        output_path: Explicit output path, or None to auto-generate one.
        server_name: Used to construct the auto-generated filename.

    Returns:
        The :class:`~pathlib.Path` where results were written.
    """
    RESULTS_DIR.mkdir(exist_ok=True)
    if output_path is None:
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        output_path = RESULTS_DIR / f"{server_name}_{ts}.json"
    output_path.write_text(json.dumps(results, indent=2))
    return output_path


def main() -> None:
    """CLI entry point for the MCP attack testbed.

    Usage examples::

        python attack_runner.py --server filesystem --mode attack
        python attack_runner.py --server filesystem --mode eval
        python attack_runner.py --server dvmcp --template command_injection --mode attack
        python attack_runner.py --all --mode attack
    """
    parser = argparse.ArgumentParser(description="MCP Attack Testbed Runner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--server", help="Server name to test (from servers/*.json)")
    group.add_argument("--all", action="store_true", help="Run all server profiles")
    parser.add_argument("--template", help="Only run this attack template ID")
    parser.add_argument("--mode", choices=["attack", "eval"], default="attack")
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.all:
        server_names = [p.stem for p in sorted(SERVERS_DIR.glob("*.json"))]
    else:
        server_names = [args.server]

    all_results: list[dict[str, Any]] = []
    for server_name in server_names:
        print(f"\n=== {server_name} ===")
        results = asyncio.run(run_server(server_name, args.mode, args.trials, args.template))
        print_results(results)
        all_results.extend(results)

    saved_path = save_results(
        all_results,
        args.output,
        server_names[0] if len(server_names) == 1 else "all",
    )
    print(f"\nResults saved to: {saved_path}")


if __name__ == "__main__":
    main()
