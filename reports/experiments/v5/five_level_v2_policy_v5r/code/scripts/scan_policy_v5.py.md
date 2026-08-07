# `scan_policy_v5.py` — the driver

**247 lines.** The script that decides what a v5r scan is *allowed to know*.

## The two documents, and nothing else

For each target it assembles a `ServerRegistry` from exactly two sources:

1. **the captured tool catalog** — `reports/tool_lists/<catalog>.json`
2. **the organization's policy section** — `docs/mcp-tools/server-policies.md`

`build_policy_registry()` turns the policy's asset register into the asset list:
`Description` becomes the asset description, `Tools` becomes `tool:<name>` tags
(the exact tool×asset homing blast scores against), `Flags` becomes `flag:<name>`
tags (the escape routes a tier-5 blast must cite), and `expected_use()` supplies
the app purpose.

`server-profiles.md` is **never read**. Its per-asset numbers are the held-out
ground truth the derived sensitivities get scored against afterwards.

## The guard that runs before scoring

If the register names a tool the server does not advertise, the driver **raises**
rather than scanning:

```
{server}: the policy's asset register names N tool(s) the server does not
advertise: [...]. Fix the register's Tools cells — a wrong homing silently
mis-scores blast.
```

A tool with *no* register row is only reported, not fatal: a genuinely asset-free
tool (`get-current-time`) is a legitimate answer the policy states in prose.

## Modes and outputs

`--impact-mode` selects the arm, and each writes to its own directory:

| Mode | Output |
|---|---|
| `five_level_v2_v5` | `reports/experiments/v5/five_level_v2_policy_v5/` |
| `five_level_v2_v5r` | `reports/experiments/v5/five_level_v2_policy_v5r/` |

Six targets: the three `_real` orgs and the three live-provisioned ones
(`calendar_aurora`, `github_helios`, `slack_vireo`), which reuse the same vendor
catalogs so a score difference is attributable to the policy alone.

`strict=use_llm` is the important argument passed down: a GPU run is strict, so a
model failure aborts rather than falling back to a heuristic.

## What it stamps on every artifact

`registry_source: "tool_catalog+org_policy_only"`, `description_source`,
`catalog_sha256`, `policy_register_unmapped_tools`, and `uncovered_tools` (tools
whose every cell came back N/A). Existing artifacts are skipped unless
`--overwrite` is passed, so a resumed run never destroys completed work.
