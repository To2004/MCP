# v4 prompts — exactly as sent by these runs

Generated from `mcp_security.static_scoring.prompts` after the bulk
"drops a safety" clause was removed, so this file matches what the model saw.

## Tool impact (inputs: the tool JSON alone — no preamble, no profile, no domain)

```text
You are classifying one MCP tool. Output ONLY valid JSON,
no prose, no fences.

TASK: Assign TOOL IMPACT (1-5) -- what ONE call DOES, judged from the tool's
description and parameters alone. Not how much it touches (that is scored
separately), not how valuable the target is.

The ladder follows the MCP annotation vocabulary (read-only / destructive /
open-world) and CVSS integrity-and-availability loss:
  1 NO EFFECT      the caller learns only that the service is reachable, or facts
                   about its own session (ping, health, version, whoami, clock).
  2 METADATA       read-only, and returns only about-ness: names, ids, counts,
                   sizes, timestamps, permissions, schema, a listing. OR changes
                   only about-ness: mark read, star, pin, mute, pure rename.
  3 CONTENT READ   read-only, and returns the substance itself (bodies, values,
                   file contents, message text, search results with content).
                   Nothing changes; what was seen cannot be unseen.
  4 REVERSIBLE WRITE  modifies state in a way the system itself can undo: create,
                   append, partial/field edit, move, membership or permission
                   change (grant AND revoke), a message posted where it can still
                   be edited or deleted.
  5 IRREVERSIBLE OR OPEN-WORLD  no path back from inside the system: delete, wipe,
                   drop, purge, or a COMPLETE overwrite that replaces an item's
                   entire content; executes code; moves money; OR crosses the
                   system boundary (email/SMS/webhook/public post/external invite),
                   which is unrecallable once sent.

RULES
- Score the DESCRIPTION and PARAMETERS, never the name. Annotation hints
  (readOnlyHint, destructiveHint, openWorldHint) are HINTS ONLY -- corroborating
  evidence, never overriding a description that says otherwise.
- A tool spanning tiers takes the HIGHEST it can reach.
- Scoped edit (leaves the rest intact, reconstructable) = 4. Full overwrite of an
  item's entire content = 5. A tool that can do either takes 5.
- A bulk/batch variant takes AT LEAST its singular twin's tier.

Tool:
{tool_json}

Return JSON (reason first): {{"tool_name": str, "reasoning": str,
"tool_impact": 1-5, "confidence": 0.0-1.0}}
```

## Blast radius (inputs: org profile + domain profile + tool + asset + sibling lists)

```text
TASK: Assign BLAST RADIUS (1-5) for ONE (tool, asset) pair --
HOW FAR the consequences of one call reach. This is the CVSS v4.0 question: does
the impact stay inside this asset (the "vulnerable system"), or does it reach
systems, identities and data beyond it (a "subsequent system")?

Sensitivity is supplied separately by the organization's table and is ALREADY
multiplied into the score. Do NOT price value here. Blast prices REACH ONLY.

  1 ONE ITEM      a single item among many; one subject. The asset as a whole is
                  untouched.
  2 NARROW SLICE  a few items or one small bounded scope; a handful of subjects.
                  The overwhelming majority of the asset is unaffected.
  3 BROAD CUT     most of the asset, or several whole scopes in one call --
                  serious but still PARTIAL; a substantial part survives.
  4 TOTAL, CONTAINED   essentially everything the asset holds (CVSS "total loss
                  ... all information within the Vulnerable System"), including
                  the whole of a single-item asset -- but the consequences STOP at
                  the asset's boundary. Full coverage of an ordinary asset is 4.
  5 ESCAPES       CVSS Subsequent System impact: the consequences do NOT stay
                  constrained to this asset. Award 5 only via a route the
                  ORGANIZATION'S TABLE sanctions, and name it:
                  (a) hub -- the asset is flagged `hub`: other systems
                      authenticate against it, load config from it, or deploy
                      from it, and one call discloses, corrupts or removes it
                      wholesale.
                  (b) population -- the asset is flagged `population` (or
                      `self-sufficient`) and one call reaches its ENTIRE set of
                      subjects at once.
                  (c) irreversible-total -- the whole asset is destroyed with no
                      path back, so nothing remains to restore.

DISCIPLINE
- If the asset carries NO escape flag in the table, the ceiling is 4. Do not
  infer a population or hub escape from prose adjectives.
- Reading a listing, names, or metadata is reconnaissance: it exposes no contents
  and removes nothing, so it cannot exceed the metadata tier.
- Reach is RELATIVE TO THIS ASSET: touching the only item of a single-item asset
  is 100% of it. Physical size is a red herring.
- CONSISTENCY: the sibling lists below are the SAME server. The same kind of call
  on two comparable assets must not differ by more than one tier without a reason
  you can state in one sentence.

RELEVANCE FIRST: does this tool act on this asset AT ALL? If it operates only on
a different class, set affects_asset=false and blast_radius=null (N/A, not a low
score).

Tool: {tool_json}
Asset: {asset_json}
Other tools on this server: {peer_tools}
Other assets on this server: {peer_assets}

Return JSON: {{"tool_name": str, "asset_id": str, "affects_asset": bool,
"coverage_reasoning": str, "escape": "a|b|c|none",
"blast_radius": "1-5 or null", "confidence": 0.0-1.0}}
```
