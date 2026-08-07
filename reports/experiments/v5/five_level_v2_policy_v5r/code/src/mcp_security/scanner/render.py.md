# `render.py` — turning the table into readable output

**292 lines.** Two functions, both pure formatting — no scoring logic.

| Function | Produces |
|---|---|
| `scan_to_markdown(server, kind, table)` | `<stem>.md` — the readable report |
| `matrix_csv(table)` | `<stem>_matrix.csv` — the tool × asset grid |

## What the markdown report contains

The inferred domain, the three primitive tables (tool impact, asset sensitivity,
blast radius), the scored `cells` with their bands, the band distribution, and the
`deterministic_rules` manifest — so a reader can see which assembly passes ran
without opening the JSON.

## Why the CSV exists separately

The matrix is the artefact people actually compare between arms: one row per
asset, one column per tool, the cell score or `na`. It diffs cleanly, loads into a
spreadsheet, and is what `scripts/compare_*.py` read.

`na` in a cell is not a zero. It means the blast stage judged that this tool does
not act on this asset at all (`affects_asset: false`), so the pair was never
scored. On `github_helios` that is 352 of 494 cells — most tools touch most assets
not at all, and collapsing that to 0 would make the totals meaningless.

## What it does not do

It never recomputes anything. Every number it prints comes from the table
`pipeline.build_static_table()` returned, which is why the report and the JSON can
never disagree.
