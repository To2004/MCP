# Literature Review — MCP Security

This folder contains the complete literature review for the MCP Security thesis project, which builds a **dynamic 1-10 risk scoring system** for evaluating AI agent access to Model Context Protocol (MCP) servers.

## Start Here

1. **Excels/** — Begin with the Excel spreadsheets to see the full paper catalog, relevance scores, and comparison matrices
2. **PDF/Top_20/** — Read the 20 most important papers in ranked order
3. **PDF/** — Browse all papers by category and relevance score
4. **reviews/** — Read the generated analysis documents (datasets and benchmarks reviews)
5. **scripts/** — Automation tools used to organize papers and generate reviews

## Key Documents

| Document | Description |
|----------|-------------|
| [concepts_and_papers_summary.md](concepts_and_papers_summary.md) | Comprehensive educational document covering MCP concepts, attacks, defenses, risk scoring, datasets, and how it all connects to the thesis |
| [meeting_pitch_practical.md](meeting_pitch_practical.md) | Lab meeting pitch document for MCP-RSS with full implementation plan, architecture, code examples, and Lenovo justification |
| [thesis_research_plan.md](thesis_research_plan.md) | Detailed thesis research plan with methodology, phases, and literature references |
| [alternative_thesis_direction.md](alternative_thesis_direction.md) | Backup thesis direction (implicit poisoning detection via semantic drift) |

## Folder Structure

| Folder | Description |
|--------|-------------|
| [Excels/](Excels/) | Excel spreadsheets tracking all papers, scores, and comparison matrices |
| [PDF/](PDF/) | Full paper PDFs organized by category (1-7) and relevance score |
| [reviews/](reviews/) | Generated review deliverables (datasets and benchmarks analysis) |
| [scripts/](scripts/) | Python scripts for paper organization and review generation |

## How Everything Relates

- **Excels** are the master tracking system — they list every paper with metadata, relevance scores (1-10), and cross-reference matrices
- **PDFs** are the actual papers, organized into 7 categories matching the Excel catalog. Each category has score subfolders (Score_04 to Score_10). The **Top_20/** folder duplicates the highest-ranked papers for quick access
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
