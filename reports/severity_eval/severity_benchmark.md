# Severity-agreement benchmark: risk scorers vs. graded ground truth

Each scorer maps the same extracted action features to a 0–4 severity (none..critical) through its own logic; we grade it against the reference severity by rank correlation (Spearman ρ), magnitude-/chance-corrected agreement (quadratic-weighted Cohen's κ), mean absolute band error (MAE), and within-one / exact agreement. This is a risk-*scoring* comparison, not attack detection. AgentTrust sources are external (third-party); `mcp_native` is an author-created MCP-specific set (secondary).

### HEADLINE — external (pooled) (430 scenarios)

| scorer | Spearman ρ | QW-κ | MAE | within-1 | exact |
| --- | --- | --- | --- | --- | --- |
| keyword | +0.48 | +0.24 | +1.51 | 52% | 27% |
| **ours** | +0.35 | +0.27 | +1.33 | 64% | 18% |
| owasp | +0.34 | +0.26 | +1.28 | 61% | 20% |
| nist | +0.32 | +0.28 | +1.30 | 68% | 18% |
| cvss | +0.23 | +0.07 | +1.82 | 51% | 30% |
| random | +0.11 | +0.11 | +1.62 | 52% | 24% |
| dread | +0.08 | +0.02 | +1.54 | 59% | 21% |
| majority | — | +0.00 | +2.06 | 41% | 30% |

### agenttrust_internal (300 scenarios)

| scorer | Spearman ρ | QW-κ | MAE | within-1 | exact |
| --- | --- | --- | --- | --- | --- |
| keyword | +0.49 | +0.26 | +1.42 | 56% | 29% |
| **ours** | +0.45 | +0.34 | +1.23 | 69% | 20% |
| nist | +0.42 | +0.37 | +1.17 | 73% | 22% |
| owasp | +0.41 | +0.30 | +1.23 | 64% | 21% |
| cvss | +0.27 | +0.06 | +1.90 | 47% | 27% |
| dread | +0.10 | +0.02 | +1.56 | 55% | 21% |
| random | +0.02 | +0.01 | +1.74 | 48% | 22% |
| majority | — | +0.00 | +1.99 | 44% | 30% |

### agenttrust_independent (30 scenarios)

| scorer | Spearman ρ | QW-κ | MAE | within-1 | exact |
| --- | --- | --- | --- | --- | --- |
| random | +0.41 | +0.35 | +1.33 | 63% | 30% |
| keyword | +0.37 | +0.13 | +1.83 | 37% | 10% |
| owasp | +0.03 | +0.04 | +1.33 | 57% | 20% |
| dread | -0.03 | -0.01 | +1.27 | 73% | 27% |
| nist | -0.12 | -0.14 | +1.63 | 50% | 17% |
| cvss | -0.21 | -0.08 | +1.63 | 60% | 33% |
| **ours** | -0.23 | -0.20 | +1.80 | 40% | 10% |
| majority | — | +0.00 | +2.50 | 27% | 23% |

### agenttrust_realworld (100 scenarios)

| scorer | Spearman ρ | QW-κ | MAE | within-1 | exact |
| --- | --- | --- | --- | --- | --- |
| keyword | +0.48 | +0.20 | +1.69 | 43% | 25% |
| random | +0.32 | +0.33 | +1.36 | 60% | 26% |
| **ours** | +0.24 | +0.21 | +1.51 | 59% | 14% |
| owasp | +0.21 | +0.21 | +1.39 | 52% | 19% |
| cvss | +0.20 | +0.14 | +1.63 | 58% | 37% |
| nist | +0.15 | +0.16 | +1.56 | 61% | 8% |
| dread | +0.06 | +0.02 | +1.55 | 64% | 18% |
| majority | — | +0.00 | +2.16 | 35% | 35% |

### mcp_native (66 scenarios)

| scorer | Spearman ρ | QW-κ | MAE | within-1 | exact |
| --- | --- | --- | --- | --- | --- |
| keyword | +0.74 | +0.29 | +1.48 | 50% | 20% |
| **ours** | +0.64 | +0.49 | +0.98 | 76% | 38% |
| owasp | +0.58 | +0.52 | +0.91 | 80% | 36% |
| cvss | +0.55 | +0.36 | +1.44 | 52% | 27% |
| nist | +0.54 | +0.44 | +0.89 | 82% | 36% |
| dread | +0.26 | +0.05 | +1.30 | 61% | 27% |
| random | -0.13 | -0.14 | +1.74 | 45% | 20% |
| majority | — | +0.00 | +2.05 | 39% | 18% |

### all (pooled) (496 scenarios)

| scorer | Spearman ρ | QW-κ | MAE | within-1 | exact |
| --- | --- | --- | --- | --- | --- |
| keyword | +0.50 | +0.25 | +1.51 | 51% | 26% |
| **ours** | +0.38 | +0.30 | +1.29 | 66% | 21% |
| owasp | +0.37 | +0.30 | +1.23 | 63% | 22% |
| nist | +0.34 | +0.30 | +1.24 | 70% | 21% |
| cvss | +0.27 | +0.11 | +1.77 | 51% | 30% |
| dread | +0.10 | +0.02 | +1.51 | 59% | 22% |
| random | +0.09 | +0.08 | +1.64 | 51% | 23% |
| majority | — | +0.00 | +2.06 | 41% | 29% |
