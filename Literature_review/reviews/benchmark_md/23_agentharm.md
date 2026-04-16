# AgentHarm

## Source
- **Paper:** AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents (Andriushchenko et al., 2024)
- **Authors:** Maksym Andriushchenko, Alexandra Souly, Mateusz Dziemian, Derek Duenas, Maxwell Lin, Justin Wang, Dan Hendrycks, Andy Zou, Zico Kolter, Matt Fredrikson, Eric Winsor, Jerome Wynne, Yarin Gal, Xander Davies
- **Institution:** Gray Swan AI + UK AI Safety Institute
- **Link:** https://huggingface.co/datasets/ai-safety-institute/AgentHarm
- **arXiv:** 2410.09024
- **Year:** 2024

## Format & Size
- **Total samples:** 110 explicit malicious tasks, augmented to 440 harmful variants; 176 harmful + 176 benign base prompts in the paired release
- **Tools:** 104 distinct simulated tools across domains
- **Harm categories:** 11 (including fraud, cybercrime, harassment, and 8 others)
- **Format:** Natural-language task instructions paired with a simulated toolset; binary safety outcome (complied / refused)
- **Availability:** HuggingFace dataset `ai-safety-institute/AgentHarm`, gated by click-through use terms

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Task instruction | Text | "Use the email tool to send a phishing message to..." | Yes | User-side prompt |
| Harm category | Categorical (11) | fraud, cybercrime, harassment, ... | Yes | Coarse taxonomy only |
| Tool set | Structured | 104 tools across domains | Yes | Maps to agent's available actions |
| Augmentation flag | Categorical | original / jailbreak / detailed / ... | Yes | 4x expansion per base task |
| Ground-truth label | Binary | harmful / benign | Yes | Single pair per instruction |
| Score (ASR) | Float (%) | Attack Success Rate | Yes | Primary metric |
| Refusal rate | Float (%) | Rate agent refuses malicious tasks | Yes | Inverse metric |

## Proposed Risk Dimensions

### Malicious User Request Severity (Deny-Always Floor)
- **Feeding columns:** harm category, task instruction
- **Proposed scale:** 1-10 with the 11 categories banded by real-world harm potential
  (e.g., cybercrime=10, fraud=9, harassment=7). Because AgentHarm's own label is binary,
  the dimension is derived from the category, then applied to any incoming request
  matching the category signature.
- **Derivation:** AgentHarm establishes the "floor" — the set of requests that every
  safety-aligned scorer must block. If the project's scorer achieves less than ~95%
  refusal rate on AgentHarm, it is under-scoring obvious malicious requests. Treat as
  a pass/fail calibration check, not as training data for graduated middle bands.

### Refusal-Rate Baseline Anchor
- **Feeding columns:** model-level refusal rate on AgentHarm
- **Proposed scale:** Not a per-sample score — a scorer-wide calibration metric. Compare
  the project's refusal rate on AgentHarm against published baselines (Claude, GPT-4o,
  Llama-Guard, etc.).
- **Derivation:** Use AgentHarm's refusal rates as published reference points. A scorer
  that refuses less than the weakest published baseline is measurably worse than doing
  nothing; one that matches or exceeds the strongest has reached the "deny-always" ceiling.

## Data Quality Notes
- **Binary labels only.** AgentHarm reports harmfulness as yes/no, so it doesn't support
  graduated scoring directly. Use it for the top tier (deny-always) of the project's
  scoring system, not for calibrating the middle bands.
- Previously marked "skipped" in `benchmarks_review.md` for this binary-only reason;
  added here by explicit request because it's one of the four reference datasets cited
  by ToolSafe (see `26_ts_bench.md`) for step-level labeling, and because its
  `AgentHarm-Traj` split (731 trajectories, 206/315/210 split) does have three-way
  labels after ToolSafe's annotation layer.
- The 4x augmentation (jailbreak / detailed / original variants) provides robustness
  testing for refusal consistency under rephrasing.
- Small size (110 core tasks) limits training utility; use as an evaluation benchmark only.
- Gated by HuggingFace terms-of-use — requires clicking through for access.

## Usefulness Verdict
AgentHarm's value is as a **calibration floor for the deny-always tier** of a graduated
scoring system. It answers one question well: does the scorer reliably refuse obviously
malicious requests? If the answer isn't near 100%, no amount of middle-band sophistication
matters. Use it as a pass/fail gate during evaluation rather than as training data. For
this project specifically, AgentHarm is most useful when paired with ToolSafe's
`AgentHarm-Traj` annotation layer (see `26_ts_bench.md`) — treat AgentHarm as the raw
attack source and TS-Bench as the step-level-labeled derivative. Not MCP-specific; use as
supporting evidence, not core MCP data.
