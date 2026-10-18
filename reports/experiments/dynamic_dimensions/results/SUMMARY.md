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
