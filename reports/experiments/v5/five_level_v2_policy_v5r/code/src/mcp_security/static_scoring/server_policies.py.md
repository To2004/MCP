# `server_policies.py` — reading the organization's policy

**211 lines.** The realistic-disclosure counterpart to `server_profiles.py`: a
profile hands the scanner a per-asset `Sens.` number, a policy deliberately does
not.

## What it parses

`parse_asset_register()` reads the section's
`| Asset | Description | Tools | Flags | CIA |` table into `PolicyAssetRow`
objects. Column positions come from the header, so registers with or without the
optional `Flags` and `CIA` columns both parse. Three fields matter downstream:

- **Description** → becomes the asset description the sensitivity stage classifies
- **Tools** → becomes `tool:<name>` tags: the exact tool×asset homing blast scores
- **Flags** → becomes `flag:<name>` tags: the escape routes a tier-5 blast must cite

An em-dash `Tools` cell is a legitimate statement, not a parse error — nothing on
this server reaches that asset, and the scan marks its whole row N/A.

## What it refuses

`assert_no_sensitivity_numbers()` raises `PolicyNumbersError` if the section
contains an `| Asset | Sens. |` table. That guard is the experiment's integrity
check: a policy that states its own 1–5 is no longer measuring whether the scanner
can *derive* sensitivity, and without the guard the two documents could be
silently swapped. `policy_for()` is the loader that always applies it.

`PolicyRegisterError` covers a missing register, a short row, a duplicate asset id,
and an unknown `Flags` value — all scoring inputs, so silence is not an option.

## Why `Flags` is still policy-grade

A flag states what an asset *is* — other systems authenticate against it, it holds
a whole population, it is already published — not what it is worth. Two mechanisms
consume it: the blast rubric requires a tier-5 award to cite `hub` / `population` /
`self-sufficient`, and (in the older arms) the blast roof exempted flagged assets
from its read cap. v5r runs no roof, so only the tier-5 requirement uses it.

## Coverage helpers

`unmapped_tools()` and `unknown_register_tools()` are what
`scripts/check_policies.py` and the driver use: a tool the register names but the
server does not advertise is a hard error (a wrong homing silently mis-scores
blast); a tool with no register row is reported, because a genuinely asset-free
tool is a legitimate answer the section states in prose.
