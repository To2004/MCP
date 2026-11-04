# Synthetic example: the analysis path end to end

Everything in this folder is **synthetic**. No person answered these; the files only show
that a responses file in the documented format runs through `analyse_responses.py` against the
committed `items.json` and `key.json`.

## Files

| File | What it is |
|---|---|
| `make_synthetic_responses.py` | writes the synthetic responses: seeded random answers, 10 "people" (one fails the wild attention check, one stops early, as extra cases) and 2 "Claude" runs; every document says `"synthetic": true` |
| `synthetic_responses.json` | its output, a JSON list of response documents |
| `synthetic_results.md`, `synthetic_results.json` | the analysis of that file; the report opens with a "Synthetic data" banner |

The answers are random, so the numbers in the report mean nothing: they are not results of
the study and must not be quoted.

## Rebuild

```bash
uv run python reports/experiments/dynamic_dimensions/human_study/examples/make_synthetic_responses.py
uv run python reports/experiments/dynamic_dimensions/human_study/analyse_responses.py \
    --responses reports/experiments/dynamic_dimensions/human_study/examples/synthetic_responses.json \
    --key reports/experiments/dynamic_dimensions/human_study/key.json \
    --items reports/experiments/dynamic_dimensions/human_study/items.json \
    --out reports/experiments/dynamic_dimensions/human_study/examples/synthetic_results.md
```

## References

- [../README.md](../README.md): the study, the response format and the analysis
