# Scan — slack:real · CIA-native score

_kind=slack · scoring=cia_loss_vector · source=five_level_v2_v5 artifacts · score_max=125 · bands={'low': 26, 'medium': 40, 'high': 31, 'critical': 18, 'na': 205}_

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
| `channels_list` | LIST | 2 | 0 | 0 |
| `channels_me` | METADATA | 2 | 0 | 0 |
| `conversations_add_message` | BROADCAST | 4 | 5 | 0 |
| `conversations_history` | READ | 5 | 0 | 0 |
| `conversations_join` | CREATE | 4 | 4 | 0 |
| `conversations_leave` | MODIFY | 4 | 4 | 0 |
| `conversations_mark` | MODIFY | 2 | 4 | 0 |
| `conversations_replies` | READ | 5 | 0 | 0 |
| `conversations_search_messages` | BROADCAST | 4 | 5 | 0 |
| `conversations_unreads` | METADATA | 3 | 0 | 0 |
| `usergroups_create` | CREATE | 0 | 4 | 0 |
| `usergroups_list` | LIST | 2 | 2 | 0 |
| `usergroups_me` | METADATA | 2 | 5 | 0 |
| `usergroups_update` | MODIFY | 0 | 4 | 0 |
| `usergroups_users_update` | MODIFY | 0 | 5 | 0 |
| `users_search` | SEARCH | 4 | 0 | 0 |

## Asset sensitivity per objective

_Unchanged from the v5 scan and NOT split per objective — a loss-axis ranking is not a magnitude. The axis breaks ties between objectives and routes the control._

| asset | sensitivity | loss axis | flags |
| --- | --- | --- | --- |
| `exec-private` | 4 | C>I>A | — |
| `hr-internal` | 4 | C>I>A | — |
| `incident-response` | 5 | C>I>A | self-sufficient |
| `on-call` | 4 | C>I>A | — |
| `team-leads` | 4 | C>I>A | — |
| `research-team` | 4 | C>I>A | — |
| `engineering` | 3 | C>I>A | — |
| `general` | 1 | C>I>A | public |
| `announcements` | 1 | I>C>A | public |
| `random` | 1 | C>I>A | public |
| `channel-messages` | 4 | C>I>A | population |
| `usergroup-membership` | 4 | I>C>A | hub |
| `user-group-membership` | 4 | I>C>A | hub |
| `agent-channel-membership` | 4 | I>C>A | hub |
| `user-directory` | 4 | C>I>A | population |
| `channel-directory` | 2 | C>I>A | metadata-only |
| `usergroup-directory` | 2 | C>I>A | metadata-only |
| `usergroup-metadata` | 2 | C>I>A | metadata-only |
| `read-markers` | 2 | I>A>C | metadata-only |

## Risk matrix (score · driver)

_Each cell shows `score (driver: S×B×I)`; range 0–125, peak here 125. Colour is by score on the v5 thresholds: 🟢 <17 · 🟡 17–49 · 🟠 50–99 · 🔴 ≥100._

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `exec-private` | N/A | N/A | 80 (I: 4×4×5) 🟠 | 80 (C: 4×4×5) 🟠 | 48 (C: 4×3×4) 🟡 | 48 (C: 4×3×4) 🟡 | 25 (I: 4×1×4) 🟡 | 60 (C: 4×3×5) 🟠 | 80 (I: 4×4×5) 🟠 | 0 | N/A | N/A | N/A | N/A | N/A | N/A |
| `hr-internal` | N/A | N/A | 80 (I: 4×4×5) 🟠 | 80 (C: 4×4×5) 🟠 | 64 (C: 4×4×4) 🟠 | 48 (C: 4×3×4) 🟡 | 25 (I: 4×1×4) 🟡 | 60 (C: 4×3×5) 🟠 | 80 (I: 4×4×5) 🟠 | 0 | N/A | N/A | N/A | N/A | N/A | N/A |
| `incident-response` | N/A | 0 | 125 (I: 5×4×5) 🔴 | 125 (C: 5×5×5) 🔴 | 100 (C: 5×4×4) 🔴 | 100 (C: 5×4×4) 🔴 | 50 (I: 5×1×4) 🟠 | 125 (C: 5×5×5) 🔴 | 125 (I: 5×4×5) 🔴 | 94 (C: 5×5×3) 🟠 | N/A | N/A | N/A | N/A | N/A | N/A |
| `on-call` | N/A | N/A | 80 (I: 4×4×5) 🟠 | 80 (C: 4×4×5) 🟠 | 48 (C: 4×3×4) 🟡 | 48 (C: 4×3×4) 🟡 | 25 (I: 4×1×4) 🟡 | 40 (C: 4×2×5) 🟡 | 80 (I: 4×4×5) 🟠 | 0 | N/A | N/A | N/A | N/A | N/A | N/A |
| `team-leads` | N/A | N/A | 80 (I: 4×4×5) 🟠 | 80 (C: 4×4×5) 🟠 | 64 (C: 4×4×4) 🟠 | 48 (C: 4×3×4) 🟡 | 25 (I: 4×1×4) 🟡 | 80 (C: 4×4×5) 🟠 | 80 (I: 4×4×5) 🟠 | 0 | N/A | N/A | N/A | N/A | N/A | N/A |
| `research-team` | N/A | N/A | 60 (I: 4×3×5) 🟠 | 80 (C: 4×4×5) 🟠 | 48 (C: 4×3×4) 🟡 | 48 (C: 4×3×4) 🟡 | 25 (I: 4×1×4) 🟡 | 60 (C: 4×3×5) 🟠 | 80 (I: 4×4×5) 🟠 | 36 (C: 4×3×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A |
| `engineering` | N/A | N/A | 60 (I: 3×4×5) 🟠 | 60 (C: 3×4×5) 🟠 | 24 (C: 3×2×4) 🟡 | 24 (C: 3×2×4) 🟡 | 12 (I: 3×1×4) 🟢 | 45 (C: 3×3×5) 🟡 | 45 (I: 3×3×5) 🟡 | 18 (C: 3×2×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A |
| `general` | 2 (C: 1×1×2) 🟢 | 2 (C: 1×1×2) 🟢 | 20 (I: 1×4×5) 🟡 | 20 (C: 1×4×5) 🟡 | 8 (C: 1×2×4) 🟢 | 8 (C: 1×2×4) 🟢 | 4 (I: 1×1×4) 🟢 | 10 (C: 1×2×5) 🟢 | 20 (I: 1×4×5) 🟡 | 3 (C: 1×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `announcements` | 2 (I: 1×1×2) 🟢 | N/A | 20 (I: 1×4×5) 🟡 | 20 (C: 1×4×5) 🟡 | 8 (I: 1×2×4) 🟢 | 8 (I: 1×2×4) 🟢 | 4 (I: 1×1×4) 🟢 | 20 (C: 1×4×5) 🟡 | 20 (I: 1×4×5) 🟡 | 3 (I: 1×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `random` | 2 (C: 1×1×2) 🟢 | 2 (C: 1×1×2) 🟢 | 10 (I: 1×2×5) 🟢 | 20 (C: 1×4×5) 🟡 | 8 (C: 1×2×4) 🟢 | 8 (C: 1×2×4) 🟢 | 4 (I: 1×1×4) 🟢 | 20 (C: 1×4×5) 🟡 | 20 (I: 1×4×5) 🟡 | 3 (C: 1×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `channel-messages` | N/A | N/A | 125 (I: 4×5×5) 🔴 | 125 (C: 4×5×5) 🔴 | N/A | N/A | N/A | 125 (C: 4×5×5) 🔴 | 125 (I: 4×5×5) 🔴 | 36 (C: 4×3×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 48 (I: 4×3×4) 🟡 | 50 (I: 4×5×2) 🟠 | 60 (I: 4×3×5) 🟠 | 100 (I: 4×5×4) 🔴 | 125 (I: 4×5×5) 🔴 | N/A |
| `user-group-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 80 (I: 4×4×4) 🟠 | 50 (I: 4×5×2) 🟠 | 125 (I: 4×5×5) 🔴 | 100 (I: 4×5×4) 🔴 | 125 (I: 4×5×5) 🔴 | N/A |
| `agent-channel-membership` | N/A | 40 (I: 4×4×2) 🟡 | N/A | N/A | 100 (I: 4×5×4) 🔴 | 80 (I: 4×4×4) 🟠 | N/A | N/A | N/A | N/A | N/A | N/A | 125 (I: 4×5×5) 🔴 | N/A | N/A | N/A |
| `user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 100 (C: 4×5×4) 🔴 |
| `channel-directory` | 16 (C: 2×4×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (C: 2×2×4) 🟢 | 16 (C: 2×4×2) 🟢 | N/A | 32 (C: 2×4×4) 🟡 | N/A | N/A |
| `usergroup-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 24 (C: 2×3×4) 🟡 | 16 (C: 2×4×2) 🟢 | N/A | 16 (C: 2×2×4) 🟢 | N/A | N/A |
| `read-markers` | N/A | N/A | N/A | N/A | N/A | N/A | 8 (I: 2×1×4) 🟢 | N/A | N/A | 18 (I: 2×3×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A |
| `message-reactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Per-objective scores

_The vector behind each cell, before the high-water mark. A zero means the tool cannot violate that objective at all. Top 25 by score._

| asset | tool | score_C | score_I | score_A | → score | driver |
| --- | --- | --- | --- | --- | --- | --- |
| `incident-response` | `conversations_add_message` | 80 | 125 | 0 | **125** | I |
| `incident-response` | `conversations_history` | 125 | 0 | 0 | **125** | C |
| `incident-response` | `conversations_replies` | 125 | 0 | 0 | **125** | C |
| `incident-response` | `conversations_search_messages` | 80 | 125 | 0 | **125** | I |
| `channel-messages` | `conversations_add_message` | 80 | 125 | 0 | **125** | I |
| `channel-messages` | `conversations_history` | 125 | 0 | 0 | **125** | C |
| `channel-messages` | `conversations_replies` | 125 | 0 | 0 | **125** | C |
| `channel-messages` | `conversations_search_messages` | 80 | 125 | 0 | **125** | I |
| `usergroup-membership` | `usergroups_users_update` | 0 | 125 | 0 | **125** | I |
| `user-group-membership` | `usergroups_me` | 40 | 125 | 0 | **125** | I |
| `user-group-membership` | `usergroups_users_update` | 0 | 125 | 0 | **125** | I |
| `agent-channel-membership` | `usergroups_me` | 40 | 125 | 0 | **125** | I |
| `incident-response` | `conversations_join` | 100 | 80 | 0 | **100** | C |
| `incident-response` | `conversations_leave` | 100 | 80 | 0 | **100** | C |
| `usergroup-membership` | `usergroups_update` | 0 | 100 | 0 | **100** | I |
| `user-group-membership` | `usergroups_update` | 0 | 100 | 0 | **100** | I |
| `agent-channel-membership` | `conversations_join` | 0 | 100 | 0 | **100** | I |
| `user-directory` | `users_search` | 100 | 0 | 0 | **100** | C |
| `incident-response` | `conversations_unreads` | 94 | 0 | 0 | **94** | C |
| `exec-private` | `conversations_add_message` | 64 | 80 | 0 | **80** | I |
| `exec-private` | `conversations_history` | 80 | 0 | 0 | **80** | C |
| `exec-private` | `conversations_search_messages` | 64 | 80 | 0 | **80** | I |
| `hr-internal` | `conversations_add_message` | 64 | 80 | 0 | **80** | I |
| `hr-internal` | `conversations_history` | 80 | 0 | 0 | **80** | C |
| `hr-internal` | `conversations_search_messages` | 64 | 80 | 0 | **80** | I |

## Blast radius (coverage · 1–5)

_Unchanged from the v5 scan: what fraction of the asset ONE call reaches. Used as B in the score, per objective._

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `exec-private` | N/A | N/A | 4 | 4 | 3 | 3 | 1 | 3 | 4 | 1 | N/A | N/A | N/A | N/A | N/A | N/A |
| `hr-internal` | N/A | N/A | 4 | 4 | 4 | 3 | 1 | 3 | 4 | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `incident-response` | N/A | 1 | 4 | 5 | 4 | 4 | 1 | 5 | 4 | 5 | N/A | N/A | N/A | N/A | N/A | N/A |
| `on-call` | N/A | N/A | 4 | 4 | 3 | 3 | 1 | 2 | 4 | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `team-leads` | N/A | N/A | 4 | 4 | 4 | 3 | 1 | 4 | 4 | 1 | N/A | N/A | N/A | N/A | N/A | N/A |
| `research-team` | N/A | N/A | 3 | 4 | 3 | 3 | 1 | 3 | 4 | 3 | N/A | N/A | N/A | N/A | N/A | N/A |
| `engineering` | N/A | N/A | 4 | 4 | 2 | 2 | 1 | 3 | 3 | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `general` | 1 | 1 | 4 | 4 | 2 | 2 | 1 | 2 | 4 | 1 | N/A | N/A | N/A | N/A | N/A | N/A |
| `announcements` | 1 | N/A | 4 | 4 | 2 | 2 | 1 | 4 | 4 | 1 | N/A | N/A | N/A | N/A | N/A | N/A |
| `random` | 1 | 1 | 2 | 4 | 2 | 2 | 1 | 4 | 4 | 1 | N/A | N/A | N/A | N/A | N/A | N/A |
| `channel-messages` | N/A | N/A | 5 | 5 | N/A | N/A | N/A | 5 | 5 | 3 | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 5 | 3 | 5 | 5 | N/A |
| `user-group-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 5 | 5 | 5 | 5 | N/A |
| `agent-channel-membership` | N/A | 4 | N/A | N/A | 5 | 4 | N/A | N/A | N/A | N/A | N/A | N/A | 5 | N/A | N/A | N/A |
| `user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 |
| `channel-directory` | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 4 | N/A | 4 | N/A | N/A |
| `usergroup-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 4 | N/A | 2 | N/A | N/A |
| `read-markers` | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A |
| `message-reactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Controls implied

_The driving objective selects the control, which a bare number cannot do. Cells scoring ≥ 50._

| control | cells | why |
| --- | --- | --- |
| **require human confirmation** | 28 | recoverable only if a restore path exists |
| **deny** | 20 | disclosure cannot be undone, so approval buys nothing |
| **existing control (CIA adds no reason here)** | 1 |  |

## Biggest changes from the v5 product (76 of 115 cells moved)

| asset | tool | driver | v5 | v6 | Δ | workings |
| --- | --- | --- | --- | --- | --- | --- |
| `incident-response` | `conversations_search_messages` | I | 60.0 | **125** 🔴 | +65 | 5×4×5 |
| `channel-messages` | `conversations_history` | C | 60.0 | **125** 🔴 | +65 | 4×5×5 |
| `channel-messages` | `conversations_replies` | C | 60.0 | **125** 🔴 | +65 | 4×5×5 |
| `channel-messages` | `conversations_search_messages` | I | 60.0 | **125** 🔴 | +65 | 4×5×5 |
| `incident-response` | `conversations_history` | C | 75.0 | **125** 🔴 | +50 | 5×5×5 |
| `incident-response` | `conversations_replies` | C | 75.0 | **125** 🔴 | +50 | 5×5×5 |
| `incident-response` | `conversations_add_message` | I | 80.0 | **125** 🔴 | +45 | 5×4×5 |
| `channel-messages` | `conversations_add_message` | I | 80.0 | **125** 🔴 | +45 | 4×5×5 |
| `incident-response` | `channels_me` | — | 10.0 | **50** 🟠 | +40 | existing score |
| `incident-response` | `conversations_mark` | I | 10.0 | **50** 🟠 | +40 | 5×1×4 |
| `user-directory` | `users_search` | C | 60.0 | **100** 🔴 | +40 | 4×5×4 |
| `exec-private` | `conversations_history` | C | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `exec-private` | `conversations_search_messages` | I | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `hr-internal` | `conversations_history` | C | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `hr-internal` | `conversations_search_messages` | I | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `on-call` | `conversations_history` | C | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `on-call` | `conversations_search_messages` | I | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `team-leads` | `conversations_history` | C | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `team-leads` | `conversations_replies` | C | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `team-leads` | `conversations_search_messages` | I | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `research-team` | `conversations_history` | C | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `research-team` | `conversations_search_messages` | I | 48.0 | **80** 🟠 | +32 | 4×4×5 |
| `usergroup-membership` | `usergroups_users_update` | I | 100.0 | **125** 🔴 | +25 | 4×5×5 |
| `user-group-membership` | `usergroups_me` | I | 100.0 | **125** 🔴 | +25 | 4×5×5 |
| `user-group-membership` | `usergroups_users_update` | I | 100.0 | **125** 🔴 | +25 | 4×5×5 |
| `agent-channel-membership` | `usergroups_me` | I | 100.0 | **125** 🔴 | +25 | 4×5×5 |
| `exec-private` | `conversations_replies` | C | 36.0 | **60** 🟠 | +24 | 4×3×5 |
| `hr-internal` | `conversations_replies` | C | 36.0 | **60** 🟠 | +24 | 4×3×5 |
| `research-team` | `conversations_replies` | C | 36.0 | **60** 🟠 | +24 | 4×3×5 |
| `engineering` | `conversations_history` | C | 36.0 | **60** 🟠 | +24 | 3×4×5 |

_Top 30 by absolute change; 76 moved in total._
