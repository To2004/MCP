# Dynamic dimensions: findings and three plans

This summary covers which runtime dimensions should price "strange usage" of an MCP server's own tools by legitimate callers, and how three candidate designs compare at equal analyst load. The horizons are one month, one year and two years. Evidence comes from synthetic two-year worlds grounded in real GitHub calls (two seeds, plus two dense 75-day worlds), and from a literature and vendor review.

## What the tests show

Unless stated otherwise, numbers are at a fixed false-alarm budget and averaged over the two seeds. Full tables: `results_seed{1,2}.md`, `plans.md`, `drift.txt`.

1. **Each kind of strange usage is caught by its own dimension.** No single score covers all of them.
   - Repetition: loops 95–98%.
   - Rate: bursts 55–57%.
   - Size: page walks 80–95%; weekly habits 90–100%.
   - Reach: over-fetch 72–75%.
   - Asset novelty: fan-out 95–98%, slow creep 62–67%, sensitivity escalation 35–42%.
   - Tool novelty, policy rules and order: off-role tools 92–98%, skipped workflow steps 100%.
   - Dormancy: dormant agents waking 80%.
   - Time of week alone: off-hours 55–62%.
2. **Compared with whom.** Self ≈ self→peer hierarchy > peer > whole org for nearly every dimension. The org-wide reference is the weakest (time: 1% vs 32%).
3. **The peer reference resists self-normalisation.** A weekly page-walk habit scored against the caller's own history fades from 46% to 6% alerted by week 13. Against peers it stays at 19–34%.
4. **Sensitivity is a consequence, not a strangeness signal.** "Touched something more sensitive than usual" caught almost nothing (≤ 5%), because most callers already touch sensitivity-4 repos. Weighting alerts by static impact × sensitivity changes ranking, not detection.
5. **Don't sum surprise across dimensions.** A plain sum misses dormant agents (0–13%), off-hours (0%) and workflow skips (30–50%). Calibrating each dimension separately and then taking the strongest has no such blind spots.
6. **Horizon effects.**
   - In month 1, per-call baselines flood: they cannot stay under 2 caller-days per day.
   - In year 2, scope-type kinds degrade as the org grows: creep 47% → 14% and sensitivity escalation 78% → 55% for per-call baselines.
7. **Slow drift needs weekly aggregation against a re-anchored baseline.** This catches 47–60% of creep at under one alert per week. A rolling 8-week baseline catches 33–38%. A frozen, never-updated baseline fails: 64–70% false alarms on legitimate-change weeks.
8. **Still weak in every design:** off-hours use (≤ 26% once combined), sensitivity escalation into another team's repo, and slow creep.

## The three plans at equal analyst load

Detection share at ≤ 2 alerted caller-days per day:

| Plan | Month 1 | Months 2–2.5 | Year 1 | Year 2 |
|---|---|---|---|---|
| P1 guardrails + per-caller counters | 38% | 38% | 51% | 47% |
| P2 per-call baselines, self→peer | unreachable (floods) | 39% | 51% | 54% |
| P3 risk events → caller-day risk | 56% | 59% | 63% | 66% |

At ≤ 4 caller-days per day, P2 catches up with P3 in year 1 (80% vs 79%) but not in year 2 (65% vs 77%).

## Which topic to focus on

Topics are combined by adding risk per caller-day, with no policy rules. Each cell is mean detection at ≤ 2 caller-days per day (`focus_accumulated.md`).

| Topic | Month 1 | Year 1 | Year 2 |
|---|---|---|---|
| A volume over short time (repetition, rate, reach, size) | 36% | 29% | 32% |
| B what is touched vs peers (first touch vs self/team, breadth) | 22% | 15% | 12% |
| C order and time (next-tool rarity, new tool, time of week, dormancy) | 27% | 47% | 51% |
| A + C | 25% | 62% | 61% |
| A + B + C | 44% | 61% | 58% |

- A + C matches all three topics in years 1–2.
- B is the only topic that catches fan-out (91–100%). Through the weekly drift check, it is also the only one that catches slow creep (47–60%).

## Three ways to build the full dynamic layer

Each cell is mean detection at ≤ 2 caller-days per day, with no policy rules.

| Option | What it reads | Month 1 | Year 1 | Year 2 |
|---|---|---|---|---|
| 1 envelope only | caller, session, server, tool, time + static tool operation | 24% | 54% | 59% |
| 2 static-guided | option 1 + only the inputs static kept, handled by effect type | 44% | 61% | 58% |
| 3 learned token model | generic tokens per call, one model per caller-day | 39% | 34% | 37% |

- Option 3 is the best catcher of slow creep (57–61%), but weak on single rare events.
- Options 2 and 3 sharing one analyst load reach 55–56% (`hybrid.md`).
- Unregistered assets: 5% of repo calls in the first 3 months, about 48% after a year, 62–70% after two years. Strange usage on them is caught as well as on registered repos, because strangeness needs only an opaque asset handle. Only the consequence needs the register.

## Dimensions added from the Dynamic Context Catalog

Each dimension was scored alone at a 0.5% budget (`new_dims.md`).

- **Assets per session**, judged against the policy's Block 4 "one repository at a time": fan-out 90–100% with about 0% benign alerts. This is optimistic, because benign sessions in the world name one repo by design.
- **Consequence added up over a day:** weak (bursts 15–30%).
- **Weekly write share:** weak (habits 15–25%).
- **Share of calls on unregistered assets:** about 0%. It is not a strangeness signal: it measures register coverage, so it should trigger a re-scan.
- **Protocol dimensions** (client software change, how often the client re-lists tools, session churn): untested, because the world has no protocol messages.

## What to focus on: greedy selection (corrected worlds)

Strange usage is now injected at the caller's normal hours and inside its normal workflow. The earlier worlds gave "hour of week" and "order" free credit. Selection picks on one world and checks on the other, in both directions, at ≤ 2 caller-days per day (`select_pick{1,2}_v2.md`).

| Rank | Dimension | Gain (both directions) |
|---|---|---|
| 1 | Order: next-step rarity in the session | +16–19 |
| 2 | Size of each request (static `how_much` inputs) | +16–17 |
| 3 | First touch of an asset by this caller (static `which` input) | +6–8 |
| 4 | Calls per hour | +5–6 |
| 5 | New tool for this caller | +3 |
| 6–9 | Dormancy, assets per day, items per day, learned day model | +0–3 each |

- Five dimensions reach 45–51%; nine reach 55–57%.
- Hour of week is never picked. Off-hours use stays at 0% unless working hours are stated in the policy.

**Real-call checks (live corpora):**
- Benign callers repeat an identical call within their last 10 calls 8–16% of the time, so the repetition baseline must be per caller.
- 97% of benign GitHub runs name more than one repo (70% name three or more), so the policy's "one repository at a time" is a prior, not the observed normal.
- `per_page = 100` appears in about 13% of benign GitHub calls.
- Every capture shows the same client software (the SDK default), so client-software dimensions carry little information.

## Wire-log (gateway-log/2) dimensions and the ceiling

`wire_dims.py` adds three request-side dimensions the new wire log supports: argument keys new for this caller and tool, session length so far (`gateway.seq`), and sessions started per hour. At ≤ 2 caller-days per day they shift coverage rather than raise the mean (50% → 51%).

| Added dimension | What it improves |
|---|---|
| Argument keys | Page walks 77% → 89%, over-fetch 27% → 43% |
| Session length | Loops 32% → 44% |
| Sessions per hour | Bursts 61% → 85% |

They raise the **ceiling**:

| Analyst load (caller-days per day) | Five focus dimensions | Five + six more (wire + dormancy, assets per day, items per day) |
|---|---|---|
| ≤ 2 | 50% | 56% |
| ≤ 4 | 52% | 65% |
| ≤ 8 | 52% | 68% |

The wire log's who/where/client fields (`client.address`, `gateway.client`, `user_agent.original`) are recorded, but the only v2 log has one agent, one address and one client, so they cannot be measured yet.

## Dimension search across 9 scenarios (world2, final)

**Setup:**
- 60 dimensions and 21 kinds of strange usage at mild, medium and strong intensity.
- 9 scenarios: GitHub, Calendar and Slack; small, medium and large orgs; high churn; mostly bots; two repeat seeds.
- About 1–4 M messages each, grounded in real calls and real static labels.
- Generator fixes before the final run: roles keep their real tools, and effect-type strange calls sit inside normal sessions.

**Best single set for all scenarios at ≤ 4 agent-days per day:** 71% mean detection (60–78% per scenario) with about 10 dimensions. At ≤ 2 agent-days per day: 57%.

| Order | Dimension | Notes |
|---|---|---|
| 1 | New argument-key set for this agent and tool (Kruegel & Vigna attribute presence) | First in all 9 scenarios |
| 2 | First touch of an asset | |
| 3 | Client context: address + client + user agent, given the agent (Freeman et al.) | |
| 4 | Same call repeated within 10 minutes | |
| 5 | Addresses per hour | |
| 6 | Calls today | |
| 7 | Items requested today | |
| 8 | New user agent | |
| 9 | New recipients | |
| 10 | Peer-rare first touch, new action value, peer-rare new tool | |

**Specialists** (the best single dimension for its kind):

| Kind | Dimension | Detected |
|---|---|---|
| Loops | Identical calls | 93% |
| Bursts | Sessions per hour | 73% |
| Weekly habits | Monotone page/asset run | 97% |
| Cancel storms | List-to-call delay | 99% |
| Cancel storms | Retry after cancel | 97% |
| Skipped workflow steps | Write as the first call | 92% |
| Off-role tools | Next-tool rarity | 99% |
| Content dumps | Request bytes | 76% |

**Still weak:**
- Over-fetch (≤ 54%)
- Long time spans (≤ 60%)
- Protocol skip when mild (6%)
- Off-hours: 71% alone, but ≤ 7% once combined; it needs stated working hours

**False alarms:** about 0.2% of benign messages or fewer per dimension. The worst cases are addresses per hour during a role change (4.4%) and client context during a client upgrade (2.7%).

## Identity, log fields and scale (REPORT.md)

**Identity:**

| Identity the gateway sees | Detection at ≤ 4 per day |
|---|---|
| One token per person | 75% |
| Token shared by 10 people | 71% (off-role 91% → 65%, sensitivity escalation 90% → 71%, and attribution is lost) |
| Session only | 12% |

Key baselines by user + agent app, from OAuth `sub` and `client_id`.

**Log fields:**

| What the log keeps | Detection at ≤ 4 per day |
|---|---|
| Everything | 70% |
| No argument values (names + hash + size) | 64% |
| No wire fields | 60% |
| Envelope + wire only | 57% |
| Envelope only | 49% |

**Scale:** 10,000 agents ran at about 21,000 calls/s on one core, with 40 µs median latency (108 µs at p99), 72 KB per agent and 12 s for the weekly peer computation.

## Limits

- The traffic is synthetic. Strange usage was designed by us, so a dimension matching our design looks good by construction. Read the results as relative rankings and failure modes, not production rates.
- Caller identity, roles and teams come from the generator. A real gateway needs identity on the wire.
- No peer-reviewed evaluation of misuse (not attacks) by legitimate agents on MCP was found. Errico et al. 2025 (arXiv:2511.20920) recommends per-role baselines and rate limits but reports no evaluation.

## Combining the dimensions into one score (2026-10-18, FORMULA.md)

Same five high-level dimensions (next tool, repeat in 10 min, new /16, new client family, calls today), 9 organisations, mean over 21 kinds:

| Combination | ≤ 2 / day | ≤ 4 / day |
|---|---|---|
| Strongest calibrated signal, one threshold set by load | 48% | 57% |
| Earlier rule (sum, ≥ 2 agree or one extreme), (T, B) tuned with labels | 43% | 56% |
| Earlier rule, (T, B) from the other eight organisations | 41% | 53% |
| Sum of three groups | 35% | 53% |
| Product of three groups (1+s)^3, calibrated | 33% | 52% |
| Product, raw bits, no calibration (formula_test.py, hard daily cap) | 26% | 36% |

With a hard daily cap instead of average load, strongest-signal gives 41% / 52% (still best). Four dimensions (no calls today) give 48% / 56%. Adding writes today gives 49% / 57%. Recommended: four dimensions, strongest signal, R_dynamic = R_static × (1 + min(1, log10 N / 6)) for display.

## Three families and the e formula (2026-10-18, FORMULA.md, family_formula.py)

Families: Pace (same tool in 10 min [+ calls today]), Path (next-tool rarity), Place (new /16, new client family). Each family keeps its strongest dimension. Four dimensions, 9 organisations, mean over 21 kinds, ≤ 2 / ≤ 4 flagged agent-days per day (average load):

| Signal per dimension | Add | Largest | (1+s)^3 |
|---|---|---|---|
| Excess surprise over the month's 99.5th percentile, max(0, u − B) | 50 / 58 | 50 / 57 | 50 / 58 |
| Deck form, max(0, B − L) with support share L = 2^-u | 42 / 51 | 41 / 50 | 42 / 51 |
| CARMA σ(u), no organisation comparison | 43 / 53 | 35 / 57 | 42 / 51 |
| Rank "1 in N" against the month | 35 / 54 | 49 / 57 | 32 / 54 |

With the excess over normal, the join no longer matters: on about 95% of agent-days at most one family is above normal (12–18% of strange agent-days have two). Families alone: Path 25/29, Pace 20/22, Place 16/16. Hard daily cap: 40/53. Full 11-dimension set: 51/62. Recommended: R = R_static × e^(λ ΣX), λ = ln 2 / 10, capped at ×8.

## Scenarios and two new ideas (2026-10-18, SCENARIOS.md, dynamic_engine.py, scenarios.py, idea_eval.py)

- 15 scenarios were run through a reference engine on a simulated 50-agent GitHub organisation over 90 days. The budget is 2 a day, with a floor of 4 bits.
- **The base formula catches the single-agent cases on the day:**
  - off-role ×2.4, shared credential ×2.0, loop ×1.4;
  - a new hire's day-1 off-role step is caught only with team fill-in.
- **It breaks on:**
  - organisation-wide changes: a client rollout gives 38 alerts, a server slowdown 40;
  - a legitimate role change, which alerts on 7 of 15 working days.
- **Idea A, crowd:** a strong thing shared by 5 or more agents becomes one organisation notice. Rollout: 2 alerts + 1 notice a day. Slowdown: 0 alerts + 2 notices.
- **Idea B, settling:** a step made on 3 or more of the last 7 days counts 0. Role change: 5 of 15 days. Slow creep is unchanged.
- **9 organisations:** base 50/58; crowd, settling and both 50/58; persistence 41/52, so it was dropped. The floor gives 49/52 at 1.8 and 2.3 alerts a day.

## Self-only dimensions, no user id, no comparison with other users (2026-10-19, self_only_dims.py, self_only_eval.py)

**Constraints:**
- no tool-type-specific dimensions (no writes today);
- no user id: the identity is the agent, a shared token, or the session;
- no comparison with other users: no team fill-in, no org-rare, no peers.

There are 8 self-only dimensions. The table shows greedy detection on 9 organisations at ≤ 4 a day:

| Calibration | 1 | 2 | 3 | 4 | 5 | 6 | 8 |
|---|---|---|---|---|---|---|---|
| Pooled (organisation sets the alert scale) | 21 next tool | 37 + repeat 10 min | 48 + new network | 51 + new client | 53 + calls today | 56 + new tool | 57 |
| Self (each agent vs its own month only) | 20 next tool | 32 + repeat 10 min | 39 + new client | 41 + new tool | 42 + new network | 44 + calls today | 47 |

**Identity**, on github_M, slack_M and calendar_M with pooled calibration at ≤ 4:

| Identity | 3 dimensions | 4 dimensions |
|---|---|---|
| Per agent | 51 | 55 |
| Shared by 10 | 57 | 59 |
| Session only | 12 | 12 |

The shared-by-10 numbers look higher only because one alert covers 10 people's day, and the person behind it is lost. Session only collapses to 0% under self calibration.

## Velocity / Knowledge / Place baseline (2026-10-19, vkp_extra_dims.py, vkp_eval.py, vkp_greedy.py, vkp_engine.py, vkp_scenarios.py)

The user's proposal has 3 families and 16 high-level dimensions, plus distinct assets a day (which needs inputs). Results on 9 organisations, at ≤ 2 / ≤ 4 flagged agent-days a day:

- **All 16, maximum inside each family:** 50 / 62.
- **Greedy order:**
  - tool rarity for this agent: 24 / 29;
  - \+ repeat in 10 min, + new (network /16, client family) pair: 51 / 58;
  - \+ calls in the last hour, + session duration: 52 / 61;
  - best of all: 53 / 62.5.
- **Unique value (drop-one):**
  - Exact IP hurts: −3.1 / −0.7. Use /16.
  - Next tool, org-rare new tool, network new, client new, asset types today and calls today each add ≤ 0.3. They are redundant with tool rarity and the new pair.
- **Inside a family**, detection by method:

  | Method | ≤ 2 a day | ≤ 4 a day |
  |---|---|---|
  | Average | 52.9 | 61.5 |
  | Average of e | 52.7 | 61.5 |
  | Max | 50.0 | 61.2 |
  | Sum | 51.4 | 60.3 |

  Average works, but it shrinks the multiplier shown.
- **Scenarios (self-only engine, no team fill-in, no crowd, no settling):**
  - Caught on the day: loop, off-role, shared credential, creep, nagging loop, long session (session duration), org-rare tool.
  - Missed:
    - busy day spread out (rank 4);
    - new hire off-role on day 1 (no own history);
    - over-fetch (invisible).
  - False alarms:
    - role change on 9–11 days;
    - org-wide rollout and server slowdown fill the whole daily budget.

## Coverage of the 6-dimension set and candidate additions (2026-10-19, vkp_coverage.py)

The base set has 6 dimensions:
- Velocity: repeat in 10 min, calls today, session duration.
- Knowledge: tool rarity for this agent, asset types today.
- Place: new network + client pair.

It uses the average inside each family and catches 52.7% / 60.5% at ≤ 2 / ≤ 4. Kinds at ≥ 55% (≤ 4): 15 of 21.

| Candidate | Overall | Benign days | Notable change |
|---|---|---|---|
| \+ call without initialize | 56.4 / 63.8 | 0.0% | protocol skip 29 → 99 |
| \+ request size vs own usual for this tool | 54.9 / 65.4 | 18.5% | content dump 23 → 90, recipient blast 73 → 89, fan-out 41 → 52 |
| \+ hour of week | 52.3 / 60.4 | 22.7% | off-hours 6 → 23, but loops and page walks drop |
| \+ list-to-call delay | 53.2 / 61.1 | 32.6% | — |
| \+ call without list | 53.3 / 61.9 | 13.2% | — |
| \+ dormancy | 52.2 / 60.0 | 0.7% | — |

**8 dimensions (base + initialize + size): 58.6 / 68.7.** Adding hour of week as a 9th gives 59.0 / 69.0.

Still weak with 8: over-fetch 12, sensitive asset 7, off-hours 5.

## User's Timing / Footprint / Request design with policy limits, GitHub only (2026-10-19, policy_github.py)

**Setup:**
- 3 GitHub organisations; learned dimensions use only the agent's own past (own 99.5th percentile as the normal level).
- A policy breach counts as 10 bits; families use the average inside, added in the exponent.
- New asset = own novelty × sensitivity / 5, with an unregistered asset counted as 5 (the worst). New tool = own novelty × impact / 5.

**Results** at ≤ 2 / ≤ 4 a day:

| Design | Average inside | Max inside |
|---|---|---|
| The user's design as given | 53.3 / 56.2 | 14.8 / 14.8 (noisy limits tie at 10 bits) |
| Fixed, 4 families | **58.9 / 68.6** | 48.5 / 68.3 |
| Fixed, 4 families + learned request size | 59.1 / 70.6 | — |

The fixed design has four families:
- Timing: calls per hour, repeat in 10 min, clean sequences.
- Footprint: new tool, new asset.
- Origin: new exact IP, new client family.
- Request: size over 10 KB, call without initialize.

**Ordinary agent-days each check fires on:**

| Check | Ordinary days |
|---|---|
| Burst over 10 a minute | 9.7% (bots) |
| Session over 4 h | 0% (never fires) |
| Write to a sensitive asset not read first | 15.1% |
| Merge without review | 1.8% |
| Sensitive read then write elsewhere | 0% |
| New exact IP | 0.6% |
| Request over 10 KB | 0% |
| New tool | 1.6% |
| New asset | 1.7% |
| New client | 0% |
| Call without initialize | 0% |

**Lessons:**
- **Averaging dilutes.** A breach in a 4-dimension family counts half; splitting Request into Origin + Request restored new origin at ≤ 2 (37 → 100).
- **Noisy limits ruin the max formula**, and adding the burst limit cost 8 points.
- **"Worst for unregistered" makes no measurable difference** in the simulation (53.6 vs 53.3).
- **New asset lifts sensitivity escalation to 79% and fan-out to 88%**, against 4–7% and 41–51% without the asset.

## Footprint as shares, every policy kept and recalibrated, GitHub (2026-10-19, footprint_policy_github.py)

**Footprint shares:**
- Tool share: own calls of the tool ÷ own calls (90 days), × impact / 5.
- Asset share: own calls on the asset ÷ own asset calls, × sensitivity / 5, with unregistered = 5.

**Recalibrated limits**, set from ordinary traffic:

| Limit | Old → new | Ordinary days, old → new |
|---|---|---|
| Burst | 10 → 20 a minute | 9.7% → 0.1% |
| Session | 4 h → 10 min | never → 0.0%; now catches cancel storms at 34% |
| Blind sensitive write | in-session → not read in 7 days | 15.1% → 2.3% |

All timing limits together: 24.1% → 4.0%. Each family carries one policy check (any limit broken = 10 bits).

**Results** at ≤ 2 / ≤ 4 a day:

| Design | ≤ 2 | ≤ 4 |
|---|---|---|
| A. Previous best (limits dropped) | 59.0 | 68.8 |
| B. A with shares | 55.2 | 68.2 |
| C. Shares + all limits, old values | 51.2 | 57.6 |
| D. Shares + all limits, recalibrated | 56.9 | 67.6 |
| **E. D + new tool and new asset alongside the shares** | **58.2** | **69.1** |

**Ordinary days and what the footprint checks catch:**

| Check | Ordinary days | Catches |
|---|---|---|
| Tool share | 24.7% | off-role 99%, mode switch 91% |
| Asset share | 8.7% | fan-out 94%, sensitivity escalation 80% |
| New tool | 1.6% | — |
| New asset | 1.7% | — |

The shares are broader but noisier; "new" is the clean extreme.

## One simple formula per dimension, levels 0–5, GitHub (2026-10-19, levels_github.py)

There is no combined exponent: each dimension gives its own level.
- Rules (first-time tool/asset at the static level; first IP/client, burst, request, sequence, protocol skip: 4; session: 3) give a fixed level.
- The other dimensions are compared with the agent himself.

**Results** at ≤ 2 / ≤ 4 a day:

| How the self-relative level is set | Day = highest level | Day = sum of levels |
|---|---|---|
| Rarity per call (1 in 10 / 30 / 100 / 300 / 1000) | 41.8 / 65.9 | 52.5 / 67.9 |
| **Excess over his own normal (every 2 bits = 1 level)** | **55.1 / 69.3** | 54.0 / 65.6 |

The best (excess, day = highest) is close to the family-formula E (58.2 / 69.1).

**Per-call rarity is too noisy:** "1 in 100 for him" happens daily for busy agents. With it, off-hours reaches level ≥ 3 on 34% of ordinary days, against 0.1% with excess.

**Off-hours as a share of his calls in 48 slots** (hour × weekday/weekend) catches the off-hours kind at 74%, against 2–9% before.

## No bits: fractions and averages, bounded multiplier (2026-10-19, levels_fraction_github.py, bounded_examples.py, DIMENSION_FORMULAS.md)

**Levels from fractions and averages, 3 GitHub organisations**, ≤ 2 / ≤ 4 a day:
- Share thresholds 2/1/0.5/0.2/0.1% and ratio thresholds 2/3/5/10/20: 48 / 75.
- Same, with time of day counted ±1 hour (set D): **58 / 74**.
- For comparison, the bits version: 55 / 69.
- An exact-hour time share is noisy (level ≥ 3 on 23% of ordinary days); ±1 hour brings it to 0.9%.

**Final formula (worked scenarios only, not a full test):**
- s = value / (value + his average), or s = 1 / (1 + K × share), with share = (n + 1) / (N + K).
- S = the largest s.
- M = 5^(2S − 1) above normal, 0.8^(1 − 2S) below.
- R = static × M, between 0.8 and 25 with no clipping.
- Ordinary ×1.2, loop ×4.4, never-used tool ×4.9, rule (s = 0.9) ×3.6, new agent's new tool ×1.7.

**Update (same day, user ranges):**
- The multiplier is now 0.7–5, so the risk is 0.7–25.
- Tolerance 2: s = v / (v + 2·avg), and s = 1 / (1 + 2·K·share). Up to twice his usual is ordinary (M = 1).
- K = different values he has used + 1.
- Warm-up: 5 calls (M = 1 before that).
- Worked results: ordinary ×0.92, familiar ×0.85, loop ×3.9, never-used tool ×4.9, 3 am ×4.95, rule ×3.6. A new user's new tool gives ×1.3 at 5 calls and ×2.8 at 50.

## Stress test of the bounded formula (2026-10-19, bounded_stress.py; results/bounded_stress*.json)

**User changes:** removed "same tool in 10 min"; replaced the fixed session rule with learned session length; first-time tool ≈ ×3.2–3.6 (ceiling 0.9); network /16; protocol skip 0.7 (×1.9).

**Breaks found and fixed:**
- 0 bytes caused a division by zero; fixed with units of 1 call / 1 minute / 1 KB.
- The fixed session rule fired all day on desktop clients.
- Exact IP fired on mobile and NAT.
- Stateless clients looked like protocol skip; it now fires only for agents who normally initialize.
- Plain shares let rare-but-normal things flare daily; replaced by "times per day" (e = (rare calls + 1) / (active days + 1)).
- Onboarding first uses are excluded.
- Weekend calls are compared with weekend days.

**Results on 9 organisations:**
- M stays within 0.79–4.78, with no NaN.
- Ordinary agent-days at ≥ 3: 6–16% → 3–10%.
- Daily list at ≤ 4 a day: 57% → 65%.
- Remaining ordinary causes: asset tail (Calendar/Slack) and the GitHub sequence rule.

**Still weak:**
- ties at ×3.62 at ≤ 2 a day;
- legit pagination (burst);
- slow loops (×2.2);
- 5× bot surge (×1.95);
- night work 54% and new network 35% of legit days.

## Production behaviour engine with a learned policy (2026-10-19, behaviour_policy_sim.py)

**Setup:**
- `src/mcp_security/behaviour` run on 9 organisations, ties not broken (included at the cut-off).
- The policy is learned from each organisation's first 30 days: burst 15–20 a minute, request 1 KB, no required steps found.

**Results**, default → learned policy:

| Measure | Default | Learned |
|---|---|---|
| Ordinary agent-days at ≥ 3, mean | 3.9% | 4.2% |
| Review list, ≤ 2 a day | 48% | 50% |
| Review list, ≤ 4 a day | 68% | 70% |

**Changes by kind:** content dump 49 → 100%, loop 52 → 65%, recipient blast 45 → 65%.
