# Static Scan of Tool Inputs (v13): Report

The static scan reads every tool of an MCP server once, at design time, and writes a rule for each tool input that turns the input's value into a risk level from 1 (safest) to 5 (critical). The rules form a lookup table for the dynamic layer: when an agent calls a tool, the table gives each argument its level with no model on the call path, and the call gets the highest one. The server is the protected asset; the agent calling it is the threat.

## In short

- **One prompt, one model step per tool.** The model says what each input decides, then writes a rule that fills all five levels, or no rule. An input is kept when it gets such a rule.
- **The policy decides what it speaks to; the model decides the rest.** Which assets are riskier, what is prohibited and what is unusual come from the organization's policy. The cut-offs the policy does not give (how many messages is a lot, which hours are night) are the model's. Fixed parts (the asset table, the secret words, the email ladder) and every check are done by code.
- **What the policy does not say and is not common knowledge is left out.** No rule is built on a guess.
- **Result (run21, frozen):** 211 of 419 inputs kept with a complete rule (6 more kept without one); 30 of 35 policy scenarios and 14 of 14 common-knowledge scenarios pass. On 3,000 real labelled calls, slack separates risky from harmless calls at AUC 0.91 and calendar at 0.95; github at 0.67. The full prompt and a one-page summary: [run21-prompt-and-summary.md](run21-prompt-and-summary.md); counts per tool and input: [run21/input-statistics.md](run21/input-statistics.md).

## What it is for: one call

An agent calls slack `conversations_history` with `channel_id = vireo-unblinding`, `limit = 20`, `cursor = abc`.

| Input | Rule from the table | Level |
|---|---|---|
| `channel_id` | the policy's asset list: announcements 1, eng-platform 3, trial-ops 4, unblinding 5 | **5** |
| `limit` | under 10 → 1, 10–50 → 2, 50–100 → 3, 100–500 → 4, 500 and up → 5 | 2 |
| `cursor` | no rule: it only pages through results | – |

The call's level is 5, set by `channel_id`, and the dynamic layer can block it or ask a human.

## How it works

| # | Who | Step |
|---|---|---|
| 1 | code | Inputs with fewer than five possible values (true/false, 2 to 4 choices) get no rule, without asking. The two ends of a read window are paired |
| 2 | code | The policy block for the tool: its description and normal workflow, the assets it reaches with their level from the v5 scan, the policy's rules and normal/unusual rows for the tool, the rest of the asset list |
| 3 | **model** | For each input, two questions: what does it decide (which asset, how much, who receives it, what action, when, what is sent, nothing)? Then a rule from 1 to 5, or no rule |
| 4 | code | Repairs: the whole asset list goes into every asset-name rule; the secret words (`password`, `.env`, `id_rsa` …) at 5 into every text rule |
| 5 | code | Checks: all five levels filled, a value that matches nothing is ordinary (1 to 3), a window rated by its length, no copied placeholders, the policy's "left out" rows followed |
| 6 | **model** | Inputs that failed are asked again with their last rule and what failed, up to six passes |

The first question is what makes the second work. Without it (run1) the model said "no rule" 131 times, even for repositories and channels, and kept 78 of 156 important inputs; with it (run2), 150 of 156. It also picks the kind of rule: an asset name, number ranges, words in a text, a list of choices, or the email ladder.

The prompt is explained, with real calls as sent and received, in [prompt-explained.md](prompt-explained.md). The exact text, with line numbers for review, is in [prompt-review.md](prompt-review.md).

## Decisions taken

| Decision | Why |
|---|---|
| Every kept input has a rule that fills all five levels | a level that can never occur is not a scale; v12's rules filled none |
| Inputs with fewer than five values get no rule | they cannot be rated 1 to 5. The cost: some critical switches are lost (`private=false` on a new repository) |
| One step instead of v12's three prompts and three votes | fewer steps, same five levels; 138 model calls for the five servers in run21 (counted in its call log) instead of v12's 345; two jobs of about 12 minutes, one GPU each |
| The policy decides which asset is riskier, what is prohibited and what is unusual; the model decides the cut-offs | the organization knows its assets; how many items is "a lot" is general |
| What the policy does not say and is not simple is left out | a rule built on a guess cannot be explained. 8 of the 57 scenarios are of this kind and are listed, not counted |
| Peak working hours are levels 1 and 2, night is 5 | the time of a meeting or a change |
| Email: own domain 1, partner 2, no readable domain 3, another organization 4, personal mailbox or a flagged domain 5 | only what an address shows, or the policy lists, can be known |
| The filesystem server reads the policy of CBG's corporate share | the repo already had it (`fs_corp_filesystem`); rewritten in the short template, nothing added |
| Payroll on the file share stays at 3 | the policy says payroll is prohibited to read, but not where it is or what the files are called (`sensitive/financials/payslips_q1.csv`). Accepted gap; a later layer that learns file-to-asset links from traffic may catch it |

## How it was tested

1. **57 scenario pairs** ([scenarios.json](scenarios.json)): the same call with one input moved from harmless to risky. 35 rest on a line of the policy (quoted), 14 on common knowledge, 8 on neither (listed, not counted). A pair passes when the risky call scores higher.
2. **3,000 real labelled calls** from live sessions on github, slack and calendar (benign, misuse, malicious): does the level separate risky sessions from harmless ones?
3. **A reference list** of which inputs matter, one annotator's judgement, counted strictly: an input counts as kept only with a rule that passed every check.
4. **Coverage**: all 419 inputs of the five servers have a row; none is missing.

## Results

| | run10 | run13 | run20 | **run21 (frozen)** |
|---|---|---|---|---|
| Prompt | run10's | run13's | run13's, with the newer code | run20's, plus two program rules |
| Kept inputs with a complete rule | 198 / 209 | 218 / 224 | 217 / 222 | 211 / 217 |
| Policy scenarios pass | 15 / 35 | 28 / 35 | 28 / 35 | **30 / 35** |
| Common-knowledge scenarios pass | 13 / 14 | **14 / 14** | **14 / 14** | **14 / 14** |
| Important inputs with a usable rule (github, slack, calendar) | 143 / 156 | **151 / 156** | 145 / 156 | 144 / 156 |
| Important inputs with a usable rule (filesystem, sqlite) | **20 / 20** | 16 / 20 | **20 / 20** | **20 / 20** |
| Unimportant inputs dropped (github, slack, calendar) | 114 / 122 | 113 / 122 | 112 / 122 | **116 / 122** |
| AUC github, slack, calendar (0.5 = chance; tool-only 0.62, 0.65, 0.65) | 0.64, 0.83, 0.67 | 0.65, **0.92**, 0.95 | **0.67**, 0.91, **0.95** | **0.67**, 0.91, **0.95** |
| Harmless calls at 4–5, of 500 (github, slack, calendar) | 70, 114, 243 | 331, 114, 243 | 317, 114, 239 | 327, 114, 239 |
| Harmless calls at 5, of 500 | 22, 0, 4 | 86, 0, 4 | 86, 0, **0** | 86, 0, **0** |
| Risky calls at 4–5, of 500 | 238, 348, 312 | 406, 467, 469 | 406, 467, 469 | 406, 467, 469 |

All four are scored with the current code; run20's slack column changed with run21's left-out rule (it was 0.90 with 144 harmless calls at 4–5), because that rule also applies when scoring. Run21 is frozen: run20 plus two program rules, an id keeps a rule only as a lookup in the policy's register (the eleven GitHub issue and pull-request numbers are dropped), and a left-out input is rated at most 3 unless a policy row calls it risky. Compared with run13, run20 passes the same number of scenarios, keeps all the held-out servers' important inputs again, and lets no harmless calendar call reach 5; it keeps six fewer important inputs on the tuned servers, three of them short choice lists the program now drops on purpose (below).

Per tool (run21): a tool has 5.8 inputs on average and keeps 2.9. Of the 419 inputs, 211 are kept with a complete rule; 117 are dropped by code (fewer than five values, paging, sorting, time zone, record numbers, ids the register cannot tell apart), 85 by the model (a label next to a body, a record inside a chosen asset, presentation, metadata), and 6 never got a complete rule. The full counts are in [run21/input-statistics.md](run21/input-statistics.md).

**Can the prompt be simpler?** Not with this model, so far. A rewrite to half the length, built on published prompt-writing guidance (data in tags first, each rule once, six examples from other products, the reason before the rule, a reply schema), passed 24 of 35 policy scenarios and 8 to 9 of 14 common-knowledge ones, and left 41 to 64 inputs without a complete rule (run17, run18). Only the reviewer's wording fixes on the working prompt still lost ground (run19: 25/35, 12/14). The working prompt is long because each part fixed a mistake this 32B model actually made. Wording fixes are kept for later, to be tried one at a time over several runs, or with a larger model.

## Known gaps and accepted limits

- **Harmless by the test traffic, unusual by the policy.** Every harmless call scored 4 or 5 comes from the policy: reads of the four repositories the scan rates 4–5, four-month calendar windows (the policy calls months unusual), reads of slack's trial-operations channel (scanned 4). Changing that is a policy decision, not a rule decision.
- **The normal workflow cannot lower a level.** Slack's policy calls summarizing a trial-operations thread normal, yet those reads score 4. Overrides only raise.
- **The filesystem policy names kinds of data, not files.** Its assets (`security-keys`, `payroll-records`) never appear in a path, and the model still makes some path rules asset-name rules. 3 of 7 filesystem policy scenarios pass in run20: reading the private key, reading `.env` and moving the key score 5; twenty files in one read, overwriting product source, editing the audit log and listing the security folder do not.
- **Switches are lost by design**: `private=false`, calendar `visibility`, `guestsCanInviteOthers`, `sendUpdates`.
- **Short choice lists are dropped.** A list with fewer than five real values cannot fill five levels; the model used to pad one with an invented value (`other_type`), and the program now drops it instead (`channel_types`, `usergroups_me.action`).
- **Five inputs have no complete rule**, among them github `create_or_update_file.path` and `.content` (a level-2 entry missing after six passes).
- **Any change to the prompt moves other answers.** The first pass is greedy, so the same prompt gives the same table, but one new sentence changes several scenarios and up to 0.1 AUC elsewhere (run15, run19).
- **Email needs the policy's domain lists.** None are recorded, so every non-personal address scores 4.

## History

| Version | Design | Outcome |
|---|---|---|
| v10, v11 | one label per input; then many flags per input | too complicated to explain |
| v12 | three prompts: is it important (three votes), a check, the rules | 0 of 237 rules filled all five levels |
| v13 run1–10 | one prompt; every rule fills all five levels; code checks and re-asks | run10: 198 of 209 complete |
| v13 run11–13 | the model gets the policy's rules and baseline; the whole asset list in every asset-name rule; secret words by code; the policy's "left out" rows checked | run13 frozen: policy scenarios 13 → 27 of 28 (on the first 28) |
| v13 run14–15 | a policy for the filesystem server; every model call saved | filesystem partly works (gap above) |
| v13 run17–19 | a prompt half the length, then only wording fixes; more checks moved into code | all worse than the working prompt with this model |
| v13 run20 | the working prompt (run13's) with the new code | frozen until run21 |
| v13 run21 | run20 plus two program rules: ids only as register lookups, left-out inputs at most 3 unless the policy calls it risky | frozen: policy scenarios 30 of 35, unimportant inputs dropped 116 of 122 |

Details per run: [README.md](README.md).

## Next steps

1. Validate run21 with experts: a short "Inputs That Change the Risk" step per server in the survey, eight inputs each (five for SQL), live on the survey's `main` ([validation-survey-proposal.md](validation-survey-proposal.md), answer key [survey-input-key-run21.json](survey-input-key-run21.json)).
2. Wording fixes from [prompt-review.md](prompt-review.md) one at a time, each over more than one run, kept only if nothing gets worse; "never invent a value" is now enforced in code.
3. Try the short prompt with a larger model: whether the long prompt is needed may depend on the model.

## Files

| File | What it holds |
|---|---|
| [prompt-review.md](prompt-review.md) | the exact prompt with line numbers, one real call's data, and the twelve findings |
| [prompt-explained.md](prompt-explained.md) | the steps and three real calls as sent and received |
| [README.md](README.md) | the full record: every run, the grading, the commands |
| [scenarios.json](scenarios.json) | the 57 scenario pairs |
| `run21/rule-levels.md`, `run21/checks.md` | the frozen table and its checks |
| `run21-prompt-and-summary.md`, `run21/input-statistics.md` | the full prompt with a summary; counts per server, tool and input |
| [docs/standards/tool-input-levels.md](../../../docs/standards/tool-input-levels.md) | the prompt |
| [docs/mcp-tools/server-policies-abstract.md](../../../docs/mcp-tools/server-policies-abstract.md) | the four policies the scan reads |
