# Alternative Thesis Direction — Implicit Poisoning Detection via Semantic Drift Analysis

> This is a secondary direction discovered during research planning.
> Only pursue this if the main plan (MCP-RSS dynamic scoring) proves infeasible
> or if this direction feels more compelling after Phase 1.
> Created: 2026-03-29

---

## The Opportunity

MCP-ITP (Li et al., 2026) demonstrated that implicit tool poisoning achieves **84.2% attack success rate** with only **0.3% detection rate** by existing defenses. This is arguably the single biggest open problem in MCP security — attacks that don't look malicious at the word level but steer agent behavior through subtle semantic manipulation.

Every existing defense (MCP-Guard's pattern matching, MCPShield's probing, mcp-scan's static analysis) fundamentally fails against implicit poisoning because these attacks use individually innocuous words. The detection gap is enormous: 84.2% attack success vs 0.3% detection.

## What's Different Here

Instead of building a risk scorer (the main plan), this direction would build a **semantic drift detector** — a system that detects when an MCP tool description has been subtly modified to influence agent behavior, even when no individual word or phrase looks malicious.

The approach:
1. Build a corpus of "known good" tool descriptions from the MCP ecosystem (67K+ servers provide ample data)
2. For each tool category, learn the expected semantic distribution of descriptions
3. When a new tool description is encountered, measure its **semantic distance** from the expected distribution
4. Flag descriptions that are semantically close enough to look normal but have subtle directional drift toward influencing agent behavior

This is inspired by MindGuard's Total Attention Energy (TAE) approach (which looks at internal LLM attention patterns to detect metadata poisoning) but operates on the description text itself rather than requiring access to model internals.

## Why It's Worth Considering

- The 0.3% detection rate means the bar is extremely low — any meaningful improvement would be significant
- The problem is well-scoped and focused (unlike the broad risk scoring system)
- The datasets exist: MCPTox's 548 implicit poisoning cases + MCP-ITP's framework-generated attacks
- It addresses the single most dangerous gap identified in the literature
- It's more novel — nobody is doing semantic drift analysis on MCP tool descriptions

## Why the Main Plan is Better

- The main plan (MCP-RSS) has broader impact — it addresses the entire risk scoring problem
- Implicit poisoning is one input to the main plan's scoring system (the "Description Integrity" metric)
- A thesis about a complete system is stronger than a thesis about one detection technique
- The main plan has clearer evaluation methodology and more available benchmarks

## Bottom Line

If the main plan's Phase 2-3 results are disappointing (LLM scoring doesn't transfer from CVEs to MCP), pivot to this direction. It's narrower but potentially higher-impact on a single critical problem.
