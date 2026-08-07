# v5 — `five_level_v2_v5`, the policy-grade run

Scans of `calendar_real`, `github_real` and `slack_real` in which the
organization supplies **no sensitivity number at all**. Everything the scanner
knows comes from two documents per server: the captured tool catalog and the
org's policy section.

Design and rationale: [`../README.md`](../README.md).
Full tables: [`EVALUATION.md`](EVALUATION.md).

**Headline.** Derived sensitivity matches the organization on 50 of 56 assets
(88–90 % exact per server, **100 % within one tier**, MAE 0.10–0.125). The
deterministic ladder decided **55 of 55** tool impacts with no model call,
agreeing with v4's LLM on 51. Blast moved on 19–22 % of cells, which is this
stage's own variance rather than an input effect.

## Files

| File | What |
|---|---|
| `<stem>.json` | the full scan artifact — derived `asset_sensitivity`, `tool_impact` + `tool_impact_source`, `static_impacts` (ladder evidence per tool), raw and assembled `blast_radius`, `cells`, `bands`, and the `deterministic_rules` manifest |
| `<stem>.md` | the readable per-server report |
| `<stem>_matrix.csv` | the tool × asset severity matrix |
| `EVALUATION.md` | derived sensitivity vs the organization's held-out numbers, the impact hand-off ledger, and the v4↔v5 diff |
| `evaluation.json` | the same, machine-readable |
| `sensitivity_comparison.csv` | per asset: org truth · v5 derived · error · v4's table value · flags |
| `impact_comparison.csv` | per tool: v5 impact · which scorer decided it · the ladder's evidence · v4's model answer |
| `ALL_SERVERS_summary.csv` | one row per server: accuracy, hand-off counts, bands, Σ score |
| `scoring-prompts-AS-RUN.md` | every prompt this run sent to the model, verbatim |
| `inputs/<stem>.policy.md` | the policy section the scan consumed |
| `inputs/<stem>.tools.json` | the tool catalog the scan consumed |
| `inputs/<stem>.register.csv` | the parsed asset register — the machine view of what the org disclosed |
| `inputs/manifest.json` | sha256 of both inputs per server, so a result is traceable to its exact inputs |

## Reading the artifact

Three fields carry what is new in this arm:

- **`sensitivity_source: "llm_policy_class"`** — the number was derived, not
  supplied. `asset_sensitivity` is the model's classify-then-map output.
- **`tool_impact_source`** — `static_ladder` or `llm_fallback` per tool. The
  deterministic ladder answers unless it had no verb evidence at all; then the v4
  impact prompt decides and `static_impacts[tool]` records the abstention, its
  reason, and the tier the ladder would otherwise have defaulted to.
- **`asset_flags`** — the register's `Flags` cells, which are what a tier-5 blast
  must cite and what exempts an asset from the deterministic read roof.

`blast_radius_raw` and `tool_impact_raw` hold the model's verbatim answers before
the deterministic assembly; `alias_fixups`, `bulk_fixups`, `roof_fixups` and
`blast_floor.raised_cells` account for every change the assembly made.

## Caveats

- **The LLM fallback never fired.** The three real vendor catalogs declare no MCP
  tool annotations, so the ladder's confidence is set by description verbs alone:
  every one of the 55 tools matched a tier verb (confidence 0.8) and none reached
  the 0.35 abstention branch. On this corpus the hand-off is therefore untested
  in anger — its behaviour is covered by
  `tests/static_scoring/test_policy_register.py` instead. A catalog with
  vocabulary the ladder does not carry (or a server that declares annotations but
  writes a terse description) is where it would matter.
- **Calendar scores one asset worse than the earlier probe.**
  [`../../staticscanner/`](../../staticscanner/) reached 94 % exact on calendar
  (15/16) against v5's 88 % (14/16). The extra miss is `account-directory`, and
  the likely cause is an input change rather than a scoring change: the earlier
  run described assets from the declarative registry ("the list of linked
  accounts"), while v5 uses the policy register, where that row sits directly
  beneath `connected-account-config` — an asset the classification table calls
  Restricted. Adjacency in the register appears to pull a neighbouring row up a
  tier.
- **Half the blast movement is the relevance gate.** Of the cells that differ
  from v4, 15/40 (calendar), 32/100 (github) and 16/72 (slack) went from scored
  to N/A, plus 11/21/8 in the other direction. The register's `Tools` column
  states which tool acts on which asset, and the model does not always agree with
  it — that disagreement, not a tier change, is the largest single source of
  difference between the arms.
- `get-current-time` (calendar) touches no organizational asset and has no
  register row; the policy says so in prose and its cells come back N/A. That is
  the intended behaviour, not a coverage gap.
