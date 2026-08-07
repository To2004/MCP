# v7 — does the framework an organization writes its policy in change the score?

Every policy arm before this one asked the scanner to read one register shape.
The v5r `sensiso` / `sensnist` / `senscis` arms varied the *prompt* — the model
was told to reason like ISO, NIST or CIS — but the document it read knew nothing
about those standards. **v7 varies the document.**

Four organizations each publish their policy four times: once in our baseline
register shape, and once in each of three security frameworks' own shapes. The
scanner, the tool catalogs, the deterministic impact ladder, the blast rubric and
the assembly are identical across all four. So a difference between arms is
attributable to how the organization wrote its policy, and to the sensitivity
prompt written to read that shape.

| arm | policy document | output |
|---|---|---|
| `nacombo` (reference) | [`server-policies.md`](../../../docs/mcp-tools/server-policies.md) | [`../v5/five_level_v2_policy_v5r_nacombo/`](../v5/five_level_v2_policy_v5r_nacombo/) |
| `v7_iso` | [`server-policies-iso.md`](../../../docs/mcp-tools/server-policies-iso.md) | `five_level_v2_policy_v7_iso/` |
| `v7_nist` | [`server-policies-nist.md`](../../../docs/mcp-tools/server-policies-nist.md) | `five_level_v2_policy_v7_nist/` |
| `v7_cis` | [`server-policies-cis.md`](../../../docs/mcp-tools/server-policies-cis.md) | `five_level_v2_policy_v7_cis/` |

## The four organizations

| Server | Organization | Domain | Catalog |
|---|---|---|---|
| `fs_corp_filesystem` | unregulated mid-size product company | corporate file share | filesystem, 14 tools |
| `github_helios` | Helios Grid | electricity transmission, NERC CIP | real GitHub, 26 tools |
| `slack_vireo` | Vireo Bio | biopharmaceutical R&D, ICH-GCP blinding | real Slack, 16 tools |
| `calendar_aurora` | Aurora Airways | commercial aviation | real Google Calendar, 13 tools |

## What changes between arms

**The register shape diverges on purpose.** If every framework produced the same
register, the arms would differ only in prose and there would be nothing to
measure. Row counts, against the baseline:

| server | nacombo | iso | nist | cis |
|---|---:|---:|---:|---:|
| `fs_corp_filesystem` | 16 | 16 | 18 | 9 |
| `github_helios` | 19 | 19 | 21 | 12 |
| `slack_vireo` | 15 | 15 | 17 | 10 |
| `calendar_aurora` | 17 | 17 | 19 | 10 |

ISO keeps the rows and adds columns (an A.5.9 owner, an A.8.3 authorization set).
NIST splits a row whose read and write categorize on different FIPS 199 axes —
`audit-records` from `audit-records-integrity`, `aurora-crew-roster` from
`aurora-crew-roster-commitment`. CIS merges non-sensitive data into functional
entries, which Safeguard 3.2 permits since it asks only that *sensitive* data be
enumerated.

**Every register states its tool→asset authorization.** `Tools` remains the
reachability fact and the tool×asset homing the blast stage scores; a second
column names which of those tools the organization actually sanctions, in the
framework's vocabulary (ISO A.8.3, NIST AC-3/AC-6, CIS Safeguard 3.3). The
parser reads it as a strict subset of reach — an authorization cell can narrow
what a register grants, never widen it.

**No register carries flags.** That costs nothing against `nacombo`, which
already runs `asset_flags: "none"` and `floors: "none"` against a v5r assembly
whose blast roof is empty — no flag reached the model or the arithmetic there
either.

**No register carries a sensitivity number.** `assert_no_sensitivity_numbers`
guards these documents as it guards the baseline.

## What this experiment does *not* measure

**Accuracy.** None of these four servers has held-out numeric ground truth.
`github_helios`, `slack_vireo` and `calendar_aurora` have no section in
`server-profiles.md` at all, and `fs_corp_filesystem`'s profile uses path-shaped
asset ids (`sensitive/security/private_key.pem`) that do not align with the
policy register's concept ids (`security-keys`) — only 7 of 16 overlap. The three
servers with aligned ground truth are `calendar_real`, `github_real` and
`slack_real`, which is why `SENS_SCHEME_RESULTS.md` in the v5 folder reports MAE
only for those.

So [`FRAMEWORK_RESULTS.md`](FRAMEWORK_RESULTS.md) reports two things that need no
truth: **movement** relative to `nacombo` on shared asset ids, and **agreement**
between the three frameworks describing the same deployment.

## Reproducing

```bash
# one arm, all four servers (rtx_4090; ~3 GPU-hours per arm)
sbatch scripts/scan_v7.sbatch iso
sbatch scripts/scan_v7.sbatch nist
sbatch scripts/scan_v7.sbatch cis

# offline smoke test — no model, checks register parsing and homing only
uv run python scripts/scan_policy_v5.py --no-llm --impact-mode five_level_v2_v7_iso \
    --only fs_corp_filesystem --out-dir /tmp/smoke

# the comparison
uv run python scripts/compare_v7_frameworks.py
```

## Contents

| file | what it holds |
|---|---|
| `five_level_v2_policy_v7_<arm>/<server>.json` | the full artifact: every primitive, its reasoning, its provenance |
| `five_level_v2_policy_v7_<arm>/<server>.md` | the same scan as a readable report |
| `five_level_v2_policy_v7_<arm>/<server>_matrix.csv` | the tool × asset score matrix |
| [`FRAMEWORK_RESULTS.md`](FRAMEWORK_RESULTS.md) | the cross-arm comparison |
| `framework_results.json` | the same, machine-readable |
| `framework_sensitivity.csv` | per-asset sensitivity, one column per arm |
