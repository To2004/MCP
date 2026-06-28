# Persona-critic panel

Five opinionated LLM reviewers, each with a different personality and lens, told to find what is weak. Their critiques are the raw material for the improvement plan.

**5 critics · 27 critiques** (critical:6, high:8, medium:12, low:1)

## Vera, the red-teamer

> The MCP security pipeline is fundamentally flawed due to its reliance on an LLM for scoring and its inability to handle multi-step threats.

- **[critical] High fragility of band cut-points under input perturbation**
    - *why:* 85% of cells are fragile, meaning a minor change in inputs can drastically alter the risk score and bypass security controls.
    - *fix:* Implement more robust scoring thresholds that reduce sensitivity to small changes in input parameters.
- **[high] Lack of multi-step threat modeling**
    - *why:* The pipeline scores calls individually, ignoring the cumulative risk from a series of seemingly low-risk actions.
    - *fix:* Integrate a mechanism to evaluate and score sequences of tool calls for their combined impact.
- **[medium] Circular ground truth reliance**
    - *why:* The accuracy is measured against the scanner's own LLM-generated tables, leading to potential self-confirmation bias.
    - *fix:* Use an independent and diverse set of ground truths for validation that includes real-world scenarios.
- **[medium] Low inter-rater agreement among oracles**
    - *why:* The scanner's consensus with human/oracle panels is only 35% exact, indicating significant potential for misclassification.
    - *fix:* Improve the LLM training data and validation process to better align with expert judgments.
- **[low] Coarse asset scoping**
    - *why:* Assets are scoped at a high level (e.g., entire calendars), which can mask specific, targeted attacks.
    - *fix:* Refine the scope of assets to include more granular instances such as individual events or files.

## Klaus, the statistician

> The MCP security pipeline's reliance on a single LLM for both ground truth and scoring introduces significant circularity and undermines confidence in its accuracy.

- **[critical] Circular Ground Truth Generation**
    - *why:* Using the scanner's own LLM-generated tables as ground truth creates a self-referential loop, leading to potential overfitting and inflated agreement metrics.
    - *fix:* Develop an independent ground truth using human experts or a diverse panel of frameworks that do not include the scanner's LLM.
- **[high] Low Agreement Metrics**
    - *why:* The overall exact agreement between the scanner and consensus is only 35%, which is insufficient for high-stakes security decisions.
    - *fix:* Improve the scoring formula or LLM training to increase the exact band agreement with the consensus panel.
- **[high] High Fragility of Band Assignments**
    - *why:* 85% of cells are fragile under a ±1 perturbation, indicating that small changes in input can drastically alter risk assessments.
    - *fix:* Strengthen the scoring formula to reduce fragility and ensure more stable band assignments.
- **[medium] Lack of Confidence Intervals**
    - *why:* Without confidence intervals or significance tests, it is impossible to assess the reliability of reported metrics.
    - *fix:* Include statistical measures such as confidence intervals and p-values in all reported metrics.
- **[medium] Limited Scope of Asset Definition**
    - *why:* Assets are defined at a coarse level (e.g., entire calendars or repositories), which may not capture fine-grained risks.
    - *fix:* Refine asset definitions to include more granular instances such as individual files or events.
- **[medium] No Multi-Step Chain Modelling**
    - *why:* The pipeline does not account for multi-step chains and cross-call aggregations, which could lead to underestimation of risk.
    - *fix:* Incorporate a mechanism to model multi-step chains and aggregate risks across multiple calls.

## Mona, the SRE

> This pipeline is a ticking time bomb with high false positives and unstable scoring that will break at 3am.

- **[critical] Unresolved calls are silently dropped without any logging or alerting.**
    - *why:* Silent failures can lead to undetected security vulnerabilities and operational issues.
    - *fix:* Add comprehensive logging for unresolved calls and implement alerts for silent drops.
- **[critical] Formula sensitivity is extremely high, with 85% of cells being fragile under minor input perturbations.**
    - *why:* The scoring system is unstable and can lead to inconsistent risk assessments across similar inputs.
    - *fix:* Strengthen the formula by introducing more robust thresholds or smoothing techniques to reduce fragility.
- **[high] High false-positive rate in gate marking routine reads HIGH.**
    - *why:* Routine operations may be incorrectly flagged as risky, leading to unnecessary throttling or denial of service.
    - *fix:* Implement a more nuanced scoring mechanism that considers historical data and context for each tool call.
- **[high] Non-reproducibility across GPUs/model versions.**
    - *why:* Inconsistent results can lead to security gaps or false negatives/positives depending on the execution environment.
    - *fix:* Ensure reproducibility by fixing model parameters and using deterministic settings (e.g., fixed seeds, temperature=0) across all environments.
- **[medium] Lack of a cheap deterministic fast-path for common operations.**
    - *why:* Performance degradation due to reliance on LLM for every operation can lead to increased latency and cost.
    - *fix:* Develop a lightweight, deterministic path for frequently occurring and low-risk operations.
- **[medium] 1-hour LLM scan that must rerun whenever a file changes.**
    - *why:* High operational cost and latency due to frequent full scans can lead to performance bottlenecks.
    - *fix:* Implement incremental scanning or caching mechanisms to reduce the frequency of full scans.

## Ada, the security architect

> The MCP security pipeline is overly reliant on a single LLM for scoring and lacks comprehensive coverage of multi-step attack vectors, leading to significant risk underestimation.

- **[critical] Lack of multi-step call chain analysis**
    - *why:* The pipeline fails to account for multi-step attack vectors, which can aggregate risk across multiple low-scoring calls.
    - *fix:* Implement a dynamic analysis component that evaluates the cumulative risk of multi-step call chains.
- **[high] Over-reliance on Qwen2.5 LLM for banding decisions**
    - *why:* The pipeline's reliance solely on the Qwen2.5 LLM for banding decisions introduces a single point of failure and potential bias, leading to inaccurate risk assessments.
    - *fix:* Integrate multiple independent oracles (e.g., human experts, other LLMs) to cross-verify banding decisions.
- **[high] Formula sensitivity and fragility**
    - *why:* The scoring formula is highly sensitive to small input changes, leading to unstable banding decisions.
    - *fix:* Refine the scoring formula to reduce sensitivity and increase stability under minor perturbations.
- **[medium] Abstract asset modeling vs. per-instance sensitivity**
    - *why:* The pipeline models assets at a coarse scope (e.g., entire calendars/repos) rather than individual instances, potentially missing nuanced risk factors.
    - *fix:* Enhance the model to consider per-instance asset sensitivity for more granular risk assessment.
- **[medium] Circular ground truth validation**
    - *why:* Using the scanner's own LLM tables as ground truth introduces circular reasoning and reduces confidence in accuracy.
    - *fix:* Develop an independent, external ground truth dataset for validating scanner accuracy.

## Sam, the minimalist

> The MCP security pipeline is overly complex and fragile, with questionable accuracy and unnecessary reliance on a large LLM.

- **[critical] High fragility in band cut-points (85% cells flip bands under minor input perturbations).**
    - *why:* This indicates that the risk scores are highly sensitive to small changes, leading to unreliable and potentially inconsistent security decisions.
    - *fix:* Stabilize band cut-points by increasing their robustness or using a more stable scoring formula.
- **[high] Over-reliance on a 32B LLM (Qwen2.5) for risk scoring when simpler models or rule-based systems could suffice.**
    - *why:* The large model introduces unnecessary complexity and computational overhead without clear evidence of superior performance over simpler alternatives.
    - *fix:* Replace the LLM with a smaller, more efficient model or a deterministic rule-based system for risk scoring.
- **[medium] Lack of ground truth for most servers, relying on the scanner's own LLM tables for accuracy checks.**
    - *why:* This circular validation method undermines confidence in the system’s accuracy and reliability.
    - *fix:* Develop an independent ground truth dataset or use a more diverse set of external validators to ensure unbiased evaluation.
- **[medium] No consideration for multi-step chains and cross-call aggregation, leading to potential oversight of cumulative risk.**
    - *why:* Ignoring the context of multiple calls can result in underestimating or overestimating risks, especially in complex scenarios.
    - *fix:* Integrate a mechanism for analyzing multi-step chains and aggregating cross-call risks to provide a more holistic risk assessment.
- **[medium] Coarse asset scoping (e.g., entire calendars/repos/channels) without finer-grained analysis.**
    - *why:* This coarse granularity may miss critical details that could significantly impact the security posture of individual assets.
    - *fix:* Refine asset scoping to include more granular instances (e.g., per-event/per-file) for a more precise risk assessment.
