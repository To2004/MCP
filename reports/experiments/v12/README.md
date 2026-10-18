# v12: which tool inputs matter, and run-time rules for them

> Superseded by [v13](../v13/README.md): one step instead of two, and every rule fills all five levels (none of run11's rules did).

v10 gave every input one label; v11 stacked many flags on each input and became too complicated to explain. v12 asks two plain questions per tool. First: which inputs can change how risky a call is? Second: for those, how does a value turn into a level? The answer to the second is a rule a program applies at run time, with no model on the call path.

## The two stages

| Stage | Prompt | Reads | Produces |
|---|---|---|---|
| 1. Importance | [tool-input-importance.md](../../../docs/standards/tool-input-importance.md), then [tool-input-importance-check.md](../../../docs/standards/tool-input-importance-check.md) | the tool, all its inputs, the policy slice for the tool | `important` yes or no per input, with a reason |
| 2. Rules | [tool-input-rules.md](../../../docs/standards/tool-input-rules.md) | the important inputs, the other inputs as context, the policy slice with each asset's scanned level | one rule per important input, turning a value into a level 1 to 5 |

Both run once per tool at design time. At run time, [`mcp_security.input_rules`](../../../src/mcp_security/input_rules/README.md) applies the rules to a call's arguments and returns the highest level among its inputs, and which input set it.

### Stage 1: two questions, decided by code (frozen at run11)

For each input of a tool, the model answers two questions; the prompt is product-neutral and its examples come from other domains (payments, storage, email, SQL, HR).

1. **Does the input affect an asset?** Yes when its value decides `which` asset (the asset itself, not a record inside it), `how_much` of it (amounts, counts, limits, page sizes), `who` receives it, is notified or gains access, the `action` done to it, `when` (a read window or when a change takes effect), or what is `carried` (a body, a message, a query that runs). No for presentation, ordering, pagination position, tags, reminders, bookkeeping, and record ids inside an asset another input already chose.
2. **Rank its influence from 1 to 5** by comparing the call at the input's safest and riskiest realistic value.

The program keeps an input when question 1 is yes **and** the rank is 3 or more. Three passes (majority for question 1, median rank for question 2); inputs no pass answered are asked again in small batches; inputs the policy names in a special-value or baseline row are always kept.

Graded against one annotator's verdicts (`grading/`): on github, slack and calendar it keeps 175 of 185 important inputs and drops 113 of 122 that should go; on the held-out filesystem and sqlite catalogs, which no prompt was tuned on, 21 of 21 and 9 of 9. A typical tool has about four inputs and keeps two or three.

### Stage 2: rules on five levels

| Level | Meaning |
|---|---|
| 1 | No concern: safer than a normal call. |
| 2 | Low. |
| 3 | Normal: what an ordinary call passes. The neutral point. |
| 4 | High: a sensitive target, a lot at once, outside normal hours or audience. |
| 5 | Critical: restricted or credential-bearing, outside the organization, bulk, prohibited by policy. |

Because 3 is the neutral point, the call's level can lower a previously computed score (below 3), leave it (3), or raise it (above 3).

| Rule kind | For | Example |
|---|---|---|
| `ranges` | numbers, lengths, times (hour of day, weekday, span between two inputs, hours from now) | `per_page` above 100 is 4 |
| `register` | a value that names one of the organization's assets | `repo=helios-scada-gateway` is 5, the asset's scanned level |
| `keywords` | paths, names, queries, text | a path containing `.env` or `id_rsa` is 5 |
| `values` | fixed choices and switches | `private=false` is 5 for Helios |
| `domain` | addresses | an external attendee is 5 |

Every rule also says what happens when the input is left out (`when_absent`): a search with no channel filter searches everything. Each rule is checked when it is written (levels 1 to 5, ascending ranges, a known measure, a real sibling input); an input whose rule is missing or broken is asked again, alone, up to three rounds.

The levels a `register` rule returns are not written by the model: they are the 1 to 5 asset sensitivities from the v5 scan (`v5/five_level_v2_policy_v5r_nacombo`). All 50 assets across the three organizations have one.

### Where the other levels come from

1. **The policy**, when it speaks to the input: a baseline row (Table 4), a special-value rule (Table 3), or the listed assets the value reaches.
2. **The schema**, when it states bounds.
3. **The model's own judgment**, marked `inferred`: approximate, the direction matters more than the exact cut.

Passing an empty policy (`--no-policy`) gives the ablation that shows what the policy adds.

## Policy inputs

The three live organizations in the abstract template: [server-policies-abstract.md](../../../docs/mcp-tools/server-policies-abstract.md) (`github_helios`, `slack_vireo`, `calendar_aurora`), on the real captured tool lists of `@modelcontextprotocol/server-github` (26 tools), `slack-mcp-server` (16) and `@cocal/google-calendar-mcp` (13). Table 4 rows marked `draft` were proposed by the author of the document and are not ground truth.

## Run history

| Run | Design | What happened |
|---|---|---|
| run1 | one prompt: label and three bands for every input | finished; 2 github tools failed. Only 37 of 186 `RANGE` bands had numbers and every `ASSET` band was prose, so none of it could be looked up at run time |
| run2 | one prompt with importance added | cancelled after 3 minutes, no results |
| run3 | stage 1 once (yes or no), then stage 2 as labels and three bands | stage 1 answered every tool. Stage 2 failed on many tools; the saved rejected replies showed 46 of 47 were rejected only for a missing `confidence` field the runner required but never used, and the rest for a path spelled `account[]` instead of `account`. Stage 1 dropped run1-`RANGE` page and page-size inputs correctly, found risk switches run1 had called `IGNORE` (`create_repository.private`, `modificationScope`, `sendUpdates`, `anyoneCanAddSelf`), but answered `account` inconsistently across calendar tools and dropped the slack search `limit` |
| run4 | stage 1 with three votes and the check; stage 2 as run-time rules | stage 1 kept 344 of 384 inputs (recall-first). Stage 2 rules scored the 3,000 real labelled calls: slack separated well (AUC 0.83 against 0.65 for a tool-only baseline), github and calendar did not, because of wrong rules on important inputs (an owner rated as an asset, read windows measured from now) |
| run5 | run4 with stage 2 fixes | cancelled before results |
| run6 | stage 1 with the extremes test (keep only if the riskiest value is two levels above the safest) | precise but missed inputs: important kept 171/185, noise dropped 112/122 |
| run7 | run6 plus policy-named keep and a cross-tool consistency pass | important 179/185, noise 106/122; the consistency pass spread one wrong keep (a page number) to five tools |
| run8 | run7 wording plus held-out servers | cancelled |
| run9 | two questions: affects an asset, rank 1 to 5 | important 162/185, noise 100/122; held-out 21/21 and 9/9. Missed page sizes (read as pagination) and event times on create |
| run10 | two questions: can it be ranked (by kind), safest and riskiest level | important 179/185 and record ids dropped, but noise only 77/122 and held-out noise 1/9: almost anything looked rankable |
| run11 | run9 plus four general wording fixes and a re-ask of unanswered inputs | **frozen**: important 175/185, noise 113/122; held-out 21/21 and 9/9 |

Lessons folded into run4: require only the reply fields the runner uses; match paths with or without `[]`; never reject a whole reply for one bad row, re-ask that input alone; a retry must sample, because repeating a greedy prompt returns the same reply; make the not-important list closed, so a limit or an account selector cannot be dropped by a judgement call.

## Commands

```
# both stages for one server (local model must be reachable)
scripts/derive_input_labels.py --server github --stage both -v

# on the cluster, all three servers, into a pinned folder
sbatch --export=ALL,LABEL_FLAGS="--stage both",MCP_INPUT_LABELS_OUT=$PWD/reports/experiments/v12/runN \
  scripts/derive_input_labels.sbatch

# every kept input's five levels, and whether each comes from the policy, the scan,
# the schema or the model's guess, into runN/rule-levels.md
python3 scripts/render_input_rule_levels.py --run reports/experiments/v12/runN
```

## Layout of a run

```
runN/
├── prompt-importance-AS-RUN.md, prompt-importance-check-AS-RUN.md, prompt-rules-AS-RUN.md
├── <server>.importance.json   stage 1: decision, votes, check and reason per input
├── <server>.json              stage 2: every input; the important ones with their rule
├── rule-levels.md             the same rules as one table of levels 1 to 5 per kept input
└── logs/                      per-server logs; rejected/ holds any reply the runner could not use
```

## Out of scope

- Combining the call's input level with the static tool score. The level is built to do that (3 is neutral), but the combination is decided separately.
- Opaque identifiers: a `register` rule matches assets by name; ids that never contain the asset's name need the traffic-discovered bindings in `mcp_security.binding`.
- v11's flags, composites and `track_*` fields.
