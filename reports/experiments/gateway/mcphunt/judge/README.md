# Independent judge on MCPHunt calls

A second model (`gemma3:27b`) rated 600 sampled MCPHunt calls 1-5, giving the per-call ground truth MCPHunt does not have. The method and findings are in the [experiment README](../README.md#independent-judge-call-by-call).

## Files

| File | What it is |
|---|---|
| `sample.jsonl` | The 600 calls: route, tool, full arguments (values cut at 2,000 characters), the run's six earlier calls, MCPHunt's labels, and the framework's scores under `ours` (kept from the judge). Not in git: it carries MCPHunt's fake Slack token, which GitHub's secret scanner blocks. The seeded `sample` command under Re-run rebuilds it |
| `verdicts.jsonl` | One line per call: `risk` 1-5, the asset the judge named, `policy_violation`, a one-sentence reason |
| `report.md`, `report.json` | The grade: the judge against MCPHunt's labels, then the framework against the judge, with over- and under-scored examples |

## Re-run

```bash
uv run python scripts/judge_mcphunt_calls.py sample --logs external/mcphunt/gateway_logs/spread90 \
    --out reports/experiments/gateway/mcphunt/judge/sample.jsonl
sbatch scripts/judge_mcphunt_calls.sbatch   # resumable; pull gemma3:27b on the login node first
uv run python scripts/judge_mcphunt_calls.py grade \
    --sample reports/experiments/gateway/mcphunt/judge/sample.jsonl \
    --verdicts reports/experiments/gateway/mcphunt/judge/verdicts.jsonl \
    --out reports/experiments/gateway/mcphunt/judge/report.md
```
