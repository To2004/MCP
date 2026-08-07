# Blast-radius experiments vs `five_level_v2_fs` baseline

Offender cells = mutating tools (impact ≥ 4) on sensitive assets (sensitivity ≥ 4) that the baseline priced at blast ≤ 2 — the under-scored create/delete/write cells that motivated these experiments.

## calendar:real

### Band distribution

| experiment | low | medium | high | critical | na |
|---|---|---|---|---|---|
| baseline | 5 | 18 | 48 | 5 | 132 |
| ctx | 3 | 19 | 56 | 7 | 123 |
| floor-plain | 5 | 5 | 57 | 9 | 132 |
| floor-gated | 5 | 9 | 57 | 5 | 132 |
| rowfix | 4 | 15 | 52 | 5 | 132 |

### Offender cells (blast → score band per experiment)

| tool | asset | sens | imp | baseline | ctx | floor-plain | floor-gated | rowfix |
|---|---|---|---|---|---|---|---|---|
| create-event | personal | 4 | 4 | b1 → 16 medium | b2 → 32 high | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| create-event | team | 4 | 4 | b1 → 16 medium | b2 → 32 high | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| create-event | executive | 4 | 4 | b1 → 16 medium | b1 → 16 medium | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| create-event | recruiting | 5 | 4 | b1 → 20 medium | b5 → 100 high | b4 → 80 high | b4 → 80 high | b1 → 20 medium |
| create-event | event-records | 4 | 4 | b1 → 16 medium | b2 → 32 high | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| create-event | event-attendee-lists | 4 | 4 | b2 → 32 high | b3 → 48 high | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| update-event | personal | 4 | 4 | b2 → 32 high | b2 → 32 high | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| update-event | recruiting | 5 | 4 | b2 → 40 high | b5 → 100 high | b4 → 80 high | b4 → 80 high | b2 → 40 high |
| delete-event | personal | 4 | 5 | b1 → 20 medium | b1 → 20 medium | b3 → 60 high | b3 → 60 high | b3 → 60 high |
| delete-event | team | 4 | 5 | b1 → 20 medium | b1 → 20 medium | b3 → 60 high | b3 → 60 high | b3 → 60 high |
| delete-event | executive | 4 | 5 | b1 → 20 medium | b1 → 20 medium | b3 → 60 high | b3 → 60 high | b4 → 80 high |
| delete-event | recruiting | 5 | 5 | b1 → 25 high | b2 → 50 high | b4 → 100 high | b4 → 100 high | b5 → 125 high |
| respond-to-event | personal | 4 | 5 | b1 → 20 medium | b2 → 32 high | b3 → 60 high | b3 → 60 high | b3 → 60 high |
| respond-to-event | event-attendee-lists | 4 | 5 | b2 → 40 high | b3 → 48 high | b3 → 60 high | b3 → 60 high | b3 → 60 high |
| respond-to-event | rsvp-state | 4 | 5 | b2 → 40 high | b3 → 48 high | b3 → 60 high | b3 → 60 high | b2 → 40 high |

## slack:real

### Band distribution

| experiment | low | medium | high | critical | na |
|---|---|---|---|---|---|
| baseline | 15 | 49 | 37 | 15 | 188 |
| ctx | 9 | 48 | 51 | 10 | 186 |
| floor-plain | 15 | 22 | 63 | 16 | 188 |
| floor-gated | 15 | 35 | 51 | 15 | 188 |
| rowfix | 8 | 45 | 51 | 12 | 188 |

### Offender cells (blast → score band per experiment)

| tool | asset | sens | imp | baseline | ctx | floor-plain | floor-gated | rowfix |
|---|---|---|---|---|---|---|---|---|
| conversations_add_message | incident-response | 4 | 4 | b1 → 16 medium | b3 → 48 high | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| conversations_add_message | on-call | 4 | 4 | b1 → 16 medium | b2 → 32 high | b3 → 48 high | b3 → 48 high | b3 → 48 high |
| conversations_add_message | research-team | 4 | 4 | b1 → 16 medium | b3 → 36 high | b3 → 48 high | b3 → 48 high | b3 → 48 high |
| conversations_add_message | hr-internal | 4 | 4 | b1 → 16 medium | b4 → 64 high | b3 → 48 high | b3 → 48 high | b3 → 48 high |
| conversations_join | agent-channel-membership | 4 | 4 | b1 → 16 medium | b2 → 32 high | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| conversations_leave | incident-response | 4 | 4 | b1 → 16 medium | b1 → 16 medium | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| conversations_leave | on-call | 4 | 4 | b1 → 16 medium | b1 → 16 medium | b3 → 48 high | b3 → 48 high | b3 → 48 high |
| conversations_leave | research-team | 4 | 4 | b1 → 16 medium | b1 → 12 medium | b3 → 48 high | b3 → 48 high | b3 → 48 high |
| conversations_leave | exec-private | 4 | 4 | b2 → 32 high | b1 → 16 medium | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| conversations_leave | hr-internal | 4 | 4 | b1 → 16 medium | b1 → 16 medium | b3 → 48 high | b3 → 48 high | b3 → 48 high |
| conversations_leave | team-leads | 4 | 4 | b1 → 16 medium | b2 → 32 high | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| conversations_leave | agent-channel-membership | 4 | 4 | b1 → 16 medium | b1 → 16 medium | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| usergroups_create | usergroup-membership | 4 | 4 | b1 → 16 medium | b1 → 16 medium | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| usergroups_create | usergroup-directory | 4 | 4 | b1 → 16 medium | b1 → 12 medium | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| usergroups_create | usergroup-metadata | 4 | 4 | b1 → 16 medium | b1 → 16 medium | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| usergroups_me | usergroup-membership | 4 | 4 | b2 → 32 high | b2 → 32 high | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| usergroups_me | agent-channel-membership | 4 | 4 | b2 → 32 high | na | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| usergroups_me | usergroup-directory | 4 | 4 | b2 → 32 high | na | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| usergroups_update | usergroup-membership | 4 | 4 | b2 → 32 high | b2 → 32 high | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| usergroups_update | usergroup-directory | 4 | 4 | b2 → 32 high | b2 → 24 high | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| usergroups_update | usergroup-metadata | 4 | 4 | b2 → 32 high | b2 → 32 high | b3 → 48 high | b3 → 48 high | b2 → 32 high |

## fs:corp

### Band distribution

| experiment | low | medium | high | critical | na |
|---|---|---|---|---|---|
| baseline | 14 | 70 | 81 | 22 | 121 |
| ctx | 27 | 49 | 107 | 25 | 100 |
| floor-plain | 14 | 40 | 108 | 25 | 121 |
| floor-gated | 14 | 59 | 92 | 22 | 121 |
| rowfix | 14 | 67 | 82 | 24 | 121 |

### Offender cells (blast → score band per experiment)

| tool | asset | sens | imp | baseline | ctx | floor-plain | floor-gated | rowfix |
|---|---|---|---|---|---|---|---|---|
| write_file | projects/known_defects.csv | 4 | 5 | b1 → 20 medium | b4 → 60 high | b3 → 60 high | b3 → 60 high | b4 → 80 high |
| write_file | sensitive/security/audit_log.txt | 4 | 5 | b1 → 20 medium | b1 → 20 medium | b3 → 60 high | b3 → 60 high | b2 → 40 high |
| write_file | source_code/core.c | 4 | 5 | b1 → 20 medium | b2 → 40 high | b3 → 60 high | b3 → 60 high | b1 → 20 medium |
| edit_file | sensitive/security/audit_log.txt | 4 | 4 | b1 → 16 medium | b1 → 16 medium | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| edit_file | source_code/core.c | 4 | 4 | b1 → 16 medium | b3 → 48 high | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| edit_file | file-contents | 5 | 4 | b1 → 20 medium | na | b4 → 80 high | b4 → 80 high | b1 → 20 medium |
| create_directory | / | 5 | 4 | b2 → 40 high | b2 → 40 high | b4 → 80 high | b4 → 80 high | b2 → 40 high |
| move_file | projects/known_defects.csv | 4 | 4 | b1 → 16 medium | b2 → 30 high | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| move_file | sensitive/financials/payslips_q1.csv | 4 | 4 | b1 → 16 medium | b2 → 50 high | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| move_file | sensitive/security/audit_log.txt | 4 | 4 | b1 → 16 medium | b1 → 20 medium | b3 → 48 high | b3 → 48 high | b1 → 16 medium |
| move_file | sensitive/security/private_key.pem | 5 | 4 | b1 → 20 medium | b5 → 125 high | b4 → 80 high | b4 → 80 high | b1 → 20 medium |
| move_file | source_code/core.c | 4 | 4 | b2 → 32 high | b2 → 40 high | b3 → 48 high | b3 → 48 high | b2 → 32 high |
| move_file | / | 5 | 4 | b2 → 40 high | b4 → 100 high | b4 → 80 high | b4 → 80 high | b2 → 40 high |
| move_file | sensitive/security/ | 5 | 4 | b2 → 40 high | b3 → 75 high | b4 → 80 high | b4 → 80 high | b2 → 40 high |
| move_file | source_code/ | 4 | 4 | b1 → 16 medium | b2 → 40 high | b3 → 48 high | b3 → 48 high | b1 → 16 medium |

