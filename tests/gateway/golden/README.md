# Gateway golden files

INF-3 of the v5 plan: a recorded gateway log, re-scored offline with the route's v4 behaviour
policy, must give the same CSV after every change, and recording the same traffic again must
give the same lines. `tests/gateway/test_golden_gateway.py` checks both on every run.

## Files

| File | What it is |
|---|---|
| `github.jsonl` | A synthetic gateway log (gateway-log/3), written by the real gateway app in front of a fake upstream, with callers signed in by the test identity provider (`tests/gateway/tokens.py`) and a fake clock. Four invented callers over five days, between a `gateway_started` and a `gateway_stopped` line (the run goes through the app's lifespan). Nothing in it is real. |
| `scan.json`, `breadth.json` | The route's synthetic scan and breadth specs |
| `behaviour_policy_v4.json` | The route's v4 behaviour policy (limits and a required earlier step) |
| `github_scored.csv` | What `score.py` writes when it re-scores `github.jsonl` with those files: the pin |
| `CHANGELOG.md` | One line per regeneration, naming the change that moved the CSV |

The re-score test compares every CSV column except `score_us`, which is wall-clock timing.
The re-record test compares every log line except `gateway.decision.score_us`, the hash chain
(`gateway.prev_sha256`, which covers `score_us`) and `gateway.config_sha256`, which covers the
artifacts' paths and so depends on the folder a log is recorded in. A separate test checks
that a re-recorded v4 route keeps its pre-v5 config digest; it is marked `xfail` until
`proxy._config_digest` hashes `config.digest_view` (proxy.py is outside Batch 0).

## Rules

- Never copy `runs/gateway/*.jsonl` here: real logs can hold real identities and tokens.
- Re-baselining the CSV needs a changelog line naming E9, AI-3 or PS7, the only changes
  allowed to move it.

## Regenerating

```bash
uv run python -m tests.gateway.golden_log --reason "AI-3: <why the re-score changes>"
uv run python -m tests.gateway.golden_log --rerecord --reason "E9: <why the lines change>"
```

The first form keeps `github.jsonl` and the artifacts and rewrites only the CSV, from the
pinned log, so a diff shows scorer drift alone. `--rerecord` (a change to the live gateway's
lines, such as E9) first re-records the log and the artifacts. Both append the reason and the
mode to `CHANGELOG.md`. A re-recorded log is not byte-identical from run to run: its live
decision lines carry `score_us`, and the hash chain covers those lines. The CSV is identical
apart from `score_us`.

## References

- [v5 implementation plan](../../../reports/experiments/dynamic_dimensions/knowledge_base/v5-implementation-plan.md), Batch 0, step 0.2
- [v5 design spec](../../../reports/experiments/dynamic_dimensions/knowledge_base/v5-design-spec.md), section 4.2 (INF-3)
