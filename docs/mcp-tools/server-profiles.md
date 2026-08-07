# MCP Server Profiles

Hand-written organizational profiles for the 18 MCP servers this project scans —
13 LLM-scanned servers under [`reports/scan/`](../../reports/scan/) and 5 finance
servers under [`reports/scan_finance/`](../../reports/scan_finance/).

Each profile answers four things, in the threat direction this repo uses (**the
MCP server is the protected asset, the agent is the threat**):

1. **Who owns it** — the company and the MCP server implementation behind it.
2. **Expected organizational use** — what benign agent traffic is supposed to
   look like, so deviation is measurable.
3. **Asset severity** — the peak asset sensitivity the server can reach, on the
   repo's 1–5 scale (`asset_sensitivity` in each scan JSON).
4. **CIA emphasis** — which of confidentiality / integrity / availability
   actually carries the loss, per asset where the assets differ materially, and
   in general for the server as a whole.

Profile lengths are deliberately uneven. Each server is tagged with a length
tier (**XS / S / M / L / XL**) so the same profiles can be A/B'd as scanner
prompt context — the open question is how much organizational context the
scoring model actually needs before extra words stop moving the numbers. Tiers
are spread *within* each server kind (two filesystems get XL and XS, two GitHub
servers get L and S, …) so length is comparable against a near-identical tool
surface.

`*_cbg` / `*_real` naming: `cbg` variants are the seeded demo tenant of the
fictional **CBG — Consolidated Business Group**; `real` variants are scans of
the vendor's genuine published tool catalog (26-tool `github/github-mcp-server`,
16-tool Slack API surface, 13-tool Google Calendar surface) rather than the
trimmed demo catalog.

## Index

| Profile | Server id | Kind | Tools | Assets | Peak sens. | CIA priority | Tier | Words |
|---|---|---|---|---|---|---|---|---|
| [fs_fintech_fs](#fs_fintech_fs) | `fs:fintech_fs` | filesystem | 14 | 23 | 5 | C > I > A | XL | 493 |
| [fs_medical_clinic_fs](#fs_medical_clinic_fs) | `fs:medical_clinic_fs` | filesystem | 14 | 21 | 5 | C > I > A | L | 346 |
| [fs_corp_filesystem](#fs_corp_filesystem) | `fs:corp_filesystem` | filesystem | 14 | 15 | 5 | C ≈ I > A | M | 178 |
| [fs_law_firm_fs](#fs_law_firm_fs) | `fs:law_firm_fs` | filesystem | 14 | 22 | 4 | C > I > A | S | 116 |
| [fs_media_studio_fs](#fs_media_studio_fs) | `fs:media_studio_fs` | filesystem | 14 | 21 | 4 | I > C > A | XS | 53 |
| [github_real](#github_real) | `github:real` | GitHub repo mgmt | 26 | 6 | 5 | I > C > A | L | 292 |
| [github_cbg](#github_cbg) | `github:cbg` | code repo mgmt | 11 | 6 | 5 | I > C > A | S | 94 |
| [slack_real](#slack_real) | `slack:real` | communication | 16 | 10 | 4 | C > I > A | M | 154 |
| [slack_cbg](#slack_cbg) | `slack:cbg` | communication | 8 | 10 | 4 | C > I > A | XS | 49 |
| [sqlite_devops_sqlite](#sqlite_devops_sqlite) | `sqlite:devops_sqlite` | SQL database | 5 | 5 | 5 | I ≈ C > A | L | 308 |
| [sqlite_cbg_sqlite](#sqlite_cbg_sqlite) | `sqlite:cbg_sqlite` | SQL database | 5 | 7 | 5 | C > I > A | S | 100 |
| [calendar_real](#calendar_real) | `calendar:real` | calendar mgmt | 13 | 6 | 4 | C > A > I | M | 169 |
| [calendar_cbg](#calendar_cbg) | `calendar:cbg` | calendar mgmt | 11 | 6 | 5 | C > I > A | XS | 57 |
| [maverick](#maverick) | `maverick-mcp` | finance / trading | 119 | — | 5 | I > A > C | XL | 472 |
| [finance_tools](#finance_tools) | `finance-tools-mcp` | finance data | 17 | — | 3 | A > I > C | L | 257 |
| [openbb](#openbb) | `openbb-platform` | finance data | 30 | — | 4 | A > I > C | M | 159 |
| [sec_edgar](#sec_edgar) | `sec-edgar-mcp` | regulatory filings | 21 | — | 2 | I > A > C | S | 98 |
| [yahoo_finance](#yahoo_finance) | `yfinance` | market data | 9 | — | 2 | A > I > C | XS | 62 |

Finance servers have no `assets` column: they are scanned by the deterministic
layer (`scripts/scan_finance.py`), which ranks tools by atomic-op severity and
does not build an asset matrix. Their "peak sens." is the top tool severity.

## Conformance

Sections are written against the
[MCP Server Profile Spec](../standards/mcp-profile-spec.md). Seven servers are at
**L3** — every asset carries a `Contents` cell stating what it holds, plus the
flags (`self-sufficient`, `population`, `completeness-is-the-asset`,
`metadata-only`, `hub`, `public`) that enumeration cannot know:

`fs_fintech_fs` · `fs_medical_clinic_fs` · `fs_corp_filesystem` · `github_real` ·
`slack_real` · `calendar_real` · `sqlite_devops_sqlite`

Their `Contents` facts (table columns, file extensions, directory file counts)
are generated from the real store by
`scripts/emit_profile_skeleton.py`, so they cannot drift into fiction by
transcription error; the meaning, the flags and the judgement columns are
hand-authored. Every one of the seven covers 100% of the assets its scan
enumerates.

The remaining eleven sections are prose-only (**L0**): the six demo-tenant
servers, which are not `ult` targets, and the five finance servers, which have no
asset matrix to tabulate. Adding a table to any of them is the
`emit_profile_skeleton.py` → fill → `--check-profiles` loop from the spec.

---

## Filesystem servers

All five run the same official Anthropic filesystem MCP server
(`@modelcontextprotocol/server-filesystem`, 14 tools) over a different tenant's
file tree. The tool surface is identical; **only the organization changes**,
which makes this group the cleanest test of whether org context alone moves the
score.

### fs_fintech_fs

**Tier: XL** · `fs:fintech_fs` · 14 tools · 23 assets · peak sensitivity **5**

**Company.** Fintech Ops — a card-present and card-not-present payments platform
that authorizes, settles, and reconciles transactions on behalf of merchant
customers. It is a PCI-DSS in-scope environment: the file share it exposes
carries a card vault, KYC identity documents, settlement ledgers, and live
production credentials. This is the highest-consequence filesystem tenant in the
corpus, and the only one where a single successful read is simultaneously a
regulatory breach, a fraud enabler, and a production compromise.

**Expected organizational use.** The agent is an operations assistant. Benign
traffic is narrow and repetitive: read `payments/settlements/*.csv` to reconcile
a day's batch, read a named `customers/cust_XXXX/profile.json` to answer a single
support ticket, read `marketing/launch_2026.md`, and occasionally write a
reconciliation summary into a scratch path. Legitimate agents address **one
customer at a time by id** and never need `security/secrets/`, never need
`payments/card_vault/`, and never need directory-wide enumeration of
`customers/`. Any traversal that walks the customer tree, any glob over the
vault, and any read of `security/` is out-of-policy by definition rather than by
degree.

**Asset severity and CIA, per asset.**

| Asset | Sens. | C | I | A | Contents | Why |
|---|---|---|---|---|---|---|
| `README.md` | 1 | L | L | L | file · ext:md | Public overview. |
| `customers/cust_0001/kyc_passport.png` | 5 | **H** | M | L | file · ext:png · a government identity document for one customer | Government identity document — identity-theft grade PII. |
| `customers/cust_0001/profile.json` | 4 | **H** | M | L | file · ext:json · one customer's identity and account record | Customer PII; damaging but not instantly weaponizable. |
| `customers/cust_0002/profile.json` | 4 | **H** | M | L | file · ext:json · one customer's identity and account record | Customer PII; damaging but not instantly weaponizable. |
| `marketing/launch_2026.md` | 3 | M | L | L | file · ext:md · unannounced launch plan, embargoed until release | Pre-announcement embargo only. |
| `payments/card_vault/pan_tokens.csv` | 5 | **H** | H | M | file · ext:csv · one row per card token; the whole cardholder set · population | Cardholder data; confidentiality drives statutory breach notification. |
| `payments/settlements/2026-05_settlement.csv` | 4 | M | **H** | M | file · ext:csv · one row per settled transaction, real amounts · population | Money movement; an edited row misdirects real funds and surfaces days later. |
| `security/audit/access_log.txt` | 4 | M | **H** | **H** | file · ext:txt · append-only access record; the completeness is the evidence · completeness-is-the-asset | Forensic record; deletion destroys the ability to prove what an agent did. |
| `security/secrets/db_root_password.txt` | 5 | **H** | H | M | file · ext:txt · the primary database root password, usable alone · self-sufficient · hub | Root database credential; one read is total database compromise. |
| `security/secrets/stripe_api_key.txt` | 5 | **H** | H | M | file · ext:txt · the live processor key, complete and usable alone · self-sufficient · hub | Live processor credential; disclosure is instant lateral movement into the payment rail. |
| `source/payment_gateway.py` | 4 | M | **H** | M | file · ext:py · the authorization path that moves money · hub | Executable authorization logic; a write is a supply-chain change to money handling. |
| `/` | 4 | **H** | H | M | directory · directory scope 'store root' containing 11 file(s) [csv, json, md, png, py, txt] — one enumeration exposes all of them (ext: csv, json, md, png, py, txt) · scope of / | Root scope — broad enough to reach the vault and the secrets. |
| `customers/` | 4 | **H** | M | L | directory · directory scope 'customers' containing 3 file(s) [json, png] — one enumeration exposes all of them (ext: json, png) · scope of customers/ · every customer folder; one tree walk is the full customer set · population | One tree walk converts a single-record leak into the full customer set. |
| `security/` | 4 | **H** | H | M | directory · directory scope 'security' containing 3 file(s) [txt] — one enumeration exposes all of them (ext: txt) · scope of security/ · parent of secrets and audit · self-sufficient · hub | Parent of secrets and audit. |
| `customers/cust_0001/` | 4 | **H** | M | L | directory · directory scope 'customers/cust_0001' containing 2 file(s) [json, png] — one enumeration exposes all of them (ext: json, png) · scope of customers/cust_0001/ · one customer's folder | One customer's folder. |
| `payments/` | 4 | M | **H** | M | directory · directory scope 'payments' containing 2 file(s) [csv] — one enumeration exposes all of them (ext: csv) · scope of payments/ · parent of the vault and the ledger · population | Parent of the vault and the ledger. |
| `security/secrets/` | 5 | **H** | H | M | directory · directory scope 'security/secrets' containing 2 file(s) [txt] — one enumeration exposes all of them (ext: txt) · scope of security/secrets/ · holds both live credentials · self-sufficient · hub | Both live credentials in one scope — a single listing-plus-read is the whole vault. |
| `customers/cust_0002/` | 4 | **H** | M | L | directory · directory scope 'customers/cust_0002' containing 1 file(s) [json] — one enumeration exposes all of them (ext: json) · scope of customers/cust_0002/ · one customer's folder | One customer's folder. |
| `marketing/` | 2 | M | L | L | directory · directory scope 'marketing' containing 1 file(s) [md] — one enumeration exposes all of them (ext: md) · scope of marketing/ · marketing working files | Ordinary marketing working files. |
| `payments/card_vault/` | 5 | **H** | H | M | directory · directory scope 'payments/card_vault' containing 1 file(s) [csv] — one enumeration exposes all of them (ext: csv) · scope of payments/card_vault/ · the cardholder vault · population | The vault scope; one call reaches every token. |
| `payments/settlements/` | 4 | M | **H** | M | directory · directory scope 'payments/settlements' containing 1 file(s) [csv] — one enumeration exposes all of them (ext: csv) · scope of payments/settlements/ · the settlement ledger · population | The settlement ledger scope. |
| `security/audit/` | 4 | M | **H** | **H** | directory · directory scope 'security/audit' containing 1 file(s) [txt] — one enumeration exposes all of them (ext: txt) · scope of security/audit/ · the audit scope · completeness-is-the-asset | The audit scope; erasure is itself the attack. |
| `source/` | 3 | M | **H** | M | directory · directory scope 'source' containing 1 file(s) [py] — one enumeration exposes all of them (ext: py) · scope of source/ · the gateway source tree · hub | The gateway source tree. |
| `file-contents` | 5 | **H** | H | M | surface · reach of the tool that homes here · what a content read returns; inherits the vault and the secrets | A content read here inherits the vault and the secrets. |
| `media-records` | 5 | **H** | M | L | surface · reach of the tool that homes here · image reads — the KYC passport scans | Image reads reach the KYC passport scans. |
| `file-records` | 4 | M | **H** | M | surface · reach of the tool that homes here · what a write or overwrite targets; any file in the share | A write targets any file, including the gateway and the ledger. |
| `directory-structure` | 2 | M | L | L | surface · reach of the tool that homes here · recursive tree of names and paths, no contents · metadata-only | Recursive names and paths; reconnaissance, not exfiltration. |
| `directory-contents` | 2 | M | L | L | surface · reach of the tool that homes here · one directory listing, no contents · metadata-only | One listing; names only. |
| `file-directory` | 2 | M | L | L | surface · reach of the tool that homes here · search over names and paths · metadata-only | Search over names and paths. |
| `file-metadata` | 1 | L | L | L | surface · reach of the tool that homes here · sizes, timestamps, permissions; never contents · metadata-only | Sizes and timestamps; never contents. |

**CIA in general.** **C > I > A.** The dominant loss is disclosure — secrets,
PAN tokens, and KYC documents are all confidentiality-first, and three of them
sit at sensitivity 5. Integrity is a close second and concentrated in exactly
three places (settlements, audit log, gateway source), which is where the four
write-capable tools (`write_file`, `edit_file`, `move_file`, `create_directory`)
should be gated hardest. Availability is the weakest axis: the file share is not
in the authorization path, so deleting files degrades reporting rather than
stopping payments — except for `security/audit/`, where availability loss is
itself the attack.

### fs_medical_clinic_fs

**Tier: L** · `fs:medical_clinic_fs` · 14 tools · 21 assets · peak sensitivity **5**

**Company.** A small outpatient medical clinic — two practising clinicians, a
front desk, and a billing contractor. The file tree is the clinic's entire
patient record system, so it is a HIPAA covered-entity asset with no
compensating segmentation: patient charts, diagnostic imaging, and billing all
sit in one share behind one MCP server.

**Expected organizational use.** The agent drafts visit summaries, looks up a
named patient's history before an appointment, and prepares invoices. Benign
access is **single-patient, by name, on demand**. The clinic never has a
legitimate reason for an agent to enumerate `patients/` wholesale or to batch-read
every chart — that shape is the signature of exfiltration, not of care delivery.

**Asset severity and CIA, per asset.**

| Asset | Sens. | C | I | A | Contents | Why |
|---|---|---|---|---|---|---|
| `README.md` | 1 | L | L | L | file · ext:md | Fictional overview. |
| `billing/invoices/inv_2026-05-20_alice_johnson.txt` | 4 | **H** | M | L | file · ext:txt · one invoice linking a patient to a service | Financial PII linking patient to service. |
| `billing/invoices/inv_2026-05-21_bob_martinez.txt` | 4 | **H** | M | L | file · ext:txt · one invoice linking a patient to a service | Financial PII linking patient to service. |
| `patients/alice_johnson/intake_form.txt` | 5 | **H** | H | M | file · ext:txt · one patient's intake PHI | PHI; confidentiality is the statutory harm. |
| `patients/alice_johnson/medical_history.txt` | 5 | **H** | H | M | file · ext:txt · one patient's diagnosis history | Diagnosis history — the most sensitive PHI the clinic holds. |
| `patients/alice_johnson/prescription.txt` | 5 | **H** | **H** | M | file · ext:txt · active medication and dose for one patient; a wrong value injures a person | Integrity is a patient-safety harm: an altered dose can injure a person. |
| `patients/bob_martinez/intake_form.txt` | 5 | **H** | H | M | file · ext:txt · one patient's intake PHI | PHI; confidentiality is the statutory harm. |
| `patients/bob_martinez/medical_history.txt` | 5 | **H** | H | M | file · ext:txt · one patient's diagnosis history | Diagnosis history — the most sensitive PHI the clinic holds. |
| `patients/bob_martinez/prescription.txt` | 5 | **H** | **H** | M | file · ext:txt · active medication and dose for one patient; a wrong value injures a person | Integrity is a patient-safety harm: an altered dose can injure a person. |
| `policies/hipaa_notice.txt` | 4 | L | **H** | M | file · ext:txt · the published HIPAA notice; public text, but the clinic's compliance artifact | Public text, but the clinic's compliance artifact — tampering is a regulatory finding. |
| `scans/alice_johnson_xray.png` | 4 | **H** | M | M | file · ext:png · a diagnostic image; the filename alone identifies the patient | Diagnostic image; the filename alone leaks PHI. |
| `scans/bob_martinez_xray.png` | 4 | **H** | M | M | file · ext:png · a diagnostic image; the filename alone identifies the patient | Diagnostic image; the filename alone leaks PHI. |
| `staff_directory.txt` | 4 | M | M | L | file · ext:txt · clinician and staff contact list | Employee contact data; reconnaissance for social engineering. |
| `/` | 3 | M | M | L | directory · directory scope 'store root' containing 13 file(s) [md, png, txt] — one enumeration exposes all of them (ext: md, png, txt) · scope of / | Root scope — the enumeration surface. |
| `patients/` | 5 | **H** | H | M | directory · directory scope 'patients' containing 6 file(s) [txt] — one enumeration exposes all of them (ext: txt) · scope of patients/ · every patient chart; one tree walk is the clinic's whole panel · population | One walk reaches the clinic's entire patient panel. |
| `patients/alice_johnson/` | 5 | **H** | H | M | directory · directory scope 'patients/alice_johnson' containing 3 file(s) [txt] — one enumeration exposes all of them (ext: txt) · scope of patients/alice_johnson/ · one patient's full chart | One patient's full chart. |
| `patients/bob_martinez/` | 5 | **H** | H | M | directory · directory scope 'patients/bob_martinez' containing 3 file(s) [txt] — one enumeration exposes all of them (ext: txt) · scope of patients/bob_martinez/ · one patient's full chart | One patient's full chart. |
| `billing/` | 4 | **H** | M | L | directory · directory scope 'billing' containing 2 file(s) [txt] — one enumeration exposes all of them (ext: txt) · scope of billing/ · the billing scope · population | The billing scope. |
| `billing/invoices/` | 4 | **H** | M | L | directory · directory scope 'billing/invoices' containing 2 file(s) [txt] — one enumeration exposes all of them (ext: txt) · scope of billing/invoices/ · all invoices · population | All invoices; disclosure-led. |
| `scans/` | 4 | **H** | M | M | directory · directory scope 'scans' containing 2 file(s) [png] — one enumeration exposes all of them (ext: png) · scope of scans/ · all diagnostic images; names leak PHI without reading a byte · population | All diagnostic images; the names are identifying on their own. |
| `policies/` | 3 | L | **H** | M | directory · directory scope 'policies' containing 1 file(s) [txt] — one enumeration exposes all of them (ext: txt) · scope of policies/ · published policy notices | Published policy notices. |
| `file-contents` | 5 | **H** | H | M | surface · reach of the tool that homes here · what a content read returns; inherits patient charts | A content read here inherits the patient charts. |
| `media-records` | 4 | **H** | M | M | surface · reach of the tool that homes here · image reads — the diagnostic scans | Image reads reach the diagnostic scans. |
| `file-records` | 5 | **H** | **H** | M | surface · reach of the tool that homes here · what a write or overwrite targets; any file, including prescriptions | A write targets any file, including prescriptions. |
| `directory-structure` | 3 | M | L | L | surface · reach of the tool that homes here · recursive tree of names and paths; patient names are in the paths · metadata-only | Patient names are in the paths, so even the tree leaks. |
| `directory-contents` | 2 | M | L | L | surface · reach of the tool that homes here · one directory listing, no contents · metadata-only | One listing; names only. |
| `file-directory` | 3 | M | L | L | surface · reach of the tool that homes here · search over names and paths · metadata-only | Search over names and paths. |
| `file-metadata` | 1 | L | L | L | surface · reach of the tool that homes here · sizes, timestamps, permissions; never contents · metadata-only | Sizes and timestamps; never contents. |

**CIA in general.** **C > I > A.** Disclosure of PHI is the headline loss and it
is irreversible. Integrity ranks unusually high for a filesystem because
prescriptions and the HIPAA notice both carry real-world consequence when
rewritten. Availability is lowest — a clinic this size can fall back to paper,
so file loss is disruptive but not the primary risk driver.

### fs_corp_filesystem

**Tier: M** · `fs:corp_filesystem` · 14 tools · 15 assets · peak sensitivity **5**

**Company.** CBG (Consolidated Business Group) corporate file share — the
general-purpose internal drive holding security material, finance records,
product source, and onboarding docs for a mid-size multi-business group.

**Expected organizational use.** A generalist internal assistant: search
onboarding material, summarize project docs, look up a schema, draft notes.
Nothing in the sanctioned workflow requires reading `sensitive/security/` or
writing to `source_code/`.

**Asset severity and CIA.** `sensitive/security/private_key.pem` (5) and the
`sensitive/security/` and root `/` scopes (5) are confidentiality-first — key
material plus a scope broad enough that one enumeration reaches everything.
`sensitive/financials/payslips_q1.csv` (4) is confidentiality-led PII;
`sensitive/security/audit_log.txt` (4) is integrity-and-availability-led, since
its value is being intact and complete; `source_code/core.c` and `source_code/`
(4) are integrity-led supply-chain assets. `projects/*` (3) is mixed and mild;
`onboarding/` (2) and `README.md` (1) are near-public.

| Asset | Sens. | C | I | A | Contents | Why |
|---|---|---|---|---|---|---|
| `README.md` | 1 | L | L | L | file · ext:md | Near-public. |
| `onboarding/org_chart.png` | 2 | L | L | L | file · ext:png · reporting lines; useful for social engineering | Org chart — routine internal. |
| `projects/db_schema.sql` | 3 | M | M | L | file · ext:sql · table and column definitions; no data values | Internal schema. |
| `projects/known_defects.csv` | 3 | M | M | L | file · ext:csv · open defect list, one row per defect | Internal defect list — embarrassing, not damaging. |
| `sensitive/financials/payslips_q1.csv` | 4 | **H** | M | L | file · ext:csv · one row per employee, gross pay and identifiers · population | Payroll PII. |
| `sensitive/security/audit_log.txt` | 4 | M | **H** | H | file · ext:txt · append-only action record; no single line matters, the whole is the evidence · completeness-is-the-asset | Value is being intact and complete. |
| `sensitive/security/private_key.pem` | 5 | **H** | M | L | file · ext:pem · a complete private key, usable on its own · self-sufficient · hub | Key material — exploitable the moment it leaks. |
| `source_code/core.c` | 4 | M | **H** | M | file · ext:c · product logic that ships to production · hub | Supply-chain integrity asset. |
| `/` | 5 | **H** | H | M | directory · directory scope 'store root' containing 8 file(s) [c, csv, md, pem, png, sql, txt] — one enumeration exposes all of them (ext: c, csv, md, pem, png, sql, txt) · scope of / | Root scope — broad enough to reach everything on the share. |
| `sensitive/` | 5 | **H** | H | M | directory · directory scope 'sensitive' containing 3 file(s) [csv, pem, txt] — one enumeration exposes all of them (ext: csv, pem, txt) · scope of sensitive/ · parent of the security and finance scopes · population | Parent of the security and finance scopes. |
| `projects/` | 3 | M | M | L | directory · directory scope 'projects' containing 2 file(s) [csv, sql] — one enumeration exposes all of them (ext: csv, sql) · scope of projects/ · project working files | Projects scope, mixed and mild. |
| `sensitive/security/` | 5 | **H** | H | L | directory · directory scope 'sensitive/security' containing 2 file(s) [pem, txt] — one enumeration exposes all of them (ext: pem, txt) · scope of sensitive/security/ · holds the key and the audit log together · self-sufficient · hub | The security scope; one enumeration reaches the key and the log. |
| `onboarding/` | 2 | L | L | L | directory · directory scope 'onboarding' containing 1 file(s) [png] — one enumeration exposes all of them (ext: png) · scope of onboarding/ · onboarding material | Near-public onboarding material. |
| `sensitive/financials/` | 4 | **H** | M | L | directory · directory scope 'sensitive/financials' containing 1 file(s) [csv] — one enumeration exposes all of them (ext: csv) · scope of sensitive/financials/ · holds the payroll extract · population | Finance scope. |
| `source_code/` | 4 | M | **H** | M | directory · directory scope 'source_code' containing 1 file(s) [c] — one enumeration exposes all of them (ext: c) · scope of source_code/ · the deployable source tree · hub | Source scope. |
| `file-contents` | 4 | **H** | M | L | surface · reach of the tool that homes here · what a content read returns; inherits the worst file it can reach | Generic file bodies across the share; characteristically mixed with restricted content. |
| `media-records` | 2 | L | L | L | surface · reach of the tool that homes here · binary/image reads | Media files; routine. |
| `file-records` | 3 | M | M | L | surface · reach of the tool that homes here · what a write or overwrite targets; any file in the share | Generic per-file records. |
| `directory-structure` | 2 | L | L | L | surface · reach of the tool that homes here · recursive tree of names and paths, no contents · metadata-only | Names and layout only — metadata. |
| `directory-contents` | 2 | L | L | L | surface · reach of the tool that homes here · one directory listing, no contents · metadata-only | Listings — metadata. |
| `file-directory` | 2 | L | L | L | surface · reach of the tool that homes here · search over names and paths · metadata-only | File locations — metadata. |
| `file-metadata` | 2 | L | L | L | surface · reach of the tool that homes here · sizes, timestamps, permissions; never contents · metadata-only | Sizes, timestamps, permissions. |

**In general: C ≈ I > A.** This tenant is the corpus's balanced case — a genuine
confidentiality asset (the PEM) and a genuine integrity asset (source code) at
the same sensitivity, with availability immaterial because the share is a
document store, not a running dependency.

### fs_law_firm_fs

**Tier: S** · `fs:law_firm_fs` · 14 tools · 22 assets · peak sensitivity **4**

**Company.** A litigation practice. The agent summarizes matter files, drafts
correspondence, and assembles timesheets — always scoped to one case or one
client.

**Asset severity and CIA.** Nearly everything sits flat at **4**: `cases/CASE-*/`
contract, correspondence, and signed agreements, `clients/*/intake.txt`,
`billing/timesheets/*`, and the `cases/`, `clients/`, `billing/` scopes.
Confidentiality dominates throughout — these are privileged communications, and
disclosure waives privilege irrecoverably. Integrity is second and matters most
on `signed_agreement.pdf` and `templates/nda_template.txt` (2), where a silent
edit propagates into executed contracts. Availability is minor.

**In general: C > I > A**, with the unusual property that the flat sensitivity
profile leaves the *tool* verb, not the asset, doing all the discrimination.

### fs_media_studio_fs

**Tier: XS** · `fs:media_studio_fs` · 14 tools · 21 assets · peak sensitivity **4**

Commercial photography studio; the agent tracks shoots and invoices. Client
contracts and invoices (4) are integrity-first — altered rates and terms are the
real loss — while shoot briefs and photos (3) are ordinary work product.
**I > C > A** overall; nothing here is regulated.

---

## Source-code servers

### github_real

**Tier: L** · `github:real` · 26 tools · 6 assets · peak sensitivity **5**

**Company.** CBG's engineering organization on `github/github-mcp-server`, the
vendor's own 26-tool catalog — the scanned surface includes write paths
(`create_or_update_file`, `push_files`, `merge_pull_request`, `create_branch`,
`create_repository`, `update_issue`, `update_pull_request_branch`) alongside a
wide read/search surface.

**Expected organizational use.** The agent is a code assistant with a
contributor's, not a maintainer's, mandate: read files, search code, list
commits and issues, open a PR, comment on a review. The organization expects
**proposal, not promotion** — every change lands through human review. The
crossing point is `merge_pull_request` and `push_files`, which bypass the review
gate entirely, and `create_or_update_file`, which writes to a branch directly.

**Asset severity and CIA, per asset** (scoring input — one row per registry
asset id):

| Asset | Sens. | C | I | A | Contents | Why |
|---|---|---|---|---|---|---|
| `public-website` | 1 | L | M | L | repository · already public; only defacement matters · public | Already public — only defacement is a real outcome. |
| `internal-docs` | 3 | M | M | L | repository · internal runbooks and knowledge | Internal knowledge; useful for reconnaissance. |
| `backend-api` | 4 | M | **H** | H | repository · core service code; a merge reaches production behavior · hub | Core service code; a merge reaches production behavior. |
| `payments-service` | 4 | M | **H** | H | repository · money-handling service code; a merge reaches live payment processing · hub | Money-handling code — the same shape as `backend-api` but with financial consequence per defect. |
| `infra-config` | 5 | H | **H** | **H** | repository · terraform and deploy config for the production estate; merges reconfigure production · hub | Terraform / deployment config. Integrity and availability lead: a merged change here reconfigures production, and a bad one takes the estate down. Confidentiality is high too because infra repos leak topology and credentials. |
| `ml-research` | 4 | **H** | M | L | repository · unpublished research, models and datasets | Unpublished research and model work; confidentiality-led, since the loss is competitive/priority rather than operational. |
| `branch-heads` | 4 | L | **H** | M | repository · where each branch points; a force-move rewrites what deploys · hub | Branch pointers decide what merges and deploys. |
| `issues-and-comments` | 3 | M | M | L | repository · issue threads and comments | Internal discussion; reconnaissance value. |
| `pull-requests-and-reviews` | 4 | M | **H** | M | repository · proposed changes and their approvals — the review gate itself · hub | The review gate itself; carries unmerged code. |
| `org-external-copies` | 4 | **H** | M | L | repository · forks pushed outside the org boundary; content leaves the org on creation · population | Copies of private code outside the org boundary. |
| `platform-user-directory` | 1 | L | L | L | repository · GitHub account records the org can search | Public GitHub user handles. |
| `repository-catalog` | 2 | L | L | L | repository · the list of repository names, no code · metadata-only | Names and list of repos — metadata. |
| `repository-contents` | 4 | M | **H** | M | repository · file contents of a repo; inherits the worst repo it can reach | Actual code contents across repos (generated). |
| `issue-records` | 3 | M | M | L | repository · what an issue write creates or edits | Issue bodies (generated). |
| `pull-request-records` | 4 | M | **H** | M | repository · what a PR write creates, edits or merges · hub | PR bodies and diffs (generated homing asset). |
| `branch-directory` | 2 | L | L | L | repository · branch names and refs, no contents · metadata-only | Branch names — metadata (generated). |
| `commit-list` | 2 | L | L | L | repository · commit messages and metadata, no diffs · metadata-only | Commit listing — metadata (generated). |
| `issue-catalog` | 2 | L | L | L | repository · issue listings and search results · metadata-only | Issue listing — metadata (generated). |
| `code-records` | 4 | M | **H** | M | repository · code search results — snippets across every repo in scope · population | Code entries across repos (generated). |
| `repository-records` | 3 | M | M | L | repository · what a repo-level write creates or merges · hub | Per-repo records (generated). |

**CIA in general.** **I > C > A.** A source-code MCP is an integrity asset first:
the damage path is *agent writes code → code merges → code runs*, which converts
a tool call into arbitrary production execution. Confidentiality is second and
concentrates in `ml-research` and `infra-config`. Availability only becomes the
lead axis for `infra-config`, where the repo is effectively a control plane.

### github_cbg

**Tier: S** · `github:cbg` · 11 tools · 6 assets · peak sensitivity **5**

CBG's trimmed demo GitHub catalog — same six repos, but the tool set adds
`delete_file` and keeps the merge path, so this variant carries a destructive
verb the real catalog does not. `payments-service` and `infra-config` are both
sensitivity 5 here: integrity-first (a merge reaches production money handling
and production infrastructure), with availability close behind on `infra-config`
and confidentiality leading only on `ml-research` (4). Expected use is
read-and-propose; `delete_file`, `push_files`, and `merge_pull_request` are the
three verbs that should never fire unsupervised. **I > C > A.**

### slack_real

**Tier: M** · `slack:real` · 16 tools · 10 assets · peak sensitivity **4**

**Company.** CBG's Slack workspace on the vendor's real 16-tool API surface —
notably including group-membership administration (`usergroups_users_update`,
`usergroups_create`, `usergroups_update`) and channel join/leave, which are
*access-control* operations rather than messaging ones.

**Expected organizational use.** Read channel history to summarize a thread,
search for a prior decision, post a status update to a team channel. The agent
is a participant, not an administrator.

**Asset severity and CIA.** `exec-private`, `hr-internal`, `incident-response`,
`on-call`, and `team-leads` all sit at **4** and are confidentiality-first:
compensation discussions, unreleased strategy, and live incident detail (which
frequently includes credentials pasted mid-incident). `engineering` and
`research-team` (3) are ordinary internal traffic. `general`, `announcements`,
and `random` (1) are broadcast-grade.

| Asset | Sens. | C | I | A | Contents | Why |
|---|---|---|---|---|---|---|
| `general` | 1 | L | L | L | channel · message = one post; whole-company channel | Broadcast-grade. |
| `announcements` | 1 | L | M | L | channel · message = one post; broadcast, already seen by everyone · public | Broadcast-grade; only spoofing matters. |
| `random` | 1 | L | L | L | channel · message = one post; social channel · public | Broadcast-grade. |
| `engineering` | 3 | M | M | L | channel · message = one post; ordinary engineering traffic | Ordinary internal traffic. |
| `incident-response` | 4 | **H** | H | M | channel · message = one post; live incident detail, credentials often pasted mid-incident · self-sufficient | Live incident detail; credentials pasted mid-incident. |
| `on-call` | 4 | **H** | H | M | channel · message = one post; live operational traffic | Live operational traffic. |
| `research-team` | 3 | M | M | L | channel · message = one post; pre-publication research discussion | Ordinary internal traffic. |
| `exec-private` | 4 | **H** | M | L | channel · message = one post; unreleased strategy and compensation | Unreleased strategy, compensation. |
| `hr-internal` | 4 | **H** | M | L | channel · message = one post; personnel matters and salary data | Personnel matters. |
| `team-leads` | 4 | **H** | M | L | channel · message = one post; management discussion | Management-only discussion. |
| `channel-messages` | 4 | **H** | M | L | channel · what a history read returns; inherits the most sensitive channel in scope · population | Cross-channel message store; characteristically includes the private channels. |
| `message-reactions` | 2 | L | L | L | channel · emoji reactions on a post · metadata-only | Emoji state — about-ness. |
| `read-markers` | 2 | L | L | L | channel · seen/unseen state; says nothing about content · metadata-only | Consumption state — metadata. |
| `usergroup-membership` | 4 | M | **H** | M | channel · who belongs to a user group — the access-control list · hub | Access control: who can read the sensitivity-4 channels. |
| `agent-channel-membership` | 4 | M | **H** | M | channel · which channels the agent itself has joined; joining grants read access to history · hub | The agent's own channel access — joining widens what it can read. |
| `user-directory` | 4 | **H** | L | L | channel · workspace member records, one per person · population | Workspace-wide people directory (emails, profiles). |
| `channel-directory` | 2 | L | L | L | channel · the list of channels, no messages · metadata-only | Channel names — metadata. |
| `usergroup-directory` | 2 | L | L | L | channel · the list of user groups · metadata-only | Group names — metadata. |
| `user-group-membership` | 4 | M | **H** | M | channel · who belongs to a user group — the access-control list · hub | Same access-control asset (generated naming variant — keep equal to the row above). |
| `usergroup-metadata` | 2 | L | L | L | channel · group names, handles and descriptions · metadata-only | Group attributes — metadata. |

**In general: C > I > A.** Disclosure dominates. But the real escalation on this
server is integrity-of-access: `usergroups_users_update` and `conversations_join`
change *who can read the sensitivity-4 channels*, converting a low-impact tool
call into a durable confidentiality breach.

### slack_cbg

**Tier: XS** · `slack:cbg` · 8 tools · 10 assets · peak sensitivity **4**

CBG's demo workspace, messaging-only (8 tools, no admin verbs). The five private
channels — `exec-private`, `hr-internal`, `incident-response`, `on-call`,
`team-leads` (4) — are confidentiality-first; `slack_post_message` is the one
integrity concern, since a posted message impersonates the workspace.
**C > I > A.**

---

## Database servers

### sqlite_devops_sqlite

**Tier: L** · `sqlite:devops_sqlite` · 5 tools · 5 assets · peak sensitivity **5**

**Company.** CBG's platform-engineering team. This SQLite database is the
control-plane record for deployments: who the platform users are, which API
tokens authenticate automation, what has been deployed and when, and the audit
trail over both. It is small — five tables, five tools — but it is the highest
*leverage* database in the corpus, because two of its tables are authentication
material and deployment control rather than business records.

**Expected organizational use.** The agent answers operational questions:
"what deployed last night", "which service owns this metric", "show the audit
entries for release 4.2". That workload is entirely `read_query`, `list_tables`,
`describe_table`. `write_query` and `insert_row` exist for maintenance and have
no place in the agent's routine path.

**Asset severity and CIA, per table.**

| Asset | Sens. | C | I | A | Contents | Why |
|---|---|---|---|---|---|---|
| `users` | 4 | **H** | H | M | table · columns: id, email, full_name, ssn, created_at · row = one platform user; carries `ssn`, and authorization reads this table · population | PII at identity-theft grade — the `ssn` column lifts this above an ordinary directory. Integrity second: authorization reads this table. |
| `api_tokens` | 5 | **H** | H | M | table · columns: id, service, token, scope, created_at · row = one live credential; `token` holds the secret in plaintext, usable alone · self-sufficient · hub | Live authentication material. Reading one row is credential theft; inserting is persistent unauthorized access that outlives the session. |
| `deployments` | 3 | M | **H** | M | table · columns: id, service, version, deployed_by, deployed_at · row = one release event; names internal services and versions | Deployment history; tampering hides what shipped. |
| `audit_log` | 4 | M | **H** | **H** | table · columns: id, actor, action, target, ts · row = one recorded action; append-only, the completeness is the asset · completeness-is-the-asset | The forensic record. A DELETE here is the standard anti-forensic move, and it is silent. |
| `public_metrics` | 1 | L | L | L | table · columns: id, metric, value, day · row = one published daily figure, already on the status page · public | Published figures — the floor case. Scoring it higher is the over-scoring failure mode. |
| `table-catalog` | 2 | L | L | L | surface · reach of the tool that homes here · the list of table names only, no values · metadata-only | Names reveal that `api_tokens` exists — reconnaissance, not exfiltration. |
| `table-metadata` | 2 | L | L | L | surface · reach of the tool that homes here · column names and types for one table; shows where `ssn` and `token` live · metadata-only | Tells an attacker where to aim without returning a value. |
| `database-records` | 5 | **H** | H | M | surface · reach of the tool that homes here · an arbitrary SELECT may join or UNION across every table, so one call can return the whole database · population | Free-form SELECT: reach is bounded by the query, not the table. |
| `table-records` | 5 | M | **H** | **H** | surface · reach of the tool that homes here · an arbitrary INSERT/UPDATE/DELETE may target any table, including `api_tokens` and `audit_log` · hub | One statement can mint a credential and then erase the evidence. |

**CIA in general.** **I ≈ C > A.** Unusually for a database, integrity ties
confidentiality: `write_query` is a free-form SQL verb, so a single call can
mint a token, elevate a user, or wipe the audit trail. `write_query` scores
impact 3 here versus 2 on the research database precisely because of what these
tables control. Availability is lowest — the database records the platform, it
does not run it — except on `audit_log`, where erasure *is* the attack.

### sqlite_cbg_sqlite

**Tier: S** · `sqlite:cbg_sqlite` · 5 tools · 7 assets · peak sensitivity **5**

CBG's research-arm database — employees, projects, datasets, experiments,
publications, grants, and an `api_keys` table. The agent's sanctioned job is
analytical: query experiment results, cross-reference datasets to grants,
summarize project status. `api_keys` (5) is confidentiality-first credential
material that has no business being in an analytics database at all. `employees`
(4, salary + email) and `grants` (4, funding terms) are disclosure-led;
`projects`, `datasets`, and `experiments` (3) are pre-publication IP where the
loss is scientific priority; `publications` (2) is near-public.
**C > I > A** — this is a read-heavy asset whose value is secrecy, not uptime.

**Content unit.** One table row. **Owner.** CBG research-arm data team;
contact `research-data@cbg.example`. **Provenance.** Authored 2026-07-28 against
the 5-tool sqlite catalog and the live `demo/cbg_sqlite/cbg.db` schema.

| Asset | Sens. | C | I | A | Contents | Why |
|---|---|---|---|---|---|---|
| `api_keys` | 5 | **H** | H | M | table · columns: id, service, key, owner_email · row = one live credential · self-sufficient · hub | One row is an independently usable credential for another service. |
| `employees` | 4 | **H** | M | L | table · columns: id, name, email, role, department, salary · 15 rows, one per person · population | Salary and contact PII for the whole staff. |
| `grants` | 4 | **H** | **H** | L | table · columns: id, sponsor, grant_no, pi_employee_id, amount_usd, dates, status · row = one award | Funding terms and amounts; a tampered row misstates a sponsor obligation. |
| `datasets` | 3 | M | M | L | table · columns: id, name, description, classification, size_gb, owner_email, created_at | Pre-publication research IP; loss is scientific priority. |
| `experiments` | 3 | M | **H** | L | table · columns: id, project_id, dataset_id, run_label, started_at, status, notes | Run records; a corrupted result silently invalidates conclusions. |
| `projects` | 3 | M | M | L | table · columns: id, code, title, status, pi_employee_id, start_date | Internal project register. |
| `publications` | 2 | L | M | L | table · columns: id, title, venue, year, doi, status, project_id | Near-public; only pre-print status is sensitive. |
| `table-catalog` | 2 | L | L | L | table · the list of table names, no rows · metadata-only | Names only — reconnaissance, not disclosure. |
| `table-metadata` | 2 | L | L | L | table · column names and types for one table · metadata-only | Schema only; no cell values. |
| `database-records` | 4 | **H** | **H** | M | surface · arbitrary SQL may join across every table, including `api_keys` · population | An unrestricted query reaches whatever the caller names. |
| `table-records` | 3 | M | **H** | L | table · rows written or inserted into whichever table is targeted | The write path; what it reaches depends on the target table. |

---

## Calendar servers

### calendar_real

**Tier: M** · `calendar:real` · 13 tools · 16 assets · peak sensitivity **5**

**Owner.** CBG workplace-services team (calendar administration); contact:
`workplace@cbg.example`.

**Company.** CBG on the real Google Calendar MCP surface — 13 tools including
bulk creation (`create-events`) and account administration (`manage-accounts`).

**Expected organizational use.** Scheduling assistance: find a free slot, read
the week, create or move a meeting, RSVP. Bounded, low-volume, and always tied
to a request a human made. An agent should never need `manage-accounts`, bulk
`create-events`, or anything on the `executive` calendar.

**Content unit.** One calendar event (an entry with title, time, attendees);
for `contacts`, one person's record. **The event is the central asset of this
server**: every calendar row below is a container of events, and almost every
tool creates, reads, moves, or deletes events — the per-calendar rows exist
because the same event operation carries different consequences depending on
whose calendar it touches.

**Irreversible actions.** Deleting an event silently removes a commitment (the
loss surfaces only when the meeting does not happen); sending an outbound
invite or update emails people outside the org and cannot be recalled; changes
to `connected-account-config` alter which accounts and scopes every other tool
can reach.

**Provenance.** Authored by the CBG security review, 2026-07-27, against the
13-tool `calendar_real.json` catalog capture.

**Asset severity and CIA.** `executive` and `recruiting` calendars (4) are
confidentiality-first for a non-obvious reason — the *metadata* is the leak. An
executive calendar showing a bank's counsel three times in a week discloses an
acquisition without exposing a single event body, and a recruiting calendar
discloses candidate identities and pending departures. `contacts` (4) is the
directory-scale PII asset. `personal` and `team` (3) are ordinary; `holidays`
(1) is public.

| Asset | Sens. | C | I | A | Contents | Why |
|---|---|---|---|---|---|---|
| `personal` | 3 | M | M | H | calendar · event = one entry; an individual's own schedule | Ordinary schedule; deletion is the sharp edge. |
| `team` | 3 | M | M | H | calendar · event = one entry; ordinary team scheduling | Ordinary team schedule. |
| `executive` | 4 | **H** | M | H | calendar · event = one entry; attendee lists and titles disclose deals and departures without opening a body | Metadata alone discloses deals and departures. |
| `recruiting` | 4 | **H** | M | M | calendar · event = one entry; candidate identities and pending moves | Candidate identities and pending moves. |
| `contacts` | 4 | **H** | L | L | calendar · one record per person; the whole directory in one call · population | Directory-scale PII. |
| `holidays` | 1 | L | M | L | calendar · event = one entry; the published holiday calendar · public | Public calendar. |
| `event-records` | 3 | M | M | H | calendar · what a create/update/delete targets; any event on any calendar in scope | Generic event bodies. |
| `event-attendee-lists` | 4 | **H** | L | L | calendar · who is invited to an event — the people behind the entry · population | Who meets whom — the metadata leak in list form. |
| `outbound-invite-email` | 4 | M | **H** | L | calendar · mail leaving the org under its identity; unrecallable once sent | Crosses the org boundary; unrecallable once sent. |
| `rsvp-state` | 2 | L | L | L | calendar · accept/decline state on one invitation · metadata-only | Attendance state — about-ness. |
| `connected-account-config` | 5 | **H** | **H** | M | calendar · which accounts are linked and with what scope; changing it reaches every calendar · self-sufficient · hub | Account/auth configuration — the access hub for every calendar. |
| `free-busy-availability` | 3 | **H** | L | L | calendar · busy blocks with no titles or attendees · metadata-only | Pattern-of-life metadata across calendars. |
| `calendar-directory` | 2 | L | L | L | calendar · the list of calendars, no events · metadata-only | Calendar names — metadata. |
| `color-catalog` | 1 | L | L | L | calendar · the static colour palette; no organizational state at all · public | Cosmetic color ids. |
| `calendar-records` | 3 | M | M | H | calendar · what a calendar-level write targets | Generic calendar records (generated homing asset). |
| `account-directory` | 4 | **H** | L | L | calendar · the linked-account list · metadata-only | Which accounts exist — organizational PII. |

**In general: C > A > I.** Confidentiality leads on metadata grounds.
Availability ranks second, ahead of integrity, because deletion is the sharp
edge on a calendar: `delete-event` silently removes a commitment, and the loss
only surfaces when the meeting does not happen.

### calendar_cbg

**Tier: XS** · `calendar:cbg` · 11 tools · 6 assets · peak sensitivity **5**

CBG's demo calendar, which adds two verbs the real surface lacks:
`delete_all_events` (bulk destruction) and `send_email_invite` (outbound
messaging from the org's identity). `contacts` (5) is the confidentiality peak;
`executive` and `recruiting` (4) leak by metadata. **C > I > A**, with
availability spiking on the bulk-delete path.

---

## Finance servers

Vendored under [`external/`](../../external/) and scanned live through the MITM
proxy from each server's own advertised `tools/list`. These are third-party
open-source servers an organization would adopt as-is, so the profile question
shifts: the asset is less "the company's data" and more "the company's decisions
and positions".

### maverick

**Tier: XL** · `maverick-mcp` · 119 tools · 10 Critical / 15 Medium / 94 Low

**Company.** A quantitative trading desk or a retail-advisory firm running
`maverick-mcp` as its research and portfolio backend. This is by a wide margin
the largest and most dangerous finance server in the corpus — 119 tools, and the
only finance server in the set that holds mutable organizational state rather
than just proxying public market data. It owns portfolios, watchlists, trading
signals, a trade journal, backtest infrastructure, and a data cache.

**Expected organizational use.** An analyst-facing agent: screen for candidates,
pull technical indicators, run a backtest against a strategy, record a trade in
the journal, adjust a watchlist. The overwhelming majority of that traffic is
read-shaped (94 of 119 tools are Low), and a normal session touches a handful of
symbols. The expected write set is narrow — add a position, add a journal
entry, create a signal — and always additive.

**Asset severity and CIA.** The scanner flags ten Critical tools, and they split
into two distinct threat shapes that deserve different treatment:

| Tool group | Op | Sev | Leading CIA axis | Why |
|---|---|---|---|---|
| `portfolio_remove_position`, `portfolio_clear_portfolio`, `remove_portfolio_position`, `watchlist_remove`, `delete_signal` | DELETE | 5 | **Integrity** | These destroy the firm's *record of its own positions*. `portfolio_clear_portfolio` takes a `confirm` flag — an escalating boolean that flips one call from scoped to total, which is exactly the input-risk pattern the dynamic layer exists to catch. A wiped portfolio is not just data loss; it makes the desk's exposure unknown, which is a trading risk, not an IT one. |
| `run_backtest`, `run_ml_strategy_backtest`, `run_health_diagnostics`, `data_clear_cache`, `performance_clear_system_caches` | EXECUTE | 5 | **Availability** | Unbounded compute. `run_ml_strategy_backtest` takes a `train_ratio` magnitude parameter and `run_backtest` takes 16 parameters — a single call with hostile magnitudes is a self-inflicted denial of service, and cache clears amplify it by forcing every subsequent query to refetch. |
| `agents_analyze_market_with_agent`, `agents_get_agent_streaming_analysis` | MODIFY | 3 | Integrity | Free-form `query` parameters (input-risk r5) — unbounded reach, and the natural injection surface on this server. |
| `journal_add_trade`, `portfolio_add_position`, `create_signal`, `create_strategy_ensemble` | CREATE/WRITE | 3 | Integrity | Additive state changes; individually mild, dangerous in volume because they poison the record the desk trades from. |

**CIA in general.** **I > A > C.** Integrity leads: every asset this server owns
is a decision input, and a corrupted portfolio, signal, or journal produces bad
trades that cost money without ever triggering a security alert. Availability is
a genuine second because of the EXECUTE cluster — this is the only server in the
whole corpus where availability is a first-class concern rather than an
afterthought. Confidentiality ranks last, and this is the important asymmetry
against the filesystem tenants: the market data is public, so the only
confidential thing here is *the firm's own positions and strategies* — which
leak through the read surface (`portfolio_*` getters, watchlists, journal) and
tell an observer exactly what the desk is doing. That makes maverick's read path
low-severity per call but high-severity in aggregate.

### finance_tools

**Tier: L** · `finance-tools-mcp` · 17 tools · 1 Medium / 16 Low

**Company.** A generalist investment-research or corporate-treasury function
using `finance-tools-mcp` for market and macro lookups — yfinance price and
fundamentals data, CNN Fear & Greed sentiment, FRED macroeconomic series, plus a
`calculate` tool.

**Expected organizational use.** Ad-hoc research: pull a price history, check
earnings, read insider trades and institutional holders, look up a macro series,
scan the news feed. It is a pure read-and-compute workload against public data,
run at analyst volumes — tens of calls per session, not thousands.

**Asset severity and CIA.** Sixteen of seventeen tools are Low because they
touch no organizational state at all. The single non-Low tool is the one worth
attention: `calculate` is an expression evaluator, which is an **execute**
primitive dressed as a utility. Its severity comes not from the data it reaches
but from what an evaluator does with a hostile expression — code execution or
resource exhaustion inside the server process. Everything else is a public-data
read whose severity is genuinely low, and over-scoring public-data reads was a
known failure mode in this repo's finance scans.

**In general: A > I > C.** Confidentiality is near-irrelevant — the data is
public by construction, and the only confidential signal is the *query pattern*
(which tickers the firm is researching, which leaks intent). Integrity matters
because a wrong number drives a wrong allocation, but the server does not hold
the number, it fetches it. Availability leads by default: the failure mode that
actually occurs is rate-limit exhaustion or an evaluator hang, which takes the
research workflow offline.

### openbb

**Tier: M** · `openbb-platform` · 30 tools · 1 High / 2 Medium / 27 Low

**Company.** An investment-research team on the OpenBB platform server —
equities, derivatives, crypto, ownership, fundamentals, and screening across 30
tools.

**Expected organizational use.** Broad multi-asset research: historical prices,
options surfaces, futures curves, ownership statistics, management data, and
`equity_screener` runs to build candidate lists.

**Asset severity and CIA.** The one High tool and two Mediums are the fan-out
and compute-heavy paths — `equity_screener` and the surface/curve builders,
where a single call with wide parameters expands into a large query. The other
27 are single-symbol public reads. There is no organizational state on this
server: it holds no portfolio, no positions, and no credentials beyond upstream
data-provider keys.

**In general: A > I > C.** Availability first (fan-out queries and provider rate
limits are the realistic failure), integrity second (bad data drives bad
decisions), confidentiality last — the only leak is which instruments the firm
is screening for, which is real but second-order.

### sec_edgar

**Tier: S** · `sec-edgar-mcp` · 21 tools · 21 Low

**Company.** A compliance, audit, or fundamental-research function pulling SEC
filings — recent filings, XBRL concepts, Form 4 insider transactions, period
comparisons, and company search.

**Asset severity and CIA.** Every one of the 21 tools scores Low, and correctly
so: EDGAR is a public regulatory archive, the server is read-only, and it holds
no organizational state whatsoever. **I > A > C** — integrity leads because
filings feed regulatory and valuation conclusions where a wrong figure has legal
weight; availability follows (SEC rate limits are strict); confidentiality is
effectively nil, since everything retrieved is already published.

### yahoo_finance

**Tier: XS** · `yfinance` · 9 tools · 9 Low

Thin `yfinance` wrapper for quick quote and fundamentals lookups; nine tools, all
public reads, no state, no credentials. **A > I > C** — the only real failure is
Yahoo rate-limiting or returning stale data. This is the corpus's floor case and
the correct answer for it is "low", which makes it the best control for
detecting over-scoring.

---

## Using these as scanner context

These profiles are **read by the scanner**, not just by people. The
`five_level_v2_desc` mode
(`sbatch scripts/scan_desc.sbatch`, driver `scripts/scan_desc_no_sens.py`) parses
this document via `mcp_security.static_scoring.server_profiles` and puts the
matching section in front of every scoring stage — domain inference, tool impact,
blast radius, baselines — while **removing the asset-sensitivity primitive**
entirely: the score becomes `blast × impact` and how much an asset is worth comes
from the text below instead of a derived 1–5 number. Results land in
`reports/experiments/five_level_v2_desc/`.

Consequences for editing this file: the `### <name>` heading and the
``**Tier: X** · `server-id` `` fact line are load-bearing — the parser keys on
both, and a scan whose server has no section here fails loudly rather than
scanning without its description.

The tiers are the experiment. Suggested comparisons, all within one server kind
so the tool surface is held constant:

- **Filesystem:** `fs_fintech_fs` (XL) vs `fs_media_studio_fs` (XS) — identical
  14 tools, opposite ends of the context budget.
- **GitHub:** `github_real` (L) vs `github_cbg` (S) — nearly the same six assets.
- **Calendar:** `calendar_real` (M) vs `calendar_cbg` (XS).
- **Database:** `sqlite_devops_sqlite` (L) vs `sqlite_cbg_sqlite` (S) — the same
  five tools over different table semantics.
- **Finance:** `maverick` (XL) vs `yahoo_finance` (XS) — the ceiling and floor.

The measurable question is whether the extra words change `asset_sensitivity`,
`blast_radius`, or the band distribution relative to the current
`inferred_profile` the scanner generates on its own, and if so, at which tier
the gain flattens.

## References

- Scan artifacts: [`reports/scan/`](../../reports/scan/),
  [`reports/scan_finance/`](../../reports/scan_finance/)
- Asset ranking rubric: [`reports/asset_ranking_rubric.md`](../../reports/asset_ranking_rubric.md)
- Server catalog: [`catalog.md`](catalog.md)
- Asset-ranking guidelines: [`../standards/asset-ranking-guidelines.md`](../standards/asset-ranking-guidelines.md)
