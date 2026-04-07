# MCPShield

## Source
- **Paper:** MCPShield: A Security Cognition Layer for Adaptive Trust Calibration in Model Context Protocol Agents
- **Link:** https://arxiv.org/abs/2602.14281
- **Year:** 2026

## Format & Size
- **Total samples:** The arXiv abstract confirms evaluation on **6 novel MCP-based attack scenarios** across **6 widely used agentic LLMs**
- **Format:** Defense benchmark spanning the MCP tool invocation lifecycle: pre-invocation probing, runtime event monitoring, and post-invocation historical reasoning
- **Availability:** Public arXiv paper. At verification time, the arXiv page exposed the paper PDF/HTML/TeX, but did **not** clearly expose a public dataset or code artifact link on the abstract page

## Data Structure

The exact released benchmark schema is **not yet verified** from a public artifact. The fields below are inferred from the paper abstract and the benchmark setup described there.

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Attack scenario ID | Categorical | 1-6 | Partially | The abstract confirms 6 novel MCP-based attack scenarios, but not their exact names |
| Target LLM agent | Categorical | 6 widely used agentic LLMs | Partially | Good for model-aware defense evaluation |
| Tool metadata / manifest | Structured text | Name, description, schema | Partially | Pre-invocation probing appears to analyze metadata-to-behavior alignment |
| Runtime event trace | Sequence / log | Observed side effects, policy violations | Partially | Runtime cognition is a key part of the framework |
| Historical invocation trace | Temporal sequence | Per-server interaction history | Partially | Used for post-invocation reasoning and drift detection |
| Benign vs. malicious outcome | Boolean / score | Accept / reject / suspicious | Partially | Inferred from the defense setting rather than directly confirmed as a released label |

## Proposed Risk Dimensions

### Metadata-Behavior Misalignment
- **Feeding columns:** Tool metadata, probe results, scenario label
- **Proposed scale:** 1-10 based on how strongly a server's declared behavior diverges from observed behavior
- **Derivation:** MCPShield is explicitly designed around the idea that third-party server metadata can look benign while actual behavior is risky. A server whose probe outputs strongly conflict with declared descriptions should score 8-10.

### Runtime Side-Effect Risk
- **Feeding columns:** Runtime event traces, policy violations, execution outcomes
- **Proposed scale:** 1-10 where benign side effects score low and policy-violating side effects score high
- **Derivation:** The framework constrains execution and reasons over observed events. This maps naturally to a server-defense dimension: the more dangerous the execution trace, the higher the score.

### Temporal Drift Risk
- **Feeding columns:** Historical traces, repeated invocation windows
- **Proposed scale:** 1-10 based on whether the server becomes more suspicious over time
- **Derivation:** MCPShield reasons over historical traces after invocation. That makes it unusually relevant for session-aware or server-reputation-aware risk scoring.

## Data Quality Notes
- The paper is very relevant, but the **public artifact availability is weaker than the benchmark papers already in this folder** because the arXiv abstract page did not clearly expose a dataset or repository at verification time.
- The exact sample count is not given on the abstract page beyond the 6-scenario x 6-model evaluation framing.
- This resource is strongest as a **defense evaluation benchmark design** rather than a ready-made training corpus.
- Because the benchmark appears lifecycle-aware, it is especially useful for validating your v3 dimensions around compromise indication, action severity, and temporal escalation.

## Usefulness Verdict
MCPShield is one of the strongest **new internet-sourced additions** for your project because it is explicitly about defending agents against malicious MCP servers across the full invocation lifecycle. For your server-defense thesis framing, that matters because a malicious or deceptive server is precisely what can turn a benign-looking session into a dangerous one.

It is not yet as plug-and-play as MCP-AttackBench or MCPSecBench for training a scorer, because the public abstract page does not confirm a released artifact schema. But it is highly valuable as a **benchmark design reference** and as evidence that strong MCP defenses increasingly depend on combining metadata checks, runtime observation, and temporal reasoning rather than relying on one-shot prompt inspection.
