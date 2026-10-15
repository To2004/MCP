"""Markdown tables from the load-test results: throughput and latency per setup.

    python reports/experiments/gateway/scale/summarize.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
#: file -> (server kind, the shard counts it ran, in order). Direct-mode cells repeat once
#: per shard count, with that many fake servers; they are labelled from this order.
FILES = {
    "results_load.jsonl": ("fast server", [1, 2, 4, 8]),
    "results_load_aiohttp.jsonl": ("fast server", [1, 2, 4, 8]),
    "results_load_latency400_httpx.jsonl": ("server 400 ms", [1, 4]),
    "results_load_latency400_aiohttp.jsonl": ("server 400 ms", [1, 4]),
}


def rows() -> list[dict]:
    out = []
    for name, (server, shard_order) in FILES.items():
        path = HERE / name
        if not path.exists():
            continue
        seen: dict[int, int] = defaultdict(int)
        for line in path.read_text().splitlines():
            if line.strip():
                cell = json.loads(line)
                cell["server"] = server
                if cell["mode"] == "direct":
                    cell["gateway"] = "none (servers)"
                    cell["shards"] = cell.get("servers") or shard_order[seen[cell["agents"]]]
                    seen[cell["agents"]] += 1
                else:
                    cell["gateway"] = cell.get("gateway") or "httpx"
                out.append(cell)
    return out


def table(cells: list[dict], mode: str, server: str) -> str:
    grid: dict[tuple, dict] = {}
    agents = sorted({c["agents"] for c in cells})
    for c in cells:
        if c["mode"] == mode and c["server"] == server:
            grid[(c["gateway"], c["shards"], c["agents"])] = c
    setups = sorted({(g, s) for g, s, _ in grid})
    if not setups:
        return ""
    head = "| gateway | shards | " + " | ".join(f"{a} agents" for a in agents) + " |"
    lines = [f"**{mode}, {server}** — calls/s (p50 / p99 ms)", "", head,
             "|---|---:|" + "---:|" * len(agents)]
    for g, s in setups:
        cells_ = []
        for a in agents:
            c = grid.get((g, s, a))
            if c is None:
                cells_.append("")
                continue
            err = f", {c['errors']} err" if c["errors"] else ""
            cells_.append(f"{c['throughput_cps']:.0f} ({c['p50_ms']:.0f} / {c['p99_ms']:.0f}{err})")
        lines.append(f"| {g} | {s} | " + " | ".join(cells_) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    cells = rows()
    by = defaultdict(list)
    for c in cells:
        by[(c["mode"], c["server"])].append(c)
    for mode in ("direct", "off", "inline", "background"):
        for server in ("fast server", "server 400 ms"):
            text = table(cells, mode, server)
            if text:
                print(text)


if __name__ == "__main__":
    main()
