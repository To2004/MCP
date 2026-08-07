# v4 — PROPOSED scoring prompts (not yet run)

Rewritten tool-impact and blast-radius prompts, grounded in published standards
instead of hand-grown prose. **Nothing here has been executed** — this is the
document to read and approve before the v4 run.

Two design changes carried in from the v3 findings and your instructions:

| Stage | v3 (current) | v4 (proposed) | Why |
|---|---|---|---|
| Tool impact | tool JSON **+ org profile + inferred domain profile**, 6 484 chars of rubric | **tool JSON only** + a 1 000-char ladder | The v3 `imponly` arm changed 12/13 impacts not at all — the asset table was dead weight. Impact is a property of the *action*, not of what it touches. |
| Blast radius | tool JSON + asset JSON + profile, 8 099 chars | **everything**: tool + asset + full profile + domain + the sibling tool/asset lists, ~2 400-char rubric | Reach is inherently relative — it needs the whole picture. The v3 inconsistencies (same tool, same sensitivity, blast 1 vs 5) come from scoring each cell blind. |

Prompt budget: impact **6 484 → ~1 050 chars** (−84 %), blast **8 099 → ~2 400
chars** (−70 %), and the impact stage also drops the ~780-char profile preamble.

---

## Sources (read these first)

1. **CVSS v4.0 Specification Document** — FIRST.org.
   <https://www.first.org/cvss/v4.0/specification-document>
   The v4 release **retired the old "Scope" metric** because it was scored
   inconsistently, and replaced it with two impact groups: **Vulnerable System
   Impact (VC/VI/VA)** and **Subsequent System Impact (SC/SI/SA)**. Definitions
   used below, verbatim:
   - VC:High — *"There is a total loss of confidentiality, resulting in all
     information within the Vulnerable System being divulged to the attacker."*
   - VC:Low — *"There is some loss of confidentiality. Access to some restricted
     information is obtained, but the attacker does not have control over what
     information is obtained."*
   - VI:High — *"There is a total loss of integrity … the attacker is able to
     modify any/all files protected by the Vulnerable System."*
   - VA:High — *"There is a total loss of availability, resulting in the attacker
     being able to fully deny access to resources in the Vulnerable System."*
   - Subsequent-system **None** — *"no loss … or all impact is constrained to the
     Vulnerable System."*
   - A system is *"the set of computing logic that executes in an environment with
     a coherent function and set of security policies"*; impacts outside it belong
     to the subsequent-system metrics.

   **This is the backbone of the new blast rubric**: our asset = CVSS's
   *Vulnerable System*; blast 1–4 is impact *inside* it (partial → total), blast 5
   is *Subsequent System* impact (it escaped).

2. **CVSS v4.0 User Guide / FAQ** — <https://www.first.org/cvss/v4.0/user-guide> ·
   <https://www.first.org/cvss/v4.0/faq> — why Scope was dropped and how the
   vulnerable/subsequent split is meant to be applied.

3. **MCP Tool Annotations (spec 2025-03-26)** — the protocol's own risk vocabulary:
   `readOnlyHint` (does not modify the environment), `destructiveHint`
   (irreversible, e.g. deletion — only meaningful when not read-only),
   `idempotentHint` (repeat calls = one call), `openWorldHint` (touches external
   entities rather than a closed domain).
   <https://modelcontextprotocol.io/community/interest-groups/tool-annotations>

4. **"Tool Annotations as Risk Vocabulary: What Hints Can and Can't Do"** — MCP
   blog, 2026-03-16.
   <https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/>
   Annotations are *hints, not guarantees*; an untrusted server can misrepresent
   them, so safety-critical decisions belong in deterministic controls. **This is
   why the new impact prompt uses the four hint concepts as its ladder vocabulary
   but tells the model to score the DESCRIPTION, not the flags.**

5. **OWASP Top 10 for Agentic Applications (Dec 2025)** — the threat classes this
   scoring exists to price: *Tool Misuse and Exploitation*, *Identity and
   Privilege Abuse*, *Agent Behavior Hijacking*.
   <https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/>

6. **Blast radius, identity/agentic definition** — *"the set of assets,
   identities, datasets, and downstream systems an attacker can reach from a
   single compromised asset."*
   <https://nhimg.org/glossary/agentic-blast-radius/> ·
   <https://www.beyondtrust.com/resources/glossary/blast-radius> ·
   <https://cloudsecurityalliance.org/blog/2026/05/29/understanding-the-blast-radius-how-cloud-threat-detection-speeds-up-incident-scoping>

---

## 1 · TOOL IMPACT — proposed prompt

**Inputs: the tool's JSON only.** No org profile, no inferred domain profile, no
asset. (Impact is a property of the action; v3's `imponly` arm showed the asset
table changed nothing.)

```text
You are classifying one MCP tool. Output ONLY valid JSON, no prose, no fences.

TASK: Assign TOOL IMPACT (1-5) — what ONE call DOES, judged from the tool's
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
  (readOnlyHint, destructiveHint, openWorldHint) are HINTS ONLY — corroborating
  evidence, never overriding a description that says otherwise.
- A tool spanning tiers takes the HIGHEST it can reach.
- Scoped edit (leaves the rest intact, reconstructable) = 4. Full overwrite of an
  item's entire content = 5. A tool that can do either takes 5.
- A bulk/batch variant takes AT LEAST its singular twin's tier.

Tool:
{tool_json}

Return JSON (reason first): {"tool_name": str, "reasoning": str,
"tool_impact": 1-5, "confidence": 0.0-1.0}
```

## 2 · BLAST RADIUS — proposed prompt

**Inputs: everything.** The org profile (prose + asset table + flags), the
inferred domain profile, the tool, the asset row, **and** the sibling lists —
every other tool name and every other asset id on this server — so the model can
judge reach comparatively instead of blind. This directly targets the v3 defect
where the same tool scored blast 1 on one asset and 5 on an equally sensitive
sibling.

```text
You are a security classifier for an MCP gateway. Output ONLY valid JSON.

ORGANIZATION'S DESCRIPTION OF THIS SERVER (authoritative for what the assets are
and who depends on them):
{org_description}

INFERRED DOMAIN PROFILE (authoritative for what the tools can do):
{domain_profile}

TASK: Assign BLAST RADIUS (1-5) for ONE (tool, asset) pair — HOW FAR the
consequences of one call reach. This is the CVSS v4.0 question: does the impact
stay inside this asset (the "vulnerable system"), or does it reach systems,
identities and data beyond it (a "subsequent system")?

Sensitivity is supplied separately by the organization's table and is ALREADY
multiplied into the score. Do NOT price value here. Blast prices REACH ONLY.

  1 ONE ITEM      a single item among many; one subject. The asset as a whole is
                  untouched.
  2 NARROW SLICE  a few items or one small bounded scope; a handful of subjects.
                  The overwhelming majority of the asset is unaffected.
  3 BROAD CUT     most of the asset, or several whole scopes in one call —
                  serious but still PARTIAL; a substantial part survives.
  4 TOTAL, CONTAINED   essentially everything the asset holds (CVSS "total loss …
                  all information within the Vulnerable System"), including the
                  whole of a single-item asset — but the consequences STOP at the
                  asset's boundary. Full coverage of an ordinary asset is 4.
  5 ESCAPES       CVSS Subsequent System impact: the consequences do NOT stay
                  constrained to this asset. Award 5 only via a route the
                  ORGANIZATION'S TABLE sanctions, and name it:
                  (a) hub      — the asset is flagged `hub`: other systems
                                 authenticate against it, load config from it, or
                                 deploy from it, and one call discloses,
                                 corrupts or removes it wholesale.
                  (b) population — the asset is flagged `population` (or
                                 `self-sufficient`) and one call reaches its
                                 ENTIRE set of subjects at once.
                  (c) irreversible-total — the whole asset is destroyed with no
                                 path back, so nothing remains to restore.

DISCIPLINE
- If the asset carries NO escape flag in the table, the ceiling is 4. Do not
  infer a population or hub escape from prose adjectives.
- Reading a listing, names, or metadata is reconnaissance: it exposes no contents
  and removes nothing, so it cannot exceed the metadata tier.
- Reach is RELATIVE TO THIS ASSET: touching the only item of a single-item asset
  is 100 % of it. Physical size is a red herring.
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

Return JSON: {"tool_name": str, "asset_id": str, "affects_asset": bool,
"coverage_reasoning": str, "escape": "a|b|c|none",
"blast_radius": "1-5 or null", "confidence": 0.0-1.0}
```

---

## What changed, line by line

**Impact**
- Dropped: the print-server worked examples, the borderline-actions block, the
  JOIN/LEAVE/GRANT/REVOKE paragraph, the domain-profile preamble, the org
  description. (~5 400 chars removed.)
- Kept as one line each: scoped-edit-vs-overwrite, bulk dominance, highest-tier.
- Added: annotations named as *hints only*, per source 4.

**Blast**
- Dropped: the SIEM/signing-key worked examples, the CALIBRATION-BY-TRAIT block,
  the long disclosure-vs-metadata argument. (~5 700 chars removed.)
- Replaced the home-grown tier-5 "escape routes" with **CVSS's vulnerable-vs-
  subsequent framing**, and made a tier-5 award require a **flag in the org
  table** rather than a judgement from prose — this is the deterministic fix for
  the `recruiting list-events = 5` over-read.
- Added the sibling tool/asset lists + an explicit consistency instruction,
  targeting the v3 same-tool-different-blast defect.
