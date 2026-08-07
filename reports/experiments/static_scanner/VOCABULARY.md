# Static scanner — tool-impact vocabulary

Deterministic 1–5 tool-impact classification from a tool's own declaration:
**name, description, parameters, MCP annotation hints**. No LLM call.

**Threat model: misuse during NORMAL operation.** The tool declaration is taken
at face value. This scanner does not look for malicious or poisoned servers,
prompt injection in descriptions, or rug pulls — only for what a legitimate
tool can do when an agent uses it wrongly.

## The ladder

| Tier | Meaning |
|---|---|
| **1** | NO EFFECT — the server talks about itself, not the data |
| **2** | METADATA — about-ness: what exists, how it is organised, its state |
| **3** | CONTENT READ — the substance itself is disclosed |
| **4** | REVERSIBLE WRITE — state changes the system itself can undo |
| **5** | IRREVERSIBLE, OR IT LEAVES THE SYSTEM |

## Vocabulary — the same operation, named differently across domains

A tool is placed by the strongest action its declaration names. The tables below
are the full synonym sets, grouped so the domain vocabularies are visible:
filesystem (`rm`, `unlink`, `mkdir`), database (`select`, `drop`, `truncate`,
`upsert`), version control (`clone`, `push`, `merge`, `rebase`), messaging
(`post`, `mute`, `pin`), calendar (`rsvp`, `reschedule`), cloud/infra
(`provision`, `deprovision`, `terminate`), payments (`charge`, `refund`,
`payout`), identity (`grant`, `revoke`, `assign`).

### Tier 1 — NO EFFECT — the server talks about itself, not the data

16 patterns:

`capability/ies` · `current time` · `diagnostics` · `echo` · `healthcheck` · `heartbeat` · `liveness` · `noop` · `nop` · `now` · `ping` · `readiness` · `server time` · `uptime` · `version` · `whoami`

### Tier 2 — METADATA — about-ness: what exists, how it is organised, its state

50 patterns:

`acknowledge` · `attributes` · `availability` · `browse` · `catalogue` · `columns` · `counts` · `describe` · `dir` · `directory` · `discover` · `emoji` · `enumerate` · `exists` · `fields` · `flag` · `follow` · `free.busy` · `glob` · `headers` · `ids` · `index` · `inventory` · `keys` · `list` · `ls` · `mark as read/unread/seen` · `metadata` · `mute` · `names` · `permissions` · `pin` · `quotas` · `reaction` · `registry` · `rename` · `schema` · `sizes` · `star` · `stat` · `status` · `timestamps` · `unfollow` · `unmute` · `unpin` · `unstar` · `unwatch` · `usage` · `walk` · `watch`

### Tier 3 — CONTENT READ — the substance itself is disclosed

46 patterns:

`analyzse` · `backtest` · `blame` · `body` · `calculate` · `cat` · `compare` · `compute` · `contents` · `details` · `diff` · `display` · `download` · `dump` · `evaluate` · `export` · `extract` · `fetch` · `find` · `forecast` · `get` · `grep` · `history/ies` · `inspect` · `lookup` · `open` · `payload` · `preview` · `query` · `read` · `replies` · `report` · `research` · `retrieve` · `scan` · `screener/ing` · `search` · `select` · `show` · `simulate/ion` · `summary/ise/ize` · `tail` · `text` · `thread` · `transcripts` · `view`

### Tier 4 — REVERSIBLE WRITE — state changes the system itself can undo

85 patterns:

`accept` · `activate` · `add` · `adjust` · `allocate` · `amend` · `annotate` · `append` · `apply` · `archive` · `assign` · `authorizse` · `branch` · `build` · `checkout` · `clone` · `close` · `comment` · `commit` · `configure` · `copy` · `create` · `deactivate` · `decline` · `disable` · `draft` · `duplicate` · `edit` · `enable` · `fork` · `generate` · `grant` · `import` · `insert` · `join` · `label` · `leave` · `make` · `manage` · `membership` · `mirror` · `mkdir` · `modify` · `move` · `mv` · `new` · `open` · `patch` · `pause` · `permit` · `post` · `provision` · `put` · `register` · `relabel` · `relocate` · `reopen` · `reply` · `reschedule` · `respond` · `restore` · `resume` · `revise` · `revoke` · `rsvp` · `save` · `schedule` · `set` · `share` · `snapshot` · `stage` · `store` · `submit` · `subscribe` · `sync` · `tag` · `transfer to` · `unarchive` · `unassign` · `unsubscribe` · `update` · `upload` · `upsert` · `vote` · `write`

### Tier 5 — IRREVERSIBLE, OR IT LEAVES THE SYSTEM

63 patterns:

`announce` · `broadcast` · `buy` · `cancel` · `charge` · `clear` · `completely overwrite` · `decommission` · `delete` · `deploy` · `deprovision` · `destroy` · `discard` · `drop` · `email` · `empty` · `erase` · `evaluate code/script/expression` · `evict` · `execute/ing` · `expire` · `flush` · `force push` · `forward` · `invalidate` · `invite` · `invoke` · `kill` · `merge` · `notify/ication` · `overwrite/ing` · `payments` · `payout` · `place an order` · `prune` · `publish` · `purge` · `push` · `rebase` · `refund` · `release` · `remove` · `replace/ing the entire/whole/complete` · `reset` · `revert` · `rm` · `rollback` · `run a command/script/code/query/job` · `sell` · `send` · `settle` · `shutdown` · `sms` · `terminate` · `trade` · `transfer funds` · `truncate` · `uninstall` · `unlink` · `void` · `webhook` · `wipe` · `withdraw`

## Scoping rules — why a word does not always count

Matching verbs anywhere in a description is the dominant source of wrong
answers, because MCP descriptions are increasingly written as instructions to
an agent rather than as API documentation. Four rules constrain it:

| Rule | What it does | Why |
|---|---|---|
| **Annotation ceiling** | `readOnlyHint: true` caps the tier at 3 | a declared read-only tool cannot write or destroy |
| **Name-scoped ambiguity** | 112 words (`branch`, `email`, `merge`, `set`, `run`, `generate`, …) count only in the tool NAME | *"groups that **notify** all members"* is not a notifier; *"commits of a **branch**"* does not create a branch; *"search by name, **email**"* does not send email |
| **Negation guard** | a verb preceded by never / do not / without / cannot is ignored | sec-edgar's read-only tools say *"**NEVER add** external information"* and were scoring as writes |
| **Return-shape caps** | what a READ returns bounds its tier (liveness markers in the name; return markers in the opening sentence) | *"**Get** the current time"* is tier 1, not 3 |

Caps never lower a mutation: a delete stays a delete however its payload is described.

## Parameter signals

Capability evidence from the input schema, recorded separately from the tier —
a tool can sit at a modest tier and still be broad because its inputs are
unconstrained.

| Signal | Meaning | Raises tier? |
|---|---|---|
| `raw-query` | takes a raw query string — the caller composes the operation | no — recorded as a flag |
| `raw-command` | takes a command/script to execute | yes → 5 |
| `outbound` | can emit a message outside the system | no — recorded as a flag |
| `path` | takes a filesystem path | no — recorded as a flag |
| `recursive` | can descend recursively — one call reaches a subtree | no — recorded as a flag |
| `glob` | takes a pattern — one call can select many items | no — recorded as a flag |
| `force` | has a force/overwrite switch that removes a safety | no — recorded as a flag |
| `unbounded` | caller controls result volume | no — recorded as a flag |
| `dry-run` | offers a dry-run — the real call is consequential | no — recorded as a flag |

`raw-query` raises the tier only when the tool's text shows a **mutating**
language (INSERT/UPDATE/DELETE/DROP). Arbitrary `SELECT` reaches a lot, but
reaching a lot is *blast radius*; the action is still a read — so `read_query`
stays 3 while `write_query` is 5.

A `path`, `raw-command` or `raw-query` parameter with no `enum`, `pattern` or
`format` is additionally marked **unconstrained**.

## Confidence

| Value | Meaning |
|---|---|
| 0.95 | explicit verb evidence + a corroborating annotation |
| 0.80 | explicit verb evidence |
| 0.75 | tier set by parameter evidence |
| 0.35 | **no verb matched** — fell through to the default; treat as unclassified |

