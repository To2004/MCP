# Independent Scoring - Slack MCP

## Approach

Slack risk scoring follows a persona-context multiplier model on top of an
intrinsic per-tool capability score. Each tool has a base danger profile
(read vs. write, scoped vs. bulk, identity-bearing vs. anonymous), but the
realized impact depends on which persona's workspace the agent is acting in.
The same `slack_post_message` call is a Medium-tier nuisance in a Public
channel but a Critical impersonation event in a Management channel where
the recipient assumes the sender is an authenticated exec. Scoring is
grounded in NIST SP 800-30 (likelihood x impact) for severity bands and
NIST SP 800-122 / GDPR for PII weighting: bulk identifier reads
(`slack_get_users`) outrank per-record reads (`slack_get_user_profile`)
because the breach class is "directory exfiltration", not "lookup".

The cube view captures the three-axis interaction: Tool x Asset x Persona.
Notable shapes: write tools climb sharply when the persona is high-trust
(Management, HR) because the posted content carries that persona's
authority. Read tools climb sharply when the persona handles sensitive
data (HR over Public) regardless of write capability. `add_reaction` is
deceptively low-risk in isolation but becomes a covert-channel signaling
primitive in a multi-agent or insider-threat context, which is why it is
not scored as N/A.

## Scoring rubric

| Level | Score | Meaning |
|-------|-------|---------|
| Critical | 4 | PII exfiltration; mass-DM social-engineering surface; impersonation against execs |
| High | 3 | Bulk private message read; targeted post-as-user; persona escalation |
| Medium | 2 | Partial private data read; messages to a single channel |
| Low | 1 | Public channels / workspace metadata only |
| N/A | 0 | Tool genuinely does not apply to this asset |

## 1. Tool Ranking (avg danger per tool)

### Empty structure (user's scoring blank)

| Rank | Tool | Risk | Reasoning |
|------|------|------|-----------|
| 1 | (blank) | (blank) | (blank) |
| 2 | (blank) | (blank) | (blank) |
| 3 | (blank) | (blank) | (blank) |
| 4 | (blank) | (blank) | (blank) |
| 5 | (blank) | (blank) | (blank) |
| 6 | (blank) | (blank) | (blank) |
| 7 | (blank) | (blank) | (blank) |
| 8 | (blank) | (blank) | (blank) |

### Agent's independent scoring

| Rank | Tool | Risk | Reasoning |
|------|------|------|-----------|
| 1 | slack_get_users | Critical (4) | Bulk PII directory dump - emails, phones, titles for the entire workforce in one call, classic GDPR/NIST 800-122 mass-identifier breach. |
| 2 | slack_post_message | Critical (4) | Identity-bearing write that enables impersonation, phishing, and command injection against humans in any channel the bot can reach. |
| 3 | slack_reply_to_thread | High (3) | Identity-bearing write inside an existing trust context, slightly narrower blast radius than a fresh post but higher contextual credibility. |
| 4 | slack_get_channel_history | High (3) | Bulk read of an entire channel's messages, exposing private conversations, secrets-in-chat, and conversational PII. |
| 5 | slack_get_thread_replies | Medium (2) | Scoped read of one thread - sensitive but bounded in volume compared to full-channel history. |
| 6 | slack_get_user_profile | Medium (2) | Per-record PII read, sensitive individually but not a mass breach unless iterated. |
| 7 | slack_list_channels | Low (1) | Workspace metadata enumeration, useful as reconnaissance but no message content. |
| 8 | slack_add_reaction | Low (1) | Single-emoji write, low intrinsic damage but a viable covert-channel signal between collaborating agents. |

## 2. Persona / Asset-Category Ranking (6 personas)

### Empty structure (user's scoring blank)

| Rank | Persona | Risk | Reasoning |
|------|---------|------|-----------|
| 1 | (blank) | (blank) | (blank) |
| 2 | (blank) | (blank) | (blank) |
| 3 | (blank) | (blank) | (blank) |
| 4 | (blank) | (blank) | (blank) |
| 5 | (blank) | (blank) | (blank) |
| 6 | (blank) | (blank) | (blank) |

### Agent's independent scoring

| Rank | Persona | Risk | Reasoning |
|------|---------|------|-----------|
| 1 | Management | Critical (4) | Exec-level impersonation surface, wire-transfer-grade phishing payoff, and access to strategic decisions in private channels. |
| 2 | HR | Critical (4) | Employee records, salary discussions, terminations, and concentrated PII make any read or write catastrophic under GDPR / employment law. |
| 3 | Supervisor | High (3) | Line-manager authority for social engineering of direct reports, plus visibility into performance and 1:1 channels. |
| 4 | Technical | High (3) | Engineering / on-call channels carry secrets, credentials, and incident response context that enables lateral movement. |
| 5 | Researcher | Medium (2) | Research IP and pre-publication data are sensitive but rarely include PII or operational credentials. |
| 6 | Public | Low (1) | Open-to-all-employees content is by definition low-confidentiality; main risk is reputational spam. |

## 3. Asset Ranking (4 assets)

### Empty structure (user's scoring blank)

| Rank | Asset | Risk | Reasoning |
|------|-------|------|-----------|
| 1 | (blank) | (blank) | (blank) |
| 2 | (blank) | (blank) | (blank) |
| 3 | (blank) | (blank) | (blank) |
| 4 | (blank) | (blank) | (blank) |

### Agent's independent scoring

| Rank | Asset | Risk | Reasoning |
|------|-------|------|-----------|
| 1 | User PII | Critical (4) | Directly regulated under GDPR / NIST 800-122; mass exposure triggers breach notification obligations regardless of persona. |
| 2 | Private Channel Messages | High (3) | Contains negotiation, strategy, secrets-in-chat, and personal disclosures with strong confidentiality expectation. |
| 3 | Public Channel Messages | Medium (2) | Lower confidentiality but still a write surface for impersonation and a read surface for org reconnaissance. |
| 4 | Team / Workspace Metadata | Low (1) | Channel names and counts are useful reconnaissance but carry no message content or PII directly. |

## 4. Persona x Asset x Tool cube

For each persona, the 4 assets x 8 tools sub-matrix is shown. Each cell is
the realized risk of invoking that tool against that asset within that
persona's workspace. N/A means the tool does not interact with that asset
class (e.g. `slack_list_channels` against User PII).

### Management

#### Empty structure (user's scoring blank)

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | (blank) | (blank) | (blank) | (blank) |
| slack_get_thread_replies | (blank) | (blank) | (blank) | (blank) |
| slack_get_user_profile | (blank) | (blank) | (blank) | (blank) |
| slack_post_message | (blank) | (blank) | (blank) | (blank) |
| slack_reply_to_thread | (blank) | (blank) | (blank) | (blank) |
| slack_get_users | (blank) | (blank) | (blank) | (blank) |
| slack_list_channels | (blank) | (blank) | (blank) | (blank) |
| slack_add_reaction | (blank) | (blank) | (blank) | (blank) |

#### Agent's independent scoring

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | N/A (0) | Critical (4) | Medium (2) | N/A (0) |
| slack_get_thread_replies | N/A (0) | High (3) | Medium (2) | N/A (0) |
| slack_get_user_profile | High (3) | N/A (0) | N/A (0) | N/A (0) |
| slack_post_message | N/A (0) | Critical (4) | Critical (4) | N/A (0) |
| slack_reply_to_thread | N/A (0) | Critical (4) | High (3) | N/A (0) |
| slack_get_users | Critical (4) | N/A (0) | N/A (0) | Medium (2) |
| slack_list_channels | N/A (0) | N/A (0) | N/A (0) | Medium (2) |
| slack_add_reaction | N/A (0) | Medium (2) | Low (1) | N/A (0) |

Reasoning: exec impersonation makes every write a Critical event in private
channels; the read side is dominated by strategic confidentiality.

### HR

#### Empty structure (user's scoring blank)

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | (blank) | (blank) | (blank) | (blank) |
| slack_get_thread_replies | (blank) | (blank) | (blank) | (blank) |
| slack_get_user_profile | (blank) | (blank) | (blank) | (blank) |
| slack_post_message | (blank) | (blank) | (blank) | (blank) |
| slack_reply_to_thread | (blank) | (blank) | (blank) | (blank) |
| slack_get_users | (blank) | (blank) | (blank) | (blank) |
| slack_list_channels | (blank) | (blank) | (blank) | (blank) |
| slack_add_reaction | (blank) | (blank) | (blank) | (blank) |

#### Agent's independent scoring

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | N/A (0) | Critical (4) | Medium (2) | N/A (0) |
| slack_get_thread_replies | N/A (0) | Critical (4) | Medium (2) | N/A (0) |
| slack_get_user_profile | Critical (4) | N/A (0) | N/A (0) | N/A (0) |
| slack_post_message | N/A (0) | Critical (4) | High (3) | N/A (0) |
| slack_reply_to_thread | N/A (0) | Critical (4) | Medium (2) | N/A (0) |
| slack_get_users | Critical (4) | N/A (0) | N/A (0) | Medium (2) |
| slack_list_channels | N/A (0) | N/A (0) | N/A (0) | Medium (2) |
| slack_add_reaction | N/A (0) | Medium (2) | Low (1) | N/A (0) |

Reasoning: HR carries the densest PII per message; reads dominate the
risk profile and writes can spoof termination or comp decisions.

### Public

#### Empty structure (user's scoring blank)

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | (blank) | (blank) | (blank) | (blank) |
| slack_get_thread_replies | (blank) | (blank) | (blank) | (blank) |
| slack_get_user_profile | (blank) | (blank) | (blank) | (blank) |
| slack_post_message | (blank) | (blank) | (blank) | (blank) |
| slack_reply_to_thread | (blank) | (blank) | (blank) | (blank) |
| slack_get_users | (blank) | (blank) | (blank) | (blank) |
| slack_list_channels | (blank) | (blank) | (blank) | (blank) |
| slack_add_reaction | (blank) | (blank) | (blank) | (blank) |

#### Agent's independent scoring

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | N/A (0) | N/A (0) | Low (1) | N/A (0) |
| slack_get_thread_replies | N/A (0) | N/A (0) | Low (1) | N/A (0) |
| slack_get_user_profile | Medium (2) | N/A (0) | N/A (0) | N/A (0) |
| slack_post_message | N/A (0) | N/A (0) | Medium (2) | N/A (0) |
| slack_reply_to_thread | N/A (0) | N/A (0) | Medium (2) | N/A (0) |
| slack_get_users | High (3) | N/A (0) | N/A (0) | Low (1) |
| slack_list_channels | N/A (0) | N/A (0) | N/A (0) | Low (1) |
| slack_add_reaction | N/A (0) | N/A (0) | Low (1) | N/A (0) |

Reasoning: writes are spam-tier; the persistent risk is bulk PII via
`slack_get_users` which sees the whole workspace regardless of persona.

### Supervisor

#### Empty structure (user's scoring blank)

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | (blank) | (blank) | (blank) | (blank) |
| slack_get_thread_replies | (blank) | (blank) | (blank) | (blank) |
| slack_get_user_profile | (blank) | (blank) | (blank) | (blank) |
| slack_post_message | (blank) | (blank) | (blank) | (blank) |
| slack_reply_to_thread | (blank) | (blank) | (blank) | (blank) |
| slack_get_users | (blank) | (blank) | (blank) | (blank) |
| slack_list_channels | (blank) | (blank) | (blank) | (blank) |
| slack_add_reaction | (blank) | (blank) | (blank) | (blank) |

#### Agent's independent scoring

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | N/A (0) | High (3) | Low (1) | N/A (0) |
| slack_get_thread_replies | N/A (0) | High (3) | Low (1) | N/A (0) |
| slack_get_user_profile | High (3) | N/A (0) | N/A (0) | N/A (0) |
| slack_post_message | N/A (0) | High (3) | Medium (2) | N/A (0) |
| slack_reply_to_thread | N/A (0) | High (3) | Medium (2) | N/A (0) |
| slack_get_users | Critical (4) | N/A (0) | N/A (0) | Low (1) |
| slack_list_channels | N/A (0) | N/A (0) | N/A (0) | Low (1) |
| slack_add_reaction | N/A (0) | Medium (2) | Low (1) | N/A (0) |

Reasoning: 1:1 channels and direct-report visibility make impersonation
both believable and coercive; reads carry performance review content.

### Researcher

#### Empty structure (user's scoring blank)

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | (blank) | (blank) | (blank) | (blank) |
| slack_get_thread_replies | (blank) | (blank) | (blank) | (blank) |
| slack_get_user_profile | (blank) | (blank) | (blank) | (blank) |
| slack_post_message | (blank) | (blank) | (blank) | (blank) |
| slack_reply_to_thread | (blank) | (blank) | (blank) | (blank) |
| slack_get_users | (blank) | (blank) | (blank) | (blank) |
| slack_list_channels | (blank) | (blank) | (blank) | (blank) |
| slack_add_reaction | (blank) | (blank) | (blank) | (blank) |

#### Agent's independent scoring

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | N/A (0) | Medium (2) | Low (1) | N/A (0) |
| slack_get_thread_replies | N/A (0) | Medium (2) | Low (1) | N/A (0) |
| slack_get_user_profile | Medium (2) | N/A (0) | N/A (0) | N/A (0) |
| slack_post_message | N/A (0) | Medium (2) | Medium (2) | N/A (0) |
| slack_reply_to_thread | N/A (0) | Medium (2) | Medium (2) | N/A (0) |
| slack_get_users | High (3) | N/A (0) | N/A (0) | Low (1) |
| slack_list_channels | N/A (0) | N/A (0) | N/A (0) | Low (1) |
| slack_add_reaction | N/A (0) | Low (1) | Low (1) | N/A (0) |

Reasoning: pre-publication IP and ongoing experiment data dominate the
risk; PII is sparse, mostly contained in user profiles.

### Technical

#### Empty structure (user's scoring blank)

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | (blank) | (blank) | (blank) | (blank) |
| slack_get_thread_replies | (blank) | (blank) | (blank) | (blank) |
| slack_get_user_profile | (blank) | (blank) | (blank) | (blank) |
| slack_post_message | (blank) | (blank) | (blank) | (blank) |
| slack_reply_to_thread | (blank) | (blank) | (blank) | (blank) |
| slack_get_users | (blank) | (blank) | (blank) | (blank) |
| slack_list_channels | (blank) | (blank) | (blank) | (blank) |
| slack_add_reaction | (blank) | (blank) | (blank) | (blank) |

#### Agent's independent scoring

| Tool \\ Asset | User PII | Private Msgs | Public Msgs | Metadata |
|----|----|----|----|----|
| slack_get_channel_history | N/A (0) | High (3) | Low (1) | N/A (0) |
| slack_get_thread_replies | N/A (0) | High (3) | Low (1) | N/A (0) |
| slack_get_user_profile | Medium (2) | N/A (0) | N/A (0) | N/A (0) |
| slack_post_message | N/A (0) | High (3) | Medium (2) | N/A (0) |
| slack_reply_to_thread | N/A (0) | High (3) | Medium (2) | N/A (0) |
| slack_get_users | High (3) | N/A (0) | N/A (0) | Medium (2) |
| slack_list_channels | N/A (0) | N/A (0) | N/A (0) | Medium (2) |
| slack_add_reaction | N/A (0) | Medium (2) | Low (1) | N/A (0) |

Reasoning: on-call channels routinely contain credentials, tokens, and
incident war-room context; writes can trigger fake incidents or coax
operators into running adversary commands.

## Notes

### Why persona context matters

Persona context matters because Slack is an identity-bearing channel: the
recipient assumes the message carries the sender persona's authority. A
write in Management is not merely "a write" - it is "a write that everyone
will treat as if it came from a VP". This is why the same `slack_post_message`
tool spans Medium (Public) to Critical (Management, HR, in private channels)
across the cube. The framework would dramatically under-score Slack if it
treated tools as persona-agnostic, and would over-score it if it treated
all personas as equally privileged. The persona axis is the difference
between a CVSS-style fixed score and an environment-aware risk score, which
is exactly the gap a defense-oriented framework is meant to close.

A consequence of this model is that the same physical tool deserves
different rate limits, approval thresholds, and audit verbosity per
persona. A runtime gate that treats `slack_post_message` identically across
all personas will either be too permissive in Management or too restrictive
in Public; a persona-aware gate can right-size both.

### Impersonation risk

Impersonation is the dominant write risk. Wire-transfer and credential-phish
patterns observed in BEC (business email compromise) incidents map directly
to `slack_post_message` and `slack_reply_to_thread` when the bot is acting
under a high-trust persona. The threading variant is arguably worse than
fresh posts in adversarial settings because it inherits the thread's
pre-existing trust context and is less likely to be flagged as out-of-band;
victims do not re-validate sender identity on a reply the way they might
on a cold message.

Impersonation risk also compounds with read tools: `slack_get_channel_history`
is what makes a subsequent `slack_post_message` convincing, because the
attacker can pattern-match the persona's writing style, in-jokes, and
project context. Read-then-write tool chains should therefore be scored
higher than the sum of their parts under a sequence-aware policy.

### Is `slack_add_reaction` really only Low?

On `slack_add_reaction`: in isolation it is Low. The reason it is not N/A
is the covert-channel use case. A reaction is a binary signal visible to
all members of a channel and is rarely audited; two collaborating agents
(or an insider plus an agent) can encode information through reaction
patterns at low bandwidth but with high evasion. Multi-agent threat models
should flag any write primitive, even a single emoji. A defensible
counter-argument is that a sophisticated covert channel needs many
reactions to carry meaningful payload, so the rate-limit gate, not the
per-call gate, is the right control surface. Either way, scoring it N/A
would be a mistake.

A second subtlety: reactions can act as a social-engineering primitive
on their own. A thumbs-up from an exec persona on a malicious link posted
by another agent confers implicit endorsement and is enough to flip
human-in-the-loop verification in many shops. Under a Management persona
this argues for Medium, not Low, in private channels - which is how the
cube scores it.

### Bulk vs. per-message reads

`slack_get_users` is the highest-impact read on the entire surface because
it returns the full workforce directory in one call - this is a directory
exfiltration class, not a per-record PII access. NIST SP 800-122 and GDPR
both treat bulk identifier sets as categorically more sensitive than
isolated records because aggregation enables linkability across systems
(LinkedIn enrichment, credential-stuffing target lists, social graph
reconstruction).

`slack_get_user_profile` is per-record and lower-impact unless iterated.
A defense framework should treat repeated `slack_get_user_profile` calls
as approaching `slack_get_users` risk asymptotically; the per-call score
is Medium but the session-level score should escalate after some threshold
of distinct user IDs queried.

`slack_get_channel_history` is bulk in the message dimension but scoped
to one channel; its risk is therefore conditioned on the sensitivity of
that channel (high in HR / Management private channels, low in Public).
The framework should preserve this distinction rather than collapsing
all reads into one tier - this is precisely why the cube and not the
flat tool ranking is the authoritative view.

### Asset-vs-persona override case

The Public persona's elevated `slack_get_users` score (High, not Low) is
load-bearing: even when the persona itself is low-trust, the user list is
workspace-wide and not partitioned by persona. This is a case where the
asset's intrinsic sensitivity overrides the persona multiplier. Any
purely multiplicative model (risk = persona_weight x tool_weight) would
mis-score this cell; the cube is therefore not a pure outer product and
needs explicit per-cell judgment for cross-persona assets like the user
directory and workspace metadata.
