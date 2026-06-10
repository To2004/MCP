# Atomic-Op Classification — Methodology

How the rules-based classifier maps MCP tools to the 13 atomic operations.

## Two classification paths

Every server is classified twice, independently, from different signal sources:

| Path | Input | Module |
|------|-------|--------|
| **README** | Tool name + description extracted from the server's README prose | `readme_rules.py` |
| **ToolList** | Tool name + description + `inputSchema` from a live or cached tool-list JSON | `toollist_rules.py` |

Discrepancies (same tool, different ops in each path) are surfaced in the `Discrepancies` sheet of the xlsx and logged diagnostically.

## Rule structure

Each rule is a small function that receives `(tool_name, description, [readme_excerpt / input_schema])` and returns either a `RuleHit` or `None`.

```python
@dataclass(frozen=True)
class RuleHit:
    rule_id: str        # e.g. "readme.delete.keyword"
    atomic_op: str      # e.g. "DELETE"
    confidence: Confidence  # HIGH / MEDIUM / LOW
    matched_on: str     # human-readable evidence string
```

A single tool can produce multiple `RuleHit`s for different atomic ops. Hits are de-duplicated by `(rule_id, atomic_op)` so the same rule can fire at most once per tool, but multiple rules can tag the same op.

## README rules (`readme_rules.py`)

These rules scan the concatenated string `"{tool_name} {description} {readme_excerpt}"` for keyword patterns using `\b`-anchored regex.

| Rule ID | Atomic op | Signal |
|---------|-----------|--------|
| `readme.execute.shell_keyword` | EXECUTE | `execute shell`, `run command`, `eval`, `spawn process`, `subprocess` |
| `readme.delete.keyword` | DELETE | `deletes a …`, `permanently delete`, `removes …`, `drops table`, `destroys …` |
| `readme.overwrite.keyword` | OVERWRITE | `overwrites`, `replaces the content`, `replaces an existing` |
| `readme.schema_modify.keyword` | SCHEMA_MODIFY | `alters schema`, `creates a table`, `adds a column`, `DDL statement` |
| `readme.broadcast.keyword` | BROADCAST | `posts a message`, `sends a message`, `publish`, `reply to` |
| `readme.write.keyword` | WRITE | `inserts a row`, `writes a file`, `appends a note`, `creates a new issue` |
| `readme.modify.keyword` | MODIFY | `edits a file`, `updates an existing`, `renames`, `find-and-replace` |
| `readme.move.keyword` | MOVE | `moves a file`, `renames a directory`, `relocate` |
| `readme.create.keyword` | CREATE | `creates a directory`, `forks a repository`, `makes a new folder` |
| `readme.read.keyword` | READ | `returns the contents`, `reads a file`, `gets the file`, name prefix `read_/get_/fetch_/view_` |
| `readme.search.keyword` | SEARCH | `searches for …`, `finds files matching`, `glob pattern`, name prefix `search_` |
| `readme.metadata.keyword` | METADATA | `returns metadata`, `returns the size`, `describes a table`, `file info` |
| `readme.list.keyword` | LIST | `lists the contents`, `lists channels`, `enumerates`, `returns a list`, name prefix `list_` |

## ToolList rules (`toollist_rules.py`)

These rules use structural signals — name prefixes, schema shapes — rather than prose keywords.

### Name-prefix detection

| Prefixes / bare names | Atomic op |
|-----------------------|-----------|
| `list_`, `ls_`, `list`, `ls` | LIST |
| `search_`, `find_`, `web_search`, `local_search`, `search`, `find` | SEARCH |
| `delete_`, `remove_`, `drop_`, `destroy_`, `delete`, `remove`, `drop`, `destroy` | DELETE |
| `move_`, `rename_`, `move`, `rename` | MOVE |

Service namespaces (`slack_`, `github_`, `git_`, `gdrive_`, `redis_`, etc.) are stripped before matching so `slack_list_channels` is still detected as LIST.

### READ vs METADATA disambiguation

Tools whose names start with `read_`, `get_`, `fetch_`, `view_`, `show_`, `open_` are tagged READ unless their name also contains an info/stat/metadata keyword (`info`, `stat`, `schema`, `profile`, `metadata`, `size`), in which case they are tagged METADATA.

### WRITE / OVERWRITE / CREATE / SCHEMA_MODIFY / MODIFY

| Signal | Ops assigned |
|--------|-------------|
| `write_` prefix or `overwrites` in description | OVERWRITE + WRITE |
| `insert_`, `append_`, `add_`, `post_`, `commit` prefix | WRITE |
| `create_` + `table`/`schema` in name or description | SCHEMA_MODIFY |
| `create_` (without table/schema) | CREATE |
| `create_directory`, `mkdir_` | CREATE (directory special-case) |
| `edit_` prefix or `find-and-replace` in description | MODIFY (HIGH) |
| `update_` prefix or `updates` in description | MODIFY (MEDIUM) |
| `set`/`put` names or prefixes | OVERWRITE + WRITE (MEDIUM) |

### Freeform SQL (`_freeform_sql`)

Tools named `write_query`, `exec_query`, `execute_query`, `sql_exec`, `run_sql`, or whose description contains `non-select sql` / `any sql` are assigned all five worst-case ops: `EXECUTE`, `DELETE`, `OVERWRITE`, `SCHEMA_MODIFY`, `WRITE`. Confidence is HIGH if the input schema contains a `query` property, MEDIUM otherwise.

### Other structural patterns

| Function | Detection |
|----------|-----------|
| `_broadcast` | `post_message`, `reply_to_thread`, `send_email`, `add_reaction` in name/description |
| `_explicit_execute` | `exec_`, `run_`, `shell_`, `evaluate` prefixes; `_trigger` suffix; `workflow_dispatch` in description |
| `_push_merge_fork` | `push_`/`merge_`/`fork_` prefixes or matching description phrases |
| `_tree` | `_tree` in name or `recursive tree` in description → LIST |
| `_list_suffix` | Name ends with `_list` → LIST |
| `_star_dismiss` | `star_`/`unstar_` → MODIFY LOW; `dismiss_`/`mark_` → MODIFY MEDIUM |
| `_dom_interaction` | Puppeteer-style descriptions (`clicks an element`, `fills a form`) → MODIFY MEDIUM |

## Severity assignment

After rules fire, the classified atomic ops are looked up in the taxonomy CSV
(`presentations/heatmap_byhand/csv/atomic_operations.csv`). The tool's `max_severity`
is the highest severity among all tagged ops, and `severity_label` is the
corresponding label (Critical / High / Medium / Low).

Severity order (1 = lowest risk): LIST = METADATA = SEARCH = READ < MOVE < MODIFY < CREATE < WRITE < BROADCAST < SCHEMA_MODIFY < OVERWRITE < DELETE < EXECUTE.

## Scripts

| Script | Purpose |
|--------|---------|
| `presentations/atomic_op_classification/regen_xlsx.py` | Regenerate the heatmap xlsx |
| `presentations/atomic_op_classification/dump_rule_fires.py` | Print rule fire counts across all servers |
| `uv run python -m mcp_security.atomic_ops.build_heatmap --help` | Full CLI options |
