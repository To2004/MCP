# medium — Data classification guidelines (University of Iowa)

The **middle** rung of the [ladder](../README.md). Still not an inventory, but it stops
asserting classifications and starts showing the derivation — and it names one real system.

| | |
|---|---|
| Source | <https://itsecurity.uiowa.edu/it-policies/it-guidelines/data-classification-guidelines> |
| Register | No register. A CIA criteria matrix + 5 worked classification examples |
| Named systems | **1** — `InfoHawk+` (the library catalog interface) |
| Semi-concrete assets | 4 — faculty grade books, student records, sensitive research data, a professor's blog on a departmental server |
| Operations | None |

## Why it grades "medium"

Two things lift it above IT-19.

**The derivation is published.** A three-axis matrix (Confidentiality / Integrity /
Availability, each Low→Very High) with the rule stated explicitly: *"A positive response to
the highest level in ANY row is sufficient to place the data into that respective
classification."* That is a high-water-mark rule, published rather than implied — the same
rule our CIA loss-vector scoring applies offline.

**The assets stop being pure categories.** They are still not an inventory, but "InfoHawk+,
the end-user interface to search the online library catalog" is a thing with a name and a
URL, and "a professor's blog hosted on a departmental server" is a thing with a location.
Each is walked axis by axis, with the reasoning attached:

> The need for availability is recommended (medium impact) because there is no paper
> alternative and the University of Iowa probably wouldn't experience a long-term loss of
> reputation … if the library catalog is unavailable for a short period of time.

It also publishes a caveat our synthetic registers do not: that rating an asset in isolation
is insufficient, because you must *"look at the other information assets that may be affected
by a loss in confidentiality, integrity, or availability in the asset being rated."* That is
blast radius, named in a real policy, with no method given for computing it.

## What a scanner could and could not derive from it

- **Could**: the class scale, the CIA high-water-mark rule, and calibration anchors — five
  examples of what a Low/Medium/High judgment looks like in this organization's own voice.
- **Could not**: coverage. Five examples are not a register; anything not among them is
  unclassified, and there is still no tool→asset mapping.

## Files

- `uiowa-data-classification-guidelines.md` — text extraction
- `source.html` — raw page as downloaded
- `provenance.json` — URL, retrieval timestamp, SHA-256
