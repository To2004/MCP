# good — Data Classification Guide to IT Services (University of Iowa)

The **most concrete** rung of the [ladder](../README.md), and the closest real-world thing
we have found to our synthetic asset registers: a published grid of real named assets, each
cell an authorization decision.

| | |
|---|---|
| Source | <https://its.uiowa.edu/services/protecting-sensitive-data/data-classification-guide-it-services> |
| Register | 41 rows × 4 classes = **164 published authorization cells** |
| Named systems | **41**, all real and loggable-into |
| Named owners | **0** — services, not accountable people |
| Operations | None. Granularity is store/share per service, not per operation |
| Page last updated | 2026-06-24 |

## Why it grades "good"

Every row is a thing that exists: `REDCap`, `Qualtrics`, `Box`, `Globus`, `HPC Systems`,
`ICON`, `Home Drives (Files@Iowa)`, `Large Scale Storage (LSS)`, `Research Data Storage
Service (RDSS)`, `Iowa Health Data Resource (IHDR) Data Enclave`, `XNAT`, `UICapture`,
`UI Zoom`, `ChatGPT Edu`, `Microsoft 365 Copilot`, `DeepSeek`. You can name the asset, find
its service page, and read off what the organization permits against it.

Crucially the grid is **not** a sensitivity rating. It is an access-restriction table — the
real-world instance of the `Authorized operations` column in the ISO arm, at service rather
than tool granularity.

## What the distribution shows

| Class | permitted | consultation required | not permitted |
|---|---|---|---|
| Public | 39 | 1 | 1 |
| University/Internal | 29 | 4 | 8 |
| Restricted | 15 | 14 | 12 |
| Critical | **0** | 30 | 11 |

Three things fall out of the numbers that a synthetic register would not have produced:

1. **No service is outright permitted for Critical data.** All 30 non-blocked services
   require a human consultation. The organization published a hard procedural gate rather
   than a per-asset severity — the control is "ask a person", not "score ≥ 4".
2. **`DeepSeek` is the only service blocked at every class**, including Public. A
   vendor-level ban, expressed in the same grid as everything else, with no explanation and
   no separate mechanism.
3. **Two rows are non-monotonic** — they permit a *more* sensitive class than a less
   sensitive one:

   | Service | Public | University/Internal | Restricted | Critical |
   |---|---|---|---|---|
   | Iowa Health Data Resource (IHDR) Data Enclave | consultation | consultation | **permitted** | consultation |
   | XNAT | permitted | permitted | **not permitted** | consultation |

   The IHDR enclave is purpose-built for regulated health data, so routine files are the
   thing it discourages. This is fit-for-purpose routing, not risk ordering, and no
   severity-monotone model can express it. It is a concrete counterexample to the assumption
   that authorization falls monotonically as sensitivity rises.

## What it still does not give us

- **No owner per asset** — ISO A.5.9 would require one; this document has none.
- **No operations** — the axis is service × data class. There is no `read` vs `write`
  distinction anywhere, so nothing here maps onto per-tool authorization.
- **Assets are containers, not contents.** These are places data can sit, not the data
  itself. Our registers list `payroll-records`; this one lists the drives it might be on.

## Extraction note

The grid ships as Font Awesome glyphs (`fa-check`, `fa-question`, `fa-xmark`) with no text
content, so a naive HTML-to-text pass drops all 164 verdicts and leaves an empty table. The
fetcher maps those classes back to the page's own legend wording. Validation: 164 grid cells
+ 3 legend icons = 167 glyphs, matching the raw page.

## Files

- `uiowa-data-classification-guide-to-it-services.md` — text extraction, grid intact
- `source.html` — raw page as downloaded
- `provenance.json` — URL, retrieval timestamp, SHA-256
