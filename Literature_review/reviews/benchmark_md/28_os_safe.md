# OS-Safe (from AGrail)

## Source
- **Paper:** AGrail: A Lifelong Agent Guardrail with Effective and Adaptive Safety Detection (Luo et al., 2025b)
- **Authors:** Weidi Luo, Shenghong Dai, Xiaogeng Liu, Suman Banerjee, Huan Sun, Muhao Chen, Chejian Xiao
- **Venue:** Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (ACL 2025), Vienna — long paper, pp. 8104-8139
- **Link:** (check AGrail project page / ACL Anthology — arXiv preprint candidate: 2502.11448)
- **Year:** 2025

## Format & Size
- **Annotation level:** **Step-level**
- **Monitored behavior:** web browsing and code execution (not general tool calls)
- **Pattern coverage (per ToolSafe):** MUR ✓, PI ✓, HT ✓, BTRA — (no benign-tool-risky-args)
- **Focus:** lifelong adaptive guardrail for OS-level agents (web + code execution
  environments)
- **Availability:** Published at ACL 2025; implementation artifacts released by authors
- **Exact sample counts:** not confirmed from abstract — resolve from full paper before citing numbers

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Trajectory ID | String | OS-Safe-0045 | Yes | Links to scenario |
| Environment | Categorical | web browser / code interpreter / OS shell | Yes | Execution surface |
| Action type | Categorical | click / type / shell-exec / file-write | Yes | OS-level action primitive |
| Pre-action context | Structured | DOM state / file system state / prior actions | Yes | Needed for pre-execution judgment |
| Step safety label | Categorical | safe / unsafe | Yes | Step-level, not trajectory |
| Attack type | Categorical | MUR / PI / HT | Yes | BTRA excluded by design |
| Risk taxonomy tag | Categorical | task-specific / systemic | Yes | AGrail's two-layer taxonomy |

## Proposed Risk Dimensions

### OS-Level Action Primitive Severity
- **Feeding columns:** action type
- **Proposed scale:** 1-10 with OS primitives banded by blast radius
- **Derivation:** OS-Safe tracks concrete execution primitives (click, type, file-write,
  shell-exec) rather than abstract tool calls. Each primitive maps to a severity band:
  DOM read (2), DOM click (4), form submit (5), shell read (5), shell write (7),
  shell-exec (9), network egress (9). For an MCP server exposing filesystem or shell
  tools, this mapping translates directly. Complements the tool-level severity mapping
  in the project's static mode.

### Task-Specific vs. Systemic Risk Split
- **Feeding columns:** risk taxonomy tag (task-specific / systemic)
- **Proposed scale:** 1-10 where systemic risks (persistence, privilege escalation,
  cross-session contamination) score above task-specific risks
- **Derivation:** AGrail distinguishes risks tied to the current task from risks that
  affect the system's long-term integrity. The server-side scorer can use this split
  to decide whether to block one call (task-specific) or terminate the whole session
  (systemic). Maps into the project's Cross-Tool Escalation dimension.

## Data Quality Notes
- **Step-level annotation** is the most valuable property — few benchmarks provide
  pre-execution labels at the primitive-action granularity that OS-Safe does.
- **BTRA not covered** — every labeled action is either safe or intrinsically unsafe;
  there is no "benign tool weaponized by arguments" case. This is the largest gap
  vs. TS-Bench and directly motivates combining the two sources.
- **Execution surface is OS / web / code**, not general tool calls. For MCP servers
  exposing shell or filesystem tools (a large subset), this is a near-perfect match;
  for MCP servers exposing domain APIs (billing, email, calendar), the transfer is
  looser.
- The sample counts, exact split between safe/unsafe, and precise risk-tag distributions
  were not recoverable from the abstract alone. Resolve from the full ACL 2025 paper
  before citing in thesis tables.
- AGrail itself is evaluated with high latency (~8.75 sec/sample per ToolSafe's
  comparison) — the *benchmark* is useful, but AGrail's guardrail approach is too slow
  to reuse directly for real-time server scoring.

## Usefulness Verdict
OS-Safe is the step-level, OS-primitive complement to the tool-call-level TS-Bench.
Its strength for the project is twofold: (1) it provides pre-execution labels at the
granularity of concrete filesystem and shell primitives, which matches exactly the
kind of actions an MCP server exposing system-level tools would receive; and (2) the
task-specific / systemic risk split maps cleanly into the Cross-Tool Escalation
dimension the project's v3 refinement already defines. The main limitation is missing
BTRA coverage — benign-tool-risky-args is the dimension the project most needs,
and OS-Safe does not label it. The right usage is **pair with TS-Bench**: OS-Safe
contributes OS-primitive severity + task/systemic split, TS-Bench contributes BTRA
coverage and the three-level safety scale. Before citing exact numbers in thesis
tables, resolve sample counts from the full ACL 2025 paper.
