"""Load test matrix: modes × concurrency (× gateway shards), against a fast local fake server.

Modes:
- ``direct``     agents call the fake server, no gateway (the floor)
- ``off``        through the gateway, logging only
- ``inline``     scored before forwarding (runtime)
- ``background`` scored right after forwarding, same process (semi-runtime)

For each cell: agents in several load-generator processes for a fixed time; reports
throughput, latency percentiles and each gateway process's CPU use. Processes are started
and stopped by PID. Results go to ``results_load.jsonl``, one line per cell.

    uv run python reports/experiments/gateway/scale/loadtest.py --levels 1,16,64,256 --shards 1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ROUTES = REPO / "src/mcp_security/gateway/routes.example.json"
UPSTREAM_PORT = 19100
GATEWAY_PORT = 18800
CLK_TCK = os.sysconf("SC_CLK_TCK")


def cpu_seconds(pid: int) -> float:
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return (int(fields[11]) + int(fields[12])) / CLK_TCK  # utime + stime


def wait_up(url: str, timeout: float = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            httpx.post(url, json={"jsonrpc": "2.0", "method": "ping"}, timeout=2)
            return
        except httpx.HTTPError:
            time.sleep(0.3)
    raise RuntimeError(f"{url} did not come up")


def start(cmd: list[str], log: Path, env: dict | None = None) -> subprocess.Popen:
    return subprocess.Popen(
        cmd,
        cwd=REPO,
        stdout=log.open("w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
    )


AIOHTTP_PY = REPO / "runs" / "exp-venv-aiohttp" / "bin" / "python"


def gateway_cmd(kind: str, cfg: Path, port: int) -> tuple[list[str], dict | None]:
    """httpx: the gateway as shipped. aiohttp: the experiment variant (gateway_aiohttp.py)."""
    if kind == "aiohttp":
        env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
        return [str(AIOHTTP_PY), str(HERE / "gateway_aiohttp.py"), str(cfg), str(port)], env
    cmd = [sys.executable, "-m", "mcp_security.gateway.proxy", "--config", str(cfg)]
    return [*cmd, "--port", str(port)], None


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)


def gateway_config(work: Path, mode: str, history: str, agents: dict[str, str], shard: int) -> Path:
    """Shard ``i`` of the gateway talks to fake server ``i``: uvicorn's multi-worker mode
    adds a ~40 ms stall per request on this cluster, so each fake server is one process."""
    route = json.loads(ROUTES.read_text())["upstreams"]["github"]
    route = {
        k: (str(REPO / v) if k in {"scan", "breadth", "rules"} else v) for k, v in route.items()
    }
    route.update(
        url=f"http://127.0.0.1:{UPSTREAM_PORT + shard}/mcp",
        history=history,
        scoring="off" if mode == "off" else mode,
    )
    route.pop("key_env", None)
    cfg = {
        "log_dir": str(work / f"logs-{mode}-{shard}"),
        "agents": agents,
        "upstreams": {"github": route},
    }
    path = work / f"routes-{mode}-{shard}.json"
    path.write_text(json.dumps(cfg))
    return path


def run_cell(
    work: Path, tokens: Path, ports: list[int], path: str, agents: int, procs: int, seconds: float
) -> dict:
    per = [agents // procs + (1 if i < agents % procs else 0) for i in range(procs)]
    gens, first = [], 0
    for n in per:
        if n == 0:
            continue
        cmd = [
            sys.executable,
            str(HERE / "loadgen.py"),
            "--ports",
            ",".join(map(str, ports)),
            "--path",
            path,
            "--agents",
            str(n),
            "--first",
            str(first),
            "--seconds",
            str(seconds),
            "--tokens",
            str(tokens),
        ]
        gens.append(subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.PIPE, text=True))
        first += n
    outs = [json.loads(g.communicate()[0]) for g in gens]
    lat = sorted(x for o in outs for x in o["latencies_ms"])
    wall = max(o["wall_s"] for o in outs)
    q = lambda p: lat[min(len(lat) - 1, int(p * len(lat)))] if lat else None  # noqa: E731
    kinds: dict[str, int] = {}
    for o in outs:
        for k, v in o.get("error_kinds", {}).items():
            kinds[k] = kinds.get(k, 0) + v
    return {
        "calls": len(lat),
        "errors": sum(o["errors"] for o in outs),
        "error_kinds": kinds,
        "throughput_cps": round(len(lat) / wall, 1),
        "p50_ms": q(0.5),
        "p95_ms": q(0.95),
        "p99_ms": q(0.99),
        "max_ms": lat[-1] if lat else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--levels", default="1,16,64,256")
    parser.add_argument("--modes", default="direct,off,inline,background")
    parser.add_argument("--shards", default="1")
    parser.add_argument("--history", default="caller")
    parser.add_argument("--seconds", type=float, default=20)
    parser.add_argument("--procs", type=int, default=4)
    parser.add_argument("--gateway", choices=["httpx", "aiohttp"], default="httpx")
    parser.add_argument("--port-offset", type=int, default=0, help="for two runs on one node")
    parser.add_argument("--upstream-delay-ms", type=float, default=0, help="fake server latency")
    parser.add_argument("--out", default=str(HERE / "results_load.jsonl"))
    args = parser.parse_args()
    global UPSTREAM_PORT, GATEWAY_PORT  # noqa: PLW0603 — set once, before any server starts
    UPSTREAM_PORT += args.port_offset
    GATEWAY_PORT += args.port_offset
    levels = [int(x) for x in args.levels.split(",")]
    work = Path(tempfile.mkdtemp(prefix="gwload-"))
    max_agents = max(levels)
    names = {f"agent-{i}": secrets.token_urlsafe(16) for i in range(max_agents)}
    tokens = work / "tokens.json"
    tokens.write_text(json.dumps(names))
    agents = {hashlib.sha256(t.encode()).hexdigest(): n for n, t in names.items()}
    shard_counts = [int(s) for s in args.shards.split(",")]
    upstream_env = {**os.environ, "FAKE_DELAY_MS": str(args.upstream_delay_ms)}
    upstreams = [
        start(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "fake_upstream:app",
                "--app-dir",
                str(HERE),
                "--port",
                str(UPSTREAM_PORT + i),
                "--log-level",
                "warning",
            ],
            work / f"upstream-{i}.log",
            upstream_env,
        )
        for i in range(max(shard_counts))
    ]
    try:
        for i in range(len(upstreams)):
            wait_up(f"http://127.0.0.1:{UPSTREAM_PORT + i}/mcp")
        for shards in shard_counts:
            for mode in args.modes.split(","):
                gws, ports = [], [UPSTREAM_PORT + i for i in range(shards)]
                if mode != "direct":
                    ports = [GATEWAY_PORT + i for i in range(shards)]
                    gws = []
                    for i, p in enumerate(ports):
                        cfg = gateway_config(work, mode, args.history, agents, i)
                        cmd, env = gateway_cmd(args.gateway, cfg, p)
                        gws.append(start(cmd, work / f"gw-{mode}-{p}.log", env))
                    for p in ports:
                        wait_up(f"http://127.0.0.1:{p}/github")
                for level in levels:
                    cpu0 = [cpu_seconds(g.pid) for g in gws]
                    t0 = time.time()
                    cell = run_cell(
                        work,
                        tokens,
                        ports,
                        "/mcp" if mode == "direct" else "/github",
                        level,
                        min(args.procs, level),
                        args.seconds,
                    )
                    wall = time.time() - t0
                    cell |= {
                        "mode": mode,
                        "agents": level,
                        "shards": shards if gws else 0,
                        "gateway": args.gateway if gws else None,
                        "upstream_delay_ms": args.upstream_delay_ms,
                        "servers": shards,
                        "history": args.history,
                        "gateway_cpu_pct": [
                            round((cpu_seconds(g.pid) - c) / wall * 100, 1)
                            for g, c in zip(gws, cpu0)
                        ],
                    }
                    print(json.dumps(cell), flush=True)
                    with open(args.out, "a") as handle:
                        handle.write(json.dumps(cell) + "\n")
                for g in gws:
                    stop(g)
                if mode != "direct":
                    logs = list(work.glob(f"logs-{mode}-*"))
                    size = sum(f.stat().st_size for d in logs for f in d.rglob("*") if f.is_file())
                    print(
                        json.dumps({"mode": mode, "shards": shards, "log_mb": round(size / 1e6, 1)})
                    )
                    for d in logs:
                        shutil.rmtree(d, ignore_errors=True)
    finally:
        for u in upstreams:
            stop(u)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
