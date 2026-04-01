# ASB (Agent Security Bench)

## Source
- **Paper:** Agent Security Bench (Zhang et al., 2025)
- **Link:** https://github.com/agiresearch/ASB
- **Year:** 2025

## Format & Size
- **Total samples:** Not explicitly documented as a fixed count — the benchmark is structured around 6 attack prompt types evaluated against agent tasks
- **Format:** Attack prompts paired with agent tasks; measures Utility (%) and ASR (%) per attack type and defense combination
- **Availability:** GitHub (https://github.com/agiresearch/ASB)

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Attack prompt type | Categorical (6 types) | combined_attack, context_ignoring, escape_characters, fake_completion, naive, average | Yes | Core taxonomy — 6 distinct attack strategies |
| Utility score | Float (%) | Task completion rate under each condition | Yes | Measures collateral damage of attacks/defenses |
| ASR | Float (%) | Attack success rate per attack type | Yes | Primary adversarial effectiveness metric |
| Defense baseline | Categorical | delimiters, sandwich, instructional prevention | Yes | 3 defense strategies for comparison |
| Agent task | Structured | The legitimate task the agent is trying to complete | Yes | Context for measuring utility degradation |

## Proposed Risk Dimensions

### Attack Type Input-Level Risk
- **Feeding columns:** Attack prompt type (6 categories)
- **Proposed scale:** 1-10 where each attack type maps to a risk level based on its typical ASR and evasiveness
- **Derivation:** Rank the 6 attack types by their average ASR across all tested configurations. The "naive" type likely has the lowest ASR (simple, easily caught) — score 2-3. "combined_attack" likely has the highest ASR (combines multiple evasion strategies) — score 8-9. The remaining four fall in between based on their measured success rates. At runtime, if an incoming input matches the signature of a high-ASR attack type, the risk score increases accordingly. The "average" type serves as a baseline reference point. Specific proposed ordering (to be validated against ASB results):
  - **naive:** 2-3 (easy to detect, low sophistication)
  - **escape_characters:** 4-5 (exploits formatting, moderate evasion)
  - **context_ignoring:** 5-6 (attempts to override context, moderate success)
  - **fake_completion:** 6-7 (tricks the agent into thinking the task is done, harder to detect)
  - **combined_attack:** 8-9 (multi-strategy, highest evasion)

### Utility-Security Threshold Calibration
- **Feeding columns:** Utility (%), ASR (%), defense baseline
- **Proposed scale:** 1-10 representing the operating point on the utility-security tradeoff curve
- **Derivation:** For each defense baseline (delimiters, sandwich, instructional prevention), compute the tradeoff ratio: (ASR reduction) / (utility drop). Plot these as points on a Pareto frontier. A risk score of 5 means the system is operating at the balanced midpoint; scores below 5 mean security is being sacrificed for utility; scores above 5 mean utility is being sacrificed for security. This dimension does not score individual inputs — it scores the system's overall configuration. It answers: "given the defense stack we have deployed, how well-calibrated are we?"

### Cross-Paper Comparability Score
- **Feeding columns:** Attack prompt type, ASR, Utility — standardized format
- **Proposed scale:** Not a 1-10 risk score per se, but a metadata dimension that records whether a given result can be directly compared to published numbers
- **Derivation:** ASB is used by both Progent and ToolSafe for evaluation, which means results obtained on ASB are directly comparable with at least two published defense systems. For any new defense or risk scorer, running on ASB and comparing against these published baselines gives immediate context for how the system performs relative to the state of the art. This is a practical advantage rather than a risk dimension, but it affects the confidence level of any risk score derived from ASB data.

## Data Quality Notes
- The exact total sample count is not prominently documented — ASB is structured more as a framework (6 attack types x N tasks x 3 defenses) than a fixed dataset with a sample count. This means you need to run the benchmark to generate results rather than loading a static CSV.
- The 6 attack types are well-defined but somewhat generic. "naive," "escape_characters," and "fake_completion" are common across many injection benchmarks, so ASB's attack taxonomy overlaps heavily with other benchmarks. Its value is in the standardized evaluation protocol, not in unique attack coverage.
- The 3 defense baselines (delimiters, sandwich, instructional prevention) are all prompting-based defenses. There are no ML-based or architectural defenses in the baseline set, unlike AgentDojo which includes transformers_pi_detector and DataSentinel. This limits the defense coverage.
- The "average" attack type is ambiguous — it may represent an average across other types or a specific blended attack. Needs clarification from the repository documentation.
- Used by Progent and ToolSafe, which validates the benchmark's relevance and ensures published comparison points exist.

## Usefulness Verdict
ASB's primary value for multi-label risk scoring is as a standardized evaluation protocol rather than a rich data source. The 6 attack types provide a clean input-level risk taxonomy, and the Utility/ASR dual-metric structure ensures that any risk score considers both security effectiveness and usability cost. The fact that both Progent and ToolSafe have published results on ASB means you get free comparison baselines — you can immediately contextualize your risk scorer's performance against two known systems.

The limitation is depth. With only 6 attack types and 3 defense baselines, ASB is narrower than AgentDojo (which has 629 injection tasks and 6 defense baselines) or MCIP-Bench (which has 10 risk categories). ASB is best used as a secondary evaluation benchmark for cross-paper comparison rather than as a primary data source for training or calibrating a multi-dimensional risk scorer. Run your system on ASB to get comparable numbers, but rely on richer benchmarks for the actual risk dimension definitions and training data.
