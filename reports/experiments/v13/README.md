# v13: Five Levels per Tool Input, in One Step

v12 needed two stages, three votes, a re-ask pass and a policy-named keep to decide which inputs matter, then a second stage to write their rules, and none of its rules filled all five levels. v13 asks once per input: write a rule that turns the value into a level, reaching every level from 1 to 5, or answer none. An input is kept exactly when it gets such a rule. The rules are a lookup table for the dynamic layer: no model runs on a call. **run21 is frozen**: run13's prompt with the code of run14 to run17 and run21's two program rules (identifiers, left-out inputs). The full prompt with a summary: [run21-prompt-and-summary.md](run21-prompt-and-summary.md).

## Results (run21, frozen) against run10, run13 and run20

All columns scored with the current code and the current 57 scenario pairs (35 decided by the policy, 7 of them filesystem; 14 by common knowledge).

| | v13 run10 | v13 run13 | v13 run20 | **v13 run21** |
|---|---|---|---|---|
| Prompt | run10's | run13's | run13's | run13's |
| Kept inputs whose rule reaches all five levels | 198 of 209 | 218 of 224 | 217 of 222 | 211 of 217 |
| Scenario pairs the policy decides | 15 / 35 | 28 / 35 | 28 / 35 | **30** / 35 |
| Scenario pairs common knowledge decides | 13 / 14 | **14** / 14 | **14** / 14 | **14** / 14 |
| Important inputs with a usable rule, github, slack, calendar (switches aside) | 143 / 156 | **151** / 156 | 145 / 156 | 144 / 156 |
| Inputs that should go, dropped (github, slack, calendar) | 114 / 122 | 113 / 122 | 112 / 122 | **116** / 122 |
| Held out (filesystem, sqlite): important with a usable rule, noise dropped | **20/20, 9/9** | 16/20, 9/9 | **20/20**, 5/9 | **20/20**, 5/9 |
| github: AUC; harmless calls at 4-5, at 5; risky calls at 4-5 | 0.640; 70, 22; 238 of 500 | 0.648; 331, 86; 406 | **0.671**; 317, 86; 406 | 0.669; 327, 86; 406 |
| slack | 0.827; 114, 0; 348 | **0.916**; 114, 0; 467 | 0.913; 114, 0; 467 | 0.913; 114, 0; 467 |
| calendar | 0.671; 243, 4; 312 | 0.949; 243, 4; 469 | **0.953**; 239, **0**; 469 | **0.953**; 239, **0**; 469 |

run21 is run20's prompt and code plus two program rules. **An identifier keeps a rule only as a lookup in the policy's register**, or when a policy row names it: the eleven GitHub issue and pull-request numbers (three of them rated by size in run20, pull request 600 at 5) and a calendar attachment's file id are dropped, and the noise dropped rises to 116 of 122. **A left-out input is rated at most 3** unless a policy row calls leaving it out risky: the server's default is an ordinary call. The second rule is applied at run time too, so it also rescored run20: its slack row was 0.895 with 144 harmless calls at 4-5, 30 of them `channels_me` calls with no `limit` rated at the default 100. Two more policy scenarios pass (a `.env` written to a repository, twenty files read at once), from the model's answers moving, not from the two rules; for the same reason github has 10 more harmless calls at 4-5 (issue searches naming a perimeter repository) and calendar has 5 inputs without a complete rule against 2.

"Usable rule" counts only inputs whose rule passed the check (`grade_stage1.py` also counts a `broken` one). The tool-only baseline is AUC 0.623, 0.653 and 0.647. Run20 against run13: the same scenarios pass; the held-out servers keep all 20 important inputs again (the override bug of run13 is fixed); the program now drops three short choice lists the model had padded with an invented fifth value (`channel_types` twice, `usergroups_me.action`); and it keeps a few unimportant inputs run13 dropped (`head` and `tail` on the file share, two GitHub pull-request numbers). Every harmless call scored 4 or 5 still comes from the policy: reads of the repositories the scan rates 4 or 5, four-month calendar windows (the policy calls months unusual), reads of slack's trial-operations channel (scanned 4).

**Shorter prompts did worse with this model.** A rewrite to half the length (run17, run18: data in tags first, each rule once, six examples from other products, a reply schema) passed 24 of 35 policy scenarios and 8 or 9 of 14 common-knowledge ones, and left 41 to 64 inputs without a complete rule: qwen2.5 32B wrote windows from now, used asset names as path words and left the safe levels empty. Applying only the review's wording fixes to run15's prompt (run19) still lost ground (25/35, 12/14; calendar AUC 0.85). Run20, the same code with run13's exact prompt, matches run13: the code is not the cause, the wording is. Any prompt change moves the greedy answers by several scenarios and up to 0.1 AUC, so wording fixes need to be tried one at a time, each over more than one run.

## The step

One prompt, [tool-input-levels.md](../../../docs/standards/tool-input-levels.md), run by [`scripts/derive_input_levels.py`](../../../scripts/derive_input_levels.py) once per tool, ten inputs per call:

1. Before asking, the program answers `null` for every input with fewer than five possible values (a boolean, a short enum), for paging, sorting and time-zone inputs, and for a record number no policy row names (`issue_number`, `pull_number`: never an asset's name; from run21), gives an email-address input the fixed email ladder, and marks the two ends of a read window (`timeMin` and `timeMax`, `after` and `before`) with `window_with`. Every batch carries the tool's other inputs as context.
2. The model names what each remaining input decides (`effect`), then gives a rule or `null`. The reply is held to a JSON schema by the server (from run17).
3. The program repairs and checks each rule (`mcp_security.input_rules.repairs`). An asset-name rule gets the policy's whole asset register as its table, every asset of the server with its scanned level whatever the tool, and keeps the model's name words only at levels no asset reaches (from run11). A text rule gets the credential words at level 5 (from run11). Name words that contradict a listed asset they are part of are dropped. Then `rule_problems(..., all_levels=True)` asks for the right shape and an entry of its own at each level 1 to 5 (the fallback `default` does not count); a window end must be rated by the window's length; placeholders copied from the prompt are rejected; an override may only raise an asset of the register; a `values` rule must list values the input really takes, and with fewer than five it becomes `null`; a level whose ranges lie outside the schema's minimum and maximum does not count (from run17). From run21: an identifier (`eventId`, `fileId`) keeps a rule only as a lookup in the policy's register, or when a policy row names it, else it is `null`; and a `when_absent` above 3 is lowered to 3 unless a policy row calls leaving the input out risky.
4. An input with no answer or a failed rule is asked again with its last rule and what failed (including any name words the program dropped and why), so the model adds the missing levels to its own rule; sampled, up to six passes in all.

No importance stage, no rank, no votes.

## The five levels

| Level | Meaning |
|---|---|
| 1 | The safest realistic value |
| 2 | Safe |
| 3 | Ordinary |
| 4 | High: a sensitive target, a lot at once, outside working hours |
| 5 | Critical: restricted or credential-bearing, bulk, or leaving the organization |

An ordinary call gets 1 to 3 from every rule, and a value no entry matches is ordinary, so a rule's `default` is 1 to 3. Time of day: peak working hours are 1 and 2, late night 5.

## When an input gets none

1. It cannot take five levels: a true or false switch, a choice of two to four options. Decided by the program from the schema; the model answers the same for short lists the schema does not enumerate.
2. It does not touch an asset (`effect: none`): presentation, sorting, a time zone, a reminder, a page number, bookkeeping, custom metadata, a record inside an asset another input picked (an issue number, an event id).
3. It only narrows the call: an exclude list, the first or last lines of a file read anyway.
4. It is a label next to the main content: a title or a commit message when the tool has a body.
5. Its levels would need facts nobody has: who a person is behind an opaque user id.

## Where a level comes from

| Source | For |
|---|---|
| **scan** | an asset name: the asset's 1 to 5 level from the v5 scan of the policy's asset register, looked up in the whole register whatever the tool |
| **policy** | an email address: the fixed ladder own domain 1, partner 2, no readable domain 3, another organization 4, a personal mailbox or a flagged domain 5. The policy makes its own people the normal audience and any outside address unusual, and gives the domain lists. Also `overrides`: an asset the policy prohibits for this tool (a write to the crew roster) raised above its scan level |
| **program** | the credential words at 5 in every text rule |
| **agent** | everything else: numbers, windows, times, words |

From run11 the model gets everything the policy says about the tool: besides the description, the workflow and the assets, the special-value rules and the normal and unusual baseline rows that name it. It follows them where they speak; numbers and cut-offs the policy does not give are its own. What is neither in the policy nor common knowledge is left out: no rule can know it (see `scenarios.json`, `out_of_scope`). Runs 1 to 10 did not send the two tables.

## Rule kinds

| Kind | For | Five levels from |
|---|---|---|
| `ranges` | numbers, lengths, a window's span, hour of day, hours from now | five or more ranges |
| `register` | a value that names a listed asset | the assets' scanned levels plus name words for the missing levels |
| `keywords` | paths, queries, bodies, commands | five word groups |
| `values` | a choice of five or more options | five or more listed values |
| `email` | addresses | the fixed ladder |

## Report and review

- [static-scan-report.md](static-scan-report.md): the static scan in one report: purpose, steps, decisions, tests, results, gaps.
- [prompt-review.md](prompt-review.md): the exact prompt with line numbers and one real call's data, for flagging mistakes, with twelve findings.

## How the prompt works

[prompt-explained.md](prompt-explained.md): the steps, what the model is given, and real calls from run15 exactly as they went to the model and came back (every call of a run is saved under `logs/calls/` from run14).

## Checks without reading every rule

`scripts/check_input_levels.py --run <folder>` writes `<folder>/checks.md`:

1. **Scenarios** ([scenarios.json](scenarios.json)): 57 hand-written pairs, the same call with one input moved from harmless to risky, each marked by what says it is risky: the policy (35, the line quoted; 7 of them filesystem, from run14), common knowledge (14), or neither (8, listed but not counted). A pair passes when the risky call scores higher, and at least `risky_at_least` when given (5 for what the policy prohibits).
2. **Real calls**: the inputs whose value alone tells risky sessions from harmless ones in the labelled corpus, with their status in the run and how well their rule does on the same calls. A dropped input here is a missed one. Most corpus values never vary (the owner is always the account, the path almost always `README.md`), so this screens rather than grades.

run10 baseline: policy scenarios 13 of 28, simple 13 of 17. Its failures: the four most-used asset inputs had no rule (`get_file_contents.repo`, `create_branch.repo`, `create-event.calendarId`, `delete-event.calendarId`, 504 real calls), credential paths (`.env`, `id_rsa`) and a posted password scored 3, a search with no channel filter and searches for `DSMB` or `unblind` scored 3, and the prohibited writes to the crew-roster and maintenance calendars scored their scan level 3.

run13: policy 27 of 28, simple 16 of 17. Still failing: a search for `DSMB` (in the unblinding channel's description, not in the rule) and an overwrite of `.env` on the filesystem server (`write_file.path` has no rule).

## Grading

Against v12's reference verdicts (`../v12/grading/`): `grade_stage1.py <run folder>` counts an input as kept when it has a rule, and gives the totals with and without the inputs v13 drops by design (fewer than five choices). `compare_end_to_end.py run11 reports/experiments/v13/runN` scores the 3,000 real labelled calls.

## Run history

| Run | Change | Result |
|---|---|---|
| run1 | first one-step prompt: five `null` cases (no asset, a record, under five values, text next to the main content, unknowable) | important kept 78/156 (run11: 147/156), noise dropped 116/122, held-out noise 2/9. The model answered `text next to the main content` 131 times, for `repo`, `owner`, `channel_id`, `content`; 44 rules never filled every level (asset-name rules left the levels no asset reaches empty); fragments copied from the prompt's examples. End to end, github 0.672 (run11 0.579, no benign call at 4-5), slack 0.621 (0.852), calendar 0.596 (0.654) |
| run2 | the model first names the `effect` (run11's list); three narrow `null` exceptions and a never-`null` list; switches decided by the program; each tool told which levels its name words must add; "do not copy the examples" | important kept 150/156, noise dropped 107/122, held out 20/20 and 5/9 (`head`, `tail` kept). But 89 inputs stayed `broken`, mostly asset-name rules still leaving levels empty. End to end: github **0.726**, slack 0.601, calendar 0.591 |
| run3 | JSON mode; a fourth `null` exception (fewer than five values with no schema enum); single-date measure; a worked name-word example; head, tail, reminders and custom properties named | important kept **152/156**, noise 110/122, held out 20/20 and 7/9; `broken` down to 56, the failed rules showing one or two levels left out. End to end: github **0.747**, slack 0.786, calendar 0.553 (start and end of a window rated as two single dates) |
| run4 | a re-ask hands back the rule written last time and asks to add the missing levels; entries written from level 1 up; four passes; single dates only with no end input | `broken` down to **4**: 224 of 228 kept inputs have a complete rule. Important kept 150/156, noise 102/122, held out 20/20 and 5/9. End to end: github 0.633, slack **0.840**, calendar 0.616. Name words reused pieces of the listed asset names at the wrong level (`scada` at 2 while the asset is 5); `search_code.q` copied the example fragments word for word |
| run5 | example fragments replaced by placeholders, which are rejected if copied; name words checked against the listed assets they are part of (within one level); a final list of always-`null` inputs | keep decisions the best yet: important 149/156, noise 110/122, held out **20/20 and 9/9**. But the name-word check left the key asset rules `broken` (`conversations_history.channel_id`, which sets the level of 447 slack calls; eight github `repo` and `owner` rules), and end to end fell to github 0.498, slack 0.587, calendar 0.621 |
| run6 | contradicting name words are dropped by the program instead of rejecting the rule; read windows paired by name and checked for `span_hours`; email reads addresses inside attendee records | keep decisions the best yet: important 149/156, noise **115/122** (run11 113), held out 20/20 and 9/9. Calendar **0.671** (run11 0.654). But 23 rules still `broken`, nearly all one level short: the model re-added the same contradicting words, which were dropped again. Github 0.508, slack 0.631 |
| run7 | a re-ask also names the name words the program dropped and why; empty groups removed; up to six passes | slack **0.851** (run11 0.852, with 97 benign calls at 4-5 against 135); calendar 0.576 (benign list-events read about four months, which the agent rated 5). The github part crashed on a malformed group (fixed: model replies are now never trusted to have every key) |
| run8 | the crash fixed; `default` must be 1 to 3 (an unmatched value is ordinary). Scored with the policy's email ladder (outside addresses 4) | important 149/156, noise 111/122, held out 20/20 and 9/9; 8 rules `broken`. End to end: github 0.587, slack 0.827, calendar **0.715** (run11 0.654). Misuse code searches for `secret OR token` matched no fragment: the agent had put `bidding` at 5 and no credential words |
| run9 | credential words always at 5 in text that can carry them; window example in plain units | github **0.695**, slack **0.846** (86 benign calls at 4-5, run11 135), calendar 0.618; important 146/152, noise 109/120, held out 20/20 and 9/9. Both jobs landed on one node and shared one ollama port, so two github tools failed at the end (fixed: the port comes from the job id). Calendar windows: the agent wrote 365 and 1095 meaning days, in an hours measure |
| run10 (frozen before run13) | hours spelled out (a day 24, a week 168, a month 720, a year 8760); only entries a value can reach count toward the five levels (a range hidden by earlier ones, a repeated value); ollama port per job | see Results. 198 of 209 kept inputs complete; important 150/156, noise 114/122, held out 20/20 and 9/9; github 0.640, slack 0.827, calendar 0.671 |
| run11 | the model gets everything the policy says about the tool (special-value rules and baseline rows again, the rest of the register); asset-name rules use the policy's whole register with the model's guessed name words dropped; credential words added by the program to every text rule; overrides for what the policy prohibits; scenario and real-call checks | scenarios: policy **25/28** (run10 13), simple **16/17** (13). The four asset inputs run10 left without a rule have one; the crew-roster and maintenance calendars raised to 5 for writes. 195 of 197 kept inputs complete; important 151/156, noise 109/122, held out 20/20 and 7/9 (`head`, `tail`). End to end: calendar **0.953** (run10 0.671), slack 0.827, github 0.646 but 333 benign calls at 4-5 (run10 70): every one reads a perimeter repository, which the policy's baseline calls unusual. Still failing: a slack search with no channel filter (the policy calls it risky; the model left `when_absent` empty), and searches for `DSMB` and `unblind` (the rule has `unblinding` at 4, which `unblind` does not contain) |
| run12 | an input a policy row calls risky when left out ("with no `filter_in_channel`") needs a rule and `when_absent` 4 or 5, or it is sent back; fragments written as short stems (`unblind`, not `unblinding`) | scenarios: policy **27/28**, simple 16/17. slack **0.919** (run11 0.827): a search with no channel filter now scores 4. calendar 0.949, github 0.648. 218 of 224 kept inputs complete; important 152/156, noise 113/122, held out 20/20 and 9/9 |
| run13 (frozen before run20) | the prompt's placeholder phrases are rejected also when copied without their brackets (`safest words`) | identical to run12 except two filesystem rules that had copied the placeholders, now rewritten. See Results |
| run14 | the filesystem catalog reads a policy: `fs_corp_filesystem` from [server-policies.md](../../../docs/mcp-tools/server-policies.md), rewritten in the abstract template like the other three; on a server with no policy an override is dropped, not the rule; every model call saved | every filesystem path became a `register` rule with no name words: the share's assets are kinds of data (`security-keys`), which no path contains, so every path scored 3 and all 8 filesystem policy scenarios failed |
| run15 | `register` only when the values are the assets' own names; `keywords` for kinds of data, with the policy's words | filesystem policy scenarios 3 of 8; policy 29/36 overall (run13 29/36), simple 13/14 (run13 14/14). Held out 18/20 with a usable rule. Some path rules still `register`, others use the asset ids as words. The new sentence also moved other answers: slack lost `unblind`, sqlite's `write_query` turned around. Not frozen |
| run16 | an earlier draft of the short prompt, started by a submit that had been stopped | cancelled after 16 minutes; partial logs kept |
| run17 | the prompt rewritten to half the length: data in tags first, each rule once, six examples from other products, the reason before the rule, a reply schema enforced by the server. Code: paging, sorting and time-zone inputs and email addresses decided by the program; a `values` rule must list real values (fewer than five means none); levels outside the schema's bounds do not count; every batch sees all the tool's inputs; a left-out input is rated at its default; words match at word starts; a credential-shaped path is 5 under any rule; one end of a window is measured to now | worse: policy 24/35, simple 8/14, 64 inputs without a complete rule |
| run18 | run17 plus the read-window rule, "words that appear in values, not asset names", "start with the safest values" and a three-line check | still worse: policy 24/35, simple 9/14, 41 without a complete rule; event descriptions dropped |
| run19 | run15's prompt with only the review's wording fixes, the server-specific items removed, the data in tags; the new code | policy 25/35, simple 12/14; AUC github 0.700, slack 0.882, calendar 0.846 |
| run20 (frozen before run21) | run13's exact prompt with the new code (`MCP_INPUT_LEVELS_PROMPT`) | see Results |
| **run21** (frozen) | run20 plus two program rules: an identifier keeps a rule only as a register lookup or when a policy row names it; a left-out input is rated at most 3 unless a policy row calls it risky | see Results |

## Known gaps

- **Benign by the corpus, unusual by the policy.** See Results: the remaining false alarms are where the corpus labels and the policy disagree. A deployment that finds them wrong changes the policy (or its scan levels), not the rules.
- **The normal workflow does not lower a level.** Slack's policy calls summarizing a trial-operations thread normal, yet `vireo-trial-ops` is scanned 4, so those reads score 4. Overrides only raise.
- **What the policy does not say, and is not simple, is left out** (`out_of_scope` in `scenarios.json`): an outside GitHub organization (the policy lists none of its own), a CI workflow path, a one-letter or `@` search that matches everyone, `/etc`, which sqlite table is sensitive, the public holiday calendar's id (missing from the deployment's id table).
- **Words from an asset's description are the model's to carry over.** The policy says `vireo-unblinding` holds DSMB coordination; the search rule has `blind` at 5 but no `DSMB`.
- **Payroll on the file share stays at 3 (accepted).** The filesystem policy says reading payroll is prohibited, but not where payroll is or what its files are called (`sensitive/financials/payslips_q1.csv`); that scenario is `out_of_scope`. A later layer that learns file-to-asset links from traffic may catch it.
- **Email needs the policy's lists.** No organization's own or partner domains are recorded, so every non-personal address scores 4 and is flagged unresolved; a deployment fills `org_domains`, `partner_domains`, `flagged_domains`.
- **More noise kept than run10** (113 vs 114 of 122 dropped on the tuned servers; reminder minutes, extended properties, `get-current-time.account`): an asset-name rule is complete as soon as the register is, and a text rule needs only levels 1 to 4. These inputs rarely carry a risky value.
- **5 inputs have no complete rule in run20**: `github.create_or_update_file.path`, `github.create_or_update_file.content`, `slack.usergroups_users_update.users`, `calendar.create-event.attachments[].fileUrl`, `calendar.create-events.events[].attendees`.

## Commands

```bash
sbatch scripts/derive_input_levels.sbatch                       # all five servers, next free runN
# rerun an earlier run's prompt with the current code
sbatch --export=ALL,MCP_INPUT_LEVELS_PROMPT=$PWD/reports/experiments/v13/run13/prompt-levels-AS-RUN.md scripts/derive_input_levels.sbatch
python3 reports/experiments/v12/grading/grade_stage1.py reports/experiments/v13/runN
python3 reports/experiments/v12/grading/compare_end_to_end.py run11 reports/experiments/v13/runN
python3 scripts/render_input_rule_levels.py --run reports/experiments/v13/runN
uv run python scripts/check_input_levels.py --run reports/experiments/v13/runN
uv run python scripts/input_level_stats.py --run reports/experiments/v13/runN   # runN/input-statistics.md
```

## Expert survey

[validation-survey-proposal.md](validation-survey-proposal.md): the survey step that checks which inputs the scan keeps (eight per server, five for SQL, live on the survey's `main`), with its answer key [survey-input-key-run21.json](survey-input-key-run21.json).

## Few-shot ratings

[rating-sheet-run13.md](rating-sheet-run13.md): the same 23 inputs as [rating-sheet-run10.md](rating-sheet-run10.md), with run13's rules, for the annotator to mark right or wrong. The marked rows become the prompt's few-shot examples and a baseline for later runs.

## Layout of a run

```
runN/
├── prompt-levels-AS-RUN.md   the prompt as run, with its sha256
├── <server>.json             every input: status (rule, null, broken, unanswered), rule, reason
├── eval_<server>.json, .md   the 3,000 labelled calls scored with these rules
├── rule-levels.md            every kept input's five levels in one table
├── checks.md                 scenario pairs and the real-call screen
├── input-statistics.md       counts per server, tool and input; why inputs were dropped
└── logs/                     per-server logs; rejected/ holds any reply the runner could not use;
                              calls/ every model call, the prompt as sent and the reply (from run14)
```
