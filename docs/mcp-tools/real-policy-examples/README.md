# Real-world policy examples

Real, publicly published data-classification policies, collected as the outside-world
counterpart to the synthetic registers in [`../server-policies.md`](../server-policies.md)
and the v7 framework arms. They exist to answer one question: **when a real organization
publishes a policy, how concrete are the assets in it?**

All three documents come from **one organization** — The University of Iowa — and all three
describe the same subject: how institutional data is classified and where it is allowed to
live. They differ only in how concretely they name the things being protected. That makes
them a controlled ladder rather than three unrelated samples.

## The ladder

| Rung | Document | Assets as published | Register shape |
|---|---|---|---|
| **bad** | [IT-19 Institutional Data Policy](bad-uiowa-it19-institutional-data-policy/) | Entirely abstract. Four classes, generic data examples (`Social Security Number`, `Student transcripts`). **Not one system, owner, or operation is named.** | 4 rows: `Class · Description · Data examples` |
| **medium** | [Data classification guidelines](medium-uiowa-data-classification-guidelines/) | Mostly abstract, but the reasoning is shown and **one real system is named** (`InfoHawk+`). The rest are semi-concrete ("faculty grade books", "a professor's blog hosted on a departmental server"). | A CIA derivation matrix + 5 worked classifications |
| **good** | [Data Classification Guide to IT Services](good-uiowa-data-classification-guide-to-it-services/) | **41 real named services** you can log into — `REDCap`, `Qualtrics`, `Box`, `HPC Systems`, `ICON`, `Files@Iowa`, `Iowa Health Data Resource (IHDR) Data Enclave`, `XNAT`, `ChatGPT Edu`, `Microsoft 365 Copilot`. | 41 × 4 grid; every cell an explicit authorization |

### What "bad" actually looks like

IT-19 is a real, board-approved policy of record, and its entire asset model is this:

> | Classification Level | Description | Institutional Data Examples |
> | Critical | Inappropriate handling or disclosure of this data could cause severe harm… | Patient health… Social Security Number… ITAR data |

Everything else in the document is governance — Data Trustee, Data Steward, Data Custodian,
backup schedules. A scanner reading only this cannot tell you which tool touches what,
because nothing in it is a thing.

### What "medium" adds

It stops asserting classes and starts *deriving* them, one CIA axis at a time:

> InfoHawk+, the end-user interface to search the online library catalog has an optional
> (low) need for confidentiality since the catalog is public… The need for integrity is
> recommended (medium risk) because we do not want records to be changed… the online
> library catalog is classified as University-Internal data.

That is the same move as the ISO arm's A.5.12 four-criteria block: publish the *procedure*
so the class can be re-derived, not just looked up.

### What "good" adds

An actual grid, of which these are four rows:

| Service | Public | University/Internal | Restricted | Critical |
|---|---|---|---|---|
| Box | permitted | not permitted | not permitted | not permitted |
| REDCap | permitted | permitted | permitted | consultation required |
| Iowa Health Data Resource (IHDR) Data Enclave | consultation required | consultation required | permitted | consultation required |
| DeepSeek | not permitted | not permitted | not permitted | not permitted |

Each cell is a published authorization decision about a named asset. The IHDR row is the
interesting one: it is *more* restricted for `Public` data than for `Restricted` data —
a real organization encoding "this enclave is for regulated health data, don't park your
public files here." No purely severity-driven model produces that shape.

## What this validates in our synthetic policies

- **No sensitivity numbers is realistic.** Iowa publishes classes and permissions and never
  publishes a numeric severity. `assert_no_sensitivity_numbers` is not a handicap we imposed
  on the scanner — it is what real disclosure looks like.
- **Reachable ≠ authorized is real.** The whole "good" document exists *because* every one of
  those 41 services is technically reachable by any staff member. The grid is the
  organizational control with no technical backstop — exactly the framing in the ISO arm's
  A.8.3 access-restriction block.
- **The authoritative document is the least concrete one.** IT-19 is the policy of record;
  the concrete inventory is an IT-services web page that is not policy at all. Concreteness
  and authority run in opposite directions, which is the disclosure asymmetry our policy
  arms are built around.

## What it challenges

- **No owner column anywhere.** ISO A.5.9 requires a named owner per asset. Iowa's most
  concrete document has none — it names services, not accountable people. Our ISO arm's
  required `Owner` column is more disclosure than this real certified-adjacent org gives.
- **Service granularity, not tool granularity.** Iowa's axis is `service × data class`. Ours
  is `tool × asset`, one level finer. No rung of this real ladder reaches per-operation
  authorization, so the `Authorized operations` column has no direct real-world analogue
  here — it remains a synthetic affordance.
- **Assets are containers, not contents.** Iowa's register lists places data can sit. Ours
  lists the data itself (`payroll-records`, `security-keys`). Both are legitimate readings
  of "asset"; they are not interchangeable inputs to a blast-radius calculation.

## Provenance and refresh

Each folder holds the raw `source.html` as downloaded, a Markdown text extraction, and a
`provenance.json` with the URL, retrieval timestamp and SHA-256 of the exact bytes converted.
The permission grid is stored as Font Awesome glyphs with no text, so a naive text extraction
silently loses all 164 verdicts; the fetcher maps the icon classes back to the page's own
legend wording.

```bash
uv run python scripts/fetch_real_policy_examples.py            # re-download and re-extract
uv run python scripts/fetch_real_policy_examples.py --offline  # re-extract from cached html
```

These are public web pages, retained here as reference examples for research. Copyright
remains with The University of Iowa.

## Sources

- [Institutional Data Policy (IT-19)](https://itsecurity.uiowa.edu/policies-standards-guidelines/institutional-data-policy)
- [Data classification guidelines](https://itsecurity.uiowa.edu/it-policies/it-guidelines/data-classification-guidelines)
- [Data Classification Guide to IT Services](https://its.uiowa.edu/services/protecting-sensitive-data/data-classification-guide-it-services)
