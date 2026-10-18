# Real-world policy examples

Real, publicly published data-classification policies, collected as the outside-world
counterpart to the synthetic registers in [`../server-policies.md`](../server-policies.md)
and the v7 framework arms. Two independent sets live here, answering two different questions.

The **ladder** (below) asks: when a real organization publishes a policy, how concrete are
the assets in it? The **framework set** asks a narrower question: when a real org discloses
that it follows ISO/NIST/CIS, what does the resulting document actually cite and say?

## The ladder

All three ladder documents come from **one organization** — The University of Iowa — and all
three describe the same subject: how institutional data is classified and where it is allowed
to live. They differ only in how concretely they name the things being protected. That makes
them a controlled ladder rather than three unrelated samples.

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

## The framework set

Three documents from **three different organizations**, each publicly citing one of the
frameworks the v7 arms ([`../server-policies-iso.md`](../server-policies-iso.md),
[`-nist.md`](../server-policies-nist.md), [`-cis.md`](../server-policies-cis.md)) write in
natively. Unlike the ladder, these aren't a controlled comparison — they're independent
evidence for the same question the ladder's "What it challenges" section raises: does a real
disclosure under this framework actually reach the concreteness our synthetic arm assumes?

| Framework | Document | What it cites | Register shape |
|---|---|---|---|
| **iso** | [Information Classification Scheme — Leeds Beckett University](iso-leedsbeckett-information-classification-scheme/) | "BS ISO/IEC 27002:2013 Section 8.2" by name, and controls A.8.1.1/A.8.2.1/A.8.2.2/A.8.2.3 — the 2013-numbering predecessors of A.5.9/A.5.12/A.8.3 | 3 classes (Public/Internal/Confidential) × a worked matrix of concrete data examples (staff names, passwords, server-room details, exam papers) |
| **nist** | [Data Classification and System Security Categorization — University of Colorado Denver](nist-ucdenver-data-classification-and-system-security-categorization/) | "FIPS 199" and "NIST 800-60" by name, the {confidentiality, integrity, availability} security-category triple, and the high-water-mark rule | 3 classes (Highly Confidential/Confidential/Public) for data elements, plus a separate FIPS 199 information-type categorization worked end-to-end for one type (Funds Control) straight from the NIST 800-60 catalog |
| **cis** | [Statewide Policy for Data Classification — State of Nevada](cis-nevada-statewide-data-classification-policy/) | "CIS Controls v8" as a named federal reference alongside NIST SP 800-53/800-60, directs its own technical-control policies to be built on "NIST and CIS Control frameworks," and defines CIS as the Center for Internet Security in its glossary | 4 tiers (Public/Sensitive/Confidential/Restricted) with named regulatory sub-categories (CJIS, FTI, CUI, PCI) rather than a per-system register |

### What each one actually confirms

The ISO document is the strongest hit for a *named-control* citation: it walks the reader
through all four A.8.1.1→A.8.2.3 steps in one sentence, exactly the "publish the procedure"
move the ladder's "medium" rung and the ISO arm's A.5.12 block both make. The NIST document is
the strongest hit for a *worked example*: it doesn't just name FIPS 199 and SP 800-60, it
reproduces one of SP 800-60's own information-type tables (Financial Management → Funds
Control) and carries it through to a high-water-mark verdict, which is the same move the NIST
arm's information-type register is built around. The CIS document is the weakest of the three
on citation depth — CIS Controls v8 appears as one named reference among several (NIST SP
800-53, SP 800-60, the Cybersecurity Framework) rather than the sole framework the classification
scheme derives from — but it is real, current (effective 2026-02-10), and its four-tier,
sub-category structure (CJIS/FTI/CUI/PCI as named carve-outs) is closer to a live-organization
register than either of the other two.

### What none of the three reach

None of the three is a per-tool or per-system register the way the synthetic v7 arms are.
Leeds Beckett's matrix is `class × data-example`, Colorado's is `information type × CIA impact`,
and Nevada's is `tier × sub-category`. All three name *kinds* of data, not *systems* that hold
it — the same gap the ladder's "good" rung (Iowa) closes with 41 named services, and that no
document in the framework set closes on its own. Reading the framework set and the ladder
together is the point: the ladder shows what concreteness a real disclosure *can* reach: the
framework set shows what a real disclosure *actually says* when it names ISO, NIST, or CIS by
name — and it is closer to "bad"/"medium" than to "good."

## Provenance and refresh

Each folder holds the raw downloaded file (`source.html` for the ladder, `source.pdf` for the
framework set), a Markdown text extraction, and a `provenance.json` with the URL, retrieval
timestamp and SHA-256 of the exact bytes converted. The Iowa permission grid is stored as Font
Awesome glyphs with no text, so a naive text extraction silently loses all 164 verdicts; the
fetcher maps the icon classes back to the page's own legend wording. The framework-set PDFs are
extracted page-by-page with `pypdf`.

```bash
uv run python scripts/fetch_real_policy_examples.py            # re-download and re-extract all six
uv run python scripts/fetch_real_policy_examples.py --offline  # re-extract from cached source files
```

These are public documents, retained here as reference examples for research. Copyright
remains with each publisher.

## Sources

Ladder (The University of Iowa):

- [Institutional Data Policy (IT-19)](https://itsecurity.uiowa.edu/policies-standards-guidelines/institutional-data-policy)
- [Data classification guidelines](https://itsecurity.uiowa.edu/it-policies/it-guidelines/data-classification-guidelines)
- [Data Classification Guide to IT Services](https://its.uiowa.edu/services/protecting-sensitive-data/data-classification-guide-it-services)

Framework set:

- [Information Classification Scheme — Leeds Beckett University](https://www.leedsbeckett.ac.uk/-/media/files/policies/information-governance/upig_information_classification.pdf)
- [Process for Data Classification and System Security Categorization — University of Colorado Denver](https://clas.ucdenver.edu/it-support/sites/default/files/attached-files/cudataclassification.pdf)
- [Statewide Policy for Data Classification — State of Nevada Governor's Technology Office](https://www.it.nv.gov/siteassets/itnew.nv.gov/content/governance/statewide-policy-for-data-classifications---signed_020220206-12.pdf)
