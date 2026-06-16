# Asset Ranking Guidelines (Asset Class → Risk Level + Sensitivity)

How to fill in the **Asset Table** in `heatmap.xlsx` — one row per
asset class, three columns:

| Asset class | Risk Level | Sensitivity (1–5) | Reasoning |
|---|---|---|---|

This rubric is **MCP-agnostic**. The "asset class" is whatever the MCP
server exposes as the unit of access:

| MCP server | What "asset class" means | Example rows |
|---|---|---|
| Filesystem | File extension or filetype family | `.pem`, `.docx`, `.txt` |
| Database | Table / schema family | `auth.*`, `billing.*`, `public_views.*` |
| Email | Mailbox or folder class | inbox, drafts, archived |
| Source-control | Repository class | private repo, public mirror, secrets-bearing |
| Calendar / scheduling | Event class | board meeting, customer call, public |
| Browser / web | Data class | cookies, history, saved passwords |
| Cloud / IAM | Resource class | role policies, KMS keys, bucket ACLs |
| Messaging | Channel class | DMs, private channels, public channels |

Pick the right unit for *your* MCP server and the same five-step method
below applies.

Goal: every row pickable in under 30 seconds and defensible to a
security architect.

---

## The two columns relate

| Sensitivity | Risk Level | Plain meaning |
|---|---|---|
| 5 | Critical | Compromise = full takeover or kill-chain enabler |
| 4 | High | Compromise = significant IP / regulatory / financial hit |
| 3 | Medium | Compromise = real but bounded harm |
| 2 | Low | Compromise = embarrassment, minor leak |
| 1 | Minimal | Compromise = ~no business impact |

Sensitivity is the number the formula uses. Risk Level is the qualitative
label a stakeholder reads. They must always agree.

---

## How to think — 5 steps per asset class

### Step 1 — Apply FIPS 199 (NIST asset categorization)

Rate the asset class on the CIA triad:

| Dimension | Question |
|---|---|
| **Confidentiality** | If an attacker reads this asset, what's the worst that happens? |
| **Integrity** | If an attacker silently modifies this asset, what breaks? |
| **Availability** | If this asset is destroyed or denied, how much damage / downtime? |

Each gets **Low / Moderate / High**. Take the **max** — that's your
sensitivity floor.

| Max FIPS rating | Sensitivity floor |
|---|---|
| High on ≥ 2 of C/I/A | 5 (Critical) |
| High on 1 + Moderate on others | 4 (High) |
| Moderate across the board | 3 (Medium) |
| Low–Moderate | 2 (Low) |
| Low on all three | 1 (Minimal) |

### Step 2 — Find the MITRE Technique that targets this asset class

If a Technique ID names this asset class, that's your strongest anchor:

| Asset class | MITRE Technique | Suggests Sens |
|---|---|---|
| Credentials, keys, vaults, tokens | T1552 *Unsecured Credentials*, T1555 *Credentials from Password Stores* | 5 |
| OS / kernel / boot artifacts | T1543 *Create/Modify System Process*, T1547 *Boot Persistence* | 5 |
| Executable artifacts (scripts, binaries) | T1059 *Command and Scripting Interpreter*, T1204 *User Execution* | 5 |
| Source / build / IaC artifacts | T1195 *Supply Chain Compromise* | 4 |
| Knowledge / document repositories | T1213 *Data from Info Repositories* | 3–4 |
| Local data stores | T1005 *Data from Local System* | 3 |
| Cloud-resident data | T1530 *Data from Cloud Storage* | 3–4 |
| Email | T1114 *Email Collection* | 3–4 |
| Browser data | T1539 *Web Session Cookie*, T1555.003 *Browser Stores* | 4–5 |
| Public-by-default content | (no specific Technique) | 1–2 |

### Step 3 — Apply OWASP business-impact factors

OWASP Risk Rating Methodology lists four business-impact dimensions.
Bump the rank one level if **any** of these would apply to a leak of
this asset class:

- **Financial damage** — does loss cost real money?
- **Reputation damage** — would media cover it?
- **Non-compliance** — GDPR / HIPAA / SOX / PCI exposure?
- **Privacy violation** — identifiable individuals affected?

Same asset class can sit in different rows depending on content. A
"public dataset table" is Sens 1–2; an "internal customer-PII table"
is Sens 4 — same shape of object, OWASP factor decides.

### Step 4 — Check the kill-chain role

Ask which role this asset class usually plays in an attack:

| Role | Sens range | Examples (multi-MCP) |
|---|---|---|
| **Weapon** — directly executable / triggers action | 5 | binaries, RPC entry points, webhook targets |
| **Key** — enables authentication or lateral movement | 5 | private keys, OAuth tokens, session cookies, IAM role policies |
| **Crown jewel** — direct business asset | 4 | signed contracts, customer DB, financial records |
| **Payload vector** — format / object can carry exploits | 3–4 | macro-bearing docs, HTML emails, package manifests |
| **Passive data** — information value only | 3 | internal reports, PII tables, archived emails |
| **Reference / template** — low intrinsic value | 1–2 | READMEs, public images, sample data |

### Step 5 — Write the Reasoning cell

Don't just write the number. Always cite **one framework anchor** —
either FIPS, MITRE, or OWASP. Future-you reviewing the table needs to
know *why*, not just *what*.

Good reasoning examples (mixed MCPs):

- `private key file | Critical | 5 | FIPS H/H/H; T1552 — full pivot enabler`
- `auth.users table | Critical | 5 | T1213 + OWASP PII non-compliance` (database MCP)
- `session cookies | Critical | 5 | T1539 Web Session Cookie hijack` (browser MCP)
- `signed contract doc | High | 4 | T1213 + OWASP reputation factor`
- `public marketing image | Minimal | 1 | FIPS Low across CIA; no Technique target`

---

## Anchoring examples by category (illustrative, not exhaustive)

Use these as **anchors** to position new asset classes — find the
closest match, then justify any deviation. Examples span MCP types so
you can see the same Sens band across different kinds of asset.

### Critical / 5 — direct kill-chain enablers

- **Filesystem**: `.pem`, `.key`, `.exe`, `.sys`, `.env`
- **Database**: credentials / token tables, IAM mapping tables
- **Cloud / IAM**: KMS keys, role-assumption policies, root account creds
- **Browser**: saved-password vault, session cookies for admin domains
- **Source-control**: secrets-bearing repos, signed-release branches

MITRE: T1552, T1555, T1543, T1547, T1059, T1539.

### High / 4 — significant business / regulatory impact

- **Filesystem**: source code (`.c`, `.py`, `.go`), contracts (`.docx`),
  financials (`.xlsx`)
- **Database**: customer PII tables, financial-record tables, audit tables
- **Source-control**: private repos with production code
- **Email**: legal / HR mailboxes, executive accounts
- **Cloud**: production data buckets, infra-as-code state files

MITRE: T1195, T1213, T1530, T1114.

### Medium / 3 — real but bounded harm

- **Filesystem**: structured data (`.json`, `.csv` generic), internal `.pdf`
- **Database**: internal-only tables without PII, app configuration
- **Email**: general-staff mailboxes
- **Messaging**: private team channels
- **Calendar**: internal meetings

MITRE: T1005, T1213 (generic).

### Low / 2 — minor leak, embarrassment

- **Filesystem**: documentation (`.md`, `.txt`), images
- **Database**: lookup / reference tables (countries, currencies)
- **Email**: bulk notifications
- **Messaging**: public-channel content
- **Source-control**: public open-source mirrors

### Minimal / 1 — no business impact

- Public marketing assets, whitepapers, sample datasets, public docs
- No applicable MITRE Technique → Sens 1

---

## Common adjustments

- **Same class, different content**: PII vs. non-PII versions of the
  same shape sit at different Sens. Keep one row per *typical* content
  type; flag specific instances with a directory- or namespace-level
  bump (the Ctx multiplier in the formula exists for that exact reason
  — don't double-count by inflating Sens itself).
- **Active vs. passive formats**: macros, embedded scripts, template
  injection vectors → bump one level for T1204 *User Execution* risk.
- **Tokens with short TTL vs. long-lived**: long-lived → Sens 5;
  short-lived single-use → Sens 4.
- **Unknown class**: default to Sens 2 with reasoning `"unknown —
  pending review"`. Don't leave blank.

---

## Worked example — adding "saved-password vault" (browser MCP)

1. **FIPS 199**: Confidentiality = High (full credential cache),
   Integrity = High (tampering = silent credential bypass),
   Availability = High (recovery is painful). Max = High → Sens 5 floor.
2. **MITRE**: T1555.003 *Credentials from Web Browsers*. Direct match.
3. **OWASP business impact**: financial + reputation + non-compliance
   + privacy — all four fire.
4. **Kill-chain role**: Key (enables lateral movement at scale).
5. **Row**:
   `saved-password vault | Critical | 5 | T1555.003 Credentials from Web Browsers; FIPS H/H/H; credential cascade`

The five-step method works identically whether the row is `.pem`,
`auth.users`, or `saved-password vault`.

---

## Filling-in checklist

For any new asset class:

1. **Define the unit** — what does one row of the Asset Table mean for
   *this* MCP server (extension, table family, mailbox class, …)?
2. **Pick the closest existing row** as your anchor.
3. **Walk FIPS → MITRE → OWASP → kill-chain** (5 minutes max).
4. **Sanity-check** with the tie-breaker: *"If a leak of this asset
   class hit the press, would Legal be in the room?"* — yes → Sens ≥ 3.
5. **Write the row** with Risk Level + Sensitivity + a Reasoning cell
   that cites at least one framework anchor (T-code, FIPS rating, or
   OWASP factor).

If no FIPS High *and* no MITRE Technique fits the asset class, it's
almost certainly Sens 1–2 — a passive, low-value asset.

---

## Tool table — Risk Level, Blast Radius, and Tool Impact

The **Tool table** (separate from the Asset table) scores each tool by the
*capability* it grants — what an agent can **do** — not the data it touches.
One row per tool:

| Tool | Risk Level | Blast Radius (1–5) | Tool Impact | Reasoning |
|---|---|---|---|---|

### Step 1 — rank the tool's Risk Level (capability, not asset)

Use the same FIPS → MITRE → OWASP lens as assets, applied to the *action*:

- **FIPS**: weight **Integrity** and **Availability** (a tool changes or
  destroys state) above Confidentiality.
- **MITRE**: pick the Technique the capability enables — Impact tactic
  (T1485 *Data Destruction*, T1486 *Encrypted for Impact*), Collection /
  Exfiltration (T1005, T1114, T1567), Discovery (T1083, T1082), or
  Execution (T1059).
- **Blast Radius (1–5)**: how much one call can touch — a single record (1)
  up to the whole store or an external broadcast (5).

### Step 2 — read Tool Impact straight from the Risk Level (fixed mapping)

| Tool Risk Level | Tool Impact | Outcome class (MITRE) |
|---|---|---|
| **Critical** | **×3** | Destructive / unrecoverable — T1485, T1486, T1059 |
| **High** | **×3** | Overwriting / recursive / external send — same destructive class |
| **Medium** | **×2** | Recoverable modify — T1565 *Data Manipulation*, T1222 *File Permissions* |
| **Low** | **×1** | Read / metadata — no state change — T1005, T1083, T1082 |

Critical and High are both ×3 — if you can't decide between them the score
is unaffected; only the label differs.

### Filesystem tools (canonical example)

| Tool | Risk Level | Blast Radius | Tool Impact | Reasoning |
|---|---|---|---|---|
| `write_file` | High | 5 | ×3 | Creates/overwrites file content — T1565 / T1485 |
| `edit_file` | Medium | 4 | ×2 | Modifies existing content — T1565 |
| `move_file` | Medium | 4 | ×2 | Relocates / can clobber — T1565 |
| `list_dir` | Medium | 3 | ×2 | Enumerates directory — T1083 Discovery |
| `search` | Medium | 3 | ×2 | Scans across files — T1083 / T1005 |
| `read_file` | Low | 2 | ×1 | Reads content (exfil risk) — T1005 |
| `create_dir` | Low | 1 | ×1 | Staging only, no asset impact |
| `get_file_info` | Low | 1 | ×1 | Metadata only — T1082 |

### Don't overfit to filesystem — the same method across MCP types

The Risk Level → ×multiplier logic is **MCP-agnostic**; only the Technique
and blast radius change per server kind:

| MCP server | Tool (example) | Risk Level | Blast | Tool Impact | MITRE / reasoning |
|---|---|---|---|---|---|
| Database | `drop_table`, `write_query` | Critical | 5 | ×3 | T1485 destruction / raw-SQL exec |
| Database | `read_query` | Low | 2 | ×1 | T1005 — reads rows |
| Database | `list_tables` | Low | 1 | ×1 | T1083 — schema discovery |
| Cloud / IAM | `attach_role_policy` | Critical | 5 | ×3 | T1098 Account Manipulation — privilege escalation |
| Cloud / IAM | `delete_bucket` | Critical | 5 | ×3 | T1485 Data Destruction |
| Cloud / IAM | `list_buckets` | Low | 2 | ×1 | T1580 Cloud Infrastructure Discovery |
| Browser | `execute_script` | Critical | 5 | ×3 | T1059 — script in page context |
| Browser | `read_cookies` | Low | 2 | ×1 | T1539 Web Session Cookie (read) |
| Messaging | `post_message`, `send_dm` | High | 4 | ×3 | T1567 Exfil Over Web Service — irreversible send |
| Messaging | `list_channels` | Low | 1 | ×1 | discovery only |
| Source-control | `force_push`, `merge_pr` | High | 5 | ×3 | T1195 Supply-Chain Compromise |
| Email | `send_email` | High | 4 | ×3 | T1114 / T1567 — exfil + impersonation |
| Email | `read_email` | Low | 2 | ×1 | T1114 Email Collection (read) |

Cross-cutting patterns the examples show:

- **Outbound tools** (`post_message`, `send_email`) are High → ×3 even
  though they destroy no local state — the *send* itself is irreversible
  exfiltration (T1567).
- **Read / discovery tools** (`read_query`, `read_cookies`, `list_*`) are
  ×1 in every store — no state change to reverse.

> **Caveat on read-only tools.** `list_dir` / `search` are rated Medium
> above → ×2 by the fixed mapping, yet they change no state. If Tool Impact
> is meant to capture *irreversibility* (read ×1 / modify ×2 / destroy ×3),
> read-only enumeration should be ×1 regardless of Risk Level. Decide whether
> Tool Impact tracks **Risk Level** (current rule → ×2) or **irreversibility**
> (→ ×1); the two diverge only for high-blast read-only tools.

---

## References

- **NIST SP 800-60 Vol. 2 Rev. 1** — Appendices of data-type mappings
  to security categories
- **FIPS PUB 199** — CIA-based asset categorization
- **NIST SP 800-122** — Guide to Protecting PII
- **MITRE ATT&CK Enterprise Matrix** —
  <https://attack.mitre.org/matrices/enterprise/>
- **OWASP Risk Rating Methodology** —
  <https://owasp.org/www-community/OWASP_Risk_Rating_Methodology>
- **OWASP ASVS** — Application Security Verification Standard
  (asset-handling controls)
