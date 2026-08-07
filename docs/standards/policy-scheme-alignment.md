# What to ask an organization for, and which standard it already has it under

The scanner needs one document per server. The risk is that our format
(`docs/standards/mcp-policy-spec.md`) is ours — an organization has no reason to
produce it, and if the shape only ever comes from us the method does not
transfer.

So: three schemes that organizations genuinely maintain, what each one already
gives us, and the exact gap we would have to ask them to fill. Nothing here is
aspirational — every field listed as "you already have this" is a documented
requirement of the named standard.

## The short version

| Our register field | ISO 27001:2022 | NIST (FIPS 199 / SP 800-60 / CSF 2.0) | CIS Controls v8.1 |
|---|---|---|---|
| Classification table (class · adverse impact · examples) | **A.5.12** | **FIPS 199 + SP 800-60** | **3.7** |
| Asset + Description | **A.5.9** | **CSF ID.AM** | **3.2** |
| CIA / loss priorities | A.5.12 (requires C, I and A be considered) | **FIPS 199** — categorization *is* a {C,I,A} triple | partial |
| Expected use / prohibited behavior | **A.5.10** | — | 3.1 |
| Recognition rules | A.5.13 (labelling) | SP 800-60 information types | 3.7 |
| **Tools — which tool reaches which asset** | ✗ | ✗ | **3.8 (closest)** |
| Flags (`hub`, `population`, `self-sufficient`) | ✗ | ✗ | ✗ |

**Five of seven fields come free from any of the three.** Two do not, and one of
those two is load-bearing — see "The one thing nobody has" below.

---

## Scheme 1 — ISO/IEC 27001:2022, Annex A 5.9 / 5.10 / 5.12

**Who has it:** anyone certified, or preparing for certification. This is the most
common single answer in commercial organizations outside the US public sector.

**A.5.9 — Inventory of information and other associated assets.** An inventory
with owners, "reasonably complete and current", every asset having an identified
accountable owner. Typical fields: *Asset ID, Name/Description, Type, Location,
Owner, Classification, Custodian.*

**A.5.12 — Classification of information.** Classify by legal requirement, value,
criticality and sensitivity to unauthorized disclosure **or modification**, and
explicitly consider confidentiality, availability and integrity when assigning a
category.

**A.5.10 — Acceptable use.** Rules for acceptable use of information and assets.

**What we get:** the classification table, the asset list with descriptions, a
per-asset classification, the CIA consideration, and acceptable-use rules. That is
our Blocks 1, 2, 3 (partly), 6 and 7.

**What is missing:** the Tools column, and the structural flags.

**Bonus we should be taking and are not:** A.5.9 requires an **owner** per asset.
Our register has no owner field. That is a free, standards-backed column that
tells a reviewer who to ask when a score is disputed — worth adding.

---

## Scheme 2 — NIST: FIPS 199 + SP 800-60 + CSF 2.0 `ID.AM`

**Who has it:** US federal agencies, contractors, anyone under FedRAMP or FISMA,
and a large number of private organizations that adopted CSF voluntarily.

**FIPS 199** categorizes an information type as a **triple** — a {low, moderate,
high} rating for each of confidentiality, integrity and availability — defined by
the *adverse effect* of a loss. **SP 800-60** supplies the catalogue of
information types with provisional impact levels, plus the adjustment step
(aggregation raises impact) we already cite. **CSF 2.0 `ID.AM`** is the asset
management category.

**What we get:** the strongest version of the classification table, because FIPS
199 defines classes by adverse effect exactly as our spec asks, *and* it gives the
per-asset CIA triple directly rather than as an afterthought. Our "loss
priorities" line is a weaker restatement of what FIPS 199 already requires.

**What is missing:** the Tools column, and the flags.

**Caveat worth knowing:** FIPS 199 has **three** levels (low/moderate/high); we
map onto **five**. The mapping is lossy in both directions and should be stated
explicitly rather than fudged — this is the same "the scale is ours" problem
recorded in `reports/experiments/v5/GROUNDING.md`.

---

## Scheme 3 — CIS Critical Security Controls v8.1, Control 3

**Who has it:** mid-market organizations with a security program but no
certification pressure. Often the most *practically* complete of the three,
because CIS safeguards are written as things you do rather than things you assert.

- **3.1** Establish and maintain a data management process
- **3.2** Establish and maintain a **data inventory**, enumerating sensitivity levels
- **3.7** Establish and maintain a **data classification scheme**
- **3.8** **Document data flows**

**What we get:** classification scheme, data inventory with sensitivity levels,
handling process — and **3.8 is the closest any standard comes to our Tools
column**, because documenting data flows means recording what moves data where.

**What is missing:** the flags, and per-asset CIA. And 3.8 documents flows between
*systems*, not between *a tool and an asset class*, so it needs translating rather
than lifting.

---

## The one thing nobody has

**No standard requires an organization to record which tool reaches which asset.**

That column is not decorative. Our own ablation measured it:

- treating the register's Tools cell as authoritative (`naregister`) produced
  **100 %** relevance agreement and skipped **762** model calls;
- letting the model decide unaided (`scope`) left **7** pairs the organization
  says exist marked N/A, and **89** pairs scored that the organization never
  declared;
- removing the relevance gate entirely (`nona`) collapsed to 20 % agreement with
  **514 of 955** cells dumped into the lowest tier.

So the tool→asset mapping is the highest-value thing to ask for and the only field
with no standards home. CIS 3.8 is the hook to hang it on: *"you already document
data flows — this is the same question, scoped to the tools you are about to
expose to an agent."*

The **flags** (`hub`, `population`, `self-sufficient`) have no home either, and our
measurements suggest they may not need one — the no-flags arm scored better than
the flagged arm on the uncontaminated subset of the judge comparison. Do not ask
for them.

---

## The minimum ask

For an organization that has **any** of the three schemes, the request is small:

1. **Your existing data classification scheme, unchanged.** Classes with what a
   loss of each actually causes. No numbers — we derive those, and asking for them
   defeats the measurement.
2. **The rows of your asset inventory that this server can reach.** Id,
   one-line description, owner, and your existing classification if you have one.
3. **One new column: which of these tools touches which of those assets.** This is
   the only thing we are asking you to create. If you have documented data flows
   (CIS 3.8), it is the same exercise at tool granularity.
4. **Your acceptable-use rules for agents**, if you have them — what the agent is
   sanctioned to do and what is prohibited outright.

Everything else in our spec — recognition rules, operation limits, loss priority
ordering — improves the result but is not required to run.

## On machine-readable formats

If the question is *what format*, the answer the industry is converging on is
**NIST OSCAL**, and there is a forcing function: FedRAMP RFC-0024 (January 2026)
requires machine-readable packages from all providers, first deadline September
2026.

But OSCAL's models are **control-oriented** — catalog, profile,
component-definition, system security plan, assessment plan, POA&M. There is no
asset register with tool homing in any of them. So OSCAL is the right answer for
*how to serialize and exchange* this, and the wrong answer for *what to write*.
Markdown with a stable table shape, which is what we have, is fine for the
content; OSCAL matters only if the organization already runs an OSCAL pipeline.

## Sources

- ISO/IEC 27001:2022 Annex A 5.9 (inventory), 5.10 (acceptable use), 5.12
  (classification), 5.13 (labelling) —
  <https://www.isms.online/iso-27001/annex-a-2022/5-9-inventory-of-information-other-associated-assets-2022/>,
  <https://www.isms.online/iso-27001/annex-a-2022/5-12-classification-of-information-2022/>
- NIST FIPS 199 — security categorization as a {C,I,A} triple by adverse effect
- NIST SP 800-60 Vol. I/II — information types, provisional impact, aggregation
  adjustment — <https://csrc.nist.gov/pubs/sp/800/60/r2/iwd>
- NIST CSF 2.0 — `ID.AM` asset management
- CIS Critical Security Controls v8.1, Control 3 (3.1, 3.2, 3.7, 3.8) —
  <https://www.cisecurity.org/controls/data-protection>,
  <https://cas.docs.cisecurity.org/en/latest/source/Controls3/>
- NIST OSCAL — <https://pages.nist.gov/OSCAL/>; FedRAMP RFC-0024 machine-readable
  package mandate — <https://quzara.com/fedramp/oscal>
