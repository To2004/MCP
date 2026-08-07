# Scan — slack:real

_kind=slack · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v4_static · bands={'low': 57, 'medium': 49, 'high': 19, 'critical': 4, 'na': 191}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Deterministic rules applied

- sensitivity = org profile table (never LLM-scored)
- bulk twin impact: impact(bulk) >= impact(singular)
- alias twins (DEPRECATED -> canonical): max blast per asset
- gated blast floor (impact >= 4): sens 5 -> blast >= 4, sens 4 -> blast >= 3
- impact-keyed floor (one tier lower): impact 5 -> blast >= 3, impact 4 -> blast >= 2
- bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)
- blast roof (impact <= 3 only, never a mutation): non-escaping read caps at 4, sens-1 caps at 4 — assets flagged hub/population/self-sufficient are exempt
- bands: band_label_v5 — pure score thresholds on the 0-125 scale (low <17, medium 17-49, high 50-99, critical >=100); no categorical overrides, so a band is explainable from its own score

## Inferred domain profile

- **mcp_kind**: communication
- **asset_meaning**: Slack channels and related metadata
- **blast_radius_meaning**: The extent to which a tool can affect the confidentiality, integrity, or availability of Slack channel messages and user group memberships
- **dangerous_classes**: holds unreleased strategy or compensation data, live incident detail with credentials, management discussion
- **irreversible_actions**: usergroups_users_update, conversations_join
- **worked_example**: The tool 'usergroups_users_update' paired with the asset 'exec-private' can irreversibly change who has access to sensitive executive discussions, escalating severity due to its impact on confidentiality.

## Tool impact

| tool | impact |
| --- | --- |
| `channels_list` | 2 |
| `channels_me` | 2 |
| `conversations_add_message` | 4 |
| `conversations_history` | 3 |
| `conversations_join` | 4 |
| `conversations_leave` | 4 |
| `conversations_mark` | 2 |
| `conversations_replies` | 3 |
| `conversations_search_messages` | 3 |
| `conversations_unreads` | 3 |
| `usergroups_create` | 4 |
| `usergroups_list` | 2 |
| `usergroups_me` | 5 |
| `usergroups_update` | 4 |
| `usergroups_users_update` | 5 |
| `users_search` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `general` | 1 |
| `announcements` | 1 |
| `random` | 1 |
| `engineering` | 3 |
| `incident-response` | 4 |
| `on-call` | 4 |
| `research-team` | 3 |
| `exec-private` | 4 |
| `hr-internal` | 4 |
| `team-leads` | 4 |
| `channel-messages` | 4 |
| `message-reactions` | 2 |
| `read-markers` | 2 |
| `usergroup-membership` | 4 |
| `agent-channel-membership` | 4 |
| `user-directory` | 4 |
| `channel-directory` | 2 |
| `usergroup-directory` | 2 |
| `user-group-membership` | 4 |
| `usergroup-metadata` | 2 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v4_static, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 4 (1×2×2) 🟢 | 2 (1×1×2) 🟢 | 8 (1×2×4) 🟢 | 12 (1×4×3) 🟢 | 8 (1×2×4) 🟢 | 8 (1×2×4) 🟢 | 2 (1×1×2) 🟢 | 9 (1×3×3) 🟢 | 9 (1×3×3) 🟢 | 3 (1×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `announcements` | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 8 (1×2×4) 🟢 | 12 (1×4×3) 🟢 | 8 (1×2×4) 🟢 | 8 (1×2×4) 🟢 | 8 (1×4×2) 🟢 | 3 (1×1×3) 🟢 | 9 (1×3×3) 🟢 | 3 (1×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `random` | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 8 (1×2×4) 🟢 | 12 (1×4×3) 🟢 | 8 (1×2×4) 🟢 | 8 (1×2×4) 🟢 | 2 (1×1×2) 🟢 | 9 (1×3×3) 🟢 | 3 (1×1×3) 🟢 | 3 (1×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `engineering` | 12 (3×2×2) 🟢 | 6 (3×1×2) 🟢 | 24 (3×2×4) 🟢 | 36 (3×4×3) 🟡 | 24 (3×2×4) 🟢 | 24 (3×2×4) 🟢 | 6 (3×1×2) 🟢 | 18 (3×2×3) 🟢 | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `incident-response` | N/A | 8 (4×1×2) 🟢 | 48 (4×3×4) 🟡 | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 16 (4×2×2) 🟢 | 48 (4×4×3) 🟡 | 48 (4×4×3) 🟡 | 36 (4×3×3) 🟡 | N/A | N/A | N/A | N/A | 100 (4×5×5) 🔴 | N/A |
| `on-call` | N/A | 8 (4×1×2) 🟢 | 48 (4×3×4) 🟡 | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 32 (4×4×2) 🟢 | 36 (4×3×3) 🟡 | 48 (4×4×3) 🟡 | 12 (4×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `research-team` | 12 (3×2×2) 🟢 | 6 (3×1×2) 🟢 | 24 (3×2×4) 🟢 | 36 (3×4×3) 🟡 | 24 (3×2×4) 🟢 | 24 (3×2×4) 🟢 | 6 (3×1×2) 🟢 | 18 (3×2×3) 🟢 | 27 (3×3×3) 🟢 | 18 (3×2×3) 🟢 | N/A | N/A | N/A | N/A | 60 (3×4×5) 🟡 | N/A |
| `exec-private` | N/A | N/A | 48 (4×3×4) 🟡 | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 8 (4×1×2) 🟢 | 48 (4×4×3) 🟡 | 48 (4×4×3) 🟡 | 48 (4×4×3) 🟡 | N/A | N/A | N/A | N/A | 80 (4×4×5) 🟠 | N/A |
| `hr-internal` | 8 (4×1×2) 🟢 | N/A | 48 (4×3×4) 🟡 | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 8 (4×1×2) 🟢 | 12 (4×1×3) 🟢 | 36 (4×3×3) 🟡 | 12 (4×1×3) 🟢 | N/A | N/A | N/A | N/A | 80 (4×4×5) 🟠 | N/A |
| `team-leads` | 8 (4×1×2) 🟢 | 8 (4×1×2) 🟢 | 48 (4×3×4) 🟡 | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 8 (4×1×2) 🟢 | 36 (4×3×3) 🟡 | 48 (4×4×3) 🟡 | 12 (4×1×3) 🟢 | N/A | N/A | N/A | N/A | 80 (4×4×5) 🟠 | N/A |
| `channel-messages` | N/A | N/A | 64 (4×4×4) 🟡 | 60 (4×5×3) 🟡 | 80 (4×5×4) 🟠 | N/A | 24 (4×3×2) 🟢 | 60 (4×5×3) 🟡 | 60 (4×5×3) 🟡 | 60 (4×5×3) 🟡 | N/A | N/A | N/A | N/A | 100 (4×5×5) 🔴 | N/A |
| `message-reactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 6 (2×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `read-markers` | N/A | N/A | N/A | N/A | N/A | N/A | 16 (2×4×2) 🟢 | N/A | N/A | 18 (2×3×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 32 (4×4×2) 🟢 | 60 (4×3×5) 🟡 | N/A | 100 (4×5×5) 🔴 | N/A |
| `agent-channel-membership` | N/A | 32 (4×4×2) 🟢 | N/A | N/A | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 60 (4×5×3) 🟡 |
| `channel-directory` | 16 (2×4×2) 🟢 | 8 (2×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (2×2×4) 🟢 | 16 (2×4×2) 🟢 | N/A | 16 (2×2×4) 🟢 | N/A | N/A |
| `user-group-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 24 (4×3×2) 🟢 | 60 (4×3×5) 🟡 | N/A | 100 (4×5×5) 🔴 | N/A |
| `usergroup-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 24 (2×3×4) 🟢 | 16 (2×4×2) 🟢 | N/A | 24 (2×3×4) 🟢 | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 2 | 1 | 2 | 4 | 2 | 2 | 1 | 3 | 3 | 1 | N/A | N/A | N/A | N/A | N/A | N/A |
| `announcements` | 1 | 1 | 2 | 4 | 2 | 2 | 4 | 1 | 3 | 1 | N/A | N/A | N/A | N/A | N/A | N/A |
| `random` | 1 | 1 | 2 | 4 | 2 | 2 | 1 | 3 | 1 | 1 | N/A | N/A | N/A | N/A | N/A | N/A |
| `engineering` | 2 | 1 | 2 | 4 | 2 | 2 | 1 | 2 | 3 | 3 | N/A | N/A | N/A | N/A | N/A | N/A |
| `incident-response` | N/A | 1 | 3 | 4 | 4 | 3 | 2 | 4 | 4 | 3 | N/A | N/A | N/A | N/A | 5 | N/A |
| `on-call` | N/A | 1 | 3 | 4 | 4 | 3 | 4 | 3 | 4 | 1 | N/A | N/A | N/A | N/A | N/A | N/A |
| `research-team` | 2 | 1 | 2 | 4 | 2 | 2 | 1 | 2 | 3 | 2 | N/A | N/A | N/A | N/A | 4 | N/A |
| `exec-private` | N/A | N/A | 3 | 4 | 4 | 3 | 1 | 4 | 4 | 4 | N/A | N/A | N/A | N/A | 4 | N/A |
| `hr-internal` | 1 | N/A | 3 | 4 | 4 | 3 | 1 | 1 | 3 | 1 | N/A | N/A | N/A | N/A | 4 | N/A |
| `team-leads` | 1 | 1 | 3 | 4 | 4 | 3 | 1 | 3 | 4 | 1 | N/A | N/A | N/A | N/A | 4 | N/A |
| `channel-messages` | N/A | N/A | 4 | 5 | 5 | N/A | 3 | 5 | 5 | 5 | N/A | N/A | N/A | N/A | 5 | N/A |
| `message-reactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `read-markers` | N/A | N/A | N/A | N/A | N/A | N/A | 4 | N/A | N/A | 3 | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 3 | N/A | 5 | N/A |
| `agent-channel-membership` | N/A | 4 | N/A | N/A | 5 | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 |
| `channel-directory` | 4 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 4 | N/A | 2 | N/A | N/A |
| `user-group-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 3 | N/A | 5 | N/A |
| `usergroup-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 4 | N/A | 3 | N/A | N/A |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `channels_list` | **LIST** | 1 (Low) | LIST | rules |
| `channels_me` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `conversations_add_message` | **BROADCAST** | 4 (High) | BROADCAST | verb-fallback |
| `conversations_history` | **READ** | 2 (Low) | READ | verb-fallback |
| `conversations_join` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `conversations_leave` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `conversations_mark` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `conversations_replies` | **READ** | 2 (Low) | READ | verb-fallback |
| `conversations_search_messages` | **BROADCAST** | 4 (High) | BROADCAST | verb-fallback |
| `conversations_unreads` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `usergroups_create` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `usergroups_list` | **LIST** | 1 (Low) | LIST | rules |
| `usergroups_me` | **METADATA** | 1 (Low) | METADATA | verb-fallback |
| `usergroups_update` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `usergroups_users_update` | **MODIFY** | 3 (Medium) | MODIFY | verb-fallback |
| `users_search` | **SEARCH** | 2 (Low) | SEARCH | verb-fallback |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `channels_list` | `query` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `channels_list` | `query_targets` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `channels_list` | `limit` | 3 | large value | magnitude/count — larger value means broader effect |
| `channels_list` | `channel_types` | 2 | — | names the target resource — selects what the op touches |
| `channels_list` | `cursor` | 1 | — | minor / structural parameter |
| `channels_list` | `sort` | 1 | — | minor / structural parameter |
| `channels_me` | `limit` | 3 | large value | magnitude/count — larger value means broader effect |
| `channels_me` | `channel_types` | 2 | — | names the target resource — selects what the op touches |
| `channels_me` | `cursor` | 1 | — | minor / structural parameter |
| `conversations_add_message` | `blocks` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `conversations_add_message` | `content_type` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `conversations_add_message` | `text` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `conversations_add_message` | `channel_id` | 2 | — | names the target resource — selects what the op touches |
| `conversations_add_message` | `thread_ts` | 1 | — | minor / structural parameter |
| `conversations_history` | `include_activity_messages` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `conversations_history` | `limit` | 3 | large value | magnitude/count — larger value means broader effect |
| `conversations_history` | `channel_id` | 2 | — | names the target resource — selects what the op touches |
| `conversations_history` | `cursor` | 1 | — | minor / structural parameter |
| `conversations_join` | `channel_id` | 2 | — | names the target resource — selects what the op touches |
| `conversations_leave` | `channel_id` | 2 | — | names the target resource — selects what the op touches |
| `conversations_mark` | `channel_id` | 2 | — | names the target resource — selects what the op touches |
| `conversations_mark` | `ts` | 1 | — | minor / structural parameter |
| `conversations_replies` | `include_activity_messages` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `conversations_replies` | `limit` | 3 | large value | magnitude/count — larger value means broader effect |
| `conversations_replies` | `channel_id` | 2 | — | names the target resource — selects what the op touches |
| `conversations_replies` | `thread_ts` | 1 | — | minor / structural parameter |
| `conversations_replies` | `cursor` | 1 | — | minor / structural parameter |
| `conversations_search_messages` | `filter_date_after` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `conversations_search_messages` | `filter_date_before` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `conversations_search_messages` | `filter_date_during` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `conversations_search_messages` | `filter_date_on` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `conversations_search_messages` | `filter_in_channel` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `conversations_search_messages` | `filter_in_im_or_mpim` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `conversations_search_messages` | `filter_threads_only` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `conversations_search_messages` | `filter_users_from` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `conversations_search_messages` | `filter_users_with` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `conversations_search_messages` | `search_query` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `conversations_search_messages` | `limit` | 3 | large value | magnitude/count — larger value means broader effect |
| `conversations_search_messages` | `cursor` | 1 | — | minor / structural parameter |
| `conversations_unreads` | `include_messages` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `conversations_unreads` | `max_messages_per_channel` | 4 | — | payload content — injection / exfiltration / poisoning vecto |
| `conversations_unreads` | `max_channels` | 3 | large value | magnitude/count — larger value means broader effect |
| `conversations_unreads` | `channel_types` | 2 | — | names the target resource — selects what the op touches |
| `conversations_unreads` | `include_muted` | 1 | — | minor / structural parameter |
| `conversations_unreads` | `mentions_only` | 1 | — | minor / structural parameter |
| `usergroups_create` | `description` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `usergroups_create` | `name` | 2 | — | names the target resource — selects what the op touches |
| `usergroups_create` | `channels` | 2 | — | names the target resource — selects what the op touches |
| `usergroups_create` | `handle` | 1 | — | minor / structural parameter |
| `usergroups_list` | `include_count` | 3 | large value | magnitude/count — larger value means broader effect |
| `usergroups_list` | `include_users` | 2 | — | names the target resource — selects what the op touches |
| `usergroups_list` | `include_disabled` | 1 | — | minor / structural parameter |
| `usergroups_me` | `usergroup_id` | 2 | — | names the target resource — selects what the op touches |
| `usergroups_me` | `action` | 1 | — | minor / structural parameter |
| `usergroups_update` | `description` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `usergroups_update` | `usergroup_id` | 2 | — | names the target resource — selects what the op touches |
| `usergroups_update` | `channels` | 2 | — | names the target resource — selects what the op touches |
| `usergroups_update` | `name` | 2 | — | names the target resource — selects what the op touches |
| `usergroups_update` | `handle` | 1 | — | minor / structural parameter |
| `usergroups_users_update` | `usergroup_id` | 2 | — | names the target resource — selects what the op touches |
| `usergroups_users_update` | `users` | 2 | — | names the target resource — selects what the op touches |
| `users_search` | `query` | 5 | unbounded / no bound on scope | free-form query/command — unbounded reach; the whole payload |
| `users_search` | `limit` | 3 | large value | magnitude/count — larger value means broader effect |
