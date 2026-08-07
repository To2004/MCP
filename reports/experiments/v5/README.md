# v5 — the policy-grade arm: the organization supplies no numbers

The last thing the scanner was still being handed is the answer. Through v4, the
organization gave the scan a per-asset `Sens.` 1–5 table and the model scored only
reach and action type. Real organizations do not publish that table: the
inventory is itself sensitive, per-asset labels drift the week after they are
written, and what a security function actually ships is a *policy*.

v5 removes it. Each server's only inputs are:

1. the captured tool catalog (`tools/list` — name, description, parameters), and
2. the organization's **policy** section in
   [`docs/mcp-tools/server-policies.md`](../../../docs/mcp-tools/server-policies.md) —
   a data-classification table stating adverse impact per class, an asset
   register (asset · description · tools · flags · CIA), recognition rules with a
   fail-closed default, operation limits, expected use and loss priorities, and
   **no 1–5 anywhere**.

The per-asset table in `server-profiles.md` is held out entirely and used only
afterwards, as ground truth for how close the derived numbers came.

## What changed from v4

| Stage | v4 | v5 | Why |
|---|---|---|---|
| Org context | `server-profiles.md` — per-asset `Sens.` inventory | `server-policies.md` — classification policy, no numbers | The inventory is the disclosure a real org refuses. Testing the framework on a document nobody will hand you measures nothing. |
| Asset registry | the profile table's rows | the **policy register's** rows | Keeps the org in control of what gets scored, and makes the inventory deterministic instead of LLM-enumerated. |
| Asset sensitivity | read off the org's table | LLM **classify → map**: find the register row, apply the recognition rules, map that class's adverse-impact language onto 1–5 | The org states consequences in its own vocabulary; the rubric owns the scale. This is how FIPS 199 / SP 800-60 and the university standards actually work. |
| Tool impact | LLM (v4 prompt), or the all-rules `v4static` arm | **deterministic ladder first**, the v4 impact prompt only where the ladder abstains | v4 showed impact is rule-derivable (0–3 disagreements/server). Rules where they know; the model where they cannot. |
| Blast radius | v4 rubric: CVSS vulnerable-vs-subsequent, full context, sibling tool/asset lists | same, retargeted at the register (`BLAST_TASK_V5`) | Unchanged on purpose, so a v4↔v5 difference is attributable to the two rows above. |
| Assembly | bulk twins, alias twins, gated floor, blast roof, `band_label_v5` | identical | The assembly keys on the sensitivity *number*, not on who produced it. |

## The hand-off rule

`static_impact.classify()` reports a confidence: **0.35** when no tier verb
matched at all and it fell through to its default, 0.8 when a verb fired, 0.95
when a verb fired *and* an MCP annotation corroborated it. v5 hands a tool to the
model exactly when that confidence drops below
`pipeline.STATIC_IMPACT_MIN_CONFIDENCE` (0.5) — the one case where the rules do
not know, rather than disagree. Every decision is logged in the artifact:
`tool_impact_source` names the scorer per tool, and `static_impacts` keeps the
ladder's evidence, its confidence, and (on a hand-off) what it would have said.

## Results

Three servers, 56 assets, 55 tools. Full tables in
[`five_level_v2_policy_v5/EVALUATION.md`](five_level_v2_policy_v5/EVALUATION.md).

**1 · The scanner recovers the organization's severities from policy text alone.**

| server | assets | MAE | exact | within 1 |
|---|--:|--:|--:|--:|
| calendar_real | 16 | 0.125 | 88 % | **100 %** |
| github_real | 20 | 0.10 | 90 % | **100 %** |
| slack_real | 20 | 0.10 | 90 % | **100 %** |

50 of 56 assets match the organization exactly and **no asset is off by more than
one tier**, against a document that never states a number. The six misses are all
adjacent-tier judgement calls, and each is defensible:

| miss | derived | org | why |
|---|--:|--:|---|
| `account-directory` (calendar) | 5 | 4 | the list of linked accounts sits beside the account *configuration*, which the policy classes Restricted |
| `calendar-records` (calendar) | 2 | 3 | read as a bare attribute listing → Routine |
| `infra-config` (github) | 4 | 5 | scored as serious-lasting-harm rather than control-plane |
| `repository-catalog` (github) | 3 | 2 | the policy says a full catalog enumeration maps the estate, so it did not treat it as Routine |
| `incident-response` (slack) | 5 | 4 | the `self-sufficient` flag plus "credentials pasted mid-incident" reads as crown-jewel |
| `research-team` (slack) | 4 | 3 | pre-publication research read as competitively damaging |

**2 · Tool impact needed no model at all.** The deterministic ladder answered
**55 of 55** tools; the LLM fallback never fired, because all three real vendor
catalogs declare no MCP annotations, so every tool's confidence was set by
description verbs alone (0.8) and none fell to the 0.35 abstention branch.
Against v4's LLM answers the rules agree on **51 / 55 (93 %)**, and every
disagreement is one tier:

| tool | rules | v4 LLM | reading |
|---|--:|--:|---|
| `get_pull_request_files` | 3 | 2 | diffs are content, not metadata |
| `search_users` | 3 | 2 | search results carry profile substance |
| `conversations_leave` | 4 | 5 | leaving is a recoverable membership change, not irreversible |
| `usergroups_me` | 5 | 4 | its description mentions `remove` |

**3 · Blast remains the noisy stage.** 19–22 % of cells moved between the arms
(40/208, 100/520, 72/320) with the same rubric and the same asset ids — at or
somewhat above the 23–35 cells per server v4 measured as this stage's own
run-to-run variance. Roughly half of the movement is the relevance gate flipping
(`became N/A` / `left N/A`), which is where the register's `Tools` column now
disagrees with the model's own judgement about what a tool touches.

**4 · Totals move in both directions**, so policy-grade context is not a uniform
discount: Σ score calendar 2280 → 2697, slack 3779 → 4096, github 6340 → 5328.

## Contents

| Path | What |
|---|---|
| [`five_level_v2_policy_v5/`](five_level_v2_policy_v5/) | the run: per-server JSON / MD / CSV, the inputs it consumed, the prompts as run, and the evaluation |

## Reproducing

```bash
uv run python scripts/check_policies.py                  # validate the policy doc
sbatch scripts/scan_v5.sbatch                            # scan all three servers
uv run python scripts/export_v5_inputs.py                # snapshot the inputs
uv run python scripts/dump_scoring_prompts.py --impact-mode five_level_v2_v5 \
    --org-desc --out reports/experiments/v5/five_level_v2_policy_v5/scoring-prompts-AS-RUN.md
uv run python scripts/evaluate_policy_v5.py              # score it
```

## Related

- Policy spec: [`docs/standards/mcp-policy-spec.md`](../../../docs/standards/mcp-policy-spec.md)
- The inventory-grade arm this is measured against: [`../v4/`](../v4/)
- The earlier policy-sensitivity probe (calendar only, v3-era prompts):
  [`../staticscanner/`](../staticscanner/)
