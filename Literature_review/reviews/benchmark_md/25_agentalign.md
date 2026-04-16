# AgentAlign

## Source
- **Paper:** AgentAlign: Navigating Safety Alignment in the Shift from Informative to Agentic Large Language Models (Zhang et al., 2025)
- **Authors:** Jinchuan Zhang, Lu Yin, Yan Zhou, Songlin Hu
- **Institution:** Institute of Information Engineering, Chinese Academy of Sciences
- **Link:** Dataset and code open-sourced per abstract (exact repo URL not on arXiv page — check supplementary)
- **arXiv:** 2505.23020
- **Year:** 2025

## Format & Size
- **Harmful instructions:** 4,956
- **Legitimate (benign) instructions:** 9,783
- **Total:** ~14,739 instructions — largest training-oriented split among the four
  ToolSafe-referenced datasets
- **Format:** Multi-step agent instructions synthesized via "abstract behavior chains" —
  structured action plans decomposed into tool-call sequences
- **Availability:** Open-sourced (dataset + code per paper abstract)
- **Reported alignment gain:** 35.8% to 79.5% improvement on AgentHarm safety metrics
  after fine-tuning on AgentAlign

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Instruction type | Categorical (harmful / benign) | "delete all files matching *.key" | Yes | ~1:2 harmful:benign ratio |
| Abstract behavior chain | Structured list | [auth → list → filter → delete → exfil] | Yes | Pre-decomposed action plan |
| Target tools | Categorical | tool set per step | Yes | Supports static severity lookup |
| Step-level safety label | Categorical | safe / unsafe per step | Yes | Training signal for pre-execution classifiers |
| Benign variant pair | Structured | Matched legitimate instruction | Yes | Supports paired-contrastive training |

## Proposed Risk Dimensions

### Behavior-Chain Sequence Risk
- **Feeding columns:** abstract behavior chain
- **Proposed scale:** 1-10 where risk scales with chain length × per-step severity
- **Derivation:** AgentAlign's contribution is showing that multi-step action sequences
  encode risk that any single step doesn't. A 3-step chain "auth → read-sensitive → exfil"
  is higher risk than its three steps scored independently. This is the cleanest published
  training source for a sequence-aware Cross-Tool Escalation dimension in the project's v3.

### Paired Contrastive Calibration
- **Feeding columns:** harmful/benign instruction pair
- **Proposed scale:** 1-10 where a well-calibrated scorer gives a *wide gap* between
  paired instructions
- **Derivation:** Each harmful instruction has a matched benign variant (same tool set,
  same surface behavior, different intent). A scorer that gives similar scores to both is
  mis-calibrated. Use the paired gap as a calibration metric during training: larger gap =
  better discrimination between "same tools, different intent" cases — exactly the
  BTRA-style dynamic risk the project's dynamic mode needs to distinguish.

## Data Quality Notes
- **Largest training split** among ToolSafe's four references — roughly 10x AgentHarm's
  size and the only one with enough volume to fine-tune a guardrail classifier directly.
- AgentAlign's own reported improvement range (35.8% to 79.5% safety gain on AgentHarm
  benchmarks) suggests the training data is effective for alignment fine-tuning, not
  just evaluation.
- Synthetic generation via abstract behavior chains means attacks are *systematic*
  rather than hand-crafted — strengths are coverage and controllability, weaknesses are
  realism compared to AgentDojo's real-trajectory attacks.
- **Not MCP-specific.** Tools are general agent tools; chains are not structured around
  MCP-specific surfaces.
- Paper is recent (May 2025), so downstream defense papers have not yet adopted it
  broadly — baselines will be sparse.

## Usefulness Verdict
AgentAlign is the **training-data asset** of the four ToolSafe-referenced datasets. Its
value is volume and structure, not evaluation: the ~15K instructions with paired
benign/harmful variants and pre-decomposed action chains are directly useful for training
a step-level risk classifier, which is exactly what the project's scorer needs. The
abstract behavior chain format is especially aligned with the Cross-Tool Escalation
dimension in v3 — labeled sequences can be fed in directly without having to recover the
action graph from raw trajectories. The main caveat is synthetic-vs-real: AgentDojo and
AgentHarm capture organic attack phrasings; AgentAlign captures systematic variants. Use
them together — AgentAlign for training volume, AgentDojo and AgentHarm for evaluation
realism.
