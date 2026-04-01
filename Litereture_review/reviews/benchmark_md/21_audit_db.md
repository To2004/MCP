# Audit Database (audit-db)

## Source
- **Project:** ModelContextProtocol-Security/audit-db
- **Link:** https://github.com/ModelContextProtocol-Security/audit-db
- **Year:** 2025-2026 era community project (public GitHub repository verified 2026-03-30)

## Format & Size
- **Total samples:** Sample count not verified from the repository landing page
- **Format:** Community-maintained database of MCP server audit results and security assessments with structured manifests, findings, artifacts, and generated indexes
- **Availability:** Public GitHub repository with documented schema, templates, examples, and validation tooling

## Data Structure

The repository README exposes a fairly detailed intended schema.

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Repository metadata | JSON | `metadata.json` per audited repo | Yes | Repo-level context for each target |
| Audit manifest | JSON | `audit-manifest.json` | Yes | Standardized audit metadata |
| Security assessment | Markdown | `security-assessment.md` | Yes | Main narrative report |
| Finding documents | Markdown | `high-001-credential-exposure.md` | Yes | Structured per-finding evidence |
| Supporting artifacts | Mixed files | Code samples, diagrams, dependency trees | Partially | Rich evidence but may need normalization |
| Indexes | JSON | `by-auditor.json`, `by-date.json`, `by-severity.json`, `by-repo.json` | Yes | Makes it queryable as a dataset |
| Validation tooling | Scripts / schema | `validate-audit.py`, JSON schemas | Yes | Useful for quality control |

## Proposed Risk Dimensions

### Audit Finding Density
- **Feeding columns:** Count of findings by severity per repository
- **Proposed scale:** 1-10 based on severity-weighted finding totals
- **Derivation:** Repositories with repeated high-severity audit findings should receive stronger baseline distrust.

### Reproducibility Confidence
- **Feeding columns:** Presence of methodology, artifacts, exact versions, and reproduction steps
- **Proposed scale:** 1-10 where higher means higher confidence in the evidence
- **Derivation:** audit-db emphasizes transparency and reproducibility. That makes it useful not only for finding risk, but also for scoring confidence in the underlying assessment.

### Server Trust Baseline
- **Feeding columns:** Latest audit status, repo-level history, indexed severity profile
- **Proposed scale:** 1-10 where higher means less trustworthy server posture
- **Derivation:** If the community begins contributing enough audits, this can become a prior for your Agent Trust Modifier or server reputation layer.

## Data Quality Notes
- This is an **emerging community schema repository**, not yet a mature benchmark with verified breadth.
- The repository structure is strong, but the public landing page does not confirm a large number of completed audits.
- Its value today is mainly in the **data model and governance design**, not in large-scale statistical coverage.
- For a thesis project, it is best used as an external signal source or future-facing extension rather than as the primary evaluation benchmark.

## Usefulness Verdict
audit-db is valuable because it shows how MCP security assessments can be stored in a reproducible, machine-readable, community-reviewable format. That aligns well with a risk-scoring system that needs explainability and evidence trails.

Right now, it is more of a **structured audit corpus framework** than a fully populated benchmark. Even so, it is a good internet-sourced addition because it points toward a realistic way to attach community audit evidence to your risk scores instead of relying only on lab datasets.
