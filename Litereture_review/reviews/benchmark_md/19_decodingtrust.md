# DecodingTrust Dataset

## Source
- **Paper:** DecodingTrust: A Comprehensive Assessment of Trustworthiness in GPT Models — Wang et al. (NeurIPS 2023 Outstanding Paper)
- **Link:** https://huggingface.co/datasets/AI-Secure/DecodingTrust
- **Year:** 2023

## Format & Size
- **Total samples:** Varies per sub-benchmark (aggregate of multiple established datasets plus custom evaluation sets across 8 dimensions)
- **Format:** HuggingFace dataset collection with per-dimension subsets; each sub-benchmark has its own prompt/response format
- **Availability:** HuggingFace — https://huggingface.co/datasets/AI-Secure/DecodingTrust

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Evaluation dimension | categorical | toxicity, stereotype bias, adversarial robustness, OOD robustness, adversarial demonstrations, privacy, machine ethics, fairness | Yes | 8 top-level dimensions — these are the core scoring axes |
| Sub-benchmark source | categorical | RealToxicityPrompts, BOLD, BBQ, SST-2, AdvGLUE, ANLI, RealtimeQA, MMLU, Enron Email, ETHICS, Jiminy Cricket, Adult (UCI) | Partially | Each sub-benchmark has its own schema; needs per-benchmark parsing |
| Prompt/input text | string | Varies by sub-benchmark | Yes | The actual test input fed to models |
| Model response | string | GPT-4 and GPT-3.5 outputs | Yes | Baseline comparison responses available |
| Trustworthiness score | numeric | Per-dimension scores for GPT-4 vs GPT-3.5 | Yes | Aggregated metrics per dimension; raw per-sample scores vary by sub-benchmark |
| Jailbreak susceptibility | boolean/numeric | GPT-4 more vulnerable than GPT-3.5 | Yes | Key finding: higher capability does not equal higher trustworthiness |

## Proposed Risk Dimensions

### Toxicity Risk
- **Feeding columns:** RealToxicityPrompts and BOLD sub-benchmark outputs; toxicity dimension scores
- **Proposed scale:** 1-10 where 1 = model consistently avoids toxic output, 10 = model readily produces toxic content even with mild prompting
- **Derivation:** Map the toxicity evaluation scores (typically 0-1 probability) to a 1-10 scale. For MCP tools, this measures the risk that an agent's output through a tool will contain harmful content. Aggregate across prompt categories (mild, moderate, adversarial) with heavier weight on adversarial prompts.

### Stereotype & Fairness Risk
- **Feeding columns:** BBQ (bias benchmark), stereotype bias dimension, fairness dimension, Adult (UCI) dataset results
- **Proposed scale:** 1-10 where 1 = no measurable bias, 10 = strong systematic bias across protected categories
- **Derivation:** Combine stereotype bias scores and fairness metrics. For MCP risk scoring, this captures whether a tool/agent introduces discriminatory outputs. Use the BBQ accuracy gap across demographic groups as the base metric, normalized to 1-10.

### Adversarial Robustness Risk
- **Feeding columns:** AdvGLUE, ANLI, adversarial demonstrations dimension, adversarial robustness dimension
- **Proposed scale:** 1-10 where 1 = robust to adversarial inputs, 10 = trivially broken by adversarial perturbations
- **Derivation:** Measure accuracy drop between clean and adversarial inputs. For MCP, this directly maps to how easily an attacker can manipulate tool behavior through crafted inputs. Compute (clean_accuracy - adversarial_accuracy) / clean_accuracy, then scale to 1-10.

### Privacy Leakage Risk
- **Feeding columns:** Enron Email sub-benchmark, privacy dimension scores
- **Proposed scale:** 1-10 where 1 = no PII leakage, 10 = readily extracts/reveals private information
- **Derivation:** Use the privacy evaluation metrics (PII extraction success rate, memorization rate) from the Enron Email tests. For MCP, this measures the risk that a tool leaks sensitive data from its context or training data. Map extraction success rates directly to the 1-10 scale.

### Machine Ethics Risk
- **Feeding columns:** ETHICS dataset, Jiminy Cricket sub-benchmark, machine ethics dimension
- **Proposed scale:** 1-10 where 1 = consistently ethical choices, 10 = readily complies with unethical requests
- **Derivation:** Use accuracy on ETHICS benchmark scenarios and Jiminy Cricket moral evaluations. For MCP risk scoring, this measures whether an agent will follow harmful instructions through a tool. Invert accuracy (lower accuracy = higher risk score) and map to 1-10.

### Out-of-Distribution Robustness Risk
- **Feeding columns:** RealtimeQA, MMLU, OOD robustness dimension
- **Proposed scale:** 1-10 where 1 = stable performance on OOD inputs, 10 = severe degradation on unfamiliar inputs
- **Derivation:** Measure performance gap between in-distribution and OOD test sets. For MCP, this captures the risk that a tool behaves unpredictably when inputs differ from expected patterns. Compute the relative performance drop and scale to 1-10.

## Data Quality Notes
- The dataset is a meta-collection of established benchmarks, so data quality varies per sub-benchmark. Some (like RealToxicityPrompts) are well-validated; others may have labeling noise.
- Baselines are only for GPT-4 and GPT-3.5 — no open-source model baselines in the original evaluation, which limits cross-model comparisons.
- Some sub-benchmarks overlap in what they measure (e.g., adversarial robustness and adversarial demonstrations are related but distinct), which can cause double-counting in aggregate scoring.
- The Enron Email privacy benchmark tests a specific type of memorization — it does not cover all privacy risks (e.g., inference attacks, context window leakage).
- Scores are not inherently on a 1-10 scale; each dimension uses its own metric, requiring normalization before cross-dimension comparison.

## Usefulness Verdict
DecodingTrust is one of the most directly useful benchmarks for MCP multi-dimensional risk scoring. Its 8-dimension framework provides a ready-made rubric template — toxicity, bias, robustness, privacy, ethics, and fairness are all dimensions that matter when an AI agent invokes MCP tools in an enterprise setting. The sub-benchmark structure means you can cherry-pick the most relevant evaluations for your specific risk model rather than treating it as a monolithic score.

The most critical insight for MCP risk scoring design is the finding that GPT-4 is more vulnerable to jailbreaking than GPT-3.5 despite having better baseline performance. This directly validates the thesis that capability and trustworthiness are not the same dimension — a more capable agent is not automatically safer, and may in fact need *higher* scrutiny. This "capability ≠ trustworthiness" principle should be baked into how the 1-10 risk scores are calibrated: agent capability level should be an independent variable, not a proxy for safety.
