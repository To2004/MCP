# Gateway at Scale: Runtime or Semi-Runtime, How Many Callers, What Breaks

Overnight runs, 2026-10-14/15: what the framework costs per call, how it behaves with many
callers, how much traffic one gateway process carries, what breaks first, and whether
scoring belongs before forwarding (runtime) or after it (semi-runtime). The load tests ran
on dedicated 48-core CPU nodes against local fake MCP servers, so the gateway is the only
thing measured; the per-call benchmarks used the real remote-GitHub artifacts and the 100k
synthetic org corpus translated to the remote server's tool names.

## Answers first

| Question | Answer, with the number behind it |
|---|---|
| Can the framework run **before** each call is forwarded? | Yes. A call's whole score (cell, `B × L`, input level) costs **~40 µs median, 0.29 ms p99** after warm-up. Against a server that takes 400 ms (GitHub-like), inline scoring adds nothing measurable. |
| Does cost grow with the number of callers? | No: 39–43 µs median from 1 to 100,000 possible callers (35k active). Memory ~15 KB per active caller. |
| Does cost grow as history fills? | No: 40–45 µs per call across a million calls from one caller; memory stays 112 MB (each history is capped). |
| How much does one gateway process carry? | **Today (httpx): ~600 calls/s, and it collapses above ~64 requests in flight** (64 calls/s at 256 agents, 2 at 1,024). With aiohttp as the upstream client: ~1,500 calls/s, no collapse at 256. |
| Why the collapse? | Profiled: at 256 agents **70% of the gateway's time is in httpcore's `_assign_requests_to_connections`** (10M connection checks for 1,150 requests). Not the framework, not logging. |
| How do we carry a lot of people? | Several gateway processes, each caller routed to the same one by a hash of its token. Measured scaling with aiohttp: 1 → 2 → 4 → 8 processes = 1.7k → 3.2k → 6.2k → 11.3k calls/s (scoring off), 1.4k → 2.6k → 4.9k → 9.2k (inline). |
| Runtime or semi-runtime? | Both work. Inline costs ~10–20% of a saturated process; scoring in a separate process from the log decides **2.8 ms (p50) / 6 ms (p99)** after the request, and one scorer process keeps up with **~14,000 calls/s**. Recommendation below. |
| Does a restart lose the dynamic history? | Not any more: history saved and restored (`state_file`); 400 real calls stopped after 250 and restarted score identically to an uninterrupted run (and differently without the saved state). |
| Is storage a bottleneck? | Speed no (log 25,600 records/s; SQLite 18,000/s batched). **Volume yes**: ~3.6 KB per record, ~3 records per call, ≈ 1 TB/day at 1,000 calls/s. |

## Per-call cost (`bench_scorer.py`, `results_scorer*.jsonl`)

| Part of a call | µs, before | µs, now |
|---|---:|---:|
| Static cell (arguments → asset → cell) | 179 | 19 (cached) |
| Runtime factor `B × L` | 13 | 9 |
| Input rules | 29 | 17 |
| Whole call, mean | 212 | 63 |

The asset lookup was 85% of a call: `binding.identifiers.name_coverage` re-tokenises both
strings for every asset × argument (~18 times a call). It is a pure function, so
`framework.RouteScorer` now caches the lookup per `(tool, arguments)` (bounded, 65,536
entries); results identical on 20,000 of 20,000 calls. Only 8,718 of the corpus's 100,000
calls are distinct. A cache inside `name_coverage` (shared code, not changed) gave the same
speed-up and would also help calls whose combination is new.

**Many callers** (300k calls on a Zipf curve, history per caller):

| Callers (active) | µs p50 / p99 | Memory growth | Save, original `snapshot` | Save, one pass | Restore |
|---|---|---:|---:|---:|---:|
| 1 | 39 / 261 | 28 MB | 0.0 s | — | 0.0 s |
| 1,000 | 39 / 255 | 140 MB | 3.3 s | 0.05 s | 0.24 s |
| 10,000 (9,578) | 42 / 250 | 314 MB | 349 s | 0.36 s | 0.71 s |
| 100,000 (34,817) | 43 / 263 | 536 MB | hours (not run) | 0.44 s | 1.07 s |

`gate_runtime.GateScorer.snapshot` rescans every key for each caller, so saving N callers
costs N × keys. `RouteScorer.snapshot_all` builds the same output (byte-identical, tested)
in one pass; `restore_all` loads it back.

## Throughput (`loadtest.py`; full tables in [`results_tables.md`](results_tables.md))

Calls/s, scoring **inline**, fast fake server, per number of gateway processes:

| Gateway | Processes | 16 agents | 64 agents | 256 agents | 1,024 agents |
|---|---:|---:|---:|---:|---:|
| httpx (today) | 1 | 577 | 608 | **81** | **4** |
| httpx | 4 | 2,762 | 2,384 | 2,068 | 277 |
| httpx | 8 | 4,096 | 4,830 | 3,976 | 2,631 |
| aiohttp | 1 | 1,310 | 1,387 | 1,182 | 667 |
| aiohttp | 4 | 4,250 | 4,941 | 4,944 | 4,193 |
| aiohttp | 8 | 5,309 | 9,037 | 9,192 | 8,002 |

With a **400 ms** server (GitHub-like), what agents get:

| Setup | 64 agents | 256 agents | 1,024 agents |
|---|---|---|---|
| Direct, no gateway | 158/s, 403 ms | 621/s, 404 ms | 2,229/s, 423 ms |
| aiohttp, 4 processes, inline | 157/s, 404 ms | 621/s, 404 ms | 2,358/s, 406 ms |
| httpx, 4 processes, inline | 156/s, 407 ms | 515/s, 483 ms | **189/s, 4.3 s** |
| httpx, 1 process, inline | 128/s, 516 ms | **45/s, 4.5 s** | **1/s** |

Requests in flight = calls/s × server latency, so a slow server is what fills a gateway:
1,000 calls/s against GitHub keeps ~400 requests open at once.

## Runtime, semi-runtime, or both

| | Inline (runtime) | Background, same process | Separate scorer from the log |
|---|---|---|---|
| Decision exists | before forwarding | ~0 ms after | 2.8 ms p50, 6 ms p99 after |
| Can block a call later | yes | no | no |
| Cost to the gateway | ~10–20% of a saturated process | same | none |
| Capacity of the scoring | per gateway process | per gateway process | ~14,000 calls/s per scorer process |

Measured: `background` performed like `inline` (same CPU, same process), so it buys nothing.

## Storage (`bench_storage.py`)

| How | Records/s |
|---|---:|
| JSONL, open + close per line (before tonight) | 14,900 |
| JSONL, kept open, flushed per line (now) | 25,600 |
| SQLite WAL, commit per row | 6,100 |
| SQLite WAL, commit per 1,000 | 17,600–18,700 |

## Things that broke, and what was changed

- **Asset lookup = 85% of a call** → bounded cache in `framework.py`.
- **History save was N × keys** (349 s at 10k callers) → one-pass `snapshot_all`.
- **Log file opened, mkdir'd and closed per message** → kept open, flushed per line (+70%).
- **httpx connection pool collapses** above ~64 in flight → not changed (aiohttp would be a
  new dependency); measured with `gateway_aiohttp.py`, an experiment-only variant.
- **uvicorn `--workers N` adds ~40 ms to every request on this cluster** (1.3 ms with one
  worker, 43 ms with two) → run separate processes, never `--workers`.
- **Port 9100 is the node's Prometheus exporter** → tests use 18800+/19100+.
- **Asset name on cell ties depends on Python's hash seed** (`binding.scoring`); risk is
  unaffected; not changed.

## Reproduce

```bash
uv run python reports/experiments/gateway/scale/bench_scorer.py all
uv run python reports/experiments/gateway/scale/bench_storage.py
sbatch reports/experiments/gateway/scale/loadtest.sbatch                     # httpx
GATEWAY=aiohttp MODES=off,inline,background LEVELS=16,64,256,1024 SUFFIX=_aiohttp \
    PORT_OFFSET=500 sbatch --export=ALL reports/experiments/gateway/scale/loadtest.sbatch
UPSTREAM_DELAY_MS=400 MODES=direct,inline LEVELS=64,256,1024 SHARDS=1,4 SUFFIX=_latency400_httpx \
    sbatch --export=ALL reports/experiments/gateway/scale/loadtest.sbatch
uv run python reports/experiments/gateway/scale/semi_runtime.py --levels 16,64,256
python3 reports/experiments/gateway/scale/summarize.py > results_tables.md
```

Jobs 22979117, 22979419, 22979456, 22979457 (manifest: `runs/gw-loadtest/manifest.json`).
One cell may be disturbed: httpx, 2 processes, background, 1,024 agents (job 22979412 was
cancelled 17 s after starting on the same node and ports).
