# Scan — calendar:real · CIA-native score

_kind=calendar · scoring=cia_loss_vector · source=five_level_v2_v5 artifacts · score_max=125 · bands={'low': 14, 'medium': 43, 'high': 11, 'critical': 8, 'na': 132}_

`score = max(existing score, sensitivity floor, max over C/I/A of S x B_f x I_f)` — the same three factors as v5, computed **per security objective** and collapsed by the high-water mark. Sensitivity and coverage are the unchanged v5 numbers; the 1–5 action ladder is replaced by per-objective impact. Every cell carries the objective that drove it, and that objective selects the control.

## Scoring rules applied

- score = max(existing score, sensitivity floor, max over C/I/A of S x B_f x I_f), range 0-125
- **INVARIANT: a cell is never scored below its existing value.** CIA is evidence added to the framework's judgement, not a re-weighting of it — so nothing the existing scale prices correctly can move down
- sensitivity floor: an asset the org rates 5 never scores below 50, and one rated 4 never below 25 — a crown jewel is not a routine cell just because the verb is a listing. Mirrors the pipeline's existing gated blast floor, one factor over
- sensitivity is NOT split per objective. `C>I>A` says disclosure hurts most on this asset; it does not say integrity loss is a tier cheaper. The loss axis breaks ties between objectives and routes the control, nothing more
- per-objective impact replaces the 1-5 action ladder as a LOWER BOUND: a READ is I_C=5 (a total confidentiality loss) and I_I=0, while writes and deletes keep their existing tiers — so only under-priced reads move
- self-sufficient assets: for CONFIDENTIALITY only, and only for content-returning ops, one item is the whole loss so B_C is treated as 5
- escape (CVSS subsequent system): assets flagged hub/self-sufficient/population gain 25% on the driving objective at coverage >= 4, capped at the scale max
- the driving objective is kept and selects the control: C -> deny, I -> confirm, A -> throttle
- bands are the v5 thresholds on the score (low <17, medium 17-49, high 50-99, critical >=100), so the two arms are directly comparable

## Tool impact per objective

_How completely one call violates each objective; 0 means it cannot touch that objective at all. Replaces the single 1–5 impact number._

| tool | atomic ops | I_C | I_I | I_A |
| --- | --- | --- | --- | --- |
| `list-calendars` | LIST | 2 | 0 | 0 |
| `list-events` | LIST | 2 | 0 | 0 |
| `search-events` | SEARCH | 4 | 0 | 0 |
| `get-event` | READ | 5 | 0 | 0 |
| `list-colors` | LIST | 2 | 2 | 2 |
| `create-event` | CREATE, WRITE | 4 | 4 | 0 |
| `create-events` | CREATE, WRITE | 4 | 4 | 0 |
| `update-event` | MODIFY | 4 | 4 | 0 |
| `delete-event` | DELETE | 5 | 5 | 5 |
| `get-freebusy` | READ | 5 | 0 | 0 |
| `respond-to-event` | MODIFY | 4 | 4 | 0 |
| `manage-accounts` | MODIFY | 5 | 5 | 0 |

## Asset sensitivity per objective

_Unchanged from the v5 scan and NOT split per objective — a loss-axis ranking is not a magnitude. The axis breaks ties between objectives and routes the control._

| asset | sensitivity | loss axis | flags |
| --- | --- | --- | --- |
| `connected-account-config` | 5 | I≈C>A | self-sufficient hub |
| `contacts` | 4 | C>I>A | population |
| `event-attendee-lists` | 4 | C>I>A | population |
| `executive` | 4 | C>I>A | — |
| `recruiting` | 4 | C>I>A | — |
| `outbound-invite-email` | 4 | I>C>A | — |
| `account-directory` | 5 | C>I>A | metadata-only |
| `personal` | 3 | C>A>I | — |
| `team` | 3 | C>A>I | — |
| `event-records` | 3 | A>I>C | — |
| `calendar-records` | 2 | C>I>A | — |
| `free-busy-availability` | 3 | C>A>I | metadata-only |
| `calendar-directory` | 2 | C>I>A | metadata-only |
| `rsvp-state` | 2 | I>A>C | metadata-only |
| `holidays` | 1 | I>C>A | public |
| `color-catalog` | 1 | none | public |

## Risk matrix (score · driver)

_Each cell shows `score (driver: S×B×I)`; range 0–125, peak here 125. Colour is by score on the v5 thresholds: 🟢 <17 · 🟡 17–49 · 🟠 50–99 · 🔴 ≥100._

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `connected-account-config` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 125 (C: 5×5×5) 🔴 |
| `contacts` | N/A | 50 (C: 4×5×2) 🟠 | 100 (C: 4×5×4) 🔴 | 25 (C: 4×1×5) 🟡 | N/A | 100 (C: 4×5×4) 🔴 | 100 (C: 4×5×4) 🔴 | 100 (C: 4×5×4) 🔴 | N/A | N/A | N/A | N/A | N/A |
| `event-attendee-lists` | N/A | 50 (C: 4×5×2) 🟠 | 100 (C: 4×5×4) 🔴 | 25 (C: 4×1×5) 🟡 | N/A | 48 (C: 4×3×4) 🟡 | 100 (C: 4×5×4) 🔴 | 48 (C: 4×3×4) 🟡 | 60 (C: 4×3×5) 🟠 | N/A | N/A | 48 (C: 4×3×4) 🟡 | N/A |
| `executive` | N/A | 0 | 48 (C: 4×3×4) 🟡 | 25 (C: 4×1×5) 🟡 | N/A | 48 (C: 4×3×4) 🟡 | 64 (C: 4×4×4) 🟠 | 48 (C: 4×3×4) 🟡 | 60 (C: 4×3×5) 🟠 | 40 (C: 4×2×5) 🟡 | N/A | 48 (C: 4×3×4) 🟡 | N/A |
| `recruiting` | N/A | 0 | 48 (C: 4×3×4) 🟡 | 25 (C: 4×1×5) 🟡 | N/A | 48 (C: 4×3×4) 🟡 | 64 (C: 4×4×4) 🟠 | 48 (C: 4×3×4) 🟡 | 60 (C: 4×3×5) 🟠 | 60 (C: 4×3×5) 🟠 | N/A | 48 (C: 4×3×4) 🟡 | N/A |
| `outbound-invite-email` | N/A | N/A | N/A | N/A | N/A | 48 (I: 4×3×4) 🟡 | 64 (I: 4×4×4) 🟠 | 48 (I: 4×3×4) 🟡 | 60 (I: 4×3×5) 🟠 | N/A | N/A | N/A | N/A |
| `account-directory` | 0 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 100 (C: 5×4×5) 🔴 |
| `personal` | N/A | 18 (C: 3×3×2) 🟡 | 36 (C: 3×3×4) 🟡 | 15 (C: 3×1×5) 🟢 | N/A | 24 (C: 3×2×4) 🟡 | 36 (C: 3×3×4) 🟡 | 24 (C: 3×2×4) 🟡 | 45 (C: 3×3×5) 🟡 | 45 (C: 3×3×5) 🟡 | N/A | 24 (C: 3×2×4) 🟡 | N/A |
| `team` | N/A | 12 (C: 3×2×2) 🟢 | 24 (C: 3×2×4) 🟡 | 15 (C: 3×1×5) 🟢 | N/A | 24 (C: 3×2×4) 🟡 | 36 (C: 3×3×4) 🟡 | 24 (C: 3×2×4) 🟡 | 45 (C: 3×3×5) 🟡 | 30 (C: 3×2×5) 🟡 | N/A | 24 (C: 3×2×4) 🟡 | N/A |
| `event-records` | N/A | 18 (A: 3×3×2) 🟡 | 36 (C: 3×3×4) 🟡 | 15 (C: 3×1×5) 🟢 | N/A | 24 (A: 3×2×4) 🟡 | 36 (A: 3×3×4) 🟡 | 36 (A: 3×3×4) 🟡 | 45 (A: 3×3×5) 🟡 | N/A | N/A | 24 (A: 3×2×4) 🟡 | N/A |
| `calendar-records` | 8 (C: 2×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `free-busy-availability` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 45 (C: 3×3×5) 🟡 | N/A | N/A | N/A |
| `calendar-directory` | 4 (C: 2×1×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `rsvp-state` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (I: 2×2×4) 🟢 | N/A |
| `holidays` | 2 (I: 1×1×2) 🟢 | 8 (I: 1×4×2) 🟢 | 8 (C: 1×2×4) 🟢 | 5 (C: 1×1×5) 🟢 | N/A | 8 (I: 1×2×4) 🟢 | N/A | N/A | 15 (I: 1×3×5) 🟢 | N/A | N/A | N/A | N/A |
| `color-catalog` | N/A | N/A | N/A | N/A | 8 (C: 1×4×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Per-objective scores

_The vector behind each cell, before the high-water mark. A zero means the tool cannot violate that objective at all. Top 25 by score._

| asset | tool | score_C | score_I | score_A | → score | driver |
| --- | --- | --- | --- | --- | --- | --- |
| `connected-account-config` | `manage-accounts` | 125 | 125 | 0 | **125** | C |
| `contacts` | `search-events` | 100 | 0 | 0 | **100** | C |
| `contacts` | `create-event` | 100 | 80 | 0 | **100** | C |
| `contacts` | `create-events` | 100 | 80 | 0 | **100** | C |
| `contacts` | `update-event` | 100 | 80 | 0 | **100** | C |
| `event-attendee-lists` | `search-events` | 100 | 0 | 0 | **100** | C |
| `event-attendee-lists` | `create-events` | 100 | 80 | 0 | **100** | C |
| `account-directory` | `manage-accounts` | 100 | 80 | 0 | **100** | C |
| `executive` | `create-events` | 64 | 64 | 0 | **64** | C |
| `recruiting` | `create-events` | 64 | 64 | 0 | **64** | C |
| `outbound-invite-email` | `create-events` | 0 | 64 | 0 | **64** | I |
| `event-attendee-lists` | `delete-event` | 60 | 60 | 60 | **60** | C |
| `executive` | `delete-event` | 60 | 60 | 60 | **60** | C |
| `recruiting` | `delete-event` | 60 | 60 | 60 | **60** | C |
| `recruiting` | `get-freebusy` | 60 | 0 | 0 | **60** | C |
| `outbound-invite-email` | `delete-event` | 0 | 60 | 60 | **60** | I |
| `contacts` | `list-events` | 50 | 0 | 0 | **50** | C |
| `event-attendee-lists` | `list-events` | 50 | 0 | 0 | **50** | C |
| `account-directory` | `list-calendars` | 40 | 0 | 0 | **50** |  |
| `event-attendee-lists` | `create-event` | 48 | 48 | 0 | **48** | C |
| `event-attendee-lists` | `update-event` | 48 | 48 | 0 | **48** | C |
| `event-attendee-lists` | `respond-to-event` | 48 | 48 | 0 | **48** | C |
| `executive` | `search-events` | 48 | 0 | 0 | **48** | C |
| `executive` | `create-event` | 48 | 48 | 0 | **48** | C |
| `executive` | `update-event` | 48 | 48 | 0 | **48** | C |

## Blast radius (coverage · 1–5)

_Unchanged from the v5 scan: what fraction of the asset ONE call reaches. Used as B in the score, per objective._

| asset \ tool | list-calendars | list-events | search-events | get-event | list-colors | create-event | create-events | update-event | delete-event | get-freebusy | get-current-time | respond-to-event | manage-accounts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `connected-account-config` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 |
| `contacts` | N/A | 5 | 5 | 1 | N/A | 5 | 5 | 5 | N/A | N/A | N/A | N/A | N/A |
| `event-attendee-lists` | N/A | 5 | 5 | 1 | N/A | 3 | 5 | 3 | 3 | N/A | N/A | 3 | N/A |
| `executive` | N/A | 3 | 3 | 1 | N/A | 3 | 4 | 3 | 3 | 2 | N/A | 3 | N/A |
| `recruiting` | N/A | 3 | 3 | 1 | N/A | 3 | 4 | 3 | 3 | 3 | N/A | 3 | N/A |
| `outbound-invite-email` | N/A | N/A | N/A | N/A | N/A | 3 | 4 | 3 | 3 | N/A | N/A | N/A | N/A |
| `account-directory` | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 |
| `personal` | N/A | 3 | 3 | 1 | N/A | 2 | 3 | 2 | 3 | 3 | N/A | 2 | N/A |
| `team` | N/A | 2 | 2 | 1 | N/A | 2 | 3 | 2 | 3 | 2 | N/A | 2 | N/A |
| `event-records` | N/A | 3 | 3 | 1 | N/A | 2 | 3 | 3 | 3 | N/A | N/A | 2 | N/A |
| `calendar-records` | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `free-busy-availability` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | N/A | N/A | N/A |
| `calendar-directory` | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `rsvp-state` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A |
| `holidays` | 1 | 4 | 2 | 1 | N/A | 2 | N/A | N/A | 3 | N/A | N/A | N/A | N/A |
| `color-catalog` | N/A | N/A | N/A | N/A | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Controls implied

_The driving objective selects the control, which a bare number cannot do. Cells scoring ≥ 50._

| control | cells | why |
| --- | --- | --- |
| **deny** | 16 | disclosure cannot be undone, so approval buys nothing |
| **require human confirmation** | 2 | recoverable only if a restore path exists |
| **existing control (CIA adds no reason here)** | 1 |  |

## Biggest changes from the v5 product (30 of 76 cells moved)

| asset | tool | driver | v5 | v6 | Δ | workings |
| --- | --- | --- | --- | --- | --- | --- |
| `contacts` | `search-events` | C | 60.0 | **100** 🔴 | +40 | 4×5×4 |
| `event-attendee-lists` | `search-events` | C | 60.0 | **100** 🔴 | +40 | 4×5×4 |
| `recruiting` | `get-freebusy` | C | 24.0 | **60** 🟠 | +36 | 4×3×5 |
| `personal` | `get-freebusy` | C | 18.0 | **45** 🟡 | +27 | 3×3×5 |
| `free-busy-availability` | `get-freebusy` | C | 18.0 | **45** 🟡 | +27 | 3×3×5 |
| `executive` | `get-freebusy` | C | 16.0 | **40** 🟡 | +24 | 4×2×5 |
| `contacts` | `create-event` | C | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `contacts` | `create-events` | C | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `contacts` | `update-event` | C | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `event-attendee-lists` | `create-events` | C | 80.0 | **100** 🔴 | +20 | 4×5×4 |
| `team` | `get-freebusy` | C | 12.0 | **30** 🟡 | +18 | 3×2×5 |
| `contacts` | `get-event` | C | 12.0 | **25** 🟡 | +13 | 4×1×5 |
| `event-attendee-lists` | `get-event` | C | 12.0 | **25** 🟡 | +13 | 4×1×5 |
| `executive` | `get-event` | C | 12.0 | **25** 🟡 | +13 | 4×1×5 |
| `recruiting` | `get-event` | C | 12.0 | **25** 🟡 | +13 | 4×1×5 |
| `executive` | `search-events` | C | 36.0 | **48** 🟡 | +12 | 4×3×4 |
| `recruiting` | `search-events` | C | 36.0 | **48** 🟡 | +12 | 4×3×4 |
| `contacts` | `list-events` | C | 40.0 | **50** 🟠 | +10 | 4×5×2 |
| `event-attendee-lists` | `list-events` | C | 40.0 | **50** 🟠 | +10 | 4×5×2 |
| `account-directory` | `list-calendars` | — | 40.0 | **50** 🟠 | +10 | existing score |
| `personal` | `search-events` | C | 27.0 | **36** 🟡 | +9 | 3×3×4 |
| `event-records` | `search-events` | C | 27.0 | **36** 🟡 | +9 | 3×3×4 |
| `personal` | `get-event` | C | 9.0 | **15** 🟢 | +6 | 3×1×5 |
| `team` | `search-events` | C | 18.0 | **24** 🟡 | +6 | 3×2×4 |
| `team` | `get-event` | C | 9.0 | **15** 🟢 | +6 | 3×1×5 |
| `event-records` | `get-event` | C | 9.0 | **15** 🟢 | +6 | 3×1×5 |
| `holidays` | `search-events` | C | 6.0 | **8** 🟢 | +2 | 1×2×4 |
| `holidays` | `get-event` | C | 3.0 | **5** 🟢 | +2 | 1×1×5 |
| `executive` | `list-events` | — | 24.0 | **25** 🟡 | +1 | existing score |
| `recruiting` | `list-events` | — | 24.0 | **25** 🟡 | +1 | existing score |

_Top 30 by absolute change; 30 moved in total._
