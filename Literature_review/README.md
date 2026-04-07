# Literature Review — MCP Security

This folder contains the complete literature review for the MCP Security thesis project, which builds a **dynamic 1-10 risk scoring system** for evaluating AI agent access to Model Context Protocol (MCP) servers.

> **Threat model scope:** The **MCP server is the protected asset** (the victim). All reviewed benchmarks, datasets, and attack taxonomies are evaluated from the perspective of **client → server** attacks — how a malicious or compromised agent can harm the server. The inverse direction (malicious server attacking the agent) is noted where relevant but is **out of scope** for this project.

## Start Here

1. **excels/** — Begin with the Excel spreadsheets to see the full paper catalog, relevance scores, and comparison matrices
2. **pdf/Top_20/** — Read the 20 most important papers in ranked order
3. **pdf/** — Browse all papers by category and relevance score
4. **reviews/** — Read the generated analysis documents (datasets and benchmarks reviews)
5. **scripts/** — Automation tools used to organize papers and generate reviews

## Key Documents

| Document | Description |
|----------|-------------|
| [concepts_and_papers_summary.md](concepts_and_papers_summary.md) | Comprehensive educational document covering MCP concepts, attacks, defenses, risk scoring, datasets, and how it all connects to the thesis |
| [meeting_pitch_practical.md](meeting_pitch_practical.md) | Lab meeting pitch document for MCP-RSS with full implementation plan, architecture, code examples, and Lenovo justification |
| [thesis_research_plan.md](thesis_research_plan.md) | Detailed thesis research plan with methodology, phases, and literature references |
| [alternative_thesis_direction.md](alternative_thesis_direction.md) | Backup thesis direction (implicit poisoning detection via semantic drift) |
| [dimension_refinement_analysis.md](dimension_refinement_analysis.md) | Data-grounded refinement of risk dimensions: 11 benchmark dimensions → 8 final scoring dimensions with row counts, merge rationale, and 1-10 scale specs |
| [dimension_refinement_v2_agent_boundary.md](dimension_refinement_v2_agent_boundary.md) | **v2 refocus:** 8 ecosystem dimensions → 7 agent-boundary dimensions + 1 modifier, centered on "is THIS call by THIS agent safe RIGHT NOW?" |
| [final_report_datasets_dimensions_idea.md](final_report_datasets_dimensions_idea.md) | **Final report:** All 22 datasets with extractable columns, v1→v2 dimension transformation, scoring pipeline, and the MCP-RSS thesis idea |
| [mcp_server_attack_taxonomy_v2_agent_boundary.md](mcp_server_attack_taxonomy_v2_agent_boundary.md) | **v2 attack taxonomy:** Agent→server attacks with evidence tiers (CVEs vs DVMCP vs benchmark gaps). Refactored threat model centered on the server as protected asset |

## Folder Structure

| Folder | Description |
|--------|-------------|
| [excels/](excels/) | Excel spreadsheets tracking all papers, scores, and comparison matrices |
| [pdf/](pdf/) | Full paper PDFs organized by category (1-7) and relevance score |
| [reviews/](reviews/) | Generated review deliverables (datasets and benchmarks analysis) |
| [scripts/](scripts/) | Python scripts for paper organization and review generation |

## How Everything Relates

- **excels/** is the master tracking system — it lists every paper with metadata, relevance scores (1-10), and cross-reference matrices
- **pdf/** contains the actual papers, organized into 7 categories matching the Excel catalog. Each category has score subfolders (Score_04 to Score_10). The **Top_20/** folder duplicates the highest-ranked papers for quick access
- **reviews/** contain AI-generated analysis documents that synthesize findings from the papers, focusing on datasets and benchmarks
- **scripts/** contain the Python tools that automated the organization of PDFs into category/score folders and generated the review documents

## Paper Categories

| # | Category | Papers | Focus |
|---|----------|--------|-------|
| 1 | MCP Security | 19 | MCP-specific security frameworks, attacks, and defenses |
| 2 | MCP Protocol | 5 | MCP architecture, specifications, and ecosystem studies |
| 3 | Multi-Agent Trust | 7 | Trust frameworks, access control, and authorization |
| 4 | Prompt Injection | 14 | Prompt injection attacks, tool poisoning, and defenses |
| 5 | LLM Guardrails | 2 | LLM guardrail and safety rail systems |
| 6 | Risk Scoring | 8 | Risk scoring, anomaly detection, and safety benchmarks |
| 7 | Not Academic / Unmatched | 4 + 22 | MCP specs (text) and uncategorized papers |

## Scoring System

Papers are scored 1-10 based on relevance to the thesis topic (dynamic risk scoring for MCP agent access):
- **Score 10** — Directly addresses MCP risk scoring or is a foundational MCP security reference
- **Score 8-9** — Highly relevant MCP security, attack, or defense research
- **Score 6-7** — Relevant but broader in scope (general agent security, trust frameworks)
- **Score 4-5** — Background reading (general LLM trustworthiness, IoT anomaly detection)
