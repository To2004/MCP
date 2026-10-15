"""How fast can the gateway store what it sees? Records per second for log and database
options, using real records from the live run (requests, replies, decisions), cycled to N.

    uv run python reports/experiments/gateway/scale/bench_storage.py > results_storage.jsonl
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
import time
from pathlib import Path

SOURCE = Path("runs/gateway/live/github.jsonl")
N = 200_000


def records() -> list[dict]:
    lines = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line]
    return [lines[i % len(lines)] for i in range(N)]


def jsonl_open_per_line(rows: list[dict], path: Path) -> None:
    for row in rows:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def jsonl_kept_open(rows: list[dict], path: Path, flush_every: int = 1) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for i, row in enumerate(rows, 1):
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            if i % flush_every == 0:
                handle.flush()


SCHEMA = """CREATE TABLE IF NOT EXISTS messages (
    seq INTEGER PRIMARY KEY, ts REAL, route TEXT, direction TEXT, agent TEXT, session TEXT,
    method TEXT, tool TEXT, rpc_id TEXT, body TEXT)"""


def sqlite_insert(rows: list[dict], path: Path, batch: int, synchronous: str) -> None:
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute(f"PRAGMA synchronous={synchronous}")
    db.execute(SCHEMA)
    sql = "INSERT INTO messages (ts, route, direction, agent, session, method, tool, rpc_id, body) " \
          "VALUES (?,?,?,?,?,?,?,?,?)"
    pending = []
    for row in rows:
        pending.append((row.get("ts"), row.get("gateway.route"), row.get("gateway.direction"),
                        row.get("gateway.agent"), row.get("mcp.session.id"),
                        row.get("mcp.method.name"), row.get("gen_ai.tool.name"),
                        json.dumps(row.get("jsonrpc.request.id")), json.dumps(row, ensure_ascii=False)))
        if len(pending) >= batch:
            db.executemany(sql, pending)
            db.commit()
            pending.clear()
    if pending:
        db.executemany(sql, pending)
        db.commit()
    db.close()


def main() -> None:
    rows = records()
    work = Path(tempfile.mkdtemp(prefix="gwstore-"))
    cases = {
        "jsonl, open+close per line (before)": lambda p: jsonl_open_per_line(rows, p),
        "jsonl, kept open, flush per line (now)": lambda p: jsonl_kept_open(rows, p, 1),
        "jsonl, kept open, flush per 100": lambda p: jsonl_kept_open(rows, p, 100),
        "sqlite WAL, commit per row, sync NORMAL": lambda p: sqlite_insert(rows[:20_000], p, 1, "NORMAL"),
        "sqlite WAL, commit per 1000, sync NORMAL": lambda p: sqlite_insert(rows, p, 1000, "NORMAL"),
        "sqlite WAL, commit per 1000, sync FULL": lambda p: sqlite_insert(rows, p, 1000, "FULL"),
    }
    for i, (name, fn) in enumerate(cases.items()):
        path = work / f"case{i}.{'db' if 'sqlite' in name else 'jsonl'}"
        n = 20_000 if "per row" in name else N
        started = time.perf_counter()
        fn(path)
        elapsed = time.perf_counter() - started
        size = sum(f.stat().st_size for f in work.glob(f"case{i}*"))
        print(json.dumps({"case": name, "records": n, "records_per_s": round(n / elapsed),
                          "bytes_per_record": round(size / n)}), flush=True)


if __name__ == "__main__":
    main()
