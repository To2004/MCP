# Dynamic layer: three questions and one formula

> **Superseded on 2026-10-19:** the current design gives each dimension its own formula and level 0–5 instead of one combined formula. See [DIMENSION_FORMULAS.md](DIMENSION_FORMULAS.md).

The dynamic layer asks three simple questions about every call and turns the answers into one multiplier on the static score. It never looks inside a call: it uses only the tool, the time, the volume and a general client and network. This page is the short version for reviewers and clients. Every number comes from the 9 simulated organisations (GitHub, Calendar, Slack; 21 kinds of strange usage), measured after the first month. [SCENARIOS.md](SCENARIOS.md) runs it on 15 concrete scenarios and adds two ideas for organisation-wide and legitimate changes.

## The three questions

| Family | The question | Dimensions | Catches | Close to |
|---|---|---|---|---|
| **Pace** | Is it doing this more or faster than usual? | Same tool repeated within 10 minutes (optional: calls today) | Loops, page walks, bursts, storms | Deviation |
| **Path** | Is it doing something it does not usually do? | Unusual next step: this tool right after the previous one | Off-role tools, skipped workflow steps, slow scope creep | Access anomaly, at tool level |
| **Place** | Is it coming from somewhere new? | New network range (/16); new client family (name without version) | New origin, shared credential, client switch | Novelty |

Every question compares the agent with its **own** last 90 days. The families see different things, so they work best together:

| Family | Catches alone (≤ 2 / ≤ 4 per day) |
|---|---|
| Path | 25% / 29% |
| Pace | 20% / 22% |
| Place | 16% / 16% |
| **All three** | **50% / 58%** |

## The formula

```
R_dynamic = R_static × e^( λ · (X_pace + X_path + X_place) )        at most ×8
```

**1. Surprise.** For each dimension, `u = −log2(p)`, where `p` is how often this agent did this in its last 90 days.

- The unit is bits: 10 bits means about 1 in 1,000.
- While an agent is new, its team's habit fills in, worth 20 calls.

**2. Normal level.** `B` is the surprise reached by only 0.5% of the organisation's calls in the last 30 days, set separately for each dimension.

- It is learned from the organisation's own month, so nobody sets it by hand.
- A new network or new client is already rarer than that, so their `B` is 0 and every new one counts in full.

**3. Excess.** `x = max(0, u − B)`.

- Only the part above normal counts.
- It is never negative, so familiar behaviour never lowers the risk.

**4. One value per family.** `X` is the largest `x` among the family's dimensions. A new network that also brings a new client counts once.

**5. Multiply.** `e^(λ · ΣX)` with `λ = ln 2 / 10`.

- Every 10 bits above normal (about 1,000 times rarer than the usual "unusual") doubles the risk.
- The multiplier is capped at ×8.

**Daily check.** An agent's day score is the sum of each family's largest `X` that day. Flag the agent-days above a threshold chosen so the flagged count matches what the team can review, for example 2 or 4 a day per organisation.

**Example (illustrative numbers).** A release agent calls `create_release` right after `search_code`. It has never made that step in 90 days, so `u` is 16 bits; this dimension's normal level is 4 bits.

1. Path: X = 16 − 4 = **12**. Pace and Place are normal, so both are 0.
2. The multiplier is e^(0.069 × 12) = **×2.3**. With a static score of 4, the call shows **9.2**.
3. If the same call also came from a new network and a new client, Place = max(11, 11) = **11**, counted once.
4. The multiplier is then e^(0.069 × 23) = **×4.9**, so the call shows **19.7**.

## Where it comes from

| Source | What we kept | What we changed, and why |
|---|---|---|
| Methodology deck, `e^(λ(B − L))` | The `e` form; a baseline `B` per feature | `L`, the support share, became surprise. A share puts every rare value near 0, so 1 in 100 and 1 in 100,000 look the same. Surprise keeps them apart. `B` is learned instead of set. The term is clamped at 0, so there is no discount. Fixed windows replace growing history, which fixes the aging problem. |
| CARMA, `R_static × D × A × N` | Three families; the strongest signal inside each; multiply across; never below static; the team fills in for new agents | The families are redefined for the high level (no assets or inputs). The `σ` cap is replaced by excess over the normal level. |
| Hyndman & Frazier 2026 | Surprise (−log p) as the measure of strangeness. A value counts when it is in the tail of everyone's surprises. | Our `B` is that tail point, the month's top 0.5%. |
| Kriegel et al. 2011 | Put different detectors on one scale before combining them | One scale: bits above each dimension's own normal level |
| Heard & Rubin-Delanchy 2018 | Adding surprises (= multiplying e-terms) is Fisher's method; taking the largest is Tippett's | Subtracting the normal level gives the benefits of both (see below) |
| Splunk RBA, Exabeam | Add risk per entity over 24 hours; alert above a threshold | The same daily check |
| Microsoft Sentinel UEBA, Elastic ML | Score deviation from the entity's own history; normalise scores against history | The same baseline idea |

## Why this form

We tested every way of turning surprise into a signal and every way of joining the three families. Same four dimensions, 9 organisations, mean over 21 kinds:

| Signal | Join | ≤ 2 / day | ≤ 4 / day |
|---|---|---|---|
| **Excess over normal (this page)** | **Add (= multiply e-terms)** | **50%** | **58%** |
| Excess over normal | Largest only | 50% | 57% |
| Excess over normal | (1+s)(1+s)(1+s) | 50% | 58% |
| Deck form, `e^(B − L)` with support share | Add | 42% | 51% |
| CARMA `σ`, no comparison with the organisation | (1+s)(1+s)(1+s) | 42% | 51% |
| "1 in N" against the month | Add | 35% | 54% |
| "1 in N" against the month | Largest only | 49% | 57% |
| Earlier two-threshold rule, thresholds from other organisations | — | 41% | 53% |

**Subtracting the normal level is what makes adding safe.**

- Without it, every small oddity adds up, and ordinary days with two mild signals outrank a day with one truly rare thing.
- With it, a just-above-normal value adds almost 0.
- On 95% of ordinary agent-days at most one family is above normal, so adding behaves like "take the largest".
- When two families really are high, adding still ranks that day higher. Two families are above normal on 12–18% of strange agent-days but only 4–5% of ordinary ones.

**λ and the cap do not change who is flagged, only the number shown.** The ranking depends only on the sum. With `λ = ln 2 / 10`, a strong single signal shows about ×2–×3 and the maximum is ×8, matching CARMA's range.

With a hard cap of exactly N agent-days on every day, instead of N on average, the result is 40% / 53%. Adding *calls today* to Pace gives 51% / 58%. The full 11-dimension high-level set gives 51% / 62%. At ≤ 4 per day each organisation lands between 45% and 63%.

**By kind, at ≤ 4 per day:**

| Detection | Kinds |
|---|---|
| Very high | New origin 100%, off-role tool 99%, shared credential 97%, page walk 92%, client switch 89%, slow creep 89% |
| Good | Repeated habit 76%, recipient blast 72%, workflow skip 65%, mode switch 64%, dormant wake 63%, loop 62%, long span 58% |
| Fair | Burst 55%, cancel storm 51% |
| Not visible at this level | Content dump 24%, protocol skip 23%, fan-out 18%, over-fetch 7%, off-hours 6%, sensitive asset 3% |

## What you need

**From each logged call.** gateway-log/2 already has every field except identity.

| Field | Used for | Status |
|---|---|---|
| Timestamp | Pace, the daily check | Have (`ts`) |
| Tool name | Pace, Path | Have (`gen_ai.tool.name`) |
| Session id | Path (what came before) | Have (`mcp.session.id`) |
| Client address, cut to /16 | Place | Have (`client.address`) |
| Client name, version dropped | Place | Have (`gateway.client`) |
| **User + agent app** | Whose history to compare with | **Add**: OAuth `sub` (hashed) and `client_id` from the bearer token |

**From the static scan.** The static score per tool (`R_static`).

**State per user + agent app.** About 70 KB each, sharded by agent:

- tool-to-tool counts for 90 days;
- the network ranges and client families seen, each with a last-seen day;
- the last 10 minutes of calls, and a short history of its 10-minute repeat counts.

**State per organisation.** For each dimension, the normal level `B`: the 99.5th percentile of the last 30 days' surprise values. A quantile sketch is enough.

**Parameters.**

| Parameter | Value |
|---|---|
| History | 90 days |
| Repeat window | 10 minutes |
| Team fill-in | Worth 20 calls |
| Normal level `B` | 99.5th percentile over the last 30 days |
| `λ` | ln 2 / 10 (doubles every 10 bits) |
| Cap | ×8 |
| Daily threshold | Set to the review budget |

**From the policy (optional).**

- **Working hours.** Without them off-hours use is not visible (6%).
- **Planned changes.** Network moves, client rollouts and role changes create expected "new" signals, so mute those agents for the change window.

## Keep in mind

- **Identity decides everything.** With one token per person, detection is 75%. One token shared by 10 people gives 71%, and you can no longer tell who did it. Session id only gives 12%.
- **The first month is calibration.** `B` needs 30 days of the organisation's traffic. New agents lean on their team until they have their own history.
- **Legitimate change causes most false alarms.** A role change makes the Path question fire for about a month. New hires, client upgrades and network moves set off Place. Planned-change windows from the policy remove most of this.
- **Dynamic says "strange", static says "how much it matters".** The daily check decides which agent-days to flag, and `R_static` decides which of them to look at first.
- **What this level cannot see.** Normal-looking work on a sensitive asset, over-fetching, content dumps and mild fan-out. These need an asset-name hash or the request size in the log (see [HIGH_LEVEL.md](HIGH_LEVEL.md)).
- **The traffic is synthetic.** The ranking held across 9 different organisations, but these are not production rates. The Place dimensions have not been checked on real multi-agent traffic.

## References

- Hyndman, R. J. and Frazier, D. T. (2026). *Anomaly detection using surprisals.* [arXiv:2603.09318](https://arxiv.org/abs/2603.09318)
- Kriegel, H.-P., Kröger, P., Schubert, E. and Zimek, A. (2011). *Interpreting and unifying outlier scores.* SIAM SDM. [preprint](https://www.dbs.ifi.lmu.de/~zimek/publications/SDM2011/SDM11-outlier-preprint.pdf)
- Heard, N. A. and Rubin-Delanchy, P. (2018). *Choosing between methods of combining p-values.* Biometrika 105(1). [arXiv:1707.06897](https://arxiv.org/abs/1707.06897)
- Splunk Enterprise Security, [risk-based alerting](https://help.splunk.com/en/splunk-enterprise-security-7/risk-based-alerting/7.2/introduction/how-risk-based-alerting-works-in-splunk-enterprise-security)
- Exabeam Advanced Analytics, [session risk score and the notable threshold](https://docs.exabeam.com/en/advanced-analytics/i56/advanced-analytics-user-guide/113570-entity-analytics.html)
- Microsoft Sentinel, [UEBA](https://learn.microsoft.com/azure/sentinel/identify-threats-with-entity-behavior-analytics)
- Elastic, [anomaly scoring](https://www.elastic.co/blog/changes-to-elastic-machine-learning-anomaly-scoring-in-6-5)
- Code: `family_formula.py` (this page's tables, results in `results/family_formula.json`), `formula_compare.py` (the earlier "1 in N" comparison).
- Scenarios and two further ideas (crowd, settling), run by a reference engine: [SCENARIOS.md](SCENARIOS.md).
