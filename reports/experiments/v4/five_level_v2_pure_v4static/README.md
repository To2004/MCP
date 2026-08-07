# v4-static — deterministic tool impact (no scan run)

The full scan for this arm was **cancelled on request**; this folder holds the
tool-impact result only.

| File | What |
|---|---|
| `static_tool_impact.md` | tool impact for every tool on all four servers, computed with **no LLM** by `src/mcp_security/static_scoring/static_impact.py`, with the evidence behind each score and the v3 LLM value beside it |
| `inputs/calendar_real.tools.json` | the tool catalog |
| `inputs/calendar_real.profile.md` | the org profile |

Agreement with the v3 LLM impacts: **58/69 = 84%** overall (slack 94 %, fs 86 %,
github 81 %, calendar 77 %).

The `five_level_v2_v4_static` mode remains wired in the pipeline, so the full
scan can be produced later with:

```
sbatch --job-name=mcp-v4st --export=ALL,MODE=five_level_v2_v4_static,\
ONLY=calendar_real,OUT_DIR=<repo>/reports/experiments/v4/five_level_v2_pure_v4static \
scripts/scan_pure.sbatch
```

Note: the "bulk drops a safety ⇒ +1 tier" rule was removed from v4, so
`create-events` scores 4 (the same as `create-event`) rather than 5.
