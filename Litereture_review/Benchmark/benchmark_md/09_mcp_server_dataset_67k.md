# MCP Server Dataset (67K)

## Source
- **Paper:** Toward Understanding Security Issues in the Model Context Protocol Ecosystem — Li & Gao
- **Link:** https://arxiv.org/abs/2510.16558
- **Year:** 2025

## Format & Size
- **Total samples:** 67,057 servers across 6 registries; 44,499 Python-based tools extracted via AST analysis
- **Format:** Server metadata with tool-level code analysis, vulnerability annotations, and registry-level statistics
- **Availability:** Data sourced from 6 public registries: mcp.so, MCP Market, MCP Store, Pulse MCP, Smithery, npm

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Server registry source | Categorical | mcp.so, MCP Market, MCP Store, Pulse MCP, Smithery, npm | Yes | 15K+ / 10K+ / 5K+ / 7K+ / 7,682 / 52,102 distribution |
| Server language | Categorical | Python (52.1%), JavaScript (22.5%), TypeScript (11.6%), Other | Yes | Language distribution across ecosystem |
| Tool source code | Code (Python) | AST-parsed Python tool implementations | Partially | 44,499 tools — requires code analysis pipeline |
| Tool confusion attack success | Numeric (%) | 20-100% success rate | Yes | Per-tool or per-category success rates |
| Tool shadowing attack success | Numeric (%) | 40-100% success rate | Yes | Higher baseline than confusion attacks |
| Credential leakage instances | Count/Detail | 9 PATs, 3 API keys found | Yes | Small but concrete set of real leaks |
| Server hijacking instances | Count | 111+ instances | Yes | Direct security violations |
| Affix-squatting groups | Count | 408 groups identified | Yes | Naming-based attack surface |
| Invalid link rate | Percentage | 6.75% | Yes | Ecosystem health indicator |

## Proposed Risk Dimensions

### Tool Confusion/Shadowing Vulnerability
- **Feeding columns:** Tool confusion attack success rate, tool shadowing attack success rate
- **Proposed scale:** 1-10 based on observed attack success ranges
- **Derivation:** Tool confusion success ranges 20-100%, tool shadowing 40-100%. For a given tool, estimate its susceptibility based on properties that correlate with these attacks (name ambiguity, description overlap with other tools, common naming patterns). Map the expected success rate to 1-10: tools with unique, unambiguous names and clear descriptions = 2-3. Tools with generic names like "search" or "get_data" that overlap with many others = 7-9. Tools in affix-squatting groups (408 identified) automatically get +2.

### Registry Trust Score
- **Feeding columns:** Server registry source, invalid link rate, credential leakage prevalence, server hijacking count
- **Proposed scale:** 1-10 where 1 = highly trusted registry, 10 = untrusted/risky source
- **Derivation:** Each registry gets a base trust score derived from its observed vulnerability rates. npm has the largest volume (52,102) but also the most attack surface. Smaller curated registries like Awesome MCP Servers may have lower vulnerability rates. Compute per-registry rates for: invalid links, credential leaks, hijacking incidents, squatting groups. Normalize each to 0-1, weight equally, multiply by 10. A registry with zero issues across all metrics = 1. A registry with high rates across the board = 9-10.

### Ecosystem Prevalence Risk
- **Feeding columns:** Language distribution, tool count per server, registry size
- **Proposed scale:** 1-10 reflecting how "exposed" a tool is based on ecosystem factors
- **Derivation:** Python tools (52.1% of ecosystem) are the most analyzed and the most attacked. A Python tool on a large registry like npm or mcp.so is more exposed than a TypeScript tool on a small registry. Score = base language risk (Python=5, JS=4, TS=3, Other=2) + registry size factor (log-scaled, 0-3) + tool density factor (tools per server, 0-2). This captures the idea that being part of a large, heavily-targeted ecosystem is itself a risk factor.

### Credential/Secret Exposure Risk
- **Feeding columns:** Credential leakage instances (9 PATs, 3 API keys), server hijacking instances (111+)
- **Proposed scale:** 1-10 where tools handling credentials score higher
- **Derivation:** Binary initial check: does the tool handle authentication tokens, API keys, or user credentials? If no → score 2 (baseline). If yes → start at 5. Then adjust: tools on servers with known credential leaks → 8-10. Tools on servers with hijacking history → 7-9. Tools that require credential pass-through → +2. The 9 PATs and 3 API keys found in the wild are small numbers but represent catastrophic failures — each one justifies high scores for similar tool patterns.

## Data Quality Notes
- At 67,057 servers, this is by far the largest MCP dataset available — but size introduces noise. Many npm packages may be stale, abandoned, or duplicates.
- The 44,499 Python tools were extracted via AST analysis, meaning only Python tools have deep code-level data. JavaScript and TypeScript tools (34.1% combined) lack equivalent analysis depth.
- Attack success rates (20-100% for confusion, 40-100% for shadowing) are ranges, not per-tool measurements. Individual tool scores would need to be estimated from tool properties.
- The 6.75% invalid link rate suggests non-trivial ecosystem decay — some servers in the dataset may no longer exist or function.
- Credential leakage numbers (9 PATs, 3 API keys) are likely undercounts — these are only the ones found through automated scanning.
- Registry overlap is possible — the same server may appear on multiple registries, inflating the 67K count.

## Usefulness Verdict
This is the **ecosystem-scale calibration dataset** for MCP risk scoring. With 67K servers and 44K analyzed tools, it provides the statistical base rates needed to set scoring thresholds: what fraction of tools are vulnerable to confusion attacks? What does the distribution of shadowing success look like? How common is credential leakage? These numbers answer the question "what should a score of 5 actually mean?" by grounding it in real prevalence data.

The multi-registry structure is particularly useful for building a **registry trust dimension** into the scorer — the same tool hosted on different registries can carry different risk scores based on the registry's track record. The language distribution data enables language-aware risk adjustment (Python tools have more analysis coverage but are also the most targeted). For a 1-10 scoring system, this dataset provides the population-level statistics needed to ensure scores are well-calibrated against the real MCP ecosystem, not just against synthetic benchmarks.
