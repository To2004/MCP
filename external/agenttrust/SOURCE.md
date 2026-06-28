# AgentTrust benchmark (vendored)

Severity-graded scenarios used as **external ground truth** to evaluate the
risk-scoring framework (not attack detection — graded `none/low/medium/high/critical`
severity over benign→misuse agent tool operations).

- Upstream: https://github.com/chenglin1112/AgentTrust
- Paper: "AgentTrust: Runtime Safety Evaluation and Interception for AI Agent Tool Use", arXiv:2605.04785
- Commit: `5503647dd04006c916324b92c753752842c33aec`
- License: AGPL-3.0 (see `LICENSE`)
- Vendored: `src/agent_trust/benchmarks/scenarios/*.yaml` (300 internal scenarios, 6 categories)

Each scenario carries an `expected_risk` (none/low/medium/high/critical) and
`expected_verdict` (allow/warn/block/review) plus the concrete action
(`action_type`, `tool_name`, `parameters`, `raw_content`). We use `expected_risk`
as the ground-truth severity and grade each risk scorer's output against it.
