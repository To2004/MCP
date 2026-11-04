# Static and dynamic risk scores: formulas and dimensions

This report puts the framework's two scores side by side. For each one it gives the dimensions,
the formula, where every number comes from, and how the two combine. The MCP server is the
protected asset and the calling agent is the threat: every call is scored before it reaches the
server.

- **Status (2026-10-28).** The static score is written as in the paper draft. The gateway runs
  an earlier combination of the same factors (§2.5). The dynamic score is the design the author
  chose on 2026-10-28; it has been checked in a prototype but is not yet in the engine.
- **What it replaces.** It supersedes the dimension list in
  [behaviour-multiplier-formula.md](behaviour-multiplier-formula.md), which had 8 different
  dimensions; that note's derivation, guarantee and judges' review still apply.

## 1. The whole score

```text
R = Risk_static × M

Risk_static = 0.3·ToolImpact + 0.3·AssetSensitivity + 0.3·BlastRadius + 0.1·ParameterRisk
                                         ∈ [0.9, 5]     how dangerous the call can be
M           = ((A + 1)/(2D + 1))^γ      ∈ [0.78, 5]    how unusual the call is for this agent
R                                        ∈ [0.7, 25]
```

The static score follows the paper's §"Static Risk Assessment" (draft of 2026-10-28). It has four
factors, each on a 1-5 scale, combined by a weighted sum. ParameterRisk is the highest level among
the call's risk-relevant inputs, or 0 when the tool has none.

The two scores answer different questions and never share an input:
- **The static score asks:** "how much damage can this tool, on this asset, with these parameter
  values, do?" Its factors and mappings are fixed at design time from the tool catalog and the
  organisation's policy.
- **The dynamic score asks:** "is this agent behaving unlike itself?" It is learned at run time
  from the agent's own past days.

Sensitivity, impact, reach and parameter values live only in the static score. Habit lives only in
the dynamic score.

## 2. The static score

### 2.1 Four factors, each from 1 to 5

These are the paper's tables (Tables "Tool impact levels" to "Parameter-dependent risk levels").

| Factor | Defined for | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| **ToolImpact(t)** | each tool | no material effect | metadata | content access, or a limited change | major change, normally reversible | irreversible or consequential |
| **AssetSensitivity(a)** | each asset | public, negligible impact | routine internal | moderate impact | restricted, high impact | critical (credentials, regulated data, crown jewels) |
| **BlastRadius(t, a)** | each tool and asset pair | single object | bounded subset | broad subset | complete asset | systemic, fans out beyond one asset |
| **ParameterRisk(t, input)** | each risk-relevant input of a tool | minimal (e.g. a $100 transfer) | low ($500) | moderate ($2,000) | high ($10,000) | critical ($50,000) |

- **Where the factors come from:** ToolImpact comes from fixed rules for obvious names (such as
  `delete_file`), and from an LLM reading the tool description otherwise. AssetSensitivity comes
  from the organisation's own labels mapped onto the scale, or from an LLM when there are none.
  BlastRadius comes from an LLM; a pair the tool cannot reach is marked N/A.
- **Thresholds:** the ParameterRisk thresholds come from organisational policy where it exists,
  and from an LLM otherwise.

### 2.2 The formula

```text
ParameterRisk(t) = max over risk-relevant inputs k of ParameterRisk(t, input_k)      (0 if none)
Risk_static(t, a) = 0.3·ToolImpact(t) + 0.3·AssetSensitivity(a) + 0.3·BlastRadius(t, a)
                  + 0.1·ParameterRisk(t)
```

- **Maximum, not average:** one high-risk parameter must not be diluted by several harmless ones.
- **Equal weights** for the three main factors, and a smaller weight for parameters.

| Example | ToolImpact | AssetSensitivity | BlastRadius | ParameterRisk | Risk_static |
|---|---|---|---|---|---|
| Ping | 1 | 1 | 1 | 0 | 0.9 |
| Read one message in a routine channel | 3 | 2 | 1 | 0 | 1.8 |
| Write one file in an internal folder (path rated 3) | 4 | 3 | 1 | 3 | 2.7 |
| Delete one event in the CEO's calendar | 5 | 4 | 1 | 0 | 3.0 |
| `send_money` $100 / $50,000 | 5 | 5 | 1 | 1 / 5 | 3.4 / 3.8 |
| Drop the salaries table (query rated 5) | 5 | 4 | 4 | 5 | 4.4 |

### 2.3 Which asset a call is priced on

At run time the call's asset is resolved by the binding layer, which is deterministic and runs no
model on the call path:
1. **One candidate asset for the tool:** that asset.
2. **Several candidates:** the tool's target inputs (for example a repository's owner and name)
   are matched against the policy's asset register.
3. **No match, or the tool names no target:** the **worst** candidate. Not knowing costs
   precision, never safety.

So an asset that is not in the policy gets the riskiest score the tool can have.

### 2.4 How parameter levels are found

- **At design time,** an LLM writes one rule per risk-relevant input (the repo's v13 step). The
  rule turns the input's value into a level from 1 to 5, and an input that cannot reach all five
  levels gets none. See the [v13 README](../../v13/README.md) and
  [tool-input-levels.md](../../../../docs/standards/tool-input-levels.md).
- **At run time** each rule is a table lookup, a threshold or a substring test
  (`src/mcp_security/input_rules/rules.py`). No model runs.

| Kind of input | Rule | Where the levels come from |
|---|---|---|
| Amounts, counts, lengths, time windows | ranges | the policy's thresholds where it gives them; otherwise the LLM |
| A name of a listed asset | register lookup | the asset's level from the policy register |
| An email address | fixed ladder | the policy: own domain 1, partner 2, unreadable 3, other organisation 4, personal mailbox or flagged domain 5 |
| Text: paths, queries, bodies, commands | keyword groups | credential words (`.env`, `token`, `id_rsa`, …) are always 5; the rest from the LLM, following the policy |
| A choice among 5 or more options | values | the LLM |

The v13 experiment folder holds development measurements of these rules. They are not paper results.

### 2.5 The code and the paper differ (to align before experiments)

| Point | Paper | Code today (`gateway/framework.py`) |
|---|---|---|
| How the factors combine | weighted sum, 0.3 / 0.3 / 0.3 / 0.1 | cube root of ToolImpact × AssetSensitivity × BlastRadius (`static_level`) |
| ParameterRisk | the fourth factor (weight 0.1) | computed and logged as `input_level`, but not used in the score |
| ToolImpact 4 and 5 | 4 = major change, normally reversible; 5 = irreversible or consequential | the scanner prompt has 4 = full modification (write, update) and 5 = destructive or executing (delete, run code) |

### 2.6 Notes on the static formula for the paper

1. **The parameter weight is small for the paper's own example.** With w_P = 0.1, the $100 and
   $50,000 transfers score 3.4 and 3.8 out of 5. The text says the second may cause "substantially
   greater financial loss", so a reviewer may ask why the score moves by only 0.4.
2. **"0 when there is no risky parameter" ranks below "minimal".** A tool with no risk-relevant
   parameter scores 0.1-0.5 lower than the same tool whose parameter is at level 1-5, and its
   maximum is 4.5, not 5. Making "none" neutral fixes this: divide the other three weights by 0.9
   when there is no parameter.
3. **ParameterRisk depends on the call, not only on the tool.** The equation writes
   ParameterRisk(t_i), but its value comes from the call's arguments. The last paragraph says so;
   the equation should show it, as ParameterRisk(t_i, x) for the call's values x. The asset index
   (t_i, a_j, input_k) is also dropped between the definition and the max.
4. **BlastRadius at run time.** The last paragraph maps "the actual call scope" to a blast-radius
   level at run time. In the scanner, BlastRadius is fixed per tool and asset, and scope that
   depends on the call (record counts, recipients) enters through ParameterRisk. One sentence
   would align them.
5. **The letter A means two things.** w_A is the asset-sensitivity weight here, while A in the
   dynamic formula is the agent's active days. Renaming one avoids the clash.
6. **A sum of ordinal levels.** Adding 1-5 levels treats them as equally spaced. Reviewers raise
   this for risk matrices (Cox 2008), so report how sensitive the results are to the weights.

## 3. The dynamic score (behaviour multiplier M)

> **Superseded on 2026-10-29** by [dynamic-score-report.md](dynamic-score-report.md): six dimensions,
> counting calls. This section is kept as the record of the 2026-10-28 design.

### 3.1 Whose history

- **The key is the agent id only.** There is no user id, no sign-in and no network address, and
  one id may stand for a whole organisation.
- **Assumption:** the operator issues the id and a client cannot choose it.
- **The history is the agent's last H = 90 active days.** Days without calls do not count, so a
  break changes nothing.

### 3.2 Eight dimensions

| Group | Dimension | What it measures | More unusual means | Compared with |
|---|---|---|---|---|
| How much | **Call rate** | calls in the last hour | a higher doubling | the agent's past days |
| | **Tool rate** | calls of this tool in the last hour | a higher doubling | the days the agent used this tool |
| | **Breadth** | different resources in the last hour | a higher doubling | the agent's past days |
| | **Read volume** | bytes returned in the last hour, before this call | a higher doubling | the agent's past days |
| | **Request size** | argument bytes of this call | a higher doubling | the days the agent used this tool |
| What | **Resource** | the container the call works on | used on fewer past days | the agent's past days |
| | **Action** | this tool on this resource | used less often on it | the days the agent touched this resource; with no resource, all days |
| When | **Hour** | the hour of the call | active then on fewer past days | the agent's past days |

**Resources come from the same binding layer as the static score:**
- **In the policy:** the static score knows its sensitivity, and the dynamic score tracks it by
  its policy name.
- **Not in the policy:** the static score gives it the worst case. The dynamic score tracks a
  keyed name inferred from the arguments.
- **No container named:** only the tool-level dimensions apply.

**Amounts are compared in doublings** (1, 2-3, 4-7, 8-15, …). A 10% busier hour is not a record;
twice the usual is.

**Read volume** counts replies that have already arrived. A large download is therefore seen on
the agent's next call, not on the call that pulled it.

**Removed, with reasons:**

| Removed | Why |
|---|---|
| The Red Flags (burst, sweep, oversized request, unsafe sequence, missing handshake) and the behaviour policy file | They needed hand-written limits or rules. Their useful ideas returned as learned dimensions (Tool rate, Request size, Action). |
| Step, Area | They were tied to files, so they over-fitted one kind of server. |
| Repetition | Tool rate catches loops. |
| Network, Client, Session duration | There is no address and no client name, and an organisation-wide id never idles. |
| Floors, budget shares, surge guard, comparison with other agents | One formula replaces them. Sensitivity stays in the static score. |

### 3.3 The formula

```text
1. Each dimension d:   f_d = (n_d + ½) / (A_d + 1)
                       n_d = past days at least as unusual on d,   A_d = past days on which d applied
2. The whole call:     sort the f_d, most unusual first.
                       D = past days whose sorted list is at least as unusual
                       (compare the most unusual entry first, then the next)
3. M = ((A + 1) / (2D + 1))^γ,    γ = ln 5 / ln(H + 1) ≈ 0.357,    A = past active days (≤ 90)
```

The whole call is ranked against the agent's own past days in step 2. This is needed because, with
eight dimensions, every ordinary day looks rare on at least one of them. Without the rank, a typical
call would score about ×1.9 instead of ×1.

### 3.4 Why this form

| Number | Where it comes from |
|---|---|
| ½ in f | It makes "seen on half the agent's days" give exactly ×1, for any history length (the mid-p correction). It also gives a new agent ×1. |
| The power form | It is the only form in which each halving of how often something happens raises M by the same step: ×1.28 at H = 90. |
| 5 at the top | It gives behaviour the same span as the static score's 1-5 scale (a factor of 5), so neither layer outweighs the other. Ranking calls by M alone does not depend on it. |
| γ | It makes "never in a full 90-day window" land exactly on ×5. |
| 0.78 at the bottom | It is not chosen: it follows from the ½. With no ½, there is no discount and M runs from 1 to 5. |

The full derivation, its limits and the four judges' review are in
[behaviour-multiplier-formula.md](behaviour-multiplier-formula.md) §3-§5 and §13.

### 3.5 What it guarantees

Assume an agent's ordinary active days are exchangeable: no trend, and no cycle that 90 days does
not absorb. Then the chance that any call on a given day reaches ×5 is at most 1/91 ≈ 1.1%. For
×2 it is at most 7.7% of days, and for ×3 at most 2.8%. The guarantee holds for any number of
dimensions, because step 2 ranks the whole call
([behaviour-multiplier-formula.md](behaviour-multiplier-formula.md) §5).

### 3.6 Guideline values

Here is one dimension for an agent with a full history:

| How often the agent does this | M |
|---|---|
| Less than on any past day | ×0.78 |
| About every other day | ×1.00 |
| About once a week | ×1.54 |
| About once a month | ×2.50 |
| Once in 90 days | ×3.38 |
| Never in 90 days | ×5.00 |

**For the whole call:**
- one unusual thing on its own gives **×2-5**, depending on how varied the agent's other days
  are (in the prototype, ×5 for steady agents and ×2.1-3.4 for varied ones);
- several unusual things together give **×5**.

**New agents start at ×1 and move only as far as their history allows.** Something never seen
before gives ×1.28 after 1 day of history, ×2.35 after 10 days and ×5 after 90.

## 4. How the two scores combine

| Situation | Risk_static | M | R |
|---|---|---|---|
| Routine file write in an internal folder | 2.7 | ×1 | 2.7 |
| The same write, in a pattern never seen in 90 days | 2.7 | ×5 | 13.5 |
| The same write, as a deep habit | 2.7 | ×0.78 | 2.1 |
| Dropping a sensitive table, routine for this agent | 4.4 | ×1 | 4.4 |
| Reading one public item at 3 am for the first time | 1.5 | ×3.38 | 5.1 |

- **For the daily review list,** rank by R.
- **For blocking, the open recommendation is to use max(1, M).** Habit should reorder the list
  but never lower a block decision; otherwise an attacker who mimics the agent's habit earns a
  discount (§6).

## 5. Checks so far

The prototype is [probes/m_formula_servers.py](probes/m_formula_servers.py). It runs 24 general
scenarios on 7 kinds of synthetic agent:
- five shaped like the GitHub, Slack, Calendar, SQLite and Filesystem servers, with their real
  tool names;
- one that works around the clock;
- one with very uneven daily volume.

Every expectation was fixed before running. **154 of 164 checks came out as expected.** These are
design checks, not paper numbers.

| Group | Scenarios | Result |
|---|---|---|
| A. Should stay quiet (≤ ×1.75) | ordinary days, busy day, new agent, new action after 2 weeks, periodic big job, an explorer opens another resource, weekend day, steady growth | ordinary days ×0.9-1.1 on every agent. Misses: always-on busy day ×1.82; steady growth ×2.13 on one agent |
| B. One unusual thing (≥ ×2) | new resource (agent rarely explores), known resource with a new action, new action with no resource, unusual hour, one action far above its rate, many resources in an hour, much larger request, much more data back | ×2.1-5. Miss: new resource on the always-on agent, ×1.90 |
| C. Several at once (×5) | at night with many resources and a big read; mass change; look around, then take | ×5. Miss: mass change on the uneven agent, ×3.38 |
| D. Expected to get through (limits) | mimicry, pacing, fresh id, habit building, skipping the usual step | all stay under ×2, as expected |
| D. One misbehaving agent inside an id shared by 4 | — | it was expected to be hidden but still scored ×5 on 6 of 7 agents. Strong misuse survives a shared id |

An earlier prototype with 12 dimensions, [probes/m_formula_scenarios.py](probes/m_formula_scenarios.py),
showed why the file-specific dimensions were dropped.

## 6. Decisions

**Decided by the author on 2026-10-28:**
- **One formula** for every dimension, with no policy file and no Red Flags in M.
- **Eight general dimensions** (§3.2); nothing is specific to one kind of server.
- **Combiner:** the whole call is ranked against the agent's own past days (choice A). One unusual
  thing gives ×2-5, several give ×5.
- **History:** the last 90 active days (choice A). A new action becomes ordinary after about 1-2
  weeks of daily use.
- **Identity:** the agent id only.
- **Resources:** taken from the binding layer (policy first, then inferred names), shared with the
  static score.

**Still open:**
1. **Align the static score in code and paper** (§2.5): the weighted sum and ParameterRisk in the
   code, and the ToolImpact 4/5 wording. Also consider the weight and "none" notes in §2.6.
2. **Gate rule:** use max(1, M) when blocking (recommended).
3. **Bottom:** ×0.78 with the ½ (recommended), or no discount (M from 1 to 5).
4. **Low-count doublings:** ignore doublings below about 4 calls, so an agent with 1-2 calls an
   hour is not flagged for a third. Suggested by the always-on misses; not yet tested.
5. **Outside scenario writers and lab consent** (X1, X3), due 8 November.

## 7. Known limits

| Limit | Effect |
|---|---|
| Mimicry | Misuse inside the agent's habit gets M ≤ 1; only the static score sees it. |
| Pacing | Staying under its own past peaks sets no record. |
| Fresh id | A new id starts at ×1 and ramps slowly. |
| Habit building | Doing something on half the days first makes it ordinary. |
| Skipping a usual step | Write-without-read is not a signal of its own, now that Step is gone. |
| Steady growth | It can set new peaks and rise mildly (×2.1 in one check). |
| New tool on the server | Every agent sets a record at once; there is no cross-agent discount. |
| An id shared by many agents | Weak misuse is diluted in the totals; strong misuse still shows. |
| Weekly cycles and trends | They weaken the exchangeability the guarantee rests on, and must be measured. |

## 8. Files

| File | What it holds |
|---|---|
| [behaviour-multiplier-formula.md](behaviour-multiplier-formula.md) | The formula's derivation, guarantee, constants, judges' review and paper text |
| [probes/m_formula_numbers.py](probes/m_formula_numbers.py) | Every number of the formula, the guarantee and the H sweep |
| [probes/m_formula_servers.py](probes/m_formula_servers.py) | The 24 general scenarios on 7 agents (§5) |
| `src/mcp_security/binding/` | Asset resolution shared by both scores |
| `src/mcp_security/gateway/framework.py` | Where the gateway computes `static_level` and `dynamic_risk` today |
| `src/mcp_security/static_scoring/prompts.py` | The T, S and B tier definitions |
| `src/mcp_security/input_rules/rules.py`, [v13 README](../../v13/README.md) | ParameterRisk: the run-time lookup, and how the rules are written and checked |

## References

- S. Bates, E. Candès, L. Lei, Y. Romano, M. Sesia. Testing for outliers with conformal p-values.
  *Annals of Statistics* 51(1):149-178, 2023. doi:10.1214/22-AOS2244.
- L. A. Cox Jr. What's wrong with risk matrices? *Risk Analysis* 28(2):497-512, 2008.
  doi:10.1111/j.1539-6924.2008.01030.x.
- H. O. Lancaster. Significance tests in discrete distributions. *Journal of the American
  Statistical Association* 56(294):223-234, 1961. doi:10.1080/01621459.1961.10482105.
- V. Vovk, R. Wang. E-values: calibration, combination and applications. *Annals of Statistics*
  49(3):1736-1754, 2021. doi:10.1214/20-AOS2020.
