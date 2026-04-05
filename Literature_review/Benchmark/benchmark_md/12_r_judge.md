# R-Judge Records

## Source
- **Paper:** R-Judge: Benchmarking Safety Risk Awareness for LLM Agents — Yuan et al.
- **Link:** https://github.com/Lordog/R-Judge
- **Year:** 2024

## Format & Size
- **Total samples:** 569 multi-turn agent interaction records
- **Format:** Annotated interaction traces with safety labels, covering 27 risk scenarios across 5 application categories and 10 risk types
- **Availability:** Public on GitHub — https://github.com/Lordog/R-Judge

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Interaction record | Multi-turn text | Agent-environment conversation trace | Yes | 569 records — full interaction context, not just single turns |
| Risk scenario | Categorical | 27 distinct scenarios | Yes | Scenario-level labels for risk mapping |
| Application category | Categorical | 5 categories (sourced from WebArena, ToolEmu, InterCode-Bash, InterCode-SQL, MINT) | Yes | Domain-level grouping |
| Risk type | Categorical | 10 annotated risk types | Yes | Fine-grained risk classification labels |
| Safety label | Binary/Categorical | Safe / Unsafe | Yes | Ground-truth annotation per record |
| Source environment | Categorical | WebArena, ToolEmu, InterCode-Bash, InterCode-SQL, MINT | Yes | Indicates which evaluation framework generated the trace |
| LLM evaluation scores | Numeric | Per-model safety judgment accuracy | Yes | 11 LLMs evaluated; GPT-4o best at 74.42% |

## Proposed Risk Dimensions

### Risk Type Classification (10-label)
- **Feeding columns:** Risk type (10 annotated types)
- **Proposed scale:** 1-10 where each risk type maps to a severity level
- **Derivation:** The 10 risk types provide a ready-made multi-label classification scheme. Assign each type a base severity: types involving data destruction or system compromise = 8-10, types involving privacy violation = 6-8, types involving resource misuse = 4-6, types involving policy violation = 2-4. For a given interaction, if multiple risk types apply, take the maximum (worst-case) or a weighted sum. The 569 labeled records provide training data for a risk-type classifier.

### Scenario-Level Risk Mapping
- **Feeding columns:** Risk scenario (27 scenarios), safety label
- **Proposed scale:** 1-10 per scenario based on observed unsafe rate
- **Derivation:** For each of the 27 scenarios, compute the fraction of records labeled "unsafe." Scenarios where most interactions are unsafe = high inherent risk (7-10). Scenarios where most are safe = lower risk (2-4). This gives a prior: when an agent enters a scenario matching one of these 27 patterns, the scenario's historical unsafe rate provides the baseline risk score before examining the specific interaction.

### Application Domain Risk
- **Feeding columns:** Application category (5 categories)
- **Proposed scale:** 1-10 per domain
- **Derivation:** The 5 application categories (web browsing via WebArena, tool use via ToolEmu, bash execution via InterCode-Bash, SQL execution via InterCode-SQL, general via MINT) represent fundamentally different risk profiles. Bash and SQL execution environments allow direct system manipulation → base score 7-9. Tool use environments depend on the tools → base score 4-7. Web browsing → base score 3-6. Compute per-domain unsafe rates from the 569 records to calibrate these base scores empirically.

### Agent Safety Judgment Difficulty
- **Feeding columns:** LLM evaluation scores (11 models), GPT-4o accuracy at 74.42%
- **Proposed scale:** 1-10 measuring how hard it is for an LLM to correctly judge risk in this record
- **Derivation:** The fact that the best model (GPT-4o) only achieves 74.42% accuracy — and most models perform near random — means safety judgment is genuinely hard. For each record, compute how many of the 11 LLMs correctly judged its safety label. Records where all models fail = difficulty 9-10 (these are the subtle, ambiguous cases). Records where most models succeed = difficulty 2-4. This dimension identifies which types of interactions are hardest to score, informing where a risk scorer needs the most calibration data.

## Data Quality Notes
- 569 records is relatively small for training a robust model, but each record is a rich multi-turn interaction (not a single sentence), making the per-sample information density high.
- The 27 scenarios and 10 risk types are author-defined categories. They cover a broad range but may not include all MCP-specific attack patterns (e.g., no explicit MCP tool poisoning or toolchain attacks).
- The interaction traces come from 5 different source environments, each with different formats and conventions. Standardization may be needed before combining.
- Safety labels are binary (safe/unsafe), not graded — there is no built-in 1-10 severity scale. Converting binary labels to a continuous score requires additional annotation or modeling.
- The 74.42% best accuracy shows a hard ceiling for current LLMs on safety judgment, which is useful as a baseline but also means any LLM-based scorer will have significant error margins on this type of data.
- Fine-tuning on safety judgment data reportedly improves performance significantly, suggesting the 569 records could serve as fine-tuning data for a risk scorer.

## Usefulness Verdict
R-Judge fills a gap that pure MCP-focused datasets miss: **multi-turn interaction risk assessment**. MCP risk scoring cannot just look at a tool's description in isolation — it needs to evaluate the full interaction trace (what the agent asked for, what the tool returned, what the agent did next). R-Judge's 569 multi-turn records, with ground-truth safety labels, provide exactly this kind of sequential-context training data.

The 10 risk types and 27 scenarios offer a structured taxonomy that partially overlaps with MCP-relevant risks (tool misuse, data exposure, unauthorized actions). The 5 application categories — especially InterCode-Bash, InterCode-SQL, and ToolEmu — map to common MCP server types. The main limitation is that R-Judge was not designed for MCP specifically, so some adaptation is needed. But the core value — labeled multi-turn safety data with multi-dimensional risk categories and 11-model evaluation baselines — makes it one of the few datasets where you can actually train and validate a continuous risk scorer rather than just a binary classifier. The 74.42% GPT-4o accuracy sets a realistic performance ceiling that any MCP risk scorer should aim to exceed through MCP-specific fine-tuning.
