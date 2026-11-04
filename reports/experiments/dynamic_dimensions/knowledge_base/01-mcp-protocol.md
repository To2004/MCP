# MCP protocol state on 2026-10-25: what the dynamic layer can rely on

This note fixes, from primary sources only, what the Model Context Protocol (MCP) specification
says on 2026-10-25 about lifecycle, transport, sessions and caller identity. It then works out
what that means for the behaviour multiplier's `protocol_skip` ("missing handshake") and
`session_length` ("session duration"), and for the gateway. Every quote below was read on the
page linked in [Sources](#sources), accessed 2026-10-25. Threat model as everywhere in this repo:
the MCP server is the protected asset, the calling agent is the threat.

## Answers in brief

1. **The reviewer is right.** Revision `2026-07-28` exists. It is the Current revision. It removes
   the `initialize` / `notifications/initialized` handshake (SEP-2575) and protocol-level sessions
   with the `Mcp-Session-Id` header (SEP-2567). Every request now carries its protocol version and
   client capabilities in `_meta`, and on HTTP also in headers.
2. **`initialize` is removed, not deprecated.** It is absent from the modern protocol. A server
   *may* keep answering it, but only for legacy clients. Sessions are removed too: a modern-only
   server ignores `Mcp-Session-Id` and never mints one. Neither feature is in the deprecated
   registry, and the registry says nothing has been "Removed" under the new policy. They went in
   one step, as a declared backward-incompatible change.
3. **Backward compatibility is optional.** It works by probing, not by a handshake. Supporting both
   eras is a MAY. No end date is set for legacy revisions. The SDK posts promise only that nothing
   breaks on 2026-07-28, at least six months of TypeScript v1.x fixes, and opt-in modern serving in
   the TypeScript and Go SDKs. Mixed-era traffic should be expected for the life of the paper.
   All gateway traffic captured in this repo so far is `2025-11-25`.
4. **Identity per request.**
   - *Verified:* the OAuth bearer token, which must be on every HTTP request when authorization is
     used, and whatever it says about issuer, subject and `client_id`.
   - *Self-reported:* `clientInfo`, which is now optional, `clientCapabilities`, `protocolVersion`
     and the `Mcp-*` headers. The spec says `clientInfo` SHOULD NOT be relied on for security
     decisions.
   - *Not yet in the spec:* agent identity (DPoP, workload identity). It is on the Aug 2026 roadmap.
5. **For this repo:**
   - Under `2026-07-28` traffic, `protocol_skip` and `session_length` never take part.
   - The `requires_before` branch of the "unsafe sequence" flag fires on *every* call to a tool
     with a required step. I reproduced this: an ordinary review-then-merge gets M = 3.62.
   - The gateway's `session_agent_mismatch` cannot fire.
   - The gateway does not compare `MCP-Protocol-Version` with the body, and does not flag missing
     required headers.
   - Section [Proposed version-scoped replacements](#proposed-version-scoped-replacements) gives
     signals that hold in both eras.

## 1. Revision timeline

Dates are revision identifiers. Each one "indicate[s] the last date backwards incompatible changes
were made" (versioning page). GitHub release objects of `modelcontextprotocol/modelcontextprotocol`
were read from the releases API:

- `2024-10-07`: published 2024-11-06. It has no spec page (404).
- `2024-11-05`: published 2025-01-17, then `2024-11-05-final` on 2025-03-26.
- `2025-03-26`, `2025-06-18`: published on those dates.
- `2025-11-25`: RC on 2025-11-15, final on 2025-11-25.
- `2026-07-28`: RC on 2026-05-29, final on 2026-07-28T16:47:49Z. The RC blog post says "The
  release candidate is locked as of May 21, 2026."

The `draft` changelog is empty ("Changes since the most recent release will accumulate here."), so
nothing after `2026-07-28` is pending in normative text.

| Revision | Lifecycle | Transport | Sessions | Authorization |
|---|---|---|---|---|
| **2024-11-05** | "The initialization phase **MUST** be the first interaction"; client sends `initialize`, then "**MUST** send an `initialized` notification"; operation: both "**SHOULD**" respect the negotiated version | stdio and HTTP+SSE (GET opens an SSE stream; server sends an `endpoint` event; client POSTs) | none at protocol level | no authorization page (404); transport: "Servers **SHOULD** implement proper authentication" |
| **2025-03-26** | same handshake | Streamable HTTP replaces HTTP+SSE (PR #206); JSON-RPC batching added (PR #228) | introduced: a server "**MAY** assign a session ID at initialization time … in an `Mcp-Session-Id` header" | OAuth 2.1 framework added (PR #133), "Authorization is **OPTIONAL**" |
| **2025-06-18** | "Change **SHOULD** to **MUST** in Lifecycle Operation" | batching removed (PR #416); `MCP-Protocol-Version` header required on later HTTP requests (PR #548) | unchanged (MAY assign) | servers become OAuth Resource Servers with protected resource metadata (PR #338); clients MUST use RFC 8707 resource indicators (PR #734); security best practices page added |
| **2025-11-25** | unchanged; `Implementation` gains `description` | SSE polling, servers may disconnect at will (SEP-1699); invalid `Origin` → 403 (PR #1439) | unchanged; best practices: "MCP Servers **MUST NOT** use sessions for authentication", bind as `<user_id>:<session_id>` | OIDC discovery (PR #797); incremental scope consent (SEP-835); Client ID Metadata Documents (CIMD) recommended (SEP-991); RFC 9728 alignment (SEP-985) |
| **2026-07-28** (Current) | handshake removed (SEP-2575); `server/discover` added, MUST implement, MAY call | GET stream, resumability and server-sent requests removed; `subscriptions/listen`; MRTR replaces server-initiated requests (SEP-2322); `Mcp-Method` / `Mcp-Name` required (SEP-2243) | removed (SEP-2567) | `iss` validation (SEP-2468); `application_type` in DCR (SEP-837); credentials bound to issuer (SEP-2352); DCR deprecated in favour of CIMD (PR #2858) |

## 2. The reviewer's claim, checked

### The revision exists and is Current

Versioning page: "The **current** protocol version is **2026-07-28**."
`https://modelcontextprotocol.io/specification/latest` redirects (307) to `/specification/2026-07-28`.
The 2026-07-28 changelog, major changes 1 and 2:

> Remove protocol-level sessions and the `Mcp-Session-Id` header from the Streamable HTTP transport.
> … Servers that need cross-call state use explicit, server-minted handles passed as ordinary tool
> arguments (SEP-2567).

> Make MCP stateless: remove the `initialize`/`notifications/initialized` handshake. Every request
> now carries its protocol version and client capabilities in `_meta` … Clients SHOULD identify
> themselves on each request (`io.modelcontextprotocol/clientInfo`), and servers SHOULD identify
> themselves in each result's `_meta` … Version mismatches return `UnsupportedProtocolVersionError`
> (SEP-2575).

The lead maintainers' release post (2026-07-28) says: "we've officially retired the
initialize/initialized exchange along with the Mcp-Session-Id header (refer to SEP-2575, SEP-2567)".
The `2026-07-28/basic/lifecycle` URL now redirects (308) to `basic/versioning`. There is no
lifecycle page any more.

### `initialize`: removed from the protocol, optional for legacy interop

- Versioning page: "There is no negotiation handshake. Every request carries its protocol version,
  and the server accepts or rejects each request independently".
- Terms: **Modern** = "revision `2026-07-28` and later". **Legacy** = "protocol versions that
  establish a session with an `initialize` handshake (`2025-11-25` and earlier)".
- "A server that wishes to support both legacy clients … and modern clients … **MAY** implement both
  behaviors." A dual-era server picks the era per request: "A request carrying modern per-request
  `_meta` is served statelessly … An `initialize` request selects legacy semantics, scoped to the
  stdio process (stdio) or the session (HTTP)". It "**MAY** serve both eras concurrently on the same
  endpoint or process."
- Not deprecated: the [deprecated registry](https://modelcontextprotocol.io/specification/2026-07-28/deprecated)
  lists Roots, Sampling, Logging, DCR, two `includeContext` values and HTTP+SSE only. Its Removed
  section says "No features have been removed under this policy yet." SEP-2575 calls the change "a
  **fundamental, backward-incompatible change**", so the twelve-month deprecation window never
  applied to the handshake.

### Sessions: removed

Streamable HTTP 2026-07-28 says: "Revision 2026-07-28 changed the behavior of Streamable HTTP …
Removal of the GET stream endpoint. Removal of protocol-level sessions." A modern-only server
receiving old traffic SHOULD:

- answer "HTTP GET or DELETE to the MCP endpoint" with "`405 Method Not Allowed`";
- treat "An `Mcp-Session-Id` header on a request" this way: "ignore it, and do not mint or echo
  session IDs";
- ignore "A `Last-Event-ID` header".

The base protocol now has a normative Statelessness section:

> Servers **MUST NOT** rely on prior requests over the same connection to establish context (e.g.,
> capabilities, protocol version, client identity). Every request supplies this metadata in its
> `_meta` field. … State that needs to span multiple requests … **MUST** be referenced by an
> explicit identifier the client passes on each request.

> … a server must not treat connection or process identity as a proxy for conversation or session
> continuity.

### Per-request metadata now on the wire

| Where | Field | Status | Note |
|---|---|---|---|
| body `params._meta` | `io.modelcontextprotocol/protocolVersion` | **required** | missing → "malformed; the server **MUST** reject it with … `-32602`", HTTP 400 |
| body `params._meta` | `io.modelcontextprotocol/clientCapabilities` | **required** | server "**MUST NOT** rely on capabilities the client has not declared" (`-32021`) |
| body `params._meta` | `io.modelcontextprotocol/clientInfo` | optional | "Clients **SHOULD** include … on every request unless specifically configured not to do so" |
| body `params._meta` | `io.modelcontextprotocol/logLevel`, `progressToken` | optional | log level replaces `logging/setLevel` |
| body `params._meta` | `traceparent`, `tracestate`, `baggage` | optional | W3C trace context (SEP-414) |
| result `_meta` | `io.modelcontextprotocol/serverInfo` | SHOULD | self-reported by the server |
| HTTP header | `MCP-Protocol-Version` | **MUST** on every POST | "**MUST** match" the `_meta` value, else 400 + `HeaderMismatch` |
| HTTP header | `Mcp-Method`; `Mcp-Name` | **REQUIRED** | `Mcp-Name` for `tools/call`, `resources/read`, `prompts/get`; base64 sentinel `=?base64?…?=` for unsafe values |
| HTTP header | `Mcp-Param-{Name}` | MUST, when the tool's schema marks a parameter with `x-mcp-header` | server "**MUST** validate that encoded header values … match" the body (`-32020`) |
| HTTP header | `Authorization: Bearer …` | MUST when authorization is used | "authorization **MUST** be included in every HTTP request" |

Two points matter for us.

- **`clientInfo` was weakened after SEP-2575 was finalized.** SEP-2575 lists it as **Required**.
  Its "Changes since SEP became Final" section records that PR #3002 "made
  `io.modelcontextprotocol/clientInfo` optional". So its absence is legal.
- **The spec's warning on self-reported identity.** It reads: "`clientInfo` and `serverInfo` are
  self-reported by the sender and are not verified by the protocol … Implementations **SHOULD NOT**
  use them to change the behavior of the client or server, and **SHOULD NOT** rely on them for
  security decisions." `docs/project/gateway-architecture.md` says "must not". The spec says
  SHOULD NOT.

The header/body rule exists for gateways. The spec says it "prevents potential security
vulnerabilities when different components in the network rely on different sources of truth (e.g.,
a load balancer routing on the header value while the MCP server executes based on the body
value)". Intermediaries that act on headers "**SHOULD** verify that the `MCP-Protocol-Version`
header indicates a version that requires header–body validation. If the version is older or the
header is absent, the intermediary **SHOULD** reject the request rather than trusting unvalidated
header values."

### Negotiation and backward compatibility

- **Per request.** If the version is unsupported the server "**MUST** respond with an
  `UnsupportedProtocolVersionError`" (`-32022`, HTTP 400) listing `supported`. `server/discover` is
  "a mandatory RPC" for servers. For clients, "Calling it is optional".
- **Era detection.** It is done by the client and differs by transport. Over HTTP the client
  "attempt[s] a modern request and inspect[s] the body of a `400 Bad Request` before falling back".
  Over stdio it probes with `server/discover`. Clients "**SHOULD** cache the result for the
  lifetime of the server process (stdio) or origin (HTTP)".
- **Outcomes.** Legacy client to modern-only server: "Fails … Legacy clients have no fall-forward
  mechanism." A modern-only server "**SHOULD** name the protocol versions it supports in any error
  it returns to an `initialize` request".
- **Pre-2025-06-18 clients.** A server that still supports them "**MAY** treat a request that omits
  the header as protocol version `2025-03-26`".

### How long older revisions will be in use

The spec sets no end date for legacy revisions. The relevant facts:

- **Feature lifecycle policy.** It governs features, not revisions. "Removal from the specification
  does not oblige an SDK to drop the feature from releases. That timeline is governed by the SDK's
  own revision-support policy."
- **SDK beta post (2026-06-29):**
  - "nothing breaks on July 28 either. This is merely the date when the normative specification
    text is published and is not a switch-off".
  - "the TypeScript SDK will continue shipping v1.x bug fixes and security updates for at least six
    months, and the Python v1.x branch continues to receive critical bug fixes and security
    patches".
  - Modern serving is opt-in in two SDKs: "In the TypeScript and Go SDKs, the opt-in extends to the
    wire". In Go, without `StreamableHTTPOptions.Stateless = true`, "clients negotiate down to
    2025-11-25".
  - Python v2 and C# answer both eras.
  - "clients that speak 2026-07-28 fall back to the initialize handshake when they reach a server on
    2025-11-25 or earlier".

So an upgraded Go or TypeScript server keeps speaking legacy until its operator opts in, and new
clients keep using `initialize` against such servers. In this repo, every captured message (the
`runs/gateway/*` and `logs/proxy/sessions/*` logs) carries `2025-11-25`.

## 3. Caller identity a gateway gets per request (2026-07-28)

| Signal | Source | Verified? | Notes |
|---|---|---|---|
| Bearer token: issuer, subject, `client_id`, scopes, expiry, token id, actor | `Authorization` header, every HTTP request | **yes**, if authorization is used | server "**MUST** validate that access tokens were issued specifically for them as the intended audience" (RFC 8707); "**MUST NOT** accept or transit any other tokens". The claims available depend on the authorization server's token format; MCP does not fix one. Authorization is "**OPTIONAL**"; stdio "**SHOULD NOT**" use it |
| `client_id` as an HTTPS URL (CIMD) | token / authorization server | partly | "The `client_id` URL **MUST** use the "https" scheme and contain a path component"; security considerations: "Client ID Metadata Documents cannot prevent `localhost` URL impersonation by themselves." |
| Enterprise subject (ID-JAG) | Enterprise-Managed Authorization extension | yes | "ID-JAG tokens will always contain a subject claim and may additionally contain an email claim" |
| `clientInfo` name/version | `_meta` | **no** | optional; SHOULD NOT be relied on for security decisions |
| `clientCapabilities` | `_meta` | no | required on every request; its shape (keys, `extensions`) is a fingerprint of the client implementation |
| `protocolVersion` | `_meta` and `MCP-Protocol-Version` | no, but the two must match | a mismatch is a MUST-reject |
| `Mcp-Method`, `Mcp-Name`, `Mcp-Param-*` | headers | must equal the body | a mismatch or a missing header is a MUST-reject (`-32020`) |
| `traceparent` | `_meta` | no | optional; groups calls of one trace when the client propagates it |
| `Origin`, client address, `User-Agent` | HTTP | no | servers "**MUST** validate the `Origin` header" (403 if invalid) |

Not in the spec yet. The 2026-08-22 roadmap says the agent-identity work "covers finalizing
Demonstrating Proof of Possession (DPoP) and driving its adoption, and defining an opinionated path
for agent identity and delegation through Workload Identity Federation, the ID-JAG grant behind
Enterprise-Managed Authorization, and standard token exchange." Today a gateway cannot tell an agent
from the human client app holding the same token, except through the token's own claims.

SEP-2575 shifts identity onto authentication: "Without a session handshake, every request must be
independently authenticated and authorized." SEP-2567 names the replacement grouping key. Telemetry
keyed on the session ID must move to "typically the authenticated principal (bearer token subject,
API key) or a request-level correlation ID". Gateways should "route by authenticated principal, or a
cookie / gateway-issued header".

## 4. Consequences for the dynamic layer and the gateway

### `protocol_skip` (missing handshake)

`engine.py` raises it only when `warm and session and not session.initialized and
normally_initializes`. Under 2026-07-28 there is no `Mcp-Session-Id`, so `Message.session` is
`None` and the flag can never fire. The design's question ("did this call come from the program he
normally uses?") is still a good one. Only its legacy test is gone. The paper's sentence "Every MCP
session starts with an `initialize` handshake" (`DYNAMIC-LAYER-V4-NOTES.md`, missing-handshake
paragraph) cites `mcp2026spec`, an unversioned URL accessed 2026-07-30. On that date the cited spec
said the opposite. Cite `2025-11-25/basic/lifecycle` for the legacy claim and `2026-07-28` for the
modern one. The same applies to the `2025-06-18/basic/lifecycle` link in `DIMENSION_FORMULAS.md`
(Sources) and to the "negotiated protocol version … exchanged during the handshake" and "sessions
that connect but never complete the handshake" sentences in `main-restructured.tex` (~l. 600–618).

There is a second, legacy-era caveat. SEP-2567 surveyed deployed clients: "ChatGPT creates a fresh
session for every individual tool call … most desktop and IDE clients create one at application
launch … web clients typically create one per page load. Almost no clients resume a prior session".
Per-agent baselining absorbs a stable client habit. A client switch or update still changes the
session pattern without any change in the agent's behaviour.

### `session_length` (session duration)

It is computed as `(m.ts - session.start)` and only `if session`. Under 2026-07-28 it never takes
part, so Typical Cadence loses a dimension without any notice. Even in the legacy era, SEP-2567
says session lifetime "is undefined" and depends on the host. Some clients use one tool call per
session, others keep one session for a whole app launch. The dimension therefore measures the
client's architecture as much as the caller's behaviour.

### Other session-dependent paths (found while reading the code)

- **Unsafe sequence, `requires_before`: a false positive in the modern era.** The rule is
  `if needed and not (session and session.tools & needed): return True`. With `session is None`
  this is always true. I reproduced it with `BehaviourEngine(BehaviourConfig(requires_before=
  {"merge_pull_request": {"get_pull_request"}}))`: every merge was preceded by its review, and the
  only difference was no session id.
  - Day 0: `sequence = 0.9`, M = 3.62.
  - Days 1–3: 0.45, 0.39, 0.36, through the habit discount.
  - The same calls with session ids: no `sequence`, M = 0.98.
  - `policy.py` learns `requires_before` only from sessioned traffic, but "written steps stay". Any
    org-written step, or one learned on a legacy route, fires on every modern call.
- **Unsafe sequence, "a write after reading a different sensitive asset in the session":** silently
  off. Only the per-agent 7-day `last_read` part still works.
- **Policy learning:** `requires_before` counts sessions only (`if m.session:`). A modern-only route
  learns no required steps.
- **Gateway:** `session_agent_mismatch` (`SessionBook.claim`), `SessionBook.listed` ("was this tool
  in this session's `tools/list`") and the per-session catalog digest all need a session, so they
  return nothing. DELETE as "session ended" is legacy only.
- **Gateway headers:**
  - `protocol_version = header or _meta`: the header wins and the two are never compared, although
    the spec makes a mismatch a MUST-reject.
  - `_header_mismatch` compares `Mcp-Method` / `Mcp-Name` only when they are present. A *missing*
    required header on a modern request is not flagged, and `Mcp-Param-*` is not checked.
  - The gateway reads the `_meta` keys `io.modelcontextprotocol/clientInfo` and
    `io.modelcontextprotocol/protocolVersion` correctly.
- **Simulator:** `normal_org_world.py` gives every message a session id. Its "stateless" bots only
  skip `initialize`, which is not what modern traffic looks like. All v4 results are legacy-era
  results.

## Proposed version-scoped replacements

**Era of a request.** The gateway can classify each request deterministically from the spec text
above:

- **Modern:** the body's `_meta` carries `io.modelcontextprotocol/protocolVersion`.
- **Legacy:** the request is `initialize`, carries `Mcp-Session-Id`, is a GET/DELETE, or has a
  `MCP-Protocol-Version` of `2025-11-25` or earlier.
- **Legacy, `2025-03-26` assumed:** no header at all.

Log the era on every line and report every result per era.

**Principal.** Key all behaviour state by the verified principal (issuer, subject, `client_id`).
`gateway.agent_id` already does this. Do not key it by session. This follows SEP-2567's own
migration advice.

| Today | Legacy (≤2025-11-25) | Modern (2026-07-28) | Replacement valid in both eras |
|---|---|---|---|
| `protocol_skip` | valid as designed | cannot fire | **conformance** red flag + **identity omitted** + **era/version change** (below) |
| `session_length` | valid but client-shaped | undefined | **spell length**: minutes since the principal's current run of calls began, a new run starting after an idle gap `G` (a constant calibrated on the org's own gaps) |
| sequence, `requires_before` | valid | fires on every call (bug) | the required tool called by the same principal within the current spell, or with the same state handle |
| sequence, read-then-write in session | valid | off | same check, scoped to the spell |
| `session_agent_mismatch` | valid (best practices: bind sessions to user) | cannot fire | **handle–principal mismatch**: a handle the server returned to principal A, presented as an argument by principal B ("State Handle Hijacking", 2026-07-28 best practices) |
| `client` (Typical Footprint) | from `initialize` | from `_meta`, optional | keep; add `protocol_version` and `capabilities_fingerprint` as rarity dimensions |

**Conformance (Red Flags, modern only).** Raise it when a modern request has any of these:

- a missing required `_meta` key;
- a missing `MCP-Protocol-Version` or `Mcp-Method`, or `Mcp-Name` where it is required;
- a header that differs from the body: protocol version, method, name, or `Mcp-Param-*` after
  base64 decoding;
- legacy artefacts on a modern request: `Mcp-Session-Id` or `Last-Event-ID`.

Each is a spec MUST or SHOULD with a fixed error code, so it is "a line that holds for every agent".
That is the definition of the Red Flags group. A conforming server rejects these calls, so the harm
is not in the call itself. Keep the flag on the principal for a short window, so it raises his next
calls. Benign causes are an SDK bug or an intermediary that strips headers. Those show up for a
whole route at once, and the org-wide discount already handles that.

**Identity omitted (Red Flags, modern).** This is the direct heir of `protocol_skip`. Raise it when
a modern request carries no `clientInfo` and the principal normally sends it, on at least half of
his requests across at least 3 days. Use the existing `normally_initializes` pattern and the same
value 0.7 (×1.9), for the same reasons: a different program on his token is likely, and harm is not
implied. The spec lets clients be "configured not to" send it. The per-caller baseline turns the
flag off for those callers. In the current engine `client_family(None)` skips the client dimension,
so omission is invisible today.

**Era or version change (Typical Footprint).** Score the principal's (era, `protocolVersion`,
capabilities-shape) value as "rarer than his usual", like client app and network in v4. A principal
whose client has always been modern and who now sends `initialize` (a downgrade), or flips versions,
is unusual: the spec says clients SHOULD cache the era per origin. Benign causes are an SDK upgrade
(rare and one-way) or a second, older client. Pricing it by rarity rather than as a rule matches the
v4 decision to keep every "new for him" check in Typical Footprint.

**Token and client consistency (Typical Footprint, both eras with OAuth).** Learn org-wide which
`clientInfo` families appear with each verified `client_id` (for example a CIMD URL). A pair never
seen in the organisation is rare. One half of the pair is verified and the other is self-reported.

**How to defend self-reported fields against the spec's SHOULD NOT.** M takes the strongest
dimension. For a warm tool call, tool and time of day are always scored. So a self-reported field
can only *raise* M, never lower it below what the verified and behavioural dimensions give. A
spoofed `clientInfo` therefore cannot make a call look safer than it would without the field. It can
only fail to catch the spoofer. State in the paper that these signals catch unsophisticated misuse
(a script on a borrowed token) and not a careful attacker who copies the client's metadata.

**Paper and evaluation.**

- Present "missing handshake" as a legacy-era signal with the modern equivalent above, and cite
  versioned spec URLs.
- Add a modern-era (or mixed) variant of `normal_org_world.py`: no session ids, `_meta` on every
  request, and some clients that omit `clientInfo`.
- Report, per era: the `sequence` false-alarm rate, and whether the "personal script on the same
  token" episode is still caught once `protocol_skip` is gone.

## UNVERIFIED and open points

- Stable release dates of the TypeScript and Python v2 SDKs. These start the six-month v1.x clock,
  and I did not find them. The 2026-07-28 post says only that all four Tier 1 SDKs "speak
  2026-07-28 as of today".
- How many deployed servers have opted in to modern serving. No primary source for this exists.
- The token claims available (`client_id`, `act`, `azp`) depend on the authorization server. I did
  not open RFC 9068 or RFC 8693, so no claim about their content is made here.
- The idle gap `G` for spell length is a design parameter, not a standard. It must be calibrated on
  the org's own data.

## Sources

All accessed 2026-10-25.

- Versioning (Current revision, feature states): https://modelcontextprotocol.io/specification/versioning
- 2026-07-28 changelog: https://modelcontextprotocol.io/specification/2026-07-28/changelog
- 2026-07-28 versioning and compatibility (era model, matrix): https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning
- 2026-07-28 base protocol (`_meta`, statelessness, error codes): https://modelcontextprotocol.io/specification/2026-07-28/basic/index
- 2026-07-28 Streamable HTTP (headers, validation, backward compatibility): https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
- 2026-07-28 stdio (backward compatibility): https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio
- 2026-07-28 `server/discover`: https://modelcontextprotocol.io/specification/2026-07-28/server/discover
- 2026-07-28 authorization: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization
- 2026-07-28 client registration: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration
- 2026-07-28 authorization security considerations: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations
- 2026-07-28 deprecated registry: https://modelcontextprotocol.io/specification/2026-07-28/deprecated
- Draft changelog (empty): https://modelcontextprotocol.io/specification/draft/changelog
- Security best practices 2026-07-28 (state handle hijacking): https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
- Security best practices 2025-11-25 (session hijacking): https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices
- 2025-11-25 changelog: https://modelcontextprotocol.io/specification/2025-11-25/changelog
- 2025-11-25 lifecycle: https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle
- 2025-11-25 transports (session management): https://modelcontextprotocol.io/specification/2025-11-25/basic/transports
- 2025-11-25 authorization: https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
- 2025-06-18 changelog: https://modelcontextprotocol.io/specification/2025-06-18/changelog
- 2025-06-18 transports: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
- 2025-06-18 authorization: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
- 2025-03-26 changelog: https://modelcontextprotocol.io/specification/2025-03-26/changelog
- 2025-03-26 transports: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports
- 2025-03-26 authorization: https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization
- 2024-11-05 lifecycle: https://modelcontextprotocol.io/specification/2024-11-05/basic/lifecycle
- 2024-11-05 transports: https://modelcontextprotocol.io/specification/2024-11-05/basic/transports
- SEP-2575, Make MCP Stateless (Final): https://modelcontextprotocol.io/seps/2575-stateless-mcp
- SEP-2567, Sessionless MCP via Explicit State Handles (Final): https://modelcontextprotocol.io/seps/2567-sessionless-mcp
- Feature lifecycle and deprecation policy (SEP-2596): https://modelcontextprotocol.io/community/feature-lifecycle
- SDK tiers: https://modelcontextprotocol.io/community/sdk-tiers
- Enterprise-Managed Authorization extension: https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization
- GitHub releases API: https://api.github.com/repos/modelcontextprotocol/modelcontextprotocol/releases
- Blog, "The 2026-07-28 Specification" (Soria Parra, Delimarsky, 2026-07-28): https://blog.modelcontextprotocol.io/posts/2026-07-28/
- Blog, "The 2026-07-28 MCP Specification Release Candidate" (2026-05-21): https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- Blog, "Beta SDKs for the 2026-07-28 MCP Spec Release Candidate Are Here" (Weinberger, Isbey, Delimarsky, 2026-06-29): https://blog.modelcontextprotocol.io/posts/sdk-betas-2026-07-28/
- Blog, "The New MCP Roadmap" (2026-08-22): https://blog.modelcontextprotocol.io/posts/mcp-roadmap/
- Secondary, not used for any claim (search results only): blog.mcpservers.org, betterstack.com, composio.dev write-ups of 2026-07-28.
