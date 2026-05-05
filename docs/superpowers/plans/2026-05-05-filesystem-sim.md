# Filesystem Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simulate 20 realistic org-employee filesystem calls against a copy of `demo/corp_filesystem`, captured via the existing mitmproxy logging stack.

**Architecture:** `run_filesystem_sim.py` copies the original filesystem to `demo/corp_filesystem_sim/`, starts `npx @modelcontextprotocol/server-filesystem` via mcp-proxy on port 8094, intercepts all calls with mitmdump on port 9094, then writes `captured.jsonl` → `calls.csv` + `calls_report.txt` + `raw_log.txt` to `logs/proxy/sessions/filesystem_sim/`. Follows the exact same pattern as POC A in `run_mitm_two_servers.py`.

**Tech Stack:** Python 3.12, asyncio, `mcp` SDK (`ClientSession`, `streamablehttp_client`), `mitmproxy` (via `uvx`), `mcp-proxy`, `npx @modelcontextprotocol/server-filesystem`, `shutil.copytree`

---

## File Map

| Action | Path | Purpose |
|--------|------|---------|
| Modify | `.gitignore` | Exclude `demo/corp_filesystem_sim/` from git |
| Create | `logs/proxy/scripts/run_filesystem_sim.py` | Simulation runner |
| Create (runtime) | `demo/corp_filesystem_sim/` | Working copy of org filesystem |
| Create (runtime) | `logs/proxy/sessions/filesystem_sim/` | Session output directory |

---

## Task 1: Gitignore the simulation working copy

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add sim directory to .gitignore**

Open `.gitignore` and append after the `# Testbed runtime artifacts` block:

```
# Filesystem simulation working copy (recreated each run)
demo/corp_filesystem_sim/
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: gitignore demo/corp_filesystem_sim working copy"
```

---

## Task 2: Write the simulation runner script

**Files:**
- Create: `logs/proxy/scripts/run_filesystem_sim.py`

- [ ] **Step 1: Create the file with this complete content**

```python
"""
Corp filesystem simulation — 20 realistic org employee calls.

Copies demo/corp_filesystem → demo/corp_filesystem_sim (fresh each run),
then routes all calls through:
  mcp-proxy:8094  (npx @modelcontextprotocol/server-filesystem <sim_root>)
  → mitmdump:9094 (reverse proxy, -s mitm_capture.py)
  → captured.jsonl → calls.csv + calls_report.txt + raw_log.txt
"""
from __future__ import annotations

import asyncio
import csv
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHFABCDJrs]|\x1b[()][AB012]|\r")

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

PROXY_PORT  = 8094
MITM_PORT   = 9094
REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
SIM_ROOT    = REPO_ROOT / "demo" / "corp_filesystem_sim"
ORIG_ROOT   = REPO_ROOT / "demo" / "corp_filesystem"
SESSION_OUT = Path("logs/proxy/sessions/filesystem_sim")
ADDON       = Path(__file__).parent.parent / "analysis" / "mitm_capture.py"

HEAVY = "=" * 80
LINE  = "-" * 80
CSV_HEADERS = [
    "timestamp", "index", "persona", "session_id", "jsonrpc_id",
    "category", "status", "tool", "args",
    "http_status", "elapsed_s", "content_count", "error_code", "result",
]

# (category, persona, tool, args)
CALLS: list[tuple[str, str, str, dict]] = [
    ("VALID", "Alice (HR)",       "list_directory",   {"path": str(SIM_ROOT / "onboarding")}),
    ("VALID", "Alice (HR)",       "read_file",        {"path": str(SIM_ROOT / "onboarding" / "policies.pdf")}),
    ("VALID", "Alice (HR)",       "get_file_info",    {"path": str(SIM_ROOT / "onboarding" / "org_chart.png")}),
    ("VALID", "Bob (Dev)",        "list_directory",   {"path": str(SIM_ROOT / "source_code")}),
    ("VALID", "Bob (Dev)",        "read_file",        {"path": str(SIM_ROOT / "source_code" / "core.c")}),
    ("VALID", "Bob (Dev)",        "write_file",       {
        "path": str(SIM_ROOT / "source_code" / "notes.txt"),
        "content": "Sprint 12 notes\n- Fix auth bug\n- Review PR #44\n- Update API docs\n",
    }),
    ("VALID", "Carol (Finance)",  "list_directory",   {"path": str(SIM_ROOT / "sensitive" / "financials")}),
    ("VALID", "Carol (Finance)",  "read_file",        {"path": str(SIM_ROOT / "sensitive" / "financials" / "budget_2026.xlsx")}),
    ("VALID", "Carol (Finance)",  "read_file",        {"path": str(SIM_ROOT / "sensitive" / "financials" / "payslips_q1.csv")}),
    ("VALID", "Dave (Manager)",   "read_file",        {"path": str(SIM_ROOT / "projects" / "known_defects.csv")}),
    ("VALID", "Dave (Manager)",   "search_files",     {"path": str(SIM_ROOT), "pattern": "*.pdf"}),
    ("VALID", "Dave (Manager)",   "get_file_info",    {"path": str(SIM_ROOT / "public" / "whitepaper.pdf")}),
    ("VALID", "Eve (Security)",   "list_directory",   {"path": str(SIM_ROOT / "sensitive" / "security")}),
    ("VALID", "Eve (Security)",   "read_file",        {"path": str(SIM_ROOT / "sensitive" / "security" / "audit_log.txt")}),
    ("VALID", "Eve (Security)",   "read_file",        {"path": str(SIM_ROOT / "sensitive" / "contracts" / "nda_template.docx")}),
    ("VALID", "Frank (New hire)", "read_file",        {"path": str(SIM_ROOT / "README.md")}),
    ("VALID", "Frank (New hire)", "list_directory",   {"path": str(SIM_ROOT / "public")}),
    ("VALID", "Frank (New hire)", "read_file",        {"path": str(SIM_ROOT / "public" / "whitepaper.pdf")}),
    ("VALID", "Bob (Dev)",        "create_directory", {"path": str(SIM_ROOT / "source_code" / "feature_branch")}),
    ("VALID", "Bob (Dev)",        "move_file",        {
        "source":      str(SIM_ROOT / "source_code" / "notes.txt"),
        "destination": str(SIM_ROOT / "source_code" / "feature_branch" / "notes.txt"),
    }),
]


# ── helpers ───────────────────────────────────────────────────────────────────

def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _wait(port: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_open(port):
            return True
        time.sleep(0.5)
    return False


def _free_port(port: int) -> None:
    subprocess.run(
        ["powershell", "-Command",
         f"Get-Process -Id (Get-NetTCPConnection -LocalPort {port} "
         f"-State Listen -ErrorAction SilentlyContinue).OwningProcess "
         f"-ErrorAction SilentlyContinue | Stop-Process -Force"],
        capture_output=True,
    )
    time.sleep(0.3)


def _clean_log(path: Path) -> None:
    if not path.exists():
        return
    raw = path.read_bytes().replace(b"\x00", b"")
    text = raw.decode("utf-8", errors="replace")
    text = _ANSI_RE.sub("", text)
    lines = [l for l in text.splitlines() if l.strip()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def _start_mitmdump(
    upstream_port: int, listen_port: int, capture_path: Path, log_path: Path
) -> subprocess.Popen:
    env = {**os.environ, "MITM_OUT": str(capture_path.resolve())}
    lf = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        ["uvx", "--from", "mitmproxy", "mitmdump",
         "--mode", f"reverse:http://localhost:{upstream_port}",
         "--listen-port", str(listen_port),
         "-s", str(ADDON),
         "--set", "stream_large_bodies=10m"],
        stdout=lf, stderr=subprocess.STDOUT, env=env,
    )
    lf.close()
    return proc


def _parse_result(resp: dict) -> tuple[str, int, str]:
    if "error" in resp:
        return str(resp["error"].get("message", resp["error"])), 0, str(resp["error"].get("code", ""))
    result = resp.get("result", {})
    if not isinstance(result, dict):
        return str(result), 0, ""
    if result.get("isError"):
        content = result.get("content", [])
        text = "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
        return text, len(content), ""
    content = result.get("content", [])
    text = "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
    return text, len(content), ""


def _fmt_args(args: dict) -> str:
    if not args:
        return "(none)"
    # Shorten absolute paths to relative-from-sim-root for readability
    def _shorten(v: object) -> object:
        if isinstance(v, str) and str(SIM_ROOT) in v:
            return v.replace(str(SIM_ROOT), "<sim>")
        return v
    return ",  ".join(f"{k} = {json.dumps(_shorten(v))}" for k, v in args.items())


def _extract_tools_list(flows: list[dict]) -> list[str]:
    for flow in flows:
        try:
            req = json.loads(flow["req_body"])
            if req.get("method") == "tools/list":
                resp = json.loads(flow["resp_body"])
                tools = resp.get("result", {}).get("tools", [])
                return [t["name"] for t in tools]
        except Exception:
            continue
    return []


def write_report(capture_path: Path) -> None:
    flows = [json.loads(l) for l in capture_path.read_text(encoding="utf-8").splitlines()]

    tool_flows = [
        f for f in flows
        if _safe_method(f) == "tools/call"
    ]

    rows: list[dict] = []
    for i, ((cat, persona, tool, args), flow) in enumerate(zip(CALLS, tool_flows), 1):
        try:
            req  = json.loads(flow["req_body"])
            resp = json.loads(flow["resp_body"])
        except Exception:
            req = {}; resp = {}

        result_str, content_count, error_code = _parse_result(resp)
        session_id = flow["req_headers"].get("mcp-session-id", "")
        jsonrpc_id = str(req.get("id", ""))
        is_error   = bool(error_code) or any(
            kw in result_str.lower()
            for kw in ("not found", "validation error", "unknown tool", "error executing", "access denied")
        )
        rows.append({
            "timestamp":     datetime.fromtimestamp(flow["ts_request"], tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "index":         i,
            "persona":       persona,
            "session_id":    session_id,
            "jsonrpc_id":    jsonrpc_id,
            "category":      cat,
            "status":        "ERROR" if is_error else "OK",
            "tool":          tool,
            "args":          json.dumps(args),
            "http_status":   flow["status"],
            "elapsed_s":     f"{flow['duration_s']:.3f}",
            "content_count": content_count,
            "error_code":    error_code,
            "result":        result_str,
        })

    # calls.csv
    csv_path = SESSION_OUT / "calls.csv"
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            for r in rows:
                writer.writerow({**r, "result": r["result"][:300]})
    except PermissionError:
        print(f"  WARNING: {csv_path.name} is open in another program — skipping")

    # calls_report.txt
    available_tools = _extract_tools_list(flows)
    session_ids = sorted({r["session_id"] for r in rows if r["session_id"]})
    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"OK": 0, "ERROR": 0})
    for r in rows:
        totals[r["category"]][r["status"]] += 1

    report_path = SESSION_OUT / "calls_report.txt"
    with open(report_path, "w", encoding="utf-8-sig") as f:
        f.write(HEAVY + "\n")
        f.write("MCP SESSION LOG  --  Corp Filesystem Simulation\n")
        f.write(HEAVY + "\n")
        f.write(f"Generated  : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Session ID : {session_ids[0] if session_ids else 'n/a'}\n")
        f.write(f"Total calls: {len(rows)}\n")
        f.write(f"Sim root   : {SIM_ROOT}\n\n")

        if available_tools:
            f.write("TOOLS AVAILABLE ON THIS SERVER\n")
            f.write(LINE + "\n")
            for t in available_tools:
                f.write(f"  - {t}\n")
            f.write("\n")

        f.write("CALL LOG\n")
        f.write(LINE + "\n\n")
        for r in rows:
            status_tag = "OK" if r["status"] == "OK" else "ERROR"
            f.write(f"[{r['index']:02d}] {r['category']}  --  {r['persona']:<18}  --  {r['tool']}  [{status_tag}]\n")
            f.write(f"     INPUT  : {_fmt_args(json.loads(r['args']))}\n")
            result_lines = r["result"].splitlines()
            if not result_lines:
                f.write("     OUTPUT : (empty)\n")
            elif len(result_lines) == 1:
                f.write(f"     OUTPUT : {result_lines[0][:120]}\n")
            else:
                f.write(f"     OUTPUT : {result_lines[0]}\n")
                for line in result_lines[1:6]:
                    f.write(f"              {line}\n")
                if len(result_lines) > 6:
                    f.write(f"              ... ({len(result_lines) - 6} more lines)\n")
            f.write(f"     META   : RPC id={r['jsonrpc_id']}  |  HTTP {r['http_status']}  "
                    f"|  {r['elapsed_s']}s  |  {r['content_count']} content item(s)\n")
            if r["error_code"]:
                f.write(f"     ERROR  : code {r['error_code']}\n")
            f.write("\n")

        f.write(HEAVY + "\n")
        f.write("SUMMARY BY CATEGORY\n")
        f.write(LINE + "\n")
        for cat in ["VALID", "BAD_TOOL", "BAD_PARAMS", "EDGE"]:
            c = totals[cat]
            total = c["OK"] + c["ERROR"]
            if total:
                bar = ("+" * c["OK"]) + ("-" * c["ERROR"])
                f.write(f"  {cat:<12}  [{bar:<6}]  {c['OK']}/{total} OK\n")
        f.write(HEAVY + "\n")

    # raw_log.txt
    raw_path = SESSION_OUT / "raw_log.txt"
    with open(raw_path, "w", encoding="utf-8-sig") as f:
        f.write("RAW HTTP FLOWS  --  Corp Filesystem Simulation\n")
        f.write(f"Generated  : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Source     : {capture_path.name}  ({len(flows)} flows)\n\n")
        for i, flow in enumerate(flows, 1):
            ts = datetime.fromtimestamp(flow["ts_request"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            f.write(HEAVY + "\n")
            f.write(f"FLOW {i:02d}  |  {ts}  |  {flow['duration_s']:.3f}s\n")
            f.write(HEAVY + "\n")
            f.write("REQUEST\n")
            f.write(f"  {flow['method']} {flow['path']}\n")
            for k, v in flow["req_headers"].items():
                f.write(f"  {k}: {v}\n")
            f.write("\n")
            if flow["req_body"]:
                try:
                    f.write(json.dumps(json.loads(flow["req_body"]), indent=2, ensure_ascii=False))
                except Exception:
                    f.write(flow["req_body"])
            else:
                f.write("  (no body)")
            f.write("\n\n")
            f.write(f"RESPONSE  {flow['status']}\n")
            for k, v in flow["resp_headers"].items():
                f.write(f"  {k}: {v}\n")
            f.write("\n")
            if flow["resp_body"]:
                try:
                    f.write(json.dumps(json.loads(flow["resp_body"]), indent=2, ensure_ascii=False))
                except Exception:
                    f.write(flow["resp_body"])
            else:
                f.write("  (no body)")
            f.write("\n\n")

    print(f"\n  calls.csv      -> {csv_path}")
    print(f"  calls_report   -> {report_path}")
    print(f"  raw_log.txt    -> {raw_path}")


def _safe_method(flow: dict) -> str:
    try:
        return json.loads(flow["req_body"]).get("method", "")
    except Exception:
        return ""


async def _run_calls(url: str) -> None:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for i, (cat, persona, tool, args) in enumerate(CALLS, 1):
                try:
                    await session.call_tool(tool, args)
                    status = "OK"
                except Exception as exc:  # noqa: BLE001
                    status = f"ERR({type(exc).__name__})"
                print(f"      [{i:02d}] {persona:<18} {tool:<18} {status}")
                await asyncio.sleep(0.2)


async def main() -> None:
    print(HEAVY)
    print("Corp Filesystem Simulation")
    print(HEAVY)

    # Fresh copy of org filesystem
    print(f"\n[0/3] Copying {ORIG_ROOT.name} → {SIM_ROOT.name} ...")
    if SIM_ROOT.exists():
        shutil.rmtree(SIM_ROOT)
    shutil.copytree(ORIG_ROOT, SIM_ROOT)
    print(f"      {sum(1 for _ in SIM_ROOT.rglob('*') if _.is_file())} files copied")

    SESSION_OUT.mkdir(parents=True, exist_ok=True)
    _free_port(PROXY_PORT)
    _free_port(MITM_PORT)

    print(f"\n[1/3] Starting mcp-proxy on :{PROXY_PORT} → npx server-filesystem ...")
    with open(SESSION_OUT / "wire.log", "w", encoding="utf-8") as wf:
        proxy_proc = subprocess.Popen(
            ["mcp-proxy", "--log-level", "DEBUG", "--port", str(PROXY_PORT),
             "--", "npx", "-y", "@modelcontextprotocol/server-filesystem", str(SIM_ROOT)],
            stdout=wf, stderr=subprocess.STDOUT, env=os.environ.copy(),
        )
    if not _wait(PROXY_PORT, 60):
        print("ERROR: mcp-proxy did not start")
        proxy_proc.terminate()
        return

    capture = SESSION_OUT / "captured.jsonl"
    print(f"\n[2/3] Starting mitmdump on :{MITM_PORT} → :{PROXY_PORT} ...")
    mitm_proc = _start_mitmdump(PROXY_PORT, MITM_PORT, capture, SESSION_OUT / "mitmdump.log")
    if not _wait(MITM_PORT, 60):
        print("ERROR: mitmdump did not start")
        proxy_proc.terminate()
        mitm_proc.terminate()
        return

    print(f"\n[3/3] Running {len(CALLS)} calls through http://localhost:{MITM_PORT}/mcp ...\n")
    try:
        await _run_calls(f"http://localhost:{MITM_PORT}/mcp")
    finally:
        await asyncio.sleep(0.5)
        mitm_proc.terminate()
        proxy_proc.terminate()
        mitm_proc.wait()
        proxy_proc.wait()

    _clean_log(SESSION_OUT / "mitmdump.log")
    _clean_log(SESSION_OUT / "wire.log")
    write_report(capture)

    print(f"\n{HEAVY}")
    print(f"Session: {SESSION_OUT.resolve()}")
    print(HEAVY)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Commit**

```bash
git add logs/proxy/scripts/run_filesystem_sim.py
git commit -m "feat: add corp filesystem simulation runner (20 calls, 6 personas)"
```

---

## Task 3: Run the simulation and verify output

**Files:**
- Read: `logs/proxy/sessions/filesystem_sim/calls.csv`
- Read: `logs/proxy/sessions/filesystem_sim/calls_report.txt`

- [ ] **Step 1: Run the script from repo root**

```bash
uv run python logs/proxy/scripts/run_filesystem_sim.py
```

Expected console output (abridged):
```
================================================================================
Corp Filesystem Simulation
================================================================================

[0/3] Copying corp_filesystem → corp_filesystem_sim ...
      14 files copied

[1/3] Starting mcp-proxy on :8094 → npx server-filesystem ...

[2/3] Starting mitmdump on :9094 → :8094 ...

[3/3] Running 20 calls through http://localhost:9094/mcp ...

      [01] Alice (HR)         list_directory     OK
      [02] Alice (HR)         read_file          OK
      ...
      [20] Bob (Dev)          move_file          OK

  calls.csv      -> logs/proxy/sessions/filesystem_sim/calls.csv
  calls_report   -> logs/proxy/sessions/filesystem_sim/calls_report.txt
  raw_log.txt    -> logs/proxy/sessions/filesystem_sim/raw_log.txt
```

- [ ] **Step 2: Verify output files exist**

```bash
ls logs/proxy/sessions/filesystem_sim/
```

Expected — all six files present:
```
calls.csv  calls_report.txt  captured.jsonl  mitmdump.log  raw_log.txt  wire.log
```

- [ ] **Step 3: Verify call count in CSV**

```bash
python -c "
import csv
rows = list(csv.DictReader(open('logs/proxy/sessions/filesystem_sim/calls.csv')))
print(f'Rows: {len(rows)}')
statuses = [r[\"status\"] for r in rows]
print(f'OK: {statuses.count(\"OK\")}  ERROR: {statuses.count(\"ERROR\")}')
personas = sorted({r[\"persona\"] for r in rows})
print(f'Personas: {personas}')
"
```

Expected:
```
Rows: 20
OK: 20  ERROR: 0
Personas: ['Alice (HR)', 'Bob (Dev)', 'Carol (Finance)', 'Dave (Manager)', 'Eve (Security)', 'Frank (New hire)']
```

- [ ] **Step 4: If any call shows ERROR, investigate**

Open `logs/proxy/sessions/filesystem_sim/calls_report.txt` and find the failing call block. The `INPUT` line shows exact args sent; the `OUTPUT` line shows what the server returned. Common causes:
- Path doesn't exist in sim copy → check `demo/corp_filesystem_sim/` structure
- Tool name wrong → run `list_allowed_directories` call manually to see available tools
- mcp-proxy or mitmdump crashed → check `wire.log` and `mitmdump.log`

- [ ] **Step 5: Commit session output**

```bash
git add logs/proxy/sessions/filesystem_sim/
git commit -m "feat: add filesystem simulation session output (20 calls, 6 personas)"
```

---

## Notes

- `demo/corp_filesystem/` is **never modified** — `shutil.copytree` creates a fresh `demo/corp_filesystem_sim/` each run
- Ports 8094/9094 are chosen to not collide with existing sessions (local=8092/9092, calendar=8093/9093)
- `SESSION_OUT` is relative to CWD — run the script from the repo root
- Binary files (`.pdf`, `.xlsx`, `.docx`, `.png`) will return binary content; the server wraps it as base64 or returns a read error; both are handled by `_parse_result`
