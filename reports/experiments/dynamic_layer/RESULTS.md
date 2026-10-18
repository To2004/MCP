# Dynamic Layer — Results

Measured results for the runtime layer described in
[docs/project/dynamic-layer-design.md](../../../docs/project/dynamic-layer-design.md).
Reproduce with `scripts/dynamic_design/` (see its README).

**These numbers supersede any figure in the design doc dated before the asset-name
fix below.**

## Setup

| | |
|---|---|
| static matrices | `reports/experiments/v7/five_level_v2_policy_v7_iso/` — `score_max` 125, bands {17, 50, 100} |
| call corpora | `live_scale_<org>.csv`, rebuilt by `make_realistic_misuse.py` |
| corpus per run | 515 calls · 500 benign · 15 misuse (2.9 %) · episodes of 1-3 · distinct cells |
| likelihood prior | `reports/experiments/synthetic_static/` — 100k synthetic calls per server, uniform over scored cells |
| model | `final = min(125, max(cell × likelihood × escalation, floor))` |
| seeds | 10, mean reported |
| goal | ranking, not enforcement — nothing is blocked |

## Headline — misuse at 1 % of calls

The realistic rate. 30 seeds; two independently written implementations agree to three
decimals.

| server | scoring | misuse/run | AUC | **AP** | AP sd | P@10 |
|---|---|---:|---:|---:|---:|---:|
| `github_helios` | static cell only | 4.1 | 0.862 | **0.485** | ±0.342 | 20 % |
| | × likelihood | 4.1 | 0.865 | 0.478 | ±0.339 | 20 % |
| `slack_vireo` | static cell only | 5.0 | 0.713 | **0.021** | ±0.005 | 0 % |
| | × likelihood | 5.0 | 0.655 | 0.018 | ±0.005 | 0 % |
| `calendar_aurora` | static cell only | 5.0 | 0.868 | **0.602** | ±0.297 | 31 % |
| | × likelihood | 5.0 | 0.737 | 0.203 | ±0.224 | 10 % |
| — | random baseline | — | 0.500 | 0.010 | — | 1 % |

Against a 1 % base rate, AP 0.485 is **48×** random and 0.602 is **60×**. Slack's 0.021
is twice the base rate — effectively nothing.

**Variance is severe at this rate.** Four to five positives per run gives AP a standard
deviation of ±0.30 on the servers that work — nearly the size of the mean. A single call
landing at rank 3 rather than rank 30 swings a whole run, so no single-run figure is
usable and GitHub and Calendar are not distinguishable from each other. Slack's tiny sd
(±0.005) is not precision; it is the signature of a flat detector.

The generator can only draw from 5-12 distinct misuse cells per server, which caps how
much independent sampling is possible. More seeds do not fix that.

## The same at 3 %, for comparison

| server | scoring | misuse/run | AUC | AP | AP sd | P@10 |
|---|---|---:|---:|---:|---:|---:|
| `github_helios` | static cell only | 12.3 | 0.822 | 0.456 | ±0.151 | 50 % |
| | × likelihood | 12.3 | 0.845 | 0.455 | ±0.150 | 50 % |
| `slack_vireo` | static cell only | 15.0 | 0.693 | 0.049 | ±0.007 | 0 % |
| | × likelihood | 15.0 | 0.619 | 0.038 | ±0.006 | 0 % |
| `calendar_aurora` | static cell only | 15.0 | 0.844 | 0.592 | ±0.158 | 78 % |
| | × likelihood | 15.0 | 0.721 | 0.253 | ±0.118 | 36 % |

**Base-rate scaling is the useful comparison.** Slack's AP tracks the base rate exactly
(0.049 at 3 %, 0.021 at 1 %) — the mark of a detector at chance. GitHub and Calendar
barely move (0.456 → 0.485, 0.592 → 0.602), which is what a real signal looks like: it
does not care how rare the positives are.

**Read AP, not AUC.** ROC's x-axis is the false-positive *rate*, so against 500 benign
calls fifteen false alarms move it by three points. AP reflects what a reviewer working
down the queue actually experiences. The two disagree sharply here.

**Raw P@k is not comparable across these servers** — it is capped by the positive
count. With 13-15 positives, `max P@20` is 65-75 % and `max P@50` is 26-30 %.

## What each layer contributes

| server | static AP | × likelihood | Δ | reading |
|---|---:|---:|---:|---|
| `github_helios` | 0.510 | 0.519 | +0.009 | matrix works; the term is inert |
| `calendar_aurora` | 0.557 | 0.236 | **−0.321** | matrix works; the term does real damage |
| `slack_vireo` | 0.047 | 0.038 | −0.009 | **matrix does not work**; nothing rescues it |

The static matrix reaches 17-19× the base rate on GitHub and Calendar — six to seven of
the top ten calls are genuine misuse. On Slack it is barely above chance.

**The likelihood term is negative on all three servers.** It has not earned its place.

Calendar's regression has a stated cause: its misuse uses tools the company runs
hourly, so a frequency term discounts precisely the calls that should rise.

## Escalation

Never fired. Tukey fences need ≥20 observations of a magnitude argument; the corpora
have almost no magnitude variation.

```
github    never fired — no magnitude argument reached 20 observations
slack     290 observations, all inside the fences
calendar  340 observations, all inside the fences
```

Untested, not disproven. Testing it requires traffic where call sizes vary.

## Corpus defects found, and their effect

| # | defect | effect | status |
|---|---|---|---|
| 1 | misuse repeated 20-42× on the same cell | made misuse the agent's dominant habit, so any frequency signal reports it as routine | **fixed** — `make_realistic_misuse.py` |
| 2 | attacks more repetitive than benign (github 19.2 vs 7.9, slack 62.5 vs 33.3) | inverted the sign of every novelty signal | **fixed** with #1 |
| 3 | misuse/malicious were 25-33 % of every stream | "unusual" stops meaning anything | **fixed** — now 2.9 % |
| 4 | **asset names differ between corpus and scan** (`announcements` vs `vireo-announcements`) | **45 % of Slack calls silently dropped**, incl. 133 misuse; `conversations_history` had zero scorable rows | worked around by a prefix alias; **needs fixing at source** |
| 5 | attack assets disjoint from benign in 6 of 9 apps | the asset *is* the label; asset-aware signals score ~1.0 for the wrong reason | report the `*@helios` subset separately |
| 6 | agents one-shot (0/91 span >1 day, median 32 calls) | per-agent history cannot accumulate | pool by company |
| 7 | no magnitude variation in arguments | escalation untestable | open |
| 8 | `live_scale_all.csv` is an exact concatenation of the three per-org files | double counting | use per-org files |
| 9 | corpora blocked by org | a chronological split trains and tests on disjoint apps | split per app |

**Defect 4 is the one to act on.** Silently dropping 45 % of a corpus would distort any
evaluation run over it, not only this one. Worth checking whether the existing dynamic
evaluations are affected.

## Prior results now superseded

Before defect 4 was found, Slack was reported at AP 0.107 static → 0.244 with the
likelihood term, and described as the one server where the term earned its place. That
was an artifact: the calls surviving the name mismatch were the higher-celled ones. With
every call scored, Slack sits at AP 0.047 and the term is negative there too.

Before defects 1-3 were fixed, misuse AUC was 0.24 / 0.41 / 0.74 on
github / slack / calendar — a measurement of corpus construction, not of the signal.

## Caller identity: what the MCP logs actually contain

Searched across every captured log and corpus, because the whole design keys on a
caller and `persona` is a column we authored rather than something observed.

| field | occurrences | what it identifies |
|---|---|---|
| `clientInfo` (from `initialize`) | 12 distinct | **the SDK or the harness — not the agent** |
| `mcp-session-id` header | 2,408 | the connection; per-session, not per-agent |
| `run_id` column | `dyn_*_ins`, `v8/sweep` | our harness's grouping, not from the protocol |
| IP address | 1,718 × `127.0.0.1` | localhost only |

`clientInfo` is the field MCP defines for a client to name itself. Every distinct value
present:

```
{"name": "mcp",               "version": "0.1.0"}   <- Python SDK default
{"name": "mcp-risk-corpus",   "version": "1.0"}     <- our harness
{"name": "mcp-scale-corpus",  "version": "1.0"}     <- our harness
{"name": "mcp-security-live", "version": "1.0"}     <- our harness
{"name": "tool-asset-probe",  "version": "1.0"}     <- our harness
```

Every non-harness client is the generic `mcp/0.1.0`. **The protocol has a field for
agent identity and in practice it carries the name of the SDK.**

There is no usable IP: the proxy runs locally, and in a real deployment an IP identifies
the host rather than the agent, since agents typically share a process.

Three consequences:

- **Per-agent identity is not obtainable from MCP** — not for want of wiring, but
  because the field that exists defaults to a constant.
- This is an independent second reason to key the likelihood on `(company, tool)`: the
  company is knowable from the deployment and its auth context, the individual agent is
  not. It agrees with the measured fact that agents are one-shot (0 of 91 spanning more
  than one day).
- **Actionable recommendation**: require agents to set a meaningful `clientInfo.name`
  (e.g. `helios-ci-bot/2.1`) and treat it as the principal. One line on the client side,
  uses the protocol as designed, and without it no per-agent runtime signal is possible
  at all.

## Open

- Does the likelihood term belong at all? Negative on three of three.
- Why is the Slack matrix near chance where the other two are 17-19× base rate?
- Escalation is unmeasured for want of varying call sizes.
- Asset naming must be reconciled at source.
