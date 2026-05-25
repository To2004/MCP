# MCP Atomic-Op Classifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a rules-based Python classifier that maps each MCP tool to atomic operations (the 13-op taxonomy), driven by BOTH README text AND live tool-list introspection, then renders the results as an xlsx heatmap.

**Architecture:** New python package `src/mcp_security/atomic_ops/` with separate readme_rules and toollist_rules modules. A discovery layer attempts subprocess-based MCP introspection per server, with cached JSON fallback for servers we have docs for. The classifier orchestrates rule application; xlsx_writer emits the 5-sheet workbook. Cached tool-list JSONs live in `src/mcp_security/atomic_ops/data/tool_lists/`. README sources are paths to existing files (no duplication).

**Tech Stack:** Python 3.12, openpyxl (already a dep), pytest, MCP Python SDK (`mcp>=1.26.0`, already a dep), `subprocess` for spawning servers.

**Threat model direction:** MCP servers = protected asset; agents = threat. Severity reflects damage an agent could cause via the tool.

**Server set (target ≥10, ideal 15+):**

Tier A — full docs available in `docs/mcp-tools/`:
1. filesystem (`@modelcontextprotocol/server-filesystem`) — 13 tools
2. sqlite (`mcp-server-sqlite`) — 6 tools
3. slack (reference `@modelcontextprotocol/server-slack`) — 8 tools
4. github (`github/github-mcp-server`) — ~102 tools

Tier B — README-only from npm/PyPI registry or GitHub:
5. memory (`@modelcontextprotocol/server-memory`)
6. git (`mcp-server-git` PyPI)
7. fetch (`mcp-server-fetch` PyPI)
8. time (`mcp-server-time` PyPI)
9. everything (`@modelcontextprotocol/server-everything`)
10. sequentialthinking (`@modelcontextprotocol/server-sequentialthinking`)
11. puppeteer (`@modelcontextprotocol/server-puppeteer`) — archived
12. brave-search (`@modelcontextprotocol/server-brave-search`)
13. postgres (`@modelcontextprotocol/server-postgres`) — archived
14. gdrive (`@modelcontextprotocol/server-gdrive`) — archived
15. redis (`@modelcontextprotocol/server-redis`) — archived

For Tier B, prefer live introspection where install is cheap; fall back to README-only when not feasible. Mark `readme_only` rows in the heatmap.

---

## Task 1: Backup taxonomy and create module skeleton

**Files:**
- Create: `presentations/heatmap_byhand/csv/atomic_operations_backup.csv` (copy of the live csv)
- Create: `presentations/heatmap_byhand/csv/changes_log.md`
- Create: `src/mcp_security/atomic_ops/__init__.py` (empty)
- Create: `src/mcp_security/atomic_ops/data/__init__.py` (empty so the dir ships with the package)
- Create: `src/mcp_security/atomic_ops/data/tool_lists/.gitkeep`
- Create: `tests/atomic_ops/__init__.py` (empty)

- [ ] **Step 1: Copy taxonomy to backup**

```bash
cp presentations/heatmap_byhand/csv/atomic_operations.csv \
   presentations/heatmap_byhand/csv/atomic_operations_backup.csv
```

- [ ] **Step 2: Verify backup matches original byte-for-byte**

Run:
```bash
diff -q presentations/heatmap_byhand/csv/atomic_operations.csv \
        presentations/heatmap_byhand/csv/atomic_operations_backup.csv
```
Expected: no output (files identical).

- [ ] **Step 3: Create changes_log.md with header**

Content:
```markdown
# Atomic-Op Taxonomy — Changes Log

This file tracks any modifications to `atomic_operations.csv` and the
decisions made by the classifier during heatmap generation. The csv has a
hard rule: do not edit existing rows. Only append new ops with rank >= 14.

## Entries
```

- [ ] **Step 4: Create module skeleton (empty __init__.py files + data dir)**

- [ ] **Step 5: Commit**

```bash
git add presentations/heatmap_byhand/csv/atomic_operations_backup.csv \
        presentations/heatmap_byhand/csv/changes_log.md \
        src/mcp_security/atomic_ops/ \
        tests/atomic_ops/
git commit -m "feat(atomic_ops): backup taxonomy and create module skeleton"
```

---

## Task 2: Taxonomy loader

**Files:**
- Create: `src/mcp_security/atomic_ops/taxonomy.py`
- Test: `tests/atomic_ops/test_taxonomy.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/atomic_ops/test_taxonomy.py
from pathlib import Path

import pytest

from mcp_security.atomic_ops.taxonomy import AtomicOp, load_taxonomy

TAXONOMY_CSV = (
    Path(__file__).resolve().parents[2]
    / "presentations"
    / "heatmap_byhand"
    / "csv"
    / "atomic_operations.csv"
)


def test_load_taxonomy_returns_thirteen_ops():
    ops = load_taxonomy(TAXONOMY_CSV)
    assert len(ops) >= 13


def test_load_taxonomy_first_op_is_execute_critical():
    ops = load_taxonomy(TAXONOMY_CSV)
    first = ops[0]
    assert first.name == "EXECUTE"
    assert first.severity == 5
    assert first.severity_label == "Critical"


def test_load_taxonomy_rank_one_through_thirteen_present():
    ops = load_taxonomy(TAXONOMY_CSV)
    ranks = {op.rank for op in ops}
    for r in range(1, 14):
        assert r in ranks


def test_load_taxonomy_returns_dataclass():
    ops = load_taxonomy(TAXONOMY_CSV)
    assert isinstance(ops[0], AtomicOp)


def test_load_taxonomy_severity_in_range():
    ops = load_taxonomy(TAXONOMY_CSV)
    for op in ops:
        assert 1 <= op.severity <= 5


def test_load_taxonomy_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_taxonomy(Path("/nonexistent.csv"))
```

- [ ] **Step 2: Run tests to see them fail**

Run: `uv run pytest tests/atomic_ops/test_taxonomy.py -v`
Expected: import error / FAIL.

- [ ] **Step 3: Implement taxonomy.py**

```python
"""Load the atomic-op taxonomy from atomic_operations.csv."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AtomicOp:
    """One row of the atomic-op taxonomy."""

    rank: int
    name: str
    severity: int
    severity_label: str
    reasoning: str


def load_taxonomy(csv_path: Path) -> list[AtomicOp]:
    """Read atomic_operations.csv and return its rows as AtomicOp objects, ranked.

    The csv has columns: rank, atomic_op, severity, severity_label, reasoning.
    Rows are returned sorted by rank ascending.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Taxonomy csv not found: {csv_path}")

    ops: list[AtomicOp] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if not row.get("rank"):
                continue
            ops.append(
                AtomicOp(
                    rank=int(row["rank"]),
                    name=row["atomic_op"].strip().upper(),
                    severity=int(row["severity"]),
                    severity_label=row["severity_label"].strip(),
                    reasoning=row["reasoning"].strip(),
                )
            )
    ops.sort(key=lambda op: op.rank)
    return ops
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/atomic_ops/test_taxonomy.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/mcp_security/atomic_ops/taxonomy.py tests/atomic_ops/test_taxonomy.py
git commit -m "feat(atomic_ops): add taxonomy loader with tests"
```

---

## Task 3: Rule data structures and atomic-op constants

**Files:**
- Create: `src/mcp_security/atomic_ops/rules_base.py`
- Test: `tests/atomic_ops/test_rules_base.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/atomic_ops/test_rules_base.py
from mcp_security.atomic_ops.rules_base import ATOMIC_OPS, Confidence, RuleHit


def test_atomic_ops_contains_all_thirteen():
    expected = {
        "EXECUTE",
        "DELETE",
        "OVERWRITE",
        "SCHEMA_MODIFY",
        "BROADCAST",
        "WRITE",
        "MODIFY",
        "MOVE",
        "CREATE",
        "READ",
        "SEARCH",
        "METADATA",
        "LIST",
    }
    assert expected.issubset(ATOMIC_OPS)


def test_rulehit_holds_required_fields():
    hit = RuleHit(
        rule_id="readme.execute.shell_keyword",
        atomic_op="EXECUTE",
        confidence=Confidence.HIGH,
        matched_on="execute shell command",
    )
    assert hit.atomic_op == "EXECUTE"
    assert hit.confidence is Confidence.HIGH
    assert "shell" in hit.matched_on


def test_confidence_values():
    assert Confidence.HIGH.value == "high"
    assert Confidence.MEDIUM.value == "medium"
    assert Confidence.LOW.value == "low"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/atomic_ops/test_rules_base.py -v`
Expected: import error.

- [ ] **Step 3: Implement rules_base.py**

```python
"""Shared rule data types and atomic-op identifiers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Confidence(str, Enum):
    """How strongly a rule asserts the atomic-op tag."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


ATOMIC_OPS: frozenset[str] = frozenset(
    {
        "EXECUTE",
        "DELETE",
        "OVERWRITE",
        "SCHEMA_MODIFY",
        "BROADCAST",
        "WRITE",
        "MODIFY",
        "MOVE",
        "CREATE",
        "READ",
        "SEARCH",
        "METADATA",
        "LIST",
    }
)


@dataclass(frozen=True)
class RuleHit:
    """Result of one rule matching against a tool."""

    rule_id: str
    atomic_op: str
    confidence: Confidence
    matched_on: str
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/atomic_ops/test_rules_base.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/mcp_security/atomic_ops/rules_base.py tests/atomic_ops/test_rules_base.py
git commit -m "feat(atomic_ops): add rule base types and atomic-op constants"
```

---

## Task 4: README rules — first half (destructive ops)

**Files:**
- Create: `src/mcp_security/atomic_ops/readme_rules.py`
- Test: `tests/atomic_ops/test_readme_rules.py`

- [ ] **Step 1: Write the failing tests for the first half (EXECUTE, DELETE, OVERWRITE, SCHEMA_MODIFY, BROADCAST)**

```python
# tests/atomic_ops/test_readme_rules.py
import pytest

from mcp_security.atomic_ops.readme_rules import classify_from_readme


def ops_of(hits):
    return {h.atomic_op for h in hits}


@pytest.mark.parametrize(
    "desc",
    [
        "Executes a shell command in a subprocess",
        "Runs an arbitrary script on the host",
        "Evaluates Python code provided by the caller",
        "Spawns a new process",
    ],
)
def test_execute_keywords(desc):
    hits = classify_from_readme("run_cmd", desc, "")
    assert "EXECUTE" in ops_of(hits)


@pytest.mark.parametrize(
    "desc",
    [
        "Permanently deletes a file from disk.",
        "Drops a table from the database.",
        "Removes the resource identified by id.",
        "Destroys the message in the queue.",
    ],
)
def test_delete_keywords(desc):
    hits = classify_from_readme("delete_thing", desc, "")
    assert "DELETE" in ops_of(hits)


@pytest.mark.parametrize(
    "desc",
    [
        "Overwrites an existing file with new content.",
        "Replaces the content of the entry.",
        "write_file: Creates a new file or completely overwrites an existing one with the given content string.",
    ],
)
def test_overwrite_keywords(desc):
    hits = classify_from_readme("write_file", desc, "")
    assert "OVERWRITE" in ops_of(hits)


@pytest.mark.parametrize(
    "desc",
    [
        "Creates a new table in the database.",
        "Alters the schema of an existing table.",
        "Modifies the database schema with DDL statements.",
    ],
)
def test_schema_modify_keywords(desc):
    hits = classify_from_readme("create_table", desc, "")
    assert "SCHEMA_MODIFY" in ops_of(hits)


@pytest.mark.parametrize(
    "desc",
    [
        "Posts a message to a Slack channel.",
        "Sends an email to the specified address.",
        "Publishes a notification to subscribers.",
        "Broadcasts an update to all listeners.",
    ],
)
def test_broadcast_keywords(desc):
    hits = classify_from_readme("post_msg", desc, "")
    assert "BROADCAST" in ops_of(hits)


@pytest.mark.parametrize(
    "desc",
    [
        "Returns the current time as an ISO string.",
        "Computes the hash of the input.",
    ],
)
def test_no_destructive_op_on_benign(desc):
    hits = classify_from_readme("benign", desc, "")
    destructive = {"EXECUTE", "DELETE", "OVERWRITE", "SCHEMA_MODIFY", "BROADCAST"}
    assert ops_of(hits).isdisjoint(destructive)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/atomic_ops/test_readme_rules.py -v`
Expected: FAIL — function not defined.

- [ ] **Step 3: Implement readme_rules.py with the first 5 op-families**

```python
"""Classify a tool's atomic ops from its README/description text.

Each rule is a small function that takes (tool_name, description, readme_excerpt)
and returns either a RuleHit or None. The public classify_from_readme()
function runs every rule and collects all hits.

Rule IDs follow the pattern: readme.<atomic_op_lower>.<short_name>
"""

from __future__ import annotations

import re

from .rules_base import Confidence, RuleHit


def _matches_any(text: str, patterns: list[str]) -> str | None:
    """Return the first pattern that matches text (case-insensitive), or None."""
    lower = text.lower()
    for pat in patterns:
        if re.search(rf"\b{pat}\b", lower):
            return pat
    return None


def _rule_execute_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"execute[sd]?\s+(?:shell|command|script|arbitrary|code)",
        r"run[s]?\s+(?:a\s+)?(?:shell|command|script|arbitrary|code)",
        r"shell\s+command",
        r"eval(?:uate[sd]?)?",
        r"spawn[s]?\s+(?:a\s+)?process",
        r"subprocess",
        r"invoke[s]?\s+a\s+command",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.execute.shell_keyword",
            atomic_op="EXECUTE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_delete_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"delete[sd]?",
        r"remove[sd]?",
        r"drop[s]?\s+(?:a\s+)?(?:table|database|index)",
        r"destroy[s]?",
        r"erase[sd]?",
        r"purge[sd]?",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.delete.keyword",
            atomic_op="DELETE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_overwrite_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"overwrite[sd]?",
        r"replace[sd]?\s+(?:the\s+)?content",
        r"completely\s+overwrite",
        r"replace[sd]?\s+(?:an?\s+)?existing",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.overwrite.keyword",
            atomic_op="OVERWRITE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_schema_modify_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"alter[s]?\s+(?:the\s+)?schema",
        r"modif(?:y|ies)\s+(?:the\s+)?schema",
        r"create[s]?\s+(?:a\s+)?(?:new\s+)?table",
        r"add[s]?\s+(?:a\s+)?column",
        r"ddl\s+statement",
        r"create\s+table",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.schema_modify.keyword",
            atomic_op="SCHEMA_MODIFY",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_broadcast_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"post[s]?\s+(?:a\s+)?(?:message|update|notification)",
        r"send[s]?\s+(?:a\s+)?(?:message|email|notification)",
        r"publish(?:e[sd])?",
        r"broadcast[s]?",
        r"reply\s+to",
        r"announce[sd]?",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.broadcast.keyword",
            atomic_op="BROADCAST",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


_DESTRUCTIVE_RULES = [
    _rule_execute_keywords,
    _rule_delete_keywords,
    _rule_overwrite_keywords,
    _rule_schema_modify_keywords,
    _rule_broadcast_keywords,
]


def classify_from_readme(
    tool_name: str, description: str, readme_excerpt: str
) -> list[RuleHit]:
    """Run every README-rule against the inputs and collect hits.

    A single tool can yield multiple hits for different atomic ops. Hits are
    de-duplicated by (rule_id, atomic_op) so a rule fires at most once per
    tool, but multiple rules can tag the same op.
    """
    seen: set[tuple[str, str]] = set()
    hits: list[RuleHit] = []
    for rule in _DESTRUCTIVE_RULES:
        hit = rule(tool_name, description, readme_excerpt)
        if hit is None:
            continue
        key = (hit.rule_id, hit.atomic_op)
        if key in seen:
            continue
        seen.add(key)
        hits.append(hit)
    return hits
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/atomic_ops/test_readme_rules.py -v`
Expected: 6 tests parametrized → 22+ subtests pass.

- [ ] **Step 5: Commit**

```bash
git add src/mcp_security/atomic_ops/readme_rules.py tests/atomic_ops/test_readme_rules.py
git commit -m "feat(atomic_ops): add README rules for destructive atomic ops"
```

---

## Task 5: README rules — second half (medium/low-severity ops)

**Files:**
- Modify: `src/mcp_security/atomic_ops/readme_rules.py`
- Modify: `tests/atomic_ops/test_readme_rules.py`

- [ ] **Step 1: Add failing tests for WRITE / MODIFY / MOVE / CREATE / READ / SEARCH / METADATA / LIST**

Append to `tests/atomic_ops/test_readme_rules.py`:

```python
@pytest.mark.parametrize(
    "name,desc",
    [
        ("insert_row", "Inserts a new row into the table."),
        ("write_file", "Writes a new file with the given content."),
        ("append_insight", "Inserts a single text note into the insights table."),
        ("create_issue", "Creates a new issue in the repository."),
    ],
)
def test_write_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "WRITE" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("edit_file", "Applies one or more find-and-replace operations to an existing file."),
        ("update_issue", "Updates an existing issue's title or body."),
        ("rename_thing", "Renames the resource."),
    ],
)
def test_modify_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "MODIFY" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("move_file", "Moves or renames a file or directory."),
        ("rename_branch", "Renames a branch in the repository."),
    ],
)
def test_move_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "MOVE" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("create_directory", "Creates a directory and any missing parent directories."),
        ("create_branch", "Creates a new branch from the given ref."),
        ("create_repository", "Creates a new repository."),
    ],
)
def test_create_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "CREATE" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("read_text_file", "Returns the full text content of a file."),
        ("get_file_contents", "Returns the contents of a file at the given ref."),
        ("read_query", "Executes a SQL SELECT statement and returns rows."),
        ("get_channel_history", "Returns the most recent N messages from a channel."),
    ],
)
def test_read_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "READ" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("search_files", "Finds files matching a glob pattern within a directory."),
        ("search_code", "Runs GitHub code search across every repository."),
        ("search_files_v2", "Searches the index for matching paths."),
    ],
)
def test_search_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "SEARCH" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("get_file_info", "Returns metadata about a file: size, timestamps, type."),
        ("describe_table", "Returns the CREATE TABLE DDL for a specific table."),
        ("get_user_profile", "Returns the detailed Slack profile for a single user."),
    ],
)
def test_metadata_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "METADATA" in ops_of(hits)


@pytest.mark.parametrize(
    "name,desc",
    [
        ("list_directory", "Lists the immediate contents of a directory."),
        ("list_tables", "Returns the names of all user tables in the database."),
        ("list_channels", "Lists public channels in the workspace."),
        ("list_branches", "Lists all branches in the repository."),
    ],
)
def test_list_keywords(name, desc):
    hits = classify_from_readme(name, desc, "")
    assert "LIST" in ops_of(hits)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/atomic_ops/test_readme_rules.py -v`
Expected: many new failures (rules not yet implemented).

- [ ] **Step 3: Add the rules to readme_rules.py**

Append before `_DESTRUCTIVE_RULES`:

```python
def _rule_write_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"insert[s]?\s+(?:a\s+)?(?:new\s+)?(?:row|record|entry|note)",
        r"writes?\s+(?:a\s+)?(?:new\s+)?file",
        r"append[s]?\s+(?:a\s+)?(?:note|entry|line|row|insight)",
        r"add[s]?\s+(?:a\s+)?(?:new\s+)?(?:row|record|entry|note|comment)",
        r"create[s]?\s+(?:a\s+)?(?:new\s+)?(?:issue|pr|pull\s+request|comment|gist)",
        r"post[s]?\s+(?:a\s+)?(?:new\s+)?(?:issue|pr|comment)",
        r"append_insight",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.write.keyword",
            atomic_op="WRITE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_modify_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"edit[s]?\s+(?:a\s+)?(?:file|entry|note)",
        r"updates?\s+(?:an?\s+)?(?:existing\s+)?(?:issue|pr|file|record|entry|message)",
        r"rename[s]?",
        r"modif(?:y|ies)\s+(?:an?\s+)?(?:existing|entry|record|file|note)",
        r"find-and-replace",
        r"patch(?:e[sd])?",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.modify.keyword",
            atomic_op="MODIFY",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_move_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"move[sd]?\s+(?:a\s+)?(?:file|directory|resource)",
        r"rename[s]?\s+(?:a\s+)?(?:file|directory|branch|resource)",
        r"relocate[sd]?",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.move.keyword",
            atomic_op="MOVE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_create_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"creates?\s+(?:a\s+)?(?:new\s+)?(?:directory|folder|branch|repository|repo|gist)",
        r"makes?\s+(?:a\s+)?(?:new\s+)?(?:directory|folder)",
        r"forks?\s+(?:a\s+)?(?:repository|repo)",
    ]
    matched = _matches_any(haystack, patterns)
    if matched:
        return RuleHit(
            rule_id="readme.create.keyword",
            atomic_op="CREATE",
            confidence=Confidence.HIGH,
            matched_on=matched,
        )
    return None


def _rule_read_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    name_lower = name.lower()
    patterns = [
        r"returns?\s+(?:the\s+)?(?:full\s+)?(?:text\s+)?content[s]?",
        r"returns?\s+(?:the\s+)?(?:most\s+recent\s+)?messages",
        r"reads?\s+(?:a\s+)?file",
        r"get[s]?\s+(?:the\s+)?(?:contents?|file|message[s]?)",
        r"fetch(?:es)?\s+(?:the\s+)?(?:contents?|file|messages?)",
        r"view[s]?\s+(?:the\s+)?(?:contents?|file)",
        r"executes?\s+(?:a\s+)?sql\s+select",
        r"select\s+statement",
    ]
    matched = _matches_any(haystack, patterns)
    if matched or (
        name_lower.startswith(("read_", "get_", "fetch_", "view_"))
        and "metadata" not in name_lower
        and "info" not in name_lower
        and "schema" not in name_lower
        and "size" not in name_lower
    ):
        return RuleHit(
            rule_id="readme.read.keyword",
            atomic_op="READ",
            confidence=Confidence.HIGH,
            matched_on=matched or f"name_prefix:{name_lower.split('_')[0]}_",
        )
    return None


def _rule_search_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"search(?:es)?\s+(?:for|the|across|files|code|index|messages)",
        r"finds?\s+(?:files|matches|messages|issues|results)\s+matching",
        r"glob\s+pattern",
        r"runs?\s+(?:github\s+)?(?:code\s+)?search",
    ]
    matched = _matches_any(haystack, patterns)
    if matched or name.lower().startswith("search_"):
        return RuleHit(
            rule_id="readme.search.keyword",
            atomic_op="SEARCH",
            confidence=Confidence.HIGH,
            matched_on=matched or f"name_prefix:search_",
        )
    return None


def _rule_metadata_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"returns?\s+metadata",
        r"returns?\s+(?:the\s+)?(?:size|timestamps|type|permissions|profile|attributes)",
        r"returns?\s+(?:the\s+)?(?:create\s+table\s+)?ddl",
        r"describe[sd]?\s+(?:a\s+)?(?:table|schema|profile)",
        r"file\s+info",
        r"get\s+info",
    ]
    matched = _matches_any(haystack, patterns)
    if matched or (
        name.lower().startswith(("get_", "describe_"))
        and any(
            kw in name.lower()
            for kw in ("info", "schema", "profile", "metadata", "size", "stats")
        )
    ):
        return RuleHit(
            rule_id="readme.metadata.keyword",
            atomic_op="METADATA",
            confidence=Confidence.HIGH,
            matched_on=matched or "name_pattern:get/describe_info",
        )
    return None


def _rule_list_keywords(name: str, desc: str, readme: str) -> RuleHit | None:
    haystack = f"{name} {desc} {readme}"
    patterns = [
        r"lists?\s+(?:the\s+)?(?:immediate\s+)?(?:contents|channels|tables|files|branches|users|members|directories|notifications|issues|releases)",
        r"enumerate[sd]?",
        r"returns?\s+(?:the\s+)?names\s+of\s+all",
        r"returns?\s+(?:a\s+)?(?:paginated\s+)?list",
        r"directory\s+listing",
    ]
    matched = _matches_any(haystack, patterns)
    if matched or name.lower().startswith("list_"):
        return RuleHit(
            rule_id="readme.list.keyword",
            atomic_op="LIST",
            confidence=Confidence.HIGH,
            matched_on=matched or "name_prefix:list_",
        )
    return None
```

Then expand the rule registry:

```python
_RULES = [
    _rule_execute_keywords,
    _rule_delete_keywords,
    _rule_overwrite_keywords,
    _rule_schema_modify_keywords,
    _rule_broadcast_keywords,
    _rule_write_keywords,
    _rule_modify_keywords,
    _rule_move_keywords,
    _rule_create_keywords,
    _rule_read_keywords,
    _rule_search_keywords,
    _rule_metadata_keywords,
    _rule_list_keywords,
]
```

Update `classify_from_readme` to iterate `_RULES` instead of `_DESTRUCTIVE_RULES`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/atomic_ops/test_readme_rules.py -v`
Expected: All previous tests still pass + new ones pass.

- [ ] **Step 5: Commit**

```bash
git add src/mcp_security/atomic_ops/readme_rules.py tests/atomic_ops/test_readme_rules.py
git commit -m "feat(atomic_ops): extend README rules to cover all 13 atomic ops"
```

---

## Task 6: Tool-list rules (name + schema based)

**Files:**
- Create: `src/mcp_security/atomic_ops/toollist_rules.py`
- Test: `tests/atomic_ops/test_toollist_rules.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/atomic_ops/test_toollist_rules.py
import pytest

from mcp_security.atomic_ops.toollist_rules import classify_from_toollist


def ops(hits):
    return {h.atomic_op for h in hits}


def test_read_prefix():
    hits = classify_from_toollist("read_text_file", "Returns text", {})
    assert "READ" in ops(hits)


def test_get_prefix_for_content():
    hits = classify_from_toollist("get_file_contents", "Returns file content", {})
    assert "READ" in ops(hits)


def test_get_prefix_for_metadata_is_not_read():
    hits = classify_from_toollist("get_file_info", "Returns file metadata", {})
    assert "METADATA" in ops(hits)
    assert "READ" not in ops(hits)


def test_list_prefix():
    hits = classify_from_toollist("list_directory", "Lists dir contents", {})
    assert "LIST" in ops(hits)


def test_search_prefix():
    hits = classify_from_toollist("search_files", "Finds matching paths", {})
    assert "SEARCH" in ops(hits)


def test_write_file_is_overwrite_and_write():
    hits = classify_from_toollist(
        "write_file",
        "Creates a new file or completely overwrites an existing one.",
        {},
    )
    op_set = ops(hits)
    assert "OVERWRITE" in op_set
    assert "WRITE" in op_set


def test_delete_prefix():
    hits = classify_from_toollist("delete_file", "Deletes a file", {})
    assert "DELETE" in ops(hits)


def test_move_prefix():
    hits = classify_from_toollist("move_file", "Moves a file", {})
    assert "MOVE" in ops(hits)


def test_create_directory():
    hits = classify_from_toollist("create_directory", "Creates a dir", {})
    assert "CREATE" in ops(hits)


def test_post_message():
    hits = classify_from_toollist(
        "slack_post_message", "Posts a message to a channel", {}
    )
    assert "BROADCAST" in ops(hits)


def test_query_with_freeform_sql_schema_tags_worst_case():
    schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }
    hits = classify_from_toollist(
        "write_query", "Executes any non-SELECT SQL statement", schema
    )
    op_set = ops(hits)
    # write_query can DROP, CREATE, INSERT, UPDATE, DELETE etc.
    assert "EXECUTE" in op_set
    assert "DELETE" in op_set
    assert "SCHEMA_MODIFY" in op_set
    assert "WRITE" in op_set


def test_read_query_is_read_only():
    schema = {"type": "object", "properties": {"query": {"type": "string"}}}
    hits = classify_from_toollist(
        "read_query", "Executes a SQL SELECT statement", schema
    )
    op_set = ops(hits)
    assert "READ" in op_set
    # SELECT-only — should NOT tag worst-case
    assert "DELETE" not in op_set
    assert "SCHEMA_MODIFY" not in op_set


def test_describe_table_is_metadata():
    hits = classify_from_toollist(
        "describe_table", "Returns the CREATE TABLE DDL", {}
    )
    assert "METADATA" in ops(hits)


def test_create_table_is_schema_modify():
    hits = classify_from_toollist(
        "create_table", "Executes a CREATE TABLE DDL", {}
    )
    assert "SCHEMA_MODIFY" in ops(hits)


def test_edit_file_is_modify():
    hits = classify_from_toollist(
        "edit_file", "Applies find-and-replace operations", {}
    )
    assert "MODIFY" in ops(hits)


def test_unknown_tool_returns_empty():
    hits = classify_from_toollist("frobulate", "frobulates the framistat", {})
    assert hits == []


def test_no_destructive_for_pure_read():
    hits = classify_from_toollist("read_text_file", "Reads a file", {})
    destructive = {"DELETE", "OVERWRITE", "EXECUTE", "SCHEMA_MODIFY"}
    assert ops(hits).isdisjoint(destructive)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/atomic_ops/test_toollist_rules.py -v`
Expected: import error.

- [ ] **Step 3: Implement toollist_rules.py**

```python
"""Classify atomic ops from a live MCP tool entry (name + description + schema).

These rules emphasise structural signals — name prefixes, schema shapes — over
keywords in prose. They run independently from readme_rules and may disagree.
"""

from __future__ import annotations

import re

from .rules_base import Confidence, RuleHit

_NAME_PREFIX_OPS: dict[tuple[str, ...], str] = {
    ("list_",): "LIST",
    ("search_", "find_"): "SEARCH",
    ("delete_", "remove_", "drop_", "destroy_"): "DELETE",
    ("move_", "rename_"): "MOVE",
    ("create_directory", "mkdir_"): "CREATE",
}

_METADATA_NAME_KEYWORDS = ("info", "stat", "schema", "profile", "metadata", "size")


def _by_name_prefix(name: str) -> list[RuleHit]:
    hits: list[RuleHit] = []
    lower = name.lower()
    for prefixes, op in _NAME_PREFIX_OPS.items():
        for pfx in prefixes:
            if lower.startswith(pfx) or lower == pfx.rstrip("_"):
                hits.append(
                    RuleHit(
                        rule_id=f"toollist.{op.lower()}.name_prefix",
                        atomic_op=op,
                        confidence=Confidence.HIGH,
                        matched_on=f"name_prefix:{pfx}",
                    )
                )
                break
    return hits


def _read_or_metadata(name: str, desc: str) -> list[RuleHit]:
    lower = name.lower()
    hits: list[RuleHit] = []
    if lower.startswith(("read_", "get_", "fetch_", "view_")):
        if any(kw in lower for kw in _METADATA_NAME_KEYWORDS):
            hits.append(
                RuleHit(
                    rule_id="toollist.metadata.name_pattern",
                    atomic_op="METADATA",
                    confidence=Confidence.HIGH,
                    matched_on=f"name_prefix+metadata_kw:{lower}",
                )
            )
        else:
            hits.append(
                RuleHit(
                    rule_id="toollist.read.name_prefix",
                    atomic_op="READ",
                    confidence=Confidence.HIGH,
                    matched_on=f"name_prefix:{lower.split('_')[0]}_",
                )
            )
    if "describe_" in lower or lower.endswith("_info") or lower.endswith("_stat"):
        if not any(h.atomic_op == "METADATA" for h in hits):
            hits.append(
                RuleHit(
                    rule_id="toollist.metadata.describe",
                    atomic_op="METADATA",
                    confidence=Confidence.HIGH,
                    matched_on=f"name_pattern:describe/info/stat",
                )
            )
    return hits


def _write_create_overwrite(name: str, desc: str) -> list[RuleHit]:
    lower = name.lower()
    hits: list[RuleHit] = []
    desc_lower = desc.lower()
    if lower.startswith("write_") or "overwrites" in desc_lower:
        hits.append(
            RuleHit(
                rule_id="toollist.overwrite.write_or_keyword",
                atomic_op="OVERWRITE",
                confidence=Confidence.HIGH,
                matched_on=f"name_prefix:write_ or desc:overwrites",
            )
        )
        hits.append(
            RuleHit(
                rule_id="toollist.write.write_prefix",
                atomic_op="WRITE",
                confidence=Confidence.HIGH,
                matched_on=f"name_prefix:write_",
            )
        )
    elif lower.startswith(("insert_", "append_", "add_", "create_", "post_")):
        if not (lower.startswith("create_") and "directory" in lower):
            hits.append(
                RuleHit(
                    rule_id="toollist.write.write_prefix",
                    atomic_op="WRITE",
                    confidence=Confidence.HIGH,
                    matched_on=f"name_prefix:{lower.split('_')[0]}_",
                )
            )
    if lower.startswith("create_") and (
        "table" in lower or "table" in desc_lower or "schema" in desc_lower
    ):
        hits.append(
            RuleHit(
                rule_id="toollist.schema_modify.create_table",
                atomic_op="SCHEMA_MODIFY",
                confidence=Confidence.HIGH,
                matched_on=f"name+desc:create_table",
            )
        )
    if lower.startswith("edit_") or "find-and-replace" in desc_lower:
        hits.append(
            RuleHit(
                rule_id="toollist.modify.edit_prefix",
                atomic_op="MODIFY",
                confidence=Confidence.HIGH,
                matched_on=f"name_prefix:edit_ or desc:find-and-replace",
            )
        )
    if lower.startswith("update_") or "updates" in desc_lower:
        hits.append(
            RuleHit(
                rule_id="toollist.modify.update_prefix",
                atomic_op="MODIFY",
                confidence=Confidence.MEDIUM,
                matched_on=f"name_prefix:update_ or desc:updates",
            )
        )
    return hits


def _broadcast(name: str, desc: str) -> list[RuleHit]:
    lower = name.lower()
    desc_lower = desc.lower()
    if (
        "post_message" in lower
        or lower.endswith("_post_message")
        or "reply_to_thread" in lower
        or "send_email" in lower
        or "add_reaction" in lower
        or "post a message" in desc_lower
        or "sends an email" in desc_lower
        or "posts a comment" in desc_lower
    ):
        return [
            RuleHit(
                rule_id="toollist.broadcast.post_or_send",
                atomic_op="BROADCAST",
                confidence=Confidence.HIGH,
                matched_on=f"name/desc:post|send|reply|reaction",
            )
        ]
    return []


_SQL_WORST_CASE_OPS = ("EXECUTE", "DELETE", "OVERWRITE", "SCHEMA_MODIFY", "WRITE")
_FREEFORM_SQL_NAMES = ("write_query", "exec_query", "execute_query", "sql_exec", "run_sql")


def _freeform_sql(name: str, desc: str, schema: dict) -> list[RuleHit]:
    lower = name.lower()
    desc_lower = desc.lower()
    hits: list[RuleHit] = []
    is_sql_exec = (
        lower in _FREEFORM_SQL_NAMES
        or ("query" in lower and ("write" in lower or "exec" in lower))
        or "non-select sql" in desc_lower
        or ("any" in desc_lower and "sql" in desc_lower)
    )
    if not is_sql_exec:
        return hits
    schema_has_query = (
        isinstance(schema, dict)
        and isinstance(schema.get("properties"), dict)
        and "query" in schema["properties"]
    )
    confidence = Confidence.HIGH if schema_has_query else Confidence.MEDIUM
    for op in _SQL_WORST_CASE_OPS:
        hits.append(
            RuleHit(
                rule_id=f"toollist.{op.lower()}.freeform_sql_worst_case",
                atomic_op=op,
                confidence=confidence,
                matched_on=f"name+schema:freeform_sql:{lower}",
            )
        )
    return hits


def _explicit_execute(name: str, desc: str) -> list[RuleHit]:
    lower = name.lower()
    desc_lower = desc.lower()
    if (
        lower.startswith(("exec_", "run_", "shell_", "spawn_"))
        or lower in {"execute", "exec", "shell"}
        or "shell command" in desc_lower
        or "arbitrary code" in desc_lower
        or "subprocess" in desc_lower
    ):
        return [
            RuleHit(
                rule_id="toollist.execute.shell_pattern",
                atomic_op="EXECUTE",
                confidence=Confidence.HIGH,
                matched_on=f"name_prefix/desc:shell|exec|run",
            )
        ]
    return []


def classify_from_toollist(
    tool_name: str, description: str, input_schema: dict
) -> list[RuleHit]:
    """Run all tool-list rules against a single tool and return collected hits.

    Multiple rules can fire and the same atomic op can be tagged by more than
    one rule. Hits are de-duplicated by (rule_id, atomic_op).
    """
    seen: set[tuple[str, str]] = set()
    out: list[RuleHit] = []
    rule_results: list[list[RuleHit]] = [
        _by_name_prefix(tool_name),
        _read_or_metadata(tool_name, description),
        _write_create_overwrite(tool_name, description),
        _broadcast(tool_name, description),
        _freeform_sql(tool_name, description, input_schema),
        _explicit_execute(tool_name, description),
    ]
    for batch in rule_results:
        for hit in batch:
            key = (hit.rule_id, hit.atomic_op)
            if key in seen:
                continue
            seen.add(key)
            out.append(hit)
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/atomic_ops/test_toollist_rules.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/mcp_security/atomic_ops/toollist_rules.py tests/atomic_ops/test_toollist_rules.py
git commit -m "feat(atomic_ops): add tool-list rules with name/schema patterns"
```

---

## Task 7: Server catalog and cached tool lists for Tier A

**Files:**
- Create: `src/mcp_security/atomic_ops/server_catalog.py`
- Create: `src/mcp_security/atomic_ops/data/tool_lists/filesystem.json`
- Create: `src/mcp_security/atomic_ops/data/tool_lists/sqlite.json`
- Create: `src/mcp_security/atomic_ops/data/tool_lists/slack.json`
- Create: `src/mcp_security/atomic_ops/data/tool_lists/github.json`
- Test: `tests/atomic_ops/test_server_catalog.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/atomic_ops/test_server_catalog.py
from mcp_security.atomic_ops.server_catalog import KNOWN_SERVERS, ServerEntry


def test_known_servers_has_tier_a_four():
    names = {s.name for s in KNOWN_SERVERS}
    assert {"filesystem", "sqlite", "slack", "github"}.issubset(names)


def test_known_servers_have_readme_paths():
    for s in KNOWN_SERVERS:
        if s.tier == "A":
            assert s.readme_path is not None
            assert s.readme_path.exists(), f"missing readme: {s.readme_path}"


def test_known_servers_have_tool_list_paths_for_tier_a():
    for s in KNOWN_SERVERS:
        if s.tier == "A":
            assert s.tool_list_path is not None
            assert s.tool_list_path.exists(), f"missing tool list: {s.tool_list_path}"


def test_tool_list_json_has_expected_shape():
    fs = next(s for s in KNOWN_SERVERS if s.name == "filesystem")
    tools = fs.load_tool_list()
    assert isinstance(tools, list)
    assert len(tools) >= 10
    sample = tools[0]
    assert "name" in sample
    assert "description" in sample
    assert "inputSchema" in sample


def test_count_of_tier_b_servers():
    tier_b = [s for s in KNOWN_SERVERS if s.tier == "B"]
    assert len(tier_b) >= 6
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/atomic_ops/test_server_catalog.py -v`
Expected: import error.

- [ ] **Step 3: Implement server_catalog.py**

```python
"""Static catalog of MCP servers we classify, plus paths to cached READMEs and tool lists.

Tier A servers have deeply-curated docs/mcp-tools/<name>.md READMEs and
hand-authored tool-list JSON files in this package's data/tool_lists/. Tier B
servers are README-only by default; if introspection succeeds later, the
tool list is cached at the same data/tool_lists/ path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(__file__).resolve().parent / "data" / "tool_lists"
DOCS_MCP_TOOLS = REPO_ROOT / "docs" / "mcp-tools"


@dataclass(frozen=True)
class ServerEntry:
    """One MCP server in the classification corpus."""

    name: str
    package: str
    tier: Literal["A", "B"]
    install_hint: str
    readme_path: Path | None = None
    tool_list_path: Path | None = None
    notes: str = ""

    def load_readme(self) -> str:
        if self.readme_path and self.readme_path.exists():
            return self.readme_path.read_text(encoding="utf-8")
        return ""

    def load_tool_list(self) -> list[dict]:
        if self.tool_list_path and self.tool_list_path.exists():
            with self.tool_list_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        return []


KNOWN_SERVERS: list[ServerEntry] = [
    # ---------------- Tier A ----------------
    ServerEntry(
        name="filesystem",
        package="@modelcontextprotocol/server-filesystem",
        tier="A",
        install_hint="npx -y @modelcontextprotocol/server-filesystem <root>",
        readme_path=DOCS_MCP_TOOLS / "filesystem.md",
        tool_list_path=DATA_DIR / "filesystem.json",
    ),
    ServerEntry(
        name="sqlite",
        package="mcp-server-sqlite",
        tier="A",
        install_hint="uvx mcp-server-sqlite --db-path <db>",
        readme_path=DOCS_MCP_TOOLS / "sqlite.md",
        tool_list_path=DATA_DIR / "sqlite.json",
    ),
    ServerEntry(
        name="slack",
        package="@modelcontextprotocol/server-slack",
        tier="A",
        install_hint="npx -y @modelcontextprotocol/server-slack (needs SLACK_BOT_TOKEN)",
        readme_path=DOCS_MCP_TOOLS / "slack.md",
        tool_list_path=DATA_DIR / "slack.json",
        notes="Reference server; 8 tools. Remote slackapi server has more.",
    ),
    ServerEntry(
        name="github",
        package="github/github-mcp-server",
        tier="A",
        install_hint="docker run -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server",
        readme_path=DOCS_MCP_TOOLS / "github.md",
        tool_list_path=DATA_DIR / "github.json",
        notes="~102 tools across 15 toolsets. Token scope = blast radius.",
    ),
    # ---------------- Tier B (README-only by default) ----------------
    ServerEntry(
        name="memory",
        package="@modelcontextprotocol/server-memory",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-memory",
        notes="Knowledge-graph memory; CRUD on entities/relations.",
    ),
    ServerEntry(
        name="git",
        package="mcp-server-git",
        tier="B",
        install_hint="uvx mcp-server-git",
        notes="Git operations (status, log, diff, commit, branch).",
    ),
    ServerEntry(
        name="fetch",
        package="mcp-server-fetch",
        tier="B",
        install_hint="uvx mcp-server-fetch",
        notes="HTTP GET tool; converts HTML to markdown.",
    ),
    ServerEntry(
        name="time",
        package="mcp-server-time",
        tier="B",
        install_hint="uvx mcp-server-time",
        notes="Time/timezone conversion; pure-function.",
    ),
    ServerEntry(
        name="everything",
        package="@modelcontextprotocol/server-everything",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-everything",
        notes="Reference/demo server exercising every MCP capability.",
    ),
    ServerEntry(
        name="sequentialthinking",
        package="@modelcontextprotocol/server-sequentialthinking",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-sequentialthinking",
        notes="Single sequentialthinking tool for chain-of-thought.",
    ),
    ServerEntry(
        name="puppeteer",
        package="@modelcontextprotocol/server-puppeteer",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-puppeteer (archived)",
        notes="Browser automation; navigation/click/screenshot. Archived.",
    ),
    ServerEntry(
        name="brave-search",
        package="@modelcontextprotocol/server-brave-search",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-brave-search (API key)",
        notes="Web search via Brave; archived in monorepo.",
    ),
    ServerEntry(
        name="postgres",
        package="@modelcontextprotocol/server-postgres",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-postgres <url>",
        notes="Postgres read-only query tool. Archived.",
    ),
    ServerEntry(
        name="gdrive",
        package="@modelcontextprotocol/server-gdrive",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-gdrive",
        notes="Google Drive read access. Archived.",
    ),
    ServerEntry(
        name="redis",
        package="@modelcontextprotocol/server-redis",
        tier="B",
        install_hint="npx -y @modelcontextprotocol/server-redis <url>",
        notes="Redis KV operations. Archived.",
    ),
]


def get_server(name: str) -> ServerEntry:
    for s in KNOWN_SERVERS:
        if s.name == name:
            return s
    raise KeyError(f"Unknown server: {name}")
```

- [ ] **Step 4: Hand-author the 4 Tier-A tool-list JSON files**

Each file is an array of objects with `name`, `description`, `inputSchema`. Author from `docs/mcp-tools/<name>.md`. Each tool description should be a 1-2 sentence summary lifted from the README — close to what MCP `tools/list` would return.

**filesystem.json** contains entries for: `read_text_file`, `read_media_file`, `read_multiple_files`, `write_file`, `edit_file`, `list_directory`, `list_directory_with_sizes`, `directory_tree`, `search_files`, `get_file_info`, `create_directory`, `move_file`, `list_allowed_directories` — 13 tools.

**sqlite.json** contains entries for: `read_query`, `write_query`, `create_table`, `append_insight`, `list_tables`, `describe_table` — 6 tools.

**slack.json** contains 8 entries.

**github.json** contains ~30+ representative entries — focus on the categories listed in the docs (no need for all 102; include each unique class of tool: identity, search_code, get_file_contents, create_or_update_file, delete_file, merge_pull_request, actions_run_trigger, list/get/update for issues and PRs, etc.). Aim for at least 35 entries spanning all categories.

(Author each JSON file manually with `Write` tool, lifting names and descriptions from the corresponding `.md` doc.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/atomic_ops/test_server_catalog.py -v`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add src/mcp_security/atomic_ops/server_catalog.py \
        src/mcp_security/atomic_ops/data/tool_lists/*.json \
        tests/atomic_ops/test_server_catalog.py
git commit -m "feat(atomic_ops): server catalog with cached tool lists for 4 tier-A servers"
```

---

## Task 8: Discovery module (live introspection with fallback)

**Files:**
- Create: `src/mcp_security/atomic_ops/discovery.py`
- Test: `tests/atomic_ops/test_discovery.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/atomic_ops/test_discovery.py
import pytest

from mcp_security.atomic_ops.discovery import (
    DiscoveryResult,
    discover_server,
)
from mcp_security.atomic_ops.server_catalog import get_server


def test_discovery_falls_back_to_cached_tool_list():
    server = get_server("filesystem")
    result = discover_server(server, prefer_live=False)
    assert isinstance(result, DiscoveryResult)
    assert result.source in {"cached", "live"}
    assert len(result.tools) > 0


def test_discovery_uses_readme_only_when_no_tool_list():
    server = get_server("memory")
    result = discover_server(server, prefer_live=False)
    # No cached JSON and live not attempted -> readme_only
    assert result.readme_only or result.tools == []


def test_discovery_returns_tools_as_dicts():
    server = get_server("sqlite")
    result = discover_server(server, prefer_live=False)
    assert all("name" in t and "description" in t for t in result.tools)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/atomic_ops/test_discovery.py -v`
Expected: import error.

- [ ] **Step 3: Implement discovery.py**

```python
"""Discover an MCP server's tool list — live via subprocess when possible,
falling back to a cached JSON, then to README-only mode.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .server_catalog import ServerEntry

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryResult:
    """What discovery returned for one server."""

    server: ServerEntry
    tools: list[dict] = field(default_factory=list)
    source: Literal["live", "cached", "readme_only"] = "readme_only"
    error: str | None = None

    @property
    def readme_only(self) -> bool:
        return self.source == "readme_only"


def discover_server(
    server: ServerEntry, prefer_live: bool = False
) -> DiscoveryResult:
    """Return the server's tools using the best available source.

    Order of preference (when prefer_live is True):
      1. Live introspection via MCP subprocess
      2. Cached JSON at server.tool_list_path
      3. README-only mode (empty tools list)

    When prefer_live is False (default), live introspection is skipped entirely
    — useful for deterministic test runs and CI.
    """
    if prefer_live:
        live = _try_live_introspect(server)
        if live is not None:
            return DiscoveryResult(server=server, tools=live, source="live")

    cached = _load_cached(server)
    if cached:
        return DiscoveryResult(server=server, tools=cached, source="cached")

    return DiscoveryResult(server=server, tools=[], source="readme_only")


def _load_cached(server: ServerEntry) -> list[dict]:
    if server.tool_list_path and server.tool_list_path.exists():
        try:
            with server.tool_list_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                return data
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("failed to load cached tool list for %s: %s", server.name, exc)
    return []


def _try_live_introspect(server: ServerEntry) -> list[dict] | None:
    """Attempt to spawn the server via subprocess and call tools/list.

    Returns None on any failure; logs the reason. This is intentionally
    best-effort — many servers need credentials, runtime envs (Node, Docker),
    or network access that may not be available.
    """
    # Implementation: only try if install_hint starts with "npx" or "uvx" AND
    # the corresponding binary is on PATH. Use the MCP Python SDK to spawn
    # via stdio transport. Time out after 30s. On any error, return None.
    #
    # NOTE: This is a SKELETON. The full implementation lives in Task 9b
    # (optional). For initial heatmap generation we use cached + readme_only
    # paths; live introspection is a stretch goal.
    logger.info("live introspection skipped (skeleton) for %s", server.name)
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/atomic_ops/test_discovery.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/mcp_security/atomic_ops/discovery.py tests/atomic_ops/test_discovery.py
git commit -m "feat(atomic_ops): discovery module with cached+readme_only fallback"
```

---

## Task 9: Classifier orchestrator

**Files:**
- Create: `src/mcp_security/atomic_ops/classifier.py`
- Test: `tests/atomic_ops/test_classifier.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/atomic_ops/test_classifier.py
from mcp_security.atomic_ops.classifier import (
    ClassifiedTool,
    classify_server,
)
from mcp_security.atomic_ops.server_catalog import get_server


def test_classify_sqlite_server_returns_readme_and_toollist_classifications():
    server = get_server("sqlite")
    result = classify_server(server)
    # Expect both sources for tier A
    assert len(result.readme_classifications) > 0
    assert len(result.toollist_classifications) > 0


def test_classify_sqlite_write_query_tagged_worst_case_from_toollist():
    server = get_server("sqlite")
    result = classify_server(server)
    write_q = next(
        c for c in result.toollist_classifications if c.tool_name == "write_query"
    )
    assert {"EXECUTE", "DELETE", "SCHEMA_MODIFY", "WRITE"}.issubset(write_q.atomic_ops)


def test_classify_filesystem_write_file_tagged_overwrite():
    server = get_server("filesystem")
    result = classify_server(server)
    wf = next(
        c for c in result.toollist_classifications if c.tool_name == "write_file"
    )
    assert "OVERWRITE" in wf.atomic_ops


def test_max_severity_correct():
    server = get_server("sqlite")
    result = classify_server(server)
    write_q = next(
        c for c in result.toollist_classifications if c.tool_name == "write_query"
    )
    # EXECUTE has severity 5
    assert write_q.max_severity == 5


def test_classification_includes_rule_ids():
    server = get_server("sqlite")
    result = classify_server(server)
    write_q = next(
        c for c in result.toollist_classifications if c.tool_name == "write_query"
    )
    assert len(write_q.rule_ids) > 0


def test_classify_memory_server_is_readme_only():
    server = get_server("memory")
    result = classify_server(server)
    # No cached tool list for tier B
    assert len(result.toollist_classifications) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/atomic_ops/test_classifier.py -v`
Expected: import error.

- [ ] **Step 3: Implement classifier.py**

```python
"""Orchestrates rule application over a server's tools."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import readme_rules, toollist_rules
from .discovery import DiscoveryResult, discover_server
from .rules_base import RuleHit
from .server_catalog import ServerEntry
from .taxonomy import AtomicOp, load_taxonomy

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TAXONOMY = (
    REPO_ROOT
    / "presentations"
    / "heatmap_byhand"
    / "csv"
    / "atomic_operations.csv"
)


@dataclass
class ClassifiedTool:
    """One tool's classification under one source (readme or toollist)."""

    server_name: str
    tool_name: str
    tool_description: str
    atomic_ops: set[str] = field(default_factory=set)
    rule_ids: list[str] = field(default_factory=list)
    max_severity: int = 0
    severity_label: str = ""
    source: str = ""
    notes: str = ""


@dataclass
class ServerClassification:
    """Both source classifications for one server."""

    server: ServerEntry
    readme_classifications: list[ClassifiedTool] = field(default_factory=list)
    toollist_classifications: list[ClassifiedTool] = field(default_factory=list)
    discovery_source: str = "readme_only"


def _extract_readme_tools(readme: str) -> list[tuple[str, str]]:
    """Pull (tool_name, short_description) pairs out of a README.

    Looks for level-3 headers shaped like `### \`tool_name\`` (back-tick-quoted
    tool name), then grabs the first paragraph after the next bolded label
    'What it does:' as the description.
    """
    if not readme:
        return []
    pairs: list[tuple[str, str]] = []
    pattern = re.compile(
        r"^###\s+`([^`]+)`\s*\n+(?:.*?\*\*What it does:\*\*\s*(.+?)(?:\n\n|\Z))?",
        re.MULTILINE | re.DOTALL,
    )
    for m in pattern.finditer(readme):
        tool = m.group(1).strip()
        desc = (m.group(2) or "").strip().replace("\n", " ")
        pairs.append((tool, desc))
    return pairs


def _to_op_set_and_severities(
    hits: list[RuleHit], taxonomy: list[AtomicOp]
) -> tuple[set[str], int, str]:
    ops = {h.atomic_op for h in hits}
    severities = {op.name: (op.severity, op.severity_label) for op in taxonomy}
    if not ops:
        return ops, 0, ""
    pairs = [severities[o] for o in ops if o in severities]
    if not pairs:
        return ops, 0, ""
    max_sev, label = max(pairs, key=lambda p: p[0])
    return ops, max_sev, label


def classify_server(
    server: ServerEntry,
    taxonomy: list[AtomicOp] | None = None,
    prefer_live: bool = False,
) -> ServerClassification:
    """Classify every tool of a server from both README and tool-list sources."""
    if taxonomy is None:
        taxonomy = load_taxonomy(DEFAULT_TAXONOMY)
    readme_text = server.load_readme()
    disc = discover_server(server, prefer_live=prefer_live)

    readme_results: list[ClassifiedTool] = []
    readme_tools = _extract_readme_tools(readme_text)
    for name, desc in readme_tools:
        hits = readme_rules.classify_from_readme(name, desc, readme_text)
        ops, max_sev, label = _to_op_set_and_severities(hits, taxonomy)
        readme_results.append(
            ClassifiedTool(
                server_name=server.name,
                tool_name=name,
                tool_description=desc[:300],
                atomic_ops=ops,
                rule_ids=[h.rule_id for h in hits],
                max_severity=max_sev,
                severity_label=label,
                source="readme",
            )
        )

    toollist_results: list[ClassifiedTool] = []
    for entry in disc.tools:
        name = entry.get("name", "")
        desc = entry.get("description", "")
        schema = entry.get("inputSchema") or entry.get("input_schema") or {}
        hits = toollist_rules.classify_from_toollist(name, desc, schema)
        ops, max_sev, label = _to_op_set_and_severities(hits, taxonomy)
        toollist_results.append(
            ClassifiedTool(
                server_name=server.name,
                tool_name=name,
                tool_description=str(desc)[:300],
                atomic_ops=ops,
                rule_ids=[h.rule_id for h in hits],
                max_severity=max_sev,
                severity_label=label,
                source="toollist",
            )
        )

    return ServerClassification(
        server=server,
        readme_classifications=readme_results,
        toollist_classifications=toollist_results,
        discovery_source=disc.source,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/atomic_ops/test_classifier.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/mcp_security/atomic_ops/classifier.py tests/atomic_ops/test_classifier.py
git commit -m "feat(atomic_ops): orchestrator that runs both rule sets per server"
```

---

## Task 10: XLSX writer

**Files:**
- Create: `src/mcp_security/atomic_ops/xlsx_writer.py`
- Test: `tests/atomic_ops/test_xlsx_writer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/atomic_ops/test_xlsx_writer.py
from pathlib import Path

from openpyxl import load_workbook

from mcp_security.atomic_ops.classifier import classify_server
from mcp_security.atomic_ops.server_catalog import get_server
from mcp_security.atomic_ops.xlsx_writer import write_heatmap


def test_write_heatmap_produces_five_sheets(tmp_path):
    server = get_server("sqlite")
    cls = classify_server(server)
    out = tmp_path / "test_heatmap.xlsx"
    write_heatmap(out, [cls])
    wb = load_workbook(out)
    assert {"README", "ToolList", "Discrepancies", "Coverage", "RuleFireCounts"} <= set(
        wb.sheetnames
    )


def test_readme_sheet_has_thirteen_op_columns_plus_meta(tmp_path):
    server = get_server("sqlite")
    cls = classify_server(server)
    out = tmp_path / "test_heatmap.xlsx"
    write_heatmap(out, [cls])
    wb = load_workbook(out)
    ws = wb["README"]
    header = [c.value for c in ws[1]]
    expected_ops = [
        "EXECUTE",
        "DELETE",
        "OVERWRITE",
        "SCHEMA_MODIFY",
        "BROADCAST",
        "WRITE",
        "MODIFY",
        "MOVE",
        "CREATE",
        "READ",
        "SEARCH",
        "METADATA",
        "LIST",
    ]
    for op in expected_ops:
        assert op in header


def test_toollist_sheet_has_rows_for_sqlite_tools(tmp_path):
    server = get_server("sqlite")
    cls = classify_server(server)
    out = tmp_path / "test_heatmap.xlsx"
    write_heatmap(out, [cls])
    wb = load_workbook(out)
    ws = wb["ToolList"]
    rows = [[c.value for c in r] for r in ws.iter_rows(min_row=2)]
    tool_names = {r[1] for r in rows if r[0] == "sqlite"}
    assert {"read_query", "write_query", "list_tables", "describe_table"} <= tool_names


def test_coverage_sheet_has_per_server_row(tmp_path):
    servers = [get_server("sqlite"), get_server("filesystem")]
    cls_list = [classify_server(s) for s in servers]
    out = tmp_path / "test_heatmap.xlsx"
    write_heatmap(out, cls_list)
    wb = load_workbook(out)
    ws = wb["Coverage"]
    rows = [[c.value for c in r] for r in ws.iter_rows(min_row=2)]
    names = {r[0] for r in rows}
    assert {"sqlite", "filesystem"} <= names
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/atomic_ops/test_xlsx_writer.py -v`
Expected: import error.

- [ ] **Step 3: Implement xlsx_writer.py**

```python
"""Write the 5-sheet atomic-op heatmap workbook."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .classifier import ClassifiedTool, ServerClassification
from .rules_base import ATOMIC_OPS
from .taxonomy import AtomicOp, load_taxonomy

OP_ORDER = [
    "EXECUTE",
    "DELETE",
    "OVERWRITE",
    "SCHEMA_MODIFY",
    "BROADCAST",
    "WRITE",
    "MODIFY",
    "MOVE",
    "CREATE",
    "READ",
    "SEARCH",
    "METADATA",
    "LIST",
]

SEV_COLORS = {
    5: "C00000",
    4: "ED7D31",
    3: "FFC000",
    2: "92D050",
    1: "BDD7EE",
    0: "FFFFFF",
}

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=10)
CENTER = Alignment(horizontal="center", vertical="center")
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)


def _style_header(cell):
    cell.fill = HEADER_FILL
    cell.font = HEADER_FONT
    cell.alignment = CENTER


def _severity_lookup(taxonomy: list[AtomicOp]) -> dict[str, tuple[int, str]]:
    return {op.name: (op.severity, op.severity_label) for op in taxonomy}


def _write_source_sheet(
    wb: Workbook,
    name: str,
    rows: list[ClassifiedTool],
    sev_map: dict[str, tuple[int, str]],
    source_tag: str,
):
    ws = wb.create_sheet(name)
    header = (
        ["server", "tool_name", "tool_description"]
        + OP_ORDER
        + ["max_severity", "severity_label", "matched_rule_ids", "source", "notes"]
    )
    for ci, h in enumerate(header, 1):
        cell = ws.cell(row=1, column=ci, value=h)
        _style_header(cell)

    for ri, t in enumerate(rows, 2):
        ws.cell(row=ri, column=1, value=t.server_name)
        ws.cell(row=ri, column=2, value=t.tool_name)
        ws.cell(row=ri, column=3, value=t.tool_description).alignment = LEFT
        for oi, op in enumerate(OP_ORDER, 4):
            cell = ws.cell(row=ri, column=oi)
            if op in t.atomic_ops:
                sev = sev_map.get(op, (0, ""))[0]
                cell.value = sev
                cell.fill = PatternFill("solid", fgColor=SEV_COLORS.get(sev, "FFFFFF"))
                cell.alignment = CENTER
        base = 4 + len(OP_ORDER)
        ws.cell(row=ri, column=base, value=t.max_severity).alignment = CENTER
        ws.cell(row=ri, column=base + 1, value=t.severity_label).alignment = CENTER
        ws.cell(row=ri, column=base + 2, value=", ".join(t.rule_ids)).alignment = LEFT
        ws.cell(row=ri, column=base + 3, value=source_tag).alignment = CENTER
        ws.cell(row=ri, column=base + 4, value=t.notes).alignment = LEFT

    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 56
    for i in range(4, 4 + len(OP_ORDER)):
        ws.column_dimensions[get_column_letter(i)].width = 8
    ws.freeze_panes = "D2"


def _write_discrepancies(
    wb: Workbook, classifications: list[ServerClassification]
):
    ws = wb.create_sheet("Discrepancies")
    header = [
        "server",
        "tool_name",
        "readme_ops",
        "toollist_ops",
        "ops_only_in_readme",
        "ops_only_in_toollist",
        "likely_reason",
    ]
    for ci, h in enumerate(header, 1):
        _style_header(ws.cell(row=1, column=ci, value=h))

    row = 2
    for c in classifications:
        readme_by_name = {t.tool_name: t for t in c.readme_classifications}
        tl_by_name = {t.tool_name: t for t in c.toollist_classifications}
        all_names = set(readme_by_name) | set(tl_by_name)
        for n in sorted(all_names):
            r = readme_by_name.get(n)
            t = tl_by_name.get(n)
            r_ops = r.atomic_ops if r else set()
            t_ops = t.atomic_ops if t else set()
            if r_ops == t_ops:
                continue
            ws.cell(row=row, column=1, value=c.server.name)
            ws.cell(row=row, column=2, value=n)
            ws.cell(row=row, column=3, value=", ".join(sorted(r_ops)))
            ws.cell(row=row, column=4, value=", ".join(sorted(t_ops)))
            ws.cell(row=row, column=5, value=", ".join(sorted(r_ops - t_ops)))
            ws.cell(row=row, column=6, value=", ".join(sorted(t_ops - r_ops)))
            reason = _likely_reason(r_ops, t_ops, r, t)
            ws.cell(row=row, column=7, value=reason)
            row += 1


def _likely_reason(r_ops, t_ops, r, t):
    if r is None:
        return "tool present only in tool-list (not documented in README)"
    if t is None:
        return "tool documented in README but missing from tool-list source"
    if r_ops - t_ops:
        return "readme rules caught extra ops via prose keywords"
    if t_ops - r_ops:
        return "tool-list rules caught extra ops via name/schema patterns"
    return ""


def _write_coverage(wb: Workbook, classifications: list[ServerClassification]):
    ws = wb.create_sheet("Coverage")
    header = [
        "server",
        "tier",
        "discovery_source",
        "readme_tools",
        "toollist_tools",
        "readme_classified",
        "toollist_classified",
        "readme_unclassified",
        "toollist_unclassified",
        "discrepancy_count",
    ]
    for ci, h in enumerate(header, 1):
        _style_header(ws.cell(row=1, column=ci, value=h))
    for ri, c in enumerate(classifications, 2):
        r = c.readme_classifications
        t = c.toollist_classifications
        rc = sum(1 for x in r if x.atomic_ops)
        tc = sum(1 for x in t if x.atomic_ops)
        ru = sum(1 for x in r if not x.atomic_ops)
        tu = sum(1 for x in t if not x.atomic_ops)
        r_by = {x.tool_name: x.atomic_ops for x in r}
        t_by = {x.tool_name: x.atomic_ops for x in t}
        names = set(r_by) | set(t_by)
        diffs = sum(1 for n in names if r_by.get(n, set()) != t_by.get(n, set()))
        ws.cell(row=ri, column=1, value=c.server.name)
        ws.cell(row=ri, column=2, value=c.server.tier)
        ws.cell(row=ri, column=3, value=c.discovery_source)
        ws.cell(row=ri, column=4, value=len(r))
        ws.cell(row=ri, column=5, value=len(t))
        ws.cell(row=ri, column=6, value=rc)
        ws.cell(row=ri, column=7, value=tc)
        ws.cell(row=ri, column=8, value=ru)
        ws.cell(row=ri, column=9, value=tu)
        ws.cell(row=ri, column=10, value=diffs)


def _write_rule_fire_counts(
    wb: Workbook, classifications: list[ServerClassification]
):
    ws = wb.create_sheet("RuleFireCounts")
    counts: Counter[str] = Counter()
    for c in classifications:
        for t in c.readme_classifications + c.toollist_classifications:
            for rid in t.rule_ids:
                counts[rid] += 1
    for ci, h in enumerate(["rule_id", "fire_count"], 1):
        _style_header(ws.cell(row=1, column=ci, value=h))
    for ri, (rid, n) in enumerate(counts.most_common(), 2):
        ws.cell(row=ri, column=1, value=rid)
        ws.cell(row=ri, column=2, value=n).alignment = CENTER


def write_heatmap(
    out_path: Path,
    classifications: list[ServerClassification],
    taxonomy_path: Path | None = None,
) -> None:
    """Render the 5-sheet workbook to out_path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if taxonomy_path is None:
        from .classifier import DEFAULT_TAXONOMY
        taxonomy_path = DEFAULT_TAXONOMY
    taxonomy = load_taxonomy(taxonomy_path)
    sev_map = _severity_lookup(taxonomy)

    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    all_readme = [t for c in classifications for t in c.readme_classifications]
    all_tl = [t for c in classifications for t in c.toollist_classifications]

    _write_source_sheet(wb, "README", all_readme, sev_map, "readme")
    _write_source_sheet(wb, "ToolList", all_tl, sev_map, "toollist")
    _write_discrepancies(wb, classifications)
    _write_coverage(wb, classifications)
    _write_rule_fire_counts(wb, classifications)

    wb.save(out_path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/atomic_ops/test_xlsx_writer.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/mcp_security/atomic_ops/xlsx_writer.py tests/atomic_ops/test_xlsx_writer.py
git commit -m "feat(atomic_ops): xlsx writer producing the 5-sheet heatmap"
```

---

## Task 11: CLI entrypoint

**Files:**
- Create: `src/mcp_security/atomic_ops/build_heatmap.py`
- Create: `presentations/atomic_op_classification/README.md`

- [ ] **Step 1: Implement build_heatmap.py**

```python
"""CLI entrypoint: classify all known servers and write the xlsx heatmap.

Run with: `uv run python -m mcp_security.atomic_ops.build_heatmap`
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .classifier import classify_server
from .server_catalog import KNOWN_SERVERS
from .xlsx_writer import write_heatmap

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = (
    REPO_ROOT
    / "presentations"
    / "atomic_op_classification"
    / "mcp_tools_atomic_ops.xlsx"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the MCP atomic-op heatmap")
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="Output xlsx path"
    )
    parser.add_argument(
        "--live", action="store_true", help="Attempt live MCP introspection"
    )
    parser.add_argument(
        "--server",
        action="append",
        default=None,
        help="Restrict to specific server names (repeatable)",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    servers = KNOWN_SERVERS
    if args.server:
        wanted = set(args.server)
        servers = [s for s in KNOWN_SERVERS if s.name in wanted]
        if not servers:
            print(f"No known servers matched: {wanted}", file=sys.stderr)
            return 2

    classifications = []
    for s in servers:
        logging.info("classifying %s (%s)", s.name, s.tier)
        classifications.append(classify_server(s, prefer_live=args.live))

    write_heatmap(args.out, classifications)
    print(
        f"Wrote {args.out} — {len(servers)} servers, "
        f"{sum(len(c.readme_classifications) for c in classifications)} README rows, "
        f"{sum(len(c.toollist_classifications) for c in classifications)} tool-list rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run end-to-end to verify it produces an xlsx**

Run (after backing up any existing xlsx at that path):
```bash
uv run python -m mcp_security.atomic_ops.build_heatmap
```
Expected: prints a one-line summary, writes `presentations/atomic_op_classification/mcp_tools_atomic_ops.xlsx`.

- [ ] **Step 3: Open the xlsx and spot-check**

Verify visually (using `openpyxl` from a small script if you don't have Excel) that:
- README sheet has rows for the 4 tier-A servers
- ToolList sheet has rows for those 4 servers
- Discrepancies sheet is populated
- Coverage sheet has one row per server
- RuleFireCounts sheet lists firing rules

If any sheet is empty unexpectedly, return to the relevant rule module and refine.

- [ ] **Step 4: Write the folder README**

`presentations/atomic_op_classification/README.md`:

```markdown
# Atomic-Op Classification

This folder holds the rules-based atomic-op heatmap for MCP servers. The
heatmap is generated by `src/mcp_security/atomic_ops/`.

## Files

- `mcp_tools_atomic_ops.xlsx` — 5-sheet workbook with the classifications.

## Sheets

| Sheet | Contents |
|-------|----------|
| README | Each tool's atomic-op tags derived from the server's README/description text. |
| ToolList | Each tool's atomic-op tags derived from the live (or cached) MCP tool list. |
| Discrepancies | Rows where README and tool-list classifications differ for the same tool. |
| Coverage | Per-server coverage stats: tool counts, classified vs unclassified, discrepancy count. |
| RuleFireCounts | How often each rule_id fired across all classifications — diagnostic aid. |

## Regenerating

```
uv run python -m mcp_security.atomic_ops.build_heatmap
```

Add `--live` to attempt MCP subprocess introspection (best-effort; many
servers need credentials and will fail).

Add `--server <name>` (repeatable) to classify a subset of servers.

## Threat model

MCP servers are the protected asset; agents are the threat. Atomic-op
severity (1-5) reflects the damage an agent could cause via that tool. The
taxonomy itself lives at `presentations/heatmap_byhand/csv/atomic_operations.csv`.
```

- [ ] **Step 5: Commit**

```bash
git add src/mcp_security/atomic_ops/build_heatmap.py \
        presentations/atomic_op_classification/README.md \
        presentations/atomic_op_classification/mcp_tools_atomic_ops.xlsx
git commit -m "feat(atomic_ops): CLI entrypoint, regenerated heatmap, folder README"
```

---

## Task 12: Iterate — refine rules from real misses

**Files:**
- Modify: `src/mcp_security/atomic_ops/readme_rules.py`
- Modify: `src/mcp_security/atomic_ops/toollist_rules.py`
- Modify: `src/mcp_security/atomic_ops/data/tool_lists/*.json` (only if missing/wrong)
- Modify: `presentations/heatmap_byhand/csv/changes_log.md`

- [ ] **Step 1: Inspect the heatmap's Discrepancies and unclassified rows**

Run a small inspection script in `scripts/atomic_ops_inspect.py` (one-shot, not committed):
```python
from openpyxl import load_workbook
wb = load_workbook("presentations/atomic_op_classification/mcp_tools_atomic_ops.xlsx")
for sheet in ("README", "ToolList"):
    ws = wb[sheet]
    print(f"\n=== {sheet} unclassified ===")
    header = [c.value for c in ws[1]]
    op_cols = [i for i, h in enumerate(header) if h in {"EXECUTE","DELETE","OVERWRITE","SCHEMA_MODIFY","BROADCAST","WRITE","MODIFY","MOVE","CREATE","READ","SEARCH","METADATA","LIST"}]
    for row in ws.iter_rows(min_row=2, values_only=True):
        if all(row[i] in (None, "", 0) for i in op_cols):
            print(row[0], row[1], "-", row[2][:80] if row[2] else "")
```

- [ ] **Step 2: For each unclassified tool, decide one of**
  - Add a new rule (with a test) to catch it.
  - Confirm that no atomic op applies → mark in notes; OK to leave blank.
  - Propose a new atomic op (rank ≥ 14). Append to `atomic_operations.csv`, log in `changes_log.md`.

- [ ] **Step 3: For each discrepancy, decide one of**
  - The discrepancy is legitimate (README and tool-list emphasise different aspects) → leave it.
  - One side is wrong → refine the rule or fix the cached tool list.

- [ ] **Step 4: Re-run tests + regenerate the heatmap**

```bash
uv run pytest tests/atomic_ops/ -v
uv run python -m mcp_security.atomic_ops.build_heatmap
```
Expected: tests pass; heatmap regenerates with fewer unclassified / refined discrepancies.

- [ ] **Step 5: Commit iteration**

```bash
git add src/mcp_security/atomic_ops/readme_rules.py \
        src/mcp_security/atomic_ops/toollist_rules.py \
        src/mcp_security/atomic_ops/data/tool_lists/ \
        presentations/heatmap_byhand/csv/changes_log.md \
        presentations/heatmap_byhand/csv/atomic_operations.csv \
        presentations/atomic_op_classification/mcp_tools_atomic_ops.xlsx \
        tests/atomic_ops/
git commit -m "refactor(atomic_ops): rule iteration pass; refine misses and discrepancies"
```

---

## Task 13: Final verification + ruff

- [ ] **Step 1: Run ruff**

Run: `uv run ruff check src/mcp_security/atomic_ops/ tests/atomic_ops/`
Expected: no errors. Fix any issues.

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest -v`
Expected: every test in tests/atomic_ops/ passes; the existing tests/ unaffected.

- [ ] **Step 3: Print final summary**

After tests/lint pass, print the one-screen summary:
- # servers processed
- # tools classified (README + tool-list, sum)
- # discrepancies
- # new atomic ops added
- Path to the xlsx

- [ ] **Step 4: Final commit if anything changed**

```bash
git add -A
git commit -m "chore(atomic_ops): ruff and final cleanup"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Backup csv before edits → Task 1
- [x] Discover MCP servers → Task 7 server_catalog (>=10 known)
- [x] Both README and live tool-list sources → Tasks 4-6 (rules), Task 8 (discovery), Task 9 (classifier)
- [x] Python rule modules with RuleHit interface → Tasks 3-6
- [x] Tests with table-driven cases → every rule file has them
- [x] Apply and classify every tool → Task 9, Task 11
- [x] 5-sheet xlsx (README / ToolList / Discrepancies / Coverage / RuleFireCounts) → Task 10
- [x] New folder with sensible name + README → Task 11
- [x] Iterate pass → Task 12
- [x] uv run pytest passes → Task 13
- [x] uv run ruff check passes → Task 13

**Threat-model direction:** All atomic-op severities reflect agent-caused damage to the server. Confirmed by reading taxonomy reasoning column. ✅

**Placeholder scan:** Every task contains the actual code for the file it produces (no "TODO" or "fill in"). ✅

**Type consistency:** `RuleHit`, `AtomicOp`, `ClassifiedTool`, `ServerClassification`, `DiscoveryResult`, `ServerEntry` are referenced consistently across tasks. ✅
