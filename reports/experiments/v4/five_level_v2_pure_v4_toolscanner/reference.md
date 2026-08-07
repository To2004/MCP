# Three-way tool impact — reference (120 tools)

Three independent methods over the same catalogs:

| | method | signal it reads |
|---|---|---|
| **A** | LLM | the model reads the tool JSON and answers the ladder |
| **B** | static | tiered verb patterns over name + description prose |
| **C** | atomic | name tokenised to verb+object, mapped to an operation taxonomy, tier = max |

They share no pattern table, so agreement is corroboration rather than a shared blind spot.

## Pairwise agreement

| pair | exact | of | % | within ±1 |
|---|--:|--:|--:|--:|
| static vs atomic | 100 | 120 | 83% | 99% |

## Consensus

{'agreed': 100, 'split (2 methods)': 20}

## Where the methods disagree

| server | tool | LLM | static | atomic | max op | atomic ops |
|---|---|:--:|:--:|:--:|---|---|
| everything | `longRunningOperation` | — | 3 | 4 | `MODIFY` | MODIFY, READ |
| everything | `sampleLLM` | — | 1 | 3 | `READ` | READ |
| filesystem | `list_directory` | — | 3 | 2 | `LIST` | LIST |
| filesystem | `list_directory_with_sizes` | — | 3 | 2 | `LIST` | LIST, METADATA |
| filesystem | `search_files` | — | 3 | 2 | `LIST` | LIST |
| filesystem | `write_file` | — | 4 | 5 | `OVERWRITE` | OVERWRITE, WRITE |
| git | `git_checkout` | — | 4 | 3 | `READ` | READ |
| github | `get_commit` | — | 4 | 3 | `READ` | READ |
| github | `get_me` | — | 2 | 3 | `READ` | READ |
| github | `list_commits` | — | 3 | 2 | `LIST` | LIST |
| github | `list_dependabot_alerts` | — | 3 | 2 | `LIST` | LIST |
| github | `list_notifications` | — | 3 | 2 | `LIST` | LIST |
| memory | `open_nodes` | — | 4 | 3 | `READ` | READ |
| puppeteer | `puppeteer_hover` | — | 3 | 4 | `INTERACT` | INTERACT |
| puppeteer | `puppeteer_select` | — | 3 | 4 | `INTERACT` | INTERACT, WRITE |
| redis | `list` | — | 3 | 2 | `LIST` | LIST |
| sequentialthinking | `sequentialthinking` | — | 3 | 4 | `WRITE` | WRITE |
| slack | `slack_get_user_profile` | — | 3 | 2 | `METADATA` | METADATA |
| slack | `slack_get_users` | — | 2 | 3 | `READ` | READ |
| sqlite | `describe_table` | — | 3 | 2 | `METADATA` | METADATA |

20 of 120 tools have a disagreement (17%).

## Atomic operation census

| operation | tools | tier |
|---|--:|--:|
| `READ` | 39 | 3 |
| `LIST` | 22 | 2 |
| `CREATE` | 20 | 4 |
| `WRITE` | 15 | 4 |
| `SEARCH` | 11 | 3 |
| `MODIFY` | 6 | 4 |
| `DELETE` | 6 | 5 |
| `METADATA` | 5 | 2 |
| `INTERACT` | 4 | 4 |
| `NO_EFFECT` | 3 | 1 |
| `OVERWRITE` | 3 | 5 |
| `EXECUTE` | 2 | 5 |
| `STATE_TOGGLE` | 2 | 2 |
| `MOVE` | 1 | 4 |
| `PUBLISH` | 1 | 5 |
