# `pipeline.py` — the stages and the deterministic assembly

**1 633 lines. Everything that turns a `ServerRegistry` into a scored matrix.**

## `StaticScorer` — the four stages

| Stage | Method | Who decides |
|---|---|---|
| 0 · domain inference | `infer_domain()` | model, once per server — three fields in v5r (`mcp_kind`, `content_unit`, `contents_definition`) |
| 1 · tool impact | `score_tools()` → `_score_one_impact()` | **rules first** (`static_impact.classify_by_operation`), the model only where they abstain |
| 2 · asset sensitivity | `score_assets()` | model, classifying each register row against the org's policy classes |
| 3 · blast radius | `score_blast()` | model, once per (tool, asset) pair |

The behavioural-baseline stage exists in the file but v5r sets `no_baselines`: it
is a runtime primitive, nothing in the static cell multiplies it, and a deviation
is only measurable against an observed call.

`strict=True` (what the driver passes) means a model failure raises
`LLMUnavailableError` rather than falling back to a heuristic — a scan never
silently substitutes a hardcoded number for a model judgement.

## The mode table

`_ULT_VARIANT_OPTIONS["five_level_v2_v5r"]` is the switchboard for this arm:

```python
{"v4_prompts": True,          # short standards-grounded prompt family
 "impact_bare": True,         # the impact prompt gets the tool JSON and nothing else
 "blast_peers": True,         # blast sees the sibling tool and asset lists
 "static_impact": True,       # rules answer stage 1
 "static_impact_fallback": True,  # ...unless they abstain
 "v5r_prompts": True,         # the rewritten ladder + short domain stage
 "no_baselines": True}        # stage 4 moved to the dynamic scorer
```

`_POLICY_SENS_MODES` puts v5r on the *derived* sensitivity path: stage 2 runs, and
`sensitivity_source` records `llm_policy_class` rather than `org_profile`.

## The assembly, in order

Applied after the stages, each one recorded in the artifact so every change is
attributable:

1. **bulk twin impact** — `impact(bulk) ≥ impact(singular)`. A consistency rule,
   not a breadth promotion.
2. **alias twins** — a deprecated/canonical name pair takes the max blast per asset.
3. **blast floors** (`apply_gated_floor`) — v5r uses `V5R_FLOORS = {5: 4, 4: 3}`,
   `V5R_IMPACT_FLOORS = {5: 3}`, **ungated** (`V5R_GATE_IMPACT_MIN = 1`). The
   older arms use the gated `ULT_FLOORS`, which is why `create-event` on a
   sensitivity-5 calendar could keep blast 1 there.
4. **bulk twin blast** — `blast(bulk) > blast(singular)` per asset, +1 on tie, cap 5.
5. **blast roof** — `V5R_ROOF = {}`, so **none runs in v5r**. A cap can only
   under-score.

Then `cells = sensitivity × blast × likelihood(1.0) × impact` and
`bands = band_label_v5(...)` — pure score thresholds on 0–125 (low <17,
medium 17–49, high 50–99, critical ≥100), no categorical overrides, so a band is
explainable from its own number.

## What the artifact records

`tool_impact_source` (which scorer decided each tool), `static_impacts` (the rule
evidence, and on a hand-off what the rules would have said plus the model's
reasoning), `blast_radius_raw` vs `blast_radius`, every `*_fixups` list, and a
human-readable `deterministic_rules` manifest of exactly which passes ran.

## Honesty note

`score = sensitivity × blast × impact` on three ordinal 1–5 scales is the
framework's own construction, not a standard — see `../../../../GROUNDING.md`.
The floors are the analyst's stated policy, also unsourced.
