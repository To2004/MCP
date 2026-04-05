# MCP Server Database

## Source
- **Paper:** Mind Your Server: A Systematic Study of Parasitic Toolchain Attacks on the MCP Ecosystem — Zhao et al.
- **Link:** https://arxiv.org/abs/2509.06572
- **Year:** 2025

## Format & Size
- **Total samples:** 1,360 servers containing 12,230 tools, collected from 3 registry sources
- **Format:** Server metadata with tool-level risk classification (EIT/PAT/NAT taxonomy)
- **Availability:** Data derived from Pulse MCP, MCP Market, and Awesome MCP Servers (public registries)

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Server source | Categorical | Pulse MCP, MCP Market, Awesome MCP Servers | Yes | 784 / 310 / 266 split across sources |
| Tool name/ID | String | (tool identifiers per server) | Yes | 12,230 tools total |
| Risk category | Categorical | EIT, PAT, NAT | Yes | Core taxonomy — directly maps to risk dimensions |
| EIT flag | Boolean | True/False | Yes | External Ingestion Tools — 472 tools across 128 servers |
| PAT flag | Boolean | True/False | Yes | Privacy Access Tools — 391 tools across 155 servers |
| NAT flag | Boolean | True/False | Yes | Network Access Tools — 180 tools across 89 servers |
| Exploit risk flag | Boolean | True/False | Yes | 1,062 tools (8.7%) flagged as exploitable |
| Exploitable combo flag | Boolean | True/False | Yes | 27.2% of servers expose exploitable tool combinations |
| Parasitic toolchain membership | Boolean/Link | Toolchain ID | Partially | 90% success rate across 10 constructed toolchains |

## Proposed Risk Dimensions

### Tool Capability Risk (EIT/PAT/NAT Classification)
- **Feeding columns:** EIT flag, PAT flag, NAT flag
- **Proposed scale:** 1-10 where tools with no risky category = 1-2, single category = 3-5, multi-category overlap = 6-8, all three = 9-10
- **Derivation:** Count how many of the three risk categories a tool falls into. A tool that is simultaneously EIT + PAT + NAT presents compound risk. Weight PAT highest (privacy data exfiltration is hardest to reverse), then EIT (external data ingestion is the primary attack entry point), then NAT (network access enables lateral movement). Single-category tools score 3-5 depending on which category; each additional category adds 2-3 points.

### Server-Level Exposure Risk
- **Feeding columns:** Number of tools per server, number of exploitable tools, exploitable combo flag
- **Proposed scale:** 1-10 based on the fraction of a server's tools that carry exploit risk and whether dangerous combinations exist
- **Derivation:** Base score = (exploitable tools / total tools) × 6 + 1. If the server has exploitable tool combinations (the 27.2% group), add +2. Cap at 10. A server with 0 exploitable tools = 1. A server where most tools are exploitable AND combinations exist = 9-10.

### Toolchain Propagation Risk
- **Feeding columns:** Parasitic toolchain membership, toolchain attack success rate
- **Proposed scale:** 1-10 where isolated tools = 1-3, tools participating in one chain = 4-6, tools in multiple chains or high-success chains = 7-10
- **Derivation:** The 90% success rate across 10 toolchains sets a high baseline. If a tool participates in a known parasitic chain pattern, it starts at 5. Multiply by the chain's demonstrated success rate (e.g., 90% → ×0.9 → effective score ~8). Tools not in any chain pattern = 2.

## Data Quality Notes
- The 1,360-server corpus is a snapshot of three registries at one point in time — registries change frequently, so numbers will drift.
- The EIT/PAT/NAT categories are defined by the authors' taxonomy, not an industry standard. Some tools may be ambiguous or span categories in ways not captured.
- The 8.7% exploit rate is based on the authors' analysis methodology; different threat models could yield different numbers.
- No per-tool severity scores are provided — just binary risk category membership. Granular scoring must be derived.
- The 10 parasitic toolchains are hand-constructed proof-of-concept; real-world chain diversity is likely much larger.

## Usefulness Verdict
This dataset is highly valuable as a **base-rate calibrator** for MCP risk scoring. The EIT/PAT/NAT taxonomy gives a concrete, three-axis classification of tool capabilities that maps directly onto risk dimensions for a multi-label scorer. The 8.7% exploit rate and 27.2% server exposure rate provide empirical anchors — any scoring system should produce distributions roughly consistent with these prevalence numbers when applied to general MCP server populations.

The parasitic toolchain data is especially useful for the **multi-tool aggregation** problem: how to score the risk of a server that hosts multiple tools where the combination is more dangerous than any single tool. The 90% success rate on toolchain attacks means that compositional risk is real and measurable, not hypothetical. For a 1-10 scoring system, this dataset provides the taxonomy backbone (what to score), the base rates (how to calibrate), and the multi-tool patterns (how to aggregate).
