# Independent Scoring -- Filesystem MCP

## Approach

This file is an independent, agent-side score over the same `(Directory x
Filetype x Tool)` cube the user has hand-scored. Scoring is static: it
captures the inherent risk of an agent invoking a tool on an asset, before
any runtime context (request content, caller identity, frequency) is
applied. I did not read the user's score columns; rankings here come only
from the taxonomy labels in the prompt plus the literature baselines.

The rubric is grounded in NIST SP 800-30 Rev. 1 (qualitative risk =
likelihood x impact), FIPS 199 / NIST SP 800-60 Vol. 1+2 (CIA-tuple
categorisation with high-water-mark aggregation), NIST SP 800-83 plus
MITRE ATT&CK T1059/T1204 (executable filetype risk), CVSS v3.1/v4.0 and
OWASP Risk Rating (the four-band severity scale), and the MCP-native
scoring work in MCP-in-SoS (arXiv 2603.10194), mcp-sec-audit
(arXiv 2603.21641), OWASP AIVSS v0.5, and the Repello AI Blast Radius
model. Tool risk is judged on blast radius (read vs write vs structural
change), filetype risk on execute-on-open / parseability potential and
typical sensitivity carrier, and directory risk on FIPS-199 impact tier
of the information class.

## Scoring rubric

| Band | Code | Meaning |
|---|---|---|
| Critical | 4 | Severe / catastrophic; crown-jewel exfiltration; irreversible damage |
| High | 3 | Significant data exposure; hard-to-reverse modification; scriptable execution surface |
| Medium | 2 | Noticeable but reversible; moderate data exposure |
| Low | 1 | Limited adverse effect; public surface; easily reversed |
| N/A | 0 | Tool genuinely does not apply to target |

---

## 1. Tool Ranking

### Empty structure (user's scoring goes here)

| Rank | Tool | Risk | Reasoning |
|---|---|---|---|
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
|---|---|---|---|
| 1 | write_file | Critical | Creates arbitrary new content -- can plant executables, overwrite policy files, and is the canonical persistence primitive (ATT&CK T1105 / T1546). |
| 2 | edit_file | Critical | In-place modification of existing content; tampers with source, config, or evidence with no overwrite-protection signal. |
| 3 | move_file | High | Relocates / renames files, breaking integrity assumptions and enabling staging-for-exfil or evidence reorganisation; reversible only if path history is preserved. |
| 4 | read_file | High | Direct confidentiality breach on whatever asset class is targeted -- the canonical exfiltration primitive for crown-jewel directories. |
| 5 | search | High | Content / filename search across the tree returns matching snippets; effectively read_file at scale with discovery built in. |
| 6 | create_dir | Medium | Structural change, but no data is read or modified; primary risk is enabling later writes and noisy state changes. |
| 7 | list_dir | Medium | Discloses names and structure (metadata leak); enables targeted follow-up reads but no content is exposed directly. |
| 8 | get_file_info | Low | Metadata-only (size, mtime, mode); useful for reconnaissance but limited standalone impact. |

---

## 2. Filetype Ranking

### Empty structure (user's scoring goes here)

| Rank | Filetype | Risk | Reasoning |
|---|---|---|---|
| 1 | (blank) | (blank) | (blank) |
| 2 | (blank) | (blank) | (blank) |
| 3 | (blank) | (blank) | (blank) |
| 4 | (blank) | (blank) | (blank) |
| 5 | (blank) | (blank) | (blank) |
| 6 | (blank) | (blank) | (blank) |
| 7 | (blank) | (blank) | (blank) |
| 8 | (blank) | (blank) | (blank) |
| 9 | (blank) | (blank) | (blank) |
| 10 | (blank) | (blank) | (blank) |
| 11 | (blank) | (blank) | (blank) |
| 12 | (blank) | (blank) | (blank) |

### Agent's independent scoring

| Rank | Filetype | Risk | Reasoning |
|---|---|---|---|
| 1 | .sys | Critical | Kernel / driver-level artefact; any modification can compromise the host (NIST SP 800-83 highest-risk class). |
| 2 | .exe | Critical | Directly executable binary; ATT&CK T1204 user-execution surface for arbitrary code. |
| 3 | .bash | Critical | Shell script -- ATT&CK T1059.004; trivially runnable, often privileged, and easily tampered with. |
| 4 | .sql | High | Database script / dump; carries schema, queries, often credentials, and is the path to data-tier compromise. |
| 5 | .code | High | Source code (production logic); supply-chain risk if modified, IP loss if read. |
| 6 | .xlsx | High | Macro-capable Office format; commonly carries financials and PII; macro-enabled variants execute on open. |
| 7 | .docx | High | Macro-capable Office format; carries contracts, HR docs; ATT&CK T1204.002. |
| 8 | .csv | Medium | Plain-text tabular; common PII / exports carrier, but no execution surface. |
| 9 | .pdf | Medium | Often sensitive content (financials, contracts); historically a malware vector via embedded JS, but typically passive. |
| 10 | .md | Low | Plain-text notes; mostly low-sensitivity documentation. |
| 11 | .txt | Low | Plain-text; passive; sensitivity depends entirely on directory context. |
| 12 | .png | Low | Image; no execution surface; rare confidentiality concern unless screenshots leak data. |

---

## 3. Directory Ranking

### Empty structure (user's scoring goes here)

| Rank | Directory | Risk | Reasoning |
|---|---|---|---|
| 1 | (blank) | (blank) | (blank) |
| 2 | (blank) | (blank) | (blank) |
| 3 | (blank) | (blank) | (blank) |
| 4 | (blank) | (blank) | (blank) |
| 5 | (blank) | (blank) | (blank) |
| 6 | (blank) | (blank) | (blank) |
| 7 | (blank) | (blank) | (blank) |
| 8 | (blank) | (blank) | (blank) |

### Agent's independent scoring

| Rank | Directory | Risk | Reasoning |
|---|---|---|---|
| 1 | Sensitive Docs | Critical | Financials, contracts, PII -- SP 800-60 highest-impact information types and the canonical crown jewel. |
| 2 | Security Evidence | Critical | Audit logs and IR artefacts; tampering destroys integrity of the security function itself (ATT&CK T1070). |
| 3 | Source Code | High | Production codebase; IP loss on read, supply-chain compromise on write. |
| 4 | Eval Data | High | Model / test evaluation sets; tampering corrupts assurance signals and can mask regressions. |
| 5 | QA Test Plans | Medium | Test artefacts and expected behaviour; tampering can mask defects, but isolated from production. |
| 6 | Shared Proj Dir | Medium | Cross-team working folder; mixed sensitivity, ambient trust, but typically not crown-jewel. |
| 7 | Onboarding | Medium | HR onboarding content; some PII exposure, otherwise standardised material. |
| 8 | Public | Low | Publicly distributable artefacts; minimal confidentiality impact, integrity matters only for reputation. |

---

## 4. Cube cells -- illustrative subset

Twelve representative `(Directory x Filetype x Tool)` cells. The picks span
the matrix: high-risk corners (Sensitive Docs writes / Security Evidence
edits), medium combinations, and the lowest tail (Public reads).

### Empty structure (user's scoring goes here)

| # | Directory | Filetype | Tool | Risk | Reasoning |
|---|---|---|---|---|---|
| 1 | Sensitive Docs | .xlsx | read_file | (blank) | (blank) |
| 2 | Sensitive Docs | .xlsx | write_file | (blank) | (blank) |
| 3 | Sensitive Docs | .pdf | read_file | (blank) | (blank) |
| 4 | Security Evidence | .csv | edit_file | (blank) | (blank) |
| 5 | Security Evidence | .txt | read_file | (blank) | (blank) |
| 6 | Source Code | .code | edit_file | (blank) | (blank) |
| 7 | Source Code | .bash | write_file | (blank) | (blank) |
| 8 | Source Code | .sql | read_file | (blank) | (blank) |
| 9 | Shared Proj Dir | .docx | edit_file | (blank) | (blank) |
| 10 | Eval Data | .csv | edit_file | (blank) | (blank) |
| 11 | Onboarding | .pdf | read_file | (blank) | (blank) |
| 12 | Public | .md | read_file | (blank) | (blank) |
| 13 | Public | .png | list_dir | (blank) | (blank) |
| 14 | QA Test Plans | .md | get_file_info | (blank) | (blank) |
| 15 | Sensitive Docs | .sys | write_file | (blank) | (blank) |

### Agent's independent scoring

| # | Directory | Filetype | Tool | Risk | Reasoning |
|---|---|---|---|---|---|
| 1 | Sensitive Docs | .xlsx | read_file | Critical | Direct exfil of financial / PII workbook; canonical confidentiality breach. |
| 2 | Sensitive Docs | .xlsx | write_file | Critical | Plants a possibly macro-enabled workbook in the crown-jewel directory; later open could execute. |
| 3 | Sensitive Docs | .pdf | read_file | Critical | High-sensitivity asset, passive carrier; full content exfil with one call. |
| 4 | Security Evidence | .csv | edit_file | Critical | Audit-log tampering -- ATT&CK T1070.002; destroys the integrity of the security function itself. |
| 5 | Security Evidence | .txt | read_file | High | Discloses IR notes / findings, enabling adversary situational awareness, but reversible (information disclosure only). |
| 6 | Source Code | .code | edit_file | Critical | Direct supply-chain modification; persists into builds and downstream systems. |
| 7 | Source Code | .bash | write_file | Critical | Drops a new shell script in the source tree -- combines write primitive with executable filetype in a trusted location. |
| 8 | Source Code | .sql | read_file | High | DB schema / queries / possible credentials disclosed; sets up data-tier follow-on. |
| 9 | Shared Proj Dir | .docx | edit_file | High | Macro-capable document modified in an ambient-trust folder; integrity loss on shared collateral. |
| 10 | Eval Data | .csv | edit_file | High | Tampering biases evaluation; masks regressions in models / tests with downstream assurance impact. |
| 11 | Onboarding | .pdf | read_file | Medium | HR material, partially sensitive (PII at edges) but largely standardised; low novelty exposure. |
| 12 | Public | .md | read_file | Low | Public-tier content; confidentiality impact is minimal by definition. |
| 13 | Public | .png | list_dir | Low | Metadata listing on a public folder; both axes are low-sensitivity. |
| 14 | QA Test Plans | .md | get_file_info | Low | Metadata-only read on a passive notes file in a medium-tier folder. |
| 15 | Sensitive Docs | .sys | write_file | Critical | Kernel-level filetype, write primitive, crown-jewel directory -- worst-corner cell of the cube. |

---

## Notes

A few things were genuinely hard or worth flagging:

- **search vs read_file.** I rated `search` only one notch below `read_file`
  because in practice content search returns snippets and is the
  discovery-plus-read primitive; from a blast-radius point of view it is
  arguably worse than a single targeted read. I kept it at High rather
  than Critical because absent a target it does not by itself transfer a
  full file.
- **move_file ranking.** Conventional wisdom puts move below pure reads
  because it does not exfiltrate, but on integrity (FIPS 199 I-axis) it
  can be devastating for evidence -- moving a log out of place is
  equivalent to deleting it from a SIEM ingestion path. I ranked it
  above `read_file`, which is debatable.
- **Security Evidence vs Sensitive Docs.** I judged Security Evidence
  equally Critical because integrity loss there compromises the entire
  detection / response capability (ATT&CK T1070). A FIPS-199 high-water
  read would put both at the same tier, but most spreadsheets I have
  seen rank Sensitive Docs strictly above. This is a reasonable place to
  disagree.
- **.pdf placement.** Treated as Medium overall. Some sources rank PDFs as
  High because of embedded-JS / form-action history, but in a typical
  enterprise filesystem they are read-only carriers; their risk is
  almost entirely a function of the directory they sit in. The cell
  rating reflects this -- `.pdf` in Sensitive Docs is Critical, `.pdf`
  in Public is Low.
- **.sql.** I deliberately put it above `.code` because a `.sql` dump
  often includes connection strings and live data, whereas `.code` is
  source text without bound credentials. Many lists swap these two.
- **N/A use.** I did not use the N/A band in the illustrative cells
  because every cell in the sample is a meaningful intersection. N/A is
  most natural for `.png` x `edit_file` in `Source Code` and similar
  type-mismatched combinations, but the sample skipped those by design.
- **Single-cell ambiguity.** `Shared Proj Dir` x `.docx` x `edit_file`
  is the most ambiguous cell in the sample -- the directory tier is
  medium, the filetype tier is high (macro-capable), and the tool tier
  is critical. I resolved to High by the high-water-mark rule applied to
  the lower of the asset axes, but this is the kind of cell where a
  policy decision matters more than any single ranking.
