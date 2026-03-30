# TrustLLM Benchmark Datasets

## Source
- **Paper:** TrustLLM: Trustworthiness in Large Language Models — Huang et al. (ICML 2024)
- **Link:** https://github.com/HowieHwong/TrustLLM
- **Year:** 2024

## Format & Size
- **Total samples:** 30+ datasets aggregated across 6 dimensions and 18 subcategories
- **Format:** Mixed formats per sub-dataset; evaluation framework with standardized scoring pipeline available via GitHub
- **Availability:** GitHub — https://github.com/HowieHwong/TrustLLM (code, evaluation scripts, and dataset links)

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Trustworthiness dimension | categorical | truthfulness, safety, fairness, robustness, privacy, machine ethics | Yes | 6 top-level dimensions — maps cleanly to risk scoring axes |
| Subcategory | categorical | 18 subcategories across the 6 dimensions | Yes | Granular breakdown for fine-grained scoring |
| Sub-dataset source | categorical | SQuAD2.0, TruthfulQA, HaluEval, CrowS-Pair, StereoSet, AdvGLUE, Enron Email, ETHICS, ConfAIde, MoralChoice, Social Chemistry 101, etc. | Partially | Each dataset has its own schema; needs per-dataset handling |
| Model evaluation results | numeric | Scores for 16 mainstream LLMs | Yes | Cross-model comparison baselines available |
| Safety-utility tradeoff flag | boolean/categorical | Over-cautious refusal vs. appropriate refusal vs. compliance | Yes | Critical for calibrating risk thresholds — over-safety is itself a risk |
| Prompt/scenario | string | Varies by sub-dataset | Yes | Test inputs spanning all 6 dimensions |

## Proposed Risk Dimensions

### Truthfulness Risk
- **Feeding columns:** TruthfulQA scores, HaluEval hallucination detection, SQuAD2.0 unanswerable question handling, truthfulness subcategories
- **Proposed scale:** 1-10 where 1 = highly truthful and calibrated, 10 = frequent hallucination and confident misinformation
- **Derivation:** Combine TruthfulQA accuracy (inverted: lower accuracy = higher risk) with HaluEval hallucination rates. For MCP tools, this measures the risk that an agent produces fabricated information when using a tool. Weight hallucination-on-answerable and false-confidence-on-unanswerable separately, then average to 1-10.

### Safety Risk
- **Feeding columns:** Safety dimension sub-datasets, jailbreak susceptibility tests, harmful content generation rates
- **Proposed scale:** 1-10 where 1 = consistently refuses harmful requests, 10 = readily complies with unsafe instructions
- **Derivation:** Use safety evaluation pass/fail rates across attack categories. For MCP risk scoring, this is the most direct dimension — it measures whether an agent will execute dangerous operations through a tool when prompted. Map compliance-with-harmful-request rate to 1-10.

### Fairness Risk
- **Feeding columns:** CrowS-Pair, StereoSet, fairness subcategories
- **Proposed scale:** 1-10 where 1 = no measurable bias in outputs, 10 = strong systematic discrimination
- **Derivation:** Use CrowS-Pair bias scores and StereoSet stereotype scores. For MCP, this captures whether a tool's outputs systematically disadvantage certain groups. Compute the average bias metric across protected categories and normalize to 1-10.

### Robustness Risk
- **Feeding columns:** AdvGLUE adversarial evaluation, robustness subcategories
- **Proposed scale:** 1-10 where 1 = stable under perturbation, 10 = easily destabilized by adversarial inputs
- **Derivation:** Measure accuracy drop between standard and adversarial test sets. For MCP tools, this is the attack surface dimension — how easily can adversarial inputs change tool behavior? Use (standard_acc - adversarial_acc) / standard_acc scaled to 1-10.

### Privacy Risk
- **Feeding columns:** Enron Email privacy extraction tests, ConfAIde confidentiality evaluation, privacy subcategories
- **Proposed scale:** 1-10 where 1 = no information leakage, 10 = readily reveals private/confidential data
- **Derivation:** Combine PII extraction success rates (Enron) with ConfAIde confidentiality breach rates. For MCP, this measures the risk of data exfiltration through a tool. ConfAIde adds a valuable angle — it tests whether the model respects *implicit* confidentiality, not just explicit PII.

### Machine Ethics Risk
- **Feeding columns:** ETHICS benchmark, MoralChoice survey, Social Chemistry 101, machine ethics subcategories
- **Proposed scale:** 1-10 where 1 = aligned with ethical norms, 10 = readily violates ethical boundaries
- **Derivation:** Use ETHICS accuracy and MoralChoice alignment scores. Social Chemistry 101 adds nuance by testing understanding of social norms, not just explicit ethics. For MCP, this captures whether an agent will use a tool in ways that violate organizational or societal norms. Average across sub-benchmarks, invert (lower alignment = higher risk), scale to 1-10.

### Safety-Utility Tradeoff (Meta-Dimension)
- **Feeding columns:** Over-refusal rates across safety evaluations, utility scores on benign tasks
- **Proposed scale:** 1-10 where 1 = well-calibrated (safe but useful), 10 = extreme over-refusal or extreme under-refusal
- **Derivation:** This is a meta-dimension specific to MCP risk threshold calibration. TrustLLM found that some models over-optimize safety at the cost of utility — they refuse benign requests. For MCP scoring, a tool that blocks too many legitimate operations is itself a risk (availability risk). Compute the false-refusal rate alongside the true-compliance-with-harm rate. Both extremes score high; the optimum (low score) is in the middle.

## Data Quality Notes
- With 30+ sub-datasets, data quality is uneven. Established benchmarks like SQuAD2.0 and TruthfulQA are well-validated; newer or custom datasets may have less rigorous annotation.
- The 16-model evaluation provides good cross-model baselines, but proprietary model evaluations may not be reproducible due to model versioning (API models change over time).
- Some subcategories have limited sample sizes, which affects statistical reliability of per-subcategory scores.
- The finding that proprietary LLMs are "generally more trustworthy" comes with the caveat that proprietary models have more RLHF tuning, which may optimize for benchmark performance rather than genuine trustworthiness.
- The 18-subcategory taxonomy is useful but some boundaries between subcategories are fuzzy — careful mapping is needed to avoid double-counting when aggregating to risk scores.

## Usefulness Verdict
TrustLLM is arguably the most comprehensive trustworthiness benchmark available and maps almost directly to MCP risk scoring needs. Its 6 dimensions (truthfulness, safety, fairness, robustness, privacy, machine ethics) with 18 subcategories provide both the high-level risk axes and the granular drill-down needed for a multi-label 1-10 scoring system. The inclusion of 30+ established datasets means you are building on validated data rather than starting from scratch.

The safety-utility tradeoff finding is especially important for MCP risk scoring design. A naive risk system that simply blocks everything above a threshold will create the same over-refusal problem TrustLLM documents. The risk scoring system needs to account for the cost of *not* allowing an action, not just the cost of allowing it. This directly informs how risk thresholds should be calibrated in the 1-10 model: a score of 7 should not automatically mean "block" — it should mean "require additional authorization" or "add monitoring," preserving utility while managing risk. The 18 subcategories also enable fine-grained risk profiles where a tool might score high on one subcategory (e.g., privacy) but low on another (e.g., robustness), rather than collapsing everything into a single number.
