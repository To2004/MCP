# Dynamic layer v5: design specification

This spec brings the six Part A area designs, the v5 calibration note and a four-reviewer pass
together into one design for v5 of the dynamic layer. The MCP server is the protected asset, and
calling agents are the threat. v5 keeps the 15 paper dimensions in their three groups and keeps
s1, s2 and d*; it prices every dimension by one rule (commonness, with records ranked across the
organisation), and it states a false-alarm bound on agent-days.

**Revision 2 (2026-10-25)** applies the four review reports. What changed, finding by finding, is
in the [Review log](#review-log) at the end. Revision 1 is kept in the session scratchpad
(`rev1_backup/v5-design-spec.md`, path in the References). The implementation batches are in
[v5-implementation-plan.md](v5-implementation-plan.md).

## Status and ground rules

- **Design phase.** This spec changes no code. Probe scripts live in `probes/` (see
  [probes/README.md](probes/README.md)).
- **Numbers.** Every number is from a **development world**: seeds {1, 2, 7, 11, 12, 21, 31, 41}
  and the five existing organisations, which are burnt. Numbers from arm S5 or O1-O3 are labelled
  "development world, calibration stage on v4 scores". They come from v4 engine vectors with
  oracle simulator inputs, so they are **not v5 numbers** and none goes into the paper. Paper
  numbers come only from the frozen shipped engine through the score log (conflict 18).
- **Sources.**
  - `Part A <id>`: a change in `v5_part_a.json` (`areas[*].changes`).
  - `CAL §n`: [v5-calibration.md](v5-calibration.md).
  - `R<n>-<m>`: finding m of reviewer n (Review log).
  - A code line cited as `file:line` was read for this spec; lines cited only by Part A or a
    reviewer say so.
- **Protocol facts** (per the task brief, which reports them re-verified on primary sources; not
  opened by me): MCP 2026-07-28 removes sessions (SEP-2567) and the `initialize` handshake
  (SEP-2575). MRTR (SEP-2322) replaces server-initiated requests (KB 01:65); its wire shape is
  UNVERIFIED.
- **Ids.** Switches are named in words. Families are W1-W8, external evidence X1-X3, candidate
  configurations cfg0-cfg9, hypotheses Hyp1-Hyp6. Adversary classes and assumptions are named in
  words. KB gaps keep their K ids and are always written "KB gap K8".
- **Paper wording.** Sentences meant for the paper say "the caller" and "its".

## 1. Goals: review items mapped to changes

Change ids are defined in section 4. "Text only" means the paper or docs change and the code
does not.

### Reviewer claims C1-C12

| ID | Claim (short) | v5 answer | Changes |
|---|---|---|---|
| C1 | 2026-07-28 removes sessions and `initialize` | Every alerting dimension is era-free. Sizes are measured on `params.arguments` and `result.content`. Continuations and fallback retries fold into one logical call. Only accepted requests are learned. Era invariance is tested on rendered wire traffic. Missing handshake becomes legacy-only and watch-only. | E1-E5, E7, E8, E11, E12, B2, ARG-1, E13, EV-05, EV-10; text E15 |
| C2 | Evaluated only on design worlds | Three world pools and a hashed selection rule; eight held-out families including churn, small routes and a second catalog; three external evidence lines: independent scenarios (X1), GH Archive per-actor cadence (X2), sealed lab shadow logs (X3) | EV-01, EV-02, EV-06, EV-12, EV-15-EV-17, EV-26, EV-28, EV-30, EV-31 |
| C3 | "One shared scale" is not a calibration | One pricing rule for every dimension, a marginal agent-day bound with budgeted floors, and per-dimension spend checked against each share | CAL-1..CAL-7, RF1, RF5, EV-23 |
| C4 | Max argued, not tested | The weighted minimum of commonness is tested against the EV-20 combiners at matched budgets; the primary endpoint is detection at matched false-alarm cost | CAL-3, EV-03, EV-20, §6.1 |
| C5 | "Reads no arguments" overstated; asset unspecified | M uses the touched asset, R_static the worst-case asset; only scan-marked target inputs are read; floors need a unique match | AI-1..AI-5, AI-13, EV-04, EV-05; text PS12 |
| C6 | R and the list serve different objectives | Three outputs, each with its own objective (§2.8) | PS6, PS7, EV-24 |
| C7 | No sensitivity analysis of constants | Constants in config; tornado, Morris and factorial runs; the window sweep reports which paths can alert | EV-21, EV-13, EV-15, EV-16 |
| C8 | No adversary model or definition of detectable | Five classes in words, knowledge levels, trust assumptions T1-T10, three tiers, and adaptive kinds as a required section, including ramps | PS3-PS5, EV-25; RF7, RF11, record hold |
| C9 | "Empirical p-value" is wrong | The record rank and the organisation ranks are add-one ranks (conformal p-values) under one stated assumption; the paper body says "commonness" and "record rank" | text (§2.6, appendix) |
| C10 | The 0.9 ceiling moves the neutral point | Footprint is priced by commonness in days, so the ceiling never enters | CAL-1; text |
| C11 | Zimek et al. warn against the max | Each dimension is one view, normalised to a rank before the min; the cost-asymmetry exception is used only for the alert floors, which have their own budget | CAL-3, CAL-4, EV-20; text |
| C12 | v4 misses over-fetching | Read volume (decision D1), response sizes in the simulator, margins on every "no change" claim | AI-8, EV-07, EV-18 |

### Issues the review missed, N1-N31

| ID | Issue (short) | Changes |
|---|---|---|
| N1 | Worst-case binding driver written into the history | AI-2, AI-4, AI-5, EV-05; v5 refuses non-v5 snapshots (DEP-6) |
| N2 | Paper describes a different layer | text: PS2, PS11, PS12, §7.3 |
| N3 | Headline leaves out change days; base rates | Hyp2 on all benign agent-days; deployed at the 1% line; PPV at prevalence 10^-3 to 10^-5 |
| N4 | List credits coincidental alerts | EV-18 credited catch, random list, lift |
| N5 | Volume poisons the baseline | CAL-1: everything counted in days (B6 is no longer needed in v5) |
| N6 | Habit discount is self-granted | Unsafe sequence gets a record path keyed by (source, target) pair; copy floor with its own budget; RF11 |
| N7 | Rarity not monotone where novelty begins | CAL-1: a value never used is the strangest by construction (B8 is no longer needed in v5) |
| N8 | Callers control the identity key; day one is free | B1, B2; Red Flag records ranked against the organisation from the first call; floors; EV-25. B4 deferred. |
| N9 | Org discount trusts any three identities | RF7, RF9, AI-2 |
| N10 | Dormant identities scored as familiar | B5 |
| N11 | One shared upstream credential | PS9, T6. Per-user upstream credentials deferred. |
| N12 | `resources/read` and `prompts/get` bypass the layer | AI-10, AI-11 |
| N13 | All state in one process | §2.9 deployment: snapshot plus log replay, incremental store, scorer tier, route clock; EV-27 |
| N14 | Gray episodes carry giveaways; none adaptive | EV-04, EV-06, EV-09, EV-25, X1 |
| N15 | Simulator feeds inputs a gateway cannot derive | EV-04, EV-05, AI-5-AI-7 |
| N16 | Sequence checks scoped to one session and route | E5; E14 on for multi-route gateways; the cross-gateway gap is a trust assumption (T10) |
| N17 | Tool names are not operations | AI-7, E5. Same-PR deferred. |
| N18 | Learned limits are the max of a small sample | RF1, RF2, RF4, EV-14, EV-26 |
| N19 | The caller chooses which dimensions take part | E1, E11, B2, E3, E7; fixed shares |
| N20 | Proxy sees responses, layer ignores them | AI-8 (D1), EV-07, ARG-1 |
| N21 | Formulas do not match the code | `DIMENSION_FORMULAS_v5.md` written from the code (Batch 4) |
| N22 | No uncertainty; organisations are not replications | EV-08, EV-11, EV-12 (a must), EV-17, EV-18, X1-X3 |
| N23 | Time to detection and enforcement | EV-19, EV-27, PS6; inline mode only on one instance (T4, T9) |
| N24 | Dimensions vs threat model | PS3, EV-08 |
| N25 | Results cannot be traced to code | EV-01-EV-03 |
| N26 | Interpretability untested | PS6; claim dropped unless EV-29 runs |
| N27 | Day, hour and weekend are UTC | B9 with a directory map for zones (B9d) |
| N28 | Hosted platforms make Network constant | B10 with a per-platform egress table |
| N29 | Scalability past about 100 assets | AI-13 lookup index, cost guards (DEP-7), EV-27 at 10^5 assets and 10^4 identities |
| N30 | Unparseable bodies forwarded with no verdict | GW-1 |
| N31 | Privacy and ethics | PS10; X3 consent |

The knowledge-base gaps K1-K16 map through the same ids (Part A `addresses`). K5, K7 and K16 need
only text. K11 (probes outside the repository) is closed for the v5 probes: every number in this
spec comes from a script in `probes/`.

## 2. The v5 layer end to end

### 2.1 Inputs

The gateway, or the simulator in gateway-inputs mode (EV-04), builds one record per **logical
call**:

- **Scored methods:** `tools/call`, `resources/read` and `prompts/get` (AI-10). Housekeeping
  messages only mark legacy sessions (E12).
- **Logical call (ARG-1):** an MRTR continuation, or a modern request retried over legacy after an
  HTTP 400, folds into the call it continues. The key is (caller, tool, touched asset) plus the
  MRTR request-state field, or identical arguments within 5 seconds.
  - **MRTR wire shape (verified 2026-10-27, 2026-07-28 spec, `basic/patterns/mrtr`):**
    - The interim reply is a *result* `{"resultType": "input_required", "inputRequests": {...},
      "requestState": "..."}`. It is allowed only on `tools/call`, `resources/read` and
      `prompts/get`.
    - The retry is the same method, name and arguments under a **new** JSON-RPC id, with
      `params.inputResponses` and the echoed `params.requestState`. These sit in `params`, not
      `_meta`.
    - An `input_required` reply is not an outcome.
  - Checked end to end through the gateway with the Python SDK 2.3.0.
- **Who and when:** the caller key is the **agent** (B1, revised 2026-10-27, §8 D5); the local
  day, hour and weekend with a 04:00 rollover (B9); the era, legacy or modern (E3).
  - **Why the agent:** the author's deployments have no user ids, at most an agent id. MCP
    2026-07-28 agrees:
    - sign-in is optional;
    - no standard field carries an agent id;
    - `clientInfo` is self-reported, and servers "SHOULD NOT rely on [it] for security
      decisions";
    - SEP-2567 tells gateways to scope by the authenticated principal or by an id the gateway
      issues.
  - **Signed in:** `SHA-256(iss|client_id|sub)`, today's `Identity.id`. An agent that signs in
    as itself, with MCP's client-credentials extension (SEP-1046), gets a history of its own.
  - **Not signed in:** `SHA-256("reported"|client family|address)`. The client family is
    `clientInfo`'s name without its version, or `(none)`; the address is the caller's IP, an
    IPv6 address cut to its /64.
    - This key is **self-reported**: an agent can change its name or address and start an empty
      history.
    - The organisation-level paths, the red flags and the floors still apply from its first call
      (N8).
    - Each sensitive asset is a first access for a fresh key, so the first-access floor fires
      more often, not less.
  - **Opt-in:** a route whose tokens name people may set `baseline_key = "user"` for
    `SHA-256(iss|user claim)`, one history per person across agent applications (the old B1).
- **What:** the tool key `tool` or `tool:operation` and its read/write label (AI-7); the
  **touched asset**, which is the container named by the scan's target inputs, with its register
  sensitivity and exposure, or a keyed pseudonym, or none (AI-1, AI-2, AI-13, EXP-1).
- **From where:** the network, a /16 or a platform label for shared egress (B10); the client
  value, which is the pair (authenticated app, `clientInfo` family or `(none)`) (B2, E11).
- **Sizes (ARG-1):** request bytes are the bytes of `params.arguments`, and reply bytes are the
  bytes of `result.content`. Neither depends on the era, unlike today's whole-message size
  (wire_log.py:275, 430-431, per R3; not re-read).
- **Outcome (ARG-1):** accepted, or rejected by the server.
  - Rejections are HTTP 400/404/405, or one of these JSON-RPC errors:
    - -32602: invalid params, which now also covers resource-not-found (was -32002);
    - -32601: unknown method (with 404);
    - -32020: header mismatch;
    - -32021: missing required client capability;
    - -32022: unsupported protocol version.
  - These codes were verified 2026-10-27 against the 2026-07-28 spec.
  A call is scored before forwarding (inline) or after (background), and it is **committed** to
  history only if the server accepted it.

### 2.2 Dimensions

Each dimension measures a **strangeness** of one of three kinds:
- *amount*: a quantity; more is stranger;
- *value*: a value the caller used on fewer past days is stranger;
- *flag*: raised or not against a limit that holds for every agent, with a strength.

| Group | # | Paper name | Engine key | Kind: what is measured | Alerts? | Change from v4 |
|---|---|---|---|---|---|---|
| Typical Cadence | 1 | Call rate | `calls_last_hour` | amount: calls in the last hour | yes | counted in days (CAL-1) |
| | 2 | Write rate | `writes_last_hour` | amount: writes in the last hour | yes | writes labelled per operation (AI-7) |
| | 3 | Breadth | `assets_last_hour` | amount: touched assets in the last hour | yes | touched assets (AI-2), several per call (AI-12) |
| | 4 | Repetition | `same_call_10m` | amount: the same (tool key, touched asset) in 10 min | yes | keyed by touched asset |
| | 5 | Session duration | `session_length` | amount: minutes since the caller's current run of calls began | yes | **same name, new definition** (E4): a run ends after 30 idle minutes; not the protocol session |
| | 6 | Hour of day | `time_of_day` | value: the local hour | yes | local hour (B9); each hour counted once per day |
| | 16 | **Read volume** (D1) | `read_volume` | amount: bytes returned in the last hour | yes | **new**, only if D1 says yes (AI-8) |
| Typical Footprint | 7 | Tool | `tool` | value: the tool key | D3 | tool key (AI-7); org discount (RF7) |
| | 8 | Asset | `asset` | value: the touched asset | D3 | touched asset (AI-2); the first-access floor leaves the score (CAL-4) |
| | 9 | Network | `network` | value: the /16 or platform label | D3 | shared egress (B10); keyed pseudonyms (PS10) |
| | 10 | Client | `client` | value: (app, clientInfo family or none) | D3 | **sharper definition** (B2, E11) |
| Red Flags | 11 | Burst | `burst` | flag: calls in one minute over the limit; strength = times over | yes | limit by the agent-day procedure (RF2); per-minute counter ring (DEP-7) |
| | 12 | Sweep | `many_assets` | flag: touched assets in one hour over the limit | yes | RF2 limit, learnable from a log (AI-6) |
| | 13 | Oversized request | `request_too_big` | flag: argument bytes over the pooled limit | yes | pooled agent-day limit on argument bytes (RF1, ARG-1) |
| | 14 | Unsafe sequence | `sequence` | flag: read-then-write or write-without-review within fixed windows; strength = source minus target sensitivity, plus one when the target is public | yes | fixed windows (E5); **record path** keyed by the (source asset, target asset) pair (SEQ-1) |
| | 15 | Missing handshake | `protocol_skip` | flag: a scored call with no `initialize` behind it, for a caller who normally sends one | **never alone** | **legacy only, watch-only** (E6); modern definition cut |

Rows 1-15 keep their paper names. Row 16 exists only if D1 says yes; the paper then says "16
dimensions". "D3" means the author's decision D3 sets whether Footprint can alert.

### 2.3 One pricing rule: commonness and the record rank

Notation: J_d is the caller's active days in [start(t), t-1] on which d took part (start(t) from
B5), and A_d = |J_d| ≤ 89. N_d is the number of the route's agent-days in [t-89, t-1] on which
d took part.

**Commonness** q_d is the share of the caller's past days that were at least this strange:

```text
q_d = (1 + D_d) / (A_d + 1),   D_d = #{ j in J_d : the strangest call of day j on d was at least
                                         as strange as this call }
```

- *Amounts* compare raw day maxima: calls, writes and touched assets per hour, repeats, minutes
  and bytes. A tie counts as "at least". The usual is not needed for this test (R2-1a).
- *Values* compare how many earlier days the value had been used on. For Hour of day, each hour
  is counted leaving the day itself out of the 90-day set. A value never used before is the
  strangest possible, so N7 cannot occur.
- *Flags* count the caller's past days with the flag raised (the habit discount). For Unsafe
  sequence, the days counted are those with the same (source asset, target asset) pair.
- Oversized request and Missing handshake are always priced against the organisation:
  q_d = (1 + #{route agent-days in the window with strength ≥ this one}) / (N_d + 1).

A **record** is a call stranger than every day in J_d (D_d = 0; for a flag, the first raise in
the window, or the first raise of that pair). A record is priced by its **record rank**:

```text
r_d = (1 + #{route agent-days in [t-89, t-1] that set a record on d with strength >= this one})
      / (N_d + 1)
q_d = min( 1 / (A_d + 1), r_d )     on a record
```

The **strength** of a record measures how strong it is in a way that can be compared across
callers:
- for an amount, v4's excess score s_d (how far above the caller's usual);
- for a value, how few of the route's callers used that value in the window (a value new to the
  organisation is strongest);
- for a flag, rho: times over the limit for Burst and Sweep, and the sensitivity drop for Unsafe
  sequence.

Ranking a record against **all** of the organisation's agent-days, not only its records, is
review finding R2-1(b). It removes the per-caller 1/(A+1) factor and the second assumption of
revision 1. Each caller adds at most one record-day per dimension per day, its strongest.

**Cap condition.** The personal part 1/(A_d + 1) can reach a line α only if
(A_d + 1) · w_d · α ≥ 1. With a 90-day window and the largest share 1/12, that needs α ≥ 13.3%.
So at every stated line only the organisation ranks and the floors can alert. A longer window
(W6, the EV-21 sweep) breaks the condition at α ≥ 12/(H + 1); the config states it, and RF5
reports it.

**Path activity.** A path on d can reach line α only if N_d + 1 ≥ 1 / (w_d α). RF5 reports every
path that cannot ("path inactive at the 1% line"), per route. This replaces revision 1's frozen
`record_min_reference = 19` (R1-4, R2-9, R4-12).

| Line | Cadence (w = 1/21, with Read volume, D1) | Share 1/12 | About how many steady callers (0.67 active agent-days per caller-day, development world) |
|---|---|---|---|
| 1% (x4.69) | N_d + 1 ≥ 2,100 | ≥ 1,200 | 35 / 20 |
| 2.5% (x4.29) | ≥ 840 | ≥ 480 | 14 / 8 |
| x3 (9.43%) | ≥ 223 | ≥ 128 | 3.7 / 2.1 |

Without Read volume (w = 1/18), Cadence would need 1,800 agent-days at the 1% line. A smaller route
alerts only through its floors unless the gateway-wide reference is on (§4.4, a tune candidate
measured on W2's small-route stratum).

**Surge guard (CAL-6, R3-4).** A shared shift can produce many records at once: a release crunch,
a hosted platform's SDK update, an era flip. When today's record agent-days on d, from distinct
callers, reach max(5, 3 × the window's daily mean), today's records on d are also ranked among
today's agent-days so far, and q_d becomes the larger of the two ranks. A `flag_surge` notice is
logged. The same rule covers Oversized request. Taking the larger of two valid ranks keeps the
bound.

### 2.4 Statistic, floors and outputs

**Paper block** (with D2 = (a)):

```text
q  = min( min_d q_d / w_d ,  q_floor )
s1 = 1 / (1 + 2 q)
M  = 5 ^ max(0, 2 s1 - 1)
alert when q <= alpha;   R = R_static x M
```

**Implementation block:**

```text
1. Budget shares (CAL-3). Each group gets a third, split equally among its dimensions that can
   alert:
     Cadence 1/18 each (1/21 with Read volume)
     Footprint 1/12 each; if D3 = (b), Footprint is watch-only and its third is unspent
     Red Flags 1/12 each for Burst, Sweep, Oversized request and Unsafe sequence
   Watch-only terms (Missing handshake; Footprint under D3 (b)): v_d = max(12 q_d, 2/15), so they
   order the list but sit above every stated line. Shares are fixed and never renormalised.
   q_stat = min_d v_d, with v_d = q_d / w_d for alerting dimensions
   d* = argmin; q2 = the second-smallest v_d

2. Floors (CAL-4), outside the statistic:
     alert floor, q = alpha_deployed (0.01):
       - first access to a sensitivity-5 asset not touched in the caller's last 90 days;
       - a copy out of a sensitivity-5 source into a target that is public, outside the
         source's owner, or new for the caller (SEQ-2).
     watch floor, q = 1/8: first access to a sensitivity-4 asset not touched in 90 days.
   A floor fires only on a unique register match (AI-13).
   Floor budget: beta = 0.35% of the route's warm agent-days (0.30% first access, 0.05% copy).
   The first-access trigger fired on 0.04-0.32% of agent-days on days 90-180 in the development
   worlds (calib_v5_synthesis.py arm S1, `beta_s5`). beta is frozen at Batch 5 and swept in EV-21.
   RF5 demotes an alert floor to a watch floor on a route when the upper Wilson bound of its
   30-day realised rate exceeds its beta, counting only firings by established callers.
   The demotion is logged.
   Route warm-up: alert floors act as watch floors until the route has 14 days of v5 state, or
   the caller's history was bootstrapped (DEP-6).
   q = min(q_stat, q_floor). When a floor wins, d* names the floor and q2 = q_stat.

3. Outputs (CAL-5)
   s1 = 1/(1 + 2q); s2 = 1/(1 + 2 q2)
   M(c) = max(m_min, g(s1)), with g(s) = 5^(2s - 1) for s >= 1/2 and 0.7^(1 - 2s) below.
   m_min = 1 if D2 = (a); otherwise 0.7, which is also the value for v1-v4.
   M_day = the largest M over the agent-day's calls.

4. Alert line
   M_alpha = g(1/(1 + 2 alpha)), so an alert (q <= alpha) is the same event as M >= M_alpha.
   Deployed line: alpha = 1%, M >= x4.69 (R1-7). The 2.5% line (x4.29), the 5% line (x3.73)
   and x3 (alpha = 9.43%) are reported beside it; x3 is kept for continuity with v4.

5. Risk and list
   R(c) = R_static(tool, worst-case asset) x M(c); R_static = (T S B)^(1/3) in [1, 5] (PS7).
   List for day t: the top L agent-days by (largest s1, then s2 of the first call at that s1),
   with L = max(1, round(active agents / 40)), which gives 4 at 150 agents.
```

**Redefined kept names (R4-2):**
- s1 is no longer any one dimension's score. It is 1/(1 + 2q), where q is the smallest
  share-weighted commonness, or the floor.
- d* is that dimension or that floor.
- s2 is the same quantity for the runner-up.
- The edge of ordinary is s1 = 0.5 (q = 1/2).
- The raw per-dimension scores s_d are v4's scores and are logged in `Verdict.scores`; the paper
  never shows them.

### 2.5 What can reach the alert line

The table assumes a 90-day window, the deployed 1% line, and an active route path.

| Path | Smallest q/w | Largest M | Alerts at 1%? |
|---|---|---|---|
| A record that ranks among the route's top record-days (Cadence; Footprint if D3 = (a); Burst, Sweep, Unsafe sequence) | 1/((N_d + 1) w_d), about 0.002 at N_d ≈ 9,000 | x5 | yes, if the path is active |
| Oversized request, ranked among the route's agent-days | about 0.0013 | x5 | yes, if the path is active |
| A record that ranks low (its personal part only) | 1/((A_d + 1) w_d): 0.20 Cadence, 0.133 share 1/12 | x1.99 / x2.54 | no |
| Not a record (D_d ≥ 1) | 2/((A_d + 1) w_d): 0.40 / 0.27 | x1.20 / x1.63 | no |
| Watch-only terms: Missing handshake; Footprint under D3 (b) | ≥ 2/15 | x2.54 | no |
| Alert floor | 0.01 | x4.69 | yes (budget β) |
| Watch floor | 0.125 | x2.63 | no |

Paper version, four rows:
1. a record the organisation rarely matches (x5);
2. an oversized request the organisation rarely matches (x5);
3. an alert floor (x4.69);
4. everything else, at most x2.54.

### 2.6 The bound

**Proposition.** Draw a warm agent-day uniformly from a route's window. Assume one thing: the
route's agent-days in the window, today's included, are exchangeable for each dimension's
statistic (its record strength, or its strength for the two organisation-priced flags). Assume
also the cap condition. An inactive path only removes alerts, so it needs no assumption. Then:

P(the agent-day alerts at line α) ≤ Σ_{d alerting} w_d α + P(an alert floor fires)
≤ α + β with D3 = (a), or (2/3) α + β with D3 = (b).

**Proof sketch** (appendix; self-contained, R4-16):
1. The add-one rank of a value among n exchangeable values is super-uniform:
   P(rank ≤ x) ≤ x. Bates et al. eq. (2)-(3) state this marginal form; I read the arXiv text
   (scratchpad copy, `bates/bates.txt:100-125`).
2. Under the cap condition, the personal part cannot reach α, so dimension d fires only if
   r_d ≤ w_d α. Its probability is at most w_d α.
3. The surge guard and the min only raise q, so they keep step 2.
4. A union bound over dimensions needs nothing about how they depend on each other ("weighted
   Bonferroni over rank-based rates", named once so reviewers recognise it). Floors add their
   own rate.

Every event concerns a day maximum, and the route reference is frozen for the day (CAL-7). So the
statement is per agent-day with no volume term.

**Scope.**
- The statement is marginal: it is an average over the route's agent-days, not a per-caller
  bound. Per-caller rates are an empirical claim, tested with a binomial test against the bound.
- It holds only for warm agent-days, under the cap condition (history ≤ 90 days at the stated
  lines).
- Under D3 (a), a newcomer's novelty is ranked like anyone's, so the bound holds on average but
  alerts could concentrate on new callers. The per-tenure-band check (Hyp2) and W8 test this.
- Change days, adaptive callers and era flips are not exchangeable by definition. Hyp2 still
  reports **all** benign agent-days against the bound.
- Bates et al. warn that marginal validity can fail for an "unlucky" reference. So the share of
  worlds and of 30-day periods above the bound is reported beside the pooled rate (R2-8).
- The organisation-calibration arm overran a similar bound by 1.34-1.9x with a rolling pool
  (CAL §7). That is the stated residual risk of the exchangeability assumption, and it is why
  the bound is checked per tenure band and per 30-day period (R2-2).

**Paper sentence** (R4-5):
> On a day exchangeable with the organisation's other days in the window, the multiplier reaches
> the alert line for α with probability at most α plus the alert floors' rate, on average over the
> organisation's agent-days; nothing is assumed about how the dimensions depend on one another.

**Development world, calibration stage on v4 scores (not v5).** Probe:
[probes/org_record_rank_probe.py](probes/org_record_rank_probe.py), on main_seed7 / main_seed11 /
heavy_files_seed21. The arms:
- S5 is revision 1.
- O1 adds the record rank among all agent-days.
- O2 adds the Unsafe-sequence record path, with tied strength, and the watch-only Missing
  handshake.
- O3 adds the surge guard.
- Footprint stays at e, which is D3 (b). The O-arms use v4's records (scores as logged), not
  CAL-1's raw maxima.

| Arm | 1% line: all benign days 90-180 (%) | Per-dimension cells over share, all benign days, at 1% / 2.5% / x3 | Gray at the 1% line / x3 (of 130) | Oracle ROC points: gray at 1 / 2 / 3% benign |
|---|---|---|---|---|
| v4 | - | - | - | 50 / 66 / 80 |
| S5 | 0.70 / 0.39 / 0.52 | 8 / 12 / 16 | 56 / 83 | 80 / 83 / 88 |
| O1 | 0.75 / 0.32 / 0.62 | 8 / 6 / 6 | 55 / 82 | 77 / 84 / 86 |
| O3 | **0.22 / 0.26 / 0.19** | **1 / 0 / 0** | 53 / 81 | 74 / 83 / 85 |

- O1 removes the Cadence overruns on ordinary days at x3. Revision 1 overran there: Repetition
  spent 0.728 / 0.845 / 0.632% against a 0.524% share (R2-1).
- Under O1, on change days, Hour of day still overran its share 7-8x at the 1% line in two of
  the three worlds. The cause is one org-wide event: on main_seed7, 38 of the 43 alerting benign
  days at the 1% line fall on day 120, a release crunch
  ([probes/hour_surge_check.py](probes/hour_surge_check.py)). The surge guard removes this.
- Cost: O1-O3 together lose 0-6 gray episodes at the oracle points; the surge guard alone loses
  1-2 of them, plus 2 big_paste episodes at the 1% line.
- Burst's record reference held a median of only 1-3 record-days. Under revision 1's
  `record_min_reference = 19`, Burst and Sweep could never have alerted (R1-4).
- cross_copy stays at 4 of 13. The vectors carry v4's session-scoped sequence and no pair or
  sensitivity, so the toxic-flow path (SEQ-1, SEQ-2) cannot be measured on them.
- Every number above needs the v5 engine re-run (plan L2) before selection.

### 2.7 Mechanisms

| Mechanism | v5 definition (one sentence, paper wording) | Was in v4 | Switch |
|---|---|---|---|
| habit discount | A flag raised on many of the caller's past days counts only as rare as those days are; for Unsafe sequence, only repeats of the same source-target pair count. | 0.9/(1 + 2e), habit flags only (engine.py:504-515) | `habit_after_established` (RF11) |
| first-access floor | First access to a sensitivity-5 asset not touched in the caller's last 90 days is an alert floor (x4.69); sensitivity 4 is a watch floor (x2.63). | folded into the Asset score (engine.py:429-431, 489-502, per rev 1) | `alert_floor_rate`, `watch_floor_rate`, `floor_budget` |
| org discount | Something new for the caller counts as ordinary when at least 3 established colleagues started using it in the last 7 days and it is new to the organisation, unless it is a write tool or a high-impact tool. | any 3 identities (engine.py:551-556) | `org_new_days`, `org_discount_reads_only`, `org_discount_max_static` |
| warm-up | Until its 5th scored call and the end of its first local day, only checks that need none of the caller's past take part: the red flags, the floors and Oversized request. | yes (engine.py:288-290, per rev 1) | none |

Appendix-only mechanisms, one line each:
- *surge guard* (§2.3);
- *route warm-up* (§2.4);
- *record hold* (a tune candidate): past record-days stay out of D_d for 30 days, whether they
  alerted or not;
- *established*: at least 20 active days and 14 days since the first call; used by RF7, RF11,
  the floor budget and the established reference.

### 2.8 The three outputs and their objectives

| Output | Definition | Objective | Reported as |
|---|---|---|---|
| Alert | a call with q ≤ 1% (M ≥ x4.69) | interrupt someone within α + β of agent-days; within that, catch the most gray | benign agent-days at the deployed and stated lines; Hyp1, Hyp2; PPV at prevalence 10^-3 to 10^-5; harm before the first alert (EV-19) |
| Daily review list | the top L agent-days by (s1, s2), each with d* and the runner-up dimension | the most gray episodes per list slot | credited catch, lift over a random list, recall@L for L = 1-16 |
| Risk score R | R_static × M | order calls by consequence scaled by strangeness | gate curve: benign block rate against harm-weighted gray recall (EV-24) |

The list is keyed on s1, not M: under D2 = (a), M is flat at 1 below s1 = 0.5.

### 2.9 Deployment: state, clocks, replicas, migration

This section answers R3-1, R3-2, R3-3, R3-9, R3-10 and R3-11. Its items are DEP-1..DEP-8 in §4.3.

- **Two modes (DEP-1).**
  - *Inline*: score before forwarding, on a **single instance** only. This is trust assumption T9,
    next to T4.
  - *Scale-out*: proxy replicas are stateless and only log. One **scorer tier** consumes the
    merged logs in background mode, sharded by the baseline key (the agent key of §2.1). For a
    signed-in agent this is `gateway.agent_id`.
- **Route clock and fold (CAL-7, R3-3).**
  - Each route has a zone and rolls over at 04:00.
  - An open-day buffer keeps each active caller's running maximum per record dimension and its
    flag strengths.
  - At each route rollover, a sweep visits every caller whose local day has ended, a dormant
    caller's last day included. It appends their record-days and agent-day maxima, and it
    rebuilds one sorted array per dimension, so a call needs one bisect.
  - RF5 and the policy switch fold on the same clock. A `behaviour_fold` log line carries the new
    references' digests, so offline replay folds at the same point.
- **Shared references (DEP-2).** In scale-out, every shard writes a daily extract at the
  rollover: record-days, flag agent-days, first uses, flag counts. The route's references are built
  from all extracts, pinned by digest and loaded by every shard. A day's scores therefore do not
  depend on which replica saw a call.
- **State (DEP-3, R3-1).**
  - Restore is a snapshot plus a log replay. A snapshot is taken at each route rollover with the
    digest of the last log line it includes. On start, the log tail is replayed through the same
    `RouteScorer` path that `score.py` uses, so live equals offline by construction.
  - Per-caller state goes to an embedded store (SQLite), written incrementally for changed callers
    only, from a copy, off the event loop. Today `save_state` runs `json.dumps` inline
    (proxy.py:362-375), and `state_every` defaults to 0 (config.py:83-84), so a crash loses
    everything since start.
  - Decision lines carry every engine input, pseudonymised: the touched-asset pseudonym,
    sensitivity, exposure, operation, argument bytes, era, zone, baseline key, logical-call key
    and outcome. Routes with `log_bodies = none` can then be replayed too.
- **Policy re-learning (DEP-4, R3-9).**
  - RF4 re-learns offline into a new versioned policy file.
  - The route switches at a rollover and logs a `policy_switched` line with the new digest, and
    `score.py` replays these switches.
  - Logs rotate daily, and the first line of each file carries the previous file's last digest.
  - Readers stream; today `read_log` returns a list (log_file.py:132-136).
  - Learners read the daily agent-day extract, not raw logs.
- **Sessions (DEP-5, R3-11).** One SessionBook record per (route, session), with a 1-hour idle
  TTL and a per-caller cap. All maps are evicted together, and only live records persist. Today
  only `_owner` is capped (wire_log.py:170-193).
- **Migration and cold start (DEP-6, R3-10, R1-4).**
  - Before a route switches to v5, its last 90 days of log are replayed offline:
    `score.py --design v5 --save-state`, keyed by the agent key of §2.1:
    - `gateway.agent_id` for a signed-in call;
    - the logged client name and address for the others.
  - v5 refuses snapshots of other designs. Today restore accepts any design (engine.py:619-621).
  - Route warm-up then applies (§2.4).
  - The first-30-day alert rate after migration is an EV-27 row.
- **Cost guards (DEP-7, R3-7).**
  - Per caller and per kind, keep at most 4,096 distinct values. They are the most recent, and
    the rest fold into one overflow value that is priced as new.
  - Day counts are kept as count-of-counts. Today the Footprint tail sum is O(distinct values)
    (memory.py:101).
  - Burst uses a 60-slot per-second ring; today it scans the last hour (engine.py:476).
  - Each call has a scoring budget of 5 ms. A call over budget gets the verdict `unscored`,
    which is logged and counted like GW-1.
- **Routes without sign-in (DEP-8, R3-12; revised 2026-10-27, §8 D5).**
  - v5 runs in full on a route without sign-in. Each caller's history is keyed by its reported
    client name and address (§2.1).
  - The decision line logs the identity strength: `user`, `service` (a signed-in agent), or
    `none` (reported name and address).
  - The evaluation reports results per strength.
  - The earlier refusal (`allow_anonymous_v5`, Red Flags and floors only) is removed. It assumed
    per-user sign-in, which the author's deployments do not have.

## 3. Conflicts between the area designs and reviewers, resolved

Rows 1-25 are revision 1's conflicts between the Part A areas. Rows 26-33 are new conflicts
between reviewers.

| # | Conflict | Resolution | Why |
|---|---|---|---|
| 1 | Floor price s = 0.9 vs q = 0.01 | q = the deployed α (0.01) | x3.62 sits below the 1% line |
| 2 | Floor combination max over g vs min over q | the min over q | the same order |
| 3 | Habit formula RF6 vs CAL | commonness in days | one rule |
| 4 | Missing handshake modern: E6 vs "share unspent" | **cut**: legacy-only and watch-only (R3-4, R4-8) | the server must already reject the modern trigger; at most x0.9 in rev 1 |
| 5 | Missing handshake as a watch floor vs org-priced | org-priced, watch-only cap at q/w ≥ 2/15 | the simulator's 3% resume rate (normal_org_world.py:632) sets its base rate, and real clients rarely resume (KB 01:242-244) |
| 6 | Read volume as a 16th dimension | decision D1 | |
| 7 | Time away, Oversized reply | deferred | B5 and Read volume cover them |
| 8 | Warm-up vs role prior | B4 deferred (R4-11) | it needs a role claim no evaluated route has |
| 9 | "Established" defined three ways | one predicate (§2.7) | |
| 10 | `alert_line` vs `alert_multiplier` | one field. v1-v4 keep 3.0; v5 uses the 1% line (x4.69) | R1-7 |
| 11 | List key (M, s2) vs flat M | (s1, s2) | |
| 12 | Review budget: fixed vs share | L = round(active agents / 40) | worlds have 5-800 agents |
| 13 | M in [0.7, 5] vs [1, 5] | decision D2 | |
| 14 | Tools only vs resources and prompts | scored methods include both | |
| 15 | Client value | (app, clientInfo family or none) (R3-12) | keeps the borrowed-token signal |
| 16 | RF1 lines per tool vs operation keys | keyed by tool key | |
| 17 | Selection: fewest alarms vs mechanisms that cost alarms | **replaced**: detection at matched cost, false alarms as a hard constraint (§6.2) | R1-6, R2-4 |
| 18 | Mirror edits vs shipped engine | no v5 mirror; v5 runs only on the shipped engine | |
| 19 | Same repository vs same PR | same touched asset | |
| 20 | Keep Session duration? | kept, with a leave-one-out ablation | name constraint |
| 21 | Org discount on write tools | never | |
| 22 | Per-user key on v4 routes | opt-in for v4 routes, default for v5 | |
| 23 | One pool vs pools per era | no per-era pools: every alerting input is era-free | ARG-1, E13 |
| 24 | RF5 budget vs shares | RF5 reports each item against its own `nominal_rate` | |
| 25 | "Reads no argument values" | "M reads only the scan-marked target inputs and argument and reply byte counts, never free text." | |
| 26 | Footprint: alert path (R1-3) vs watch-only and drop F1 (R4-9) | decision D3. Recommended: the one rule, so Footprint can alert. It is not a fifth pricing rule but the same rule as every other dimension. | R4's objections were that the rule could never pick F1 and that it added a pricing rule; the new selection rule and the one rule remove both |
| 27 | Add a hold (R1-8) vs drop H1 because it loosens the bound (R4-9) | the record hold is a tune candidate | under the organisation rank, any per-agent-day statistic keeps the bound, so the hold costs no bound |
| 28 | About 8 new body names (R1-9) vs at most 5 (R4-1) | 5: commonness, budget share, record rank, alert line, alert/watch floor | stricter wins |
| 29 | Primary endpoint: recall at matched 1% / 2.5% (R1-6) vs threshold-free pAUC (R2-3) | Hyp1 = pAUC over [0, 3%]; recall at 1% and 2.5% from calibration-fitted thresholds is Hyp3 | both kept; pAUC needs no fitted threshold |
| 30 | H4 against 0.5% (R1-1e) vs nominal × tolerance (R2-5) | Hyp5 against 0.5%, tolerance 1 | satisfies both |
| 31 | List length k (R4-13) vs L (R4-6) | L | k is the habit count |
| 32 | Same-day peer price always (R3-4) vs early-day alerts | only under a surge | a plain max with ~100 agent-days a day would block every alert (1/101 / (1/18) = 0.18 > α) |
| 33 | E14 on (R1-2) vs "built but off" | on for gateways whose routes share an issuer; the cross-gateway gap is T10 | |

## 4. Changes

Each row gives the files and functions, the config, the tests and the risk to v4. `all` means
every design. Every v5-only switch has a v5 default and an "off" value that restores the v4
behaviour of that part.

### 4.1 (a) Legacy fixes, behind `legacy_fixes`

These fix v4 bugs, but they change v4's live output, so they are design-gated (R1-12, R3-8).
`legacy_fixes` defaults to False for v1-v4 and True for v5. If the author ever ships them to v4,
the paper calls that design "v4.1", and INF-1 pins both.

| ID | Change | Files: functions | Tests |
|---|---|---|---|
| E1 | A sessionless guarded call is "not evaluable", not raised | `engine.py:_problematic_sequence` (569-582) | sessionless fixture: v4 unchanged, v5 no SEQUENCE |
| E2 | Sessionless calls add no 0-minute session samples | `engine.py:_call` (379-380) | same fixture |
| RF9 | `FirstUses.others` counts distinct identities | `memory.py:FirstUses.others` (231-238) | duplicate-first-use fixture: v4 2, v5 1 |

### 4.2 (b) Logging and infrastructure

| ID | Change | Files: functions | Tests | Risk to v4 |
|---|---|---|---|---|
| INF-1 | Engine golden pin of v1-v4 verdicts on a seeded stream, including sessionless and duplicate-first-use fixtures (R1-12) | tests/behaviour/test_golden_designs.py (new) | it is the test | none |
| INF-3 | **Gateway golden** (R3-8): a recorded gateway log re-scored with v4 through `score.py` equals a pinned CSV. Re-baselining needs a changelog entry naming E9, AI-3 or PS7. | tests/gateway/test_golden_gateway.py (new), golden/ | it is the test | none |
| INF-4 | `config_to_json` emits only the fields that mean something for `config.design`; round-trip equality, not bytes (R3-8; policy.py:137-150) | `policy.py:config_to_json`, `config_from_json` | v4 policy JSON byte-identical; v5 round trip | none |
| INF-2 | Decision lines carry every score, s2, era, outcome and every engine input (§2.9), plus `behaviour_rate`, `floors`, `records` | `framework.py:RouteScorer.score`, `behaviour_fields` (283-293) | fields present, old ones unchanged | lines grow |
| LOG-1 | Batch-0 log fields: `gateway.baseline_key`, `zone`, `protocol_era`, `protocol_issues`, `reply_wire_bytes`, `logical_call`, `outcome`; lines `behaviour_fold`, `policy_switched`, `flag_surge` (R3-13) | `wire_log.py`, `framework.py` | names present | additive |
| EV-03 | Trace hook on the shipped engine | `engine.py:observe` (281-299) | trace on/off identical | none |
| PS6 | `Verdict.alert`, `runner_up`, `runner_up_dimension`; review-list report | `engine.py:Verdict` (168-181); `gateway/score.py` (`COLUMNS` 30-55, R3-16) | | additive |
| EV-21 | Bounds into config | `engine.py:multiplier` (184-188) | INF-1 | none |
| RF5 | Realised rate of every flag, floor and dimension against its `nominal_rate`; path-activity report; floor demotion; per-era base rates | behaviour/flag_rates.py (new) | Wilson bound, demotion guard, round trip | none |
| E3, E7 | Era classifier; conformance issues logged, not scored | gateway/protocol_era.py (new) | 7-case table | none |
| E10 | `gateway.instance` on start and stop lines | `proxy.py:announce` | | none |
| B3 | `gateway.identity_strength` field | `wire_log.py` | | none |
| AI-6 | Join decision lines to requests for learning | `policy.py:messages_from_log` (162-187) | | low |

### 4.3 (c) Gateway, binding and deployment, design-independent

| ID | Change | Files: functions | Tests | Risk to v4 |
|---|---|---|---|---|
| E9 | Session book per route; owner bound on accept; persisted | `wire_log.py:SessionBook`; `proxy.py` | 404 id not claimed | low; covered by INF-3 |
| DEP-5 | SessionBook TTL (1 h idle) and per-caller cap; maps evicted together | `wire_log.py:SessionBook` (170-193) | 10^6 never-deleted sessions keep memory bounded | none |
| B1 | Per-agent baseline key (revised 2026-10-27, D5): signed in → `Identity.id`; not signed in → reported client family and address; per-person key only as the opt-in `baseline_key = "user"` | `oauth.py:reported_key`, `baseline_caller`; `config.py:baseline_mode`; `framework.py` | two unsigned agents with one name on two addresses → two keys; a new version keeps the key; IPv6 cut to /64; opt-in `user` still merges two client_ids of one person | none (v1-v4 keep `user_app`) |
| B2/E11 | Client value = (authenticated app, clientInfo family or `(none)`) (R3-12) | `oauth.py`, `engine.py:client_family` (205-210) wrapper | borrowed token with a new clientInfo is a new value | none (v5 only) |
| B9d | Zone from a configured user→zone directory map, else a claim, else the route zone; the share of callers on the fallback zone is reported (R3-13) | `config.py`, `framework.py` | | none |
| B10 | Shared egress ranges as one platform network, from a per-platform egress table marked verified/UNVERIFIED (R3-16) | `engine.py:network_of` (191-202); `config.py` | empty list identical | none |
| AI-3 | Binding matches only scan-marked target inputs | `binding/scoring.py` | decoy path; golden without `tool_targets` | low; INF-3 |
| AI-13 | **Touched-asset lookup at scale** (R3-6): exact canonical id dict, then an inverted token index so `name_coverage` (identifiers.py:169-184, per R3) runs only on candidates; memoised by canonical value; floors need a unique or exact match; "most sensitive" kept only for R_static | binding/touched_asset.py (new) | 10^5-id register: time and ambiguity | none (v5 path) |
| EXP-1 | Exposure (public / internal / private) from the register or the binding's registered repositories; "outside the source's owner" from the owner argument (R1-2) | register schema; touched_asset.py | | none |
| ARG-1 | Era-free sizes, logical-call folding, score/commit split, commit only accepted (R3-5) | `wire_log.py`, `proxy.py:_relay`, `framework.py:RouteScorer.commit` | MRTR and fallback fixtures; 400 not learned | none for v4 (v4 commits at observe) |
| RPL-1 | Count raw reply bytes in `_relay`; bytearray buffer; skip parsing above a size cap (R3-14) | `http_wire.py` (95-98, per R3), `proxy.py` | 50 MB reply: linear time | none |
| PS7 | R_static = (T S B)^(1/3); `risk` → `gate_risk` alias | `framework.py:score` | viewers read both | medium for readers; INF-3 |
| PS9, PS10, GW-1 | as revision 1 | as revision 1 | | none |
| DEP-1 | Scorer tier: background consumer of merged logs, sharded by baseline key | gateway/scorer_tier.py (new) | 1, 2, 4 shards give equal scores | none |
| DEP-2 | Daily extracts and digest-pinned shared references | gateway/scorer_tier.py | | none |
| DEP-3 | Snapshot at rollover plus log-tail replay; SQLite per-caller store off the loop | behaviour/state_store.py (new), gateway/state_replay.py (new), `proxy.py:save_state` (362-375) | kill -9 recovery equals clean replay | none for v4 unless enabled |
| DEP-4 | Offline re-learn to versioned policy; switch at rollover; daily log rotation with a chain carry; streaming reader | `policy.py`, `log_file.py` (134), `score.py` (184-193) | chain verifies across files | none |
| DEP-6 | Migration bootstrap command; v5 refuses non-v5 snapshots | `score.py --design v5 --save-state`; `engine.py:restore` (619-621) | | none |
| DEP-8 | (revised 2026-10-27, D5) v5 runs in full without sign-in, keyed by the reported client name and address, and logs the identity strength; `allow_anonymous_v5` is removed | `config.py`, `framework.py` | an unsigned v5 route starts and keeps two agents apart | none |
| E14 | Cross-route sensitive-read ledger, **on** for routes that share an issuer (R1-2) | `framework.py`, `proxy.py` | read on A, write on B | none (v5 only) |

### 4.4 (d) v5-only engine changes

Engine scaffolding (Batch 0): `V5` joins `DESIGNS` (engine.py:81); `self.v4 = design in (V4, V5)`
and `self.v5 = design == V5` (engine.py:270-279). Kinds:
- *core*: on in every candidate;
- *argued*: admitted by the rule in §6.2;
- *tune*: chosen by the rule;
- *D2*, *D3*: the author decides;
- *defer*, *cut*: not built.

The three appendix bundles (R4-10) are ablated as units:
- **era-free inputs**: E4, E5, E6, E8, E11/B2, E12, ARG-1;
- **asset and operation inputs**: AI-2, AI-7, AI-10, AI-12, AI-13, EXP-1;
- **history hygiene**: B5, B9, RF7, RF9, DEP-7.

| ID | Change | Files: functions | Switch (v5 default; off) | Kind |
|---|---|---|---|---|
| CAL-1 | Commonness in days: raw day maxima for amounts, value-days for values, raised days for flags | behaviour/calibration.py (new): `DayRings` | `calibration = "commonness"` (`"max"` = v4) | core |
| CAL-2 | Record rank among all route agent-days; cap condition; path activity | calibration.py: `RecordReference` | `record_rank = True` | core |
| CAL-3 | Budget shares over alerting dimensions; watch-only cap | calibration.py: `combine` | `budget_shares = (1/3, 1/3, 1/3)`, `watch_cap = 2/15` | core |
| CAL-4 | Floors outside the statistic; floor budget and demotion; route warm-up | calibration.py: `apply_floors`; `engine.py:_first_look` (489-502) moves out of the Asset score (429-431) | `alert_floor_rate = alpha_deployed`, `watch_floor_rate = 0.125`, `floor_budget = (0.003, 0.0005)`, `route_warmup_days = 14` | core |
| CAL-5 | Outputs, the deployed 1% line, v5 Verdict fields | `engine.py:observe` | `alert_alpha = 0.01` for v5; v1-v4 keep `alert_line = 3.0` | core |
| CAL-6 | Surge guard | calibration.py | `surge_min = 5`, `surge_factor = 3.0` (None) | core |
| CAL-7 | Route clock, open-day buffer, fold sweep, `behaviour_fold` | calibration.py: `RouteClock` | `route_zone`, `day_start_hour = 4.0` | core |
| SEQ-1 | Unsafe sequence records keyed by (source, target) pair; strength = sensitivity drop + public | behaviour/unsafe_sequence.py (new) | `sequence_record = True` | core |
| SEQ-2 | Copy floor (merges RF6 and RF10): sensitivity-5 source into a public, foreign-owner or new target; its own β | unsafe_sequence.py; calibration.py | `copy_floor = True` | core |
| E4 | Session duration over the caller's own run, 30-minute idle gap | behaviour/own_session.py (new) | `idle_gap_s = 1800` | core |
| E5 | Unsafe sequence over fixed windows (10 min, 24 h, 7 d) | unsafe_sequence.py | `sequence_window_s = 600` etc. | core |
| E6 | Missing handshake: legacy only, sessionless calls count, watch-only | behaviour/handshake.py (new) | `handshake_legacy_sessionless = True` | core |
| E8 | Legacy session state: quota, TTL | handshake.py | `max_sessions_per_caller = 64`, `session_ttl_s = 604800` | core |
| E12 | Origin learned only from scored calls | `engine.py:observe` | `origin_from_calls_only = True` | core |
| RF1 | Oversized request on one pooled agent-day limit on argument bytes, graded by organisation rank | `policy.py:derive_policy_v5` | LINE_ALPHA 0.005, REFERENCE_QUANTILE 0.99, MIN_LINE_DAYS 199 | core |
| RF2, RF4 | Burst and Sweep limits; offline re-learn with growth ≤ 1.25x, switched at rollover | `policy.py` | `relearn_days = 30`, `max_growth = 1.25` | core |
| RF7 | Org discount hardened | `memory.py:FirstUses`, `engine.py:_org_wide` (551-556) | `org_new_days = 30` etc. | core |
| B5, B9 | Minimum history; local day and hour | memory.py; behaviour/clock.py (new) | `max_history_days = 365`; `local_day = True` | core |
| DEP-7 | Cost guards: value cap with overflow, count-of-counts, second ring, scoring budget | memory.py, engine.py | `max_values_per_kind = 4096`, `score_budget_ms = 5` | core |
| AI-2, AI-7, AI-10, AI-12 | Touched asset; operation keys; scored methods; several containers | engine.py | as revision 1 | core |
| B7 | Robust usual (0.75 quantile), which affects only strength | memory.py | `usual_quantile = 0.75` (None) | argued |
| RF11 | Habit days count only once established | `engine.py:_call` | `habit_after_established = True` (False) | argued |
| AI-8 | Read volume | engine.py, memory.py, framework.py | `reply_volume = True` (False) | argued, if D1 = (a) |
| PS8 | M never below 1 | `engine.py:multiplier` | `min_multiplier = 1.0` (0.7) | D2 |
| FP-1 | Footprint watch-only (D3 (b)) | calibration.py | `footprint_alerts = True` (False) | D3 |
| HOLD | Record hold, 30 days | calibration.py | `record_hold_days = None` (30) | tune |
| TOP | Top-identity-out in every reference | calibration.py | `leave_top_identity_out = False` | tune |
| EST | Established reference | calibration.py | `record_reference = "all"` (`"established"`) | tune |
| GWR | Gateway-wide reference for small routes | calibration.py | `reference_scope = "route"` (`"gateway"`) | tune |
| B4 | Role prior | | not built | defer (R4-11) |
| RF3, B11, AI-9 | Identity-class lines; Time away; Oversized reply | | not built | defer |
| E6m, H1 alert hold, separate F1, B6/B8 for v5, `record_min_reference`, rule-rate floor pricing as a candidate | | | not built (the ladder stays an ablation) | cut |

### 4.5 (e) Simulator and evaluation changes

| ID | Change | Files | Risk to v4 numbers |
|---|---|---|---|
| EV-01, EV-02, EV-04-EV-07, EV-09-EV-11, EV-13, EV-14, E13, AI-5 | as revision 1, except that E13 now runs on rendered wire messages through `RouteScorer`, covering MRTR continuations, fallback probes and `_meta`-bearing sizes (R3-5) | as revision 1 | as revision 1 |
| EV-08 | Roster scales; bot gray episodes; **churn**: continuous hires and leavers at 10-30% a year (R1-1d, R2-2) | `normal_org_world.py:roster` | re-baselined |
| EV-09b | Public repositories in every catalog; a **toxic-flow** gray kind with a plain variant (R1-2) | `normal_org_world.py:gray_episode`, `Catalog` | none |
| EV-12 | Slack catalog, a **must**: W7 is a two-route gateway (GitHub + Slack) | catalogs/ (new) | none |
| EV-31 | Every family reports days 0-89 as a route warm-up stratum, with every agent present from deployment day 0 | heldout_metrics.py | none |

### 4.6 Deferred, cut and rejected

- **Deferred:** B4 role prior; B11 Time away; AI-9 Oversized reply; RF3 (needs KB gap K8);
  per-user upstream credentials (N11); same-PR (N17); the Fenwick tree (N29, unless EV-27 shows
  need).
- **Cut in revision 2:**
  - E6m: the server must reject the trigger anyway (KB 01:132-133).
  - H1 alert hold: replaced by the record hold.
  - F1 as a separate pricing rule: Footprint uses the one rule.
  - B6 and B8 for v5: day counting removes their cause.
  - `record_min_reference`: replaced by path activity.
  - The modern Missing handshake and its per-era pool.
- **Rejected** (reasons in Part A `rejected` and CAL §7, as amended): the personal-day, org and
  three-group calibrations; the 30-minute-gap scope for read-then-write; one shared look-back; an
  era-downgrade flag; per-session identity; a habit floor of 0.7; R bands; alerts on R; a plain
  same-day price (conflict 32); HMP inside Footprint (R1-3: the one rule is simpler to explain,
  and EV-20's harmonic-mean arm measures the idea).

## 5. Implementation plan

The plan is in [v5-implementation-plan.md](v5-implementation-plan.md): batches 0-7 in
dependency order, with exclusive file ownership, plus an external-evidence track (X1-X3) that
starts at once. Batch 0 adds every interface: engine, gateway config, Exchange, log names and the
`RouteScorer` constructor (R3-15). INF-1 and INF-3 gate every batch.

## 6. Evaluation plan

The framing is mostly-ordinary traffic with gray risk. False alarms come first, as a hard
constraint. Detection at the same false-alarm cost is the objective. Adaptive callers get a
required secondary section.

### 6.1 Endpoints and hypotheses (written before selection)

**Units:** the agent-day for false alarms, keyed by the engine's local-day key, not UTC
(R2-9); the gray episode for detection; the world for replication.

**Benign** means every non-gray agent-day: ordinary and labelled change.

**Thresholds** for "matched budget" points are fitted on **unlabelled** agent-days of the
calibration pool, gray included (R2-3). They are applied unchanged to test worlds. Points fitted
on a report window's own benign days are labelled "ROC point (oracle)" and never headline.

| Hyp | Endpoint | Test | Role |
|---|---|---|---|
| Hyp1 | Detection at matched cost: per-world partial AUC of credited gray recall against the benign agent-day rate over [0, 3%], v5 minus v4 > 0 | one-sided world-level sign-flip test per family, Holm over W1-W8 | primary |
| Hyp2 | Quiet: on all benign warm agent-days, the realised rate at the deployed line is ≤ α + β (upper 95% bound, per family). The theory check is per-dimension spend ≤ w_d α, Holm over dimensions, per tenure band (A < 20, 20-44, ≥ 45) and per 30-day period. | world bootstrap bound | primary |
| Hyp3 | Transfer: credited recall at the 1% and 2.5% budgets, thresholds from the calibration pool, v5 ≥ v4 − δ; the transfer ratio (realised / target) per arm and family is reported | one-sided non-inferiority | secondary |
| Hyp4 | No EV-20 combiner beats v5 by δ_c or more on the Hyp1 endpoint | every null "arm − v5 ≥ δ_c" must be rejected, simultaneous one-sided bounds | secondary |
| Hyp5 | Real sizes: the GH Archive realised oversized rate is ≤ 0.5% (upper 95%) | bootstrap over organisations | secondary |
| Hyp6 | Continuity: v5's benign rate at x3 is below v4's (unequal budgets, stated) | one-sided Wilcoxon over worlds | secondary |

- Hyp1 and Hyp2 form an **intersection-union** claim: v5 detects more at the same cost **and**
  keeps its stated bound. Each is tested at 5%.
- Margins δ, δ_c are 1.64 × the paired world-level bootstrap SE on the development pool. They
  are fixed in the hashed rule and stated in operational units: analyst catches per 100 agents
  per month.

### 6.2 Development selection rule (EV-16, rewritten)

The rule is written and hashed before the first development run.

**Pool:**
- the five organisations, regenerated with the stable hash (EV-01);
- 5 new `dev` worlds per family W2-W8, drawn from a public salt. The churn family (W8) enters
  the pool **before** selection (R2-2).

**Windows:**
- Thresholds are fitted on days 90-134, unlabelled.
- Selection metrics use days 135-180 of the **new** development worlds only. The five
  organisations' days 135-180 were spent in revision 1 (R2-12).

**Objective:** the Hyp1 endpoint (pAUC over [0, 3%]) pooled over development worlds.

**Admissible** means all of:
- the realised rate on all benign agent-days at the deployed line is ≤ α + β (upper 95% bound);
- per-kind recall at the deployed line is ≥ cfg0's − δ_kind, for kinds with ≥ 20 episodes;
- credited list catch is ≥ max(v4, cfg4) − δ_list;
- the cumulative benign cost at x3 is ≤ cfg0's + 0.5 points;
- runtime is ≤ 2x v4, and every test passes.

**Argued switches** (B7, RF11, AI-8):
- A switch is admitted when cfg0 plus the switch does not lower the objective by more than δ,
  improves recall on the kind it targets by at least δ_kind, and keeps cfg0 plus the switch
  admissible. That is recall gained per point of false alarms, not a flat cap (R1-6).
- A switch that fails ships off, and the paper states the threat it was meant to cover.

**Candidates:**
- cfg0: the core;
- cfg1-cfg3: the core plus one argued switch each;
- cfg4: the core plus every admitted switch;
- cfg5-cfg8: cfg4 plus one tune candidate each (record hold, top-identity-out, established
  reference, gateway-wide reference);
- cfg9: cfg4 with Footprint watch-only, scored only if D3 = (c).

**Choice:** the admissible candidate with the highest objective. Ties within δ go to fewer
constants.

**Disclosure:** the appendix lists every configuration ever scored on a development world since
Part B, with its numbers (R2-4):
- the 9 ArmSpecs of `calib_per_dim_conformal.py:98-110`;
- the hour-gap rule;
- the 4 Part B proposals;
- S0-S7;
- O1-O3;
- cfg0-cfg9.

### 6.3 Freeze and preregistration

**Freeze (EV-15):**
- Tag `dyn-v5-frozen`.
- Take SHA-256 of the engine and behaviour modules, the gateway scorer, **the simulator files
  (hashed before selection, R2-6)**, the harness, the range file, the X1 scenario files and the
  X3 log digests.
- Store the default `BehaviourConfig` and every frozen constant: shares, floor prices and
  budgets, RF1 constants, surge constants, value cap, the idle gap, windows, the alert line and
  the list rule.

**Preregistration:**
- Deposit it on OSF or Zenodo, with `frozen_sha`, **before** any calibration world is generated.
- Seeds are `SHA-256(frozen_sha | beacon | family | pool | i) mod 2^31`. The beacon is a public
  randomness value published after the deposit; its source is UNVERIFIED.
- Every freeze tag is logged, and any re-freeze is reported in the paper. The test pool is scored
  once.

### 6.4 Held-out families, external evidence, SLURM

**Families.** Each has at least 30 test worlds and 10 calibration worlds.

- W1: replication of the 3 profiles, 150 agents.
- W2: varied organisations, 5-800 agents, with a reported 5-30-caller stratum (R1-4).
- W3: modern era. W4: mixed era.
- W5: agent cadence.
- W6: 365-day horizon (the cap condition is reported).
- W7: two-route gateway, GitHub + Slack, with cross-route copies (EV-12, E14).
- W8: churn, 10-30% hires and leavers a year (R1-1d, R2-2).

Every family uses:
- the random calendar;
- gateway inputs;
- plain variants at 1:1;
- response sizes;
- public repositories;
- the toxic-flow kind;
- the route warm-up stratum (EV-31).

Five worlds per family are replayed through `RouteScorer` (EV-05).

**External evidence.** These answer C2, which two reviewers make a reject.

- **X1, independent scenarios (EV-28, must; R1-1a, R2-6).**
  - People outside the design, without access to v5 development numbers, write at least 30 gray
    and 30 benign look-alike scenarios.
  - The scenarios are compiled to simulator episodes and hashed into the preregistration before
    scoring.
  - Recall on kinds seen in design is reported apart from unseen kinds.
  - If fewer arrive by the freeze, what arrived is reported. The floor is 2 gray kinds and 1
    persona model.
- **X2, GH Archive per-actor cadence (EV-26b, must; R1-1b, R2-7).**
  - Data: actor-hour streams for people and for `[bot]` and agent actors: events per hour,
    distinct repositories per hour, active hours and repeats.
  - It measures the record rate against mean 1/(A+1), the per-dimension organisation-ranked
    spend against w_d α by weekday class, and the record path's realised false-alarm rate at the
    stated lines.
  - It is labelled "real public activity, not MCP traffic", with pseudonymised extraction and
    aggregates only.
- **X3, sealed lab shadow logs (EV-30, must if consent; R1-1c).**
  - Consenting lab users work behind the observe-only gateway with `log_bodies = all` for 30-45
    days, starting at deployment day 0.
  - Collection can start before the freeze, because the logs are sealed: their digests are
    deposited, and nobody scores them until the frozen engine re-scores them once from day 0.
  - It measures the benign rate only.
  - Ethics approval and timeline are UNVERIFIED.

**SLURM:** CPU-only arrays (no `--gres`), 3 CPUs, 16 GB, 1 h, `%200`. The budget is about 800
CPU-h for 8 families. This scales Part A's 520 CPU-h estimate and is UNVERIFIED.

### 6.5 Metrics and uncertainty

- **Quiet:**
  - benign agent-days at the deployed line, at the 2.5% and 5% lines and at x3;
  - splits by tag, people and bots, tenure band, era, weekday, the route warm-up stratum and the
    small-route stratum;
  - per-dimension spend;
  - per-caller binomial tests against the bound;
  - the share of worlds and 30-day periods above the bound.
- **Detection:**
  - pAUC over [0, 3%];
  - recall at the deployed line, per kind;
  - harm before the first alert (EV-19).
- **Precision:** PPV at the deployed line, at prevalence 10^-3 to 10^-5 (R1-7).
- **List:** credited catch, lift, recall@L.
- **Uncertainty (R2-8):**
  - Worlds are resampled only, with B = 10,000 and BCa or percentile intervals.
  - Arms are compared by paired per-episode discordance, tested with a world-level sign-flip
    test.
  - Agent-day rates are compared with a Wilcoxon test over worlds.

### 6.6 Sensitivity (EV-21)

- Analytic facts:
  - the alert lines;
  - s* = 0.8413;
  - the list does not depend on the bounds;
  - the cap condition and path activity per window and route size.
- A tornado chart over every frozen constant, including β, the surge constants and the value cap.
- Morris elementary effects and a small factorial (shares × floors × idle gap).
- Results are reported as "the share of the grid where each claim holds".

### 6.7 Baselines and ablations

All of these are fitted on the calibration pool at the same α and L.

- **Baselines:**
  - v4;
  - static only;
  - Red Flags only;
  - per-agent max |z|;
  - Isolation Forest;
  - the personal-day and org calibrations.
- **Combiners** (EV-20):
  - mean, noisy-OR, soft-OR, top-2, group-AOM, Thresh;
  - Tippett, harmonic mean, Cauchy. Footprint enters these only as a rank. Under D3 (b), it is
    rank-transformed first (R2-11).
- **Ablations:**
  - leave one dimension out and leave one group out;
  - the three bundles off, one at a time;
  - record rank off;
  - surge guard off;
  - floors at v4 values and at the rule rate;
  - Footprint watch-only, or the one rule (whichever D3 did not pick);
  - PS8 off;
  - each argued switch off.

### 6.8 Adaptive kinds (EV-25, a must; R1-8)

The kinds run against frozen v4 and v5 with white-box knowledge:
- paced export, look-alike thief, split copy, injected flow, fresh identity, Sybil discount,
  limit poisoning, condition then exploit, dormant return;
- **new:**
  - a **ramp** for each record dimension;
  - a distinct-value flood (cost);
  - floor demotion by Sybils;
  - surge cover (acting during an org-wide surge);
  - a two-hop toxic flow through an intermediate repository.

Reported for each kind:
- the most harm with no alert at the deployed line, and with no day on the list;
- the cost in days and calls;
- for ramps, the **free envelope**: the most daily volume reachable with zero alerts, in
  organisation record quantiles.

The tier wording follows the result. Without the record hold the text says "detectable unless
ramped below the organisation's alerting records".

### 6.9 Real data (EV-26)

- **Sizes (Hyp5).**
  - GH Archive hourly files, 2024-12-01 to 2025-08-27, per Part A.
  - Four text-body events map to tools.
  - The RF1 limit is learned on days 0-29, and the realised rate is measured after that.
- **Per-actor cadence:** X2.
- **Conditions:** pseudonymise at extraction, publish aggregates only, publish open access
  (GitHub AUP §7, per Part A).

### 6.10 Systems measurements (EV-27, required rows)

- Save and restore time at 10^3 and 10^4 identities.
- kill -9 recovery: the alert rate in the 7 days after a crash.
- A 10^5-id register: lookup time and ambiguity rate.
- A distinct-value flood: cost per call.
- 2- and 4-replica arms, whose scores must equal one instance's.
- The first-30-day alert rate after migration.
- 10^6 never-deleted sessions: memory.
- p50 and p99 inline latency.

The synthetic estimates behind these rows are labelled synthetic:
[probes/gateway_scale_probe.py](probes/gateway_scale_probe.py) measures about 90 KB of JSON per
caller and about 0.25 s per save for 50 callers, and extrapolates to about 50 s at 10^4.

## 7. Paper plan

### 7.1 Contributions and the claims we drop

1. **A per-caller runtime layer that defends MCP servers from calling agents.** It scores every
   call against the same caller's multi-week history at the server boundary, and it works on both
   MCP eras. Scale-out through a scorer tier is future work, because the build scope is the paper
   core (§8). Note 02 surveys 23 systems; to our knowledge none does this.
2. **A two-level record rank with day-maximum units** (R1-10). A call that beats the caller's own
   history is priced by how rarely the organisation's agent-days produce such a record. The
   result is a marginal per-agent-day false-alarm bound with no volume term and budgeted policy
   floors.
   - Weighted Bonferroni and add-one ranks are prior art, cited for their robustness to
     dependence: Vovk & Wang and Heard & Rubin-Delanchy via note 04:256-264; Bates et al.;
     Laxhammar's conformal anomaly detection via note 04:85 (UNVERIFIED by me).
3. **An evaluation protocol for mostly-ordinary traffic:**
   - a preregistered freeze;
   - eight held-out families;
   - detection at matched cost as the primary endpoint;
   - independent scenarios, real per-actor cadence and sealed shadow logs.
4. **A detectability map**, defined on what the layer observes. Costs are measured by EV-25.

**Dropped claims:**
- first gateway;
- first UEBA for agents;
- calibrated scores without the stated assumption;
- "guarantees": the paper says "bounds under the stated assumption";
- prompt-injection detection;
- adaptive detection;
- "reads no arguments" without the qualifier;
- real MCP traces;
- pre-execution verdicts outside inline single-instance mode;
- interpretability, unless EV-29 runs.

PS2 keeps a claims ledger. Its first line: "Every v5 number in the paper comes from the frozen
shipped engine through the score log; calibration-stage numbers on v4 scores are design
evidence only" (R4-7).

### 7.2 Threat model summary

- **Protected:** the MCP server and its assets.
- **Threat source:** calling agents, and whoever steers them.
- **Classes:** non-adaptive misuse (primary), masquerader, hijacked agent, traitor, Sybil.
- **Trust assumptions:**
  - T1-T8 as in revision 1 (complete mediation, trusted scan and binding, observe-only, log
    integrity, pooled upstream credential, caller-chosen revision);
  - **identity, revised 2026-10-27 (D5):** history is kept per agent.
    - The key is verified when the agent signs in.
    - Otherwise it is the agent's reported client name and address, which a hostile agent can
      change. Changing it only buys an empty history: the organisation-level paths, red flags
      and floors apply from the first call.
    - No user identity is assumed;
  - **T9:** inline scoring runs on one instance;
  - **T10:** the gateway sees only the routes it fronts. A copy from a server behind another
    gateway is invisible, and it goes into the "undetectable by construction" tier (R1-2).
- **Tiers:** detectable; detectable at a cost (EV-25 numbers only); undetectable by construction.
  The PS5 table is re-measured on v5.

### 7.3 The method in 1.5 columns (R4-1)

The paper is ACM sigconf, two columns (main-restructured.tex:25, per R4). The budget is about 1.5
columns for the dynamic layer's method.

- **(a) Table 1:** 16 rows (D1) × (group, name, what it measures, compared with). It has one clause:
  amounts compare the caller's day maxima, and values compare how many days the caller had used
  them.
- **(b) Commonness and record rank**, three sentences:
  - "The commonness of a call on a dimension is the share of the caller's past days that were
    at least this strange."
  - "A call stranger than all of them is a record."
  - "Its record rank is how rare, among all of the organisation's agent-days in the same 90
    days, a record at least this strong is."
- **(c)** The four-line equation block of §2.4.
- **(d)** The four-row "what can reach the alert line" table of §2.5.
- **(e)** The proposition sentence of §2.6; the proof goes in an appendix.
- **(f)** One sentence per mechanism (§2.7).
- **(g)** Three sentences for the outputs.

The observation o(c), the per-agent key ("history is kept per agent"), the touched and worst-case
assets and the era go into the gateway subsection that the static side shares. Output objectives
go to §5.1. Switches, bundles and constants go to one appendix table: field, default, range swept,
source.

### 7.4 Names

**New body names (5):**

| Name | One-sentence definition |
|---|---|
| commonness | The share of the caller's past days that were at least this strange (replaces revision 1's "daily rate", which collided with Call rate and Write rate). |
| record rank | How rare, among all of the organisation's agent-days in the same 90 days, a record at least this strong is. |
| budget share | The part of α one dimension may spend: each group a third, split equally among its dimensions that can alert. |
| alert line | The multiplier at which a call alerts: x4.69 for α = 1%, so at most 1% of agent-days alert plus the floors' rate (other lines in one table column). |
| alert floor / watch floor | A policy rule outside the statistic that alerts on its own / that raises the list rank without alerting. |

**Kept names with a changed meaning** (stated once in the body):

| Name | Definition |
|---|---|
| s1, s2, d* | §2.4 "Redefined kept names" |
| Red Flags | "A red flag is raised or not against a limit that holds for every agent; once raised, it is priced by how often it was raised before: on the caller's own days for Burst, Sweep and Unsafe sequence, on the organisation's agent-days for Oversized request and Missing handshake." |
| Session duration | Minutes since the caller's current run of calls began; a run ends after 30 idle minutes (not the protocol session). |
| Missing handshake | Legacy MCP only: a call with no `initialize` behind it, for a caller who normally sends one; it orders the list but never alerts alone. In 2026-07-28 traffic it takes no part, and conformance problems are logged, not scored. |
| Client | The application the caller's token was issued to, together with the client name the request gives, or "none". |
| habit discount, first-access floor, org discount, warm-up | §2.7 |

**Gateway subsection names** (shared with the static side): touched asset, worst-case asset
(replaces "priced asset").

**Appendix only:**
- surge guard, route warm-up, record hold, established;
- minimum history, local day, idle gap, shared egress, operation split, learned limit;
- realised rate, floor budget, logical call, scorer tier, cap condition, path activity;
- protocol era, era invariance, score log, gateway inputs, random calendar, plain variant;
- matched budget;
- development, calibration and test worlds.

**Dropped as names:**
- "alert budget": say α;
- "review budget": say list length L;
- "per-user baseline";
- "daily rate";
- "priced asset";
- "copy floor": it is an alert floor's second trigger.

**Plain-word rules (R4-13):**
- "limit" is used for every red-flag threshold, and "line" only for the alert line.
- RF5's field is `nominal_rate`.
- Floors are stated in M terms: "the first-access floor sets M to at least x4.69".

### 7.5 Evaluation body tables (R4-17)

- **RQ1:** stated against realised, at the deployed line and at x3, per family. It includes the
  route warm-up and small-route strata.
- **RQ2:** Hyp1's matched-cost detection for v4, v5 and the best combiner, plus X1's seen and
  unseen kinds.
- **RQ4:** leave one group out, the three bundles off, record rank off, surge guard off.
- **RQ5:** the adaptive cost table, including the ramp free envelope.

Everything else goes to the appendix: X2, X3, EV-27, sensitivity, and the combiner and baseline
grids.

## 8. Open decisions for the author

**Decided by the author on 2026-10-27:**
- **D5: history per agent, never per person.** The author's deployments have no user ids, at
  most an agent id.
  - The key is the signed-in agent, `Identity.id`.
  - Without sign-in it is the reported client name (without version) plus the network address
    (IPv6 /64), marked self-reported.
  - The per-person key stays only as the opt-in `baseline_key = "user"`.
  - DEP-8's refusal of unsigned routes is removed (§2.1, §2.9).
- **SDK:** the repo moves to the MCP Python SDK 2.x (`mcp>=2.3,<3`). SDK 2.x speaks the 2025
  handshake versions and 2026-07-28, so the demo and replay scripts drive both eras through the
  gateway (`--protocol legacy|modern`).

**Decided by the author on 2026-10-26:**
- D1 = (a): Read volume is the 16th dimension, in Typical Cadence.
- D2 = (a): M in [1, 5].
- D3 = (a), as recommended, with the preregistered fallback to (b).
- D4 = (a): USENIX Security '27 cycle 2. X1 and X3 must be confirmed by 8 Nov.
- **Build scope: paper core first.** The core is built before the freeze. That means:
  - the v5 engine (CAL-1..CAL-7, SEQ-1, SEQ-2, the floors);
  - the era-free inputs;
  - the legacy fixes;
  - single-instance state saving with log-tail replay;
  - the evaluation harness.

  These are deferred until after submission:
  - the scale-out scorer tier and shared references (DEP-1, DEP-2);
  - the SQLite store (DEP-3 keeps the JSON snapshot plus replay);
  - log rotation and versioned re-learning (DEP-4, RF4);
  - the 10^5-asset token index (AI-13 keeps the unique-match rule);
  - the replica and 10^5-register rows of EV-27.

  The paper states inline single-instance scoring as trust assumption T9 and drops "scales out
  through a scorer tier" from contribution 1. The core scope is set out in the implementation
  plan.

**D1. Read volume as a 16th dimension (C12, N20).** It must be decided before Batch 0, because
the dimension count, the shares, path activity and Table 1 depend on it.
- (a) Add it to Typical Cadence as an argued switch. Cadence's question becomes "when, how often
  and how much?".
- (b) Keep 15. Over-fetching then stays "undetectable by construction".
- (c) Log a reply verdict for the list only, outside M.
- **Recommended: (a).** Overfetch is caught 1 of 18 times without it (development world).

**D2. The lower bound of M in v5.**
- (a) M in [1, 5].
- (b) [0.7, 5].
- **Recommended: (a).** It is the arithmetic of revision 1 §8: under commonness, ordinary calls
  would sit on g's lower branch and discount R by about a quarter.

**D3. Can a new tool, asset, network or app alone trigger an alert?**
- (a) Yes, by the one rule: a value new for the caller that is rare across the organisation can
  alert, within Footprint's third.
- (b) No: Footprint orders the list and raises R up to x2.54, and its third is unspent.
- (c) Let the preregistered selection decide (cfg9).
- **Recommended: (a).** It is one rule for all 15 dimensions, it is easiest to explain, and it
  keeps a careless masquerader's alert path. Under the rank, false alarms stay within the
  bound (R1-3). Preregistered fallback: if the development per-tenure-band check shows Footprint
  alerts concentrating on callers with A < 20, ship (b) and say so.

**D4. Venue and schedule.**
- (a) USENIX Security '27 cycle 2 (paper 26 Jan 2027; Part A PS1 dates, not opened by me), with
  the freeze about 8 Dec. This needs X3 consent and X1 authors confirmed by 8 Nov.
- (b) The next cycle: CCS 2027 or USENIX '28. Dates UNVERIFIED.
- **Recommended: (a)** if both recruitments are confirmed by 8 Nov; otherwise (b), because the
  C2 rejects cannot be answered without X1-X3.

## References

- **Knowledge base:**
  - [README](README.md);
  - [review-assessment](review-assessment.md) (C1-C12, N1-N31, K1-K16);
  - [improvement-options](improvement-options.md);
  - notes 01-07, especially 01:65, 132-138, 167-170, 242-244 and 04:51-54, 85, 256-264, as
    cited by the reviewers;
  - [v5-calibration](v5-calibration.md).
- **Probes:**
  - [org_record_rank_probe.py](probes/org_record_rank_probe.py);
  - [hour_surge_check.py](probes/hour_surge_check.py);
  - [calib_v5_synthesis.py](probes/calib_v5_synthesis.py);
  - [calib_eval.py](probes/calib_eval.py);
  - [gateway_scale_probe.py](probes/gateway_scale_probe.py).
  - Outputs are in the session scratchpad:
    `/tmp/claude-343913582/-home-ovadyat-MCP/d6821e4d-e280-4911-be08-63b780ec3aaa/scratchpad/rev2/org_record_rank.json`.
  - Reviewer 2's probe and outputs are in the same scratchpad: `review2_probe.py`,
    `review2_fix.json`.
- **Revision 1 backup:**
  `/tmp/claude-343913582/-home-ovadyat-MCP/d6821e4d-e280-4911-be08-63b780ec3aaa/scratchpad/rev1_backup/`
  (spec, plan, calibration note, README).
- **Part A** (`v5_part_a.json` in the same scratchpad): E1-E15, AI-1..AI-12, B1-B11, RF1-RF11,
  EV-01..EV-30, PS1-PS13.
- **Code re-read for revision 2:**
  - memory.py:89-102;
  - engine.py:472-478, 504-515, 611-621;
  - proxy.py:356-376;
  - config.py:80-86;
  - policy.py:135-151;
  - oauth.py:100-121;
  - wire_log.py:168-194;
  - log_file.py:8-12, 132-136;
  - score.py:28-32;
  - normal_org_world.py:628-634.
  - Other lines are revision 1's or the reviewers', as marked.
- **External:**
  - S. Bates et al., "Testing for outliers with conformal p-values", arXiv:2104.08279, eq. (2)-(3)
    and §1.2, read from the scratchpad copy `bates/bates.txt:100-125`; the Ann. Statist. venue is
    UNVERIFIED.
  - Zimek et al. 2014, per the brief and note 04.
  - MCP 2026-07-28, SEP-2567, SEP-2575, per the brief; SEP-2322 UNVERIFIED.
  - Arp et al. 2022, opened by Part A.
  - GH Archive and the GitHub AUP, opened by Part A.
  - Venue CFPs, opened by Part A.

## Review log

Each row is one finding from the four review reports. Action: **Done** (applied), **Partly**
(applied in part, reason given), **Not applied** (reason given). Where: the section of this spec,
`plan` or `CAL`.

### Reviewer 1 (A* security PC)

| # | Sev. | Finding | Action | Where |
|---|---|---|---|---|
| R1-1 | reject | C2: one self-written simulator; EV-28 only "could"; EV-30 deferred; one GitHub catalog; no tenure stress; H4 at 1% | **Done.** (a) X1 is a must, with 30 + 30 blind scenarios hashed before scoring. (b) X2 adds per-actor cadence from GH Archive. (c) X3 adds sealed lab shadow logs from day 0. (d) W7 (Slack, two routes) and W8 (churn) are added. (e) Hyp5 is tested at 0.5%. Recruiting is an author action (D4). | §6.4, §6.9, §8; plan X-track |
| R1-2 | reject | The toxic flow has no alert path; RF6 fails its own cap; RF10 is inert; E14 is off | **Done.** SEQ-1 gives Unsafe sequence a record path keyed by the (source, target) pair. SEQ-2 adds a copy floor (RF6 + RF10 merged, narrowed) with its own β_copy. EXP-1 provides exposure. Public repositories and a toxic-flow kind are added to every family. E14 is on for routes that share an issuer. T10 states the cross-gateway gap. The path cannot be measured on v4 vectors (cross_copy 4/13 unchanged in O2), so it is measured on the v5 engine. | §2.2, §2.4, §4.3, §4.4, §7.2 |
| R1-3 | major | Footprint can never alert; 7/15 of the budget unspendable; a window cliff | **Done.** One rule for Footprint (D3 (a) recommended); the cap condition is stated with the window; shares are split over alerting dimensions only. Watch-only terms are named. HMP inside the group was not adopted (simpler to explain; EV-20 measures it). | §2.3, §2.4, §8 D3 |
| R1-4 | major | Small routes and cold start fail quietly; `record_min_reference` = 19 unmeasured | **Done.** Path activity is derived (a route-size table); RF5 reports "path inactive". A gateway-wide reference is a tune candidate. Route warm-up and migration bootstrap are added. The W2 5-30 stratum and EV-31 day-0 stratum are added. Measured: Burst's reference median is 1-3 record-days, so the 19 rule would have disabled Burst. | §2.3, §2.6, §2.9, §6.4 |
| R1-5 | major | The guarantee is on the wrong probability space; floors unbudgeted; A uses all days | **Done.** The bound is marginal over a random warm agent-day; per-caller rates are an empirical binomial claim; floors have β with demotion; A_d and N_d count only days on which d took part; Hyp2 covers all benign days; the wording is "bounds under". | §2.3, §2.6, §6.1 |
| R1-6 | major | Selection and hypotheses invert Neyman-Pearson; H1 compares unequal budgets | **Done.** The objective is matched-cost detection (Hyp1) with false alarms as a constraint; argued switches are judged by recall gained for their target kind; old H1 is now secondary Hyp6. | §6.1, §6.2 |
| R1-7 | major | The deployed x3 is a 9.43% budget; low PPV | **Done.** Deployed at the 1% line (x4.69); x3 reported for continuity; PPV at 10^-3 to 10^-5. | §2.4, §2.8, §6.5 |
| R1-8 | major | Ramps through the record path are free; EV-25 only "should" | **Done.** EV-25 is a must with ramps for each record dimension and the free envelope. The record hold is a tune candidate, and under the organisation rank it keeps the bound. The tier wording is conditional. | §2.7, §6.2, §6.8 |
| R1-9 | major | Hard to explain: many names, false definitions, 6 dims cannot alert | **Done.** One rule, so "commonness" is true for every dimension. 5 new body names. A what-can-alert table. Missing handshake is legacy-only and watch-only. Session duration is redefined. | §2.2, §2.3, §7.3, §7.4 |
| R1-10 | minor | Contribution 2 over-claims novelty | **Done.** Claims only the two-level record rank and day units; cites Bonferroni, add-one ranks and CAD prior art. | §7.1 |
| R1-11 | minor | Development numbers are not v5's | **Done.** Labelled "calibration stage on v4 scores" everywhere; kept out of the paper; plan L2 re-runs on the v5 engine before selection. | Status, §2.6, CAL |
| R1-12 | minor | The bug fixes change v1-v4; the pin cannot see it | **Done.** `legacy_fixes` (off for v1-v4); INF-1 adds sessionless and duplicate-first-use fixtures. | §4.1, §4.2 |

### Reviewer 2 (statistics / ML PC)

| # | Sev. | Finding | Action | Where |
|---|---|---|---|---|
| R2-1 | reject | Per-dimension terms exceed w_d α; A2 fails; A1 ill-posed; a marginal statement written as per-caller | **Done.** (a) Raw day maxima for the personal test. (b) The record rank is among all route agent-days, and the second assumption is gone. (c) A marginal proposition with one assumption. (d) Per-dimension spend with Holm is the theory check. Measured (development world, v4 scores): O1 removes the ordinary-day Cadence overruns at x3; O3 also removes the change-day overruns. | §2.3, §2.6, §6.1 |
| R2-2 | major | Tenure not exercised; the drift is a change in the reference's make-up | **Done.** The W8 churn family joins the development pool before selection; per tenure band and per 30-day period checks are preregistered; the residual risk is stated with the org-calibration overrun. | §2.6, §6.1, §6.2 |
| R2-3 | major | Labels leak into operating points; oracle points used as headline; H5 on ordinary days only | **Done.** Thresholds are fitted on unlabelled agent-days; oracle points are labelled "ROC point (oracle)"; pAUC is primary; Hyp2 covers all benign days; transfer ratios are reported. | §6.1 |
| R2-4 | major | The selection rule favours quiet lines; margins not noise-scaled; no cap on cumulative cost; configs undercounted | **Done.** δ = 1.64 × the world-level SE; the per-kind metric is recall at the deployed line; a cumulative 0.5-point cap; every configuration since Part B is disclosed. | §6.2 |
| R2-5 | major | Hypotheses mis-specified (H1 by construction, H2 margin, H3 direction, families, H4) | **Done.** Primary-endpoint table; intersection-union of Hyp1 and Hyp2; Hyp4 as simultaneous non-inferiority; margins in operational units; Hyp5 at 0.5%. | §6.1 |
| R2-6 | major | Development and held-out share a generator | **Done.** X1 is a must, with seen and unseen kinds reported separately; simulator files are hashed before selection. | §6.3, §6.4 |
| R2-7 | major | No test of the assumptions on real behaviour | **Done.** X2 measures the record rate and the organisation-ranked spend on GH Archive actor-days, labelled "real public activity, not MCP traffic". | §6.4 |
| R2-8 | minor | Two-stage bootstrap; "McNemar" misnamed; unpaired Wilson; marginal-only validity | **Done.** Worlds resampled only (B = 10,000); "world-level sign-flip test"; paired discordance; the share of worlds and periods above the bound. Davison & Hinkley and Field & Welsh are UNVERIFIED (not opened). | §6.5 |
| R2-9 | minor | Hybrid numbers; the 19 rule absent from the probe; UTC agent-days | **Done.** The 19 rule is cut (path activity instead); labels fixed; plan L2 re-runs on the v5 engine; agent-days use the engine's local-day key. | §2.3, §6.1; plan |
| R2-10 | minor | The bound's scope and wording overstate | **Done.** A scope paragraph; the floor term is P(fires) with its own rates; "alert budget" is dropped. The 0.4 unspendable share is gone under D3 (a); under (b) the bound is stated as (2/3)α + β. | §2.6, §7.4 |
| R2-11 | minor | Terminology avoids "p-value"; Footprint's e is not one | **Done.** The appendix states once that the ranks are conformal p-values; under the one rule Footprint is a rank too; under D3 (b) it is rank-transformed for the combiners. | §1 (C9), §6.7 |
| R2-12 | minor | Burnt windows reused; seeds can be re-rolled | **Done.** Selection uses the new development worlds' days 135-180 only; deposit before generating calibration worlds; a beacon; freeze tags logged. | §6.2, §6.3 |

### Reviewer 3 (MCP gateway / systems)

| # | Sev. | Finding | Action | Where |
|---|---|---|---|---|
| R3-1 | major | Persistence does not scale; a crash wipes history | **Done.** Snapshot plus log replay; a SQLite store off the loop; decision lines carry every input; EV-27 recovery rows. | §2.9, §4.3, §6.10 |
| R3-2 | major | Replicas: hashing on agent_id contradicts B1; org state not partitionable | **Done.** A two-tier deployment with a scorer tier sharded by baseline key and digest-pinned daily references; inline is single-instance (T9); the 2- and 4-replica arms are required. | §2.9, §6.10, §7.2 |
| R3-3 | major | There is no daily fold point; dormant callers' days are lost | **Done.** CAL-7 route clock, open-day buffer, sweep, `behaviour_fold`; a dormant-caller unit test. | §2.9, §4.4; plan L1 |
| R3-4 | major | Org-priced flags alert in bulk on common-mode shifts; Missing handshake depends on a simulator constant | **Done.** The surge guard (only under a surge; a plain same-day max would block every alert, conflict 32); Missing handshake is watch-only; per-era base rates are in RF5. Measured: a release-crunch day drove 38 of 43 Hour-of-day benign alerts; O3 removes them. | §2.3, §2.6, §3 |
| R3-5 | major | Era invariance is vacuous at message level; MRTR and retries; learning from rejected requests | **Done.** ARG-1: argument and reply bytes; logical-call folding; score/commit; E13 on rendered wire. The SEP-2322 field name must be read before Batch 1 (UNVERIFIED). | §2.1, §4.3, §4.5 |
| R3-6 | major | Touched-asset lookup is infeasible at 10^5 assets; ambiguity creates false floors | **Done.** AI-13: an exact dict, a token index, a memo by value; floors need a unique match. | §4.3 |
| R3-7 | major | Per-caller cost and memory unbounded (DoS) | **Done.** DEP-7: value cap with overflow, count-of-counts, second ring, scoring budget with `unscored`; a flood in EV-25 and EV-27. | §2.9, §6.8, §6.10 |
| R3-8 | major | v1-v4 not kept bit-identical; INF-1 unsatisfiable; `config_to_json` | **Done.** `legacy_fixes`; INF-4 design-scoped JSON; INF-3 gateway golden with a changelog rule. | §4.1, §4.2 |
| R3-9 | major | RF4 re-learning breaks provenance; logs do not scale | **Done.** DEP-4: versioned policy, `policy_switched`, daily rotation with a chain carry, streaming readers, daily extracts. | §2.9, §4.3 |
| R3-10 | major | No cold start or migration plan | **Done.** DEP-6: an offline bootstrap keyed by `iss|user`; refuse non-v5 snapshots; route warm-up; an EV-27 row. | §2.9 |
| R3-11 | minor | SessionBook leaks | **Done.** DEP-5. | §4.3 |
| R3-12 | minor | B2 hides clientInfo; anonymous routes | **Done.** Client = (app, clientInfo family or none); DEP-8. | §2.2, §4.3 |
| R3-13 | minor | Zone and role not logged; zone claim unreliable | **Done.** LOG-1 fields; a directory map (B9d). Role is not needed (B4 deferred). | §4.2, §4.3 |
| R3-14 | minor | Reply buffering is quadratic | **Done.** RPL-1. | §4.3 |
| R3-15 | minor | Batch 1 has in-batch dependencies | **Done.** Batch 0 adds gateway config, Exchange, log names and the `RouteScorer` signature. | plan |
| R3-16 | minor | Citation slips; egress ranges | **Done.** `score.py` `COLUMNS` 30-55; the fold-point claim is corrected in CAL §5; a per-platform egress table (B10). | §4.2, §4.3, CAL |

### Reviewer 4 (paper editor)

| # | Sev. | Finding | Action | Where |
|---|---|---|---|---|
| R4-1 | reject | Does not fit 1.5 columns; about 25 new body names | **Done.** A 1.5-column outline (a)-(g); 5 new body names; observation material moved to the gateway subsection; constants to the appendix. | §7.3, §7.4 |
| R4-2 | major | s1 and d* change meaning silently | **Done.** Redefined in one sentence; raw s_d never shown; Verdict field semantics go to `DIMENSION_FORMULAS_v5.md` (plan L3). | §2.4 |
| R4-3 | major | "Daily rate" names three quantities and collides with Call/Write rate | **Done.** Renamed "commonness", and the one rule makes it true for every dimension. The name "rarity score" for e stays a v4 name. | §2.3, §7.4 |
| R4-4 | major | The Red Flags definition is false | **Done.** The reviewer's sentence (with "the caller"); rho is kept out of the body; watch-only is stated. | §7.4 |
| R4-5 | major | The guarantee is named inconsistently | **Done.** The line is named by what it bounds; "alert budget" dropped; a new paper sentence. The 0.6 explanation is no longer needed under D3 (a). | §2.6, §7.4 |
| R4-6 | major | Ids and symbols collide | **Done.** Switches in words; W, X, cfg and Hyp prefixes; classes and assumptions in words; q and q_d only; L for list length; N_d and A_d. | Status, throughout |
| R4-7 | major | Every "v5" number is arm S5 on v4 vectors | **Done.** Labels; the PS2 ledger line. | Status, §2.6, §7.1 |
| R4-8 | major | E6m is overbuilt for no effect | **Done.** Cut; a legacy-only definition. | §2.2, §4.6 |
| R4-9 | major | H1 and F1 can never win; take D3 = (a) of revision 1 (watch-only) | **Partly.** H1 is cut, and the record hold replaces it. F1 is no longer a candidate: Footprint uses the one rule. The reviewer's reasons no longer hold, because the selection now maximises matched-cost detection and the hold keeps the bound (conflicts 26-27). Watch-only stays available as D3 (b). | §3, §8 |
| R4-10 | major | The design is too big: 39 switch rows, 62 fields | **Done.** Three appendix bundles ablated as units; B4, E6m, H1, B6/B8, F1 and `record_min_reference` cut or deferred; one appendix field table. | §4.4, §6.7 |
| R4-11 | major | Double standard against the other calibrations; B4 | **Done.** B4 deferred; CAL §7 keeps only measured reasons. | §4.6; CAL §7 |
| R4-12 | minor | `record_min_reference` unexplained; D1 timing | **Done.** Replaced by the derived path activity; D1 to be decided before Batch 0. | §2.3, §8 |
| R4-13 | minor | Overloaded words (line, budget, floor, rate) | **Done.** "limit" for flags; L; `nominal_rate`; floors in M terms; "daily rate" gone. "Call rate" and "Write rate" keep their names (constraint). | §7.4 |
| R4-14 | minor | Unclear definitions | **Done.** Session duration; "not touched in the last 90 days"; worst-case asset; habit and org discount sentences; L = one slot per 40 agents. | §2.4, §2.7, §7.4 |
| R4-15 | minor | The formula block mixes levels | **Done.** Separate paper and implementation blocks; B4/B6/B8 gone. | §2.4 |
| R4-16 | minor | Bates is UNVERIFIED, though the proof is three lines | **Done.** A self-contained proof sketch; Bates eq. (2)-(3) read from the arXiv text; the venue stays UNVERIFIED. | §2.6 |
| R4-17 | minor | The evaluation produces too many results | **Done.** Body tables RQ1, RQ2, RQ4, RQ5 fixed; the rest in the appendix. | §7.5 |
| R4-18 | minor | "he/his" | **Done** for paper-facing text ("the caller", "its"). Internal notes keep their wording. | §2.7, §7 |
