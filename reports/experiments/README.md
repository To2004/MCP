# Static-scoring experiments

Every scan experiment, grouped into three generations. Each generation has its
own README with the folder-by-folder index and its headline findings.

| Generation | Question it answered | Inputs the scanner got | Sensitivity from |
|---|---|---|---|
| [v1](v1/) | Which scoring rubric? (impact ladders, blast definitions, post-hoc repairs) | tool catalog + demo store + generated assets | LLM stage |
| [v2](v2/) | Does the organization's written profile beat inference? | + org profile; then **profile only** (`pure`) | org profile table |
| [v3](v3/) | Which deterministic rules and how much description context? | tool catalog + org profile only | org profile table |
| [v4](v4/) | Can the prompts be standards-grounded, and is tool impact rule-derivable? | tool catalog + org profile only | org profile table |
| [v5](v5/) | Can the scanner **derive** the org's severities from a policy that states no numbers? | tool catalog + org **policy** only | LLM classify → map |
| [v6](v6/) | Can CIA change the *shape* of the matrix instead of its scale? | v5 artifacts, re-priced offline | per-facet split of the v5 number |

## The line through them

- **v1** searched for the rubric: five_level ladders, CIA, hybrid, the coverage
  blast + N/A gate, then three fixes for the "pinpoint mutation scores low"
  bug (ctx / floor / rowfix). Winner: the **gated floor**.
- **v2** replaced inferred severity with the org's own profile: `desc` (prose
  replaces the sensitivity primitive — rejected), then **`ult`** (the profile's
  per-asset table IS the sensitivity primitive) plus its prompt ablations, and
  finally **`pure`** — the tool catalog + profile as the ONLY inputs, which
  matched the full-input scan and became the production shape.
- **v3** added the deterministic rules on top (bulk-twin dominance, impact-keyed
  floors, blast roofs) and asked how much description the model actually needs
  (noflags / terse / rich).
- **v4** rewrote both prompts against published standards (CVSS v4.0's
  vulnerable-vs-subsequent split for blast, the MCP annotation vocabulary for
  impact), gave blast the sibling tool/asset lists, and tested whether tool
  impact is derivable by **rules alone** (`static_impact.py`). It is: 0–3
  disagreements per server against the model.
- **v5** removed the last thing the organization had to hand over — the number.
  The scanner reads a policy (classification table + asset register + recognition
  rules, no 1–5 anywhere) and **derives** sensitivity by classifying then
  mapping; tool impact is the deterministic ladder with the model as fallback
  where the rules abstain; blast keeps v4's full-context rubric.

- **v6** attacks the one thing `sens × blast × impact` cannot express: an
  interaction between the asset and the action. CIA supplies it — the asset's
  loss axis splits its sensitivity into a per-facet triple, the tool's atomic op
  selects which facet applies. Anchored at the leading axis, so it can only
  discount, never inflate (the v1 CIA arm's failure). Nothing is wired into the
  scan path yet.

Current best configuration: **v5** — see
[v5/five_level_v2_policy_v5/](v5/five_level_v2_policy_v5/) (`EVALUATION.md` for
accuracy against the organization's own numbers). It reproduces each
organization's severities on 50 of 56 assets with nothing off by more than one
tier, and needs no model at all for tool impact.

`_prompts_backup/` holds superseded prompt dumps; `risk_matrix_final_scores.md`
predates the generations.
