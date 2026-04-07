# MCIP-Bench

## Source
- **Paper:** MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol (Jing et al., 2025)
- **Link:** https://github.com/HKUST-KnowComp/MCIP
- **Year:** 2025

## Format & Size
- **Total samples:** 2,218 synthesized instances (1,192 from Glaive AI + 1,026 from ToolACE)
- **Format:** Multi-turn function-calling dialogues with safety labels; each instance contains ~6 dialogue turns
- **Availability:** GitHub (https://github.com/HKUST-KnowComp/MCIP)

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Dialogue turns | List of dicts | User/assistant/tool messages across ~6 turns | Yes | Multi-turn format captures realistic agent interactions |
| Safety label (binary) | Boolean/int | Safe / Unsafe (1 / 0) | Yes | Used for Safety Awareness evaluation |
| Risk category (11-class) | Categorical string | Identity Injection, Function Overlapping, True (safe) | Yes | 10 risk types + 1 safe/gold class |
| Source dataset | Categorical | Glaive AI, ToolACE | Yes | Useful for tracking data provenance and potential bias |
| Function calls | Structured JSON | Tool name, parameters, return values | Yes | Core signal for function-level risk analysis |

## Proposed Risk Dimensions

### Attack Type Classification (multi-label)
- **Feeding columns:** Risk category (11-class label)
- **Proposed scale:** 1-10 where each of the 10 risk types maps to a severity score based on potential impact
- **Derivation:** Direct mapping from the 10 risk categories. Suggested severity tiers:
  - **Critical (8-10):** Identity Injection, Function Injection, Data Injection — these allow direct compromise of agent identity or data integrity
  - **High (5-7):** Excessive Privileges Overlapping, Replay Injection, Causal Dependency Injection — these exploit trust boundaries and control flow
  - **Medium (3-4):** Function Overlapping, Function Dependency Injection, Wrong Parameter Intent Injection, Ignore Purpose Intent Injection — these manipulate tool selection or parameter semantics

### Detection Granularity
- **Feeding columns:** Both binary safety label and 11-class risk category
- **Proposed scale:** Two-tier evaluation — coarse (binary safe/unsafe) and fine-grained (specific attack type)
- **Derivation:** Binary label gives a quick pass/fail filter (Stage I in a cascade). The 11-class label gives the specific risk type for scoring. A model that passes binary but fails 11-class detection has a "detection gap" that itself is a risk signal.

### Dialogue Complexity
- **Feeding columns:** Number of dialogue turns, function call count per instance
- **Proposed scale:** 1-10 based on turn count and tool invocation density
- **Derivation:** More turns = more opportunities for injection. Count turns and tool calls, normalize across the dataset. Instances with 8+ turns and 3+ tool calls score higher on complexity risk.

## Data Quality Notes
- The dataset is fully synthesized, not collected from real-world MCP deployments. This means the attack patterns are controlled and well-labeled but may not capture the messy, edge-case nature of real attacks.
- The split between Glaive AI (1,192) and ToolACE (1,026) sources could introduce distributional differences — worth checking if models perform differently on each subset.
- The "True" (safe/gold) class has a specific count in the training set (1,791 in the companion Guardian dataset), but the bench split distribution across the 11 classes is not explicitly documented — may need to compute class balance manually.
- No explicit severity ranking among the 10 risk types is provided by the authors; the severity tiers above are proposed based on potential impact analysis.

## Usefulness Verdict
MCIP-Bench is one of the most directly useful benchmarks for multi-label risk scoring because it already provides a fine-grained 10-category attack taxonomy alongside a binary safety label. This dual-evaluation structure (Safety Awareness + Risk Resistance) maps naturally to a two-stage risk scoring system: first detect whether a risk exists, then classify what kind and how severe. The 10 risk types cover a broad spectrum from identity attacks to parameter manipulation, giving solid coverage for building a multi-dimensional risk score.

The main limitation is size — 2,218 instances is enough for evaluation but thin for training. The multi-turn dialogue format is a strength, since real MCP interactions are conversational, not single-shot. For a 1-10 risk scoring system, this benchmark provides the label taxonomy; the severity weighting within that taxonomy is something we need to define ourselves based on impact analysis.
