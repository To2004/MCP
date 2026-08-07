# staticscanner — policy-derived asset sensitivity

Output of the static scanner run that **derives each asset's sensitivity from
the organization's written policy** instead of being told it.

The policies in [`docs/mcp-tools/server-policies.md`](../../../docs/mcp-tools/server-policies.md)
carry no sensitivity numbers — only a data-classification table (class ·
adverse impact · examples), an asset register (asset · description · tools ·
CIA) and recognition rules. The scanner enumerates the server's assets,
classifies each one against that policy, and maps the class's adverse-impact
language onto its own 1–5 rubric.

## Contents

| File | What it is |
|---|---|
| [`asset-sensitivity.md`](asset-sensitivity.md) | The readable report: one section per MCP, every asset with its derived 1–5, plus the register's description and tools |
| [`scoring-prompts-AS-RUN.md`](scoring-prompts-AS-RUN.md) | Every prompt this scan sent to the model, verbatim — including the policy-matched sensitivity rubric (classify → map) and the preamble that carries the org policy into it |
| `<stem>.json` | Full scan artifact (`asset_sensitivity`, blast, bands, tool impact) |
| `<stem>.md` | Per-server scan report |
| `<stem>_matrix.csv` | The tool × asset matrix |
| `no_sens/` | The companion arm that drops the sensitivity primitive (`blast × impact`), same policy document — not yet run |

## Commands

| Action | Command |
|---|---|
| Scan (GPU) | `sbatch scripts/scan_policy_sens.sbatch <stems>` (omit stems for all 11; add `overwrite` as a 2nd arg to re-scan) |
| Dump the prompts as run | `uv run python scripts/dump_scoring_prompts.py --impact-mode five_level_v2_na --org-desc --out reports/experiments/staticscanner/scoring-prompts-AS-RUN.md` |
| Regenerate the report | `uv run python scripts/report_policy_sensitivity.py` |
| Compare vs baselines | `uv run python scripts/compare_policy_sensitivity.py --stem <stem>` |

## Status

`calendar_real` is scanned. Its policy section is the only one written to the
full register scheme ([spec](../../../docs/standards/mcp-policy-spec.md)); the
other ten are still prose-only, so scanning them measures the weaker
description rather than the scheme.

Result vs the organization's own numbers (from `server-profiles.md`, never
shown to any scan): no-context scanning gives MAE 1.06 / 19% exact; the
policy-derived scan gives **MAE 0.06 / 94% exact / 100% within-1** — 15 of 16
assets match the organization exactly, the sixteenth by one tier.

What it took, in order of effect:

1. The policy-matched **classify → map** sensitivity prompt (`ASSET_TASK_POLICY`)
   instead of the generic anchors — MAE 1.06 → 0.50.
2. A **metadata-only cap** and an **aggregation** rule in that prompt — → 0.31.
3. A **control-plane anchor** at tier 5 (losing it rewires what every tool can
   reach), so a config hub can reach 5 without being exfiltration-shaped.
4. A **`Routine` class** in the policy itself. The four-class ladder
   (Restricted/Confidential/Internal/Public) maps to tiers 5/4/3/1 — nothing
   maps to 2, so listings had nowhere to land and were pulled up into Internal.
   Adding it fixed four assets at once — → **0.06**.
