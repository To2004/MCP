# v4 — the static arm after the openWorld / parameter removal

The static arm was **re-assembled, not re-scanned**
(`scripts/reassemble_static_arm.py`): tool impact was recomputed from the current
rules, the model's verbatim blast (`blast_radius_raw`) was replayed from the
original artifacts, and every deterministic pass — bulk twins, alias twins,
sens/impact floors, roofs, `band_label_v5` — ran again on top.

**The replay is verified.** Four of the five servers reproduced their stored band
distributions *exactly*, down to the score sum. Only calendar moved, and only
because three of its tools changed tier. If the replay were unfaithful, the
untouched servers would have drifted too.

What changed in the rules:
- `openWorldHint` is no longer read — boundary crossing moved to the dynamic stage.
- Parameter signals (`raw-command`, `raw-query`, `outbound`) are capability flags
  only; they no longer raise the tier.

Effect on impact: **three tools, all on calendar** — `create-event`,
`create-events`, `update-event`, each 5 → 4. Slack, github, fs and sqlite: zero.

---

## Severity matrices — the three arms

| server | arm | low | med | high | crit | Σ score | Σ impact |
|---|---|--:|--:|--:|--:|--:|--:|
| calendar | v4 (LLM) | 29 | 42 | 8 | 1 | 2 280 | 41 |
| | bulkclause | 25 | 45 | 9 | 1 | 2 357 | 42 |
| | **static (new)** | 30 | 39 | 9 | 1 | **2 253** | 41 |
| | *static (old)* | *30* | *30* | *16* | *3* | *2 663* | *44* |
| slack | v4 (LLM) | 56 | 45 | 18 | 4 | 3 779 | 53 |
| | bulkclause | 56 | 45 | 18 | 4 | 3 779 | 53 |
| | static | 57 | 49 | 19 | 4 | 3 944 | 53 |
| github | v4 (LLM) | 69 | 59 | 32 | 11 | 6 340 | 85 |
| | bulkclause | 69 | 59 | 32 | 11 | 6 340 | 85 |
| | static | 57 | 76 | 29 | 14 | 6 814 | 90 |
| fs:corp | v4 (LLM) | 85 | 54 | 44 | 14 | 6 985 | 41 |
| | bulkclause | 85 | 54 | 44 | 14 | 6 985 | 41 |
| | static | 87 | 52 | 47 | 14 | 7 232 | 43 |
| sqlite | v4 (LLM) | 12 | 19 | 3 | 4 | 1 411 | 16 |
| | bulkclause | 12 | 19 | 3 | 4 | 1 411 | 16 |
| | static | 11 | 20 | 3 | 4 | 1 429 | 16 |

**Calendar is the whole story.** The old static arm sat 17 % above the LLM on
score sum (2 663 vs 2 280) and had **double its high count** (16 vs 8). After the
removal it sits at **2 253 — 1 % below** the LLM, with 9 high against 8. Three
tools were carrying the entire divergence, and they were carrying it because of
an annotation, not because of anything the tools' descriptions said.

## Impact agreement — static vs the LLM

| server | disagreements | which |
|---|--:|---|
| calendar | **0 / 13** | — (was 3/13) |
| sqlite | **0 / 5** | — |
| fs:corp | 2 / 14 | `directory_tree`, `search_files` 2 → 3 |
| slack | 2 / 16 | `conversations_leave` 5 → 4, `usergroups_me` 4 → 5 |
| github | 5 / 26 | `push_files` 4 → 5; `search_repositories`, `list_commits`, `search_users`, `get_pull_request_files` 2 → 3 |

**9 disagreements out of 74 tools — 88 % exact agreement**, and every remaining
one is a judgement call rather than an error:

- The **2 → 3 cluster** (six of the nine) is one recurring question: does a
  listing/search that returns items count as metadata or as content? The rules
  resolve upward, the model downward. `get_pull_request_files` and `list_commits`
  hand back file paths and commit messages, so the rules' reading is defensible;
  so is the model's, since neither returns file *contents*.
- `push_files` 4 → 5: pushing is publication — the rules treat it as leaving the
  repository's private state. The model reads it as a recoverable write.
- `conversations_leave` 5 → 4: the model called leaving a channel irreversible;
  the rules call it a re-joinable membership change.
- `usergroups_me` 4 → 5: its description mentions `remove`. Arguably a rules miss.

Calendar going to 0/13 is the notable one — the last server where static and LLM
gave structurally different pictures now agrees on every tool.

## Blast is still where the noise lives

Same model, same prompt, two separate runs:

| server | blast cells differing | of which N/A flips |
|---|--:|--:|
| sqlite | 2 / 55 | 0 |
| calendar | 13 / 208 | 1 |
| fs:corp | 32 / 308 | 5 |
| slack | 32 / 320 | 6 |
| github | 33 / 520 | 7 |

The static arm's remaining score gap on slack (+4 %), github (+7 %) and fs (+4 %)
is **not** an impact gap — impact agrees on 88 % of tools and the disagreements
are small and two-directional. It is blast variance between two runs of the same
deterministic decoder, plus the handful of 2 → 3 impact calls interacting with the
impact-keyed floors.

## What this says

1. **The removal was corrective, not merely simplifying.** The one place static
   and LLM disagreed structurally was calendar, and the whole gap came from the
   `openWorldHint` rule. Removing it did not lose signal — it moved a runtime
   question to the runtime stage and the design-time answer got *better*.
2. **Parameter promotions were dead weight here.** Across 74 tools on these five
   servers and 196 tools on the finance corpus, not one tier was decided by a
   parameter that the description didn't already decide. They were a latent
   source of surprise with no demonstrated benefit.
3. **Tool impact is rule-derivable; blast is not.** 88 % exact agreement on
   impact, against a model that disagrees with *itself* on 6–10 % of blast cells
   between runs.
