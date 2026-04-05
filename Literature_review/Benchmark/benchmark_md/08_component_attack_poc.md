# Component-based Attack PoC Dataset

## Source
- **Paper:** When MCP Servers Attack: Taxonomy, Feasibility, and Mitigation — Zhao et al.
- **Link:** https://arxiv.org/abs/2509.24272 (paper under review)
- **Year:** 2025

## Format & Size
- **Total samples:** 12 hand-crafted PoC servers (one per attack category A1-A12) + 120 generated servers (10 per category) = 132 servers total. Generator can produce up to 1,046,529 unique configurations.
- **Format:** MCP server configurations with modular malicious/benign components (launch commands, initialization snippets, tools, resources, prompts)
- **Availability:** Not yet publicly released (paper under review); generator architecture described in paper

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Attack category | Categorical | A1 through A12 | Yes | 12 distinct attack categories, one per PoC |
| Server type | Categorical | Hand-crafted, Generated | Yes | 12 hand-crafted + 120 generated |
| Launch commands | Config snippet | 5 malicious variants | Partially | Generator seed — needs execution context |
| Initialization snippets | Config snippet | 7 malicious variants | Partially | Injected at server startup |
| Tools | Config/Code | 10 malicious + 30 benign | Yes | Tool definitions with descriptions |
| Resources | Config/Code | 10 malicious + 10 benign | Yes | Resource definitions |
| Prompts | Config/Code | 5 malicious + 5 benign | Yes | Prompt templates |
| Host LLM | Categorical | 5 LLMs tested | Yes | Evaluation across 3 hosts × 5 LLMs |
| Trial results | Boolean/Numeric | Success/Failure per trial | Yes | 15 trials per configuration |
| Scanner detection | Boolean | Detected/Missed | Yes | mcp-scan: 4/120, AI-Infra-Guard: better but insufficient |

## Proposed Risk Dimensions

### Attack Category Severity (A1-A12 Taxonomy)
- **Feeding columns:** Attack category (A1-A12)
- **Proposed scale:** 1-10 assigned per category based on impact potential and detection difficulty
- **Derivation:** Each of the 12 attack categories represents a distinct attack surface. Rank them by two factors: (1) potential damage if successful, (2) how hard they are to detect. Categories that combine high damage + low detectability get 8-10. Categories with lower impact or easier detection get 3-6. The scanner results (mcp-scan caught only 4/120) suggest most categories are in the hard-to-detect range, pushing scores upward.

### Compositional Risk Score
- **Feeding columns:** Launch commands, initialization snippets, tools, resources, prompts (the 5 modular components)
- **Proposed scale:** 1-10 where each malicious component adds incremental risk
- **Derivation:** Each server configuration is a combination of 5 component types. Score each component slot: benign = 0, malicious = 1-2 depending on component type (tools and launch commands weighted higher than prompts). Sum the component scores and normalize to 1-10. A fully benign server = 1. A server with all 5 malicious component types = 9-10. The generator's 1,046,529 possible configurations provide a huge space for training a compositional scorer.

### Detection Difficulty Tier
- **Feeding columns:** Scanner detection results (mcp-scan, AI-Infra-Guard)
- **Proposed scale:** 1-10 where 1 = trivially detected, 10 = undetectable by current tools
- **Derivation:** mcp-scan detected only 4/120 (3.3%) poisoned servers. AI-Infra-Guard did better but was still insufficient. For each attack category, compute the detection rate across scanners. Categories where both scanners fail = 9-10. Categories where at least one scanner catches it = 5-7. Categories both catch = 1-4. This dimension directly measures how much a risk scorer needs to compensate for scanner blind spots.

### Model Susceptibility
- **Feeding columns:** Host LLM identity, trial success/failure across 15 trials
- **Proposed scale:** 1-10 per LLM per attack category
- **Derivation:** For each (LLM, attack category) pair, compute success rate over 15 trials. Map 0% success → 1, 100% success → 10 linearly. This gives a model-specific risk adjustment: some LLMs may be more resistant to certain attack categories than others.

## Data Quality Notes
- The 12 hand-crafted PoCs are expert-designed and represent idealized attacks — real-world attacks may be messier or more subtle.
- The 120 generated servers use a fixed set of seeds (5 + 7 + 10 + 10 + 5 malicious components), so they sample a small fraction of the 1,046,529 possible configurations.
- Scanner evaluation is a snapshot — mcp-scan and AI-Infra-Guard may improve. The 4/120 detection rate is a point-in-time measurement.
- Paper is under review, so the dataset may not be publicly available yet. Reproducibility depends on the generator being released.
- The 3 hosts × 5 LLMs × 15 trials design is systematic but the total evaluation count per category (225 trials) is moderate.

## Usefulness Verdict
This dataset is uniquely valuable because of its **modular, compositional structure**. Most MCP attack datasets treat servers as monolithic units; this one decomposes them into 5 component types with explicit malicious/benign variants. That decomposition maps perfectly onto a multi-dimensional risk scorer — each component type becomes a scoring axis, and the combination rules become the aggregation function.

The scanner detection gap (mcp-scan catching only 3.3%) is a critical finding for risk scoring: it means detection-based defenses are insufficient, which is exactly the argument for a continuous risk score rather than binary allow/deny. The 12-category taxonomy (A1-A12) provides a structured attack surface map that can serve as ground-truth labels for training or validating a risk scorer. The generator's ability to produce over a million configurations makes this dataset scalable for training purposes, assuming the generator becomes available.
