# LLM inputs

Every model call in the pipeline and the files it reads.

## Files

| File | What it holds |
|---|---|
| `reports/tool_lists/<kind>.json` | tool name · description · input schema · annotations |
| `demo/<store>/` (tree, `.db`, or declared scopes) | asset_id · description · tags |
| `docs/mcp-tools/server-profiles.md` | org prose · per-asset table (Sens. C I A Contents Why) |
| `registry.apps` (in code) | app_id · purpose |
| `misuse_scoring_prompt.md` | param rubric text |

## Static scan

| Call | Per | Reads |
|---|---|---|
| ④ home uncovered tools | tool | tool_lists: name + description |
| ① infer domain | server | tool_lists: all names + descriptions · store: all assets · profiles.md |
| ② tool impact | tool | tool_lists: one tool, full · profiles.md · ① output |
| ③ blast radius | cell | tool_lists: one tool · store: one asset · profiles.md · ① output |
| baseline | app | registry.apps: one entry · profiles.md · ① output |
| input ranking | tool | tool_lists: name, description, parameters |
| param rubrics | tool | tool_lists: one tool · misuse_scoring_prompt.md |

## Runtime

| Call | Per | Reads |
|---|---|---|
| decode obfuscated args | call | tool name · call arguments (normalized) |

## Not read

| Call | Does not read |
|---|---|
| ④ home uncovered tools | profiles.md · store |
| ② tool impact | store |
| input ranking | profiles.md · ① output |
| decode obfuscated args | profiles.md · store |

Asset sensitivity is read from `server-profiles.md`, never asked of the model.

## Evaluation only

| Call | Reads |
|---|---|
| blind judge | ① output · scoring rules · one item (not the proposed answer) |
| review critics / advisor | the scan artifact |

## References

- [`architecture.dot`](architecture.dot)
- [`../standards/scoring-prompts.md`](../standards/scoring-prompts.md)
