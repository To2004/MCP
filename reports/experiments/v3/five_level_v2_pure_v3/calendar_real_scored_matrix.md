# Calendar risk matrix — v3 + roofs (tools + description only)

Server `calendar:real` · score = sensitivity × blast × impact (max 125).
Bands (pure score thresholds): **low** <17 · **medium** 17–49 · **high** 50–99 · **critical** ≥100.

Deterministic rules: bulk-twin dominance · alias twins · **floors** (sens5→b≥4, sens4→b≥3 gate impact≥4; impact5→b≥3, impact4→b≥2) · **roofs** (impact≤3 only: non-escaping read caps b≤4, sens-1 caps b≤4; hub/population/self-sufficient assets exempt).

**Totals:** 2 critical · 8 high · 45 medium · 19 low · 134 N/A. Roof capped 3 cells (recruiting list/search-events 5→4, account-directory list-calendars 5→4).

| Asset | Tool | Sens | Blast | Impact | Score | Band |
|---|---|:-:|:-:|:-:|-:|---|
| `connected-account-config` | `manage-accounts` | 5 | 5 | 5 | 125 | critical |
| `account-directory` | `manage-accounts` | 4 | 5 | 5 | 100 | critical |
| `event-attendee-lists` | `create-events` | 4 | 4 | 5 | 80 | high |
| `executive` | `create-events` | 4 | 4 | 5 | 80 | high |
| `recruiting` | `create-events` | 4 | 4 | 5 | 80 | high |
| `event-attendee-lists` | `delete-event` | 4 | 3 | 5 | 60 | high |
| `executive` | `delete-event` | 4 | 3 | 5 | 60 | high |
| `executive` | `respond-to-event` | 4 | 3 | 5 | 60 | high |
| `recruiting` | `delete-event` | 4 | 3 | 5 | 60 | high |
| `recruiting` | `respond-to-event` | 4 | 3 | 5 | 60 | high |
| `event-attendee-lists` | `create-event` | 4 | 3 | 4 | 48 | medium |
| `event-attendee-lists` | `update-event` | 4 | 3 | 4 | 48 | medium |
| `executive` | `list-events` | 4 | 4 | 3 | 48 | medium |
| `executive` | `create-event` | 4 | 3 | 4 | 48 | medium |
| `executive` | `update-event` | 4 | 3 | 4 | 48 | medium |
| `recruiting` | `list-events` | 4 | 4 | 3 | 48 | medium |
| `recruiting` | `search-events` | 4 | 4 | 3 | 48 | medium |
| `recruiting` | `create-event` | 4 | 3 | 4 | 48 | medium |
| `recruiting` | `update-event` | 4 | 3 | 4 | 48 | medium |
| `calendar-records` | `create-events` | 3 | 3 | 5 | 45 | medium |
| `event-records` | `create-events` | 3 | 3 | 5 | 45 | medium |
| `event-records` | `delete-event` | 3 | 3 | 5 | 45 | medium |
| `event-records` | `respond-to-event` | 3 | 3 | 5 | 45 | medium |
| `free-busy-availability` | `delete-event` | 3 | 3 | 5 | 45 | medium |
| `personal` | `create-events` | 3 | 3 | 5 | 45 | medium |
| `personal` | `delete-event` | 3 | 3 | 5 | 45 | medium |
| `personal` | `respond-to-event` | 3 | 3 | 5 | 45 | medium |
| `team` | `create-events` | 3 | 3 | 5 | 45 | medium |
| `team` | `delete-event` | 3 | 3 | 5 | 45 | medium |
| `team` | `respond-to-event` | 3 | 3 | 5 | 45 | medium |
| `event-attendee-lists` | `list-events` | 4 | 3 | 3 | 36 | medium |
| `event-attendee-lists` | `search-events` | 4 | 3 | 3 | 36 | medium |
| `executive` | `search-events` | 4 | 3 | 3 | 36 | medium |
| `account-directory` | `list-calendars` | 4 | 4 | 2 | 32 | medium |
| `executive` | `get-freebusy` | 4 | 4 | 2 | 32 | medium |
| `rsvp-state` | `respond-to-event` | 2 | 3 | 5 | 30 | medium |
| `event-records` | `list-events` | 3 | 3 | 3 | 27 | medium |
| `event-records` | `search-events` | 3 | 3 | 3 | 27 | medium |
| `free-busy-availability` | `list-events` | 3 | 3 | 3 | 27 | medium |
| `free-busy-availability` | `search-events` | 3 | 3 | 3 | 27 | medium |
| `personal` | `list-events` | 3 | 3 | 3 | 27 | medium |
| `personal` | `search-events` | 3 | 3 | 3 | 27 | medium |
| `team` | `list-events` | 3 | 3 | 3 | 27 | medium |
| `team` | `search-events` | 3 | 3 | 3 | 27 | medium |
| `calendar-records` | `list-calendars` | 3 | 4 | 2 | 24 | medium |
| `event-records` | `create-event` | 3 | 2 | 4 | 24 | medium |
| `event-records` | `update-event` | 3 | 2 | 4 | 24 | medium |
| `free-busy-availability` | `get-freebusy` | 3 | 4 | 2 | 24 | medium |
| `personal` | `create-event` | 3 | 2 | 4 | 24 | medium |
| `personal` | `update-event` | 3 | 2 | 4 | 24 | medium |
| `recruiting` | `get-freebusy` | 4 | 3 | 2 | 24 | medium |
| `team` | `create-event` | 3 | 2 | 4 | 24 | medium |
| `team` | `update-event` | 3 | 2 | 4 | 24 | medium |
| `personal` | `get-freebusy` | 3 | 3 | 2 | 18 | medium |
| `team` | `get-freebusy` | 3 | 3 | 2 | 18 | medium |
| `calendar-directory` | `get-freebusy` | 2 | 4 | 2 | 16 | low |
| `holidays` | `delete-event` | 1 | 3 | 5 | 15 | low |
| `event-attendee-lists` | `get-event` | 4 | 1 | 3 | 12 | low |
| `executive` | `get-event` | 4 | 1 | 3 | 12 | low |
| `holidays` | `list-events` | 1 | 4 | 3 | 12 | low |
| `recruiting` | `get-event` | 4 | 1 | 3 | 12 | low |
| `team` | `list-calendars` | 3 | 2 | 2 | 12 | low |
| `event-records` | `get-event` | 3 | 1 | 3 | 9 | low |
| `personal` | `get-event` | 3 | 1 | 3 | 9 | low |
| `team` | `get-event` | 3 | 1 | 3 | 9 | low |
| `calendar-directory` | `list-calendars` | 2 | 2 | 2 | 8 | low |
| `color-catalog` | `list-colors` | 1 | 4 | 2 | 8 | low |
| `executive` | `list-calendars` | 4 | 1 | 2 | 8 | low |
| `holidays` | `update-event` | 1 | 2 | 4 | 8 | low |
| `recruiting` | `list-calendars` | 4 | 1 | 2 | 8 | low |
| `holidays` | `search-events` | 1 | 2 | 3 | 6 | low |
| `holidays` | `get-freebusy` | 1 | 3 | 2 | 6 | low |
| `holidays` | `get-event` | 1 | 1 | 3 | 3 | low |
| `holidays` | `list-calendars` | 1 | 1 | 2 | 2 | low |
