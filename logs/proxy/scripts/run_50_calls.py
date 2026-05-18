"""
50 varied MCP tool calls against the Filesystem MCP proxy (no auth required).

Backend: @modelcontextprotocol/server-filesystem
No credentials needed — path-scoping is the only protection layer.

Outputs:
  calls.csv         — machine-readable row per call (raw data)
  calls_report.txt  — human-readable formatted session report
"""

import asyncio
import csv
import time
from collections import defaultdict
from datetime import datetime, timezone

from mcp import ClientSession
from mcp.client.sse import sse_client

PROXY_URL = "http://localhost:8080/sse"
CSV_FILE = "logs/proxy/calls.csv"
REPORT_FILE = "logs/proxy/calls_report.txt"

ROOT = "C:/Users/user/Documents/GitHub/MCP"

CALLS = [
    # ── VALID CALLS ────────────────────────────────────────────────────────────
    ("VALID", "list_allowed_directories",  {}),
    ("VALID", "list_directory",            {"path": ROOT}),
    ("VALID", "list_directory",            {"path": f"{ROOT}/src"}),
    ("VALID", "list_directory_with_sizes", {"path": ROOT}),
    ("VALID", "directory_tree",            {"path": f"{ROOT}/src"}),
    ("VALID", "get_file_info",             {"path": f"{ROOT}/CLAUDE.md"}),
    ("VALID", "get_file_info",             {"path": f"{ROOT}/pyproject.toml"}),
    ("VALID", "read_file",                 {"path": f"{ROOT}/CLAUDE.md"}),
    ("VALID", "read_text_file",            {"path": f"{ROOT}/pyproject.toml"}),
    ("VALID", "read_multiple_files",       {"paths": [f"{ROOT}/CLAUDE.md", f"{ROOT}/pyproject.toml"]}),
    ("VALID", "search_files",             {"path": ROOT, "pattern": "*.py"}),
    ("VALID", "search_files",             {"path": ROOT, "pattern": "*.md"}),
    ("VALID", "search_files",             {"path": f"{ROOT}/src", "pattern": "*.py"}),
    ("VALID", "read_file",                {"path": f"{ROOT}/logs/proxy/calls.csv"}),
    ("VALID", "list_directory",           {"path": f"{ROOT}/docs"}),
    # ── WRONG TOOL NAME ────────────────────────────────────────────────────────
    ("BAD_TOOL", "non-existent-tool",     {}),
    ("BAD_TOOL", "readFile",              {}),
    ("BAD_TOOL", "read_File",             {}),
    ("BAD_TOOL", "listDirectory",         {}),
    ("BAD_TOOL", "list-directory",        {}),
    ("BAD_TOOL", "delete_file",           {}),
    ("BAD_TOOL", "execute_command",       {}),
    ("BAD_TOOL", "",                      {}),
    ("BAD_TOOL", "admin-override",        {}),
    ("BAD_TOOL", "write-file",            {}),
    # ── MISSING / WRONG PARAMS ─────────────────────────────────────────────────
    ("BAD_PARAMS", "read_file",           {}),
    ("BAD_PARAMS", "list_directory",      {}),
    ("BAD_PARAMS", "write_file",          {"path": f"{ROOT}/test.txt"}),
    ("BAD_PARAMS", "get_file_info",       {}),
    ("BAD_PARAMS", "search_files",        {"path": ROOT}),
    ("BAD_PARAMS", "move_file",           {"source": f"{ROOT}/CLAUDE.md"}),
    ("BAD_PARAMS", "read_multiple_files", {}),
    ("BAD_PARAMS", "edit_file",           {"path": f"{ROOT}/CLAUDE.md"}),
    ("BAD_PARAMS", "read_file",           {"path": 12345}),
    ("BAD_PARAMS", "directory_tree",      {}),
    # ── EDGE CASES / ATTACK-LIKE ───────────────────────────────────────────────
    ("EDGE", "read_file",                 {"path": "../../etc/passwd"}),
    ("EDGE", "read_file",                 {"path": f"{ROOT}/../../../etc/passwd"}),
    ("EDGE", "list_directory",            {"path": "C:/Windows/System32"}),
    ("EDGE", "read_file",                 {"path": f"{ROOT}/\x00evil"}),
    ("EDGE", "search_files",             {"path": ROOT, "pattern": "*"}),
    ("EDGE", "read_file",                 {"path": f"{ROOT}/" + "../" * 20 + "etc/passwd"}),
    ("EDGE", "get_file_info",             {"path": f"{ROOT}/%2e%2e%2fetc%2fpasswd"}),
    ("EDGE", "list_directory",            {"path": f"{ROOT}/../../../../"}),
    ("EDGE", "search_files",             {"path": ROOT, "pattern": "*.key"}),
    ("EDGE", "read_file",                 {"path": "C:/Users/user/.ssh/id_rsa"}),
    ("EDGE", "search_files",             {"path": ROOT, "pattern": "*.env"}),
    ("EDGE", "read_file",                 {"path": f"{ROOT}/" + "A" * 1000}),
    ("EDGE", "list_directory",            {"path": "\\\\localhost\\C$"}),
    ("EDGE", "get_file_info",             {"path": f"{ROOT}/nonexistent_file_xyz.txt"}),
    ("EDGE", "read_file",                 {"path": "CON"}),
]

assert len(CALLS) == 50, f"Expected 50 calls, got {len(CALLS)}"

CSV_HEADERS = ["timestamp", "index", "category", "status", "tool", "args_keys", "elapsed_s", "response_preview"]

LINE = "─" * 100
HEAVY = "═" * 100


def _truncate(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def write_report(results: list[dict], session_start: datetime) -> None:
    """Write a human-readable session report to REPORT_FILE."""
    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"OK": 0, "ERROR": 0})
    for r in results:
        totals[r["category"]][r["status"]] += 1

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        # ── header ──────────────────────────────────────────────────────────────
        f.write("MCP PROXY SESSION LOG\n")
        f.write(f"Generated : {session_start.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Proxy     : {PROXY_URL}\n")
        f.write(f"Total     : {len(results)} calls\n")
        f.write("\n" + HEAVY + "\n")
        f.write(f" {'#':>3}  {'CATEGORY':<12} {'STATUS':<7} {'TOOL':<35} {'TIME':>7}  RESULT\n")
        f.write(HEAVY + "\n")

        # ── one line per call ────────────────────────────────────────────────────
        for r in results:
            preview = _truncate(r["response_preview"].replace("\n", " "), 60)
            f.write(
                f" {r['index']:>3}  {r['category']:<12} {r['status']:<7} "
                f"{_truncate(r['tool'], 35):<35} {float(r['elapsed_s']):>6.3f}s  {preview}\n"
            )

        # ── summary ──────────────────────────────────────────────────────────────
        f.write("\n" + HEAVY + "\n")
        f.write("SUMMARY BY CATEGORY\n")
        f.write(LINE + "\n")
        for cat in ["VALID", "BAD_TOOL", "BAD_PARAMS", "EDGE"]:
            counts = totals[cat]
            total_cat = counts["OK"] + counts["ERROR"]
            f.write(f"  {cat:<12}  {total_cat:>2} calls  |  OK: {counts['OK']:<3}  ERROR: {counts['ERROR']}\n")

        all_ok = sum(v["OK"] for v in totals.values())
        all_err = sum(v["ERROR"] for v in totals.values())
        f.write(LINE + "\n")
        f.write(f"  {'TOTAL':<12}  {len(results):>2} calls  |  OK: {all_ok:<3}  ERROR: {all_err}\n")


async def make_call(
    session: ClientSession,
    writer: "csv.DictWriter",
    results: list[dict],
    category: str,
    tool: str,
    args: dict,
    index: int,
) -> None:
    start = time.monotonic()
    try:
        result = await session.call_tool(tool, args)
        elapsed = time.monotonic() - start
        if result.content:
            raw = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
            response_preview = raw.replace("\n", " ").replace("\r", "")[:300]
        else:
            response_preview = "(empty response)"
        status = "OK"
    except Exception as exc:
        elapsed = time.monotonic() - start
        response_preview = str(exc).replace("\n", " ").replace("\r", "")
        status = "ERROR"

    row = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "index": index,
        "category": category,
        "status": status,
        "tool": tool,
        "args_keys": str(list(args.keys())),
        "elapsed_s": f"{elapsed:.3f}",
        "response_preview": response_preview,
    }
    writer.writerow(row)
    results.append(row)
    print(f"  [{index:02d}] {category:<11} {status:<5}  {tool}")


async def run_all() -> None:
    session_start = datetime.now(timezone.utc)
    print(f"\nRunning {len(CALLS)} calls against {PROXY_URL}\n")
    print(f"  {'#':<4} {'CATEGORY':<11} {'STATUS':<6} TOOL")
    print("  " + "-" * 60)

    results: list[dict] = []

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
        writer.writeheader()

        async with sse_client(PROXY_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for i, (category, tool, args) in enumerate(CALLS, 1):
                    await make_call(session, writer, results, category, tool, args, i)
                    await asyncio.sleep(0.3)

    write_report(results, session_start)

    print(f"\nDone.")
    print(f"  calls (raw) : {CSV_FILE}")
    print(f"  calls (read): {REPORT_FILE}")
    print(f"  wire log    : logs/proxy/wire.log  (written by mcp-proxy)")


if __name__ == "__main__":
    asyncio.run(run_all())
