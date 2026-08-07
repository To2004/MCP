# bad — IT-19 Institutional Data Policy (University of Iowa)

The **least concrete** rung of the [ladder](../README.md). A real policy of record, approved
2005 and last reviewed 2023, in which every asset is virtual.

| | |
|---|---|
| Source | <https://itsecurity.uiowa.edu/policies-standards-guidelines/institutional-data-policy> |
| Register | 4 rows — `Classification Level · Description · Institutional Data Examples` |
| Named systems | **0** |
| Named owners | Roles only (Data Trustee / Steward / Custodian), never a person or team |
| Operations | None. No tool, verb, or access path appears anywhere |

## Why it grades "bad"

The only thing resembling an asset register is a four-row table of classification levels.
Its `Institutional Data Examples` column lists data *kinds* — "Social Security Number",
"Financial aid data", "Departmental memos" — not things that exist at a location. There is
no way to ask this document "what reaches payroll?" because payroll is not in it.

The rest of the document is governance and backup procedure: who may reclassify data, who
must accept the confidentiality agreement annually, what a backup runbook must contain.
All real, all useful to a human, all unusable as scanner input for tool→asset homing.

## What a scanner could and could not derive from it

- **Could**: the four-class scale and the adverse-impact language that defines each class —
  roughly what our policy arms put in the classification table.
- **Could not**: which assets exist, who owns them, what reaches them, or what an agent is
  authorized to do. Every input the blast stage needs is absent.

## Files

- `uiowa-it19-institutional-data-policy.md` — text extraction
- `source.html` — raw page as downloaded
- `provenance.json` — URL, retrieval timestamp, SHA-256
