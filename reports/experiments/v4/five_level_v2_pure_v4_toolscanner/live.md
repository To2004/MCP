# Three-way tool impact — live (74 tools)

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
| llm vs static | 70 | 74 | 95% | 100% |
| llm vs atomic | 69 | 74 | 93% | 100% |
| static vs atomic | 71 | 74 | 96% | 100% |

## Consensus

{'unanimous': 68, 'majority': 6}

## Where the methods disagree

| server | tool | LLM | static | atomic | max op | atomic ops |
|---|---|:--:|:--:|:--:|---|---|
| calendar_real | `manage-accounts` | 5 | 5 | 4 | `CONFIGURE` | CONFIGURE |
| github_real | `get_pull_request_files` | 2 | 3 | 3 | `READ` | READ |
| github_real | `search_users` | 2 | 3 | 3 | `SEARCH` | SEARCH |
| slack_real | `conversations_leave` | 5 | 4 | 4 | `MEMBERSHIP` | MEMBERSHIP |
| slack_real | `usergroups_me` | 4 | 5 | 4 | `CONFIGURE` | CONFIGURE, MEMBERSHIP |
| slack_real | `usergroups_users_update` | 5 | 5 | 4 | `MODIFY` | MODIFY |

6 of 74 tools have a disagreement (8%).

## Atomic operation census

| operation | tools | tier |
|---|--:|--:|
| `LIST` | 16 | 2 |
| `READ` | 15 | 3 |
| `CREATE` | 14 | 4 |
| `WRITE` | 10 | 4 |
| `SEARCH` | 8 | 3 |
| `MODIFY` | 8 | 4 |
| `METADATA` | 5 | 2 |
| `MEMBERSHIP` | 3 | 4 |
| `OVERWRITE` | 3 | 5 |
| `CONFIGURE` | 2 | 4 |
| `DELETE` | 1 | 5 |
| `NO_EFFECT` | 1 | 1 |
| `STATE_TOGGLE` | 1 | 2 |
| `PUBLISH` | 1 | 5 |
| `MOVE` | 1 | 4 |
