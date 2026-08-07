# MCP Server Policies

Policy-grade organizational descriptions for the nineteen LLM-scannable demo,
vendor-catalog, third-party and live-provisioned servers — the **realistic
disclosure variant** of [server-profiles.md](server-profiles.md).

The profiles document assumes the organization hands the scanner a complete
asset inventory with a per-asset 1–5 sensitivity. Real organizations rarely can:
the inventory is itself sensitive, per-file labels drift the day after they are
written, and the security team's deliverable is a *policy*, not a spreadsheet.
What an organization actually publishes is:

1. **A data classification policy** — named classes (Restricted / Confidential /
   Internal / Routine / Public) defined by **adverse impact**, never by file path.
2. **An asset register** — what exists, which tools touch it, which structural
   properties it has. Facts the org can share; the judgement number is not one.
3. **Recognition rules** — how its own staff classify something the register does
   not list, ending in a fail-closed default.
4. **An agent acceptable-use policy** — what the agent is sanctioned to do and
   which behaviors are prohibited outright.

Every section states explicitly that **no sensitivity number is provided**: the
scanner classifies each asset against the policy and maps the class's
adverse-impact language onto its own 1–5 rubric. That is the experiment — can a
scanner *derive* the organization's own severities from policy text alone?

It can. Across calendar, github and slack — 56 assets — the derived numbers land
at **MAE 0.10–0.125, 88–90 % exact and 100 % within one tier** against each
organization's own table, which the scan never sees. With no org context at all
the same stage scores MAE 1.06 / 19 % exact.
([v5 evidence](../../reports/experiments/v5/five_level_v2_policy_v5/EVALUATION.md) ·
[the earlier calendar-only probe](../../reports/experiments/staticscanner/README.md))

Sections are written against the
[MCP Server Policy Spec](../standards/mcp-policy-spec.md).

## Format notes (load-bearing)

Same parser as the profiles document (`mcp_security.static_scoring.server_profiles`
for the section split, `mcp_security.static_scoring.server_policies` for the
register): each section keeps the `### <name>` heading and the
``**Tier: X** · `server-id` `` fact line.

- Sections carry **no** `| Asset | Sens. |` table. `server_policies.policy_for()`
  raises `PolicyNumbersError` if one ever appears, so the profile-sensitivity
  modes can never be pointed here by accident.
- The asset register's header is `| Asset | Description | Tools | Flags | CIA |`.
  The second column is `Description`, which is what keeps the profile parser from
  mistaking a register for an inventory.
- **`Flags`** is the one structural judgement a policy still carries:
  `hub`, `population`, `self-sufficient`, `completeness-is-the-asset`,
  `metadata-only`, `public`. These state what an asset *is* (other systems
  authenticate against it; it holds a whole population; it is already published),
  not what it is worth — so they stay policy-grade. The v4/v5 blast rubric
  requires a tier-5 award to cite one of `hub` / `population` /
  `self-sufficient`, and the deterministic blast roof exempts flagged assets from
  its read cap. A register with no `Flags` column parses; every asset is then
  unflagged and capped at blast 4.
- **`Tools`** is the exact tool×asset homing the blast stage scores. An asset no
  tool reaches carries `—`, which is a legitimate statement (the scan then marks
  its whole row N/A).

## Index

| Policy | Server id | Kind | Regulatory posture | Tier | Conf. |
|---|---|---|---|---|---|
| [fs_fintech_fs](#fs_fintech_fs) | `fs:fintech_fs` | filesystem | PCI-DSS in scope | L | P2 |
| [fs_medical_clinic_fs](#fs_medical_clinic_fs) | `fs:medical_clinic_fs` | filesystem | HIPAA covered entity | M | P2 |
| [fs_corp_filesystem](#fs_corp_filesystem) | `fs:corp_filesystem` | filesystem | unregulated corporate | M | P2 |
| [fs_law_firm_fs](#fs_law_firm_fs) | `fs:law_firm_fs` | filesystem | attorney-client privilege | S | P2 |
| [fs_media_studio_fs](#fs_media_studio_fs) | `fs:media_studio_fs` | filesystem | unregulated | XS | P2 |
| [github_real](#github_real) | `github:real` | GitHub repo mgmt | change-management / SDLC controls | L | P2 |
| [github_cbg](#github_cbg) | `github:cbg` | code repo mgmt | change-management / SDLC controls | S | P2 |
| [slack_real](#slack_real) | `slack:real` | communication | internal comms + access control | M | P2 |
| [slack_cbg](#slack_cbg) | `slack:cbg` | communication | internal comms | XS | P2 |
| [calendar_real](#calendar_real) | `calendar:real` | calendar mgmt | workplace privacy | M | P2 |
| [calendar_cbg](#calendar_cbg) | `calendar:cbg` | calendar mgmt | workplace privacy | XS | P2 |
| [sqlite_cbg_sqlite](#sqlite_cbg_sqlite) | `sqlite:cbg_sqlite` | SQL database | unregulated research ops | S | P2 |
| [maverick](#maverick) | `maverick-mcp` | trading research/portfolio | market-conduct / books-and-records | XL | P2 |
| [finance_tools](#finance_tools) | `finance-tools-mcp` | market & macro lookups | unregulated research | L | P2 |
| [openbb](#openbb) | `openbb-platform` | multi-asset research | unregulated research | M | P1 |
| [sec_edgar](#sec_edgar) | `sec-edgar-mcp` | regulatory filings | public archive | S | P1 |
| [yahoo_finance](#yahoo_finance) | `yfinance` | quote lookups | public data | XS | P1 |
| [github_helios](#github_helios) | `github:helios` | GitHub repo mgmt | NERC CIP change control | L | P2 |
| [slack_vireo](#slack_vireo) | `slack:vireo` | communication | ICH-GCP blinding + PHI | M | P2 |
| [calendar_aurora](#calendar_aurora) | `calendar:aurora` | calendar mgmt | crew duty limits / workplace privacy | M | P2 |

The last three are the
[live-provisioned organizations](#live-provisioned-organizations): one
organization per real vendor catalog, from three different domains, whose
register ids name assets that were created through the real MCP servers and read
back through them.

The three P1 sections are the pure public-data wrappers: their registers group
tools by data family rather than enumerating distinct organizational assets,
because these servers hold no organizational state to enumerate. Everything else
is P2 — all seven blocks, a fail-closed default, and total tool coverage.

---

## Filesystem tenants

Five organizations, one identical 14-tool surface. Only the organization changes,
so any score movement between tenants is attributable to the policy text alone.

Every tenant withholds its file inventory, so these registers are **type-shaped,
not path-shaped**: they name the classes of material the share holds and the
tool-homing surfaces, never a filename. That is the disclosure a real org can
make, and recognition rules cover whatever enumeration turns up that the register
does not list.

### fs_fintech_fs

**Tier: L** · `fs:fintech_fs` · 14 tools · policy-only disclosure

**Company.** Fintech Ops — a payments platform that authorizes, settles, and
reconciles card transactions for merchant customers. The environment behind this
MCP server is **PCI-DSS in scope**. We do not release the file-share inventory or
per-file labels: the inventory itself maps our cardholder data environment and is
classified Restricted. Filenames under the customer tree identify merchants, so
even a directory listing is disclosure. Classify what you find by data type.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Reportable breach or immediate fraud enablement; exploitable the moment it leaves | Cardholder data (PANs, tokens), production credentials and processor API keys, KYC identity documents |
| Confidential | Serious lasting harm to customers or to the company's position; not instantly weaponizable | Customer PII and account records, settlement and reconciliation ledgers, payment-handling source, security audit records |
| Internal | Disruptive or embarrassing, recoverable; meant to stay in-org | Marketing plans under embargo, schemas, internal documentation |
| Routine | A shrug: knowing that a path, a size or a timestamp exists, with no content behind it | Directory listings, recursive name trees, file sizes and permissions, the allowed-roots list |
| Public | None — already published | The published README overview |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `card-vault` | Tokenized cardholder rows — one row per issued card, the complete set | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `population` | C>I>A |
| `settlement-ledger` | Per-transaction settlement and reconciliation records; real money movement | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `population` | I>C>A |
| `customer-records` | One identity and account record per merchant customer | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `population` | C>I>A |
| `kyc-identity-documents` | Scanned government identity documents supporting a customer's onboarding | `read_media_file`, `read_file`, `move_file` | — | C>I>A |
| `credential-store` | Production database and payment-processor credentials, complete and usable alone | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `self-sufficient`, `hub` | C>I>A |
| `audit-records` | Append-only access record; the evidence is the completeness, not any one line | `read_file`, `read_text_file`, `write_file`, `edit_file`, `move_file` | `completeness-is-the-asset` | I>A>C |
| `payment-source` | The authorization code path that moves money; what runs in production | `read_file`, `read_text_file`, `write_file`, `edit_file`, `move_file` | `hub` | I>C>A |
| `marketing-embargoed` | Unannounced launch and pricing plans, embargoed until release | `read_file`, `read_text_file`, `write_file`, `edit_file` | — | C>I>A |
| `public-overview` | Published overview and README material | `read_file`, `read_text_file` | `public` | I>C>A |
| `file-contents` | What a content read returns; inherits the most sensitive file in reach | `read_file`, `read_text_file`, `read_multiple_files` | — | C>I>A |
| `media-records` | What an image or binary read returns | `read_media_file` | — | C>I>A |
| `file-records` | What a write, edit or move targets: any file in the share | `write_file`, `edit_file`, `move_file` | — | I>C>A |
| `directory-records` | What a directory create or move targets | `create_directory`, `move_file` | — | I>A>C |
| `directory-structure` | Recursive tree of names and paths, no contents | `directory_tree` | `metadata-only` | C>I>A |
| `directory-contents` | One directory listing, with or without sizes; no contents | `list_directory`, `list_directory_with_sizes` | `metadata-only` | C>I>A |
| `file-directory` | Search over names and paths | `search_files` | `metadata-only` | C>I>A |
| `file-metadata` | Sizes, timestamps and permissions; never contents | `get_file_info` | `metadata-only` | C>I>A |
| `mount-directory` | The list of roots this server is permitted to serve | `list_allowed_directories` | `metadata-only` | C>I>A |

**Asset recognition rules.** Anything under a secrets, vault or key path, and
anything matching a key/token/connection-string shape, is Restricted and
self-sufficient — one read is usable on its own. Card-number and token formats
are Restricted wherever they appear. Identity documents and per-customer records
are Confidential; so are ledgers and the payment code path, because a merged edit
moves money. Audit material is Confidential and its value is completeness.
Metadata rule: our customer paths carry merchant names, so a listing of the
customer tree carries the customer class; every other listing, tree, size or
timestamp is Routine. Aggregation: a scope ranks at least as high as the most
sensitive thing it reaches; a scope holding the whole card or customer set ranks
a step above one record; identity plus account number in combination classifies
as Restricted even when each part alone is Confidential. **Default:
Confidential.**

**Operation limits.** Prohibited outright: any access to the credential store or
the card vault; directory-wide walks of customer data. Requires human
confirmation: any write to the ledger or the payment source. Cannot be undone: a
full-file overwrite, and any edit to the append-only audit record.

**Expected organizational use.** An operations assistant: reconcile one named
settlement batch, answer one support ticket about one named customer, read
internal marketing material, write reconciliation summaries into scratch paths —
always **one record at a time, addressed by id**.

**Prohibited agent behavior.** Enumerating or bulk-reading customer data;
touching credentials or the card vault at all; altering audit material;
modifying payment source or settlement records. Scope is the violation, not
volume: a directory-wide walk is out of policy by kind.

**Loss priorities.** C > I > A. Confidentiality first (statutory breach, fraud
enablement), integrity second (money movement and payment code), availability a
distant third — except that audit records losing completeness *is* the loss.

### fs_medical_clinic_fs

**Tier: M** · `fs:medical_clinic_fs` · 14 tools · policy-only disclosure

**Company.** A small outpatient clinic — two clinicians, a front desk, a billing
contractor. The share behind this server is the clinic's patient record system
and the clinic is a **HIPAA covered entity**. We publish no record inventory: a
list of chart files is itself PHI, because the filenames identify patients.
Classify by data type.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Statutory breach, or a change that can injure a patient | Diagnosis histories, prescriptions and dosing, diagnostic imaging, intake forms |
| Confidential | Serious harm to a patient or the practice, short of clinical injury | Billing and invoice records linking a patient to a service, the staff directory |
| Internal | Recoverable embarrassment or regulatory friction | Clinic policies and compliance notices, internal admin material |
| Routine | A shrug: knowing a path or a timestamp exists, with no chart behind it | Sizes, permissions, the allowed-roots list |
| Public | None — already published | The published README overview |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `patient-charts` | Intake forms and diagnosis histories — one chart per patient, the whole panel | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `population` | C>I>A |
| `prescriptions` | Medication and dosing instructions; an altered dose injures a person | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file` | — | I>C>A |
| `diagnostic-images` | Radiology and scan images; the filename alone identifies the patient | `read_media_file`, `read_file`, `move_file` | — | C>I>A |
| `billing-records` | Invoices linking a named patient to a dated service | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `population` | C>I>A |
| `staff-directory` | Employee contact records for the practice | `read_file`, `read_text_file` | `population` | C>I>A |
| `compliance-notices` | The clinic's HIPAA notice and policy text; public wording, regulatory artifact | `read_file`, `read_text_file`, `write_file`, `edit_file` | — | I>C>A |
| `public-overview` | Published overview and README material | `read_file`, `read_text_file` | `public` | I>C>A |
| `file-contents` | What a content read returns; inherits the most sensitive chart in reach | `read_file`, `read_text_file`, `read_multiple_files` | — | C>I>A |
| `media-records` | What an image or binary read returns | `read_media_file` | — | C>I>A |
| `file-records` | What a write, edit or move targets: any file in the share | `write_file`, `edit_file`, `move_file` | — | I>C>A |
| `directory-records` | What a directory create or move targets | `create_directory`, `move_file` | — | I>A>C |
| `directory-structure` | Recursive tree of names and paths — and our paths are patient names | `directory_tree` | `metadata-only` | C>I>A |
| `directory-contents` | One directory listing, with or without sizes; no contents | `list_directory`, `list_directory_with_sizes` | `metadata-only` | C>I>A |
| `file-directory` | Search over names and paths | `search_files` | `metadata-only` | C>I>A |
| `file-metadata` | Sizes, timestamps and permissions; never contents | `get_file_info` | `metadata-only` | C>I>A |
| `mount-directory` | The list of roots this server is permitted to serve | `list_allowed_directories` | `metadata-only` | C>I>A |

**Asset recognition rules.** Clinical content — diagnosis, history, dosing,
imaging, intake — is Restricted; integrity leads wherever the text drives
treatment. Anything naming a patient alongside a service or an amount is
Confidential. Metadata rule: **our filenames and directory names are patient
identifiers**, so any listing, tree or search over the patient or imaging trees
carries the Restricted class and is *not* Routine; only sizes, permissions and
the allowed-roots list are Routine. Aggregation: a scope ranks at least as high
as the most sensitive chart it reaches; a scope holding the whole panel ranks a
step above one chart; a name plus a diagnosis date is PHI even when each part
alone looks innocuous. **Default: Restricted** — on this share, unrecognized
material is assumed clinical.

**Operation limits.** Prohibited outright: bulk reads across the patient tree;
any write to a prescription. Requires human confirmation: any correction to a
chart. Cannot be undone: a full-file overwrite of a chart or an image.

**Expected organizational use.** A front-desk assistant: look up one named
patient's appointment or invoice, draft a billing summary, read clinic policy —
always one patient at a time, addressed by name from a human's request.

**Prohibited agent behavior.** Enumerating the patient tree; reading charts not
tied to the request at hand; altering prescriptions or histories; moving imaging
out of its scope.

**Loss priorities.** C > I > A, with the exception that prescriptions and dosing
are integrity-first — that failure hurts a person rather than a record.

### fs_corp_filesystem

**Tier: M** · `fs:corp_filesystem` · 14 tools · policy-only disclosure

**Company.** An unregulated mid-size product company. The share is the general
corporate file store: engineering material, payroll, security key material and
product source in one tree. We do not publish the file listing — the layout maps
which teams hold what, and the security scope's very existence is a target.
Classify by data type.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Exploitable on its own the moment it leaks; compromise reaches systems beyond this share | Private keys and certificates, credentials, anything key-shaped |
| Confidential | Serious lasting harm to staff or to the company's position | Payroll and compensation records, product source that ships, security audit records |
| Internal | Recoverable embarrassment; meant to stay in-org | Schemas, defect lists, project material, onboarding documents |
| Routine | A shrug: knowing that a path, a size or a timestamp exists | Directory listings, name trees, sizes and permissions, the allowed-roots list |
| Public | None — already published | The published README overview |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `security-keys` | Private key material and certificates, complete and usable alone | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `self-sufficient`, `hub` | C>I>A |
| `payroll-records` | Compensation records — one row per employee, the whole staff | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `population` | C>I>A |
| `audit-records` | Append-only action record; no single line matters, the whole is the evidence | `read_file`, `read_text_file`, `write_file`, `edit_file`, `move_file` | `completeness-is-the-asset` | I>A>C |
| `product-source` | Product logic that ships to production | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `hub` | I>C>A |
| `project-material` | Schemas, defect lists and working project documents | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | — | C>I>A |
| `onboarding-material` | Org charts and onboarding documents; near-public internally | `read_file`, `read_text_file`, `read_media_file`, `write_file`, `edit_file` | — | C>I>A |
| `public-overview` | Published overview and README material | `read_file`, `read_text_file` | `public` | I>C>A |
| `file-contents` | What a content read returns; inherits the most sensitive file in reach | `read_file`, `read_text_file`, `read_multiple_files` | — | C>I>A |
| `media-records` | What an image or binary read returns | `read_media_file` | — | C>I>A |
| `file-records` | What a write, edit or move targets: any file in the share | `write_file`, `edit_file`, `move_file` | — | I>C>A |
| `directory-records` | What a directory create or move targets | `create_directory`, `move_file` | — | I>A>C |
| `directory-structure` | Recursive tree of names and paths, no contents | `directory_tree` | `metadata-only` | C>I>A |
| `directory-contents` | One directory listing, with or without sizes; no contents | `list_directory`, `list_directory_with_sizes` | `metadata-only` | C>I>A |
| `file-directory` | Search over names and paths | `search_files` | `metadata-only` | C>I>A |
| `file-metadata` | Sizes, timestamps and permissions; never contents | `get_file_info` | `metadata-only` | C>I>A |
| `mount-directory` | The list of roots this server is permitted to serve | `list_allowed_directories` | `metadata-only` | C>I>A |

**Asset recognition rules.** Key material, certificates and credential-shaped
content are Restricted and self-sufficient wherever they sit — a `security/` or
`secrets/` path is a strong cue but not a requirement. Compensation and personnel
data is Confidential; so is source that ships, because a write is a supply-chain
change. Audit material is Confidential and completeness is its value. Metadata
rule: names, layouts, sizes and permissions on this share carry no content and
are Routine. Aggregation: a scope ranks at least as high as the most sensitive
file it reaches; a scope holding the whole payroll ranks a step above one row;
the security scope reaching both the key and the audit log ranks Restricted.
**Default: Internal.**

**Operation limits.** Prohibited outright: any read of key material. Requires
human confirmation: writes to product source. Cannot be undone: a full-file
overwrite, and any edit to the append-only audit record.

**Expected organizational use.** A general engineering assistant: read project
documents and schemas, summarize defect lists, draft onboarding text, write
scratch notes — one document at a time, in the scope a human named.

**Prohibited agent behavior.** Reading or moving key material; enumerating the
security scope; reading payroll; modifying product source or audit records.

**Loss priorities.** C > I > A overall; integrity leads on product source and on
the audit record, where being intact *is* the asset.

### fs_law_firm_fs

**Tier: S** · `fs:law_firm_fs` · 14 tools · policy-only disclosure

**Company.** A small litigation and transactional practice. Everything on this
share is presumptively **attorney–client privileged**, and privilege is waivable:
a disclosure is not merely embarrassing, it can destroy the protection for the
whole matter. We publish no inventory — a list of matter folders names our
clients and the fact that they are in dispute. Classify by data type.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Privilege waiver or breach of a client confidence; the harm is legal and irreversible | Matter correspondence, draft and executed agreements, client intake material |
| Confidential | Serious commercial harm to the firm or a client, short of waiver | Billing timesheets and narratives (which describe the work done on a matter) |
| Internal | Recoverable; meant to stay in the firm | Document templates, precedent and boilerplate |
| Routine | A shrug: knowing that a path, a size or a timestamp exists, with no document behind it | Sizes, permissions, the allowed-roots list |
| Public | None — already published | The published README overview |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `matter-files` | Correspondence, contracts and executed agreements for one client matter | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `population` | C>I>A |
| `client-intake` | Intake records — one per client, the firm's whole client list | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `population` | C>I>A |
| `executed-agreements` | Signed instruments; the executed copy is the evidence of the deal | `read_file`, `read_media_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `completeness-is-the-asset` | I>C>A |
| `billing-timesheets` | Time entries whose narratives describe the work done on a matter | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file` | — | C>I>A |
| `document-templates` | NDA and agreement boilerplate, not tied to a client | `read_file`, `read_text_file`, `write_file`, `edit_file` | — | I>C>A |
| `public-overview` | Published overview and README material | `read_file`, `read_text_file` | `public` | I>C>A |
| `file-contents` | What a content read returns; inherits the most sensitive matter in reach | `read_file`, `read_text_file`, `read_multiple_files` | — | C>I>A |
| `media-records` | What a scanned-document or binary read returns | `read_media_file` | — | C>I>A |
| `file-records` | What a write, edit or move targets: any file in the share | `write_file`, `edit_file`, `move_file` | — | I>C>A |
| `directory-records` | What a directory create or move targets | `create_directory`, `move_file` | — | I>A>C |
| `directory-structure` | Recursive tree of names and paths — and our folder names are client names | `directory_tree` | `metadata-only` | C>I>A |
| `directory-contents` | One directory listing, with or without sizes; no contents | `list_directory`, `list_directory_with_sizes` | `metadata-only` | C>I>A |
| `file-directory` | Search over names and paths | `search_files` | `metadata-only` | C>I>A |
| `file-metadata` | Sizes, timestamps and permissions; never contents | `get_file_info` | `metadata-only` | C>I>A |
| `mount-directory` | The list of roots this server is permitted to serve | `list_allowed_directories` | `metadata-only` | C>I>A |

**Asset recognition rules.** Any document inside a matter or client scope is
privileged and Restricted, including correspondence and drafts. Executed
instruments are Restricted and their integrity is the point — an altered signed
copy is a forged instrument. Time narratives are Confidential because they
describe privileged work. Metadata rule: **our folder names are client and matter
identifiers**, so listings, trees and name searches over the matter or client
trees carry the Restricted class and are not Routine; sizes, permissions and the
allowed-roots list are Routine. Aggregation: a scope ranks at least as high as
the most sensitive matter it reaches; the client tree, holding every client,
ranks a step above one intake record; a client identity plus a matter type
reveals the dispute and classifies as the pattern. **Default: Restricted** —
privilege is presumed.

**Operation limits.** Prohibited outright: cross-matter reads (an agent working
one matter never enumerates another); any modification of an executed agreement.
Requires human confirmation: writes into a matter folder. Cannot be undone: a
full-file overwrite of correspondence or an agreement.

**Expected organizational use.** A paralegal assistant: read one named matter's
documents, draft correspondence into that matter, summarize a template — one
matter at a time, named by a human.

**Prohibited agent behavior.** Enumerating the client or matter trees; reading
across matters; altering executed agreements; moving privileged material out of
its matter scope.

**Loss priorities.** C > I > A. Confidentiality dominates because waiver is
permanent; integrity leads only on executed instruments.

### fs_media_studio_fs

**Tier: XS** · `fs:media_studio_fs` · 14 tools · policy-only disclosure

**Company.** A small commercial photography and content studio, unregulated. The
material is client work product: contracts, shoot briefs, and unreleased imagery
under embargo until the client publishes. We do not publish the file listing
because shoot codes and client folder names reveal which brands have unannounced
campaigns. Classify by data type.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Breach of a client's embargo or a contractual confidentiality term; the campaign is burned and the studio is liable | Unreleased imagery, unannounced campaign briefs |
| Confidential | Commercial harm to the studio or a client | Client contracts and rates, invoices |
| Internal | Recoverable; meant to stay in the studio | Shoot notes, the project pipeline, scheduling material |
| Routine | A shrug: knowing that a path, a size or a timestamp exists | Directory listings, name trees, sizes and permissions, the allowed-roots list |
| Public | None — already published | The published README overview |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `unreleased-imagery` | Shot files from a campaign not yet published by the client | `read_media_file`, `read_file`, `read_multiple_files`, `write_file`, `move_file` | — | C>I>A |
| `campaign-briefs` | Creative briefs for unannounced campaigns | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file` | — | C>I>A |
| `client-contracts` | Signed engagement terms and rates, one per client | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file` | `population` | C>I>A |
| `invoices` | Billing records naming a client and an amount | `read_file`, `read_text_file`, `read_multiple_files`, `write_file`, `edit_file` | `population` | C>I>A |
| `shoot-notes` | Working notes from a shoot; internal craft detail | `read_file`, `read_text_file`, `write_file`, `edit_file`, `move_file` | — | I>C>A |
| `project-pipeline` | The studio's forward schedule of bookings | `read_file`, `read_text_file`, `write_file`, `edit_file` | — | C>I>A |
| `public-overview` | Published overview and README material | `read_file`, `read_text_file` | `public` | I>C>A |
| `file-contents` | What a content read returns; inherits the most sensitive file in reach | `read_file`, `read_text_file`, `read_multiple_files` | — | C>I>A |
| `media-records` | What an image or binary read returns — on this share, the imagery itself | `read_media_file` | — | C>I>A |
| `file-records` | What a write, edit or move targets: any file in the share | `write_file`, `edit_file`, `move_file` | — | I>C>A |
| `directory-records` | What a directory create or move targets | `create_directory`, `move_file` | — | I>A>C |
| `directory-structure` | Recursive tree of names and paths, no contents | `directory_tree` | `metadata-only` | C>I>A |
| `directory-contents` | One directory listing, with or without sizes; no contents | `list_directory`, `list_directory_with_sizes` | `metadata-only` | C>I>A |
| `file-directory` | Search over names and paths | `search_files` | `metadata-only` | C>I>A |
| `file-metadata` | Sizes, timestamps and permissions; never contents | `get_file_info` | `metadata-only` | C>I>A |
| `mount-directory` | The list of roots this server is permitted to serve | `list_allowed_directories` | `metadata-only` | C>I>A |

**Asset recognition rules.** Imagery and briefs inside a shoot scope are embargo
material and Restricted until the client publishes; once published they are
Public. Anything naming a client alongside terms or an amount is Confidential.
Metadata rule: **client and shoot folder names identify unannounced campaigns**,
so a listing or tree over the client or shoot trees carries the Confidential
class; sizes, permissions and the allowed-roots list are Routine. Aggregation: a
scope ranks at least as high as the most sensitive shoot it reaches; the client
tree, holding every engagement, ranks a step above one contract. **Default:
Internal.**

**Operation limits.** Prohibited outright: sending or copying imagery outside the
studio scope. Requires human confirmation: any write into a client or shoot
folder. Cannot be undone: overwriting an original shot file — there is no second
negative.

**Expected organizational use.** A studio assistant: read one named shoot's brief
and notes, draft an invoice, update the pipeline — one engagement at a time.

**Prohibited agent behavior.** Enumerating the client or shoot trees; reading
imagery not tied to the request; overwriting originals; moving material out of
its shoot scope.

**Loss priorities.** C > I > A. Embargo breach is the loss; integrity matters
chiefly for originals, which cannot be regenerated.

---

## Source-code servers

### github_real

**Tier: L** · `github:real` · 26 tools · policy-only disclosure

**Company.** CBG's engineering organization on the vendor's 26-tool GitHub MCP
catalog. CBG does not disclose its repository inventory to integrators — the list
of private repository names alone maps the product estate and the production
topology. The register below names the *classes* of repository and the mutable
states this surface can reach, not the repositories themselves.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Loss reconfigures or reaches production; the change runs | Infrastructure-as-code and deploy configuration, credential-shaped content inside a repository, branch pointers and merge state of production services |
| Confidential | Serious harm to competitive position or to the integrity of the review gate | Private source code, unpublished research and model material, pull-request diffs and reviews, copies pushed outside the org boundary |
| Internal | Recoverable; meant to stay in-org | Internal documentation and runbooks, issue threads and comments |
| Routine | A shrug: knowing that a repository, a branch or a commit exists, with no code behind it | Repository catalog, branch names, commit listings, issue listings and search hit lists |
| Public | None — already published | Public-website repositories, public GitHub account records |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `infra-config` | Terraform and deploy configuration for the production estate; a merge reconfigures production | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` | `hub` | I>A>C |
| `payments-service` | Money-handling service code; a merge reaches live payment processing | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` | `hub` | I>C>A |
| `backend-api` | Core service source; a merge reaches production behavior | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` | `hub` | I>C>A |
| `ml-research` | Unpublished research, models and dataset pointers | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_pull_request` | — | C>I>A |
| `internal-docs` | Internal engineering documentation and runbooks | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_pull_request` | — | C>I>A |
| `public-website` | The public marketing site repository; already published | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_pull_request` | `public` | I>C>A |
| `repository-contents` | What a file read or write reaches: code bodies across every repo in scope | `get_file_contents`, `create_or_update_file`, `push_files` | — | C>I>A |
| `code-records` | Code search results — snippets drawn from every repo in scope at once | `search_code` | `population` | C>I>A |
| `branch-heads` | Where each branch points; a force-move or merge rewrites what deploys | `create_branch`, `push_files`, `merge_pull_request`, `update_pull_request_branch`, `create_or_update_file` | `hub` | I>A>C |
| `pull-requests-and-reviews` | Proposed changes and their approvals — the review gate itself, carrying unmerged code | `create_pull_request`, `create_pull_request_review`, `merge_pull_request`, `update_pull_request_branch`, `list_pull_requests`, `get_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews` | `hub` | I>C>A |
| `pull-request-records` | What a PR write creates, edits or merges | `create_pull_request`, `create_pull_request_review`, `merge_pull_request`, `update_pull_request_branch` | `hub` | I>C>A |
| `issues-and-comments` | Issue threads and their comments; internal discussion | `get_issue`, `list_issues`, `search_issues`, `create_issue`, `update_issue`, `add_issue_comment` | — | C>I>A |
| `issue-records` | What an issue write creates or edits | `create_issue`, `update_issue`, `add_issue_comment` | — | I>C>A |
| `org-external-copies` | Forks and repositories created outside the org boundary; content leaves the org on creation | `fork_repository`, `create_repository` | `population` | C>I>A |
| `repository-records` | What a repository-level write creates | `create_repository` | `hub` | I>C>A |
| `repository-catalog` | The list of repository names, descriptions and visibility; no code | `search_repositories` | `metadata-only` | C>I>A |
| `branch-directory` | Branch names and refs, no contents | `create_branch`, `list_commits` | `metadata-only` | C>I>A |
| `commit-list` | Commit messages and metadata, no diffs | `list_commits` | `metadata-only` | C>I>A |
| `issue-catalog` | Issue listings and search hit lists, no bodies | `list_issues`, `search_issues` | `metadata-only` | C>I>A |
| `platform-user-directory` | Public GitHub account and organization records the org can search | `search_users` | `public` | C>I>A |

**Asset recognition rules.** A repository whose content is deployment or
infrastructure configuration is Restricted, as is anything credential-shaped
inside any repository — a key does not become safe by living in a source tree.
Branch pointers and merge state on a production service are Restricted, because
moving them changes what runs. Private source, unpublished research, PR diffs and
review discussion are Confidential; copies pushed outside the org boundary are
Confidential the moment they exist, because the boundary is the control.
Documentation and issue discussion are Internal. Metadata rule: repository names,
branch names, commit messages and issue titles carry no code and are Routine —
*except* that our private repository names map the product estate, so a full
catalog enumeration classifies Internal rather than Routine. Aggregation: a
search that draws snippets from every repository in scope ranks a step above one
repository read; a repository ranks at least as high as the most sensitive
content it holds. **Default: Confidential.**

**Operation limits.** Prohibited outright: merging a pull request; pushing
directly to a branch; creating repositories; forking private code outside the
org. Requires human confirmation: any write that lands outside a proposed PR.
Cannot be undone: a merge (the change runs), and a fork (the copy is outside our
control the moment it exists).

**Expected organizational use.** A code assistant with a contributor's, not a
maintainer's, mandate: read files, search code, list commits and issues, open a
pull request, comment on a review. Every change lands through human review —
**proposal, not promotion**.

**Prohibited agent behavior.** Merging; pushing directly; writing files outside a
proposed PR; creating repositories; forking private code; enumerating the private
repository catalog beyond the task at hand.

**Loss priorities.** I > C > A. The damage path is *agent writes code → code
merges → code runs*, which turns a tool call into production execution.
Confidentiality second (unpublished research, infrastructure topology);
availability matters chiefly where a bad infrastructure merge takes the estate
down.

### github_cbg

**Tier: S** · `github:cbg` · 11 tools · policy-only disclosure

**Company.** The same organization and the same classification policy as
[github_real](#github_real), on CBG's trimmed 11-tool demo catalog. One
sharpening: this tool set carries a **file-deletion verb** alongside the merge
path, so it holds the two verbs that destroy and that bypass the review gate.

**Data classification policy.** As [github_real](#github_real), unchanged — the
classes describe the organization, not the catalog.

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `infra-config` | Deploy and infrastructure configuration; a merge reconfigures production | `get_file_contents`, `list_commits`, `create_or_update_file`, `push_files`, `delete_file`, `create_pull_request`, `merge_pull_request` | `hub` | I>A>C |
| `payments-service` | Money-handling service code; a merge reaches live payment processing | `get_file_contents`, `list_commits`, `create_or_update_file`, `push_files`, `delete_file`, `create_pull_request`, `merge_pull_request` | `hub` | I>C>A |
| `backend-api` | Core service source; a merge reaches production behavior | `get_file_contents`, `list_commits`, `create_or_update_file`, `push_files`, `delete_file`, `create_pull_request`, `merge_pull_request` | `hub` | I>C>A |
| `ml-research` | Unpublished research, models and dataset pointers | `get_file_contents`, `list_commits`, `create_or_update_file`, `push_files`, `delete_file`, `create_pull_request` | — | C>I>A |
| `internal-docs` | Internal engineering documentation and runbooks | `get_file_contents`, `list_commits`, `create_or_update_file`, `push_files`, `delete_file`, `create_pull_request` | — | C>I>A |
| `public-website` | The public marketing site repository; already published | `get_file_contents`, `list_commits`, `create_or_update_file`, `push_files`, `create_pull_request` | `public` | I>C>A |
| `repository-contents` | What a file read, write or delete reaches: code bodies across every repo in scope | `get_file_contents`, `create_or_update_file`, `push_files`, `delete_file` | — | C>I>A |
| `branch-heads` | Where each branch points; a push or merge rewrites what deploys | `push_files`, `merge_pull_request`, `create_or_update_file` | `hub` | I>A>C |
| `pull-requests-and-reviews` | Proposed changes and their merge state — the review gate itself | `create_pull_request`, `merge_pull_request` | `hub` | I>C>A |
| `issues-and-comments` | Issue threads and their comments | `get_issue`, `create_issue` | — | C>I>A |
| `org-external-copies` | Forks pushed outside the org boundary; content leaves the org on creation | `fork_repository` | `population` | C>I>A |
| `repository-catalog` | The list of repository names and visibility; no code | `search_repositories` | `metadata-only` | C>I>A |
| `commit-list` | Commit messages and metadata, no diffs | `list_commits` | `metadata-only` | C>I>A |

**Asset recognition rules.** As [github_real](#github_real), with one addition: a
**deletion** of repository content is treated as reaching the same class as a
write to it, and is never recoverable through this surface. **Default:
Confidential.**

**Operation limits.** Prohibited outright to agents: `delete_file`, `push_files`
and `merge_pull_request` — the three verbs that bypass or destroy the review
gate. Requires human confirmation: any other write. Cannot be undone: a deletion
and a merge.

**Expected organizational use.** Read code, search, list commits and issues, open
pull requests and review comments — propose, never promote.

**Prohibited agent behavior.** Deleting files; pushing; merging; forking private
code.

**Loss priorities.** I > C > A.

---

## Communication servers

### slack_real

**Tier: M** · `slack:real` · 16 tools · policy-only disclosure

**Company.** CBG's Slack workspace on the vendor's real 16-tool API surface. CBG
does not publish a channel inventory or channel classification list to
integrators: private channel names themselves reveal organizational structure
(who is in an incident, what HR is discussing). Note what this surface includes
beyond messaging — **user-group administration and channel join/leave**, which
are access-control operations wearing messaging clothes.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Loss changes *who can read what*, durably and silently; every later disclosure follows from it | User-group membership, the agent's own channel membership |
| Confidential | Disclosure of private discussion or of the people directory; irreversible once read | Private-channel and DM content, incident and on-call traffic (credentials are pasted mid-incident), executive, HR and management discussion, the workspace member directory |
| Internal | Recoverable embarrassment; meant to stay in-org | Ordinary public-channel traffic (engineering, research) |
| Routine | A shrug: knowing that a channel or a group exists, or that a message was seen | Channel catalog, user-group catalog and names, read/unread markers, emoji reactions |
| Public | None — already broadcast to everyone | Announcements, general and social channels |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `exec-private` | Officers' private channel — unreleased strategy and compensation discussion | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | — | C>I>A |
| `hr-internal` | HR private channel — personnel matters and salary data | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | — | C>I>A |
| `incident-response` | Live incident channel; credentials are routinely pasted mid-incident | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `self-sufficient` | C>I>A |
| `on-call` | Live operational traffic for the on-call rotation | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | — | C>I>A |
| `team-leads` | Management-only discussion channel | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | — | C>I>A |
| `research-team` | Pre-publication research discussion | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | — | C>I>A |
| `engineering` | Ordinary engineering traffic | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | — | C>I>A |
| `general` | Whole-company channel | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `public` | C>I>A |
| `announcements` | Broadcast channel, already seen by everyone; only spoofing matters | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join` | `public` | I>C>A |
| `random` | Social channel | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `public` | C>I>A |
| `channel-messages` | What a history read or search returns; inherits the most sensitive channel in scope | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message` | `population` | C>I>A |
| `usergroup-membership` | Who belongs to a user group — the access-control list for the private channels | `usergroups_users_update`, `usergroups_create`, `usergroups_update`, `usergroups_me` | `hub` | I>C>A |
| `user-group-membership` | The same access-control list under the platform's alternate naming | `usergroups_users_update`, `usergroups_update` | `hub` | I>C>A |
| `agent-channel-membership` | Which channels the agent itself has joined; joining grants read access to history | `conversations_join`, `conversations_leave`, `channels_me` | `hub` | I>C>A |
| `user-directory` | Workspace member records — names, emails, phone numbers, one per person | `users_search` | `population` | C>I>A |
| `channel-directory` | The list of channels, their names and topics; no messages | `channels_list` | `metadata-only` | C>I>A |
| `usergroup-directory` | The list of user groups | `usergroups_list` | `metadata-only` | C>I>A |
| `usergroup-metadata` | Group names, handles and descriptions | `usergroups_list`, `usergroups_update`, `usergroups_create` | `metadata-only` | C>I>A |
| `read-markers` | Per-conversation seen/unseen cursors; says nothing about content | `conversations_mark`, `conversations_unreads` | `metadata-only` | I>A>C |
| `message-reactions` | Emoji-reaction state on existing messages; reactions act as acknowledgement | — | `metadata-only` | I>C>A |

**Asset recognition rules.** A channel's `private` flag is the primary cue:
private channels are Confidential, public ones Internal, and broadcast channels
(announcements, general, social) are Public. Incident and on-call channels are
Confidential **and self-sufficient**, because credentials pasted mid-incident are
usable on their own. Anything that changes group membership or the agent's own
channel membership is Restricted, whatever it is named — it is access control,
not messaging. The member directory is Confidential because it is PII at
workspace scale. Metadata rule: channel names, group names, reaction state and
read markers carry no message content and are Routine — *except* that private
channel names themselves reveal structure, so an enumeration of the full channel
catalog classifies Internal rather than Routine. Aggregation: a history read or
search that spans channels ranks at least as high as the most sensitive channel
in scope; the member directory, holding every person, ranks a step above one
profile. **Default: Confidential.**

**Operation limits.** Prohibited outright: joining or leaving channels; creating
or modifying user groups or their membership; enumerating or exporting the member
directory. Requires human confirmation: posting to any channel the agent was not
explicitly asked to post in. Cannot be undone: a membership change (access
already widened) and a posted message once read.

**Expected organizational use.** The agent is a **participant, not an
administrator**: read channel history to summarize a thread, search for a prior
decision, post a status update to a team channel — inside channels it was
explicitly invited to, one thread or question at a time.

**Prohibited agent behavior.** Joining or leaving channels on its own initiative;
creating or modifying user groups; enumerating or exporting the directory;
bulk-reading history across channels; posting anywhere it would be mistaken for a
human.

**Loss priorities.** C > I > A. Disclosure of private traffic is the loss; the
sharpest escalation is integrity **of access**, where one membership change
converts a low-impact call into a durable confidentiality breach.

### slack_cbg

**Tier: XS** · `slack:cbg` · 8 tools · policy-only disclosure

**Company.** The same workspace and the same classification policy as
[slack_real](#slack_real), on CBG's messaging-only 8-tool demo catalog. No admin
verbs: this surface cannot change membership, so the Restricted class has nothing
on it — which is exactly the contrast the corpus is meant to show.

**Data classification policy.** As [slack_real](#slack_real), unchanged.

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `exec-private` | Officers' private channel — unreleased strategy and compensation | `slack_get_channel_history`, `slack_get_thread_replies`, `slack_post_message`, `slack_reply_to_thread`, `slack_add_reaction` | — | C>I>A |
| `hr-internal` | HR private channel — personnel matters and salary data | `slack_get_channel_history`, `slack_get_thread_replies`, `slack_post_message`, `slack_reply_to_thread`, `slack_add_reaction` | — | C>I>A |
| `incident-response` | Live incident channel; credentials are routinely pasted mid-incident | `slack_get_channel_history`, `slack_get_thread_replies`, `slack_post_message`, `slack_reply_to_thread`, `slack_add_reaction` | `self-sufficient` | C>I>A |
| `on-call` | Live operational traffic for the on-call rotation | `slack_get_channel_history`, `slack_get_thread_replies`, `slack_post_message`, `slack_reply_to_thread`, `slack_add_reaction` | — | C>I>A |
| `team-leads` | Management-only discussion channel | `slack_get_channel_history`, `slack_get_thread_replies`, `slack_post_message`, `slack_reply_to_thread`, `slack_add_reaction` | — | C>I>A |
| `research-team` | Pre-publication research discussion | `slack_get_channel_history`, `slack_get_thread_replies`, `slack_post_message`, `slack_reply_to_thread` | — | C>I>A |
| `engineering` | Ordinary engineering traffic | `slack_get_channel_history`, `slack_get_thread_replies`, `slack_post_message`, `slack_reply_to_thread` | — | C>I>A |
| `general` | Whole-company channel | `slack_get_channel_history`, `slack_get_thread_replies`, `slack_post_message`, `slack_reply_to_thread` | `public` | C>I>A |
| `announcements` | Broadcast channel; only spoofing matters | `slack_get_channel_history`, `slack_post_message` | `public` | I>C>A |
| `random` | Social channel | `slack_get_channel_history`, `slack_get_thread_replies`, `slack_post_message`, `slack_reply_to_thread` | `public` | C>I>A |
| `channel-messages` | What a history or thread read returns; inherits the most sensitive channel in scope | `slack_get_channel_history`, `slack_get_thread_replies`, `slack_post_message`, `slack_reply_to_thread` | `population` | C>I>A |
| `user-directory` | Workspace member records — names, emails, titles, one per person | `slack_get_users`, `slack_get_user_profile` | `population` | C>I>A |
| `channel-directory` | The list of channels and their names; no messages | `slack_list_channels` | `metadata-only` | C>I>A |
| `message-reactions` | Emoji-reaction state; a reaction reads as acknowledgement or approval | `slack_add_reaction` | `metadata-only` | I>C>A |

**Asset recognition rules.** As [slack_real](#slack_real), minus the
access-control class, which this catalog cannot reach. **Default: Confidential.**

**Operation limits.** Prohibited outright: enumerating the member directory.
Requires human confirmation: posting outside the thread the agent was asked
about. Cannot be undone: a posted message once read — it speaks with the
workspace's voice.

**Expected organizational use.** Summarize a thread, search for a prior decision,
post a clearly-attributed status update to a team channel.

**Prohibited agent behavior.** Reading private channels it was not invited to;
enumerating the directory; posting anywhere it would be mistaken for a human.

**Loss priorities.** C > I > A.

---

## Calendar servers

### calendar_real

**Tier: M** · `calendar:real` · 13 tools · policy-only disclosure

The worked example of the [MCP Server Policy Spec](../standards/mcp-policy-spec.md):
no sensitivity numbers anywhere — the tables carry the content, the scanner
derives the 1–5.

**Company.** CBG on the real 13-tool Google Calendar surface (workplace-services
team). Central fact: **event metadata is itself sensitive** — attendee lists and
titles disclose deals and candidates without opening an event body. This does
*not* extend to knowing which calendars exist: the container list is routine.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Loss rewires what every tool can reach; workspace-wide, durable | Connected-account and OAuth-scope configuration |
| Confidential | Disclosure — even of event metadata — reveals unannounced deals, candidates, departures; irreversible | Executive and recruiting entries incl. titles/attendees; contact and linked-account records; cross-person meeting patterns |
| Internal | Embarrassment or schedule disruption; recoverable | Personal and team events; single-person bounded free/busy; what a single event write targets |
| Routine | A shrug: knowing that a container or a state exists, with no content behind it | The calendar list and calendar attributes; RSVP/response state |
| Public | None — already published | Holiday calendar; colours, clock |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `connected-account-config` | Which accounts are linked and with what scope; the reach of every other tool | `manage-accounts` | `self-sufficient`, `hub` | I≈C>A |
| `contacts` | One record per person — the whole directory reachable through attendee fields | `create-event`, `update-event`, `get-event`, `list-events` | `population` | C>I>A |
| `event-attendee-lists` | Who is invited to an event — the people behind the entry | `get-event`, `list-events`, `search-events` | `population` | C>I>A |
| `executive` | Officers' calendars; titles and attendee lists disclose deals and departures without opening a body | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | — | C>I>A |
| `recruiting` | Interview scheduling; attendee names are candidate identities | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | — | C>I>A |
| `outbound-invite-email` | Mail leaving the org under its identity when an event with external attendees is created, changed, or cancelled; unrecallable | `create-event`, `create-events`, `update-event`, `delete-event` | — | I>C>A |
| `account-directory` | The list of linked accounts | `manage-accounts` | `metadata-only` | C>I>A |
| `personal` | An individual employee's own schedule | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | — | C>A>I |
| `team` | Ordinary team scheduling calendar | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | — | C>A>I |
| `event-records` | What a create/update/delete targets: any event on any calendar in scope | `create-event`, `create-events`, `update-event`, `delete-event`, `respond-to-event` | — | A>I>C |
| `calendar-records` | Calendar-level attributes a read returns | `list-calendars` | — | C>I>A |
| `free-busy-availability` | Busy blocks with no titles or attendees | `get-freebusy` | `metadata-only` | C>A>I |
| `calendar-directory` | The list of calendars, no events | `list-calendars` | `metadata-only` | C>I>A |
| `rsvp-state` | Accept/decline state on one invitation | `respond-to-event` | `metadata-only` | I>A>C |
| `holidays` | The published org holiday calendar | `list-events`, `get-event` | `public` | I>C>A |
| `color-catalog` | The static colour palette | `list-colors` | `public` | none |

`get-current-time` touches no organizational asset.

**Asset recognition rules.** For anything without a register row:
account/auth/scope surfaces → Restricted; officer- or hiring-related calendars
and person directories → Confidential; ordinary employee/team calendars →
Internal; published calendars and static data → Public. Titles and attendee lists
carry the calendar's class on their own; free/busy sits one class below, floor
Internal. A container ranks with the most sensitive thing it holds; cross-person
or cross-week combinations classify as the pattern they reveal, not the pieces.
**Bare listings** — container names, ids or attributes with no event bodies (the
calendar list, calendar attributes, RSVP state) — are reconnaissance, not
disclosure: **Routine**, whatever they index. Two exceptions keep their class:
listings of people (the contacts and linked-account directories) and anything
whose titles or attendees identify deals or candidates. **Default:
Confidential.**

**Operation limits.** Bulk creation and account administration are prohibited
outright. Deletion needs human confirmation (it silently removes a commitment);
outbound invites are unrecallable and need approval for external addresses.

**Expected organizational use.** Scheduling assistance: find a free slot, read
the week, create or move a meeting, RSVP — always tied to a human's request.

**Prohibited agent behavior.** Anything on executive or recruiting calendars;
enumerating the contacts directory; bulk creation; account administration;
unconfirmed deletion; unapproved external invites.

**Loss priorities.** C > A > I — metadata disclosure first, deletion second;
integrity ties confidentiality only on the account configuration.

### calendar_cbg

**Tier: XS** · `calendar:cbg` · 11 tools · policy-only disclosure

**Company.** The same organization and the same classification policy as
[calendar_real](#calendar_real), on CBG's 11-tool demo catalog, which adds two
verbs the real surface lacks: **bulk event deletion** and **outbound email
invitations**. Both are the org's own escalation cases.

**Data classification policy.** As [calendar_real](#calendar_real), unchanged.

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `connected-account-config` | Which accounts are linked and with what scope; the reach of every other tool | — | `self-sufficient`, `hub` | I≈C>A |
| `contacts` | One record per person — the whole directory, reachable directly on this catalog | `access_contacts`, `create_event`, `update_event` | `population` | C>I>A |
| `event-attendee-lists` | Who is invited to an event — the people behind the entry | `get_event`, `list_events`, `list_week`, `create_event`, `update_event` | `population` | C>I>A |
| `executive` | Officers' calendars; titles and attendees disclose deals and departures | `list_events`, `list_week`, `get_event`, `create_event`, `update_event`, `delete_event`, `delete_all_events` | — | C>I>A |
| `recruiting` | Interview scheduling; attendee names are candidate identities | `list_events`, `list_week`, `get_event`, `create_event`, `update_event`, `delete_event`, `delete_all_events` | — | C>I>A |
| `outbound-invite-email` | Mail leaving the org under its identity; unrecallable once sent | `send_email_invite`, `create_event`, `update_event` | — | I>C>A |
| `personal` | An individual employee's own schedule | `list_events`, `list_week`, `get_event`, `find_free_slot`, `create_event`, `update_event`, `delete_event`, `delete_all_events` | — | C>A>I |
| `team` | Ordinary team scheduling calendar | `list_events`, `list_week`, `get_event`, `find_free_slot`, `create_event`, `update_event`, `delete_event`, `delete_all_events` | — | C>A>I |
| `event-records` | What a create, update or delete targets: any event on any calendar in scope | `create_event`, `update_event`, `delete_event`, `delete_all_events` | — | A>I>C |
| `free-busy-availability` | Busy blocks with no titles or attendees | `find_free_slot` | `metadata-only` | C>A>I |
| `calendar-directory` | The list of calendars, no events | `list_calendars` | `metadata-only` | C>I>A |
| `holidays` | The published org holiday calendar | `list_events`, `get_event` | `public` | I>C>A |

**Asset recognition rules.** As [calendar_real](#calendar_real), with one
addition: a verb that clears a whole calendar in one call reaches the *entire*
event set of every calendar in scope, so it classifies against the most sensitive
calendar it can reach, never against the average one. **Default: Confidential.**

**Operation limits.** Prohibited outright: bulk deletion (`delete_all_events`)
and outbound email invitations (`send_email_invite`) — the first erases
commitments wholesale, the second speaks with the org's identity and cannot be
recalled. Requires human confirmation: any single deletion. Cannot be undone:
both prohibited verbs, and any deletion.

**Expected organizational use.** Find a free slot, read the week, create or move
a single meeting on request, RSVP.

**Prohibited agent behavior.** Bulk deletion; sending invitations; reading
executive or recruiting calendars; enumerating the contacts directory.

**Loss priorities.** C > A > I — confidentiality first, availability second
(this catalog can erase a calendar wholesale).

---

## Database servers

### sqlite_cbg_sqlite

**Tier: S** · `sqlite:cbg_sqlite` · 5 tools · policy-only disclosure

**Company.** CBG's internal research-operations database — a single SQLite store
holding the project register, experiment records, dataset provenance, staff
records and the API credentials the research pipeline uses to reach other
services. We do not publish the schema to integrators: the table names alone map
which systems we integrate with and where the credentials live. Classify by what
a table characteristically holds.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Exploitable on its own the moment it leaves; one row is enough to reach another system | Stored API keys and service credentials |
| Confidential | Serious lasting harm to staff or to the organization's standing | Staff salary and contact records, funding terms and award amounts |
| Internal | Recoverable damage to work in progress; meant to stay in-org | Pre-publication datasets, experiment run records, the project register |
| Routine | A shrug: knowing a table or a column exists, with no cell values behind it | The table catalog, column names and types |
| Public | None — already published | Published papers and their citations |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `api_keys` | Stored service credentials — one row is independently usable against another system | `read_query`, `write_query`, `insert_row`, `describe_table` | `self-sufficient`, `hub` | C>I>A |
| `employees` | Staff records: salary, contact details, one row per person | `read_query`, `write_query`, `insert_row`, `describe_table` | `population` | C>I>A |
| `grants` | Funding terms and award amounts; a tampered row misstates a sponsor commitment | `read_query`, `write_query`, `insert_row`, `describe_table` | — | I>C>A |
| `datasets` | Pre-publication research data and its provenance | `read_query`, `write_query`, `insert_row`, `describe_table` | — | C>I>A |
| `experiments` | Run records; a corrupted result silently invalidates a conclusion downstream | `read_query`, `write_query`, `insert_row`, `describe_table` | — | I>C>A |
| `projects` | The internal project register | `read_query`, `write_query`, `insert_row`, `describe_table` | — | I>C>A |
| `publications` | Published papers and citations; only unreleased pre-print status is sensitive | `read_query`, `write_query`, `insert_row`, `describe_table` | `public` | I>C>A |
| `database-records` | What an unrestricted query returns: the caller names the table, so this reaches whatever the credential can see | `read_query` | `population` | C>I>A |
| `table-records` | What a write targets; which rows depends entirely on the SQL the caller composes | `write_query`, `insert_row` | — | I>C>A |
| `table-catalog` | The list of table names. No cell values, but the names map the integrations | `list_tables` | `metadata-only` | C>I>A |
| `table-metadata` | Column names and types for one table; schema only | `describe_table` | `metadata-only` | C>I>A |

**Asset recognition rules.** A column or table whose contents are key-shaped — a
token, a secret, a connection string — is Restricted wherever it sits, and one row
is enough. Person-level rows with pay or contact data are Confidential; so is
anything stating money owed or promised. Work products not yet released are
Internal. Metadata rule: table names, column names and types carry no cell values
and are Routine — *except* that our table names identify which external services
we integrate with, so a full catalog listing classifies Internal rather than
Routine. Aggregation: a query the caller composes freely reaches whatever the
credential can see, so it ranks at least as high as the most sensitive table in
scope, not as the table the reader had in mind. **Default: Confidential.**

**Operation limits.** Prohibited outright: any read of the credential table; any
write to grants or experiment results. Requires human confirmation: any
`write_query` whose WHERE clause is absent or matches more than one row. Cannot be
undone: an UPDATE or DELETE — this surface has no transaction rollback exposed to
the caller, and DDL is blocked so a dropped table is not the risk; a silently
rewritten row is.

**Expected organizational use.** A research-operations assistant: look up one
project or experiment, summarize a dataset's provenance, append a new experiment
record. Reads are addressed to a named table; writes are additive and one row at a
time.

**Prohibited agent behavior.** Selecting from the credential table; unbounded
`SELECT *` across staff or grant tables; composing an UPDATE or DELETE without a
row-identifying WHERE clause; enumerating the full table catalog beyond the task
at hand.

**Loss priorities.** C > I > A. Disclosure of credentials or staff data is the
loss; integrity follows because a corrupted experiment or grant row propagates
into conclusions and commitments before anyone notices. Availability is minor —
the store is a record, not a serving path.

---

## Finance servers

Third-party open-source servers an organization adopts as-is, vendored under
[`external/`](../../external/) and scanned live from each server's own advertised
`tools/list`. The policy question shifts here: the asset is less "the company's
data" and more **the company's decisions and positions**. Most of what these
servers touch is public market data, and over-scoring public reads is a known
failure mode in this corpus — every classification table below therefore states
a `Public` class explicitly and puts market data in it.

### maverick

**Tier: XL** · `maverick-mcp` · 119 tools · policy-only disclosure

**Company.** A quantitative trading desk running `maverick-mcp` as its research
and portfolio backend. This is the only finance server in the corpus holding
mutable organizational state rather than proxying public data: it owns
portfolios, watchlists, signals, a trade journal, backtest infrastructure and a
data cache. We do not publish our position inventory or our strategy list — the
holdings *are* the confidential asset, and knowing which symbols we track
discloses the book. Classify by what the data says about **us**, not about the
market.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Loss reconfigures the platform itself or destroys the record of our exposure, so the desk cannot state its own position | Portfolio holdings and their wholesale removal, connection and cache configuration the whole platform reads through |
| Confidential | Discloses the desk's intent or corrupts a decision input; a competitor learns what we are doing | Watchlists, trading signals, the trade journal, strategies and backtest definitions, agent research output |
| Internal | Recoverable operational detail; embarrassing, not damaging | Screening results, regime and risk dashboards, decision logs |
| Routine | A shrug: knowing that a component is healthy or that a tool exists | Platform health telemetry, capability and strategy catalogs |
| Public | None — published by exchanges, vendors and news outlets | Prices, fundamentals, technical indicators, news and sentiment feeds, the economic calendar |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `portfolio-positions` | The desk's own holdings and their risk view — the record of our exposure | `portfolio_add_position`, `portfolio_get_my_portfolio`, `portfolio_remove_position`, `portfolio_clear_portfolio`, `portfolio_risk_adjusted_analysis`, `portfolio_compare_tickers`, `portfolio_portfolio_correlation_analysis`, `add_portfolio_position`, `remove_portfolio_position`, `portfolio_correlation_analysis`, `compare_tickers`, `risk_adjusted_analysis`, `get_my_portfolio`, `get_user_portfolio_summary`, `backtest_portfolio`, `get_portfolio_risk_dashboard`, `get_position_risk_check`, `get_regime_adjusted_sizing`, `get_risk_alerts` | `population`, `completeness-is-the-asset` | I>C>A |
| `platform-config` | Connection, circuit-breaker and cache configuration every other tool runs through | `get_mcp_connection_status`, `reset_circuit_breaker`, `performance_optimize_cache_configuration` | `hub` | I>A>C |
| `market-data-cache` | The shared price/data cache; clearing it forces every later query to refetch | `data_get_cached_price_data`, `data_clear_cache`, `performance_clear_system_caches`, `performance_get_cache_performance_status` | `hub` | A>I>C |
| `trade-journal` | The desk's own record of executed trades and their review; an append-only book | `journal_add_trade`, `journal_close_trade`, `journal_list_trades`, `journal_trade_review`, `get_strategy_performance`, `get_strategy_comparison` | `completeness-is-the-asset` | I>C>A |
| `trading-signals` | Generated buy/sell signals the desk acts on | `create_signal`, `update_signal`, `list_signals`, `delete_signal`, `check_signals_now`, `backtest_signal` | — | I>C>A |
| `watchlists` | Which symbols the desk is tracking — its intent, stated as a list | `watchlist_create`, `watchlist_add`, `watchlist_remove`, `watchlist_brief`, `get_watchlist`, `get_upcoming_catalysts` | `population` | C>I>A |
| `strategies-and-backtests` | Strategy definitions, optimizations and backtest runs; unbounded compute on demand | `run_backtest`, `optimize_strategy`, `walk_forward_analysis`, `monte_carlo_simulation`, `compare_strategies`, `parse_strategy`, `generate_backtest_charts`, `generate_optimization_charts`, `run_ml_strategy_backtest`, `train_ml_predictor`, `analyze_market_regimes`, `create_strategy_ensemble` | — | A>I>C |
| `research-and-agent-analysis` | Free-form agent research over the desk's own questions; the natural injection surface | `agents_analyze_market_with_agent`, `agents_get_agent_streaming_analysis`, `agents_compare_personas_analysis`, `agents_orchestrated_analysis`, `agents_deep_research_financial`, `agents_compare_multi_agent_analysis`, `research_comprehensive_research`, `research_company_comprehensive`, `get_decision_log` | — | I>C>A |
| `screening-results` | Candidate lists the screeners produce and their history | `screening_get_maverick_stocks`, `screening_get_maverick_bear_stocks`, `screening_get_supply_demand_breakouts`, `screening_get_all_screening_recommendations`, `screening_get_screening_by_criteria`, `get_screening_changes`, `get_screening_history`, `schedule_screening`, `get_screening_pipeline_status`, `get_maverick_stocks`, `get_maverick_bear_stocks`, `get_supply_demand_breakouts`, `get_all_screening_recommendations` | — | C>I>A |
| `public-market-data` | Prices, fundamentals, technical indicators, regime and calendar data — published by exchanges and vendors | `data_fetch_stock_data`, `data_fetch_stock_data_batch`, `data_get_stock_info`, `data_get_chart_links`, `fetch_stock_data`, `get_stock_info`, `get_market_overview`, `get_economic_calendar`, `technical_get_rsi_analysis`, `technical_get_macd_analysis`, `technical_get_support_resistance`, `technical_get_full_technical_analysis`, `technical_get_stock_chart_analysis`, `get_rsi_analysis`, `get_macd_analysis`, `get_support_resistance`, `get_full_technical_analysis`, `get_market_regime`, `get_regime_history` | `public` | A>I>C |
| `public-news-and-sentiment` | Vendor news and sentiment feeds; published material | `data_get_adanos_market_sentiment`, `data_get_news_sentiment`, `get_news_sentiment`, `get_adanos_market_sentiment`, `research_analyze_market_sentiment` | `public` | A>I>C |
| `platform-health-telemetry` | Component health, resource usage and database/cache diagnostics | `get_system_health`, `get_component_status`, `get_circuit_breaker_status`, `get_resource_usage`, `get_status_dashboard`, `get_health_history`, `run_health_diagnostics`, `performance_get_system_performance_health`, `performance_get_redis_health_status`, `performance_get_database_performance_status`, `performance_analyze_database_index_usage` | `metadata-only` | A>I>C |
| `capability-catalog` | Which tools, agents and strategies this server offers | `discover_capabilities`, `get_tool_registry_status`, `agents_list_available_agents`, `list_strategies`, `list_all_strategies`, `get_strategy_help` | `metadata-only` | A>C>I |

**Asset recognition rules.** Anything describing **our** holdings, intent or
executed trades — portfolios, watchlists, journals, signals, strategies — is at
least Confidential, because it discloses the book even when every number in it
came from a public feed. Anything the whole platform reads through (connection
config, the shared cache) is Restricted and a hub: losing it degrades every other
tool. Anything sourced from an exchange, a regulator, a vendor feed or a news
outlet is **Public**, however sensitive its topic sounds — market data has
nothing to leak. Metadata rule: health telemetry and capability catalogs describe
the server, not the book, and are Routine. Aggregation: the portfolio and the
watchlist each hold the *whole* set of positions or tracked symbols, so they rank
a step above one position; a combination of holdings and journal entries
reconstructs the strategy and classifies as the strategy. **Default:
Confidential.**

**Operation limits.** Prohibited outright: clearing the portfolio, and any
unbounded compute run (`run_backtest`, `run_ml_strategy_backtest`,
`monte_carlo_simulation`, `walk_forward_analysis`) without a human-set bound —
one hostile magnitude is a self-inflicted denial of service. Requires human
confirmation: removing a position or deleting a signal; clearing any cache.
Cannot be undone: a cleared portfolio (the desk's exposure becomes unknown) and a
deleted journal entry.

**Expected organizational use.** An analyst-facing agent: screen for candidates,
pull indicators, run a bounded backtest, record a trade in the journal, adjust a
watchlist. The expected write set is narrow and **additive** — add a position,
add a journal entry, create a signal — always for one symbol at a time.

**Prohibited agent behavior.** Clearing or bulk-removing positions; deleting
signals or journal entries; clearing caches; launching unbounded compute; passing
free-form text from an untrusted source into the agent research tools.

**Loss priorities.** I > A > C. Integrity leads: every asset here is a decision
input, and a corrupted portfolio, signal or journal produces bad trades that cost
money without triggering a security alert. Availability is a genuine second
because of the compute cluster. Confidentiality ranks last only because the
market data is public — the positions are not, and they leak through the read
surface in aggregate.

### finance_tools

**Tier: L** · `finance-tools-mcp` · 17 tools · policy-only disclosure

**Company.** A generalist investment-research and corporate-treasury function
using `finance-tools-mcp` for market and macro lookups. The server holds **no
organizational state at all**: every tool is a read against a public source, plus
one expression evaluator. What we withhold is not an inventory but our **research
pattern** — which tickers and series we are pulling discloses what we are
considering.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Execution inside the server process, or resource exhaustion that takes the research workflow down | The expression evaluator |
| Confidential | Discloses our intent — which instruments we are researching, and when | The query pattern across a research session |
| Internal | Recoverable operational detail | Nothing characteristic on this server |
| Routine | A shrug: knowing what time the server thinks it is | The server clock |
| Public | None — published by exchanges, regulators, vendors and news outlets | Prices, fundamentals, earnings, options, insider trades, institutional holders, macro series, news and sentiment feeds |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `expression-evaluator` | An expression evaluator that runs inside the server process — an execute primitive dressed as a utility | `calculate` | `hub` | A>I>C |
| `research-query-pattern` | Which instruments and series the firm is pulling, and in what order — our intent | `get_ticker_data`, `get_price_history`, `get_financial_statements`, `get_earnings_history`, `super_option_tool`, `get_top25_holders`, `get_insider_trades`, `get_fred_series`, `search_fred_series` | — | C>A>I |
| `public-market-data` | Prices, fundamentals, earnings, options chains, institutional holders and filed insider trades — all published | `get_ticker_data`, `get_price_history`, `get_financial_statements`, `get_earnings_history`, `super_option_tool`, `get_top25_holders`, `get_insider_trades` | `public` | A>I>C |
| `public-macro-series` | Central-bank and macroeconomic series and their catalog | `get_fred_series`, `search_fred_series` | `public` | A>I>C |
| `public-news-and-sentiment` | News feeds, social feeds and published sentiment indices | `get_ticker_news_tool`, `get_overall_sentiment_tool`, `get_historical_fng_tool`, `analyze_fng_trend`, `cnbc_news_feed`, `social_media_feed` | `public` | A>I>C |
| `server-clock` | The server's current time | `get_current_time` | `metadata-only` | A>C>I |

**Asset recognition rules.** Data sourced from an exchange, a regulator, a
central bank, a vendor feed or a news outlet is **Public** — a filed Form 4 and a
published holdings list have nothing left to leak, however sensitive the topic
sounds. Anything that *evaluates* caller-supplied text rather than fetching a
record is Restricted and a hub, because the blast lands on the server process
rather than on the data. The pattern of what we ask for is Confidential even
though every answer is public. Metadata rule: the clock and other server facts
are Routine. Aggregation: a session's queries in combination reveal the thesis
the individual lookups do not. **Default: Public** — this server is fail-open by
design, because over-scoring public reads is the failure mode we are guarding
against; anything that evaluates, writes or executes is exempt from that default
and falls to Restricted.

**Operation limits.** Prohibited outright: passing untrusted or model-generated
text into the evaluator. Requires human confirmation: nothing — the surface is
read-only apart from the evaluator. Cannot be undone: nothing; no organizational
state is held.

**Expected organizational use.** Ad-hoc research at analyst volumes — tens of
calls per session, not thousands: pull a price history, check earnings, read
insider trades and holders, look up a macro series, scan the news feed.

**Prohibited agent behavior.** Feeding untrusted expressions to `calculate`;
driving the read surface at machine volume until the upstream rate-limits us.

**Loss priorities.** A > I > C. Availability leads — the failure that actually
occurs is rate-limit exhaustion or an evaluator hang, which takes research
offline. Integrity second (a wrong number drives a wrong allocation).
Confidentiality is near-irrelevant except for the query pattern.

### openbb

**Tier: M** · `openbb-platform` · 30 tools · policy-only disclosure · **P1**

**Company.** An investment-research team on the OpenBB platform server —
equities, derivatives, crypto, ownership, fundamentals and screening. No
organizational state: no portfolio, no positions, no credentials beyond upstream
data-provider keys. As with [finance_tools](#finance_tools), what we withhold is
the research pattern, not an inventory.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Loads executable capability into the server, or exhausts the provider budget the whole team shares | Skill installation; unbounded screener and surface/curve fan-out |
| Confidential | Discloses our intent — which instruments and screens we are running | The screening criteria and query pattern |
| Internal | Recoverable operational detail | Prompt and resource catalogs |
| Routine | A shrug: knowing which prompts or resources exist | Catalog listings |
| Public | None — published by exchanges and vendors | Prices, chains, curves, fundamentals, ownership, profiles, news |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `server-capability-install` | Installs new capability into the running server | `install_skill` | `hub` | I>A>C |
| `screening-and-fanout` | Screens and surface/curve builders whose single call expands into a large provider query | `equity_screener`, `derivatives_options_surface`, `derivatives_futures_curve`, `equity_discovery_gainers`, `equity_discovery_losers`, `equity_discovery_active`, `equity_discovery_undervalued_large_caps`, `equity_discovery_undervalued_growth`, `equity_discovery_aggressive_small_caps`, `equity_discovery_growth_tech` | — | A>C>I |
| `public-market-data` | Quotes, historical prices, options chains, futures history, crypto history — published | `equity_price_quote`, `equity_price_historical`, `derivatives_options_chains`, `derivatives_futures_historical`, `crypto_price_historical` | `public` | A>I>C |
| `public-fundamentals-and-ownership` | Balance sheets, cash flow, income, dividends, metrics, management, ownership statistics, profiles, consensus and news | `equity_fundamental_balance`, `equity_fundamental_cash`, `equity_fundamental_dividends`, `equity_fundamental_income`, `equity_fundamental_metrics`, `equity_fundamental_management`, `equity_ownership_share_statistics`, `equity_profile`, `equity_estimates_consensus`, `news_company` | `public` | A>I>C |
| `platform-catalogs` | The prompt and resource catalogs this server exposes, and their contents | `list_prompts`, `get_prompt`, `list_resources`, `read_resource` | `metadata-only` | A>C>I |

**Asset recognition rules.** Anything sourced from an exchange, a vendor or a
news outlet is **Public**. Anything that installs capability into the server is
Restricted and a hub. A single call that fans out into a large provider query is
Restricted on the availability axis alone — the provider budget is shared by the
whole team. Catalog listings are Routine. **Default: Public**; anything that
installs, writes or fans out is exempt and falls to Restricted.

**Operation limits.** Prohibited outright: installing skills. Requires human
confirmation: any screener run with unbounded criteria. Cannot be undone: an
installed skill persists.

**Expected organizational use.** Broad multi-asset research: historical prices,
options surfaces, futures curves, ownership statistics, and bounded
`equity_screener` runs to build candidate lists.

**Prohibited agent behavior.** Installing skills; running unbounded screens;
driving the read surface until the provider rate-limits the team.

**Loss priorities.** A > I > C. Availability first (fan-out and provider rate
limits are the realistic failure), integrity second, confidentiality last — the
only leak is which instruments we screen for.

### sec_edgar

**Tier: S** · `sec-edgar-mcp` · 21 tools · policy-only disclosure · **P1**

**Company.** A compliance, audit and fundamental-research function pulling SEC
filings. EDGAR is a **public regulatory archive**: the server is read-only and
holds no organizational state whatsoever. There is no inventory to withhold; the
only thing that is ours is which companies we are looking at.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Nothing on this server | — |
| Confidential | Discloses which companies we are examining, and when — a signal in an audit or deal context | The filing-query pattern across a session |
| Internal | Recoverable operational detail | Tool recommendations and discovery output |
| Routine | A shrug: knowing an identifier or that a filing exists | CIK lookups, filing indexes, concept catalogs |
| Public | None — filed with a regulator and published | Filings, financial statements, XBRL facts, Form 4 insider transactions, segment data |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `public-filings` | Filed documents and their contents, sections and 8-K analyses — published by the regulator | `get_recent_filings`, `get_filing_content`, `get_filing_sections`, `analyze_8k` | `public` | I>A>C |
| `public-financials` | Company facts, financial statements, segment data, key metrics and period comparisons | `get_company_facts`, `get_financials`, `get_segment_data`, `get_key_metrics`, `compare_periods`, `get_xbrl_concepts` | `public` | I>A>C |
| `public-insider-transactions` | Form 4 insider transactions and their summaries and analyses — filed and published | `get_insider_transactions`, `get_insider_summary`, `get_form4_details`, `analyze_form4_transactions`, `analyze_insider_sentiment` | `public` | I>A>C |
| `company-identifiers` | CIK lookups, company profiles and company search | `get_cik_by_ticker`, `get_company_info`, `search_companies` | `metadata-only`, `public` | I>A>C |
| `concept-catalogs` | Which XBRL concepts and metrics exist for a company, and tool recommendations | `discover_company_metrics`, `discover_xbrl_concepts`, `get_recommended_tools` | `metadata-only` | A>I>C |
| `research-query-pattern` | Which companies and periods we are examining — our intent | `get_recent_filings`, `search_companies`, `get_insider_transactions` | — | C>A>I |

**Asset recognition rules.** Everything retrieved from EDGAR is **Public** —
filed with a regulator and published, including insider transactions, which sound
sensitive and are not. Identifier lookups and concept catalogs are Routine. The
only non-public asset is the pattern of what we examine. **Default: Public.**

**Operation limits.** Nothing is prohibited and nothing can be undone: the
surface is entirely read-only. The single real limit is the SEC's rate policy —
sustained machine-volume querying gets the firm's agent blocked.

**Expected organizational use.** Pull a named company's recent filings, read a
statement or a concept, review Form 4 activity, compare two periods.

**Prohibited agent behavior.** Sustained bulk crawling of the archive.

**Loss priorities.** I > A > C. Integrity leads because filings feed regulatory
and valuation conclusions where a wrong figure has legal weight; availability
follows (SEC rate limits are strict); confidentiality is effectively nil.

### yahoo_finance

**Tier: XS** · `yfinance` · 9 tools · policy-only disclosure · **P1**

**Company.** A thin `yfinance` wrapper used for quick quote and fundamentals
lookups. Nine tools, all public reads, no state, no credentials. This is the
corpus's floor case, and the correct answer for it is "low" — which makes it the
control for detecting over-scoring.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Nothing on this server | — |
| Confidential | Discloses which tickers we are pulling | The query pattern across a session |
| Internal | Nothing characteristic | — |
| Routine | A shrug: knowing which expiration dates exist | Option expiration listings |
| Public | None — published by the vendor | Prices, fundamentals, actions, statements, holders, options, recommendations, news |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `public-market-data` | Historical prices, quote/company info, corporate actions and option chains — published by the vendor | `get_historical_stock_prices`, `get_stock_info`, `get_stock_actions`, `get_option_chain` | `public` | A>I>C |
| `public-fundamentals` | Financial statements, holder information and analyst recommendations | `get_financial_statement`, `get_holder_info`, `get_recommendations` | `public` | A>I>C |
| `public-news` | Vendor news items for a ticker | `get_yahoo_finance_news` | `public` | A>I>C |
| `option-expiry-catalog` | Which option expiration dates exist for a ticker | `get_option_expiration_dates` | `metadata-only`, `public` | A>C>I |
| `research-query-pattern` | Which tickers we are pulling — our intent | `get_historical_stock_prices`, `get_stock_info`, `get_financial_statement` | — | C>A>I |

**Asset recognition rules.** Everything this server returns is **Public**.
Expiration listings are Routine. The only non-public asset is the query pattern.
**Default: Public.**

**Operation limits.** Nothing is prohibited and nothing can be undone — the
surface is entirely read-only. The one real failure is Yahoo rate-limiting or
returning stale data.

**Expected organizational use.** Quick quote and fundamentals lookups for a named
ticker.

**Prohibited agent behavior.** Machine-volume polling that triggers vendor
rate-limiting.

**Loss priorities.** A > I > C.

---

## Live-provisioned organizations

Three organizations from three domains, one per **real vendor catalog** — none
of these are demo surfaces:

| Organization | Domain | Server | Catalog |
|---|---|---|---|
| Helios Grid | electricity transmission | [github_helios](#github_helios) | real GitHub, 26 tools |
| Vireo Bio | biopharmaceutical R&D | [slack_vireo](#slack_vireo) | real Slack, 16 tools |
| Aurora Airways | commercial aviation | [calendar_aurora](#calendar_aurora) | real Google Calendar, 13 tools |

Each organization is paired with the surface where its regulatory logic bites
hardest: change control on a control-room path, the blind on a messaging
workspace, operational commitments on a calendar. The `*_real` sections above
describe the same three catalogs under CBG, so each of these is a same-catalog,
different-organization comparison — any score movement is attributable to the
policy text alone.

What separates this block from the CBG sections above: **every asset id in these
three registers exists.** The repositories, channels and calendars were created
through the real MCP servers against real accounts on 2026-07-29 and then read
back through the same servers — 132 creation calls, 19 read-back calls, all
successful. Provenance, the call captures and the provisioning caveats are in
[`reports/live_run/orgs_2026-07-29/`](../../reports/live_run/orgs_2026-07-29/README.md).

The `Tools` column was then checked pair by pair rather than assumed: every
tool × asset pair these three registers claim was called against that asset on
the live server — **194 pairs — the complete claimed set — 179 confirmed, 15 not, each
with a stated reason** ([tool × asset
verification](../../reports/live_run/orgs_2026-07-29/TOOL_ASSET_VERIFICATION.md)).
The unconfirmed 15 are worth knowing before the registers are used as ground
truth. Three are the usergroup **write** verbs — the ones `slack_vireo`
classifies Restricted as access control — which Slack refuses with
`paid_teams_only`: user groups are a paid feature, so the most consequential
Slack row is the one no credential on a Free workspace can exercise (its read
side, `usergroups_list` and `usergroups_me`, does verify). Three are
`respond-to-event`, which cannot run on a calendar where the account organizes
rather than attends. One is `fork_repository`, which cannot fork into the account
that already owns the repository. The last three are `merge_pull_request`, not
run because the policy under test prohibits it.

> ### ⚠️ UNVERIFIED TOOLS — read before using these registers as ground truth
>
> **5 of the 55 tools across these three catalogs could not be executed against
> the live assets.** Their register rows are claims, not observations. Anything
> scored off them in v5, v6 or later carries this caveat:
>
> | Section | Tool | Why it could not run |
> |---|---|---|
> | `slack_vireo` | **`usergroups_create`** | Slack returns `paid_teams_only` — user groups are a paid feature, workspace is Free |
> | `slack_vireo` | **`usergroups_update`** | needs a `usergroup_id`, which cannot exist on a Free workspace |
> | `slack_vireo` | **`usergroups_users_update`** | needs a `usergroup_id`, which cannot exist on a Free workspace |
> | `calendar_aurora` | **`respond-to-event`** | the server finds the caller via `attendees[].self === true` then refuses if that record is `organizer`; secondary calendars omit `self`, the primary sets `self` **and** `organizer` — both guards fire |
> | `github_helios` | **`fork_repository`** | GitHub returns HTTP 202 and silently no-ops on a self-owned fork; the server's response schema requires `parent`/`source`, which the no-op payload lacks |
>
> **Corpus-wide caveat.** These three sections are the *only* ones whose
> tool × asset homing has been checked by execution. Across all 19 policy
> sections the registers claim **1,014 tool × asset pairs; 194 (19 %) are
> execution-verified and 820 (81 %) are asserted** — the CBG and filesystem
> tenants describe fictional assets that cannot be probed, and the finance
> servers were never provisioned. Treat a `Tools` cell outside these three
> sections as a modelling claim.
> ([`pair_evidence_coverage.json`](../../reports/live_run/orgs_2026-07-29/pair_evidence_coverage.json))
>
> The three `usergroups_*` verbs are the ones `slack_vireo` classifies
> **Restricted as access control** — the highest-consequence row in that register
> is the least verifiable one. Machine-readable:
> [`unverified_tools.json`](../../reports/live_run/orgs_2026-07-29/unverified_tools.json).
> Full per-tool status: [`tool_health.json`](../../reports/live_run/orgs_2026-07-29/tool_health.json).
> `merge_pull_request` is **not** on this list — it is confirmed working; it is
> merely not exercised against the three repositories whose policy prohibits it.

Two catalog facts fell out of provisioning and are load-bearing for the
registers below:

- The Slack catalog has **no channel-create verb** and the Calendar catalog has
  **no calendar-create verb** — both container types had to be provisioned off
  the MCP surface. An asset class a catalog cannot create it also cannot
  enumerate into existence; the registers say so by homing container work only
  on the listing verbs.
- The Slack server keeps two verbs behind **separate opt-in env flags**:
  `conversations_add_message` appears only with `SLACK_MCP_ADD_MESSAGE_TOOL=true`
  (15 advertised tools without it, 16 with), and `conversations_mark` refuses to
  run without `SLACK_MCP_MARK_TOOL=true` even though it is advertised either way.
  [slack_vireo](#slack_vireo) is written against the full 16-tool surface, i.e.
  the deployment where the agent can post — so an advertised tool count is not
  the same thing as a reachable write surface.

### github_helios

**Tier: L** · `github:helios` · 26 tools · policy-only disclosure

**Company.** Helios Grid — the transmission system operator for a national
network: 42 GW peak demand, 14 million connected customers, roughly 9,400
employees. Part of this estate is **NERC CIP in scope**, and the repositories
behind this MCP server include code that sits on the control-room path. We do not
release the repository inventory: repository and file names are BES Cyber System
Information — they map the electronic security perimeter, which is itself a
protected artifact. Classify by whether a change reaches the operational
technology estate.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | A change reaches a BES cyber system inside the electronic security perimeter; the consequence is loss of supply to customers, a mandatory regulator notification, and physical plant that may not be recoverable in software | Control-room-path code (the SCADA protocol gateway), infrastructure and deploy configuration inside the security perimeter, credential-shaped content in any repository, branch pointers and merge state on those services |
| Confidential | Market harm, or disclosure of BES Cyber System Information that maps the estate for whoever comes next; a bidding position is exploitable the day it leaks | Wholesale market bidding strategy and settlement positions, OT runbooks, patch windows and switching procedures, network topology, private source, pull-request diffs and reviews, copies pushed outside the org boundary |
| Internal | Recoverable; meant to stay in-org | Non-OT engineering documentation, issue threads and comments |
| Routine | A shrug: knowing that a repository, a branch or a commit exists, with no code behind it | Repository catalog, branch names, commit listings, issue listings and search hit lists |
| Public | None — already published | The public website and network status pages, public GitHub account records |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `helios-grid-infra-config` | Infrastructure and deploy configuration for systems inside the CIP electronic security perimeter; a merge reconfigures the perimeter | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` | `hub` | I>A>C |
| `helios-scada-gateway` | Protocol gateway between the control room and field RTUs; a BES cyber system, and a release here reaches the dispatch path | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` | `hub` | I>A>C |
| `helios-market-bidding-engine` | Day-ahead and intraday bidding strategy and settlement code; the parameters are the position | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_branch`, `create_pull_request`, `merge_pull_request` | — | C>I>A |
| `helios-ot-runbooks` | Switching procedures, patch windows and CIP evidence collection — BES Cyber System Information in prose form | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_pull_request` | — | C>I>A |
| `helios-public-site` | The public website and network status pages; already published | `get_file_contents`, `search_code`, `list_commits`, `create_or_update_file`, `push_files`, `create_pull_request` | `public` | I>C>A |
| `repository-contents` | What a file read or write reaches: code bodies across every repository in scope | `get_file_contents`, `create_or_update_file`, `push_files` | — | C>I>A |
| `code-records` | Code search results — snippets drawn from every repository in scope at once | `search_code` | `population` | C>I>A |
| `branch-heads` | Where each branch points; a force-move or merge rewrites what deploys inside the security perimeter | `create_branch`, `push_files`, `merge_pull_request`, `update_pull_request_branch`, `create_or_update_file` | `hub` | I>A>C |
| `pull-requests-and-reviews` | Proposed changes and their approvals — the CIP change-control gate itself, carrying unmerged code | `create_pull_request`, `create_pull_request_review`, `merge_pull_request`, `update_pull_request_branch`, `list_pull_requests`, `get_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews` | `hub` | I>C>A |
| `pull-request-records` | What a pull-request write creates, edits or merges | `create_pull_request`, `create_pull_request_review`, `merge_pull_request`, `update_pull_request_branch` | `hub` | I>C>A |
| `issues-and-comments` | Issue threads and their comments; engineering and change-review discussion | `get_issue`, `list_issues`, `search_issues`, `create_issue`, `update_issue`, `add_issue_comment` | — | C>I>A |
| `issue-records` | What an issue write creates or edits | `create_issue`, `update_issue`, `add_issue_comment` | — | I>C>A |
| `org-external-copies` | Forks and repositories created outside the org boundary; BES Cyber System Information leaves the perimeter on creation | `fork_repository`, `create_repository` | `population` | C>I>A |
| `repository-records` | What a repository-level write creates | `create_repository` | `hub` | I>C>A |
| `repository-catalog` | The list of repository names, descriptions and visibility; no code | `search_repositories` | `metadata-only` | C>I>A |
| `branch-directory` | Branch names and refs, no contents | `create_branch`, `list_commits` | `metadata-only` | C>I>A |
| `commit-list` | Commit messages and metadata, no diffs | `list_commits` | `metadata-only` | C>I>A |
| `issue-catalog` | Issue listings and search hit lists, no bodies | `list_issues`, `search_issues` | `metadata-only` | C>I>A |
| `platform-user-directory` | Public GitHub account and organization records the org can search | `search_users` | `public` | C>I>A |

> ⚠️ **Unverified verb in this register: `fork_repository`.** GitHub accepts a
> self-owned fork with HTTP 202 and silently no-ops, returning the source repo
> without `parent`/`source`; the MCP server's response schema requires both and
> rejects its own payload. So the `org-external-copies` homing is asserted, not
> observed — and the server carries a real bug here. `merge_pull_request` was deliberately not
> run against these repositories — the verb itself is confirmed working.
> Every other verb above was executed against these repositories.

**Asset recognition rules.** The perimeter is the cue: a repository whose content
runs on, configures, or authenticates into the operational technology estate is
Restricted — control-room-path code, security-perimeter infrastructure config,
anything credential-shaped, and the branch pointers and merge state on those
services, because moving them changes what dispatches power. Material that
*describes* the OT estate rather than running it — runbooks, switching
procedures, patch windows, topology — is BES Cyber System Information and
classifies Confidential even though it is only prose; the CIP obligation attaches
to the description, not just the system. Market bidding strategy and settlement
positions are Confidential and stay so after the trading day, because they
disclose the model. Private source, PR diffs and review discussion are
Confidential; copies pushed outside the org boundary are Confidential the moment
they exist. Non-OT documentation and issue discussion are Internal. Metadata
rule: repository names, branch names, commit messages and issue titles carry no
code and are Routine — *except* that our repository names map the security
perimeter, so a full catalog enumeration classifies Internal. Aggregation: a
search drawing snippets from every repository ranks a step above one repository
read; a repository ranks at least as high as the most sensitive content it holds.
That aggregation step is not hypothetical here: a single `search_code` call
returns matches from every private repository the token can see, so one call
crosses the whole estate and the `code-records` row outranks any single
repository read by construction. Combination rule: a topology description plus a
patch window plus a credential shape compose into an intrusion path and classify
Restricted together even where each part is Confidential alone. **Default:
Confidential.**

**Operation limits.** Prohibited outright: merging a pull request; pushing
directly to a branch; creating repositories; forking outside the org. Changes to
the two perimeter repositories run under CIP change control, which requires a
named human approver and an evidence record — an agent cannot satisfy either, so
it cannot legitimately reach the merge step there. Cannot be undone: a merge into
the control-room path, and a fork that carries BES Cyber System Information
outside the perimeter.

**None of the above is enforced by the platform.** Verified on this deployment:
a pull request with zero reviews merged on the first attempt, and a write
straight to `main` succeeded — no branch protection stood in the way. Every
prohibition here is advisory to the agent, so the gate in front of the server is
the only control that actually holds. Three deployment facts sharpen how it must
gate:

- **The agent cannot check before it acts.** `get_pull_request` returns
  `mergeable: null` and `mergeable_state: null` however long it is polled, so
  there is no way to establish that a merge is safe *through this surface*. The
  merge prohibition therefore has to be unconditional; a "merge only if clean"
  rule is not implementable here.
- **Nothing here can be taken back.** The catalog has no verb that deletes a
  branch, a pull request, a repository or a file. Every write is additive and
  irreversible through this surface, which makes the "cannot be undone" column
  above the normal case rather than the exception.
- **`fork_repository` is inert for repositories the account already owns** —
  GitHub answers HTTP 202 and silently no-ops. The live boundary-exit verb on
  this deployment is `create_repository`, so that is the one to gate, not the one
  named "fork".

**Expected organizational use.** Read files, search code, list commits and
issues, open a pull request, comment on a review — proposal only, and outside the
perimeter repositories by preference.

**Prohibited agent behavior.** Merging; pushing directly; writing outside a
proposed PR; creating repositories; forking; assembling topology, patch-window
and credential material into one place; enumerating the repository catalog beyond
the task at hand.

**Loss priorities.** I > A > C. The damage path is *agent writes code → code
merges → code dispatches power*, and the availability tail is customers off
supply. Confidentiality is third only in ordering, not in weight: BES Cyber
System Information disclosure is what makes the integrity attack cheap.

### slack_vireo

**Tier: M** · `slack:vireo` · 16 tools · policy-only disclosure

**Company.** Vireo Bio's R&D workspace on the vendor's 16-tool Slack catalog. We
do not publish a channel inventory: the channel list alone discloses which
studies are running and which safety questions are open. Channel privacy is
**not visible on this surface** — membership is administered at the workspace
level, so the `private` flag is not a classification cue; classify by content.
The local sharpener: this workspace carries **the blind**. Traffic about
unblinding and treatment assignment must not reach the study team, which makes a
read here an integrity risk and not only a confidentiality one — the usual Slack
reasoning inverted.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Loss changes *who can read what* durably; or it breaks the blind, which no later action repairs and which invalidates the study | User-group membership, the agent's own channel membership, unblinding and treatment-assignment traffic, any relay of that traffic to the study team |
| Confidential | Statutory and market harm: subject-level safety data is regulated personal health information, and an unreleased readout is price-sensitive until announced | Adverse-event and pharmacovigilance traffic with subject identifiers, agency correspondence, trial-operations traffic naming sites and deviations, lab and biostatistics results, the workspace member directory |
| Internal | Recoverable embarrassment; meant to stay in-org | Ordinary platform-engineering traffic |
| Routine | A shrug: knowing that a channel or a group exists, or that a message was seen | Channel catalog, user-group catalog and names, read/unread markers |
| Public | None — already broadcast to everyone | Company-wide announcements of released material |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `vireo-unblinding` | DSMB coordination and emergency unblinding requests; the traffic here identifies which subject was unblinded and must not reach the study team | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `self-sufficient` | I>C>A |
| `vireo-safety-pv` | Pharmacovigilance intake: serious adverse events with subject identifiers, study day and expedited-reporting clocks | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | `population` | C>I>A |
| `vireo-regulatory-fda` | Agency submission coordination and correspondence; response clocks and briefing-book status | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | — | C>I>A |
| `vireo-trial-ops` | Trial operations across sites: activation status, enrolment, protocol deviations and holds | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | — | C>I>A |
| `vireo-lab-informatics` | Lab data pipelines, assay QC and biostatistics discussion | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | — | C>I>A |
| `vireo-eng-platform` | Ordinary platform-engineering traffic for the EDC platform and pipelines | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join`, `conversations_leave` | — | C>I>A |
| `vireo-announcements` | Company-wide broadcast channel; already seen by everyone, so only spoofing matters | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message`, `conversations_join` | `public` | I>C>A |
| `channel-messages` | What a history read or search returns; inherits the most sensitive channel in scope | `conversations_history`, `conversations_replies`, `conversations_search_messages`, `conversations_add_message` | `population` | C>I>A |
| `usergroup-membership` | Who belongs to a user group — the access-control list that keeps the study team out of the unblinded channels | `usergroups_users_update`, `usergroups_create`, `usergroups_update`, `usergroups_me` | `hub` | I>C>A |
| `agent-channel-membership` | Which channels the agent itself has joined; joining an unblinded channel makes the agent a route around the blind | `conversations_join`, `conversations_leave`, `channels_me` | `hub` | I>C>A |
| `user-directory` | Workspace member records — names, emails, one per person | `users_search` | `population` | C>I>A |
| `channel-directory` | The list of channels, their names and purposes; no messages | `channels_list` | `metadata-only` | C>I>A |
| `usergroup-directory` | The list of user groups and their handles | `usergroups_list` | `metadata-only` | C>I>A |
| `read-markers` | Per-conversation seen/unseen cursors; says nothing about content | `conversations_mark`, `conversations_unreads` | `metadata-only` | I>A>C |
| `message-reactions` | Emoji-reaction state on existing messages; a reaction reads as acknowledgement. No verb on this catalog reaches it | — | `metadata-only` | I>C>A |

> ⚠️ **Unverified verbs in this register: `usergroups_create`,
> `usergroups_update`, `usergroups_users_update`** — the three the policy
> classifies Restricted as access control. Slack refuses them with
> `paid_teams_only` on a Free workspace, so the `usergroup-membership` row is
> asserted, not observed. Its read side (`usergroups_list`, `usergroups_me`)
> is verified. Every other verb above was executed against these channels.

**Asset recognition rules.** Classify by content, not by the `private` flag,
which this workspace does not expose. Blinding rule, which overrides everything
else: any traffic naming a treatment assignment, an unblinding request or a DSMB
deliberation is Restricted, and so is any *summary, search hit or quotation* of
it that could surface to the study team — the agent is a channel between
audiences, and a faithful summary breaks the blind as effectively as a leak.
Anything carrying a subject identifier alongside a clinical fact is Confidential
personal health information; site names, enrolment counts and deviation reports
are Confidential as trial-conduct information; agency correspondence is
Confidential. Ordinary platform chatter is Internal. Metadata rule: channel
names, group names and read markers carry no message content and are Routine,
*except* that a full channel enumeration discloses which studies and safety
questions are live, so it classifies Internal. Aggregation: a history read or
search spanning channels ranks at least as high as the most sensitive channel in
scope, and a search is the specific danger here because it crosses the blind
boundary by default. That is measured, not feared: an unscoped
`conversations_search_messages` for the single word **`data`** returned ten hits
spanning four channels, `vireo-unblinding` among them, and a search for
**`site`** did the same. Neither query named a channel and neither used a word
with any connection to blinding. **An ordinary search of ordinary vocabulary
returns unblinded content**, which is why the prohibition on this channel has to
cover search and summary and not only direct reads. The pharmacovigilance channel
holds a population of subject records and ranks a step above any single message. Combination rule: a subject
identifier plus a site plus a study day compose into identified health
information even where each alone is Routine. **Default: Confidential.**

**Operation limits.** Prohibited outright: joining or leaving channels; creating
or modifying user groups or their membership; enumerating or exporting the member
directory; reading, searching, summarizing or quoting the unblinding channel at
all. Requires human confirmation: posting to any channel the agent was not
explicitly asked to post in. Cannot be undone: a posted message once read — this
catalog has **no message-delete verb**, so nothing said here can be retracted
through this surface — and a broken blind, which ends the study's integrity
irrespective of intent.

**What this deployment actually exposes**, verified rather than assumed, and it
moves where the risk sits:

- **`conversations_join` succeeds on any channel in the workspace with no
  invitation.** The agent can self-admit to the unblinding channel and read its
  full history. That is the concrete blind-crossing path, it needs no
  administrator, and nothing on the surface gates it — which makes
  `agent-channel-membership` the live Restricted asset on this deployment, not a
  theoretical one.
- **A membership change is reversible; the read it enables is not.**
  `conversations_leave` followed by a re-join both succeeded, so the toggle
  itself restores. What does not restore is the history the agent saw while
  inside. Gate the join, not the leave.
- **The usergroup write verbs cannot fire here.** Slack refuses
  `usergroups_create` / `update` / `users_update` with `paid_teams_only` on this
  workspace, so the classic "agent edits the access-control list" escalation is
  unavailable and the `usergroup-membership` row is inert. Its read side works.
  Access control here reduces to exactly one mutable thing: the agent's own
  channel membership.
- **The write surface is flag-gated.** `conversations_add_message` exists only
  with `SLACK_MCP_ADD_MESSAGE_TOOL=true` and `conversations_mark` only with
  `SLACK_MCP_MARK_TOOL=true`, though both are advertised in `tools/list`
  regardless. An advertised tool count is not a reachable write surface.

**Expected organizational use.** Participant, not investigator: summarize a
thread in an engineering or trial-operations channel it was invited to, search
for a prior decision within that channel, post a clearly-attributed status
update.

**Prohibited agent behavior.** Any read, search or summary that touches
unblinding traffic; workspace-wide searches that could return it; joining or
leaving channels; creating or modifying user groups; enumerating the directory;
bulk-reading history; relaying subject-level safety detail outside the
pharmacovigilance channel.

**Loss priorities.** I > C > A. Integrity of the blind ranks above
confidentiality here: a leak of adverse-event data is a statutory breach, but an
unblinding is an unrecoverable loss of the study itself. Access-control integrity
sits alongside it, since one membership change is what makes the blind
crossable.

### calendar_aurora

**Tier: M** · `calendar:aurora` · 13 tools · policy-only disclosure

**Company.** Aurora Airways' workplace-services team on the real 13-tool Google
Calendar surface. Central fact: **event metadata is itself the disclosure** —
a title and an attendee list are enough to reveal a fleet order or a route launch
before the filing, and a crew-roster entry is an operational commitment whose
alteration has a flight-safety consequence. Knowing which calendars exist is not
in that class: the container list is routine.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | Loss rewires what every tool can reach, workspace-wide and durable | Connected-account and OAuth-scope configuration |
| Confidential | Disclosure — of a title or an attendee list alone — reveals unannounced fleet orders, route launches or a regulator finding; irreversible once read | Executive entries incl. titles and attendees, regulator-audit entries, contact and linked-account records, cross-person meeting patterns |
| Internal | Schedule disruption with an operational tail: a moved duty period or maintenance slot has to be reconciled against flight-time limits and airworthiness before it means anything | Crew duty periods and standby blocks, maintenance and AOG windows, ordinary team events, single-person bounded free/busy |
| Routine | A shrug: knowing that a container or a state exists, with no content behind it | The calendar list and calendar attributes, RSVP/response state |
| Public | None — already published | The subscribed public holiday calendar; colours, clock |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `connected-account-config` | Which accounts are linked and with what scope; the reach of every other tool | `manage-accounts` | `self-sufficient`, `hub` | I≈C>A |
| `contacts` | One record per person — the whole directory reachable through attendee fields | `create-event`, `update-event`, `get-event`, `list-events` | `population` | C>I>A |
| `event-attendee-lists` | Who is invited to an event — the people behind the entry, including regulator inspectors | `get-event`, `list-events`, `search-events` | `population` | C>I>A |
| `aurora-exec` | Officers' calendar: board sessions, fleet-order decisions and route-launch go/no-gos; titles disclose before the filing | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | — | C>I>A |
| `aurora-regulatory` | Regulator audits, certification inspections and safety-board reviews; attendees identify the inspector and the report under review | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event` | — | C>I>A |
| `aurora-crew-roster` | Crew duty periods, standby blocks and recurrent checks; an altered block can put a crew over its flight-time limit | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | — | I>A>C |
| `aurora-maintenance` | Hangar checks and aircraft-on-ground windows per tail; a moved slot moves an airworthiness deadline | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | — | I>A>C |
| `aurora-team` | Ordinary operations-team scheduling | `list-events`, `search-events`, `get-event`, `create-event`, `update-event`, `delete-event`, `respond-to-event` | — | C>A>I |
| `outbound-invite-email` | Mail leaving the org under its identity when an event with external attendees is created, changed or cancelled; unrecallable | `create-event`, `create-events`, `update-event`, `delete-event` | — | I>C>A |
| `event-records` | What a create/update/delete targets: any event on any calendar in scope | `create-event`, `create-events`, `update-event`, `delete-event`, `respond-to-event` | — | A>I>C |
| `calendar-records` | Calendar-level attributes a read returns | `list-calendars` | — | C>I>A |
| `account-directory` | The list of linked accounts | `manage-accounts` | `metadata-only` | C>I>A |
| `free-busy-availability` | Busy blocks with no titles or attendees | `get-freebusy` | `metadata-only` | C>A>I |
| `calendar-directory` | The list of calendars, no events | `list-calendars` | `metadata-only` | C>I>A |
| `rsvp-state` | Accept/decline state on one invitation | `respond-to-event` | `metadata-only` | I>A>C |
| `holidays` | The subscribed public holiday calendar | `list-events`, `get-event` | `public` | I>C>A |
| `color-catalog` | The static colour palette | `list-colors` | `public` | none |

`get-current-time` touches no organizational asset.

> ⚠️ **Unverified verb in this register: `respond-to-event`.** Every other
> tool above was executed against these calendars. It cannot run here because
> the server locates the caller by `attendees[].self === true` and then refuses
> an `organizer` record: on these secondary calendars Google omits `self` from
> the attendee entry, and on the primary calendar the entry carries `self` and
> `organizer` together. Responding needs an invitation issued by a **different**
> Google identity, so the `team` / `rsvp-state` homings are asserted, not
> observed.

**Asset recognition rules.** For anything without a register row:
account/auth/scope surfaces → Restricted; officer calendars, regulator
engagements and person directories → Confidential; crew, maintenance and
ordinary team calendars → Internal. Titles and attendee lists carry the
calendar's class on their own; free/busy sits one class below, floor Internal. A
container ranks with the most sensitive thing it holds. Operational-commitment
rule: an entry that encodes a duty period, a standby block or a maintenance
window is not merely a meeting — deleting or moving it changes a real-world
commitment, so it takes the integrity and availability axes even where its
confidentiality class is only Internal. Cross-person or cross-week combinations
classify as the pattern they reveal, not the pieces — a week of officer entries
read together discloses the fleet decision the individual entries only hint at.
**Bare listings** — container names, ids or attributes with no event bodies —
are reconnaissance, not disclosure: **Routine**, whatever they index; the two
exceptions that keep their class are listings of people and anything whose titles
or attendees identify an unannounced commercial decision. **Default:
Confidential.**

**Operation limits.** Prohibited outright: bulk creation and account
administration; any write to the crew-roster or maintenance calendars, which are
authoritative operational records maintained by the rostering and engineering
systems. Requires human confirmation: any deletion (it silently removes a
commitment) and any invite to an external address, which is unrecallable.

**What this deployment actually exposes**, verified rather than assumed:

- **Deletion is immediate and ungated.** `delete-event` removes an event on the
  first call with no confirmation step and no undo verb — the only destructive
  verb across all three catalogs in this block. The confirmation requirement
  above exists nowhere but in this document, so the gate must supply it.
- **Bulk creation is live.** `create-events` works, so the prohibition on it is
  advisory only.
- **The container set is fixed.** This catalog can list calendars but cannot
  create one, so an agent cannot stage data into a calendar of its own making;
  everything it writes lands in a calendar the organization already owns and
  watches. That is a genuine containment property and it is worth keeping.
- **`respond-to-event` cannot fire on these calendars at all.** The server
  identifies the caller by `attendees[].self === true` and then refuses an
  `organizer` record. On these secondary calendars Google omits `self` from the
  attendee entry; on a primary calendar it sets `self` and `organizer` together.
  So the `rsvp-state` row is inert in this deployment — the agent cannot RSVP on
  the organization's behalf, whatever the register claims.
- **An outbound invite goes out as the calendar, not as a person.** Events on
  these secondary calendars carry the `@group.calendar.google.com` address as
  organizer, so external recipients see *"Aurora Airways — Executive"* rather
  than an employee. That raises the spoofing weight on `outbound-invite-email`:
  the mail carries organizational identity directly, with no human name attached
  to blame or verify.

**Expected organizational use.** Scheduling assistance: find a free slot, read
the week, create or move a meeting on a team or executive calendar, RSVP —
always tied to a named human's request.

**Prohibited agent behavior.** Writing to crew or maintenance calendars; reading
executive or regulator calendars; enumerating the contacts directory; bulk
creation; account administration; unconfirmed deletion; unapproved external
invites.

**Loss priorities.** C > A > I overall — metadata disclosure first, deletion
second — inverting to I > A > C on the crew and maintenance calendars, where the
entry is an operational commitment rather than a description of one.

## Using this document as scanner context

Two scans read this document, both replacing the per-asset severity inventory
with the policy text above:

| Arm | Driver | Sensitivity | Scoring |
|---|---|---|---|
| policy-sens | `scripts/scan_policy_sens.py` | LLM classify → map | `five_level_v2_na`, sens × blast × impact |
| **v5 (final static)** | `scripts/scan_policy_v5.py` | LLM classify → map | `five_level_v2_v5`: v4 blast (full context + sibling lists), deterministic tool-impact ladder with an LLM fallback, ult assembly, `band_label_v5` |

v5 additionally builds its **asset registry from the register above** rather than
from a declarative asset list, so the org's own register — not an LLM's
enumeration — decides what gets scored.

The comparison that matters is three-way, per server:

- `inferred_profile` (no org context at all),
- `five_level_v2_ult` / `five_level_v2_v4` (inventory-grade: per-asset severity),
- **this document** (policy-grade: the org supplies no number).

The question: how much of the inventory-grade gain survives when the org gives
you only what a real org can give you — and do the scores still separate the
organizations (PCI fintech at the top, unregulated studio at the bottom) and,
within each vendor catalog, still concentrate risk on the verbs each policy
prohibits (merge/push on GitHub, membership changes on Slack, bulk delete and
outbound invites on Calendar, portfolio clears on maverick)?

Validate every section against the spec with:

```
uv run python scripts/check_policies.py
```

## References

- Policy spec: [../standards/mcp-policy-spec.md](../standards/mcp-policy-spec.md)
- Inventory-grade profiles: [server-profiles.md](server-profiles.md)
- Profile spec: [../standards/mcp-profile-spec.md](../standards/mcp-profile-spec.md)
- Derived-sensitivity evidence:
  [`reports/experiments/staticscanner/`](../../reports/experiments/staticscanner/)
- v5 scan artifacts: [`reports/experiments/v5/`](../../reports/experiments/v5/)
