# ASSEBench (from AgentAuditor)

## Source
- **Paper:** AgentAuditor: Human-Level Safety and Security Evaluation for LLM Agents (Luo et al., 2025a)
- **Authors:** Hanjun Luo, Shenyu Dai, Chiming Ni, Xinfeng Li, Guibin Zhang, Kun Wang, Tongliang Liu, Hanan Salam
- **Link:** https://github.com/Astarojth/AgentAuditor
- **arXiv:** 2506.00641
- **Year:** 2025

## Format & Size
- **Total samples:** 2,293 meticulously annotated interaction records
- **Application scenarios:** 29
- **Risk types:** 15 distinct risk categories
- **Judgment standards:** dual — "Strict" and "Lenient" for handling ambiguous risk situations
- **Annotation level:** **Trajectory-level** (per ToolSafe's comparison table in 26_ts_bench.md)
- **Monitored behavior:** tool calls
- **Pattern coverage (per ToolSafe):** MUR ✓, PI ✓, HT —, BTRA ✓
- **Availability:** GitHub (`Astarojth/AgentAuditor`) — open source

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Interaction record ID | String | ASSE-0412 | Yes | Links to scenario |
| Application scenario | Categorical (29) | e-commerce, healthcare, finance, ... | Yes | Wide domain coverage |
| Risk type | Categorical (15) | safety / security sub-categories | Yes | Fine-grained taxonomy |
| Trajectory | Structured | Sequence of (action, observation) pairs | Yes | Full interaction log |
| Strict label | Categorical | safe / risky / unsafe | Yes | Conservative judgment |
| Lenient label | Categorical | safe / risky / unsafe | Yes | Permissive judgment for ambiguous cases |
| Ground truth rationale | Text | Human-written explanation | Partial | Supports interpretability training |

## Proposed Risk Dimensions

### Strict/Lenient Dual Labeling for Gate/Throttle/Deny Calibration
- **Feeding columns:** Strict label, Lenient label
- **Proposed scale:** 1-10 with the gap between strict and lenient labels marking the
  "throttle" band
- **Derivation:** Actions labeled unsafe under both strict *and* lenient judgment are
  unambiguous deny (9-10). Actions labeled safe under both are unambiguous allow (1-3).
  Actions where strict=unsafe but lenient=safe are exactly the ambiguous middle band
  (4-6) where the project's scorer should throttle or challenge rather than deny. This
  maps cleanly onto the server-defense gate/throttle/deny tiering without requiring a
  new annotation pass.

### Scenario-Context Multiplier
- **Feeding columns:** application scenario (29)
- **Proposed scale:** 1-10 per scenario, reflecting the sensitivity of that domain
- **Derivation:** The 29 scenarios span domains of wildly different sensitivity
  (healthcare ≠ entertainment). Each scenario maps to a static multiplier applied to
  the request's per-action severity. Broader than AgentDojo's 4 suites and more
  granular than ASB's 10 scenarios.

### Risk-Type Multi-Label Vector
- **Feeding columns:** risk type (15)
- **Proposed scale:** 1-10 per category, summed or max-pooled per request
- **Derivation:** 15 categories is finer than Agent-SafetyBench's 8 or R-Judge's 10.
  Use as a multi-label target for the Agent Action Severity dimension.

## Data Quality Notes
- The dual Strict/Lenient labeling is rare among agent safety benchmarks and is the
  most directly useful feature for calibrating a graduated 1-10 scorer — most
  benchmarks only offer single-label ground truth.
- AgentAuditor itself is a **training-free memory-augmented LLM judge**, meaning
  ASSEBench's labels are produced with human annotation (not solely LLM-generated),
  giving higher label quality than synthetic benchmarks.
- Trajectory-level (not step-level) annotation is the main limitation for pre-execution
  step scoring — each label covers a whole interaction, not individual calls. ToolSafe
  uses ASSEBench as a coverage reference, not as a step-level training source.
- Not MCP-specific. 29 scenarios are general agent domains.
- Added in 2025, so downstream defense baselines are sparse.

## Usefulness Verdict
ASSEBench is the benchmark to cite when the project needs to demonstrate **calibration
of the throttle-band**. Its dual strict/lenient labels give a clean signal for which
requests are unambiguously dangerous, which are unambiguously safe, and which sit in
the uncertain middle — the exact population the project's dynamic scorer most needs to
get right. The 15 risk types and 29 scenarios provide broader domain coverage than most
alternatives, but because annotation is trajectory-level rather than step-level, it is
not a direct training source for pre-execution step classifiers. Use it for (a)
evaluation of calibration, (b) the risk-type taxonomy, and (c) scenario multipliers —
pair with step-level sources like TS-Bench (26) and ShieldAgent-Bench (29) for the
actual per-step training data.
