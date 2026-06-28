# Scorer head-to-head vs. the human oracle

Each scorer's per-(asset, tool) risk bands are graded against the hand-authored human heatmap on the shared cell surface (filetype × tool for filesystem, table × tool for SQLite). Metrics: exact band agreement (Wilson 95% CI), within-one-band, quadratic-weighted Cohen's κ (chance- and magnitude-corrected), mean absolute band error (MAE), Spearman ρ, and **over-block** = share of cells the scorer rates high or critical. Higher κ / lower MAE = closer to the human; a high over-block with low κ is a scorer that defends by rating almost everything dangerous. No LLM is called here — every band is read from a precomputed artifact.

### Overall (filesystem + SQLite pooled)

| scorer | cells | exact | within-1 | QW-κ | MAE | Spearman | over-block |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **scanner (Qwen)** | 64 | 34% [24–47] | 97% | +0.66 | +0.69 | +0.68 | 56% |
| owasp_aivss | 131 | 50% [41–58] | 95% | +0.69 | +0.56 | +0.74 | 56% |
| cvss_v3 | 129 | 40% [32–48] | 94% | +0.36 | +0.67 | +0.47 | 22% |
| nist_sp_800_60 | 131 | 29% [22–37] | 76% | +0.35 | +1.01 | +0.44 | 68% |
| chatgpt:plain | 131 | 14% [9–21] | 69% | +0.23 | +1.21 | +0.66 | 98% |
| chatgpt:security | 131 | 14% [9–21] | 64% | +0.18 | +1.27 | +0.59 | 99% |
| owasp_risk_rating | 131 | 14% [9–21] | 66% | +0.17 | +1.27 | +0.55 | 98% |
| nist_sp_800_30 | 131 | 16% [11–23] | 64% | +0.17 | +1.25 | +0.51 | 98% |
| maestro_atfaa | 131 | 21% [15–29] | 70% | +0.16 | +1.16 | +0.31 | 95% |
| dread | 131 | 14% [9–21] | 56% | +0.10 | +1.37 | +0.47 | 100% |

### Filesystem (filetype × tool)

| scorer | cells | exact | within-1 | QW-κ | MAE | Spearman | over-block |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **scanner (Qwen)** | 36 | 36% [22–52] | 100% | +0.66 | +0.64 | +0.75 | 64% |
| owasp_aivss | 96 | 46% [36–56] | 95% | +0.61 | +0.59 | +0.71 | 64% |
| cvss_v3 | 96 | 44% [34–54] | 98% | +0.39 | +0.58 | +0.49 | 25% |
| nist_sp_800_60 | 96 | 20% [13–29] | 73% | +0.22 | +1.10 | +0.31 | 79% |
| chatgpt:plain | 96 | 9% [5–17] | 72% | +0.17 | +1.19 | +0.61 | 100% |
| owasp_risk_rating | 96 | 9% [5–17] | 72% | +0.17 | +1.19 | +0.61 | 100% |
| chatgpt:security | 96 | 9% [5–17] | 69% | +0.15 | +1.22 | +0.57 | 100% |
| maestro_atfaa | 96 | 19% [12–28] | 72% | +0.09 | +1.12 | +0.29 | 100% |
| nist_sp_800_30 | 96 | 10% [6–18] | 65% | +0.05 | +1.29 | +0.30 | 100% |
| dread | 96 | 9% [5–17] | 59% | +0.01 | +1.36 | +0.18 | 100% |

### SQLite (table × tool)

| scorer | cells | exact | within-1 | QW-κ | MAE | Spearman | over-block |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **scanner (Qwen)** | 28 | 32% [18–51] | 93% | +0.63 | +0.75 | +0.70 | 46% |
| owasp_aivss | 35 | 60% [44–74] | 94% | +0.79 | +0.46 | +0.78 | 37% |
| nist_sp_800_60 | 35 | 54% [38–70] | 86% | +0.49 | +0.74 | +0.46 | 37% |
| nist_sp_800_30 | 35 | 31% [19–48] | 63% | +0.30 | +1.14 | +0.64 | 94% |
| cvss_v3 | 33 | 27% [15–44] | 82% | +0.28 | +0.91 | +0.43 | 15% |
| chatgpt:plain | 35 | 26% [14–42] | 60% | +0.28 | +1.26 | +0.65 | 94% |
| dread | 35 | 26% [14–42] | 49% | +0.20 | +1.40 | +0.61 | 100% |
| chatgpt:security | 35 | 26% [14–42] | 51% | +0.20 | +1.40 | +0.56 | 97% |
| maestro_atfaa | 35 | 29% [16–45] | 66% | +0.19 | +1.26 | +0.27 | 83% |
| owasp_risk_rating | 35 | 26% [14–42] | 49% | +0.17 | +1.49 | +0.52 | 91% |
