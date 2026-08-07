# `fallback.py` — the heuristics that never run here

**256 lines, zero of them executed in this run.**

The module holds deterministic stand-ins for every model stage: `domain_profile()`,
`tool_impact()`, `asset_sensitivity()`, `blast_radius()`. They key off MCP
annotations, the shared `mcp_security.sensitivity` anchor tables, and crown-jewel
name escalation.

## Why it is in the snapshot anyway

Because it sits behind every model call in `pipeline.py`, and its *absence* from
the execution path is a property of the run worth being able to verify.

The driver passes `strict=True`. In strict mode `StaticScorer._ask()` raises
`LLMUnavailableError` when the model returns nothing, and `_strict_fail()` raises
when it returns something unusable — so no fallback value can reach a scored cell.
A reader who wants to confirm the numbers are the model's and the rules', not a
hardcoded table's, needs to be able to see what the hardcoded table *would* have
said and that nothing called it.

The corresponding artifact fields make the same guarantee from the other side:
`model_reviewed: true` and no `needs_human_review` flag mean no fallback was used.

## Where it does run

Offline smoke tests — `scripts/scan_policy_v5.py --no-llm` — which exercise the
plumbing end to end without a GPU. Those runs are marked
`provenance: "offline-baseline"` and their numbers are meaningless by construction.

One note: `fallback.tool_impact()` is also the source of the `fb_impact` clamp
bound in the impact stage, so it participates in bounding a model answer to 1–5
even in a strict run. It never *supplies* a value there.
