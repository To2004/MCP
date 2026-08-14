# Dynamic Layer v3 — A Realistic Call Distribution

v2 was scored on corpora that drew their tool with `rng.choice`, so every tool held an
equal share and none was ever rare. That silently disabled `L`: the factor asks whether a
tool is unusual for a deployment, and under a uniform draw none is. The measured
consequence was that ±6% of the score — about a third of the whole range — was warm-up
drift rather than signal, and identical zero-argument calls scored anywhere inside it.

This run replaces the corpus and then re-measures. **1,000 live calls against each of the
three real MCP servers** — GitHub, Slack, Google Calendar — plus **100,000 synthetic**
calls per server sharing the same distribution, arguments and assets. Six corpora, three
servers, two scales each.

The one change to the formula is a cold-start guard on `L`, described at the end: it was
added because the corpora made the defect visible, not to improve the numbers.

## Where the distribution comes from

Picking 26 tool probabilities by hand invites tuning them until the scorer looks good.
The shape is declared one level up instead, in
[`org_traffic.py`](../../../../scripts/dynamic_design/org_traffic.py), as *who is calling*:

| role | share of volume | what it does |
|---|---:|---|
| `ci_bot` | 52% | polls PR status, commits, file contents |
| `developer` | 26% | reads code and issues, occasionally writes |
| `reviewer` | 11% | PR files, comments, reviews |
| `triager` | 7% | issue triage |
| `release_manager` | 3% | merges and release branches |
| `admin` | 1% | repository and user administration |

Slack and Calendar have their own persona sets on the same principle — Slack is
`assistant_bot` 44% / `member` 31% / `channel_manager` 14% / `people_ops` 8% /
`workspace_admin` 3%; Calendar is `scheduling_bot` 45% / `employee` 31% /
`exec_assistant` 14% / `room_bot` 7% / `workspace_admin` 3%. All three reach **every tool
their server exposes** (26, 16 and 13).

The tool distribution is the marginal that falls out. It is heavy-tailed because roles
are — CI runs constantly, an admin acts a few times a week — and no per-tool probability
was chosen directly. The weights were fixed before anything was scored.

| corpus | head | tail | ratio | tools | writes |
|---|---|---|---:|---:|---:|
| github live 1,000 | `get_file_contents` 18.4% | `fork_repository` 0.10% | 184× | 26 | 9.2% |
| github synthetic 100,000 | `get_file_contents` 17.6% | `fork_repository` 0.21% | 83× | 26 | 10.8% |
| slack live 1,000 | `conversations_history` 27.6% | `usergroups_create` 0.40% | 69× | 16 | 15.3% |
| slack synthetic 100,000 | `conversations_history` 26.7% | `usergroups_create` 0.56% | 48× | 16 | 15.0% |
| calendar live 1,000 | `list-events` 33.6% | `manage-accounts` 0.40% | 84× | 13 | 14.3% |
| calendar synthetic 100,000 | `list-events` 33.0% | `manage-accounts` 0.63% | 52× | 13 | 13.9% |

The top three tools are half the volume; the bottom five are under 1%. Arguments are drawn
the same way — `per_page` is the API default in 58% of calls, its maximum in 14% — because
a uniform draw over legal values makes every page size equally ordinary and flattens the
quartiles the runtime learns.

## The live runs

| server | calls | accepted | writes |
|---|---:|---:|---|
| GitHub | 1,000 | 692 (69%) | executed, confined to a scratch repository created for the run |
| Slack | 1,000 | 709 (71%) | **recorded, not executed** |
| Calendar | 1,000 | 712 (71%) | **recorded, not executed** |

GitHub's writes were safe to execute because they could be confined to a repository
created for the run. Slack and Calendar writes are outward-facing — posting into a real
workspace, and creating or deleting events whose `sendUpdates` parameter emails attendees
— so those calls were sampled and logged with their real arguments but never sent.

That costs nothing here: the runtime scores the call that was made, not the reply, so an
unexecuted call is worth exactly what one the server rejected is worth, and 31% of the
GitHub calls were rejected anyway. Rejected and unexecuted calls are both kept, because
what an agent *asked for* is the observation.

## Result

| | github 1k | github 100k | slack 1k | slack 100k | calendar 1k | calendar 100k |
|---|---|---|---|---|---|---|
| scored calls | 500 | 50,000 | 500 | 50,000 | 500 | 50,000 |
| D median | 0.923 | 0.869 | 0.937 | 0.912 | 0.919 | 0.884 |
| D min / max | 0.772 / 1.205 | 0.738 / 1.264 | 0.763 / 1.181 | 0.746 / 1.266 | 0.757 / 1.231 | 0.739 / 1.255 |
| **noise floor (p95)** | 0.033 | **0.009** | 0.034 | **0.018** | 0.145 | **0.007** |
| write vs read gap | +0.170 | +0.207 | +0.178 | +0.199 | **+0.090** | +0.163 |
| P(write above read) | 0.984 | 0.977 | 0.939 | 0.935 | 0.939 | 0.902 |
| gap vs floor | clear | clear | clear | clear | **inside** | clear |

The two GitHub corpora agree to within 0.002 on every summary, which is the point of
sharing one generator: they differ in sample size and in whether a network was involved,
and in nothing else.

All three servers order their tools the same way — administrative and state-changing at
the top, the highest-volume read at the bottom:

```
slack      usergroups_me 1.228  usergroups_update 1.222  conversations_leave 1.186
           ... conversations_replies 0.902   conversations_history 0.875
calendar   manage-accounts 1.271  create-events 1.268  delete-event 1.244
           ... get-freebusy 0.888   list-events 0.870
```

**Every server separates writes from reads at 100,000 calls.** The one failure is
Calendar at 1,000, where the gap (+0.090) sits inside its own noise floor (0.145) — and
the 100,000-call run of the same server, same generator, resolves it (+0.163 against a
floor of 0.007). The cause was warm-up length, not the server and not the formula.

### The noise floor is a warm-up artifact, and it is measurable

At 1,000 calls the three servers disagreed sharply and at 100,000 they agree — 0.009,
0.018, 0.007. The difference is warm-up length, not the servers. Holding the corpus and
the scored window fixed and varying only the warm-up length:

```
 warm calls  p95 spread    median   D range
        250       0.086     0.010     0.556
        500       0.071     0.006     0.552
      1,000       0.075     0.006     0.542
      5,000       0.031     0.002     0.543
     20,000       0.012     0.001     0.534
     60,000       0.004     0.000     0.528
```

The floor falls **20×** while the score's own range barely moves. `L`'s reference is the
median tool a deployment calls, and that reference keeps moving until enough history has
accumulated; until then identical calls score differently for no reason but arrival time.

The operational consequence is concrete: **`L` should not be trusted below a few thousand
observations.** Above ~5,000 the floor is under 0.03 and every separation reported here
clears it; at 500 it does not, which is exactly where Calendar's 1,000-call run failed.

## Cold start

The question the warm-up curve raises is what the runtime should do *before* it has any of
that history. Three cases, and only the middle one needed fixing.

**No history at all.** `D` is exactly 1.0, so `R` is the static cell and the design-time
score stands untouched. This was already correct and is now pinned by a test: inventing a
runtime adjustment from no evidence is the one answer that cannot be right. Verified on an
empty deployment for `get_file_contents`, `create_repository`, `conversations_history` and
`delete-event` — all exactly 1.0000.

**A little history — the case that was wrong.** `B` refuses to grade an argument until it
has seen `MIN_HISTORY` values of it, so it stays neutral. `L` had no such guard, and on a
fresh deployment it read:

```
after 9 calls    get_pull_request_status   L = 1.064   "0.79x the median tool"
after 99 calls   list_pull_requests        L = 0.934   "1.78x the median tool"
```

Both are noise stated as fact. Rarity is a claim about a distribution and nine calls are
not one. `L` is now shrunk toward 1.0 in proportion to the evidence behind it:

```
confidence = total_calls / (total_calls + MIN_HISTORY x tools_exposed)
L          = 1 + (raw_L - 1) x confidence
```

The per-tool requirement is `MIN_HISTORY` reused, so `B` and `L` demand evidence of the
same order before either may move the score — rather than a new constant chosen to make
the curve look right. Half confidence lands at 520 calls for GitHub, 320 for Slack, 260
for Calendar, and the same trace now reads 1.001 at nine calls and 0.989 at ninety-nine.

**Enough history.** Above roughly `20 x tools_exposed` the shrinkage is inert and `L`
behaves as before; the 100,000-call summaries are unchanged by it.

### What the shrinkage does not fix

It does not shrink the noise floor — 0.086 at 250 warm calls before and after. That is not
a failure of the guard, it is what the metric measures. The spread is taken over a
5,000-call window during which the baseline legitimately adapts, so two identical calls at
either end of it *should* differ. A frozen reference was prototyped and does not help
either, for the same reason: the window spans several refreshes.

The honest framing is that an adaptive baseline cannot also be time-invariant. What must
hold is that the drift is smaller than the signal, and at 100,000 calls it is: floors of
0.007–0.018 against gaps of +0.163–0.207, a margin of roughly ten to one.

### Against v2's uniform corpus

Measured the same way as before — byte-identical calls scored at different points in the
stream, which should score identically and do not, because `L` keeps updating.

```
v2, uniform corpus     worst identical-call spread 0.058   = 31% of the range
v3, org distribution   p95 identical-call spread   0.009   =  2% of the range
```

The floor is reported as a **p95, not a maximum**. A maximum over N groups is an
extreme-value statistic that grows with N by itself: the first version of this report
used one and made the 100,000-call corpus look 17× noisier than the 1,000-call corpus
purely for having 910 repeated groups instead of 17.

### The score separates state-changing calls from reads

`D` is not a risk score — risk is `cell × D`, and the cell carries impact and sensitivity.
But read/write is an independent label the runtime never sees, so it is a fair check on
whether `L`'s ordering tracks anything real:

```
writes  median 1.076        P(write above read) = 0.977
reads   median 0.868        (0.5 would be no separation at all)
```

Ordered by `D`, the top of the synthetic run is `fork_repository`, `create_repository`,
`search_users`, `create_issue`, `update_pull_request_branch`; the bottom is
`get_file_contents`, `get_pull_request_status`, `list_commits`. That ordering is earned:
the administrative tools are rare *because* administration is rare, and `L` is reading
exactly that.

`search_users` and `search_repositories` sit high while being reads. That is not an error —
they are genuinely rare in this org, and `L` measures rarity, not damage. The cell is what
distinguishes a rare read from a rare write.

## Two defects the realistic corpus exposed

Both were invisible under a uniform draw and both silently disabled `B`. Neither was
found by reading the code.

**1. An argument that cannot be narrow pinned the whole call.** `B` takes the least
discount any argument justifies, so an argument that can never fall below its own Q1
contributes 1.0 to every call and fixes `B` at 1.0 for the entire tool. A page number is 1
in four calls out of five, so its Q1 sits on its own minimum — and every paged tool had
`B` disabled. Measured: `B` was flat at 1.000 across min, median and max on all 50,000
calls. Such arguments are now excluded rather than scored 1.0, exactly as arguments with
no history already were.

**2. The `Q3 <= Q1` test did not detect what it claimed.** It was meant to catch a sample
with no variation. What it actually detects is a degenerate interquartile range, which a
dominant default produces on its own: `per_page` is 30 in 58% of calls, so Q1 and Q3 both
land on 30 while the sample still spans 1 to 100. The argument flipped between disqualified
and active as Q3 crossed from 30 to 50, and **identical calls scored 0.771 or 0.908
depending only on when they arrived**. Since `B` is gated at Q1, Q3 no longer participates
in it at all; the test is gone. This alone moved the 100,000-call noise floor from 0.093
to 0.009.

## What this still does not establish

Every call here is benign. Nothing shows the layer separates misuse from ordinary use.
The write/read gap shows `L` tracks **rarity**, and in these orgs rarity and administrative
power happen to coincide — `L` would score a rare read and a rare deletion identically,
because it never sees arguments and never sees what a tool does. Distinguishing those is
the cell's job, not `L`'s.

The case `L` structurally cannot catch is **a common tool used wrongly**.
`get_file_contents` is 18% of GitHub traffic; an agent walking every path in every
repository through it will keep scoring ~0.86, because the tool is ordinary. That call has
to be caught by its arguments — `B` — or by what it touches — the cell.

And `B` fires on 6–14% of calls, with a median of exactly 1.000 on every tool of every
server. For the other ~90% `D` **is** `L`, meaning the runtime is scoring the tool rather
than the request. `B` is also discount-only, so **nothing in the current runtime can raise
a call for having dangerous arguments** — only rarity can raise anything. That is the real
gap, and no benign corpus can close it.

## Files

| file | contents |
|---|---|
| `report_<server>_org.txt` | full scored report, live 1,000 — one per server |
| `report_<server>_org_100k.txt` | full scored report, synthetic 100,000 — one per server |
| `warmup_curve.txt` | noise floor against warm-up length, and the cold-start trace |
| `tool_marginal.json` | persona weights and the tool distribution they imply, all 3 servers |
| `<server>_org.csv` | the three live corpora |

The three 100,000-call corpora are 2.2–3.3 MB and live in
`reports/experiments/real_benign/<server>_org_100k.csv`.

## Reproduce

```bash
export GITHUB_TOKEN=$(gh auth token)                       # github
export SLACK_MCP_XOXP_TOKEN=...                            # slack
export GOOGLE_OAUTH_CREDENTIALS=... GOOGLE_CALENDAR_MCP_TOKEN_PATH=...   # calendar

python3 scripts/dynamic_design/make_org_live.py --server calendar --skip-writes
python3 scripts/dynamic_design/make_org_synthetic.py --server calendar \
    --state-from reports/experiments/real_benign/calendar_aurora_org.csv \
    --out reports/experiments/real_benign/calendar_aurora_org_100k.csv
python3 scripts/dynamic_design/report_org_run.py --server calendar \
    --corpus reports/experiments/real_benign/calendar_aurora_org_100k.csv
```

`--skip-writes` records state-changing calls without sending them; GitHub omits it and
routes writes to a scratch repository instead.
