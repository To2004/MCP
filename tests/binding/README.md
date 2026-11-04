# Binding tests

Tests of the runtime asset binding's v5 parts (`src/mcp_security/binding/`): the target inputs
that price a call, the touched asset the behaviour engine compares, and the operation keys.
The older discovery and resolver tests stay in `tests/test_binding.py`.

## Files

| File | What it tests |
|---|---|
| `test_matrix_targets.py` | AI-3: with the scan's `tool_targets`, the priced asset reads only the target inputs, so a decoy path cannot lower it and free text cannot raise it; on a tie the target-input path prefers the container the call named, then the first id; without `tool_targets` every call scores as it did before AI-3 |
| `matrix_golden.json` | The pin for that last check: 24 calls and the `CallScore` that `MatrixScorer` gave each one before AI-3 |
| `test_touched_asset.py` | AI-1, AI-2, AI-12, AI-13 (exact dict and unique match), EXP-1: named, unregistered, ambiguous and missing containers; keyed pseudonyms, which the lookup requires; owners, so a registered name under another owner is someone else's container; declared and inferred containers; several containers per call and their bounds; exposure; exact hits in a 10^5-id register |
| `test_operation_key.py` | AI-7: `tool:operation` keys and their read or write labels |

## Fixtures

The scan and the register are the simulated Helios Grid GitHub route in
`reports/experiments/gateway/github_remote/`. The smaller registers in the tests are
invented. Nothing here is a real organisation, person or credential. The pseudonym key is a
test-only constant.

The touched-asset tests build the route's register three ways:

- `register` / `lookup`: from the policy rows, as J3 can today. The containers are inferred,
  because the rows mix repositories with data classes such as `branch-heads`. The registered
  repository `helios/website` makes `helios` the deployment's owner.
- `declared`: the same rows once the scan declares its containers (`asset_containers`), here
  the five `helios-*` repositories. Only here may a unique name match fire a floor.
- `ownerless`: no registered repositories or owners. Two tests pin what this costs: a
  registered name names its asset under any owner, and a fork's destination folds into its
  source.

`fork_repository` declares its destination as the repository GitHub creates,
`{"inputs": ["organization", "repo"], "owner": "organization"}`. This is the shape the scanner
should emit.

## Timing

The 10^5-id test times exact hits only. Its bound is 1 ms per hit, about 50 times the
synthetic development timing of about 20 us. The name pass has no bound until AI-13's token
index (deferred) exists: in development timings it costs about 20 us per container.

## The pin and ties

On the v1-v4 path, when several surviving assets share the top cell, `MatrixScorer` picks the
driver in set order, and that order changes with `PYTHONHASHSEED`. This was true before AI-3.
The pin therefore checks the driver exactly only for the 20 calls without such a tie. For the
other 4, it checks that the driver is one of the tied assets. The target-input path breaks a
tie in favour of an asset the call named, then by asset id.

To rebuild the pin, score each call in `matrix_golden.json` with
`MatrixScorer(scan["cells"], scan["bands"])` and write the `CallScore` fields back. Do this only
when a change is meant to move the v1-v4 priced asset. Such a change also needs a line in
`tests/gateway/golden/CHANGELOG.md`.
