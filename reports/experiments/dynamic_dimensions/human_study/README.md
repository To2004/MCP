# Bot Day Check: a human study of the dynamic layer

A web survey of about 30 minutes for a small sample (10-20 people, many non-technical), used as
the human evaluation of the dynamic (behaviour) layer in the paper. The MCP server is the
protected asset and the AI agent is the threat: people judge one AI agent's day against that
agent's own usual days, and they never see the engine's score.

## What participants do

- **Intro**: what an AI agent is, that the company's code server is what we protect, that each
  card compares an agent only with its own last 3 months, and what a usual range means (about 1
  day in 5 is a bit outside it). A word list explains action, change, project, task, change
  request, marked sensitive, new to it, rare for it, upload, quick repeats, secure link, the
  cloud, owner, bot and night (10 pm to 6 am), plus "sizes are pages of text; times are the
  owner's local time (for bots, the server's clock)".
- **2 practice cards** (hand-built, obvious: one clearly normal, one clearly wild), each followed
  by how we would answer it, then one line: real cards are often less clear, and "A bit unusual"
  and "Maybe" are fine answers.
- **18 cards**, one agent-day each: 16 drawn from the simulated organisation and 2 hand-built
  attention checks hidden among them (one where every line is plainly as usual, one wildly
  unusual on many lines). A short break is offered halfway. For each card:
  1. *How unusual is this day for this agent?* Normal for it / A bit unusual / Very unusual.
  2. *Would you ask someone to check what it did today?* No / Maybe / Yes.
  3. *What stood out?* Any of the shown lines (asked only when the answer to 1 is not "Normal
     for it").
- **8 pairs**: two agents from the same day, shown line by line (A, then B, under each line);
  *there is time to check only one of them today: which one?*

## The card lines

Every card holds the same nine rows in the same order, so the presence of a row is never a cue.
Eight are shown. Each has "usual" (the same agent's last 90 days up to yesterday: the 10th-90th
percentile of its active days, or "about X" when that range is narrow) and "today":

| Row id | Line on the card | What it shows | Engine dimensions it carries (`row_map` in the key) |
|---|---|---|---|
| `hours` | Hours it worked | clock hours with an action, in the owner's home time zone; nights (10 pm-6 am) and weekends | time of day, session length |
| `actions` | Actions in the day | tool calls | calls in the last hour, burst |
| `projects` | Projects it touched | one fixed pattern: "7 projects. New to it: 3. Marked sensitive: 2 (both new to it)." | asset, distinct assets in the last hour, many assets |
| `changes` | Changes it made | write calls | writes in the last hour, risky order |
| `kinds` | Kinds of actions | tools in plain words; "nothing new", or what is new or rare for it, fact first | tool |
| `upload` | Biggest single upload | the largest request, in pages of text (1 page = 3 KB, rounded like a count; "less than a page") | request size |
| `downloads` | Most items it asked for at once | **not shown**: not recorded on any card (the simulator has no page size) | none |
| `repeats` | Quick repeats | the most extra times it did one action on one project within 10 minutes, in digits | same call in 10 minutes |
| `connection` | Where it connected from | today's places (office, home, secure link, the cloud...) and program, each new or rare one marked; "(nothing new)" | network, app, skipped hello |

Risky order, session length and the skipped "hello" have no line of their own; the key maps them
to the closest line. No product names appear: an agent uses "its usual app", "a different app
(new to it)", "its usual bot program" or "its own small program instead of an app".

## How the cards were chosen

The organisation is the main profile of `normal_org_world.py` (150 agents, seed 7; days 0-89
are history, days 90-179 are scored). It is scored by the **shipped** engine
(`src/mcp_security/behaviour/engine.py`, design v4) in one stream in time order, with the limits
`policy.py` learns from the first 30 days, as `normal_org_sim.py --check-port` runs it. Each
day's review list is the top 4 agent-days by M, then s2, as in `DIMENSION_FORMULAS.md`. Only
agent-days surely on the list (or surely off it) are used, never one tied at the cut. An
agent-day is used only when all its actions fall on the owner's own calendar date of that day,
so the weekday and the hours on a card always describe one local day.

| Stratum | Cards | Definition |
|---|---|---|
| A, caught | 4 | a gray agent-day on the list; 4 different gray kinds |
| B, false alarm | 3 | an ordinary agent-day on the list; 3 different strongest dimensions, preferring x3 or more, a cause a line shows, and no latent benign cause (at least one has none) |
| C, missed | 3 | a gray agent-day not on the list; 3 different kinds, preferring kinds the engine usually misses (scope creep, mass cleanup, cross copy), kinds A did not use, and below x3 |
| D, life or company change | 3 | a labelled benign change (vacation, travel, launch week, migration...); at least one at x3 or more and one below |
| E, plain | 3 | an ordinary agent-day not on the list, M at most x1 |

| Pair type | Pairs | The engine prefers |
|---|---|---|
| `gray_over_ordinary` | 3 | a listed gray day over the unlisted ordinary day closest to the cut |
| `false_alarm_over_gray` | 3 | a listed false alarm over an unlisted gray day (the engine is wrong) |
| `rank1_vs_rank4` | 2 | rank 1 over rank 4, both listed |

Every pair needs a clear margin: the preferred card's M at least x1.25 the other's. A pair type
that cannot be filled with that margin may fall back to any margin above an exact tie on M
(never a tie decided by s2 alone); `rank1_vs_rank4` never falls back. The key stores each pair's
`margin`, `tie_on_M` and `close`, and the analysis reports close pairs apart.

To avoid easy cues: no agent appears twice; picks spread over roles and weekdays; at most 3 of
the 16 cards are bots (bots are 14% of agents), at most 1 per stratum; at least one gray card
falls on a day with a company note, so a note never means "benign"; at least one non-gray card
falls on a weekend, so a weekend never means "gray"; gray kinds differ across the strata and the
pairs where they can; over-fetching is never used (it needs the page size, which is not
recorded). Notes are true facts of the simulated day: about the owner ("calendar" in the data)
and about the company ("company"). The practice and attention cards use novelty phrases that no
simulator card uses; the builder stops if one is shared.

`study_notes.latent_cause` finds benign changes the simulator labels on the wrong days: the
labels of an internet-provider change and an app switch cover three calendar days, while the
agent may first use the new line or app later. Such a day counts as "ordinary" for the strata
(the simulator did not label it), and `key.json` records `latent_cause` so the paper can call it
"a benign change the manager did not know about".

## Files

| File | Public? | What it is |
|---|---|---|
| `items.json` | public | the item bank the web page embeds: rows (with `shown`), texts, practice cards, cards, card orders (`forms`), pairs. Salted opaque ids, no scores, strata, kinds, labels, agent ids or day numbers |
| `cards.txt` | public | `items.json` rendered as plain text, no ids: what a participant reads. Card n is `cards[n-1]`; Agent A and B are a pair's `cards[0]` and `cards[1]`. Claude raters read this; it can go in the paper appendix |
| `key.json` | **private** | per card and pair: stratum, gray kind, labels, latent cause, org event, agent, day, M, R, strongest dimension, s2, list rank; pair margins; the id salt; the engine version, git sha and file digest; `row_map`; what the real list holds (`context`) |
| `make_items.py` | | the builder (CLI) |
| `study_scores.py` | | runs the shipped engine and builds the daily list |
| `study_select.py`, `study_pairs.py` | | picks the cards and the pairs (pure functions) |
| `study_facts.py`, `study_words.py` | | what an agent did and its usual days, in plain words |
| `study_notes.py` | | who the agent is, the notes, and latent causes |
| `study_text.py` | | the fixed texts, the hand-built cards, the phrase check, and the `cards.txt` renderer |
| `analyse_responses.py`, `analysis_stats.py` | | the analysis of the responses, and its statistics (ranks, bootstrap, Fleiss' kappa, Krippendorff's alpha) |
| `build_page.py`, `web/` | | the participant web page: `web/index.template.html` plus `items.json` gives `web/index.html` (see [web/README.md](web/README.md)) |
| `collect_responses.py` | | gathers answers from the page's store export, pasted answer codes and Claude runs into one list for the analysis |
| `claude_ratings.json` | | the 5 Claude runs on `cards.txt` (model, protocol, times, answers) |
| `results/` | **private until collection ends** | `claude_only.md` / `.json`: the analysis of the Claude runs alone (it names strata and scores) |
| `examples/` | | a **synthetic** responses file and the report it gives, to show the end-to-end path (see its README) |
| `.id_salt` | **private**, not in git | the secret that salts the ids (`.gitignore` here) |

Tests: `tests/test_dynamic_human_items.py`, `tests/test_dynamic_human_analysis.py`,
`tests/test_dynamic_human_web.py` (page build and answer collector).

## Rebuild

```bash
uv run python reports/experiments/dynamic_dimensions/human_study/make_items.py \
    [--seed 7] [--agents 150] [--profile main] [--out-dir DIR] [--cache /path/to/scores.pkl] \
    [--require-clean]
uv run pytest tests/test_dynamic_human_items.py tests/test_dynamic_human_analysis.py -q
```

It takes about 6 minutes, most of it the engine. With `--cache`, the engine's day scores are kept
in a scratch file and reused when it was made for the same world and the same engine files
(sha256 of `engine.py`, `memory.py`, `policy.py`): about 45 seconds. `--require-clean` stops
unless the engine files match git HEAD; use it for the bank people will answer.

The output is deterministic for a given seed and salt. Two catches:

- `normal_org_world.repo_prefs` orders repositories with Python's `hash()` of strings, which
  changes from one process to the next. The builder re-runs itself under `PYTHONHASHSEED=0` and
  records the value in `key.json`. (`normal_org_sim.py` does not pin it, so its saved results
  move slightly from run to run.)
- The ids are salted with a secret: `$BOT_DAY_ID_SALT`, else `.id_salt` here (made on the first
  run and ignored by git). `key.json` keeps a copy. Without it, a rebuild gives the same cards
  under different ids. The salt feeds only the ids; selection and orders do not depend on it.

`key.json` records the git sha, whether the engine files had uncommitted changes
(`engine_uncommitted`), and a sha256 of them. Changing the selection, the texts or the seed
changes the bank: bump `BANK_VERSION` in `study_text.py` before collecting answers on a new bank,
so responses always name the bank they answered.

## The web page

```bash
uv run python reports/experiments/dynamic_dimensions/human_study/build_page.py
```

writes `web/index.html` from `web/index.template.html` and `items.json`; it refuses a bank that
carries a key-only field. Rebuild after every `make_items.py` run (a test checks that the
committed page matches). The page is published as a private claude.ai artifact; how to share it
and how answers come back is in [web/README.md](web/README.md). The page does what this list
asks:

- show only rows with `shown: true`, and offer only those in "What stood out?";
- use `text.note_labels` ("About the owner", "About the company") for the two notes;
- pick one of `forms` per participant (for example by a hash of the pid) and show the cards in
  that order, with "Card 7 of 18" and the `text.sections.break` line halfway; the forms already
  keep strata apart and place the attention checks (none in the first 3, one in the second
  half), so the page never needs the key;
- shuffle the order of the pairs and the order inside each pair per participant, and record
  `top` (the card shown first) and `order`;
- on a phone, stack each line (label, then "Usual: ...", then "Today: ..."); show pairs line by
  line, A under B (side by side on a desktop), and repeat the question and the A/B buttons below
  the pair;
- save after every answer, so a person can take a break.

It also records the form it used (`form`), resumes on the same device after a reload, and ends
with an answer code for people whose answers cannot reach the store.

## Responses

One document per participant in a shared store; the analysis takes a JSON list of them:

```json
{"pid": "...", "bank_version": "dyn-human-v1", "started": "ISO time", "finished": "ISO time or null",
 "background": {"tech": "no|tech|security", "ai_use": "never|sometimes|often"},
 "cards": {"<card id>": {"unusual": 0, "check": 0, "stood_out": ["hours"], "ms": 5300, "order": 1}},
 "pairs": {"<pair id>": {"chose": "<card id>", "top": "<card id shown first>", "ms": 8100, "order": 1}},
 "mobile": false, "rater": "human|claude"}
```

`unusual`: 0 normal for it, 1 a bit unusual, 2 very unusual. `check`: 0 no, 1 maybe, 2 yes.
`stood_out` is asked only when `unusual > 0`. Whether the attention checks were passed is not
stored: the analysis computes it from the key. Optional extra fields are read when present:
`model` (for a Claude run) and `form`. Practice answers, if a page saves them under `cards`,
are skipped silently.

Gather everything into that list first:

```bash
uv run python reports/experiments/dynamic_dimensions/human_study/collect_responses.py \
    --store store_export.json --codes codes.txt \
    --claude reports/experiments/dynamic_dimensions/human_study/claude_ratings.json \
    --out responses.json
```

`--store` takes an export of the page's `responses` collection in any wrapping (each viewer's
document holds `{"runs": {pid: response document}}`); `--codes` takes a text file of answer codes
pasted from emails or messages (`BDC1-` + base64url JSON + `.`; line breaks inside a code are
fine); `--claude` takes saved Claude runs. Of two copies of one run (a stored run and its code),
the more complete one is kept.

## Analysis

```bash
uv run python reports/experiments/dynamic_dimensions/human_study/analyse_responses.py \
    --responses R.json --key key.json --items items.json --out results.md \
    [--json-out results.json] [--draws 2000] [--seed 7]
```

- **Attention rule (pre-registered).** The plainly normal card passes with "normal for it". The
  wildly unusual card passes with "a bit" or "very unusual" AND "maybe" or "yes" to a check. A
  person is kept after passing both; one who stopped early but passed both is kept with the
  answers given. The report also shows the stratum table with no attention screen.
- **Headline: per stratum and per card, "for these cards".** Shares of "unusual", "would check"
  and "yes" for A-E, each with a two-way bootstrap interval (people and cards within their
  stratum) and the number of people, cards and answers; the A minus B difference; the card table.
- **Secondary.** Spearman's rho of M against people's answers, flagged as depending on the card
  mix.
- **Pairs.** Agreement with the engine per pair type, for clear pairs and for close pairs apart,
  the gray-card share, and the share choosing the card shown first.
- **Reasons.** On cards with M of at least x2 (below it the strongest dimension is noise), how
  often the ticked lines include the line of the engine's strongest dimension. A blind spot is a
  shown line that no dimension maps to; ticks on a hidden line are counted as noise.
- **Background groups and Claude runs**: values and n only, no intervals.
- **Agreement among people**: Krippendorff's ordinal alpha (Fleiss' kappa beside it).
- **Position**: "would check" and seconds per card in the first and second half of each person's
  own card order.

## Claude raters

Claude raters are a separate group and never count toward the human results or the human
majority. Run them through the API with `cards.txt` as the only input: no tools, no file or
repository access (a rater with file tools inside this repository could read `key.json`).
Record the model and the prompt, and save each run as a response document with
`"rater": "claude"` and `"model"`, mapping card n of `cards.txt` to `items.json` `cards[n-1]`
(`collect_responses.py --claude` does this mapping).

The 5 runs in `claude_ratings.json` did not follow the API-only protocol: they were workflow
subagents (Claude Opus 5.5) inside this repository, told to read only `cards.txt`. Each run's tool
log shows exactly one Read, of `cards.txt`, and no other tool, so none of them saw the key. The
file says so in `protocol`. For the paper, either report them with that sentence or rerun them
through the API. The 5 runs answer almost identically, so they behave like one rater, not five.

## What the paper can claim

The 16 cards are a purposive sample: 6 of them (B and C) plus the high D card were chosen to
disagree with the engine, and 4 of the 7 listed cards here are gray, while on the engine's real
list gray days are a small minority (`key.json` `context.list_composition`). So:

- report the per-card table and the per-stratum shares: "for these 16 cards, k of n people asked
  for a check on ...", "people asked to check k of 3 missed cards";
- state the number of cards next to the number of people; with 10-20 people and 3-4 cards a
  stratum, only differences of about 30-40 points or more stand out from zero;
- do not report precision, recall or a population-level agreement figure, and give Spearman's
  rho only with its caveat;
- report the row ticks qualitatively, and Claude raters as their own group.

## What is private

- `key.json` and `.id_salt` must never be embedded in the web page, shown to participants or
  given to Claude raters. Only `items.json` (and `cards.txt`) are public.
- The salt stops the trivial mapping from an id to an agent-day, but someone with this code can
  still rebuild every card's text and match it. The real protection is that participants and
  raters get neither the code nor the key: do not share the repository, or a link to this
  folder, with them until data collection is over.
- Responses hold a random participant id and two background answers (technical background, how
  often they use AI); no names or contact details. Keep the response store private.

## Before anyone takes the survey

1. Commit the engine, the simulator (`normal_org_world.py`, `normal_org_sim.py`,
   `normal_org_engines.py`), this folder and the two tests; rebuild with `--require-clean` and
   check that `key.json` says `engine_uncommitted: false`. The current `key.json` was built from
   uncommitted engine files (`engine_uncommitted: true`), so its git sha alone does not
   reproduce it; its `engine_files_sha256` does.
2. Freeze `BANK_VERSION` (`dyn-human-v1`): no change to the bank after the first participant
   without a new version.
3. Pilot the timing with 2-3 people. If the median is over 30 minutes, cut to 6 pairs (and bump
   the version).
4. Arrange ethics approval (an IRB, or the university's ethics committee, or a documented
   exemption) and a consent page that says what the study is, that it takes about 30 minutes,
   that taking part is voluntary and can stop at any time, what is stored and for how long, and
   whom to contact. The survey shows only simulated data: no real company, person or agent
   appears on a card.

## Decisions

Where the two reviewers, or a reviewer and the original spec, pulled different ways, the choice
that protects blindness and plain language won.

- **The never-recorded row is hidden, not shown as "not recorded".** The spec kept it on every
  card; the participant reviewer asked to remove it (reading time, "why is this hidden?"). It
  stays in the data on every card (the response format and the "fixed rows" rule hold, and its
  absence is the same on every card, so it is no cue), but the page and `cards.txt` skip it and
  it is not a "stood out" option. The analysis treats any tick on it as noise.
- **"Nothing new" instead of "same as usual"** for kinds and connection (the spec's wording), and
  the connection line always states today's places and program: "same as usual" left open what
  was the same.
- **Pages of text instead of KB** (the spec said KB with a hint). One fixed rule, 1 page = 3 KB,
  applied to the shown number in both columns; the earlier hints gave the same size different
  pictures.
- **About 30 minutes, not 15.** The participant reviewer timed the bank at 33-38 minutes for a
  non-technical first-timer. The page now says 30 (shorter lines, one row fewer, pairs line by
  line). The 8 pairs of the spec are kept; the pilot decides whether to cut to 6.
- **Fixed card orders instead of a per-participant shuffle with stratum rules.** The method
  reviewer asked the page to shuffle per participant with no same-stratum neighbours and placed
  attention checks; that needs strata on the page, which would break blindness. The builder
  makes 6 orders that keep those rules, and the page picks one per person. The pairs, and the
  cards inside each pair, can be shuffled freely on the page.
- **Ids are salted, but the salt is not a guarantee.** Done as asked; the README says what it
  does not protect (see "What is private").
- **No commit.** The method reviewer asked to commit the engine and the study; committing is the
  study owner's call, so it is step 1 of "Before anyone takes the survey", and `--require-clean`
  enforces it. `__pycache__/` is already ignored by the repository's `.gitignore`.
- **The bank version stays `dyn-human-v1`.** Nobody has answered it yet; it is frozen from the
  first participant on.
- **Lenient wild attention rule, strict normal rule** (the method reviewer's suggestion): a
  cautious "a bit unusual, maybe" on the wild card shows the person read it; with 10-20 people
  each exclusion costs 5-10% of the sample. The report shows the table with no screen as well.
- **Latent causes are recorded, not relabelled.** Re-tagging the simulator from first use would
  change `normal_org_world.py`, outside this folder (and the repository keeps old behaviour
  selectable). Instead the key records `latent_cause`, stratum B prefers false alarms without
  one and must include at least one.
- **The secure-link note says what the simulator did.** The participant reviewer suggested
  "over the last few weeks the company moved everyone ...; this week the old one was switched
  off", but the simulator switches everyone on one day. The note says "This week the company
  switched everyone from the old secure link to a new one", and the word list says the company
  replaced it during these months, which is why many "usual" columns show both links.
- **"Biggest single upload"** (one of the participant reviewer's two options): shorter on a phone
  than "Biggest thing it added to the code server", and true for large requests that are not
  files.
- **The practice "very unusual" card stays extreme** (the spec asks for one clearly wild), now
  with phrases no real card uses and general feedback, followed by "real cards are often less
  clear".
- **No ids in `cards.txt`** (the participant reviewer): cards and agents are found by position.
- **`check_listed` is dropped** (the method reviewer): it pooled A and B as 4:3 while the real
  list is mostly not gray. The real list's mix is in `key.json` `context` and in the report.
- **Night is 10 pm to 6 am** on the cards, as the word list says (it was midnight to 6 am).

## Limits

- The organisation is simulated. The cards show what the simulator records, not a real gateway
  log.
- "Most items it asked for at once" is not recorded, so over-fetching cannot be judged.
- s2 comes from the shipped engine. The port check compared only M and the strongest dimension,
  so the list order can differ slightly from `normal_org_sim.py`'s simulation engine on days with
  ties at the same M.
- Agent-days are the server's days (UTC); hours are shown in the owner's home time zone, and
  only agent-days that fall on one local date are used.
- The engine docs and simulator comments outside this folder still use gendered pronouns for
  agents and owners; use "its" or "the agent's" in any text copied into the paper.

## References

- [DIMENSION_FORMULAS.md](../DIMENSION_FORMULAS.md): the v4 dimensions, s1, s2 and the review list
- [normal_org_world.py](../normal_org_world.py), [normal_org_sim.py](../normal_org_sim.py): the
  simulated organisation and its evaluation
- [engine.py](../../../../src/mcp_security/behaviour/engine.py): the shipped engine
- Krippendorff, K. (2011). Computing Krippendorff's alpha-reliability. Annenberg School for
  Communication, University of Pennsylvania.
