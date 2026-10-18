# v7 — three targeted fixes on top of exp2, each tested alone

Base: exp2 (`v6/breadth_prompt_categories.md`, 87.6% role agree, 24/24 tools scored) —
the best result at the time. Diagnosed its three regressed tools (all previously
perfect under v3: `get-freebusy` 1.00→0.57, `get-event` 1.00→0.75, `list-events`
1.00→0.75) down to specific parameters that flipped, and wrote one targeted rule per
diagnosis. Each variant is exp2 plus exactly ONE added tie-breaker, so the three
results below isolate which diagnosis actually mattered.

## Result

```
              exp2     context   fields   window   combined
kind agree    95.4%    96.9%     95.7%    95.8%    96.6%
role agree    87.6%    90.0%     89.3%    91.7%    91.8%
median        88.2%    90.9%     88.2%    95.9%    92.3%
identical     11/24    11/24     10/24    12/24    11/24
```

**All four beat exp2. `window` alone is the version to adopt — not `combined`.**

`combined`'s mean (91.8%) is a statistical tie with `window`'s (91.7%), but its median
(92.3%) and identical-tool count (11) are both worse, and it introduces a regression
none of the single-rule variants had: `merge_pull_request` was 1.00 (perfect) in exp2
AND in every one of context/fields/window, and drops to 0.83 only when all three rules
are combined. Adding more tie-breaker rules to one prompt is not free — this is direct
evidence of rule-crowding costing back part of what combining was supposed to gain.
`window` alone reaches the same overall mean without that new regression, so it is
strictly the better choice.

## Per-target check — did each rule fix what it was built for?

```
tool               exp2   context  fields  window
get-freebusy       0.57    1.00    0.71    1.00
get-event          0.75    0.75    1.00    1.00
list-events        0.75    0.88    0.88    0.75
```

- `context` (a tool can have more than one level-5 parameter) fully fixed
  `get-freebusy` — its target — and partly helped `list-events`, but did not move
  `get-event`.
- `fields` (a plain field-selection parameter defaults to level 2) fully fixed
  `get-event` — its target — and partly helped `list-events`, but only partly helped
  `get-freebusy` (0.57→0.71, still an improvement, just the smallest one).
- `window` (a time window narrows, it does not alter reach) fully fixed BOTH
  `get-freebusy` and `get-event`, but not `list-events`.

Each fix mostly hit its own diagnosis, with partial spillover onto the other two
tools — expected, since these three tools share overlapping ambiguous parameters
(`account`, `fields`, `timeMax`/`timeMin` all coexist across them to different degrees).
No fix was a clean single-tool patch; each moved the needle on 2 of the 3 regressed
tools.

## `combined` — do the gains stack? No, not cleanly.

All three rules in one prompt (`breadth_prompt_combined.md`). It did fix both of
`window`'s remaining gaps at once (`get-event` and `get-freebusy` both reached 1.00,
where `window` alone only got both to 1.00 too, actually — the real difference is
`list-events`, which `combined` gets to 0.88 same as context/fields, vs `window` alone's
0.75). But it paid for that with a brand-new regression, `merge_pull_request`
(1.00 -> 0.83), present in no other variant tested — see the table above. Net: a wash on
mean, worse on median, worse on identical-tool count.

## Files

- `breadth_prompt_context.md` / `_fields.md` / `_window.md` / `_combined.md` — the four
  prompt variants, each documenting its own diagnosis.
- Test harness: `scripts/check_breadth_v7_stability.py <variant>` (chosen from
  `context|fields|window|combined`).
- Raw results: `reports/experiments/breadth_spec/breadth_v7_<variant>_stability.json`.
