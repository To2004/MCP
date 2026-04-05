# Meta Tool-Use Agentic PI Benchmark

## Source
- **Paper:** LlamaFirewall: An Open Source Guardrail System for Building Secure AI Agents (Chennabasappa et al., 2025)
- **Link:** https://huggingface.co/datasets/facebook/llamafirewall-alignmentcheck-evals
- **Year:** 2025

## Format & Size
- **Total samples:** 600 scenarios (300 benign, 300 malicious) — perfectly balanced
- **Format:** Tool-use agentic interaction traces simulating smartphone app interactions across 3 domains
- **Availability:** HuggingFace (https://huggingface.co/datasets/facebook/llamafirewall-alignmentcheck-evals)

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Interaction trace | Structured JSON/text | Multi-step tool-use conversation between agent and simulated apps | Yes | Full agentic traces, not just single prompts |
| Label | Binary | Benign / Malicious | Yes | Clean 50/50 split — no class imbalance to worry about |
| Injection technique | Categorical (7 types) | 7 distinct prompt injection methods | Yes | Fine-grained attack methodology labels |
| Threat category | Categorical (8 types) | 8 threat categories | Yes | Richer than binary — enables multi-label classification |
| Domain | Categorical (3 types) | Travel, Info-retrieval, Productivity | Yes | Context for domain-specific risk calibration |
| App simulation | Structured | Smartphone app interactions (tool calls, responses) | Yes | Realistic tool-use patterns, not synthetic templates |

## Proposed Risk Dimensions

### Threat Category Classification
- **Feeding columns:** Threat category (8 categories)
- **Proposed scale:** 1-10 where each of the 8 threat categories maps to a severity level based on potential impact
- **Derivation:** With 8 threat categories, this is one of the richer taxonomies available. Map each category to a severity score based on: (1) reversibility of the harm, (2) scope of impact (single user vs. system-wide), and (3) detectability. Categories involving data exfiltration or unauthorized actions score 7-10. Categories involving information leakage or minor policy violations score 3-6. The 300 malicious samples distributed across 8 categories gives ~37 samples per category on average — enough to evaluate per-category detection performance but tight for training.

### Input Manipulation Sophistication
- **Feeding columns:** Injection technique (7 types)
- **Proposed scale:** 1-10 where simple/direct injections = 2-4, moderately obfuscated = 5-7, and advanced evasion techniques = 8-10
- **Derivation:** The 7 injection techniques represent different levels of attacker sophistication. Rank them by evasion difficulty: straightforward instruction injections are easy to detect (score 2-3), while techniques that exploit tool-response formatting or multi-step reasoning chains are harder to catch (score 7-9). At runtime, if an input matches the signature of a high-sophistication technique, the risk score increases. The 7 techniques also serve as a coverage checklist — a defense that handles all 7 is more robust than one that handles 3.

### Detection Calibration (True/False Positive Rates)
- **Feeding columns:** Label (benign/malicious), balanced split
- **Proposed scale:** 1-10 derived from the confidence margin between benign and malicious classification
- **Derivation:** The 300/300 balanced split is specifically designed for calibrating detection thresholds without class-imbalance distortion. Use the benign set to establish baseline "normal" behavior signatures and the malicious set to establish attack signatures. The risk score at inference time is derived from how far a new input falls from the benign centroid vs. the malicious centroid. Inputs deep in the benign cluster = 1-2. Inputs on the decision boundary = 5. Inputs deep in the malicious cluster = 8-10. The balanced split means precision and recall are equally weighted in calibration.

### Domain-Contextual Risk
- **Feeding columns:** Domain (Travel, Info-retrieval, Productivity)
- **Proposed scale:** 1-10 adjusted per domain based on the sensitivity of typical operations
- **Derivation:** Similar to AgentDojo's domain segmentation but with different domains. Productivity apps often handle documents and email (moderate sensitivity, baseline 5). Info-retrieval apps access search and knowledge bases (lower sensitivity, baseline 3). Travel apps handle bookings and personal itinerary data (moderate sensitivity, baseline 4-5). The domain label modulates the base risk score from other dimensions — a malicious injection in a productivity context is more concerning than the same injection in an info-retrieval context because productivity tools can take actions (send email, edit documents) rather than just read.

## Data Quality Notes
- The 600-sample size is small — this is an evaluation benchmark, not a training set. The balanced split is great for threshold calibration but the per-category sample counts (especially across 8 threat categories and 7 injection techniques) get thin when you cross-tabulate.
- The smartphone app simulation approach is distinctive and realistic, but it means the data is tied to a specific interaction paradigm. MCP server interactions may differ in structure from simulated phone apps, so some adaptation may be needed.
- This benchmark was designed to evaluate LlamaFirewall's PromptGuard + AlignmentCheck pipeline specifically. The scenarios may be biased toward attack types that LlamaFirewall is designed to detect, potentially underrepresenting attack types it was not optimized for.
- Available on HuggingFace, which means easy programmatic access and integration. No need to clone repos or parse custom formats.
- The 7 injection techniques and 8 threat categories are not fully cross-referenced in the public documentation — it is not clear whether every injection technique appears in every threat category or if there is a sparse coverage matrix.

## Usefulness Verdict
The Meta Tool-Use benchmark is the best-calibrated dataset in the survey for setting detection thresholds. The perfect 300/300 benign/malicious split means you can compute precision, recall, F1, and ROC curves without any class-weighting gymnastics. For a 1-10 risk scoring system, this is where you calibrate: what score threshold separates "probably benign" from "probably malicious" with acceptable false positive rates?

The combination of 8 threat categories and 7 injection techniques gives a 56-cell matrix of attack characteristics, which is rich enough for multi-label scoring. The practical limitation is size — 600 samples is thin, and once you slice by category and technique the per-cell counts drop to single digits. Use this benchmark for calibration and evaluation, not for training. It pairs well with larger training sets like MCIP Guardian (13,830 samples) where you train the model, and use this benchmark's balanced split to tune the decision boundaries.
