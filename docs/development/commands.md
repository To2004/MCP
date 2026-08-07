# Command Reference

All commands use `uv run` to execute within the project's virtual environment.

## Core Commands

| Command | Description |
|---------|-------------|
| `uv sync` | Install/update all dependencies |
| `uv run python -m mcp_security.main` | Run the project |
| `uv run python -m mcp_security.scanner` | Scan connected MCP servers' assets ([guide](../guides/scanning-connected-assets.md)) |
| `uv run python -m mcp_security.scanner --gen-assets ...` | Scan + generate an asset for tools the registry leaves uncovered |
| `uv run python -m mcp_security.scanner.asset_gen --eval` | Check the tool→asset generator vs the curated held-out list |
| `uv run python -m mcp_security.atomic_ops.build_heatmap` | Build the atomic-op classification heatmap |
| `uv run pytest` | Run all tests |
| `uv run ruff check .` | Lint the codebase |
| `uv run ruff format .` | Auto-format the codebase |

## Blast-Radius Experiments

Three separate experiments over the calendar/slack/fs scans, each countering the
"pinpoint mutation on a sensitive asset scores low" failure of coverage blast
(e.g. calendar delete-event at blast 1). All compare against the
`reports/experiments/five_level_v2_fs` baseline.

| Command | Description |
|---------|-------------|
| `sbatch scripts/scan_flv2ctx.sbatch` | Exp `ctx`: full re-scan under `five_level_v2_ctx` — a per-tool understanding stage (role, single-call reach, consequence carriers) is injected into every blast decision (GPU) |
| `uv run python scripts/apply_blast_floor.py` | Exp `floor`: deterministic sensitivity-coupled minimum blast (sens 5 → ≥4, sens 4 → ≥3), `plain` + impact-gated variants; no LLM |
| `sbatch scripts/rowfix_flv2.sbatch` | Exp `rowfix`: per-asset row-consistency audit — the LLM sees the whole row and repairs ordering violations (GPU) |
| `uv run python scripts/compare_blast_experiments.py` | Side-by-side band distributions + offender-cell tracking across all three experiments |

## Experiment `ultimate` (`five_level_v2_ult`)

The combined winner mode: org profile in front of every LLM stage (desc), asset
sensitivity taken ONLY from the profile's per-asset `| Asset | Sens. | ... |`
table (logged + deterministic; scan aborts listing missing rows if the table
does not cover every registry asset), formula sens×blast×impact (max 125),
in-assembly gated blast floor (impact ≥ 4 & sens 5→blast ≥ 4 / sens 4→≥ 3, raw
model blast preserved as `blast_radius_raw`), a DEPRECATED-alias twin pass, and
the sensitivity-aware `band_label_v5` irreversibility floors.

| Command | Description |
|---------|-------------|
| `uv run python scripts/scan_ultimate.py --check-profiles` | Pre-flight: profile tables parse and cover all known asset ids |
| `sbatch scripts/scan_ultimate.sbatch` | GPU scan of calendar:real, slack:real, github:real, fs:corp_filesystem → `reports/experiments/five_level_v2_ult/` |
| `uv run python scripts/scan_ultimate.py --no-llm --only fs_corp_filesystem` | Offline plumbing smoke test |
| `uv run python scripts/ultimate_gate_grid.py` | Offline gate grid (gate impact ≥3/≥4 × sens4 floor 2/3) from `blast_radius_raw` + comparison vs the fs/desc baselines |

If a scan fails with `ProfileCoverageError`, the LLM generated a homing asset
with a new name: add the listed ids as rows to the server's table in
`docs/mcp-tools/server-profiles.md` and re-run (completed stems are skipped).

### Experiment `pure` (tools + description only)

The realistic gateway scenario: the scanner's ONLY inputs are the captured tool
catalog and the org profile — the asset registry itself is built from the
profile table (Contents+Why → asset description, spec flags → tags, Sens. →
sensitivity), no store walk, no generated assets. Calendar-only. Same
`five_level_v2_ult` scoring machinery.

| Command | Description |
|---------|-------------|
| `sbatch scripts/scan_pure.sbatch` | GPU scan → `reports/experiments/five_level_v2_pure/` |
| `uv run python scripts/scan_pure_desc.py --no-llm` | Offline plumbing smoke test |
| `uv run python scripts/reassemble_static_arm.py` | Dry-run: what a static-rule change would do to the v4 static arm |
| `uv run python scripts/reassemble_static_arm.py --write` | Overwrite that arm's artifacts — no GPU, no model call |

**Re-assembly, not re-scanning.** In the static arm (`five_level_v2_v4_static`)
tool impact is deterministic, so a rule change makes the stored artifacts stale
while the model stages are unaffected. `reassemble_static_arm.py` replays the
recorded blast (`blast_radius_raw`), inferred profile and baselines, recomputes
impact from the current rules, and re-runs every deterministic pass. Servers whose
impacts did not change must reproduce their stored band distribution exactly —
that is the check that the replay is faithful.

## Description-driven scan (no asset sensitivity)

Experiment `desc` (`impact_mode=five_level_v2_desc`) changes two things at once
versus the `five_level_v2_na` baseline:

1. Every scoring stage — domain inference, tool impact, blast radius, baselines —
   is shown the organization's written profile of the server from
   [`docs/mcp-tools/server-profiles.md`](../mcp-tools/server-profiles.md) (owning
   company, expected agent use, per-asset severity, CIA emphasis).
2. The asset-sensitivity primitive is **removed**. No 1–5 sensitivity is derived;
   the cell is `blast × impact` (score_max 25) and bands come from
   `band_label_no_sens`. How much an asset is worth comes from the description.

The profiles are written at five deliberate length tiers (XS–XL), so the same run
also measures how much organizational context the scorer actually needs.

| Command | Description |
|---------|-------------|
| `sbatch --job-name=mcp-desc-fs scripts/scan_desc.sbatch <stems>` | Scan the named servers under `five_level_v2_desc` (GPU); omit `<stems>` for all 13 |
| `uv run python scripts/scan_desc_no_sens.py --only fs_corp_filesystem` | Same scan directly (needs a reachable Ollama) |
| `uv run python scripts/scan_desc_no_sens.py --no-llm --only fs_corp_filesystem` | Offline plumbing smoke test |
| `uv run python -m mcp_security.static_scoring.server_profiles` | List the parsed profiles with their tier and word count |
| `uv run python -m mcp_security.static_scoring.server_profiles --server fs:fintech_fs` | Print one server's profile text as the model sees it |

Output goes to `reports/experiments/five_level_v2_desc/`. The driver **skips any
target already scanned there** — pass `--overwrite` to redo one — so a resumed run
never destroys completed work and no earlier experiment is touched.

## Policy-driven scan (realistic disclosure, no asset sensitivity)

Experiment `policy` keeps the `five_level_v2_desc` scoring but swaps the
description document: instead of the per-asset severity inventory, every stage is
shown [`docs/mcp-tools/server-policies.md`](../mcp-tools/server-policies.md) — the
data-classification policy and agent acceptable-use rules an organization can
actually hand to an integrator (real orgs decline to release a labeled asset
inventory). Targets are the 11 servers with a policy section: the 5 filesystem
tenants (identical tool surface, so cross-org score movement is attributable to
the policy text alone) plus the github/slack/calendar real and cbg catalogs.
Artifacts carry `description_source: docs/mcp-tools/server-policies.md`.

| Command | Description |
|---------|-------------|
| `sbatch scripts/scan_policy.sbatch <stems>` | Scan the named servers under the org policy (GPU); omit `<stems>` for all 11 |
| `uv run python scripts/scan_policy_no_sens.py --no-llm --only fs_corp_filesystem` | Offline plumbing smoke test |
| `sbatch scripts/scan_policy_sens.sbatch <stems>` | DERIVE asset sensitivity from the policy (`five_level_v2_na` + policy doc; GPU) → `reports/experiments/staticscanner/` |
| `uv run python scripts/report_policy_sensitivity.py` | Render the derived sensitivities as `staticscanner/asset-sensitivity.md` |
| `uv run python scripts/compare_policy_sensitivity.py --stem calendar_real` | Per-asset comparison: org ground truth vs no-context LLM vs policy-derived |

Output goes to `reports/experiments/staticscanner/no_sens/` — a new directory;
the `five_level_v2_desc` results are never touched, and the driver skips
already-scanned targets unless `--overwrite` is passed.

## v5 scan (the final static arm)

Experiment `five_level_v2_v5` is the policy arm taken to its conclusion. Inputs
per server are exactly two documents — the captured tool catalog and the org's
policy section — and the policy states **no sensitivity number anywhere**:

- **asset registry** comes from the policy's asset register rows (deterministic,
  org-controlled), with the `Tools` cell giving the exact tool×asset homing and
  the `Flags` cell the escape routes a tier-5 blast must cite;
- **asset sensitivity** is derived — the model classifies each row against the
  classification table and recognition rules, then maps that class's
  adverse-impact language onto 1–5 (`ASSET_TASK_POLICY`);
- **tool impact** is the deterministic ladder (`static_impact.py`), with the v4
  impact prompt used only for a tool where the ladder abstains — no tier verb
  matched, so its confidence fell below `STATIC_IMPACT_MIN_CONFIDENCE`;
- **blast radius** is the v4 rubric with the full context and the sibling
  tool/asset lists (`BLAST_TASK_V5`);
- **assembly** is v4's, unchanged: bulk twins, alias twins, gated floor, blast
  roof, `band_label_v5`, `score = sens × blast × impact` (max 125).

`server-profiles.md` is never shown to this scan; its numbers are the held-out
ground truth the evaluation scores against.

| Command | Description |
|---------|-------------|
| `uv run python scripts/check_policies.py` | Validate every policy section against the spec (no numbers, register parses, tool coverage) |
| `sbatch scripts/scan_v5.sbatch [<stem>] [overwrite]` | Scan (GPU); omit `<stem>` for all three servers |
| `uv run python scripts/scan_policy_v5.py --no-llm --only calendar_real` | Offline plumbing smoke test |
| `uv run python scripts/export_v5_inputs.py` | Snapshot the policy sections, catalogs and parsed registers into the experiment folder |
| `uv run python scripts/evaluate_policy_v5.py` | Accuracy vs the org's own numbers, and the v4↔v5 diff → `EVALUATION.md` + CSVs |

Output goes to `reports/experiments/v5/five_level_v2_policy_v5/`; the driver
skips already-scanned stems unless `--overwrite` is passed.

### v7 — the framework-native policy arms

Same scanner, same catalogs, same four organizations as the v5r `nacombo` arm.
What changes is the document each organization publishes: a register written in
ISO/IEC 27001:2022's, NIST FIPS 199 / SP 800-60's, or CIS Controls v8.1 Control
3's own shape, each carrying an authorization column (which of the tools that
*reach* an asset the organization *sanctions*) and no flag column. Sensitivity is
still derived — no register states a number.

The register shapes diverge deliberately: ISO keeps the baseline's rows, NIST
splits a row whose read and write categorize on different FIPS 199 axes, CIS
merges non-sensitive data into coarse Safeguard 3.2 entries. So cell counts
differ per arm and the comparison is restricted to shared asset ids.

| Command | Description |
|---------|-------------|
| `sbatch scripts/scan_v7.sbatch <iso\|nist\|cis>` | Scan one arm over all four servers (GPU) |
| `sbatch scripts/scan_v7.sbatch nist github_helios overwrite` | One arm, one server, re-scan |
| `uv run python scripts/scan_policy_v5.py --no-llm --impact-mode five_level_v2_v7_iso --only fs_corp_filesystem --out-dir /tmp/smoke` | Offline plumbing smoke test |
| `uv run python scripts/compare_v7_frameworks.py` | Movement vs `nacombo` and cross-framework agreement → `FRAMEWORK_RESULTS.md` + CSV |

Output goes to `reports/experiments/v7/five_level_v2_policy_v7_<arm>/`. There is
no accuracy number for these four servers — none has held-out ground truth
aligned to the policy register's asset ids — so the comparison reports movement
and agreement instead. See
[`reports/experiments/v7/README.md`](../../reports/experiments/v7/README.md).

## Testing

```bash
# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_smoke.py

# Run tests matching a name pattern
uv run pytest -k "test_import"

# Run with verbose output
uv run pytest -v

# Run with print output visible
uv run pytest -s
```

## Linting and Formatting

```bash
# Check for lint errors (read-only)
uv run ruff check .

# Auto-fix lint errors where possible
uv run ruff check . --fix

# Format code
uv run ruff format .

# Check formatting without changing files
uv run ruff format . --check
```

## Dependency Management

```bash
# Add a runtime dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>

# Remove a dependency
uv remove <package>

# Update all dependencies
uv sync --upgrade
```
