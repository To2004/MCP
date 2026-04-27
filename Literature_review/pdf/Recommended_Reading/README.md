# Recommended Reading

11 papers, ordered from zero background to full project context.
Read them in sequence — each layer builds on the one before.

---

## Layer 1 — What is MCP?

Start here if you have never heard of the Model Context Protocol.

| Paper | Why read it |
|-------|-------------|
| **A Survey of the Model Context Protocol: Standardizing Context to Enhance LLMs** | Clearest introduction to what MCP is, how it works, and why it matters. Read this first. |
| **MCP Landscape, Security Threats, and Future Research Directions** | Big-picture view of the MCP ecosystem and where security fits in. |

---

## Layer 2 — Why MCP is dangerous

Now that you know what MCP does, learn why it creates new attack surfaces.

| Paper | Why read it |
|-------|-------------|
| **MCP Safety Audit: LLMs with the MCP Allow Major Security Exploits** | Hands-on audit showing real exploits — a wake-up call. Short and impactful. |
| **When MCP Servers Attack: Taxonomy, Feasibility, and Mitigation** | Systematic taxonomy of threat classes. Good reference for threat modeling. |
| **Parasites in the Toolchain: Large-Scale Analysis of Attacks on the MCP Ecosystem** | Large-scale empirical study of real MCP servers in the wild. |

---

## Layer 3 — How attacks actually work

Understand the mechanics before designing defenses.

| Paper | Why read it |
|-------|-------------|
| **Beyond the Protocol: Unveiling Attack Vectors in the MCP Ecosystem** | Catalogs attack vectors at the protocol, tool, and agent layer. |
| **MCP Threat Modeling and Analyzing Vulnerabilities to Prompt Injection with Tool Poisoning** | Detailed threat model covering tool poisoning and prompt injection chains. |

---

## Layer 4 — Risk scoring and the project approach

This is the core of what this project builds. Read these to understand the design space.

| Paper | Why read it |
|-------|-------------|
| **TRiSM for Agentic AI: Trust, Risk, and Security Management** | Comprehensive framework for thinking about risk in multi-agent systems. Sets vocabulary. |
| **R-Judge: Benchmarking Safety Risk Awareness for LLM Agents** | Shows how to score agent actions for safety risk — closest to the static scoring approach here. |
| **Progent: Programmable Privilege Control for LLM Agents** | Least-privilege policy enforcement at the agent level — the defense-side counterpart to scoring. |

---

## Layer 5 — Putting defenses in place

| Paper | Why read it |
|-------|-------------|
| **Securing the MCP: Risks, Controls, and Governance** | Practical controls and governance model. Answers "where do you actually put the defenses?" |

---

## Project context

This project scores incoming agent requests **before** an MCP server executes them.
- **Static scoring** — at design time, based on tool properties (capability, scope, reversibility)
- **Dynamic scoring** — at runtime, based on the specific request and its inputs
- **Threat direction** — agents are the threat source; MCP servers are the protected asset

The papers in Layers 4–5 directly inform the scoring rubric and policy enforcement design.
All source PDFs live in the parent `pdf/` folder, organized by category and type.
