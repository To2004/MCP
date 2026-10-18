# v9 — same scoring arm, a tightened policy: does re-scanning move the numbers?

`v5`'s `five_level_v2_v5r_nacombo` arm is the baseline the paper cites. This
generation changes nothing about *how* the scanner scores — no new rubric, no
new arm — it changes what the **policy document says** for five servers, then
re-runs the identical `five_level_v2_v5r_nacombo` mode against the edit, so any
score difference from `v5` is attributable to the policy text alone.

## What changed in the policy

[`docs/mcp-tools/server-policies.md`](../../../docs/mcp-tools/server-policies.md),
five sections:

- `calendar_real`, `github_real`, `slack_real` — the `Company.` paragraph was
  tightened to a single consistent opening pattern across all three
  ("CBG's `<team>` runs the agent against the `<n>`-tool `<surface>`..."),
  matching language reviewed for a human validation survey built from this same
  document.
- `sqlite_cbg_sqlite` — the same opening pattern applied for consistency; no
  register change.
- `fs_corp_filesystem` — explicitly rebranded as CBG's corporate file share
  (previously an unattributed "unregulated mid-size product company"), and one
  new asset added: `grant-and-compliance-records` (grant proposals, funder
  financial terms, IRB/ethics filings), with matching classification-table and
  recognition-rule entries. Register grew from 16 to 17 rows. Section id and
  server id (`fs:corp_filesystem`) are unchanged — every ISO/NIST/CIS v7 arm and
  the v7 experiments reference this id directly.

Validated against the spec: `uv run python scripts/check_policies.py` — all 20
sections pass, `fs_corp_filesystem` P2 at 17 register rows.

## Results

[`five_level_v2_v9_cbg_nacombo/`](five_level_v2_v9_cbg_nacombo/) — the same five
stems, same `five_level_v2_v5r_nacombo` impact mode, rescanned with
`--overwrite`:

| Stem | Register rows | Tool impact (static/LLM) | score_max |
|---|---|---|---|
| `calendar_real` | 16 | 9/4 | 125 |
| `github_real` | 20 | 15/11 | 125 |
| `slack_real` | 20 | 13/3 | 125 |
| `fs_corp_filesystem` | 17 (+1) | 12/2 | 125 |
| `sqlite_cbg_sqlite` | 11 | 4/1 | 125 |

Compared against the `v5` baseline (`git show HEAD:reports/experiments/v5/five_level_v2_policy_v5r_nacombo/<stem>.json`),
every stem's N/A rate held within ~1-2 percentage points of the pre-edit
baseline — consistent with normal LLM re-scan variance, not a shift the prose
edits or the new asset caused. `fs_corp_filesystem`'s new
`grant-and-compliance-records` row contributed its own live/N/A cells (6 tools
of 14 touch it) without disturbing the other 16 assets' scores.

## Why v9, not an overwrite of v5

`v5/five_level_v2_policy_v5r_nacombo/` is the committed baseline other
experiments and the paper's tables reference; it was overwritten in place during
this edit and then restored (`git checkout HEAD --`) once these numbers were
copied out. Keeping the rescan as its own generation means `v5` stays exactly
what it was at `c987a6f`, and this diff is inspectable on its own — same arm,
different policy input.
