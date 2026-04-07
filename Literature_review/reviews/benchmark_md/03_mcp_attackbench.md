# MCP-AttackBench

## Source
- **Paper:** MCP-Guard: A Multi-Stage Defense-in-Depth Framework for Securing MCP in Agentic AI (Xing et al., 2025)
- **Link:** https://arxiv.org/abs/2508.10991
- **Year:** 2025

## Format & Size
- **Total samples:** 70,448 samples total; training corpus is 5,258 samples (2,153 adversarial, 3,105 benign)
- **Format:** Structured text samples with attack/benign labels; hierarchical attack taxonomy
- **Availability:** Referenced in paper (https://arxiv.org/abs/2508.10991); check paper appendix or associated repository for data access

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Text sample | String | MCP request/tool call text | Yes | Raw input for classification |
| Binary label | Categorical | Adversarial / Benign | Yes | Top-level attack detection label |
| Attack family | Categorical (3 classes) | Semantic & Adversarial, Protocol-Specific, Injection & Execution | Partially | Hierarchical — need to check if family label is explicit in data or inferred |
| Attack subtype | Categorical | Specific attack types within each family | Partially | Granularity depends on data release format |

### Training Corpus Breakdown

| Category | Count | % of Training Set |
|---|---|---|
| Adversarial | 2,153 | 41.0% |
| Benign | 3,105 | 59.0% |
| **Total training** | **5,258** | **100%** |

## Proposed Risk Dimensions

### Attack Family Severity
- **Feeding columns:** Attack family label (3 families)
- **Proposed scale:** 1-10 mapped by family, informed by the three-stage cascade performance
- **Derivation:** The three families naturally tier by detection difficulty and impact:
  - **Injection & Execution (8-10):** Direct code/command injection — highest blast radius, can escalate to full system compromise
  - **Protocol-Specific (5-7):** Exploits MCP protocol weaknesses — requires protocol-level knowledge, medium blast radius
  - **Semantic & Adversarial (3-5):** Prompt-level manipulation — lower immediate impact but harder to detect with pattern matching alone

  The three-stage cascade results support this: Stage I pattern matching filters 38.9% of traffic in <2ms (catches obvious injection), while subtler attacks require Stage II neural analysis or Stage III LLM arbitration.

### Detection Difficulty
- **Feeding columns:** Which cascade stage catches the sample (I, II, or III)
- **Proposed scale:** 1-10 based on cascade stage required
- **Derivation:** Samples caught by Stage I (pattern matching, <2ms) = low evasion ability = risk score 1-3. Samples requiring Stage II (neural, 96.01% F1) = moderate evasion = risk score 4-7. Samples requiring Stage III (LLM arbitration) = high evasion = risk score 8-10. This directly measures how hard the attack is to detect, which is itself a risk dimension.

### Throughput-Adjusted Risk
- **Feeding columns:** Runtime latency per sample (455.9ms avg, 50.9ms optimized), speedup ratio (2.04x)
- **Proposed scale:** 1-10 factoring in detection cost
- **Derivation:** In a real-time MCP deployment, a risk that takes 455ms to detect is more dangerous during that window than one caught in 2ms. Map the latency to a "exposure window" score: <5ms = 1-2, 5-50ms = 3-4, 50-200ms = 5-6, 200-500ms = 7-8, >500ms = 9-10. This captures the operational risk dimension that static analysis misses.

## Data Quality Notes
- The big gap between total samples (70,448) and training corpus (5,258) needs clarification. The 70,448 likely includes all evaluation/test samples plus augmented variants, while the 5,258 is the curated training set. For risk scoring work, the training set composition matters more.
- The training set is moderately imbalanced (59% benign, 41% adversarial), which is actually reasonable — not as skewed as real-world traffic would be, but not artificially balanced either.
- The E5 embedding model was fine-tuned with binary cross-entropy loss on this corpus, meaning the data was used for binary classification training. The hierarchical taxonomy (3 families) may or may not be present as explicit labels in the released data.
- Stage-level cascade assignments (which stage caught each sample) would be extremely valuable for risk scoring but may need to be reproduced by running the MCP-Guard pipeline rather than being provided as static labels.
- Performance numbers (F1 95.4%, Stage II F1 96.01%) set a strong baseline — any risk scorer built on this data should aim to match or exceed these.

## Usefulness Verdict
MCP-AttackBench is the largest MCP security dataset available at 70,448 total samples, and the three-stage cascade architecture (pattern matching → neural → LLM) is directly relevant to building a practical risk scoring system. The hierarchical attack taxonomy with 3 families provides a natural coarse-grained risk categorization, while the cascade stage assignments add a unique "detection difficulty" dimension that other benchmarks lack.

The key practical insight from this benchmark is the latency-accuracy tradeoff: Stage I catches 38.9% of attacks in under 2ms, meaning a risk scorer can be fast for obvious threats and only spend computational budget on ambiguous cases. For a 1-10 risk scoring system, this benchmark contributes both the classification signal (what type of attack) and the operational signal (how hard is it to detect and how long does detection take). The training corpus at 5,258 samples is modest but proven — MCP-Guard achieved 95.4% F1 with it.
