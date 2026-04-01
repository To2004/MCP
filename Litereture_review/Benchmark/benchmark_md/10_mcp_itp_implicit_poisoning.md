# MCP-ITP Implicit Poisoning Data

## Source
- **Paper:** MCP-ITP: An Automated Framework for Implicit Tool Poisoning in MCP — Li et al.
- **Link:** https://arxiv.org/abs/2601.07395
- **Year:** 2026

## Format & Size
- **Total samples:** 548 implicit poisoning test cases (based on MCPTox dataset)
- **Format:** Tool descriptions with implicit poisoning variations, evaluated across 12 LLM agents with success/detection metrics
- **Availability:** Built on MCPTox's test cases; evaluation results across 12 models

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Test case ID | Integer | 1-548 | Yes | From MCPTox base dataset |
| Original tool description | Text | Standard tool description | Yes | Clean baseline |
| Poisoned tool description | Text | Subtly modified description with implicit steering words | Yes | Key data — the poisoned variant |
| Poisoning type | Categorical | Implicit (no explicit malicious instructions) | Yes | All cases are implicit, not explicit |
| Target LLM agent | Categorical | o1-mini, GPT-4o-mini, GPT-3.5-turbo, DeepSeek-R1, DeepSeek-V3, Gemini-2.5-flash, Qwen3 variants, etc. | Yes | 12 models evaluated |
| Attack success | Boolean | True/False | Yes | 84.2% overall success rate |
| Detection by defense | Boolean | True/False | Yes | Only 0.3% detected by AI-Infra-Guard / Oracle detectors |
| Steering words | Text tokens | Individual words embedded in descriptions | Partially | The specific words that cause behavioral steering |

## Proposed Risk Dimensions

### Implicit Poisoning Susceptibility (per model)
- **Feeding columns:** Target LLM agent, attack success (True/False) across test cases
- **Proposed scale:** 1-10 per LLM model
- **Derivation:** For each of the 12 LLMs, compute the attack success rate across the 548 test cases. Map linearly: 0% success → 1, 100% success → 10. The overall 84.2% average maps to ~8.5, meaning most models land in the 7-10 range for this dimension. Models like o1-mini (with reasoning chains) may score lower if they resist implicit steering better. This gives a model-specific risk modifier: when scoring a tool-agent pair, the agent's susceptibility score adjusts the overall risk.

### Description Toxicity Score
- **Feeding columns:** Poisoned tool description, steering words, attack success rate for that description
- **Proposed scale:** 1-10 measuring how dangerous a tool description is
- **Derivation:** The key insight from MCP-ITP is that individual words in tool descriptions can steer agent behavior without explicit malicious instructions. Score a description by: (1) count of known steering words/patterns present (from the dataset's identified set), (2) semantic similarity between the description and known poisoned variants, (3) how "innocuous" the description appears (black-box optimized descriptions that look clean but steer behavior score highest — 9-10). Clean descriptions with no steering patterns = 1-2. Descriptions with subtle steering words = 5-7. Optimized-to-look-innocent but highly effective descriptions = 8-10.

### Detection Evasion Risk
- **Feeding columns:** Detection by defense (True/False), defense tool identity
- **Proposed scale:** 1-10 where higher = harder to detect
- **Derivation:** With only 0.3% of attacks detected by existing defenses, implicit poisoning is nearly invisible to current tools. For this dimension: any tool description that uses implicit (not explicit) poisoning techniques automatically scores 8-10 for detection evasion. Explicit poisoning (obvious malicious instructions) scores 3-5 because scanners can pattern-match on it. The 0.3% detection rate means the implicit category is almost entirely in the "undetectable" tier.

### Behavioral Drift Potential
- **Feeding columns:** Attack success rate, poisoning type (implicit), original vs. poisoned description diff
- **Proposed scale:** 1-10 measuring how much agent behavior changes due to the poisoned description
- **Derivation:** Compare agent actions when given the original description vs. the poisoned variant. If the agent's behavior changes significantly (different tool calls, different data accessed, different outputs) despite the description looking nearly identical, that is high behavioral drift = 8-10. If behavior change is minimal or the agent partially resists = 4-6. No behavior change = 1-2. The 84.2% success rate suggests most test cases produce significant drift.

## Data Quality Notes
- 548 test cases is a moderate dataset size — enough to establish patterns but may not cover all implicit poisoning strategies.
- The dataset is built on MCPTox, so it inherits MCPTox's scope and limitations. New poisoning techniques not in MCPTox are not represented.
- The 84.2% success rate and 0.3% detection rate are aggregate numbers across all 12 models and 548 cases. Per-model and per-case variation is important but not fully detailed here.
- The "individual words can steer behavior" finding is powerful but the specific word list and its completeness are unclear — adversaries could use words not in the studied set.
- Black-box optimization for generating innocuous-appearing descriptions is effective but the optimization process may not generalize to all tool types or domains.
- The 12 LLMs tested span a good range (OpenAI, Google, DeepSeek, Qwen) but do not include Anthropic models or some newer releases.

## Usefulness Verdict
This dataset addresses the **hardest problem in MCP risk scoring**: attacks that are invisible to both humans and automated scanners. The 0.3% detection rate by existing defenses is the single most important number for justifying why a continuous risk score (1-10) is needed instead of binary detection. If your scanner says "safe" 99.7% of the time when the tool is actually poisoned, you need a richer signal.

For building a multi-dimensional scorer, the per-model vulnerability data is directly actionable — it enables **model-specific risk adjustment**, so the same tool gets different risk scores depending on which LLM agent will use it. The description toxicity patterns (steering words, optimized-to-look-clean descriptions) can feed into a text-analysis component of the scorer. The main limitation is dataset size (548 cases), but since each case is evaluated across 12 models, the effective evaluation count is 6,576 data points, which is workable for training a scoring model.
