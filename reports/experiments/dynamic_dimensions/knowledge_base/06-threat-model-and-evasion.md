# Dynamic layer: threat model and evasion analysis (design v4)

This note gives the dynamic layer (the behaviour multiplier `M` in [0.7, 5], design v4) the
adversary model a security reviewer will ask for. It covers who attacks, what they know and
control, what the layer claims per adversary, what per-caller baselines cannot see, how each of
the 15 dimensions is evaded and at what cost, and which mitigations close the cheapest gaps. Threat
direction as everywhere in this repo: the MCP server and the assets behind it are protected; the
calling agent is the threat. External facts were checked on the primary sources listed in
[References](#references) (opened 2026-10-25). Engine numbers come from probes of the shipped
engine ([Probe setup](#probe-setup)). Everything else is read from the code, with file names given.

## Answers in brief

1. **The paper has no adversary model for the dynamic layer.** §3 (`main-restructured.tex`
   ~416) scopes *misuse of legitimate capabilities* whatever its origin. It says nothing about what
   an attacker knows about the layer, whether they can pace themselves, write to the baselines, or
   create identities. Every gray episode in the simulation is **non-adaptive**: none of the 10
   kinds in `normal_org_world.py` (`GRAY_KINDS`) knows the layer exists or paces itself under a
   baseline. Arp et al. list "inappropriate threat model" as pitfall P10 for learning-based
   security systems.
2. **What the layer can honestly claim:**
   - it detects *non-adaptive* misuse (runaway loops, careless scripts, big pastes);
   - it detects a careless masquerader (×4.94 in the probe);
   - it catches a hijacked agent's read-then-write in one session (×3.62);
   - it catches the first access to a sensitivity-4–5 asset by anyone, including a brand-new
     identity (×2.63 / ×3.62);
   - against a design-aware adversary it only **raises cost**: they must stay inside the caller's
     own footprint and pace, or pay at least ×3.
3. **Per-caller baselines cannot see:**
   - misuse that matches the caller's own history (traitors, mimicry; Wagner & Soto 2002);
   - harm in argument content: the layer reads only request bytes;
   - data volume in responses;
   - a caller with no history;
   - campaigns spread over several identities;
   - slow poisoning of a caller's own baseline. Kloft & Laskov show that a finite-window learner
     whose training traffic the attacker controls is poisoned with linear effort. Here every
     caller controls 100% of its own baseline.
4. **Five cheap evasions, measured on the shipped engine:**
   - **Split sessions.** Moving the write to a new session evades unsafe sequence (×3.62 → ×0.94).
   - **Fresh identity.** Its first day is free: 2,400 writes at M = 1.00, and that day becomes its
     baseline (day 2: ×0.74–0.98).
   - **Three Sybils.** They switch on the org discount for a fourth identity (×4.37 → ×1.00).
   - **Poisoned limits.** 23 inflated agent-days out of 4,523 move the learned burst limit from 13
     to 200 calls a minute. For a tool seen on fewer than 200 agent-days, one oversized request
     sets that tool's limit.
   - **Habit discount.** Raising a red flag 4–5 times on alternate days brings it under ×3.
5. **MCP revision `2026-07-28` (Current) removes the `initialize` handshake and protocol
   sessions** (SEP-2575, SEP-2567). For callers on that revision, three checks have nothing to key
   on:
   - missing handshake cannot fire;
   - session duration has no session;
   - unsafe sequence's same-session read check has no session state.

   A design-aware caller can choose the stateless revision to drop all three. Clients may support
   several revisions at once.
6. **The cheapest fixes are mitigations M1–M5** ([Mitigations](#mitigations)):
   - make red flags real fixed lines;
   - count only established, independent users toward the org discount;
   - stop treating a new `client_id` for a known user as a stranger;
   - keep the first-access floor for more than one day;
   - track sensitive reads per caller over a time window, not per session.

## What the paper says now

- **§3 Threat Model (~416).** The asset is the organisation's assets and services; servers and
  tools are assumed benign. In scope: misuse "regardless of whether the operation originates from
  benign error, excessive delegation, compromised behavior, or malicious intent". Out of scope:
  malicious servers, tool poisoning, authentication bypass, implementation vulnerabilities,
  manipulation of organisational policies, and server-to-agent attacks. The commented-out older
  text treats the agent "as a source of potentially risky requests rather than as an assumed
  adversary".
- **§4.3 / §5.3 (~814, ~888).** These still describe the persona `D·A·N` factor. They say a
  verdict "cannot be steered by text an attacker writes into an argument". That is true of `M`,
  which reads no arguments. But `M` *can* be steered by behaviour over time, because a caller
  writes its own baseline. The paper should say so.
- **v4 notes (`DYNAMIC-LAYER-V4-NOTES.md`).** Familiar behaviour lowers risk by up to 30%
  (`M ≥ 0.7`). The old text said familiar behaviour "does not reduce the static risk". The
  threat-model consequence: a perfect mimic gets a discount (×0.89 in probe E13).

## What the layer stands on

These are trust assumptions. Each is read from the code and is a precondition for any claim below.

| Assumption | Where | If it fails |
|---|---|---|
| The gateway sees all traffic to the server, and its state and logs are intact | `gateway/proxy.py`; the hash-chained log is `gateway-log/3` | Bypassing the gateway voids the layer (out of scope) |
| The caller is an OAuth-verified identity; the baseline key is SHA-256 of `issuer\|client_id\|sub` (12 hex chars) | `gateway/oauth.py`, `config.py` `Identity` | With no identity provider every caller is `anonymous` and shares one baseline: the layer is void |
| The address is the TCP peer; `X-Forwarded-For` counts only from configured trusted proxies | `http_wire.client_behind` | The caller still chooses where it connects from |
| The client name is self-reported `clientInfo` (from `initialize` or `_meta`), version dropped | `wire_log.client_info_of`, `engine.client_family` | The adversary controls it fully. The spec defines it as implementation information and gives no way to authenticate it |
| Asset, sensitivity and read/write come from the static scan and the binding. The asset is the binding's `driver`, the worst-case register row among the candidates | `gateway/framework.py` `score`, `binding/scoring.py` | A tool missing from the scan has no asset and no write, so asset, write rate, sequence and the floor do not take part. Breadth and sweep count register rows, not containers |
| Verdicts are logged and never returned. The gateway never blocks | `proxy.py` docstring | No oracle for the adversary. If an organisation gates on `R`, each block leaks one bit of `M` (Barreno et al.'s *exploratory* probing) |
| History is per caller, 90 days, folded once a day. Red-flag limits are learned from the first 30 days at 99.5% of agent-days. The org discount reads every identity's first uses over 7 days | `engine.py`, `memory.py`, `policy.py` | See [Evasion](#evasion-per-dimension) |
| Only request size is observed: no argument content and no response size | `engine.Message` | See [What per-caller baselines cannot see](#what-per-caller-baselines-cannot-see) |

## Adversary classes

The insider literature separates the **masquerader**, who steals a legitimate user's identity, from
the **traitor**, a legitimate user acting against policy with their own credentials (Salem et al.
2008). Two of the survey's observations drive the design of a per-caller layer:

- a masquerader "is unlikely to know the behavior of their victim", and profiling works if the
  history is kept secret;
- "a traitor may exhibit normal behavior and still perpetrate malicious acts".

Agents add a third case: the **hijacked agent**, the caller's own agent steered by injected
instructions. It acts with the caller's credentials, from the caller's machine, inside the
caller's session (Greshake et al. 2023). On MCP, Invariant Labs showed it on the GitHub server: a
malicious public issue led the user's agent to read private repositories and publish their
contents in a pull request on a public repository (2025-05-26).

**What the adversary knows.**
- **K0, oblivious:** does not know the gateway exists.
- **K1, knows the design:** the paper and the code are public.
- **K2, knows the victim's baseline:** a traitor knows their own; a hijacked agent inherits it
  implicitly because it *is* the victim's process.
- **K3, can write to baselines:** present while they are learned, or able to mint identities.

**What the adversary controls.**
- **P, pacing:** time and rate.
- **O, origin:** network and client.
- **I, identities:** how many.
- **L, learning window:** presence while limits and baselines are learned.

| Class | Who | Credentials | Origin vs. the victim | Knows | Controls | What the layer claims |
|---|---|---|---|---|---|---|
| **A0 Non-adaptive misuse** | runaway agent, misconfigured bot, careless script, big paste | own | own | K0 | none on purpose | **Detects**: the evaluated case (gray episodes, 70.7% caught at ×3 on average, `DIMENSION_FORMULAS.md` Simulation v4) |
| **A1c Careless masquerader** | stolen bearer token replayed from the attacker's machine | victim's | new network, script client, often off-hours, no handshake | K0–K1 | P, O | **Detects**: ×4.94 in probe E9. The MCP spec warns stolen tokens give "requests that appear legitimate" |
| **A1d Design-aware masquerader** | same token, but sends `initialize`, sets `clientInfo` to the victim's client, works the victim's hours, uses the victim's tools | victim's | only the network differs | K1 (+K2 if it saw the victim's activity) | P, O | **Raises cost only**: ×3.20 for a victim who never changes network, ×2.58 after two earlier changes, ×1.40 for a roamer (E9'). Beyond that, detection rests on what it does: new tools or assets, the floor |
| **A2 Hijacked agent** | the victim's own agent, prompt-injected or otherwise compromised | victim's | identical | usually K0 (injection written for any agent) | little P (the agent loop sets the pace) | **Partial**: unsafe sequence when the read and the write share a session (×3.62, E5'). Asset rarity and the floor when the injected task reaches assets new to the victim. Tool rarity when it needs a new tool. Oversized request for large pastes. **No claim** when the task stays inside the victim's habits (a habitual sequence is discounted to 0.30 → ×0.94) |
| **A3 Traitor** | legitimate user abusing their own access | own | own | K2, and K3 on their own baseline | P, O, L | **Limited**: the first access to a sensitive asset (at least one ×2.6–3.6 per asset per 90 days), and steps beyond about 10× their own usual or past an organisation line. **No claim** against mimicry or slow drift |
| **A4 Multi-identity (Sybil)** | A1 holding several victims' tokens, or A3 minting `client_id`s (DCR, CIMD) | many | chosen | K1–K3 | P, O, I, L | **None today, and the layer is weakened**: warm-up and the org discount reward fresh identities (E6, E7), and identities can poison the learned limits (E8). Needs mitigations M1–M3 |

On A4: Douceur (2002) shows that without a logically centralised authority, Sybil attacks are
always possible except under extreme assumptions. Here the identity provider is that authority,
so Sybil resistance is exactly as strong as its policy for issuing `client_id`s and users.

- **MCP `2025-06-18`:** clients and authorization servers SHOULD support Dynamic Client
  Registration (RFC 7591).
- **MCP `2025-11-25`:** Client ID Metadata Documents become SHOULD and DCR becomes MAY. The spec
  notes that an attacker can claim to be any client by presenting its metadata URL, and that
  authorization servers MAY use domain allowlists.
- **MCP `2026-07-28`:** DCR is deprecated.

## Coverage: which dimension defends against which class

Legend:
- **●** the adversary must accept at least ×3 to act against it;
- **◐** raises cost, or catches only some variants;
- **○** the adversary controls it at no cost;
- **—** not applicable.

"Fresh" means an identity on its first day (warm-up).

| # | Dimension | A0 | A1c | A1d | A2 | A3 | A4 (fresh) | What the adversary does to stay under it |
|---|---|---|---|---|---|---|---|---|
| 1 | Call rate | ● | ● | ◐ | ◐ | ◐ | ○ | stay under about 10.6× (his usual + 1) per hour |
| 2 | Write rate | ● | ◐ | ◐ | ◐ | ◐ | ○ | same; chunk the writes |
| 3 | Breadth | ● | ◐ | ◐ | ◐ | ◐ | ○ | stay under about 10.6× his usual of distinct assets per hour |
| 4 | Repetition | ● | ○ | ○ | ◐ | ○ | ○ | vary the tool or asset, slow down |
| 5 | Session duration | ◐ | ○ | ○ | ○ | ○ | ○ | open a new session; none exists on `2026-07-28` |
| 6 | Hour of day | ◐ | ● | ○ | ○ | ○ | ○ | act within his hours |
| 7 | Tool | ◐ | ◐ | ◐ | ● | ◐ | ○ | use only his tools; condition "new tool" by starting tools |
| 8 | Asset (with the first-access floor) | ● | ◐ | ◐ | ● | ◐ | ◐ (floor only) | use his assets; for sensitivity ≤ 3, condition by starting assets; the floor costs one alerting day per sensitive asset |
| 9 | Network | ◐ | ● | ◐ | ○ | ○ | ○ | use a /16 he uses, or target roaming victims; three Sybils discount a new /16 |
| 10 | Client | ◐ | ● | ○ | ○ | ○ | ○ | set `clientInfo` to his client |
| 11 | Burst | ● | ◐ | ◐ | ◐ | ◐ | ◐ | pace under the line; habit-condition it; poison it while it is learned |
| 12 | Sweep | ● | ◐ | ◐ | ◐ | ◐ | ◐ | at most 15 distinct assets per hour; habit-condition it |
| 13 | Oversized request | ● | ◐ | ◐ | ◐ | ◐ | ◐ | chunk; poison per-tool limits |
| 14 | Unsafe sequence | ◐ | ○ | ○ | ● | ○ | ○ | split the read and the write across sessions; read before a blind write; call a review tool before a merge |
| 15 | Missing handshake | ◐ | ● (×1.9) | ○ | ○ | ○ | ○ | send `initialize`, or speak `2026-07-28` |

Reading the table:
- The **Footprint** group (7–10) and the **first-access floor** are the only defences against A1d
  and A2.
- **Unsafe sequence** is the only one that targets A2's characteristic pattern, read sensitive
  then write elsewhere.
- **Nothing** defends against A3 mimicry or A4 on a fresh identity, except the floor and the
  organisation-wide lines.

## Evasion per dimension

**The alert lines** (probe E0; ×3 is the alert line of `DIMENSION_FORMULAS.md`):

| Score | Formula | Stays under ×3 while… | Ceiling |
|---|---|---|---|
| Any | `M = 5^(2·s1 − 1)` | `s1 < 0.8413` | |
| Excess score | `x/(x+2)` | `(today + u) / (usual + u) < 10.6` | |
| Rarity score, `c = 1` (asset, hour) | `c/(1 + 2e)` | the thing happens more than once in 10.6 days (`e > 0.094`) | ×5 |
| Rarity score, `c = 0.9` (tool, network, client) | `c/(1 + 2e)` | the thing happens more than once in 28.7 days (`e > 0.035`) | ×3.62 |

**The habit discount.** With A = 20 / 44 / 89 active days, a red flag on its own falls under ×3
once it has been raised on 1 / 2 / 4 earlier days. It stops raising `M` at all (`s ≤ 0.5`) after
9 / 18 / 36 earlier days.

**Per dimension** (E-numbers are probes):

| # | Evasion | Cost to the adversary | Measured |
|---|---|---|---|
| 1 | Pace under 10.6× usual per hour. A 90-day mean moves slowly, so going further means a boiling-frog ramp (Chan-Tin et al. 2009; Rubinstein et al. 2009) | throughput cap; nothing for a traitor with time | focused agent at about 5 calls/h: 60 calls in an hour → ×3.00, 200 → ×4.20 (E1) |
| 2 | Same as 1; split large writes | more calls | 8 × 11.5 KB issues in 30 min → ×2.33 (E10) |
| 3 | Same as 1, plus the sweep line | about 15 assets/h | |
| 4 | Vary the tool or asset; slow down | none | |
| 5 | New session | none; no sessions on `2026-07-28` | |
| 6 | Act in his hours | none for A2 and A3; low for A1 (assumed: his time zone and working hours are usually visible to an outsider. UNVERIFIED, no source) | careless thief at 02:00 → ×4.94 (E9) |
| 7 | Stay on his tools (mimicry). Or start a new tool every few days so that new tools become ordinary | the task may need a tool he never uses | |
| 8 | Stay on his assets. Or manufacture an explorer: one new sensitivity-3 asset a day | 4 alerting days, then free | new asset #1 ×4.36, #5 ×2.90, #10 ×2.09, #20 ×1.45; a sensitivity-5 asset still gets ×3.62 from the floor (E3) |
| 8 (floor) | **Pre-touch**: absorb one alerting day, then return | one day at ×4.36 per sensitive asset per 90 days | payroll: day 1 ×4.36, day 2 ×1.76, day 3 ×1.68 (E4) |
| 9 | Use a /16 he already uses, or target a roaming victim. Campaign from one /16 (org discount) | needs an exit in his ranges; Sybils | new cloud /16: ×3.20 / ×2.58 / ×1.40 by victim habit; a /16 he used once 24 days earlier → ×2.14 (E9'). After 3 Sybils: ×1.00 (E7) |
| 10 | Spoof `clientInfo` | none | |
| 11 | Pace under the line (48/min learned) | throughput | habit, alternate days: the call is ×3.96, ×3.62, ×3.36, ×3.16, **×3.00**, then ×2.52 by the 10th (E2) |
| 11–13 | Poison the limits during the 30 learning days | be present with about 0.5% of agent-days | 23 of 4,523 agent-days: burst limit 13 → 200/min. One 900 KB request among a tool's 60 agent-days → limit 900 KB (E8) |
| 12 | At most 15 assets/h = 120 in an 8-hour day. Habit discount. A policy learned from a gateway log leaves sweep off (`policy.py`: no resolved assets) | throughput | |
| 13 | Chunk under the per-tool limit | more calls | 90 KB issue → ×3.62; chunked → ×2.33 (E10) |
| 14 | Read in session A, write in session B. Read before a blind write. Call any listed review tool before merging. One counter-example per 200 sessions stops a required step from being learned (`SEQUENCE_SHARE = 0.995`) | none | ×3.62 → ×0.94 (E5') |
| 14 (habit) | A victim who habitually reads sensitive data and then writes in the same session is already discounted | none: the victim did it | sequence 0.30, ×0.94 (E5') |
| 15 | Send `initialize`, or use `2026-07-28` (no sessions, no handshake) | none | |

**Three mechanisms that create evasion paths.**

- **Warm-up rewards fresh identities.** On its first day, an identity is scored only by the checks
  that need no history (burst, sweep, oversized request, sequence, the floor). It also writes its
  own baseline (E6):
  - day 1: 2,400 writes to 15 sensitivity-3 repositories an hour, 02:00–10:00, from a cloud /16, as
    `python-requests`, with no `initialize`: M = 1.00 on every call, and no dimension took part;
  - day 1, its first read of a sensitivity-5 asset: ×3.62, the floor holds;
  - day 2, the same pattern: ×0.74–0.98, a *discount*.

  A user creates such an identity by signing in with a new `client_id`, because the key is
  `issuer|client_id|sub`.
- **The org discount counts identities, including fresh ones.** `FirstUses.add` runs whether or
  not the identity is in warm-up (`engine._origin_footprint`, `_note_first_uses`), and `others()`
  counts other identity keys, not other users. In E7, three first-day identities touched
  `hr-wiki` (sensitivity 3) once, from the same new /16. The next day, a focused agent's first
  access to both went from ×4.37 to ×1.00. The same holds for a credential-stuffing campaign:
  after its third victim, a shared egress /16 is discounted for every later victim.
- **The habit discount turns fixed lines into per-caller lines.** Burst and sweep are described as
  "one line for everyone" that backs up call rate and breadth. Under the habit discount, the line
  is conditioned per caller after 2–4 raises.

**One gap from the binding.** The asset is the binding's worst-case `driver`. Calls whose
container identifier the binder cannot resolve all map to the same driver, so breadth and sweep
count them as one asset. This is a code reading and is not yet checked on a real route.

**Detection is not free to evade.** Except via warm-up, the org discount and the protocol downgrade,
every conditioning path costs the adversary visible ×3+ events first:
- 4–5 burst alerts;
- 4 new-asset alerts;
- one floor alert per sensitive asset.

The paper can claim this cost, provided those events are reviewed. Alert fatigue is the
adversary's ally.

## What per-caller baselines cannot see

These limits are fundamental to comparing a caller with its own past. More dimensions over the same
observables do not remove them.

1. **Misuse inside the caller's own footprint and pace.** This is the mimicry attack of Wagner and
   Soto (2002) on host-based anomaly detectors, and the traitor case of Salem et al. The layer
   gives such a call `M ≤ 1`, down to ×0.7 (×0.89 in E13). Only `R_static` prices what it can do.
2. **Content-level harm in arguments.** `M` reads no arguments. A 2 KB secret in a comment, a
   backdoor in a 3 KB file write, or a destructive filter on a familiar asset all look ordinary.
   This belongs to the static per-input levels (v13) and to content inspection.
3. **Data volume in responses.** `Message.size` is the request. Over-fetching is caught 0% of the
   time in the simulation (`DIMENSION_FORMULAS.md`, open decision 4).
4. **A new caller.** There is no history, so only the history-free checks apply, and the first
   day becomes the baseline (E6).
5. **Campaigns across identities.** The layer is per caller by design, and other callers can only
   lower a score. Splitting work over N identities divides every per-caller signal by N.
6. **Poisoning one's own baseline.** Kloft and Laskov (2012) show that a finite-window online
   anomaly detector is compromised with a linear amount of injected data. Bounding the
   attacker's share ν of the traffic gives a strict bound on the attacker's gain. For a per-caller
   baseline, ν = 1 by construction. Only organisation-wide quantities (the red-flag lines and the
   org discount) have ν < 1, and only while identities cannot be multiplied. ANTIDOTE (Rubinstein
   et al. 2009) shows the boiling-frog variant against periodically retrained detectors, and robust
   statistics (median and MAD instead of mean and variance) as the defence.
7. **Harm through another channel.** For example, the agent reads data through MCP and leaks it
   elsewhere.

## Out of scope for the dynamic layer

To state explicitly in the paper:
- items 1–7 above;
- bypassing or compromising the gateway, the identity provider, or the static artefacts (scan,
  register sensitivity, binding): they are the trusted computing base;
- attacks on the layer's availability. Opening more than 50,000 sessions evicts the oldest
  (`max_sessions`), causing missing-handshake false alarms for others. Flooding the daily review
  list with ×3.6 agent-days from Sybils is the other case. Note both as known limits;
- the paper's existing exclusions: malicious servers, tool poisoning, authentication bypass,
  server-to-agent attacks.

## Mitigations

None of these is implemented. Each needs an ablation on the five simulated organisations
(false alarms first, as in `DIMENSION_FORMULAS.md`) and an adaptive test
([Evaluation to add](#evaluation-to-add)).

| # | Mitigation | Closes | Trade-off |
|---|---|---|---|
| **M1** | **Red flags as fixed lines.** The organisation writes the limits, and learning only *proposes* them. If learned: each identity contributes at most one agent-day (or its median) to the quantile; a tool needs at least 200 agent-days for its own limit, otherwise the global limit applies (below 200, the 99.5% quantile *is* the maximum); robust statistics; growth on re-learning capped (for example +10% per cycle) and signed off. The habit discount on burst and sweep stops at a floor (for example 0.75, ×2.1), so the line stays a line | E8 poisoning, E2 conditioning, boiling frog | slightly more alerts for habitual bots; an organisation must own its numbers |
| **M2** | **Org discount for independent, established users only.** Count others only after their warm-up and onboarding, by user (`sub`) rather than identity. Require at least max(3, a fraction of the active agents). Discount a new network only inside org-owned ranges (VPN pools, office egress). Log every discounted score as discounted | E7, credential-stuffing campaigns | a real VPN change outside the allowlist is no longer discounted: list the ranges |
| **M3** | **No stranger discount for a known user.** A new `issuer\|client_id\|sub` whose `sub` is known is scored against the user's pooled baseline, and the new `client_id` is a Footprint event of that user. A truly new user starts from an organisation or role prior instead of `M = 1`. No familiar discount (`M ≥ 1`) and a write-rate line until onboarding ends. Shrink the first days' counts toward the org median so day 1 cannot pre-shape the baseline. At the identity provider: allowlist CIMD domains and limit DCR (both spec-allowed), and rate-limit new `client_id`s per user | E6, A4 | new hires see more alerts in week one; needs the user claim from the token (already parsed) |
| **M4** | **A floor that lasts.** The floor applies until an asset has been touched on at least k distinct days (for example 3), decaying 0.9 → 0.8 → 0.7, instead of vanishing after one day. Keep it never discounted. Count "touched" per user, not per identity. Optionally a lower floor for sensitivity 3 | E4 pre-touch, E3 explorers on sensitivity-3 assets | more alerts on genuine first weeks on a sensitive repository |
| **M5** | **Sequences per caller, not per session.** Keep sensitive reads per caller for a window (for example 1 h and 24 h) across sessions and across `2026-07-28` traffic, which has no sessions. Do not habit-discount "read sensitive → write to a lower-sensitivity or public asset" (the exfiltration direction of the GitHub MCP attack); this needs an exposure attribute in the register | E5' split, the A2 habit gap, the stateless protocol | more sequence alerts for developers who copy between repositories |
| **M6** | **Origin signals the adversary cannot set.** Sender-constrained tokens (DPoP, RFC 9449, which "allows for the detection of replay attacks"; or mTLS) make a stolen bearer token useless elsewhere, which is stronger than network rarity. Base the client dimension on the authenticated `client_id`; treat `clientInfo` changes as a weaker signal. Add the protocol revision to the client footprint, so a caller dropping to the stateless revision is a Footprint event | A1d, the protocol downgrade | needs identity-provider support; DPoP is deployment work outside the gateway |
| **M7** | **No familiar discount where it matters.** `M ≥ 1` for writes or for `R_static ≥ 4` | the E13 mimicry discount | loses part of the reward for routine work; ablation |
| **M8** | **Make drift visible.** A per-caller "boiling frog" check: his usual today against his usual 30 days ago, per Cadence dimension, as a review item. Kloft and Laskov's protection is a bounded false-positive rate on the attacker's traffic, which this approximates | slow drift (limit 6) | one more review signal; uses only his own history |
| **M9** | **Review hygiene.** Keep the gateway observe-only, or never reveal the reason when blocking. Deduplicate the daily list per user so Sybils cannot crowd it | oracle probing, list flooding | |

## Evaluation to add

What an A* reviewer will look for (Sommer & Paxson 2010; Arp et al. 2022, P9 lab-only evaluation
and P10 inappropriate threat model): the detector against an adversary who knows it.

- **New gray kinds in `normal_org_world.py`**, each a budgeted adversary:
  - `paced_export`: bulk export at about 9× his usual, under 15 assets/h;
  - `aware_thief`: A1d, with victims of different network habits;
  - `split_copy`: a cross copy split across sessions;
  - `injected_flow`: A2, read a private repository, then write to a public one, in one session,
    with and without a habit;
  - `explorer_conditioning`, `flag_conditioning`;
  - `fresh_identity`: day-1 abuse, and day-2 abuse on the pre-shaped baseline;
  - `sybil_discount`;
  - `limit_poisoning`: inflated agent-days during the 30 learning days.
- **Metrics:**
  - attack throughput while staying under ×3 (calls, distinct assets, request bytes per day);
  - alerts the adversary absorbs while conditioning, and days spent conditioning;
  - the false-alarm cost of each mitigation on ordinary agent-days.
- **Report the gap honestly:** the current catch rates are for non-adaptive misuse. The adaptive
  numbers are what the paper can claim against an attacker.

## Paste-ready text for §3

```latex
\paragraph{Adversary of the dynamic layer.}
The runtime layer compares each invocation with the calling identity's own
history. We consider four sources of runtime misuse: non-adaptive misuse
(erroneous or runaway agents, careless scripts), a masquerader replaying a
stolen credential, an agent hijacked through injected instructions that acts
with its principal's credentials and session~\cite{greshake2023indirect}, and a
traitor abusing its own access~\cite{salem2008survey}. The layer is designed to
detect the first, to raise the cost of the second and third, and to flag a
first access to a sensitive asset by any of them. It makes no claim against an
adversary who confines itself to the identity's own footprint and pace, the
mimicry setting of anomaly detection~\cite{wagner2002mimicry}, nor against
harm carried in argument content, which the layer does not read. Because each
identity controls the traffic its baseline is learned from, slow poisoning of
that baseline is possible~\cite{kloft2012security,rubinstein2009antidote}; the
organization-wide red-flag lines bound it only if one identity's share of the
traffic that sets them is bounded, which requires that identities cannot be
multiplied at will~\cite{douceur2002sybil}. We therefore assume verified caller
identities issued under the organization's control and a gateway that observes
all traffic to the server.
```

## Probe setup

All probes ran the shipped engine (`src/mcp_security/behaviour/engine.py`, design v4) with
`BehaviourConfig(burst_per_minute=48, many_assets_per_hour=15, request_limit_by_tool=
{create_issue: 12 KB, get_file_contents: 1 KB})`. These are the learned values of the main
simulated organisation, rounded.

- **The victim** (a focused agent): 44 weekdays of history. Each day, one initialised session with
  40 calls between 09:00 and 17:00, one every 12 minutes (about 5 in any hour). Two repositories
  of sensitivity 2. Three tools, `create_issue` being the write. One office /16, one client.
- **Variants:**
  - "habit": a sensitivity-5 read before that day's writes, in the same session;
  - "clean": the sensitivity-5 read in its own read-only session;
  - "roamer": a new /16 every third day after onboarding;
  - "two earlier changes": two new /16s.
- **Scripts**, in the session scratchpad, not in the repository:
  `/tmp/claude-343913582/-home-ovadyat-MCP/d6821e4d-e280-4911-be08-63b780ec3aaa/scratchpad/evasion_probe.py`
  and `evasion_probe2.py`; output in the `.out` files next to them.
- **Caveat:** these are single-agent mechanism checks, not rates. Rates need the adaptive gray
  kinds above. E1–E10 and E13 are the probe functions; E5' and E9' are the second-round variants,
  which replace E5 (whose history had the habit built in) and extend E9.

## References

All opened on 2026-10-25. **V** means verified on the page linked. No reference here is
unverified. One claim in the text is marked UNVERIFIED: that an outsider can usually see the
victim's time zone and working hours (row 6 of the evasion table). It is a reasoned assumption,
not a sourced fact.

- **V** D. Wagner, P. Soto. "Mimicry attacks on host-based intrusion detection systems." ACM
  CCS 2002. [doi:10.1145/586110.586145](https://doi.org/10.1145/586110.586145). The abstract
  defines the mimicry attack as letting "a sophisticated attacker … cloak their intrusion to avoid
  detection by the IDS".
- **V** B. I. P. Rubinstein, B. Nelson, L. Huang, A. D. Joseph, S. Lau, S. Rao, N. Taft,
  J. D. Tygar. "ANTIDOTE: understanding and defending against poisoning of anomaly detectors."
  IMC 2009, pp. 1–14. [doi:10.1145/1644893.1644895](https://doi.org/10.1145/1644893.1644895);
  [PDF](https://people.eecs.berkeley.edu/~tygar/papers/SML/IMC.2009.pdf). It covers the Boiling Frog
  scheme against weekly retraining, and the PCA-GRID and Laplace-threshold defence built on robust
  statistics (median, MAD).
- **V** M. Kloft, P. Laskov. "Security Analysis of Online Centroid Anomaly Detection." JMLR
  13(118):3681–3724, 2012. [jmlr.org](https://jmlr.org/papers/v13/kloft12b.html). Finite window:
  "an attacker can easily compromise a learning algorithm by using only a linear amount of
  injected data unless additional constraints are imposed".
- **V** M. Barreno, B. Nelson, R. Sears, A. D. Joseph, J. D. Tygar. "Can machine learning be
  secure?" ASIACCS 2006. [doi:10.1145/1128817.1128824](https://doi.org/10.1145/1128817.1128824).
  "Causative attacks alter the training process through influence over the training data.
  Exploratory attacks … use other techniques, such as probing the learner or offline analysis".
- **V** E. Chan-Tin, D. Feldman, N. Hopper, Y. Kim. "The Frog-Boiling Attack: Limitations of
  Anomaly Detection for Secure Network Coordinate Systems." SecureComm 2009, LNICST,
  pp. 448–458. [doi:10.1007/978-3-642-05284-2_26](https://doi.org/10.1007/978-3-642-05284-2_26).
  Small steps that stay within the outlier threshold, made stronger with a Sybil attack.
- **V** M. Ben Salem, S. Hershkop, S. J. Stolfo. "A Survey of Insider Attack Detection Research."
  In *Insider Attack and Cyber Security*, Advances in Information Security 39, Springer 2008,
  pp. 69–90. [doi:10.1007/978-0-387-77322-3_5](https://doi.org/10.1007/978-0-387-77322-3_5).
  It distinguishes masqueraders from traitors; the quotes above are from its introduction.
- **V** M. Schonlau, W. DuMouchel, W.-H. Ju, A. F. Karr, M. Theus, Y. Vardi. "Computer Intrusion:
  Detecting Masquerades." *Statistical Science* 16(1):58–74, 2001.
  [doi:10.1214/ss/998929476](https://doi.org/10.1214/ss/998929476). The classic per-user profile
  test against masqueraders.
- **V** J. R. Douceur. "The Sybil Attack." IPTPS 2002, LNCS 2429, pp. 251–260.
  [doi:10.1007/3-540-45748-8_24](https://doi.org/10.1007/3-540-45748-8_24).
- **V** R. Sommer, V. Paxson. "Outside the Closed World: On Using Machine Learning for Network
  Intrusion Detection." IEEE S&P 2010, pp. 305–316.
  [doi:10.1109/SP.2010.25](https://doi.org/10.1109/SP.2010.25).
- **V** D. Arp et al. "Dos and Don'ts of Machine Learning in Computer Security." USENIX Security
  2022. [usenix.org](https://www.usenix.org/conference/usenixsecurity22/presentation/arp). Pitfalls
  P9 lab-only evaluation and P10 inappropriate threat model.
- **V** K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, M. Fritz. "Not What You've
  Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt
  Injection." AISec 2023. [doi:10.1145/3605764.3623985](https://doi.org/10.1145/3605764.3623985).
- **V** M. Milanta, L. Beurer-Kellner (Invariant Labs). "GitHub MCP Exploited: Accessing private
  repositories via MCP." Blog, 2025-05-26.
  [invariantlabs.ai](https://invariantlabs.ai/blog/mcp-github-vulnerability).
- **V** D. Fett, B. Campbell, J. Bradley, T. Lodderstedt, M. Jones, D. Waite. RFC 9449, "OAuth 2.0
  Demonstrating Proof of Possession (DPoP)," September 2023.
  [rfc-editor.org](https://www.rfc-editor.org/rfc/rfc9449.html).
- **V** MCP specification:
  - [Authorization 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization):
    DCR SHOULD; the Token Theft section;
  - [Authorization 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization):
    CIMD SHOULD, DCR MAY, CIMD impersonation and trust policies;
  - [Lifecycle 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle):
    `clientInfo`;
  - [Security Best Practices 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices):
    "MCP Servers MUST NOT use sessions for authentication"; bind sessions as
    `<user_id>:<session_id>`, which the gateway already does;
  - [Changelog 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/changelog):
    SEP-2567, SEP-2575, DCR deprecated;
  - [Versioning](https://modelcontextprotocol.io/specification/versioning): `2026-07-28` is
    Current; multiple versions MAY be supported.

**BibTeX for the paper** (`refs.bib` has none of these yet; `mcp2026spec` already exists):

```bibtex
@inproceedings{wagner2002mimicry,
  author = {Wagner, David and Soto, Paolo}, year = {2002},
  title = {Mimicry Attacks on Host-Based Intrusion Detection Systems},
  booktitle = {Proceedings of the ACM Conference on Computer and Communications Security (CCS)},
  doi = {10.1145/586110.586145}}
@inproceedings{rubinstein2009antidote,
  author = {Rubinstein, Benjamin I. P. and Nelson, Blaine and Huang, Ling and Joseph, Anthony D.
            and Lau, Shing-hon and Rao, Satish and Taft, Nina and Tygar, J. D.}, year = {2009},
  title = {{ANTIDOTE}: Understanding and Defending against Poisoning of Anomaly Detectors},
  booktitle = {Proceedings of the 9th ACM SIGCOMM Conference on Internet Measurement (IMC)},
  pages = {1--14}, doi = {10.1145/1644893.1644895}}
@article{kloft2012security,
  author = {Kloft, Marius and Laskov, Pavel}, year = {2012},
  title = {Security Analysis of Online Centroid Anomaly Detection},
  journal = {Journal of Machine Learning Research}, volume = {13}, number = {118},
  pages = {3681--3724}}
@incollection{salem2008survey,
  author = {Ben Salem, Malek and Hershkop, Shlomo and Stolfo, Salvatore J.}, year = {2008},
  title = {A Survey of Insider Attack Detection Research},
  booktitle = {Insider Attack and Cyber Security}, series = {Advances in Information Security},
  volume = {39}, pages = {69--90}, publisher = {Springer}, doi = {10.1007/978-0-387-77322-3_5}}
@inproceedings{douceur2002sybil,
  author = {Douceur, John R.}, year = {2002}, title = {The {Sybil} Attack},
  booktitle = {Peer-to-Peer Systems (IPTPS)}, series = {LNCS}, volume = {2429},
  pages = {251--260}, doi = {10.1007/3-540-45748-8_24}}
@inproceedings{greshake2023indirect,
  author = {Greshake, Kai and Abdelnabi, Sahar and Mishra, Shailesh and Endres, Christoph
            and Holz, Thorsten and Fritz, Mario}, year = {2023},
  title = {Not What You've Signed Up For: Compromising Real-World {LLM}-Integrated Applications
           with Indirect Prompt Injection},
  booktitle = {Proceedings of the ACM Workshop on Artificial Intelligence and Security (AISec)},
  doi = {10.1145/3605764.3623985}}
```
