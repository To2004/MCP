"""Drive the no-credential finance MCP servers with real, read-only calls.

Same purpose as ``make_real_warmup.py`` (github/slack/calendar), extended to the five
finance servers already live-captured under ``reports/scan_finance/`` (see that dir's
README): **yahoo_finance**, **finance_tools**, **sec_edgar**, **maverick**, **openbb**.
Those five needed no key to connect, so every call here hits the real upstream (Yahoo
Finance, SEC EDGAR, FRED, OpenBB's yfinance-backed routes) — not a script that invents
argument sizes.

Unlike github/slack/calendar, there are 119+30+21+17+9 = 196 tools across five very
different schemas, so this driver does not hand-author one call plan per tool. Instead
it reuses each server's own **static scan** (``reports/scan_finance/<server>.json``,
deterministic atomic-op classification, no LLM) to select only the tools whose
``primary_op`` is a read (READ/METADATA/SEARCH/LIST) — the same read-only discipline
``make_real_warmup.py`` applies by hand — then fills each tool's declared JSON Schema
generically: parameter *names* that mean something (ticker, period, days, limit,
series_id, ...) get a pool of real values; everything else falls back to the
schema's own type/enum. Values seen in real responses (accession numbers, option
expiration dates, CIKs) are harvested opportunistically and reused, so the small
fraction of parameters that need a real discovered identifier are not invented either.

Launch config (server_dir/module/attr/run_cmd/env/transport) is reused directly from
``logs/proxy/scripts/run_mitm_finance.py``'s ``SERVERS`` dict — this script starts the
same server the same way, just without the mitmdump capture layer in front, and drives
hundreds of calls per server instead of the handful the static-scan capture needed.

    python3 scripts/dynamic_design/make_finance_real_warmup.py --server yahoo_finance --n 600
    python3 scripts/dynamic_design/make_finance_real_warmup.py --server all --n 600
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "logs" / "proxy" / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from mcp import ClientSession  # noqa: E402
from mcp.client.sse import sse_client  # noqa: E402
from mcp.client.streamable_http import streamablehttp_client  # noqa: E402

import run_mitm_finance as rmf  # noqa: E402 - reuse launch config + subprocess helpers

OUT = REPO / "reports" / "experiments" / "real_benign_finance"
SCAN_DIR = REPO / "reports" / "scan_finance"
CSV_HEADER = ["index", "org", "persona", "category", "asset", "tool", "status", "args", "source"]

# A read-only call teaches the runtime layer nothing false; a write against a real,
# unsandboxed finance deployment (portfolio state, watchlists, journal entries, cache
# resets) is a real externally-visible side effect this driver has no business causing.
# The filter is the server's OWN static scan, not a hand-picked tool list.
SAFE_OPS = {"READ", "METADATA", "SEARCH", "LIST"}

# One codename per server, in the same style as github_helios/slack_vireo/calendar_aurora.
ORG = {
    "yahoo_finance": "yahoo_finance_kestrel",
    "finance_tools": "finance_tools_orbit",
    "sec_edgar": "sec_edgar_ledger",
    "maverick": "maverick_talon",
    "openbb": "openbb_atlas",
}
DEFAULT_SEED = 20260814

# --- Real-world argument pools. Every value here is a real, well-known instrument or
# --- series id — nobody picked these to be interesting, they are just liquid/common.
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "JPM",
    "V", "UNH", "XOM", "JNJ", "WMT", "MA", "PG", "HD", "CVX", "MRK", "ABBV", "KO",
    "PEP", "COST", "AVGO", "ADBE", "CRM", "ORCL", "CSCO", "INTC", "AMD", "QCOM",
    "TXN", "IBM", "GE", "CAT", "BA", "MMM", "HON", "UPS", "GS", "MS", "BAC", "WFC",
    "C", "BLK", "SPGI", "DIS", "NFLX", "CMCSA", "T", "VZ", "PFE", "TMO", "ABT",
    "LLY", "NKE", "MCD", "SBUX", "SPY", "QQQ", "IWM", "DIA", "GLD", "VTI", "VOO",
]
PERIODS = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
INTERVALS = ["1d", "5d", "1wk", "1mo"]
FRED_SERIES = ["GDP", "UNRATE", "CPIAUCSL", "FEDFUNDS", "DGS10", "PAYEMS", "M2SL",
               "INDPRO", "HOUST", "PCE", "DEXUSEU", "T10Y2Y"]
SEARCH_TERMS = ["semiconductor", "unemployment rate", "interest rates", "inflation",
                "earnings", "merger", "buyback", "dividend", "recession", "AI chips"]
EXPRESSIONS = ["2 + 2 * 10", "(150.25 - 120.10) / 120.10 * 100", "sum([1,2,3,4,5])/5",
               "3.5 ** 2", "100000 * (1 + 0.05) ** 10"]
FORM_TYPES = ["10-K", "10-Q", "8-K", "4", "DEF 14A", "S-1"]
STATEMENT_TYPES = ["income_stmt", "balance_sheet", "cash_flow"]
COUNTRIES = ["us", "ca", "gb"]

_TICKER_NAMES = {"ticker", "symbol"}
_TICKERS_NAMES = {"tickers", "symbols"}


def value_for(name: str, sub: dict, rng: random.Random, harvest: dict[str, list]):
    """One realistic value for a schema property, name-aware first, type-aware fallback."""
    lname = name.lower()
    enum = sub.get("enum")
    if not enum:
        for branch in sub.get("anyOf", []) or sub.get("oneOf", []) or []:
            if isinstance(branch, dict) and branch.get("enum"):
                enum = branch["enum"]
                break
    if enum:
        return rng.choice(enum)

    # Values harvested from real responses take priority over any invented value: an
    # accession number or expiration date that really exists is strictly more real than
    # a name-based guess.
    for key, pool in harvest.items():
        if pool and key in lname:
            return rng.choice(pool)

    if lname in _TICKER_NAMES or lname == "identifier":
        return rng.choice(TICKERS)
    if lname in _TICKERS_NAMES:
        k = rng.choice([1, 2, 3, 5, 8])
        return rng.sample(TICKERS, min(k, len(TICKERS)))
    if lname == "period":
        return rng.choice(PERIODS)
    if lname == "interval":
        return rng.choice(INTERVALS)
    if lname == "days":
        return rng.choice([1, 7, 14, 30, 60, 90, 180, 365, 730])
    if lname in ("limit", "top_n", "max_results", "n_results", "count"):
        return rng.choice([1, 5, 10, 25, 50, 100])
    if lname in ("query", "keyword", "search", "topic", "namespace_filter"):
        return rng.choice(SEARCH_TERMS)
    if lname == "keywords":
        return rng.sample(SEARCH_TERMS, rng.choice([1, 2, 3]))
    if lname == "series_id":
        return rng.choice(FRED_SERIES)
    if lname == "expression":
        return rng.choice(EXPRESSIONS)
    if lname == "form_type":
        return rng.choice(FORM_TYPES)
    if lname == "form_types":
        return rng.sample(FORM_TYPES, rng.choice([1, 2]))
    if lname in ("statement_type", "financial_type"):
        return rng.choice(STATEMENT_TYPES)
    if lname == "provider":
        return "yfinance"  # the only provider that needs no API key here
    if lname == "recommendation_type":
        return rng.choice(["recommendations", "upgrades_downgrades"])
    if lname == "holder_type":
        return rng.choice(["major_holders", "institutional_holders", "mutual_fund_holders",
                           "insider_transactions", "insider_purchases", "insider_roster_holders"])
    if lname == "months_back":
        return rng.choice([1, 3, 6, 12, 24, 36])
    if lname == "country":
        return rng.choice(COUNTRIES)

    t = sub.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), t[0] if t else None)
    if t == "integer":
        return rng.choice([1, 5, 10, 25, 50])
    if t == "number":
        return round(rng.uniform(1, 100), 2)
    if t == "boolean":
        return rng.choice([True, False])
    if t == "array":
        item = sub.get("items") if isinstance(sub.get("items"), dict) else {}
        return [value_for(name.rstrip("s") or name, item, rng, harvest)
                for _ in range(rng.choice([1, 2, 3]))]
    return rng.choice(TICKERS)  # string fallback: a real symbol is always a valid guess


def fill_args(schema: dict, rng: random.Random, harvest: dict[str, list]) -> dict:
    props = (schema or {}).get("properties") or {}
    required = set((schema or {}).get("required") or [])
    args = {}
    for name, sub in props.items():
        if name not in required and rng.random() < 0.35:
            continue  # real callers omit optional args too; dynamic_v2 treats that honestly
        args[name] = value_for(name, sub if isinstance(sub, dict) else {}, rng, harvest)
    return args


_HARVEST_KEYS = ("accession_number", "accessionnumber", "expiration_date",
                  "expirationdate", "cik")


def _harvest_from(payload, harvest: dict[str, list]) -> None:
    """Pull real identifiers out of a response so later calls can reuse them."""
    if isinstance(payload, dict):
        for k, v in payload.items():
            lk = k.lower()
            for wanted in _HARVEST_KEYS:
                if wanted in lk and isinstance(v, (str, int)) and str(v):
                    bucket = harvest.setdefault(wanted.replace("accessionnumber", "accession_number")
                                                 .replace("expirationdate", "expiration_date"), [])
                    if str(v) not in bucket:
                        bucket.append(str(v))
                        del bucket[:-200]  # keep it bounded
            _harvest_from(v, harvest)
    elif isinstance(payload, list):
        for item in payload[:50]:
            _harvest_from(item, harvest)


def _text(result) -> str:
    parts = [c.text for c in getattr(result, "content", []) if getattr(c, "type", "") == "text"]
    return "\n".join(parts)


def _json(result):
    try:
        return json.loads(_text(result))
    except (ValueError, TypeError):
        return None


def load_safe_tools(server: str) -> dict[str, dict]:
    """``{tool_name: input_schema}`` restricted to this server's own read-only tools.

    Cross-references the deterministic static scan (``primary_op``) against the live
    tool-list catalog (``input_schema``) — the same two artifacts ``scan_finance.py``
    already produced from the live capture, just read instead of regenerated.
    """
    scan = json.loads((SCAN_DIR / f"{server}.json").read_text())
    safe_names = {t["tool"] for t in scan["tools"] if t.get("primary_op") in SAFE_OPS}
    catalog = json.loads((SCAN_DIR / "tool_lists" / f"{server}.json").read_text())
    entries = catalog["tools"] if isinstance(catalog, dict) and "tools" in catalog else catalog
    schemas = {}
    for entry in entries:
        name = entry.get("name")
        if name in safe_names:
            schemas[name] = entry.get("input_schema") or entry.get("inputSchema") or {}
    return schemas


async def _drive(client_url: str, transport: str, tool_schemas: dict[str, dict],
                  n: int, pace: float, seed: int, out_path: Path, org: str) -> None:
    rng = random.Random(seed)
    tool_names = sorted(tool_schemas)
    harvest: dict[str, list] = {}
    written = ok = failed = 0
    started = time.time()

    def _client(headers):
        if transport == "sse":
            return sse_client(client_url, headers=headers)
        return streamablehttp_client(client_url, headers=headers)

    headers = {"Authorization": "Bearer placeholder-token-for-real-warmup",
               "X-Agent-Id": org}
    async with _client(headers) as conn:
        read, write = conn[0], conn[1]
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = {t.name for t in (await session.list_tools()).tools}
            usable = [t for t in tool_names if t in listed]
            print(f"{org}: {len(listed)} tools advertised, {len(usable)} usable read-only "
                  f"of {len(tool_names)} classified read-only", flush=True)
            if not usable:
                print(f"{org}: nothing usable, stopping", flush=True)
                return

            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("w", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(CSV_HEADER)
                while written < n:
                    tool = rng.choice(usable)
                    call_args = fill_args(tool_schemas[tool], rng, harvest)
                    status = "OK"
                    try:
                        result = await asyncio.wait_for(
                            session.call_tool(tool, call_args), timeout=30)
                        if getattr(result, "isError", False):
                            status = "ERROR"
                            failed += 1
                        else:
                            ok += 1
                            _harvest_from(_json(result), harvest)
                    except asyncio.TimeoutError:
                        status, failed = "TIMEOUT", failed + 1
                    except Exception as exc:  # noqa: BLE001 - a failed call is still real traffic
                        status, failed = f"EXC:{type(exc).__name__}", failed + 1
                    written += 1
                    writer.writerow([written, org, f"Real Agent@{org}", "REAL", "", tool,
                                     status, json.dumps(call_args), "real_mcp"])
                    if written % 50 == 0:
                        fh.flush()
                        rate = written / max(time.time() - started, 1e-6)
                        print(f"  {org}: {written}/{n}  ok={ok} failed={failed} "
                              f"({rate:.2f} calls/s)", flush=True)
                    if pace:
                        await asyncio.sleep(pace)

    print(f"{org}: wrote {written} calls (ok={ok}, failed={failed}) -> {out_path}", flush=True)


async def run_one(server: str, n: int, pace: float, seed: int, out_dir: Path) -> bool:
    cfg = rmf.SERVERS[server]
    org = ORG[server]
    tool_schemas = load_safe_tools(server)
    print(f"\n{'=' * 70}\n{server}: {len(tool_schemas)} read-only tools classified "
          f"from the static scan\n{'=' * 70}", flush=True)

    port = rmf._free_port()
    if rmf._port_open(port):
        print(f"{server}: port {port} already in use, skipping", flush=True)
        return False

    out_dir.mkdir(parents=True, exist_ok=True)
    launch_log = out_dir / f"{server}_launch.log"
    if cfg.get("run_cmd"):
        launch_cmd = [str(REPO / cfg["run_cmd"][0]), *cfg["run_cmd"][1:]]
        launcher_env = {**os.environ, **cfg.get("env", {})}
        # These servers hardcode :8080 in run_cmd; only one can run at a time here.
        launch_cmd = [a if a != "8080" else str(port) for a in launch_cmd]
    else:
        server_dir = REPO / cfg["server_dir"]
        launcher_env = {
            **os.environ,
            "FIN_SERVER_DIR": str(server_dir),
            "FIN_MODULE": cfg["module"],
            "FIN_ATTR": cfg["attr"],
            "FIN_FACTORY": "1" if cfg.get("factory") else "",
            "FIN_HOST": "127.0.0.1",
            "FIN_PORT": str(port),
            "FIN_TRANSPORT": cfg.get("transport", "sse"),
            **cfg.get("env", {}),
        }
        if cfg.get("python_bin"):
            launch_cmd = [str(REPO / cfg["python_bin"]), str(rmf.LAUNCHER)]
        else:
            launch_cmd = ["uv", "run", "--project", str(server_dir)]
            for dep in cfg.get("uv_with", []):
                launch_cmd += ["--with", dep]
            launch_cmd += ["python", str(rmf.LAUNCHER)]

    print(f"[1/2] starting {server} on :{port} ...", flush=True)
    with open(launch_log, "w", encoding="utf-8") as lf:
        proc = subprocess.Popen(launch_cmd, stdout=lf, stderr=subprocess.STDOUT,
                                env=launcher_env, cwd=str(REPO))
    if not rmf._wait(port, 180, proc):
        print(f"{server}: did not start — see {launch_log}", flush=True)
        proc.terminate()
        return False
    print(f"      ready, log -> {launch_log}", flush=True)

    transport = cfg.get("transport", "sse")
    client_url = f"http://127.0.0.1:{port}{cfg.get('client_path', '/sse')}"
    print(f"[2/2] driving {n} real calls through {client_url} ({transport}) ...", flush=True)
    ok = True
    try:
        await _drive(client_url, transport, tool_schemas, n, pace, seed,
                     out_dir / f"{org}_real.csv", org)
    except Exception as exc:  # noqa: BLE001
        print(f"{server}: session error: {exc}", flush=True)
        ok = False
    finally:
        proc.terminate()
        proc.wait()
        rmf._wait_closed(port)
    return ok


async def run(servers: list[str], n: int, pace: float, seed: int, out_dir: Path) -> int:
    rc = 0
    for server in servers:
        try:
            if not await run_one(server, n, pace, seed, out_dir):
                rc = 1
        except Exception as exc:  # noqa: BLE001 - one server's failure must not stop the rest
            print(f"{server}: FAILED entirely: {exc}", flush=True)
            rc = 1
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True,
                        choices=[*sorted(ORG), "all"])
    parser.add_argument("--n", type=int, default=600)
    parser.add_argument("--pace", type=float, default=0.1,
                        help="seconds between calls, so the free public APIs aren't hammered")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    servers = sorted(ORG) if args.server == "all" else [args.server]
    return asyncio.run(run(servers, args.n, args.pace, args.seed, args.out))


if __name__ == "__main__":
    raise SystemExit(main())
