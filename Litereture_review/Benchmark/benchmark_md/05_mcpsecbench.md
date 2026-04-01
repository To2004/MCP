# MCPSecBench Playground

## Source
- **Paper:** MCPSecBench: A Systematic Security Benchmark and Playground for Testing Model Context Protocols (Yang et al., 2025)
- **Link:** https://arxiv.org/abs/2508.13220
- **Year:** 2025

## Format & Size
- **Total samples:** 17 attack types across 4 attack surfaces, with LLM-based prompt variation; 15 trials per attack per client
- **Format:** Prompt dataset with multi-layer evaluation; playground environment for live testing
- **Availability:** arXiv (https://arxiv.org/abs/2508.13220); check for associated GitHub repository

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Attack type | Categorical (17 types) | Specific attack names across 4 surfaces | Yes | Fine-grained attack classification |
| Attack surface | Categorical (4 classes) | Client-side, protocol-side, server-side, host-side | Yes | Primary risk dimension — where in the MCP stack the attack targets |
| Prompt variant | String | LLM-generated variation of attack prompt | Yes | Tests robustness to rephrasing |
| Target client | Categorical | Claude Desktop, OpenAI GPT-4.1, Cursor v2.3.29 | Yes | Client-specific vulnerability data |
| ASR per trial | Float (0-1) | Success/failure across 15 trials | Yes | Statistical reliability from multiple trials |
| Refusal Rate (RR) | Float (0-1) | Proportion of trials where client refused | Yes | Measures built-in safety mechanisms |
| Cost per round | Float (USD) | $0.41 - $0.76 | Yes | Practical deployment cost data |

### ASR by Attack Surface

| Attack Surface | ASR | Risk Implication |
|---|---|---|
| Protocol-side | 100% | Critical — no current defenses work |
| Server-side | ~47% | High — roughly half of attacks succeed |
| Client-side | ~33% | Moderate — some built-in client protections |
| Host-side | ~27% | Lower — host-level defenses are more mature |

## Proposed Risk Dimensions

### Attack Surface Severity
- **Feeding columns:** Attack surface (4 classes), ASR per surface
- **Proposed scale:** 1-10 directly mapped from empirical ASR
- **Derivation:** The ASR data provides an empirically-grounded severity scale:
  - **Protocol-side: 10** — 100% ASR means every attack succeeds. This is a fundamentally broken layer with zero effective defense currently.
  - **Server-side: 7** — ~47% ASR indicates significant vulnerability with partial mitigation
  - **Client-side: 5** — ~33% ASR shows some protection but still dangerous
  - **Host-side: 4** — ~27% ASR reflects more mature defenses but still non-trivial risk

  This is one of the few benchmarks where risk scores can be directly derived from empirical attack success rates rather than estimated.

### Attack Type Granularity
- **Feeding columns:** Attack type (17 types), attack surface mapping
- **Proposed scale:** 1-10 per attack type, nested within surface severity
- **Derivation:** Within each attack surface, rank the 17 types by their individual ASR. Types with ASR above the surface average score higher; types below average score lower. This gives a two-level risk score: surface-level (coarse) + type-level (fine).

### Client Resilience
- **Feeding columns:** Target client, ASR per client, Refusal Rate per client
- **Proposed scale:** 1-10 per client (inverse — higher score = more vulnerable client)
- **Derivation:** For each of the 3 tested clients (Claude Desktop, GPT-4.1, Cursor), compute: `vulnerability_score = (ASR * 10) * (1 - RR)`. A client with high ASR and low refusal rate scores 9-10; a client with low ASR and high refusal rate scores 1-3. This provides client-specific risk adjustment.

### Economic Cost of Detection
- **Feeding columns:** Cost per testing round ($0.41-$0.76)
- **Proposed scale:** Informational (not 1-10), but feeds into cost-benefit analysis
- **Derivation:** At $0.41-$0.76 per round, the cost of running security evaluations is non-trivial at scale. For enterprise deployment, multiply by expected traffic volume to get monthly security testing cost. This is relevant for Lenovo's cost constraint.

## Data Quality Notes
- The sample size per attack type is relatively small: 17 types x 15 trials x 3 clients = 765 total trial outcomes. This gives statistical significance within each cell (15 trials per condition) but limited power for detecting small differences between attack types.
- LLM-based prompt variation is a strength (tests robustness to rephrasing) but introduces an uncontrolled variable — the quality and diversity of generated variants depend on the LLM used for generation.
- The 100% protocol-side ASR is a headline finding but needs context: it may reflect that protocol-level attacks are fundamentally different from prompt-level attacks, targeting the transport/schema layer where LLM-based defenses are irrelevant.
- Testing only 3 clients (Claude Desktop, GPT-4.1, Cursor) limits generalizability. These are all consumer/developer tools — enterprise MCP clients may have different vulnerability profiles.
- The playground format is valuable for reproducibility but means this is more of a testing framework than a static dataset. Results may change as clients update their defenses.

## Usefulness Verdict
MCPSecBench provides the most structured attack surface taxonomy of any MCP benchmark: 4 surfaces x 17 types, with empirical ASR data per surface. The 100% protocol-side ASR is a critical finding that any risk scoring system must account for — it means protocol-level attacks should automatically receive the maximum risk score. The playground format also means this benchmark can be re-run as defenses improve, making it useful for longitudinal risk tracking.

For a 1-10 risk scoring system, MCPSecBench's main contribution is the attack surface dimension. Most other benchmarks focus on attack type or intent category, but this one asks "where in the MCP stack is the attack hitting?" — which is directly actionable for defense prioritization. The cost data ($0.41-$0.76 per round) is also practically valuable for Lenovo's deployment planning. The limitation is scale: 17 attack types is comprehensive for taxonomy but the per-type sample count is small compared to MCP-AttackBench's 70k samples.
