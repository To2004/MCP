"""Capture REAL traffic from a live git MCP server (uvx mcp-server-git) — no external auth.

Drives the actual MCP server over stdio with hundreds of real tool calls whose arguments
are drawn from the target repo's real history (real commit SHAs, real tracked file paths,
real branch names, varied counts). Records each call in the standard sessions CSV schema
so the embedding likelihood can be fit and validated on genuinely real MCP traffic.

Purpose (per the validation plan): check that the model's calibration and featurizer
survive real argument diversity — NOT a labeled attack benchmark. All calls are benign
by construction; a small set of deliberately-odd-but-valid calls is included so the
held-out check can confirm the model still separates the unusual from the routine.

Deterministic given the repo state and ``--seed``. Offline except for uvx's first fetch
of the git server package.

Usage::

    uv run python scripts/capture_real_git_mcp.py --repo /home/ovadyat/MCP --n 400
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import random
import subprocess
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CSV_HEADER = ["timestamp", "index", "persona", "category", "status", "tool", "args", "run_id"]
BASE_TS = "2026-07-12T09:00:00"


def repo_facts(repo: Path, rng: random.Random) -> dict:
    """Pull real commit SHAs, tracked files, and branches from the target repo."""

    def git(*args: str) -> list[str]:
        out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        return [ln for ln in out.stdout.splitlines() if ln.strip()]

    shas = git("rev-list", "--max-count=60", "HEAD")
    files = git("ls-files")
    branches = [b.lstrip("* ").strip() for b in git("branch", "--format=%(refname:short)")]
    return {
        "shas": shas or ["HEAD"],
        "files": files or ["README.md"],
        "branches": branches or ["main"],
    }


def plan_calls(facts: dict, tools: set[str], n: int, rng: random.Random) -> list[tuple[str, dict]]:
    """Build a realistic benign call mix using the git server's actual tool names."""
    repo = "."  # mcp-server-git resolves repo_path against its --repository root
    calls: list[tuple[str, dict]] = []

    def add(tool: str, args: dict) -> None:
        if tool in tools:
            calls.append((tool, {"repo_path": repo, **args}))

    while len(calls) < n:
        r = rng.random()
        if r < 0.30:
            add("git_log", {"max_count": rng.choice([5, 10, 20, 50])})
        elif r < 0.50:
            add("git_show", {"revision": rng.choice(facts["shas"])})
        elif r < 0.65:
            base = rng.choice(facts["shas"])
            add("git_diff", {"target": base})
        elif r < 0.78:
            add("git_status", {})
        elif r < 0.88:
            add("git_diff_unstaged", {})
        elif r < 0.95:
            add("git_diff_staged", {})
        else:  # deliberately-unusual-but-valid: a huge log pull, rare tools
            odd = rng.choice([
                ("git_log", {"max_count": 5000}),
                ("git_show", {"revision": f"{rng.choice(facts['shas'])}~20"}),
                ("git_diff", {"target": f"{rng.choice(facts['branches'])}"}),
            ])
            add(*odd)
    return calls[:n]


async def run_capture(repo: Path, n: int, seed: int, out: Path) -> None:
    rng = random.Random(seed)
    facts = repo_facts(repo, rng)
    params = StdioServerParameters(
        command="uvx", args=["mcp-server-git", "--repository", str(repo)]
    )
    rows: list[dict] = []
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tool_names = {t.name for t in (await session.list_tools()).tools}
            print(f"live git MCP tools: {sorted(tool_names)}")
            planned = plan_calls(facts, tool_names, n, rng)
            for i, (tool, args) in enumerate(planned, 1):
                status = "OK"
                try:
                    result = await session.call_tool(tool, args)
                    status = "ERROR" if result.isError else "OK"
                except Exception as exc:  # noqa: BLE001 — record real failures, never crash the run
                    status = f"EXC:{type(exc).__name__}"
                rows.append({
                    "timestamp": BASE_TS,
                    "index": i,
                    "persona": "Real Git Client@local",
                    "category": "BENIGN",
                    "status": status,
                    "tool": tool,
                    "args": json.dumps(args),
                    "run_id": f"real_git_{i // 12}",
                })
                if i % 50 == 0:
                    print(f"  captured {i}/{len(planned)} real calls")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(rows)
    ok = sum(1 for r in rows if r["status"] == "OK")
    print(f"wrote {len(rows)} real calls ({ok} OK) -> {out}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=Path.home() / "MCP")
    parser.add_argument("--n", type=int, default=400)
    parser.add_argument("--seed", type=int, default=20260712)
    parser.add_argument(
        "--out", type=Path,
        default=Path("logs/proxy/sessions/real_git_live/calls.csv"),
    )
    args = parser.parse_args()
    asyncio.run(run_capture(args.repo, args.n, args.seed, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
