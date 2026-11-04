# Dynamic layer: as-built system map (design v4)

This is a map of what the code does today, not what the design documents say it does. It covers
the behaviour multiplier `M` (design v4, the default), the gateway that feeds it, the asset binding
it depends on, and the simulator behind the v4 numbers. Line numbers refer to the working tree on
2026-10-25: several of these files have uncommitted changes, and the three simulator files are
untracked. Every claim was checked against the code. Numbers marked *checked* came from scripts run
for this map. No external sources were used.

## 0. The path of one message

1. `proxy.Gateway.handle` reads the HTTP request, identifies the caller from the OAuth token and
   builds an `Exchange` (`gateway/proxy.py:155-185`, `_exchange` at `:411-445`).
2. Each JSON-RPC request is logged first (`wire_log.build_record`). The behaviour layer then reads
   its inputs **from that log line**, so the live gateway and an offline re-score get the same
   values (`gateway/framework.py:283-293`).
3. A `tools/call` goes to `RouteScorer.score` (inline before forwarding, or queued in arrival order:
   `proxy.py:292-304`). Any other request goes to `RouteScorer.observe` (`proxy.py:306-315`). The
   `initialize` reply goes to `RouteScorer.session_initialized` (`proxy.py:317-326`).
4. `RouteScorer.score` resolves the asset, computes the older runtime factor `B×L` and the input
   level, builds a `behaviour.Message` and calls `BehaviourEngine.observe`
   (`framework.py:165-217`).
5. The engine returns `Verdict(multiplier, strongest, score, scores, learning)`
   (`behaviour/engine.py:167-181`). The gateway logs only `behaviour` (= `M`), `behaviour_reason`
   and `dynamic_risk` (`framework.py:203-206`). It does **not** log `scores`, so `s2` and the
   per-dimension scores are not in the gateway log.

## 1. Every input the engine reads, and where it comes from

The engine's whole view of a message is `Message` (`engine.py:150-164`). It has no arguments field:

```python
class Message:
    """What the gateway knows about one request message, without reading its arguments."""
    ts: float; agent: str; method: str; session: str | None = None; tool: str | None = None
    asset: str | None = None; sensitivity: int | None = None; operation: str | None = None
    address: str | None = None; client: str | None = None; size: int = 0
```

| Field | Gateway source (file:line) | What it actually is | Caveats |
|---|---|---|---|
| `ts` | `record["ts"]` (`proxy.py:312`, `:334`), set by `now = time.time()` (`wire_log.py:241,255`) | the gateway's wall clock when it writes the request's log line | Day, hour and weekend are **UTC** (`engine.py:283,388`; `memory.py:17-19`). Not the client's time. |
| `agent` | `behaviour_fields`: `record.get("gateway.agent_id") or record.get("gateway.agent")` (`framework.py:288`) | with OAuth, `sha256(f"{issuer}\|{client}\|{user}")[:12]` (`oauth.py:110`): one baseline per issuer × app × user | Without OAuth every caller is `ANONYMOUS = Identity("anonymous")` (`config.py:63`), so the whole route shares **one** baseline. `None` falls back to `"gateway"` (`framework.py:156,187`). |
| `method` | `"tools/call"` hard-coded in `score` (`framework.py:187`); `record["mcp.method.name"]` in `observe` (`proxy.py:312`) | the JSON-RPC method | Only `tools/call` and `initialize` change scoring. Every other method (tools/list, notifications, ping, resources/*) only feeds network and client counts. Resources and prompts are never scored. |
| `session` | `record["mcp.session.id"]` (`framework.py:289`) = `policy.session(exchange.session)` (`wire_log.py:95-96,266`), from the `Mcp-Session-Id` header (`proxy.py:433`) | a **pseudonym** (HMAC-SHA256, or plain SHA-256 without `GATEWAY_LOG_KEY`, cut to 32 hex: `pseudonym.py:39-44`) | The engine keys sessions per caller: `f"{m.agent}\x1f{m.session}"` (`engine.py:600`). See section 8. |
| `tool` | `params.get("name")` (`proxy.py:338`) | the tool name in the body | The `Mcp-Name` header is only compared with the body for logging (`wire_log.py:405-416`). |
| `asset` | `cell.driver if known else None` (`framework.py:188`), from `MatrixScorer.score(tool, args)` | a **register asset id**: the asset whose scanned cell is worst among those the arguments did not rule out | Derived from the argument values. See section 2. |
| `sensitivity` | `scan["asset_sensitivity"][cell.driver]` (`framework.py:189`) | the driver's scanned sensitivity, 1-5 | When the call is unresolved this is the worst candidate's sensitivity. |
| `operation` | `"write" if impact >= WRITE_IMPACT else "read"` with `WRITE_IMPACT = 4` (`framework.py:51,190`) | taken from the scan's `tool_impact` | Every tool with impact below 4 counts as a **read**, including `add_issue_comment` (3), `update_issue_comment` (3) and `request_copilot_review` (2) in `github_remote.cells.json`. The simulator labels comments as writes (`normal_org_world.py:73`). |
| `address` | `record["client.address"]` (`framework.py:290`) = `client_behind(peer, X-Forwarded-For, trusted)` (`proxy.py:419-421`; `http_wire.py:31-46`) | the peer IP, or the nearest untrusted `X-Forwarded-For` hop behind a trusted proxy | Reduced to a /16 (IPv4) or /48 (IPv6) by `network_of` (`engine.py:191-202`). Text that is not an IP is used as is. |
| `client` | `record["gateway.client"]` (`framework.py:291`) = `book.client(session) or exchange.client_info` (`wire_log.py:261`) | the **self-reported** `clientInfo` as `name/version`, from `initialize` or from `_meta["io.modelcontextprotocol/clientInfo"]` (`wire_log.py:145-153`) | The version is dropped (`engine.py:205-210`). The HTTP `User-Agent` is logged but **not** used. With no handshake and no `_meta`, `client` is `None` and the client dimension does not take part. |
| `size` | `record["gateway.message_bytes"]` (`framework.py:292`) = `len(json.dumps(message, ensure_ascii=False).encode())` (`wire_log.py:275,430-431`) | the byte length of the **re-serialised JSON-RPC message**, arguments included | Not the raw HTTP body length. |

**Never reaches the engine.** The client port, `User-Agent`, `Origin`, protocol version, token
scopes, `jti`, the RFC 8693 `act` chain, `user` and `app` as separate fields, JSON-RPC ids,
replies (outcome, error, latency), `tool_listed`, `catalog_match`, and header mismatches. None of
these appear in `behaviour_fields` (`framework.py:283-293`).

**Verdicts that are thrown away.** `observe` on a request that is not a tool call computes a
`Verdict`, and `proxy._observe` discards it (`proxy.py:312`). Network and client are scored on those
messages, but nothing is logged.

## 2. How the asset is resolved, and what "no arguments" means precisely

The live gateway resolves the asset with `binding.scoring.MatrixScorer` and **no discovery table**:
`self._matrix = MatrixScorer(artifacts.scan["cells"], artifacts.scan["bands"])`
(`framework.py:127`). The traffic-learned `AssetResolver` and `Discovery` that the paper describes
(`main-restructured.tex:899-913`) are used only in `scripts/evaluate_binding*.py`.

`RouteScorer._cell` (`framework.py:260-270`) memoises
`key = (tool, json.dumps(args, sort_keys=True, default=str))` in an LRU of
`CELL_CACHE_SIZE = 65_536` (`:109`). `MatrixScorer.score` (`binding/scoring.py:89-123`) then works
in four steps:

1. The candidates are the assets that have a scored cell for this tool that is not banded `na`
   (`:74-79`, `:85-87`). With **no candidate**, the result is `basis="no-cells"` and the engine gets
   `asset=None`.
2. With **exactly one candidate**, the result is `"sole-candidate"` and **the arguments are not
   read** (`:95-98`).
3. With **two or more candidates**, `_strings_in(args)` collects every non-empty **string value**
   at any depth (`:151-166`). Dict keys, numbers and booleans are skipped. Each value is matched
   against each candidate id with `name_coverage(value, asset)` (`:143`). That is the share of the
   id's `[a-z0-9]+` tokens covered by the tokens of `canonical_id(value)`, with prefix
   abbreviations of at least `_MIN_PREFIX_TOKEN` characters (`identifiers.py:155-185`). A score of
   0.8 or more (`NAME_MATCH_FLOOR`, `scoring.py:37`) means "named". A score above 0 but below 0.8
   means "sibling". The kept set is
   `{a for a in candidates if a not in siblings or a in matched}` (`:108`).
4. **The worst survivor wins:** `driver = max(chosen, key=lambda asset: candidates[asset])`
   (`:115`).

**What is read from the arguments:** the text of every string value, including free text such as
an issue body, a commit message, a file path or file contents. Only token coverage against
register ids is computed from it. No size, count or number is read here. The engine itself stores
only register asset ids: in its counts, `last_read`, `same_calls` keys and `assets_hour`
(`engine.py:672-696`). It never stores argument text.

*Checked* on `reports/experiments/gateway/github_remote/github_remote.cells.json` (19 register
assets; 38 tools with 1-11 candidates each, only 3 of them with a single candidate):

| Call (`get_file_contents` unless noted) | Driver handed to the engine | Basis |
|---|---|---|
| `repo="helios-public-site"` (sensitivity 1) | `repository-contents` (sensitivity 4), a facet | named |
| `repo="helios-scada-gateway"` | `helios-scada-gateway` (5) | named |
| `repo="website"` (not in the register) | `helios-scada-gateway` (5), the worst case | unresolved |
| `repo="website", path="docs/helios-public-site.md"` | `repository-contents` (4) | named |
| `list_issues`, `repo="helios-public-site"` | `issue-records` (3) | named |
| `create_issue` | `None` (no cells) | no-cells |

What this means for `M`:

- **Asset granularity.** The asset dimension, breadth, sweep, repetition, the first-access floor
  and unsafe sequence all see register ids, often a facet or the worst-case candidate, not the
  concrete repository. In the simulator the asset is the concrete repository name with its true
  sensitivity (`normal_org_world.py:394-395`).
- **The floor fires once, then goes quiet.** Every call on a repository missing from the register
  resolves to `helios-scada-gateway`. Its first such call raises the first-access floor (×3.6). After
  that the asset is "known", so a real later peek at `helios-scada-gateway` gets no floor. This
  follows from the code (`engine.py:494-498`); it was not measured.
- **The caller can steer resolution.** Agent-written text can move the driver *down*. Adding
  `path="docs/helios-public-site.md"` to a call on an unregistered repository moves the driver from
  sensitivity 5 (cell 75) to sensitivity 4 (cell 48) (*checked*). This contradicts "cannot be moved
  by anything an attacker writes into an argument" (`binding/__init__.py:12`; also
  `resolver.py:11`, `main-restructured.tex:897`): no model runs on the call path, but string
  matching over free text can be steered.

**The same `RouteScorer.score` call also reads the arguments elsewhere:**

- the runtime factor `B×L`: `self._gate.score(self.connection(caller), tool, args)`
  (`framework.py:181`), which parses argument quantities such as page sizes
  (`scripts/dynamic_design/gate_runtime.py:124-131`);
- the stage-2 input rules: `evaluate_call(rows, args, ...)` (`framework.py:272-280`);
- the log line: argument keys, an argument pseudonym and typed effects (`wire_log.py:394-401`),
  plus the full body when `log_bodies` is `all` or `requests`.

**Suggested precise wording:** *"The behaviour multiplier M reads no argument values. It uses two
features the gateway derives from the request: the register asset that the static side's
deterministic name matching resolves from the call's string arguments (and that asset's scanned
sensitivity), and the request's size in bytes."* The current wording, "computed without reading
the call's arguments" (`DYNAMIC-LAYER-V4-NOTES.md:19,205`), is accurate only for the engine
function itself.

## 3. Formulas and constants as implemented

**Where the constants live.**

- Module constants (`engine.py:66-81`): `MAX_MULTIPLIER=5.0`, `MIN_MULTIPLIER=0.7`,
  `EDGE_OF_ORDINARY=0.5`, `TOP_SENSITIVITY=5`, `SAME_CALL_WINDOW_S=600`.
- `HABIT_RULES = {burst, sequence, many_assets}` (`engine.py:106`).
- `BehaviourConfig` (`engine.py:111-147`): `history_days=90`, `warmup_calls=5`, `tolerance=2.0`,
  `call_unit=minute_unit=1.0`, `byte_unit=1000` (v1 only), `tool_ceiling=origin_ceiling=0.9`,
  `rule_score=0.9`, `protocol_skip_score=0.7`, `burst_per_minute=20`,
  `request_limit_bytes=10_000`, `request_limit_by_tool={}`, `many_assets_per_hour=None`,
  `ipv4_prefix=16`, `ipv6_prefix=48`, `sensitive_level=4`, `sensitive_step=0.1`,
  `read_memory_days=7`, `normally_initializes_after=3`, `onboarding_days=14`,
  `org_discount_agents=3`, `org_discount_days=7`, `weekend_prior_days=4.0`, `max_sessions=50_000`,
  `requires_before={}`.
- Policy learner (`behaviour/policy.py:53-57`): `QUANTILE=0.995`, `SEQUENCE_SHARE=0.995`,
  `MIN_SESSIONS=50`, `MIN_TOOL_DAYS=50`, `KB=1000`.
- Memory: `FirstUses.PRUNE_AT=4096` (`memory.py:216`).
- Gateway: `WRITE_IMPACT=4` (`framework.py:51`), `MAX_SESSION_OWNERS=100_000`
  (`wire_log.py:60`).

**Multiplier** (`engine.py:184-188`): `5 ** (2s-1)` if `s >= 0.5`, else `0.7 ** (1-2s)`. The max is
taken in `observe` (`:297-299`), and `M = 1.0` when no dimension takes part (`:295-296`). Each +0.1
of `s` above 0.5 multiplies `M` by 5^0.2 = 1.380.

**Excess score** (`engine.py:584-589`):
`scores[name] = (value + unit) / (value + unit + self.config.tolerance * (usual + unit))`. A
dimension takes part only when `usual` is not `None`.

- `usual` comes from `DailyMean.mean_then_add` (`memory.py:143-158`). It is the **call-weighted**
  mean of the value as sampled at each of his past calls, today excluded (`daily=True` in v3+).
  Each call contributes one sample, so busy hours are over-represented.
- The values: `len(recent)` (tool calls in the trailing hour, this call included: `engine.py:374-378`);
  `minutes` since the session's first message (`:379`); `assets_hour.distinct()`,
  `writes_hour.total()` and `same_calls.count((tool, asset))`, all including this call
  (`:522-535`). `(tool, None)` is a valid repetition key.

**Rarity score**:

- Tool: `cfg.tool_ceiling / (1 + cfg.tolerance * e)` (`engine.py:413-414`).
- Asset: `1 / (1 + cfg.tolerance * e)` (`:419-420`).
- Network and client: `cfg.origin_ceiling / (1 + cfg.tolerance * e)` (`:355-356`). They take part
  only once their own counts have a past day (`:354`).
- `e` is `DailyCounts.per_day(values, tail=True)` (`memory.py:89-102`):

```python
n = self.count(values)
if not tail:      rare = n
elif n == 0:      rare = self.new_uses - (self.new_by_day.get(today, 0) if self.daily else 0)
else:             rare = sum(c for c in self.counts.values() if c <= n)
return (rare + 1) / (self.active_days(weekend, today) + 1)
```

- What is counted: tool and asset count **tool calls**; network and client count **messages** of
  any method. "Active days" means days with a tool call (tool, asset, hour) or with any message
  (network, client), today excluded.

**Hour of day** (v3/v4, `engine.py:558-567`): `pooled = around + [(not weekend, h) ...]`, then
`e_all = hours.per_day(pooled, False, None, today)`, then

`return (hours.count(around) + prior * e_all) / (hours.active_days(weekend, today) + prior)`

with `around` = the UTC hour ±1 for today's kind, weekday or weekend (`:389`). It counts **calls**,
not days, and has no tail.

**First-access floor** (`engine.py:489-502,430-431`):
`value = cfg.rule_score - cfg.sensitive_step * (TOP_SENSITIVITY - sensitivity)`, applied as
`scores[ASSET] = max(scores.get(ASSET, 0.0), look)`. It applies only when sensitivity ≥ 4 and the
asset is not in his counts up to yesterday. It is never org-discounted, and it applies during
warm-up.

**Red flags** (`engine.py:459-487`, in this order):

- sweep: `breadth > many_assets_per_hour`;
- burst: calls in the trailing 60 s, this one included, `> burst_per_minute`;
- oversized request: `m.size > request_limit_by_tool.get(tool, request_limit_bytes)`;
- missing handshake: see section 8;
- unsafe sequence (`:569-582`): a required earlier step is missing; or a write after another
  sensitive asset was read in the session; or a write to a sensitive asset with no read in the last
  7 days.

**Habit discount** (`engine.py:504-515`): `value / (1 + tolerance * broken / (tools.active_days + 1))`,
for `HABIT_RULES` only. `broken` counts the days in the last 90 that he raised the flag, today
excluded, warm-up days included.

**Org discount** (`engine.py:551-556`, `memory.py:231-238`): `others >= 3`. `others` counts
first-use **events** by other agents in `[ts - 7 d, ts)`. That is effectively distinct agents,
because `is_new` fires once per agent and value per 90 days. It applies only when `not known(value)`,
and it caps the score at 0.5.

**Warm-up** (`engine.py:288-290`): `warm = st.tool_calls >= 5 and today > st.first_day`.
`first_day` is the UTC day of his first message of **any** method (`:594`).

### Where the code differs from DIMENSION_FORMULAS.md

| # | Doc says (line) | Code does | Effect |
|---|---|---|---|
| D1 | hour of day: `e = (his calls within one hour of this time + 1) ÷ (his active days of this kind + 1)`, and weekends blended (`:186-189`, `:297-307` "A weekend call is compared with…") | the 4-pseudo-day blend is applied to **weekday calls too**, and the kind-specific part has no `+1` (`engine.py:564-567`) | *Checked* on a 30-weekday agent: engine s = 0.14317 = the blend; the doc's `(+1)/(+1)` form gives 0.14554 |
| D2 | `2`: "at exactly 2× usual, s = 0.5" (`:147`); paper notes "twice the usual gives exactly 0.5" (`NOTES:237`) | `s = 0.5` exactly when `v = 2μ + u` | at `v = 2μ`, `s = (2μ+1)/(4μ+3)`: μ=1 gives 0.429 (×0.95), μ=5 gives 0.478, μ=100 gives 0.499 |
| D3 | "every other day (e = 0.5) gives s = 0.5" (`:182`); "one scale … 0.5 at every other day" (`:513-516`) | true only for κ = 1 (asset, hour) | tool, network, client (κ = 0.9): s(0.5) = 0.45 (×0.965); the neutral point is e = 0.4 |
| D4 | habit discount: "Raised every other day: 0.45 (it no longer takes part)" (`:335`) | a raised flag is always in `scores` (`engine.py:434-435`); it falls below 0.5 at `k/(A+1) = 0.4` | it still takes part: it can be `s1` (×0.965) or `s2` |
| D5 | the 5-call warm-up was removed in v3 (`:619`); "Warm-up: his first day" (`:799`) | `tool_calls >= 5` **and** past his first day (`engine.py:288-290`; same in the simulator, `normal_org_engines.py:339-341`) | a caller with fewer than 5 calls ever stays in warm-up after day 1 |
| D6 | "usual = his average of that number over 90 days" (`:146`) | a call-weighted mean of the value at each past call | session duration: with evenly spaced calls, μ ≈ half his (call-weighted) session length, so s = 0.5 near the *end* of a typical session, not at twice its length (derived) |
| D7 | Limits table: required earlier steps "none found" (`:638`) | seed 11 learned `fork_repository ← get_file_contents` (`results/normal_org_sim_seed11.json`, meta `learned_limits`) | that organisation raises unsafe sequence on such forks |
| D8 | "a merge with no review" is part of unsafe sequence (`:321`, `:604`) | it fires only when `requires_before` has it. The simulator **writes** it in (`normal_org_sim.py:72`); the live gateway has only what `policy.py` learns from the log, starting from an empty base (`policy.py:203`) | live: off unless learned |
| D9 | property 7: ablation from "log every call's scores once (`Verdict.scores`)" (`:851-853`) | the gateway logs `behaviour` and `behaviour_reason` only (`framework.py:203-204`) | leave-one-out is possible only in the simulator |
| D10 | `R = R_static × M`, R_static 1-5 (`:451`) | gateway: `static_level = cell.severity ** (1/3)` (`framework.py:194`). Simulator: the **tool's** static level 2-4 (`normal_org_world.py:60-87`, `normal_org_sim.py:434`). The gateway also logs a second number, `risk = cell × B×L` (`framework.py:200`) | two different R_static definitions, and two "dynamic" outputs |

## 4. The s = 0.5 neutral point of each dimension

| Dimension | Score | s = 0.5 exactly when | "0.5 = twice / every other day" exact? |
|---|---|---|---|
| call rate, write rate, breadth, repetition, session duration | excess, u = 1 | `(v+u)/(μ+u) = 2`, i.e. `v = 2μ + 1` | only for the smoothed ratio (D2). At his usual (`v = μ`), s = 1/3 exactly (×0.888) |
| asset | rarity, κ = 1 | `e = 0.5` | yes, where e is the tail count per active day (section 5) |
| hour of day | rarity, κ = 1, blended e | blended `e = 0.5` (calls in the ±1 h window per day) | in blended-e terms; it counts calls, not days (D1) |
| **tool, network, client** | rarity, **κ = 0.9** | **`e = κ − ½ = 0.4`**, once in 2.5 days | **no**: at e = 0.5, s = 0.45 (×0.965). The maximum is s → 0.9, i.e. ×3.62: these three alone can never exceed ×3.62 |
| red flags | set value 0.9 / 0.7 | never. The habit-discounted value is 0.5 at `k/(A+1) = 0.4` | n/a (D4) |
| first-access floor | 0.9 / 0.8 | never | n/a |
| org discount | cap | at the cap, s = 0.5 (×1) | exact |

**The answer to the κ = 0.9 question:** `0.9/(1+2e) = 0.5` gives `e = 0.4`. A tool, network or
client the agent uses at a rate of 0.5 a day scores 0.45 and slightly *lowers* risk (×0.965). The
doc's claim that "every score is built on the same curve … with 0.5 at every other day" (`:513-516`)
is exact for the asset and hour of day only.

**The practical floor.** In a normal call, the cadence counts sit near his usual, so they score
1/3. Under the max this puts ordinary calls near ×0.89, not ×0.7. *Checked*: an ordinary probe got
M = 0.888, with strongest dimension `assets_last_hour` at 0.333. ×0.7 needs every participating
score near 0, so "familiar lowers risk by at most 30%" is a bound that ordinary traffic rarely
reaches.

## 5. Is "this thing + everything rarer" an empirical p-value?

The doc says so at `:823-824`: *"an empirical p-value: the share of his past that was at least this
rare."* The code does not compute that.

- The numerator `N(v) = Σ_{w: n_w ≤ n_v} n_w` is the agent's call mass on values at least as rare as
  `v`, ties included (`memory.py:101`). Divided by his total calls `T`, it would be an empirical
  tail probability `p̂(v) = N/T`, which is the p-value the doc describes.
- The engine divides by **active days**: `e = (N+1)/(A+1) ≈ p̂ · T/A`. That is the tail probability
  times his daily call volume, i.e. the expected number of calls *per day* that land on something
  at least this rare. It is a rate, not a probability. It lies in `[1/(A+1), (T+1)/(A+1)]`, exceeds
  1 whenever `N > A`, and the doc's own example has `e = 12.8` for `repo-main` (`:211`).
- The doc itself rejected the plain share. "Plain share (calls to X ÷ all his calls)" gave 6-16%
  of agent-days at ×3, and "times per day" halved that (`:271-275`). So the p-value reading
  describes the *rejected* variant.
- For a value he never used, `N` is replaced by `new_uses`, the number of new values he started
  after onboarding (`memory.py:98-99`). Then `e` is a novelty rate per day, not a tail at all.
- Hour of day uses no tail (`tail=False`).

**A possible reading (derivation, not from a source):** under a Poisson approximation, the chance
of at least one call that rare in a day is about `1 − exp(−e)`, so `e = 0.5` means about 39%.
**Suggested wording:** "the empirical tail count of his own value frequencies, expressed per active
day: how many times a day he does something this rare". Drop "p-value".

## 6. The daily review list, and how it relates to R = R_static × M

**The list exists only in the simulator.** There is no review list in `src/`; the only mention is a
docstring at `framework.py:298`. The agent-day record is built in `normal_org_sim.py:427-435`:

```python
if M > rec[0]:
    rec[0], rec[2] = M, top
    ordered = sorted(scores.values(), reverse=True)
    rec[5] = ordered[1] if len(ordered) > 1 else 0.0
rec[1] = max(rec[1], r[10] * M)
```

- Every message counts toward the day's maximum M, `initialize` and `tools/list` included. `s2`
  comes from the **first** message that reaches the day's maximum M (strict `>`).
- The rankings compared (`:544-551`): `"M, ties at random"`, `"M, then strange dimensions"`,
  `"M, then second score"` and `"static x M"`. Ties at the cut are broken fractionally
  (`topk_probability`, `:468-495`). An episode is caught with probability
  `1 − Π(1 − p_day)` (`:556`).
- The doc's list is "rank agent-days by M, then by that call's s2" (`:453-455`). **R_static plays
  no part in it**, and neither does the ×3 alert line, which is drawn on M (`:566-568`).
  `R = R_static × M` is reported per call (`dynamic_risk`) but nothing ranks or alerts on it.

v4's gray episodes on the list, by ranking (the doc's table mixes top 4, used for four
organisations, with top 8, used for the large one, without saying so):

| Organisation (list) | M, s2 | M, strange dimensions | static × M |
|---|---|---|---|
| Main (top 4) | **58.2%** | 56.5% | 36.7% |
| Second seed (top 4) | 47.6% | **51.2%** | 32.8% |
| Heavy file writes (top 4) | 54.4% | **57.6%** | 39.1% |
| Small (top 4) | 71.4% | 71.4% | 67.1% |
| Large (top 8) | **57.4%** | 56.9% | 41.2% |

(`results/normal_org_*.md`, rows `| v4 | top k |`.) `s2` is chosen for the fewest ties at the
cut (0-2.2%). At top 4 it does not give the most gray episodes in 3 of the 5 organisations.

Two caveats on the static × M comparison:

- The simulator's static is the tool's level, not the gateway's per-asset cell.
- Most gray kinds use read or list tools (static 2-3), while the main ordinary alert, oversized
  request, is on writes (static 4). The comparison is partly decided by how the generator was
  written.

## 7. The simulator: traffic, gray episodes, tuning, held-out checks

**Generator** (`normal_org_world.py`). It covers 180 days, with day 0 a Monday
(`BASE_DAY = 20_003`), all in UTC, and the 26 GitHub tools with an operation label and a static
level (`:60-87`).

- **Organisation** (`:259-292`): about 100 repositories. Ten teams each have 6 services
  (sensitivity 2), a tools repository (3) and a deploy repository (4). There are 4 shared, 3 infra
  (4) and 3 sensitivity-5 repositories, plus about 11 new projects; 12 repositories are renamed on
  day 150.
- **Roster** (`:304-315`): 21 bots (12 CI, 4 triage, 5 report), people split across roles with
  weights 62/12/14/12, and 10 new hires.
- **People** (`:449-691`): lognormal per-person tool weights, a time zone in {0 (7 times), −6, −6,
  5.5}, 25% desktop clients, 30% remote, and per-day volume ~ lognormal. Each day has 1 + Poisson
  (2.5) sessions of at most 1.5 h. **3% of sessions skip `initialize`** (`:632`), and 50% send
  `tools/list`. Other habits: read-before-write with probability 0.3-0.7, a review step before
  85% of merges, and paging.
- **Labelled ordinary life:** vacations, sick days, travel, client switches, ISP changes, team
  transfers, role changes, new-tool adoption after day 130, a VPN change on day 110, a crunch on
  days 120-123, and SRE on-call nights at 02:00 local time.
- **Bots** (`:823-907`): 50% are stateless (no `initialize`). CI bots spread across 4, 12 or 40
  cloud /16s.
- **Gray episodes** (`:719-819`): each person has Poisson(0.6) episodes on days 95-172, at least 21
  days after starting, with kinds weighted by `GRAY_KINDS` (`:196-207`). `off_hours_batch` falls on
  a Saturday at 02:00. `shadow_script` uses a cloud /16, `python-requests/2.32`, 01:00-03:00, and
  sends no `initialize`. `overfetch` is a fixed 290 bytes, invisible by construction. Three CI bots
  each get a 400-800-call loop.
- **Evaluation:** days 0-89 are history and days 90-179 are scored (`normal_org_sim.py:68`). Limits
  are learned with `policy.derive_policy` on days 0-29, before any gray episode (`:73-75,258-262`).
  The org-discount first uses are **precomputed from the whole world** (`:327-351`) and searched by
  time (`normal_org_engines.py:619-628`).

**Parameters chosen after looking at results** (data-snooping risk), with the code's own words:

- `NEW_DETECTORS`: *"what the misses called for: breadth, writes and repetition per hour, sensitive
  first looks, weekend fallback, a size limit per tool"* (`normal_org_sim.py:85-89`).
- `RECOMMENDED`: *"the new detectors plus the fixes that helped"* (`:90-100`).
- `V3_DECIDED`: grading by the tool *"gained nothing in the five organisations"*, and no org
  discount on first looks because *"in the large organisation it hid peeks at secrets"*
  (`:131-136`). So all five organisations, the large one included, informed v3.
- Definitions changed between runs: *"Results before `v3 (decided)` counted first uses ever"*
  (`:329-330`), and the pre-v3 engines learned *"with policy.py dropping the written steps"*
  (`:1083-1085`).
- Profiles `more_pastes` and `heavy_files` were built *"for the size-per-tool check"*
  (`normal_org_world.py:221-232`).
- The doc lists the tolerance 2, the units, the ceilings 0.9, per-day counting, 5 and 0.7, the flag
  and floor values, 14 onboarding days, 4 weekend pseudo-days and 3 agents in 7 days as *"checked
  by simulation"* (`DIMENSION_FORMULAS.md:827-830`), as are the quantile 0.995 and per-agent-day
  limits (`:640-644`).
- Gray kinds are written to match detectors. For example, the shadow script runs at 01:00-03:00,
  where hour of day gives about ×5 (`:729-731`), and pastes of 15-500 KB sit above the 9-14 KB
  issue limits.

**Held-out checks that exist:**

| Results file | Seed | Profile | Agents | Engines run |
|---|---|---|---|---|
| `normal_org_sim` | 7 | main | 150 | 37 (all of the design search) |
| `normal_org_sim_seed11` | 11 | main | 150 | 17 |
| `normal_org_git_heavy_files` | 21 | heavy_files | 150 | 15 |
| `normal_org_git_small` | 31 | more_pastes | 60 | 15 |
| `normal_org_git_large` | 41 | more_pastes | 300 | 15 |

- **No organisation is held out for v3 or v4.** All five were used for v3 decisions, and v4 was
  compared on all five at once.
- All five come from the same generator and differ only in seed, size and `Profile`.
- **Port check** (`normal_org_port_check.json`): v3 ran on all five organisations with 0
  differences. v4 ran **only on the main one**: 3,495,900 messages, 0 differences.
- There are also hand-made scenarios (`normal_org_sim.py:693+`). The design documents report no
  evaluation of `M` on real gateway traffic.

**Reproducibility problems:**

- **The worlds are not deterministic across interpreter runs.** `repo_prefs` sorts by
  `hash((p.spec.aid, team, r.name)) % 9973` (`normal_org_world.py:525`), and Python salts string
  hashes. *Checked*: for `dev-021` (seed 7) the row count is the same (10,222) under
  `PYTHONHASHSEED` 1, 2 and 3, but the digests of the asset sequence differ (`3391f563…`,
  `1883ae52…`, `8ae37d66…`). Each reported number is one draw, and it cannot be rebuilt bit for
  bit.
- `normal_org_world.py`, `normal_org_engines.py` and `normal_org_sim.py` are **untracked** in git,
  so no result is tied to a code version.

**Inputs the simulator has that the gateway does not:**

- concrete assets with their true sensitivity (the gateway has resolved register drivers, section
  2);
- a `client` on every row, even for the shadow script and stateless bots that send no
  `initialize` (`normal_org_world.py:740-748`, `:828-842`). Live, those calls have `client = None`;
- comments labelled as writes;
- a written merge-review step;
- a static level per tool, not per cell.

## 8. How the session and `initialize` work, and what depends on them

**The flow on a stateful server:**

1. The `initialize` request carries no session id, so `exchange.session` is `None`.
   `proxy._observe` sends the engine `Message(method="initialize", session=None, address, client,
   size)` (`proxy.py:184-185,312`). The engine counts the network and the client, but
   `if message.method == INIT_METHOD and session:` (`engine.py:286`) is false, so nothing is marked
   as initialized.
2. The upstream reply's `Mcp-Session-Id` becomes the session:
   `session = reply.headers.get(SESSION_HEADER) or exchange.session`. Then
   `self.sessions.start(session, exchange.client_info)` stores the client name for later calls
   (`proxy.py:201-206`).
3. Each reply line is logged with that session. `_answered` sees `mcp.method.name == "initialize"`,
   recovered from the request id (`wire_log.py:245-246`), and calls
   `scorer.session_initialized(caller, session, ts)` (`proxy.py:317-326`). That sends
   `Message(ts, caller, "initialize", session)` with **no address and no client**
   (`framework.py:160-163`). The engine creates `SessionState(start=ts, initialized=True)`
   (`engine.py:597-608`).
4. Later `tools/call`s in that session find the state. `session_length` is measured from the reply
   time (`engine.py:379`), and `gateway.client` comes from `SessionBook`.

**What depends on the session:**

- **Session duration** takes part only `if session` (`engine.py:403-404`).
- **"Normally initializes":** `sessions_seen >= 3 and 2*sessions_initialized >= sessions_seen`
  (`:390-393`). A session is counted at its first tool call (`:446-450`).
- **Missing handshake:** `if warm and session and not session.initialized and
  normally_initializes` (`:483`).
- **Unsafe sequence**, in-session checks: `session.read_sensitive` and `session.tools`
  (`:574-579`).
- **Client** on calls: `book.client(session)` (`wire_log.py:261`).

| Situation | What the code does |
|---|---|
| Gateway restart; the client keeps its session | Engine sessions are not in `snapshot()` (`engine.py:611-617`), and `SessionBook` is in memory. Every call raises missing handshake (×1.9, if he normally initializes). Session duration restarts. `client = None`, so the client dimension drops out. |
| More than 50,000 open sessions, or 2 replicas | LRU eviction (`engine.py:604-605`), or per-process state: the same false "missing handshake". |
| Another caller rides a session | The engine keys per caller (`:600`), so for that caller the session never started: missing handshake. The gateway separately logs `session_agent_mismatch` (`proxy.py:173-179`); the engine never sees that notice. |
| Stateless server (no `Mcp-Session-Id`) | `session = None` throughout. Session duration and missing handshake never take part; the in-session sequence checks never fire. **Any tool with `requires_before` raises unsafe sequence on every call**, because `not (session and …)` is true (`:574`). The client dimension drops out on calls. `policy.py` learns no required steps (`policy.py:97`). |
| A script that never sends `initialize` | `client = None` (no `clientInfo`, no `_meta`), so the client dimension cannot flag it. Only network, hour of day and missing handshake can. |
| `DELETE` ends the session | `SessionBook.end` drops the stored client (`wire_log.py:225-229`). The engine's `SessionState` stays until LRU eviction. A reused id is still "initialized" but has `client = None`. |
| Offline re-score (`score.py`) | It replays non-call requests and `initialize` replies in log order (`score.py:144-159`). Calls whose body was not logged (`log_bodies: none`) are **skipped entirely**, behaviour included (`:134-136`), so the offline `M` diverges from the live decision lines. |
| Policy learned from a log | `messages_from_log` sets no asset (`policy.py:175-185`), so `many_assets_per_hour` stays `None` and the sweep flag is off. |

## 9. Where the paper draft disagrees with the code

- `main-restructured.tex:832-870` describes `L = D·A·N`, about 1-8, *"bounded below by 1"* (`:867`),
  and history that includes *"outcomes, errors, latency"* (`:871`). The engine never sees replies,
  and `M` goes down to 0.7.
- `:921-958` describes a persona profile ("highest asset sensitivity", session-size mean and
  standard deviation) and a CIA qualifier. That is the older runtime factor, not the v4 engine.
  `DYNAMIC-LAYER-V4-NOTES.md:195-280` is the replacement text, and it carries D2, D3 and the
  wording issue from section 2.
- The decision record carries both `risk` (cell × B×L, capped at 125) and `dynamic_risk`
  (cube root of the cell × M, `framework.py:200,206`). The paper should say which one is
  R_dynamic.

## References

All local files, repo-relative.

- `src/mcp_security/behaviour/engine.py`, `memory.py`, `policy.py`
- `src/mcp_security/gateway/proxy.py`, `framework.py`, `wire_log.py`, `http_wire.py`,
  `config.py`, `oauth.py`, `pseudonym.py`, `score.py`
- `src/mcp_security/binding/scoring.py`, `identifiers.py`, `resolver.py`, `__init__.py`
- `scripts/dynamic_design/gate_runtime.py`
- `reports/experiments/gateway/github_remote/github_remote.cells.json`
- `reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md` (v4) and
  `DIMENSION_FORMULAS_v3.md`
- `reports/experiments/dynamic_dimensions/normal_org_world.py`, `normal_org_engines.py`,
  `normal_org_sim.py`, and `results/normal_org_*.{md,json}`
- `paper_v5/main-restructured.tex` and `paper_v5/DYNAMIC-LAYER-V4-NOTES.md`
