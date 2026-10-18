# Tool-input rules

Run-time lookup that turns a call's argument values into a level from 1 to 5. Used by v13 ([reports/experiments/v13](../../../reports/experiments/v13/README.md)) and v12 ([reports/experiments/v12](../../../reports/experiments/v12/README.md)).

## Where the rules come from

At design time, once per tool:

- **v13, one step** ([tool-input-levels.md](../../../docs/standards/tool-input-levels.md)): per input, a rule that reaches every level 1 to 5, or none. Before the check, `repairs.py` writes in what the model should not decide: `with_register_assets` gives an asset-name rule the policy's whole register (every asset of the server with its scanned level, whatever the tool) and keeps the model's name words only at levels no asset reaches; `with_credential_words` adds the credential words (`password`, `token`, `.env`, `id_rsa` and the like) at level 5 to every text rule. `rule_problems(..., all_levels=True, assets=...)` then rejects a rule with a level gap as well as a malformed one.
- **v12, two stages**: stage 1 ([tool-input-importance.md](../../../docs/standards/tool-input-importance.md)) decides which inputs matter, stage 2 ([tool-input-rules.md](../../../docs/standards/tool-input-rules.md)) writes their rules. `rule_problems()` without `all_levels` checks only the shape, so v12 files still load.

## What happens at run time

`evaluate_call(rows, args, assets=..., aliases=..., org_domains=..., partner_domains=..., flagged_domains=...)` applies each rule to the call's actual arguments and returns the highest level, the inputs that set it, and every input's level with the reason. No model runs on the call path.

| Rule kind | Turns a value into a level by |
|---|---|
| `ranges` | a measure (the number, a length, the hour of day, the weekday, the span to a sibling date-time, hours from now) compared with thresholds |
| `register` | matching the value to one of the organization's assets; the level is that asset's scanned sensitivity, or the rule's `overrides` where the policy prohibits the tool's action on it. The table is the rule's own `assets` (v13) plus the tool's assets passed at run time (`register_table`). A name on no list is then checked against the rule's name words (`groups`) |
| `keywords` | lowercase substring fragments; the highest matching group wins |
| `values` | a fixed choice or a boolean, looked up in a table |
| `domain` | the address's domain compared with the organization's own (v12: two levels) |
| `email` | a fixed ladder from the organization's policy (v13): own domain 1, partner 2, no readable domain 3, another organization 4, a personal mailbox or a flagged domain 5 |

v13: level 1 is the safest realistic value and 5 the riskiest; an ordinary call gets 1 to 3. v12 treated 3 as the neutral point.

## Conservative defaults

- A left-out input with a schema default is rated at that default, but at most 3 (v13 from run21): the server's own default is an ordinary call. Leaving an input out rates higher only through `when_absent`, which the v13 runner allows above 3 only when a policy row calls leaving it out risky.

- A list input takes the highest level among its items.
- A value a rule cannot read (a date that does not parse, a number that is text) gets the rule's `default` and is flagged `unresolved`.
- `domain`: an address with no readable domain, or a deployment with no configured org domains, is treated as external.
- `email`: without the organization's own domains, an address that is not a personal mailbox is treated as another organization (4), never assumed internal, and flagged `unresolved`.
- A `register` value that names no listed asset and contains none of the rule's name words gets the rule's `default`, flagged `unresolved`.

## Identifiers

A deployment can pass `aliases`, a table from raw identifiers to asset ids (its own channel and calendar ids). Values with an alias resolve exactly.

## Known limit

Without an alias, `register` matches an asset by name: the value equals the asset id or contains it. Opaque identifiers with no alias need the traffic-discovered bindings in [`mcp_security.binding`](../binding/README.md); until those are plugged in, such a value falls to the rule's `default`.
