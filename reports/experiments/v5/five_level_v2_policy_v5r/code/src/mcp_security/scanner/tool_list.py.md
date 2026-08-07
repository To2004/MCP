# `tool_list.py` — loading the captured catalog

**71 lines.** `load_tool_list(kind, path=...)` reads a captured `tools/list`
response and returns `[ToolSpec]`.

This is one of exactly **two inputs** to a v5r scan. It carries, per tool: the
name, the description, the JSON input schema, and the four MCP annotation hints
(`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`).

## Why "captured" matters

The catalogs in `reports/tool_lists/` were recorded from the real vendor servers,
not written by hand. That is what makes the arm honest: the tool descriptions the
rules and the model reason over are the vendor's own words, with all their
vagueness intact. `create-event`'s description really is just "Create a new
calendar event." — which is why the rules abstain on it, and why that abstention is
a property of the world rather than of the rule set.

The driver records a `catalog_sha256` in every artifact so a result is tied to the
exact bytes it was scored from.

## The three catalogs this run used

| Catalog | Tools | Used by |
|---|--:|---|
| `calendar_real.json` | 13 | `calendar_real`, `calendar_aurora` |
| `slack_real.json` | 16 | `slack_real`, `slack_vireo` |
| `github_real.json` | 26 | `github_real`, `github_helios` |

The live-provisioned orgs reuse the same vendor catalogs as their `_real`
counterparts — only the organization, and therefore the policy, changes. That is
deliberate: it makes any score difference between `github_real` and
`github_helios` attributable to the policy text alone.
