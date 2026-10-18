# MCP Security Documentation

Guides, standards, and references for working with the project.

## How to Navigate

| Section | Path | Audience | Description |
|---------|------|----------|-------------|
| **Project** | [project/](project/) | Everyone | Overview, architecture, roadmap |
| **Development** | [development/](development/) | Contributors | Setup, commands, workflows, contributing |
| **Standards** | [standards/](standards/) | Contributors | Style, layout, testing, security, patterns |
| **Claude** | [claude/](claude/) | Claude Code | AI collaboration conventions |
| **Guides** | [guides/](guides/) | Everyone | Step-by-step how-tos |
| **MCP tools** | [mcp-tools/](mcp-tools/) | Everyone | Server catalog, per-tool references, and [organizational profiles](mcp-tools/server-profiles.md) of the scanned servers |

## Quick Links

- New to the project? Start with [Project Overview](project/overview.md) then [Setup](development/setup.md)
- Visual map of the whole system (static + dynamic dataflow): [Architecture Diagrams](project/architecture-diagrams.md) (Mermaid) / [architecture.svg](project/architecture.svg) (Graphviz)
- Building the dynamic (runtime) scorer? See [Dynamic Scoring Design](project/dynamic-scoring-design.md)
- Reviewing the runtime enforcement gateway bundle? See [Gateway Bundle Review](project/gateway-bundle-review.md)
- How the gateway connects policy, static, dynamic, storage and remote agents — and the build order? See [Gateway Architecture](project/gateway-architecture.md)
- Designing the runtime layer on top of the severity matrix? See [Dynamic Layer Design](project/dynamic-layer-design.md)
- Just need the runtime arithmetic and a worked example? See [Dynamic Layer Formula](project/dynamic-layer-formula.md) — and [Dynamic Layer v2 Formula](project/dynamic-layer-formula-v2.md) for the implemented `cell x D` runtime, including the scan-time prompt verbatim
- Resolving *which asset* a runtime call touches (no LLM, no per-server config):
  [`src/mcp_security/binding/README.md`](../src/mcp_security/binding/README.md);
  measured in [v8](../reports/experiments/v8/README.md), explained with diagrams in
  [v8 METHOD.md](../reports/experiments/v8/METHOD.md)
- Which inputs reach which model call? See [LLM Inputs](project/llm-inputs.md)
- Want the state of both layers and why neither number is *accuracy* yet? See [What Exists Now, and the Evaluation Problem](project/evaluation-problem.md)
- Want the human-baseline study that would give the static scanner ground truth — with a live rating tool? See [Human Annotation Experiment](project/human-annotation-experiment.md)
- Need an *external* benchmark, or wondering how this compares to published work? See [External Benchmarks and Positioning](project/external-benchmarks-and-positioning.md)
- **Want to understand the runtime layer end to end — every stage, formula and constant, with diagrams and a worked example? Start here: [The Dynamic Layer, Explained](project/dynamic-layer-explained.md)**
- What the runtime layer can and cannot see, and the two dimensions it missed? See [Dynamic Layer Blind Spots](project/dynamic-layer-blind-spots.md)
- Which runtime context can a gateway use without reading tool inputs — by category, with evidence and log coverage? See [Dynamic Context Catalog](project/dynamic-context-catalog.md)
- Asking "we scored this 125 — is that right?" See [Evaluating the Risk Score](project/evaluating-the-risk-score.md) (measurement theory, case-control, what to report)
- Asking "does the runtime layer actually work?" See [Evaluating the Dynamic Layer](project/evaluating-the-dynamic-layer.md) (executable protocol: noise floor, matched pairs, minimum detectable deviation, ablation, baseline poisoning)
- Writing this up for a venue? See [Claims and Defence](project/dynamic-layer-claims-and-defence.md) (what survives review, what a reviewer attacks first)
- Research foundation? See [Annotated Bibliography](project/annotated-bibliography-mcp-security.md) (30 papers, also available as [PDF](project/annotated-bibliography-mcp-security.pdf))
- Adding code? Read [Style and Naming](standards/style-and-naming.md) and [Testing Guide](standards/testing-guide.md)
- Adding a new module? Follow [Adding a Module](guides/adding-a-module.md)
- Want the experiments behind the runtime layer, with real run output? See [Dynamic Layer Experiments](guides/dynamic-layer-experiments.md)

## Conventions

- All docs are Markdown files, one topic per file
- Concise — prefer short sections over long walls of text
- Links are relative
