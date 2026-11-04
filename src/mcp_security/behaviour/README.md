# Behaviour multiplier

This is the dynamic layer's behaviour part. It answers "how strange is this call, for this agent, compared with his own last 90 days?" and gives a multiplier between ×0.7 and ×5. It never reads a tool's arguments: it uses only the request's metadata and the static scan's labels. The gateway runs it on every request and reports `dynamic_risk` = static level (1–5) × multiplier, which lies between 0.7 and 25.

## Files

| File | What it does |
|---|---|
| `engine.py` | `BehaviourEngine.observe(Message) -> Verdict`, one message at a time in arrival order. It holds v4's 15 dimensions (v5: 16, with Read volume; see `engine.dimension_groups`), the warm-up, and 90 days of memory per agent kept per day (bounded). `snapshot`/`restore` let it survive a restart. `score` gives a verdict without learning and `commit` learns from it (for v1-v4, `observe` is exactly the two). |
| `memory.py` | The bounded memory: per-day counts and means over 90 days, sliding windows, and the org discount's first uses. |
| `clock.py` | The caller's local day (04:00 rollover), hour and weekend from a timestamp and an IANA zone, daylight saving included (v5, B9). Pure functions. |
| `policy.py` | The policy (rule values, limits, required earlier steps) as JSON, and `derive_policy`, which learns it from ordinary traffic until an organisation writes one. Each limit is set so the rule fires on at most 0.5% of ordinary agent-days. A tool requires another when that one came earlier in 99.5% of its sessions (seen in at least 50 sessions). A v1-v4 policy file holds only the fields its design uses, so it is byte-identical to the one written before v5. CLI: `python -m mcp_security.behaviour.policy --log <gateway log> --out <policy.json> --days 30`. |

## Design v5 (being built)

`design = "v5"` is accepted and runs. So far it has its interfaces only (Batch 0 of
`reports/experiments/dynamic_dimensions/knowledge_base/v5-implementation-plan.md`): every v5
config switch with its v1-v4 value and its v5 default (`engine.DESIGN_VALUES`), the new
`Message` and `Verdict` fields, Read volume as the 16th dimension (`engine.dimension_groups`;
`BehaviourEngine.reply` is a no-op for now), and the legacy fixes E1, E2 and RF9 under
`legacy_fixes`, which is off for v1-v4. With every v5 switch off (`v5_switches_off()`), v5
gives exactly v4's verdicts. Golden pins of v1-v4 are in `tests/behaviour/golden/`.

On v5, `alert_line` and `alert_floor_rate` follow `alert_alpha`: change alpha or the
multiplier bounds with `replace_config` or `with_alert_alpha`, which derive both again
(`dataclasses.replace` refuses a stale line). `alerting_dimensions` and `budget_share` give
CAL-3's alerting dimensions and their shares (1/21 Cadence, 1/12 Footprint and Red Flags;
Missing handshake is watch-only).

## How a call is scored

Every dimension gives a score `s` from 0 to 1. 0.5 is the edge of ordinary: twice his usual, or something he does every other day.

| Kind | Formula | Dimensions |
|---|---|---|
| More than his usual | `s = (v + u) / (v + u + 2 (his average + u))`, u = 1 call / 1 minute / 1 KB | calls in the last hour, session length, request size |
| Rarer than his usual | `e = (his calls on things at most this common + 1) / (active days + 1)`, `s = c / (1 + 2e)`, c = 0.9 for tools | tool, asset, time of day (±1 hour, weekday or weekend) |
| Policy rule | broken → 0.9 (×3.6); protocol skip → 0.7 (×1.9) | new /16 network, new client family, burst (> 20 a minute), request over 10 KB, problematic sequence, protocol skip |

The strangest dimension decides: `M = 5^(2S−1)` when S ≥ 0.5, `0.7^(1−2S)` below. For an agent's first 5 tool calls, `M` = 1 (warm-up).

**Rule details:**

- **Protocol skip** counts only for an agent who normally sends `initialize`, so stateless clients do not fire on every call.
- **Problematic sequence** fires on any of these:
  - a write after reading a different sensitive asset in the same session;
  - a write to a sensitive asset not read in 7 days;
  - a tool listed in `requires_before` with none of its required tools earlier in the session.

## Where it comes from

- **Design and stress test:** [`reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md`](../../../reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md). It covers 33 edge cases plus 9 simulated organisations: the multiplier never left [0.7, 5], and ordinary agent-days at ×3 or more are 3–10%.
- **Tests:**
  - `tests/behaviour/test_engine.py`: those edge cases, plus bounds and restart;
  - `tests/gateway/test_framework.py`: live equals offline, and the state file.
