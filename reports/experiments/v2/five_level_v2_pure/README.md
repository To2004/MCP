# Experiment `pure` — tools + description as the ONLY scanner inputs

Calendar:real scanned with the registry built entirely from two documents: the
captured 13-tool catalog and the org profile (spec-v1 table: Contents grammar +
flags + Sens.). No store enumeration, no demo asset scopes, no LLM-generated
homing assets. Scoring machinery identical to `five_level_v2_ult`.

## Result: the description alone reproduces the full scan

Band agreement with the full ult calendar scan (which had the demo asset scopes
and generated homing assets): **64 / 67 shared scored cells (95.5%)** — 1 cell
higher, 2 lower. Every headline cell matches:

- `delete-event` → high on personal (irreversibility band floor) and 60/high on
  executive + recruiting (gated blast floor)
- `manage-accounts` on `connected-account-config` (the org-flagged `hub` +
  `self-sufficient` asset) → 125 critical, the maximum
- recon tools (list/colors/free-busy) stay low/medium — no inflation

Distributions: pure {low 23, med 37, high 8, crit 2, na 138} vs ult
{low 24, med 46, high 6, crit 2, na 130} — pure marks slightly more pairs N/A
(its asset descriptions come from the org's Contents cells, which are sharper
about what a tool does not touch).

## Rerun stability (k = 3)

Three independently scheduled GPU runs of the identical configuration
(`five_level_v2_pure`, `five_level_v2_pure_rerun`, `five_level_v2_pure_rerun2`)
are **bit-identical**: all 208 cells — raw blast, N/A decisions, tool impacts,
scores, bands — match byte for byte across all three (matrix CSVs diff empty).
Greedy decoding (temperature 0, seed 0) plus a fully deterministic registry
(profile table, no generated assets) leaves no variance source.

## Why this matters

This is the realistic deployment: a gateway scoring an MCP server it cannot
open. The store-walking and asset-generation plumbing contributed almost
nothing the org's written profile did not already carry — the profile spec
(Contents + flags + Sens.) is sufficient input for the scanner on this server.
