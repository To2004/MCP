# Scanner prompts as run

## scan_preamble

<!-- sha256: 542614909bce6b4ef073d53717d9e1b2fca7faa781bf708e6bea17de84e8b282 -->

You are a security classifier for an MCP gateway. Two
descriptions of this server are given below. The ORGANIZATION'S DESCRIPTION is
written by the people who deploy it and is authoritative for CONTEXT: who runs the
server, what agents are supposed to do with it, how severe each asset is, and which
of confidentiality / integrity / availability carries the loss. The INFERRED DOMAIN
PROFILE is derived from the tool registry and is authoritative for MECHANICS: what
the tools can actually do. Use both. Where they disagree about CAPABILITY trust the
inferred profile; where they disagree about IMPORTANCE trust the organization.

ORGANIZATION'S DESCRIPTION OF THIS MCP SERVER:
{org_description}

INFERRED DOMAIN PROFILE:
{domain_profile}

Output ONLY valid JSON, no prose, no fences.

## scan_domain

<!-- sha256: 68c1eab81602ad799b2371ebd367b9708a86e5d78efc47c41ad09036362abd69 -->

You are calibrating a risk scorer for one MCP server.
From the tool registry alone, say what this server is and what "one item" means
here. Nothing else — the deploying organization supplies the rest.

Output ONLY valid JSON, no prose, no fences.

- mcp_kind: what system this MCP fronts (filesystem, SQL database, calendar,
  chat workspace, source repository, cloud infra, ...).
- content_unit: what ONE item concretely is here — a file, a row, a message, an
  event, a record.
- contents_definition: one sentence — what counts as an item's CONTENTS (bodies,
  values, message text) as opposed to METADATA about it (ids, counts, sizes,
  timestamps, permissions, schema).

Set needs_human_review=true, and confidence below 0.7, if the registry is too
sparse to tell.

Tools:
{tools_json}

Return JSON: {{"mcp_kind": str, "content_unit": str, "contents_definition": str,
"confidence": 0.0-1.0, "needs_human_review": bool}}

## scan_impact

<!-- sha256: f849daba055b1af4afc83b62645fd18850b59559b11baa8d627f856e1f32f0ba -->

You are classifying one MCP tool. Output ONLY valid JSON,
no prose, no fences.

TASK: Assign TOOL IMPACT (1-5) — what OPERATION one call performs, judged from
the tool's description and parameters. Not how much it touches (blast radius
scores that), not how valuable the target is (sensitivity scores that).

Ask only: does it read, does it write, or does it remove?

  1 NO EFFECT      the caller learns only that the service is reachable, or facts
                   about its own session: ping, health, version, clock, whoami.
  2 METADATA       returns or changes only about-ness — names, ids, counts, sizes,
                   timestamps, permissions, schema, a listing; or consumption
                   state: mark read, star, pin, mute, rename.
  3 CONTENT READ or LIMITED WRITE
                   returns the substance itself (bodies, values, message text), OR
                   writes a bounded amount and leaves the rest of the item
                   untouched: append a line, add a comment or a reply, set one
                   named field, post a short message. HTTP calls this PATCH; CVSS
                   calls it "the amount of modification is limited".
  4 WRITE          the ordinary write: the caller supplies what the item says.
                   Create a record with its fields, update an event, write a file,
                   overwrite content. HTTP calls this PUT; CVSS calls it a total
                   loss of integrity for that item.
  5 REMOVAL or EXECUTION
                   no path back from inside the system: delete, wipe, drop, purge,
                   truncate; or it executes code, runs a command, or moves money.

RULES
- Score the DESCRIPTION and PARAMETERS, never the name alone.
- The CHANNEL is not the operation. Sending mail, posting externally or invoking a
  webhook creates a message — that is a write. Whether a specific call actually
  leaves the organization is a runtime fact, scored elsewhere.
- Annotation hints (readOnlyHint, destructiveHint, idempotentHint) are HINTS. They
  may corroborate; they never bound the answer. If a hint contradicts the
  description, follow the description and say so in your reasoning.
- A write is an ordinary write (4) unless the declaration says the amount is
  bounded (3). If it does not say, judge from the parameters: a single
  content/body field is a whole write; named optional fields are a patch.
- A tool that can do two of these takes the more consequential one.

Tool:
{tool_json}

Return JSON (reason first): {{"tool_name": str, "reasoning": str,
"tool_impact": 1-5, "confidence": 0.0-1.0}}

## scan_sensitivity_task

<!-- sha256: 33265646007f0c342d40bde59a222127651733f3c68202226647e3e7dafbff72 -->


TASK: Assign ASSET SENSITIVITY (1-5) -- how bad an incident is if THIS asset is
exposed, corrupted or destroyed. Judge what it CHARACTERISTICALLY holds, not the
worst thing it could conceivably hold.

The ORGANIZATION'S POLICY above is authoritative. Work in two steps:
  1 CLASSIFY. Find this asset in the policy's asset register -- its Description
    states what it holds. No row? Apply the policy's recognition rules. Still
    undecided? Use the policy's stated default class.
  2 MAP that class's adverse-impact definition onto the tiers below (severe /
    serious / limited adverse effect).

  5 CROWN JEWEL  exposure alone is an emergency -- exploitable or legally
                 reportable the moment it leaks (live credentials, PHI, card data,
                 privileged or money-moving records); OR a control plane: losing it
                 rewires what every other tool can reach (auth/scope configuration,
                 access-control state), so the damage is not one asset but all of
                 them.
  4 RESTRICTED   serious lasting harm one step removed: damages customers, staff or
                 the company's position, but is not instantly weaponizable.
  3 INTERNAL     disruptive and embarrassing but recoverable; meant to stay in-org.
  2 ROUTINE      low-value internal material; exposure is a shrug.
  1 PUBLIC       already published or disposable -- no confidentiality left to lose.

RULES
- ABSOLUTE scale, never relative to the other assets here. A whole server sitting
  at one tier is expected and correct; do NOT spread scores to manufacture contrast.
- CONTAINER: takes the tier of the most sensitive thing it CHARACTERISTICALLY
  holds -- its typical payload, not a conceivable one.
- METADATA-ONLY: an asset holding only about-ness -- names, ids, counts, listings,
  schema, read/RSVP state, with no bodies -- is reconnaissance, not disclosure:
  cap it at 2. Exception: the policy says those names themselves identify people,
  deals or candidates.
- AGGREGATION: if one asset holds the WHOLE population of a class, or the policy
  names a combination that reveals more than its parts, raise one tier.
- PUBLISHED, NOT TOPIC: data the organization has already published has no
  confidentiality left to lose and is 1, however sensitive its subject sounds.
- Torn between two adjacent tiers on NON-public secrets, PII, money-moving or
  regulated records: take the HIGHER. Never for public data.

## scan_sensitivity_item

<!-- sha256: ebbf5b328f203b11e5843cc0097624655b0e2c889966067b499a65a58a4fedfe -->

Asset class entry:
{asset_json}

Return JSON (classify BEFORE you score -- emit these keys in this exact order):
{{"asset_id": str, "policy_class": str, "reasoning": str,
  "sensitivity": 1-5, "confidence": 0.0-1.0}}

## scan_blast_task

<!-- sha256: b65ebb27d4b6a78caf1a5e64c64befabca4c724b926849e8002de3d41f1391b1 -->

TASK: Assign BLAST RADIUS (1-5) for ONE (tool, asset) pair —
HOW FAR the consequences of one call PROPAGATE. What the asset is worth is scored
separately and already multiplied in; price the SPREAD of the consequence only.

COUNT SUBJECTS AND SYSTEMS, NOT ITEMS, and count them in ORGANIZATIONAL SCOPE.
How many rows a call touches is a weak proxy and often the wrong one. Reading ONE
password file touches one item and reaches every system that password opens.
Ask: after this call, WHO is different, and how far across the organization do
they sit?

  1 ONE PERSON OR ITEM   the consequence stops at a single subject, or a single
                         item nothing and nobody depends on. A colour palette, a
                         scratch record, one person's own state.
  2 ONE GROUP            the people or systems attached to what the call touched,
                         within one team or one bounded scope — the attendees of
                         an event, the members of a channel, the consumers of one
                         record. **This is the normal case for a call that touches
                         real organizational data. Start here and move for a
                         reason.**
  3 SEVERAL GROUPS       the consequence crosses team or scope boundaries — an
                         event spanning several teams, a set of channels, records
                         belonging to more than one part of the organization.
  4 ORGANIZATION-WIDE    essentially everyone or everything this asset serves,
                         at once — but the consequence still stops at the
                         organization's boundary.
  5 BEYOND               the consequence does not stay inside this asset or the
                         organization. It reaches systems, identities or people
                         outside it, or it cannot be contained once it starts.

BEFORE AWARDING 5, ask these four questions of the asset's own description. Answer
each yes or no, and for any yes QUOTE the words in the description that support
it. A 5 with no quotable support is not a 5 — say so and score 4.

  Q1 LOAD-BEARING   Do other systems depend on this to function — do they
                    authenticate against it, load configuration from it, or deploy
                    from it? Then reaching it reaches them.
  Q2 PORTABLE       Is what this call RETURNS usable on its own somewhere else — a
                    credential, a key, a token? Then the consequence leaves with
                    the data even though one item was touched.
  Q3 WHOLE SET      Does one call reach the ENTIRE population of subjects this
                    asset covers, rather than some of them?
  Q4 NOTHING LEFT   Is the asset destroyed outright, with nothing remaining to
                    restore from?

Do NOT award a tier because the material is confidential, executive or otherwise
sensitive. How valuable it is has already been scored and multiplied into this
cell. Score only how far the consequence travels.

Reach is relative to THIS asset: touching the only item of a single-item asset is
all of it.

RELEVANCE. The organization's register lists which tools it believes reach this
asset; that list is given below. Use it like this:

  * IF THE REGISTER LISTS THIS TOOL — relevance is settled. The organization is
    not guessing about its own surface. Score the reach; do not return null.
  * IF THE REGISTER DOES NOT LIST IT — you decide, but silence is not evidence of
    absence. Registers are written by hand and miss shared surfaces. Ask whether
    this tool genuinely reaches this asset, not whether somebody wrote it down.

N/A IS THE MORE EXPENSIVE MISTAKE. A wrong low score stays in the matrix where a
reviewer can see it and argue with it. A wrong N/A deletes the cell — nobody ever
looks at it again, and a real consequence goes unrecorded. They are not
symmetric. So:

  * return null ONLY when the tool operates on a genuinely different class of
    thing and could not touch this asset by any route;
  * when you are unsure, score 1 — "one person or item" — rather than null. An
    over-scored 1 costs almost nothing; a wrongly hidden cell costs everything.

## scan_blast_item

<!-- sha256: 64b7240868aa66460601015b7bef1dad45d3197c90266b8484bdfbbb93a3c742 -->

Tool: {tool_json}
Asset: {asset_json}
The organization's register says these tools reach this asset: {register_tools}
Already decided for this pair — tool impact: {tool_impact} · asset sensitivity: {asset_sensitivity}
Other tools on this server: {peer_tools}
Other assets on this server: {peer_assets}

Return JSON: {{"tool_name": str, "asset_id": str, "affects_asset": bool,
"coverage_reasoning": str,
"escape": "EXACTLY ONE of these five strings: Q1, Q2, Q3, Q4, none",
"escape_evidence": "the words quoted from the asset description, or empty",
"blast_radius": "1-5 or null", "confidence": 0.0-1.0}}
