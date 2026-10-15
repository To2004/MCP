"""Semi-runtime test: gateway logs only, a separate process scores from the log.

For each load level: fake server + gateway (scoring off) + ``tail_scorer.py`` + load
generators. Reports call throughput and latency (what agents see) next to the decision
lag (how long after a request its decision exists), and the CPU of gateway and scorer.

    uv run python reports/experiments/gateway/scale/semi_runtime.py --levels 16,64,256
"""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from loadtest import (GATEWAY_PORT, HERE, REPO, UPSTREAM_PORT, cpu_seconds, gateway_config,
                      run_cell, start, stop, wait_up)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--levels", default="16,64,256")
    parser.add_argument("--seconds", type=float, default=20)
    parser.add_argument("--procs", type=int, default=4)
    parser.add_argument("--port-offset", type=int, default=200)
    parser.add_argument("--out", default=str(HERE / "results_semi.jsonl"))
    args = parser.parse_args()
    levels = [int(x) for x in args.levels.split(",")]
    work = Path(tempfile.mkdtemp(prefix="gwsemi-"))
    names = {f"agent-{i}": secrets.token_urlsafe(16) for i in range(max(levels))}
    tokens = work / "tokens.json"
    tokens.write_text(json.dumps(names))
    agents = {hashlib.sha256(t.encode()).hexdigest(): n for n, t in names.items()}
    up_port, gw_port = UPSTREAM_PORT + args.port_offset, GATEWAY_PORT + args.port_offset
    upstream = start([sys.executable, "-m", "uvicorn", "fake_upstream:app", "--app-dir", str(HERE),
                      "--port", str(up_port), "--log-level", "warning"], work / "up.log")
    try:
        wait_up(f"http://127.0.0.1:{up_port}/mcp")
        for level in levels:
            cfg = json.loads(gateway_config(work, "off", "caller", agents, 0).read_text())
            cfg["upstreams"]["github"]["url"] = f"http://127.0.0.1:{up_port}/mcp"
            cfg["log_dir"] = str(work / f"logs-{level}")
            cfg_path = work / f"routes-{level}.json"
            cfg_path.write_text(json.dumps(cfg))
            gw = start([sys.executable, "-m", "mcp_security.gateway.proxy", "--config",
                        str(cfg_path), "--port", str(gw_port)], work / f"gw-{level}.log")
            wait_up(f"http://127.0.0.1:{gw_port}/github")
            scorer = subprocess.Popen(
                [sys.executable, str(HERE / "tail_scorer.py"), "--log",
                 str(work / f"logs-{level}" / "github.jsonl"), "--out",
                 str(work / f"decisions-{level}.jsonl"), "--seconds", str(args.seconds + 8)],
                cwd=REPO, stdout=subprocess.PIPE, text=True)
            time.sleep(1)
            cpu0 = (cpu_seconds(gw.pid), cpu_seconds(scorer.pid))
            t0 = time.time()
            cell = run_cell(work, tokens, [gw_port], "/github", level, min(args.procs, level),
                            args.seconds)
            wall = time.time() - t0
            cpu = (cpu_seconds(gw.pid) - cpu0[0], cpu_seconds(scorer.pid) - cpu0[1])
            lag = json.loads(scorer.communicate()[0])
            stop(gw)
            cell |= {"mode": "semi_runtime_tail", "agents": level, **lag,
                     "gateway_cpu_pct": round(cpu[0] / wall * 100, 1),
                     "scorer_cpu_pct": round(cpu[1] / wall * 100, 1)}
            print(json.dumps(cell), flush=True)
            with open(args.out, "a") as handle:
                handle.write(json.dumps(cell) + "\n")
    finally:
        stop(upstream)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
