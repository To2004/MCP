# InjecAgent Dataset

## Source
- **Paper:** InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated LLM Agents (Zhan et al., 2024)
- **Link:** https://github.com/uiuc-kang-lab/InjecAgent
- **Year:** 2024

## Format & Size
- **Total samples:** 1,054 test cases
- **Format:** Indirect prompt injection scenarios involving tool-integrated LLM agents with distinct user-tool and attacker-tool sets
- **Availability:** GitHub (https://github.com/uiuc-kang-lab/InjecAgent)

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Test case | Structured scenario | User query + injected content in tool response | Yes | Each case is a complete injection scenario |
| User tools | Categorical (17 tools) | Legitimate tools the agent is instructed to use | Yes | 17 tools represent the agent's authorized toolset |
| Attacker tools | Categorical (62 tools) | Tools the attacker tries to get the agent to invoke | Yes | 62 attacker tools — 3.6x more attacker tools than user tools |
| Harm category | Categorical | Direct harm, Data stealing/exfiltration | Yes | Binary harm taxonomy — coarse but clean |
| Agent configuration | Categorical | Different LLM + tool setups | Yes | Multiple configs tested for vulnerability variation |
| Injection payload | Text | Prompt injection embedded in tool output | Yes | The actual attack content — useful for pattern analysis |

## Proposed Risk Dimensions

### Tool Trustworthiness
- **Feeding columns:** User tools (17) vs. attacker tools (62)
- **Proposed scale:** 1-10 where known user tools = 1-2, unknown tools with benign signatures = 3-5, tools matching attacker-tool patterns = 6-8, known attacker tools = 9-10
- **Derivation:** The 17/62 split between user and attacker tools provides a concrete "trust boundary" dataset. Build a classifier or feature set that distinguishes user-tool invocation patterns from attacker-tool patterns. At runtime, when the agent attempts to invoke a tool, score how closely it matches the attacker-tool distribution vs. the user-tool distribution. Tools that appear in the attacker set score 9-10. Tools that share characteristics (parameter types, data access patterns) with attacker tools but are not in the set score 5-7. This is the only benchmark that explicitly separates "tools the agent should use" from "tools an attacker wants the agent to use."

### Data Exposure Risk
- **Feeding columns:** Harm category (specifically: data stealing/exfiltration cases)
- **Proposed scale:** 1-10 based on the type and sensitivity of data targeted for exfiltration
- **Derivation:** Filter the 1,054 cases to the data stealing/exfiltration subset. Classify the exfiltration targets by sensitivity: credentials and API keys = 9-10, personal/financial data = 7-8, internal documents = 5-6, metadata or public info = 2-3. For each test case in this subset, the risk score reflects what the attacker tried to exfiltrate and whether the agent complied. Cases where the agent successfully exfiltrates data get the full severity score; cases where it refuses get a reduced score (risk existed but was mitigated).

### Harm Severity Classification
- **Feeding columns:** Harm category (direct harm vs. data stealing)
- **Proposed scale:** 1-10 where data stealing = 5-7 baseline (reversible, detectable) and direct harm = 7-10 baseline (may be irreversible — deleting files, sending unauthorized messages, executing transactions)
- **Derivation:** Direct harm is scored higher because it involves the agent taking destructive or unauthorized actions that may not be undoable. Data exfiltration is scored slightly lower because it is often detectable after the fact and does not alter system state. Within each category, scale by the specific action: reading data = 5, sending data externally = 7, deleting data = 9, executing financial transactions = 10.

## Data Quality Notes
- At 1,054 test cases, this is a medium-sized benchmark. Enough for evaluation and threshold tuning, but probably not enough for training a standalone classifier without augmentation.
- The 17 user tools and 62 attacker tools are not exhaustively documented in terms of what each tool does — you may need to inspect the repository to get full tool descriptions and parameter schemas.
- The binary harm taxonomy (direct harm vs. data stealing) is coarse. Real attacks often combine both — an attacker might steal credentials (exfiltration) and then use them to take direct action. The benchmark does not capture multi-stage attacks.
- Multiple agent configurations are tested, which is valuable for understanding how vulnerability varies across models and setups. However, the specific configurations are tied to models available at the time of publication (2024) and may not cover newer models.
- Actively referenced by downstream work: MindGuard uses it for attack payload adaptation, Adaptive Attacks uses a 100-case subset, and TraceAegis references it. This adoption validates the benchmark's relevance.

## Usefulness Verdict
InjecAgent's standout contribution to a multi-label risk scorer is the explicit user-tool vs. attacker-tool separation. No other benchmark in the survey draws this line so clearly. This makes it uniquely suited for building a "tool trustworthiness" risk dimension — you have 17 ground-truth safe tools and 62 ground-truth dangerous tools, which is exactly the kind of labeled data needed to train a tool-level risk classifier. The 3.6x ratio of attacker tools to user tools also reflects a realistic imbalance: in any MCP ecosystem, the number of potentially dangerous tool invocations far exceeds the number of legitimate ones.

The two harm categories (direct harm vs. data exfiltration) are simple but cover the two most important failure modes for agentic systems. For a 1-10 scoring system, InjecAgent gives you the binary foundation: is the agent being tricked into using the wrong tool (tool trustworthiness dimension) and what is the consequence (harm severity dimension). The limitation is granularity — you will need to layer finer-grained severity scoring on top of the binary harm labels using your own impact analysis.
