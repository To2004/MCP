# AgentDojo Task Suites

## Source
- **Paper:** AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents (Debenedetti et al., 2024)
- **Link:** https://github.com/ethz-spylab/agentdojo
- **Year:** 2024

## Format & Size
- **Total samples:** 97 user tasks and 629 injection tasks across 4 task suites
- **Format:** Dynamic environment with parameterized attack generation; pip-installable Python package (Python 3.10+)
- **Availability:** GitHub (https://github.com/ethz-spylab/agentdojo) — fully open source, pip installable

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Task suite / domain | Categorical | Workspace, Travel, Banking, Slack | Yes | 4 domains covering distinct enterprise contexts |
| User task | Structured task object | Natural-language task instructions with expected outcomes | Yes | 97 tasks total across the 4 suites |
| Injection task | Structured attack object | Parameterized prompt injection payloads | Yes | 629 injection tasks — ~6.5x more injections than user tasks |
| Attack implementation | Code/config | Multiple attack strategies per injection | Yes | Dynamic generation means attacks are not static strings |
| Defense baseline | Categorical/config | repeat_user_prompt, spotlighting_with_delimiting, tool_filter, transformers_pi_detector, DataSentinel, Llama Prompt Guard 2 | Yes | 6 published defense baselines for direct comparison |
| Utility score | Float (%) | Task completion rate on benign tasks | Yes | Measures whether defense degrades normal functionality |
| ASR | Float (%) | Attack success rate under each defense | Yes | Primary adversarial metric |
| Additional metrics | Float | AUC, Recall@1%FPR, TPR, FPR, Balanced Accuracy, F1 | Yes | Rich metric suite for fine-grained evaluation |

## Proposed Risk Dimensions

### Domain-Specific Risk Context
- **Feeding columns:** Task suite (Workspace, Travel, Banking, Slack)
- **Proposed scale:** 1-10 per domain, calibrated by the sensitivity of the domain's typical operations
- **Derivation:** Banking tasks involve financial transactions and PII — baseline risk starts at 7. Workspace tasks involve document access and email — baseline 5. Travel tasks involve booking and itinerary data — baseline 4. Slack tasks involve messaging and channel access — baseline 3-5 depending on channel sensitivity. The domain label acts as a context multiplier applied to other risk dimensions. A tool invocation in the Banking suite should score higher than an identical invocation pattern in the Travel suite.

### Utility-Security Tradeoff Calibration
- **Feeding columns:** Utility (%), Utility under attack (%), ASR (%)
- **Proposed scale:** 1-10 representing the "cost" of applying a defense, where 1 = defense is free (no utility loss, large ASR drop) and 10 = defense is crippling (heavy utility loss, small ASR drop)
- **Derivation:** Compute the ratio: (utility drop) / (ASR reduction). A defense that drops utility by 2% but cuts ASR by 30% has a low cost ratio (good) → score 2. A defense that drops utility by 15% but only cuts ASR by 5% is expensive → score 8-9. This dimension is not about the tool itself but about whether the defense layer applied to it is calibrated correctly. Progent achieved ASR reduction from 41.2% to 2.2% — this provides a strong reference point for what "effective defense" looks like.

### Defense Coverage Gap
- **Feeding columns:** ASR across all 6 defense baselines, per injection task
- **Proposed scale:** 1-10 where 1 = all defenses block the attack, 10 = no defense blocks it
- **Derivation:** For each injection task, count how many of the 6 defense baselines fail to prevent it. If 0/6 fail (all defenses work), score = 1. If 6/6 fail (no defense works), score = 10. Linear interpolation in between. This gives a per-attack "evasiveness" score that directly feeds into risk: attacks that bypass all known defenses are the highest risk.

## Data Quality Notes
- The 97 user tasks are relatively few for training purposes, but the 629 injection tasks provide good adversarial coverage. The ratio (~6.5 injections per user task) means evaluation leans adversarial, which is appropriate for security benchmarking but may overestimate attack prevalence.
- The dynamic/parameterized nature of the environment means the actual number of evaluable instances is much larger than 629 — attack parameters can be varied to generate many concrete instances per template. This is a strength for robustness testing but makes exact dataset size hard to pin down.
- The 6 defense baselines cover a good range (prompting-based, filtering-based, ML-based) but the defense landscape moves fast. New defenses (like Progent) have already been evaluated on AgentDojo, so the baseline set keeps growing.
- Metrics are comprehensive (ASR, AUC, Recall@1%FPR, TPR, FPR, Balanced Accuracy, F1), which means you can pick the metric most relevant to your risk dimension without re-running experiments.

## Usefulness Verdict
AgentDojo is one of the most practically useful benchmarks for building a multi-dimensional risk scorer because it is a living, extensible environment rather than a static dataset. The 4 domain-specific task suites provide natural context segmentation — you can calibrate risk scores differently for banking vs. messaging vs. travel, which is exactly what an enterprise deployment needs. The wide adoption of AgentDojo across the research community (used by Progent, referenced by multiple defense papers) means results are directly comparable with published numbers.

For a 1-10 risk scoring system, AgentDojo's main contribution is the utility-security tradeoff data. Most benchmarks only measure "does the attack succeed?" AgentDojo also measures "what does defense cost in terms of usability?" This is critical for practical deployment: a risk score of 8 means nothing if the only defense that addresses it also breaks 40% of legitimate tasks. The Progent result (ASR from 41.2% to 2.2%) sets a concrete ceiling for what defense effectiveness looks like, giving us a calibration anchor for the upper end of the risk scale.
