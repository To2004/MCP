# MCIP Guardian Training Dataset

## Source
- **Paper:** MCIP: Protecting MCP Safety via Model Contextual Integrity Protocol (Jing et al., 2025)
- **Link:** https://github.com/HKUST-KnowComp/MCIP
- **Year:** 2025

## Format & Size
- **Total samples:** 13,830 instances across 11 categories
- **Format:** MCI (Model Contextual Integrity) format with ~8 transmission steps per instance
- **Availability:** GitHub (https://github.com/HKUST-KnowComp/MCIP)

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Risk category | Categorical (11 classes) | True, Identity Injection, Function Overlapping, etc. | Yes | Primary label for classification |
| Transmission steps | Ordered list (~8 per instance) | Sender, receiver, attribute, context transitions | Yes | MCI-specific format; may need parsing for non-MCI models |
| Class label | String | True (safe), Identity Injection, Replay Injection | Yes | Same 10+1 taxonomy as MCIP-Bench |

### Class Distribution

| Category | Count | % of Total |
|---|---|---|
| True (safe) | 1,791 | 12.9% |
| Identity Injection | 1,749 | 12.6% |
| Function Overlapping | 1,395 | 10.1% |
| Function Injection | 1,382 | 10.0% |
| Data Injection | 1,361 | 9.8% |
| Excessive Privileges Overlapping | 1,401 | 10.1% |
| Function Dependency Injection | 1,372 | 9.9% |
| Replay Injection | 1,371 | 9.9% |
| Wrong Parameter Intent Injection | 664 | 4.8% |
| Ignore Purpose Intent Injection | 718 | 5.2% |
| Causal Dependency Injection | 626 | 4.5% |

## Proposed Risk Dimensions

### Risk Type Severity Weighting
- **Feeding columns:** Class label, class distribution counts
- **Proposed scale:** 1-10 severity per risk type, informed by both impact and real-world frequency
- **Derivation:** The imbalanced class distribution is informative — the three smallest classes (Wrong Parameter: 664, Ignore Purpose: 718, Causal Dependency: 626) could represent either rarer or harder-to-synthesize attacks. For risk scoring, weight by two factors: (1) estimated real-world impact if exploited, and (2) inverse of detection difficulty. Classes with fewer training samples are harder to detect, so they deserve higher risk scores when encountered.

### Training Data Coverage
- **Feeding columns:** All 11 class counts
- **Proposed scale:** Binary per class — sufficient (>1,000 samples) or under-represented (<1,000 samples)
- **Derivation:** 8 of 11 classes have 1,300+ samples (adequate for fine-tuning). Three classes — Wrong Parameter (664), Ignore Purpose (718), Causal Dependency (626) — are under-represented. Any risk scorer trained on this data should flag lower confidence on predictions for these three classes, which itself becomes a meta-risk signal.

### Classifier Confidence as Risk Signal
- **Feeding columns:** Model output logits/probabilities trained on this dataset
- **Proposed scale:** 1-10 inversely mapped from classifier confidence
- **Derivation:** Fine-tune a classifier (as done with Salesforce/Llama-xLAM-2-8b-fc-r to create MCIP Guardian). At inference time, low-confidence predictions (e.g., softmax probability < 0.6 for the top class) map to higher risk scores. A confident "safe" prediction = low risk; an uncertain prediction across multiple attack types = elevated risk even if the top prediction is "safe."

## Data Quality Notes
- The class imbalance is notable: the top 8 classes have 1,300-1,791 samples each, while the bottom 3 have 626-718. This 2-3x imbalance means a classifier will underperform on Wrong Parameter, Ignore Purpose, and Causal Dependency categories unless oversampling or class-weighted loss is applied.
- The MCI format with ~8 transmission steps is specific to the MCIP framework's contextual integrity model. If using this data for a different architecture, the transmission steps will need to be flattened or re-encoded into a more standard dialogue or feature format.
- This is the training counterpart to MCIP-Bench (which has 2,218 evaluation instances). Together they provide a train/eval split, but there is no explicit validation split documented — will need to carve one out.
- The data is synthesized, same caveat as MCIP-Bench: controlled and clean but may not capture real-world noise.

## Usefulness Verdict
This is the largest labeled MCP risk dataset currently available at 13,830 instances, and it is directly designed for training a risk classifier. The 11-class taxonomy is identical to MCIP-Bench, so training on this dataset and evaluating on MCIP-Bench gives a clean experimental setup. For a 1-10 risk scoring system, this dataset provides the supervised signal needed to train the core classifier that maps MCP interactions to risk categories.

The key practical value is that it was already used to fine-tune a working model (MCIP Guardian based on xLAM-2-8b-fc-r), so there is a proven recipe. The class imbalance is a real concern but a solvable one — standard techniques like focal loss or oversampling will help. The ~8 transmission steps per instance capture the sequential nature of MCP tool calls, which is important because risk often emerges across steps, not in a single action.
