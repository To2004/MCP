# `atomic_flags.py` — post-scan enrichment

**402 lines.** `enrich_scan(table, tools, use_llm=...)` runs after the matrix is
built and adds two per-tool annotations. **Neither one changes a score.**

| Field added | What it holds |
|---|---|
| `tool_atomic_ops` | the tool mapped onto the project's atomic-operation taxonomy (`docs/standards/atomic-op-classification.md`) — READ / CREATE / MODIFY / DELETE / EXECUTE and friends |
| `tool_input_ranking` | a per-parameter risk ranking (r1–r5): which inputs let a caller widen what one call does |

## Why it is separate from tool impact

These describe the same tool the impact ladder just classified, but they answer
different questions and feed different consumers. The atomic op is a *taxonomy
label* used for cross-server comparison and for the CIA facet work in v6; the
input ranking is what the **dynamic** stage needs, because it prices the actual
argument a caller passed.

Keeping them out of the impact tier is the same discipline that keeps parameters
from moving the tier in `static_impact.py`: a parameter states what a caller
*could* pass, and what any given call *does* pass is a runtime fact.

## Reading it in the artifact

`tool_input_ranking` is the field to look at when a tool's impact tier seems low
for how dangerous it feels. `search_code` scores impact 3 (a content read), but its
ranking flags the free-form query parameter — the reason its blast reaches 5 on
`code-records` via the `population` escape. The three primitives price the tool;
this field explains where a runtime surprise would come from.
