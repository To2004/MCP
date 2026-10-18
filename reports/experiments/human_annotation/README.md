# Human Annotation Experiment — Artifacts

Supporting files for
[`docs/project/human-annotation-experiment.md`](../../../docs/project/human-annotation-experiment.md),
the protocol for the human inter-rater-reliability study that gives the static
scanner an external baseline (see
[the evaluation problem, §3.1](../../../docs/project/evaluation-problem.md#31-the-static-layer-has-no-ground-truth-at-all)).

## Files

- **`design_transcript.json`** — the full record of how the rater-facing
  instructions, cheat sheets, worked examples, and item cards were built: one
  draft per dimension (Tool Impact / Asset Sensitivity / Blast Radius), four
  independent reviewer-persona critiques per draft (HCI/survey-design
  methodologist, A*-venue peer reviewer, security/compliance domain expert,
  first-time-rater simulation), and the final revision with every accepted and
  rejected suggestion logged under `revised.changelog` and
  `revised.unresolved_disagreements`. Kept for auditability — an A*-venue
  reviewer can see not just the final copy but what alternatives were
  considered.
- **`rater_data.json`** — the frozen item bank that generates the live rating
  tool: per dimension, the finalized instructions, tier cheat sheet, calibration
  examples, and the 8 real + 3 attention-check items (`attn: true`, `expected:
  "<tier>"`) with their assigned server tags. This is the single source of
  truth for what a rater sees; the tool's `RATER_DATA` constant is this file
  verbatim.

## What's not here yet

- `responses/` — raw per-rater CSVs, created once the study actually runs.
  Append-only once it exists; never edit a submitted row in place.
- `RESULTS.md` — the computed Krippendorff's alpha (with bootstrap CIs) and the
  LLM-in-distribution permutation test, written after `responses/` exists.
- `analysis/` — the alpha/bootstrap/AC2/permutation-test code. Per the
  protocol's pre-registration checklist, this should be written and tested
  against synthetic responses *before* real data arrives.

## The live instrument

The tool itself — [MCP Risk Docket](https://claude.ai/code/artifact/d12122a7-363a-4861-a070-b8c9a105c8cb) —
is a published Artifact, not a file in this repo; `rater_data.json` above is its
data source, kept here so the item bank is version-controlled independently of
the page.
