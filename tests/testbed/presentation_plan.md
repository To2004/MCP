# Plan: FS Research Presentation — Detective Story Arc

## Goal
Rewrite `Literature_review/litreturereview.pptx` (currently 13 slides from previous draft)
into a 7–8 minute thesis-supervisor presentation. Do NOT touch `litreturereview_original_backup.pptx`.

## Story Arc
The presentation tells a *detective story*: each batch of probes teaches something
about the server's behaviour, and that output changes the next tactic — until a real
CVE surfaces naturally from the methodology.

## Slide Plan (14 slides)

| # | Title | Time | Layout |
|---|-------|------|--------|
| 1 | Title | — | Title Slide_Black (idx 2) |
| 2 | What Is an MCP Server? | 30 s | Title Only_Black (idx 9) |
| 3 | How MCP Talks — The JSON Protocol | 60 s | Title Only_Black |
| 4 | The Two Tools: read_file + list_directory | 45 s | Title Only_Black |
| 5 | Methodology: Hypothesis-First Probing | 30 s | Title Only_Black |
| 6 | Phase 1 — Fingerprint: Baseline | 45 s | Title Only_Black |
| 7 | Phases 2–4: Errors, Normalization, Gibberish | 60 s | Title Only_Black |
| 8 | Phase 5 — First Cracks: "Almost Valid" | 45 s | Title Only_Black |
| 9 | Phase 6 — The Discovery: Prefix Bypass | 90 s | Title Only_Black |
| 10 | The CVE: What Prefix Bypass Means | 60 s | Title Only_Black |
| 11 | Phase 7 — Type Confusion | 30 s | Title Only_Black |
| 12 | Phase 8 — Follow-Up: Confirming the Family | 30 s | Title Only_Black |
| 13 | Bonus: Version Comparison Validates the Find | 45 s | Title Only_Black |
| 14 | Thesis Connection + Closing | 30 s | Closing Slide_Black (idx 35) |

## Execution Tasks

### Task 1 — Update `build_fs_presentation.py`
Rewrite the script at `tests/testbed/build_fs_presentation.py` with 14 new slide builder
functions following the detective arc above. Key changes from previous draft:
- Add slide 2: MCP server explanation (1 paragraph, concise)
- Add slide 3: JSON protocol — show a real tool call request and response as code blocks
  rendered as styled text boxes (monospace-look, dark box, white/green text)
- Add slide 4: read_file + list_directory — input params + output shape
- Rework slides 6–12 to tell the reactive story (each phase's output drives next tactic)
- Move version comparison to slide 13 as bonus
- Slide 14: thesis connection + closing

### Task 2 — Run the script
`uv run python tests/testbed/build_fs_presentation.py`
Verify: 14 slides, no crash, file written to `litreturereview.pptx`.

### Task 3 — Verify output
Open the pptx via python-pptx and confirm slide titles match the plan.
