# Scan — slack:cbg

_kind=slack · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_desc · bands={'low': 3, 'medium': 42, 'high': 17, 'critical': 6, 'na': 68}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–25), scaled to this max.

## Inferred domain profile

- **mcp_kind**: messaging platform
- **asset_meaning**: channels and user information in a messaging workspace
- **blast_radius_meaning**: the extent to which a tool can affect messages or metadata across channels and users
- **dangerous_classes**: holds PII at scale, integrity concern due to impersonation risk
- **irreversible_actions**: slack_post_message, slack_reply_to_thread
- **worked_example**: Using 'slack_post_message' on the 'exec-private' channel could severely compromise confidentiality by impersonating the organization.

## Tool impact

| tool | impact |
| --- | --- |
| `slack_list_channels` | 2 |
| `slack_get_channel_history` | 3 |
| `slack_get_thread_replies` | 3 |
| `slack_get_users` | 2 |
| `slack_get_user_profile` | 3 |
| `slack_post_message` | 5 |
| `slack_reply_to_thread` | 4 |
| `slack_add_reaction` | 4 |

## Asset sensitivity

_Not scored in `impact_mode=five_level_v2_desc`: the organization's written description of this server states how severe each asset is, so no separate 1–5 sensitivity primitive is derived. The 17 assets below still form the matrix axis; the score is `blast × impact`._

| asset | sensitivity |
| --- | --- |
| `general` | — |
| `announcements` | — |
| `random` | — |
| `engineering` | — |
| `incident-response` | — |
| `on-call` | — |
| `research-team` | — |
| `exec-private` | — |
| `hr-internal` | — |
| `team-leads` | — |
| `channel-messages` | — |
| `message-reactions` | — |
| `read-markers` | — |
| `usergroup-membership` | — |
| `agent-channel-membership` | — |
| `user-directory` | — |
| `channel-directory` | — |

## Risk matrix (score · band)

_Each cell shows `score (blast×impact)` — sensitivity is not scored in this mode; impact_mode=five_level_v2_desc, score ranges 0–25. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | slack_list_channels | slack_get_channel_history | slack_get_thread_replies | slack_get_users | slack_get_user_profile | slack_post_message | slack_reply_to_thread | slack_add_reaction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 4 (2×2) 🟢 | 9 (3×3) 🟡 | 6 (2×3) 🟢 | N/A | N/A | 15 (3×5) 🟠 | 4 (1×4) 🟢 | 4 (1×4) 🟢 |
| `announcements` | 2 (1×2) 🟢 | 12 (4×3) 🟡 | 6 (2×3) 🟢 | N/A | N/A | 15 (3×5) 🟠 | 4 (1×4) 🟢 | 4 (1×4) 🟢 |
| `random` | 6 (3×2) 🟢 | 9 (3×3) 🟡 | 9 (3×3) 🟡 | N/A | N/A | 15 (3×5) 🟠 | 8 (2×4) 🟡 | 4 (1×4) 🟢 |
| `engineering` | 4 (2×2) 🟢 | 6 (2×3) 🟢 | 9 (3×3) 🟡 | N/A | N/A | 15 (3×5) 🟠 | 4 (1×4) 🟢 | 4 (1×4) 🟢 |
| `incident-response` | 4 (2×2) 🟢 | 12 (4×3) 🟡 | 9 (3×3) 🟡 | N/A | N/A | 20 (4×5) 🔴 | 4 (1×4) 🟢 | 4 (1×4) 🟢 |
| `on-call` | 4 (2×2) 🟢 | 12 (4×3) 🟡 | 9 (3×3) 🟡 | N/A | N/A | 20 (4×5) 🔴 | 4 (1×4) 🟢 | 4 (1×4) 🟢 |
| `research-team` | 2 (1×2) 🟢 | 6 (2×3) 🟢 | 6 (2×3) 🟢 | N/A | N/A | 10 (2×5) 🟡 | 4 (1×4) 🟢 | 4 (1×4) 🟢 |
| `exec-private` | 2 (1×2) 🟢 | 15 (5×3) 🟠 | 9 (3×3) 🟡 | N/A | N/A | 25 (5×5) 🔴 | 12 (3×4) 🟡 | 4 (1×4) 🟢 |
| `hr-internal` | N/A | 12 (4×3) 🟡 | 9 (3×3) 🟡 | N/A | N/A | 25 (5×5) 🔴 | 8 (2×4) 🟡 | 4 (1×4) 🟢 |
| `team-leads` | 4 (2×2) 🟢 | 15 (5×3) 🟠 | 9 (3×3) 🟡 | N/A | N/A | 20 (4×5) 🔴 | 12 (3×4) 🟡 | 4 (1×4) 🟢 |
| `channel-messages` | N/A | 12 (4×3) 🟡 | 9 (3×3) 🟡 | N/A | N/A | 25 (5×5) 🔴 | 12 (3×4) 🟡 | 4 (1×4) 🟢 |
| `message-reactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 |
| `read-markers` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `agent-channel-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `user-directory` | N/A | N/A | N/A | 10 (5×2) 🟡 | 15 (5×3) 🟠 | N/A | N/A | N/A |
| `channel-directory` | 8 (4×2) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | slack_list_channels | slack_get_channel_history | slack_get_thread_replies | slack_get_users | slack_get_user_profile | slack_post_message | slack_reply_to_thread | slack_add_reaction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 2 | 3 | 2 | N/A | N/A | 3 | 1 | 1 |
| `announcements` | 1 | 4 | 2 | N/A | N/A | 3 | 1 | 1 |
| `random` | 3 | 3 | 3 | N/A | N/A | 3 | 2 | 1 |
| `engineering` | 2 | 2 | 3 | N/A | N/A | 3 | 1 | 1 |
| `incident-response` | 2 | 4 | 3 | N/A | N/A | 4 | 1 | 1 |
| `on-call` | 2 | 4 | 3 | N/A | N/A | 4 | 1 | 1 |
| `research-team` | 1 | 2 | 2 | N/A | N/A | 2 | 1 | 1 |
| `exec-private` | 1 | 5 | 3 | N/A | N/A | 5 | 3 | 1 |
| `hr-internal` | N/A | 4 | 3 | N/A | N/A | 5 | 2 | 1 |
| `team-leads` | 2 | 5 | 3 | N/A | N/A | 4 | 3 | 1 |
| `channel-messages` | N/A | 4 | 3 | N/A | N/A | 5 | 3 | 1 |
| `message-reactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 |
| `read-markers` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `agent-channel-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `user-directory` | N/A | N/A | N/A | 5 | 5 | N/A | N/A | N/A |
| `channel-directory` | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `slack_list_channels` | **LIST** | 1 (Low) | LIST | rules |
| `slack_get_channel_history` | **READ** | 2 (Low) | READ | rules |
| `slack_get_thread_replies` | **READ** | 2 (Low) | READ | rules |
| `slack_get_users` | **READ** | 2 (Low) | READ | rules |
| `slack_get_user_profile` | **METADATA** | 1 (Low) | METADATA | rules |
| `slack_post_message` | **BROADCAST** | 4 (High) | BROADCAST, WRITE | rules |
| `slack_reply_to_thread` | **BROADCAST** | 4 (High) | BROADCAST | rules |
| `slack_add_reaction` | **BROADCAST** | 4 (High) | BROADCAST, WRITE | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
