# Dynamic layer: scenarios and two new ideas

> **Superseded on 2026-10-19:** the current design gives each dimension its own formula and level 0–5 instead of one combined formula. See [DIMENSION_FORMULAS.md](DIMENSION_FORMULAS.md).

This page runs the formula from [FORMULA.md](FORMULA.md) on concrete scenarios, shows where it works and where it breaks, and proposes two new ideas that fix the breaks. Every number here comes from running the reference engine (`dynamic_engine.py`), not from hand calculation.

## How the scenarios were run

- **One simulated GitHub organisation:**
  - 50 agents: 16 reviewers, 16 developers, 8 triagers and 10 merge bots, over 90 days;
  - real tool names and static impacts from the mcp-static-scan reference scan;
  - people work weekdays from the office or from home, with Claude Desktop or Cursor; bots run every hour.
- **The scenario starts on day 70.** The engine scores every call in order.
- **The daily check flags agent-days:**
  - the budget is 2 per day, with the threshold taken from the previous 30 days;
  - a day is never flagged below 4 bits (the floor, see [Why a floor](#why-a-floor)).
- **Reported per scenario:**
  - the strongest call: its multiplier, and the risk before → after;
  - which family fired;
  - whether the day was flagged;
  - for organisation-wide scenarios, how many alerts the organisation received.
- **The tested reviewer has one ordinary false alarm.** On day 74 it had a busy afternoon: two overlapping sessions read 6 files in 10 minutes, more than it ever had. That scores 5.4 bits, above the floor. This false alarm appears in the control and in every reviewer scenario, so it is left out of the tables below.

## Scenarios with the base formula

| # | Scenario | What the agent does | Family | Strongest call | Flagged |
|---|---|---|---|---|---|
| 1 | Control | An ordinary day | none | ×1.0 | no |
| 2 | Loop | A developer reads the same file tool 40 more times in 8 minutes | Pace 4.8 | `get_file_contents` 3 → 4.2 (×1.39) | yes |
| 3 | Off-role step | A reviewer merges a pull request | Path 12.5 | `merge_pull_request` 4 → 9.5 (×2.38) | yes |
| 4 | Shared credential | A reviewer's token is used from 3 new networks with a new client within an hour | Place 9.8 (counted once) | 2 → 3.9 (×1.97) | yes |
| 5 | Off-role from a new place | Scenario 3 from a new network | Path 12.5 + Place 9.2 | 4 → 9.5; day score 21.7 | yes |
| 6 | Slow creep | A reviewer adds one new write tool a day for 10 days | Path ≈ 12 a day | `fork_repository` 4 → 9.7 | every working day (8) |
| 7 | Same off-role step daily | A reviewer merges every day for 10 days | Path 12.5 on day 1 | 4 → 9.5 | 2 of 8 working days (the first two) |
| 8 | Nagging loop | A developer lists commits 12 extra times a day for a week | Path 10.8 | `list_commits` 2 → 4.2 | all 5 working days |
| 9 | New hire, normal work | A new developer joins on day 70 | none in week 1 | ×1.0 | no (once on day 77: its first day from a second network, Place 5.9) |
| 10 | New hire, off-role on day 1 | The new developer merges on its first day | Path 7.2 | 4 → 6.6 (×1.64) | yes |
| 11 | Same, without team fill-in | As 10, but the engine does not borrow the team's habits | none | ×1.0 | **no: missed** |
| 12 | Over-fetch | Same calls with bigger page sizes | none | ×1.0 | no: **not visible** |
| 13 | Role change (legitimate) | A reviewer becomes a developer | Path 14.8 | 4 → 11.2 | **7 of 15 working days** |
| 14 | Client rollout (legitimate) | All 40 people switch to a new client over 3 days | Place 9.9 each | 2 → 4.0 | **38 alerts in 3 days** |
| 15 | Server slowdown | Everyone retries the same read in the same hour | Path 12.5, Pace | 3 → 7.2 | **40 alerts in one day** |

## What the scenarios show

**What works:**

- Off-role steps, shared credentials, new places, loops and creep all stand out on the day they happen.
- A new place adds to an off-role step (scenario 5) instead of hiding it.
- **Team fill-in is what catches a new hire's mistake on day 1.** Without it the agent has no history, so nothing fires (scenarios 10 and 11).
- **The agent's own history learns a repeated habit.** After two days the same daily merge no longer stands out (scenario 7). That is good for real habits and a blind spot for repeated misuse.

**What is weak:**

- **Pace says "more than ever before", not "how much more".** A 40-times loop scores only ×1.39. Once the count passes everything in the agent's history, the surprise stops growing.
- **Over-fetching is invisible at this level** (scenario 12): the calls look identical when you do not read inputs.

**What breaks:**

- **Organisation-wide changes flood the review budget.** A client rollout gives 38 agent alerts in 3 days; a server slowdown gives 40 in one day, all from one hour. Each agent looks strange, but nobody is misbehaving: the organisation changed, or the server did.
- **A legitimate role change keeps alerting for weeks** (7 of 15 working days). The agent's 90-day history is still full of its old role, so every new-role step looks rare.

Neither break can be fixed by looking at one agent: the first needs the other agents, and the second needs time.

## Idea A: Crowd, "one agent, or everyone?"

**The idea.** When many agents do the same strange thing at the same time, the cause is shared: a rollout, an outage, a new tool. It is one event for the organisation, not many agent incidents.

**How it works:**

1. A thing is the same step, the same tool in the same hour, or the same new network or client.
2. Count the agents that were clearly above normal on that thing (X ≥ 3 bits). Count over the last 7 days, or the same hour for a repeated tool, up to the end of the day.
3. Once **5 or more agents** share it:
   - it becomes **one notice** for the organisation;
   - it stops counting for each of those agents.
4. Below 5 agents nothing changes, so a shared credential used by 2 people still alerts on both.

**How this differs from peer comparison.** Products like Microsoft Sentinel compare one entity with its peers to find the odd one out. This flips it: when many agents change *together*, the change belongs to the organisation, so the alert moves from the agents to the organisation.

**Results in the scenarios:**

| Scenario | Base formula | With crowd |
|---|---|---|
| Client rollout (3 days) | 38 agent alerts | **2 agent alerts + 1 notice a day.** The 2 alerts are the first switchers, before 5 agents shared it. |
| Server slowdown (1 day) | 40 agent alerts | **0 agent alerts + 2 notices** ("everyone retries `get_file_contents`", "sessions start with a file read") |
| All single-agent scenarios | — | No change |

**Tried first:** a graded version, X ÷ (1 + c/3), where c is the number of other agents.

- **Under the same daily check, the two versions are close.** Graded leaves 3 alerts in the rollout and 1 in the slowdown; the fold leaves 2 and 0.
- **The fold is kept because it is simpler.** It is easier to explain ("5 or more agents → one notice") and gives the organisation a clear item to look at.
- **Neither works without the floor** (see [Why a floor](#why-a-floor)). Without it, graded leaves 16 and 40 alerts, and the fold 9 and 38.

**The cost.** If 5 or more agents misbehave in the same way at the same time, for example from one bad prompt template, it shows up as one organisation notice instead of 5 agent alerts. It is still visible, as a single item.

## Idea B: Settling, "changed, or misbehaving?"

**The idea.** A legitimate change settles: the agent does the new thing again and again, every day. Misuse is usually a one-off, or keeps changing (scenario 6: a different new tool each day).

**How it works.** If the agent made a step on **at least 3 different days in the last 7**, the step is a new habit and its Path excess is 0.

**Results in the scenarios:**

| Scenario | Base formula | With settling |
|---|---|---|
| Role change | 7 of 15 working days | **5 of 15** (days 70–72, 74, 77) |
| Slow creep (a new tool each day) | 8 of 8 | **8 of 8**, unchanged, because nothing repeats |
| Same off-role step daily | 2 of 8 | **2 of 8**, unchanged: the agent's own history had already absorbed it |
| All other scenarios | — | No change |

**The cost.** Misuse that repeats the same step every day alerts only for its first days. That is no worse than the base formula, whose 90-day history also learns the habit within a few days (scenario 7).

## Tried and dropped: persistence

**The idea:** a strange day should make the next day count for more. Yesterday's score fades into today at half strength.

**Why it was dropped.** In the scenarios it only echoed each alert into the next 1–2 days, which used up the budget: 9 → 12 organisation alerts over 3 days in the control (before the floor was added). It caught nothing new. On the 9 organisations it cost 9 points at ≤ 2 alerts a day (50% → 41%) and 6 at ≤ 4 (58% → 52%). Short bursts lost most: page walks −42, loops −25 and cancel storms −24 points, because yesterday's leftovers crowd them out of the budget.

## Why a floor

**The budget is a ceiling, not a quota.** This simulated organisation is quiet, so to fill 2 alerts a day the budget threshold drops to 1.3 bits, which is ordinary noise.

**A floor of 4 bits** means a day must be at least 16 times rarer than the organisation's normal level before it is flagged:

- Control: 9 → 2 organisation alerts in 3 days.
- Scenario 12: the agent's own small noise is no longer flagged.
- Every real scenario above is still flagged.
- **The crowd idea needs the floor.** Without it, the slowdown's small leftover signals still fill the budget with 38 alerts.

## The formula with both ideas

```
R_dynamic = R_static × e^( λ · (X_pace + X_path + X_place) )        at most ×8
```

This is the same formula as [FORMULA.md](FORMULA.md), with two changes to `X`:

- **Settling:** a Path step made on 3 or more of the last 7 days counts 0.
- **Crowd:** a thing shared by 5 or more agents counts 0 for each of them and becomes one organisation notice.

**Daily check.** Flag an agent-day when its score is above the larger of the budget threshold and the floor of 4 bits.

## Results on the 9 organisations

The same 9 simulated organisations as [FORMULA.md](FORMULA.md), with the same four dimensions. Detection is the mean over 21 kinds, at ≤ 2 or ≤ 4 flagged agent-days per day:

| Version | ≤ 2 / day | ≤ 4 / day | Note |
|---|---|---|---|
| Base formula | 50% | 58% | |
| + crowd | 50% | 58% | −2 points on workflow skip, mode switch and off-role tool at ≤ 4 |
| + settling | 50% | 58% | No kind moves by more than 1 point |
| + both | 50% | 58% | |
| + persistence (dropped) | 41% | 52% | |
| Base + floor of 4 bits | 49% (1.8 alerts a day) | 52% (2.3 alerts a day) | The floor leaves the budget unused on quiet days |

**What this shows:**

- **Both ideas cost almost nothing.**
- **Their value does not show here.** These organisations have no organisation-wide changes. Role changes are rare (about 5% of people, once in two years) and fall on about 1% of alerts. The value shows in the scenarios above.
- **The crowd's small cost** comes from strange episodes that several agents happened to show in the same week. It is folded into a notice.
- **The floor costs nothing per alert.** At ≤ 4 a day it sends 2.3 alerts instead of 4. Per alert it catches about the same as the base formula: 52% at 2.3 a day, against 50–58% at 2–4 a day.

**Notice volume:**

| Organisation | Agents | Notices a day |
|---|---|---|
| calendar_L, the largest | 150 | 0.8 |
| All others | 50 or fewer | 0.1 or fewer |

In a large organisation, more agents share common steps by chance, so the 5-agent threshold should grow with the organisation's size.

## Files

- `dynamic_engine.py`: the reference engine. It implements the formula, both ideas and the daily check, and reads only time, identity, session, tool name, client address and client name.
- `scenarios.py`: the 15 scenarios, each under the base formula, graded crowd, crowd, settling, and both. Results are in `results/scenarios.json` and `results/scenarios.txt`.
- `idea_eval.py`: both ideas, persistence and the floor on the 9 simulated organisations. Results are in `results/idea_eval.json`.
