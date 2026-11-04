# Behaviour golden files

These files pin outputs of the behaviour layer that must not move by accident. The tests in
`tests/behaviour/` compare the code against them on every run.

## Files

| File | What it pins | Test |
|---|---|---|
| `engine_v1.json.gz` ... `engine_v4.json.gz` | INF-1, for one design on the seeded stream built by `tests/behaviour/golden_stream.py`: every verdict (multiplier, strongest, score, the scores dict, warm-up flag; floats rounded to 1e-9, compared message by message); `exact_sha256`, the SHA-256 of every verdict's exact floats (`float.hex`), with `recorded_on` (machine and OS: exact digests are compared only there); `snapshot_sha256`, the engine's snapshot after the stream; `restore`, every verdict after a snapshot -> JSON -> restore into a fresh engine at day 15; and the stream's SHA-256 | `test_golden_designs.py` |
| `policy_v*.json` | INF-4: the exact bytes `config_to_json` wrote for v1-v4 policies before v5 (the CLI's `indent=1` format), so v4 policy files and their digests never move | `test_policy_design_scope.py` |
| `CHANGELOG.md` | One line per regeneration, naming the change that moved the output | |

## Regenerating

Regenerate only when a change to v1-v4 output is intended, and say which change it is. The
v5 work keeps v1-v4 bit-identical: E1, E2 and RF9 run only under `legacy_fixes`.

```bash
uv run python -m tests.behaviour.golden_stream --reason "E1: <why v4 output changes>"
```

This rewrites `engine_v1.json.gz` to `engine_v4.json.gz` and appends the reason to
`CHANGELOG.md`. To show a regeneration does not move v1-v4, record it with the engine of the
commit before the change (that tree's `src` first on `sys.path`, as the 2026-10-26 entry
was) and check that the current engine still passes. The `policy_v*.json` files are never regenerated: v4 policy JSON is
byte-identical by contract (INF-4).

## References

- [v5 implementation plan](../../../reports/experiments/dynamic_dimensions/knowledge_base/v5-implementation-plan.md), Batch 0
- [v5 design spec](../../../reports/experiments/dynamic_dimensions/knowledge_base/v5-design-spec.md), sections 4.1 and 4.2
