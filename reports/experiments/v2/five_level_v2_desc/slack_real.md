# Scan — slack:real

_kind=slack · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_desc · bands={'low': 19, 'medium': 67, 'high': 28, 'critical': 12, 'na': 194}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–25), scaled to this max.

## Inferred domain profile

- **mcp_kind**: communication platform
- **asset_meaning**: Slack channels and user groups
- **blast_radius_meaning**: The extent to which a tool can affect the membership or content of Slack channels and user groups, from modifying individual messages to changing group memberships or channel access.
- **dangerous_classes**: holds PII at scale, confidentiality-first: compensation discussions, unreleased strategy, live incident detail
- **irreversible_actions**: usergroups_users_update, conversations_join, conversations_leave
- **worked_example**: The tool 'usergroups_users_update' on the asset 'exec-private' can permanently change who has access to sensitive management conversations.

## Tool impact

| tool | impact |
| --- | --- |
| `channels_list` | 2 |
| `channels_me` | 2 |
| `conversations_add_message` | 4 |
| `conversations_history` | 3 |
| `conversations_join` | 5 |
| `conversations_leave` | 4 |
| `conversations_mark` | 2 |
| `conversations_replies` | 3 |
| `conversations_search_messages` | 3 |
| `conversations_unreads` | 3 |
| `usergroups_create` | 4 |
| `usergroups_list` | 2 |
| `usergroups_me` | 4 |
| `usergroups_update` | 4 |
| `usergroups_users_update` | 5 |
| `users_search` | 3 |

## Asset sensitivity

_Not scored in `impact_mode=five_level_v2_desc`: the organization's written description of this server states how severe each asset is, so no separate 1–5 sensitivity primitive is derived. The 20 assets below still form the matrix axis; the score is `blast × impact`._

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
| `usergroup-directory` | — |
| `user-group-membership` | — |
| `usergroup-metadata` | — |

## Risk matrix (score · band)

_Each cell shows `score (blast×impact)` — sensitivity is not scored in this mode; impact_mode=five_level_v2_desc, score ranges 0–25. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 9 (3×3) 🟡 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | 8 (4×2) 🟡 | 6 (2×3) 🟢 | 6 (2×3) 🟢 | 6 (2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `announcements` | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 12 (4×3) 🟡 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | 8 (4×2) 🟡 | 6 (2×3) 🟢 | 6 (2×3) 🟢 | 6 (2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `random` | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 12 (4×3) 🟡 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 12 (4×3) 🟡 | 6 (2×3) 🟢 | 6 (2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `engineering` | 4 (2×2) 🟢 | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 12 (4×3) 🟡 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 9 (3×3) 🟡 | 9 (3×3) 🟡 | 12 (4×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A |
| `incident-response` | 4 (2×2) 🟢 | N/A | 4 (1×4) 🟢 | 12 (4×3) 🟡 | 25 (5×5) 🔴 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 9 (3×3) 🟡 | 15 (5×3) 🟠 | 6 (2×3) 🟢 | N/A | N/A | N/A | N/A | 20 (4×5) 🔴 | N/A |
| `on-call` | 2 (1×2) 🟢 | N/A | 4 (1×4) 🟢 | 12 (4×3) 🟡 | 20 (4×5) 🔴 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 12 (4×3) 🟡 | 9 (3×3) 🟡 | 6 (2×3) 🟢 | N/A | N/A | N/A | N/A | 25 (5×5) 🔴 | N/A |
| `research-team` | 4 (2×2) 🟢 | N/A | 8 (2×4) 🟡 | 12 (4×3) 🟡 | 5 (1×5) 🟢 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 12 (4×3) 🟡 | 6 (2×3) 🟢 | 9 (3×3) 🟡 | N/A | N/A | N/A | N/A | 20 (4×5) 🔴 | N/A |
| `exec-private` | 2 (1×2) 🟢 | N/A | 4 (1×4) 🟢 | 12 (4×3) 🟡 | 25 (5×5) 🔴 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 12 (4×3) 🟡 | 15 (5×3) 🟠 | 6 (2×3) 🟢 | N/A | N/A | N/A | N/A | 25 (5×5) 🔴 | N/A |
| `hr-internal` | N/A | N/A | 4 (1×4) 🟢 | 12 (4×3) 🟡 | N/A | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 9 (3×3) 🟡 | 12 (4×3) 🟡 | 6 (2×3) 🟢 | N/A | N/A | N/A | N/A | 25 (5×5) 🔴 | N/A |
| `team-leads` | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 4 (1×4) 🟢 | 9 (3×3) 🟡 | 25 (5×5) 🔴 | 4 (1×4) 🟢 | 2 (1×2) 🟢 | 12 (4×3) 🟡 | 12 (4×3) 🟡 | 6 (2×3) 🟢 | N/A | N/A | 8 (2×4) 🟡 | 8 (2×4) 🟡 | 20 (4×5) 🔴 | N/A |
| `channel-messages` | N/A | N/A | 16 (4×4) 🟠 | 9 (3×3) 🟡 | N/A | N/A | N/A | 6 (2×3) 🟢 | 12 (4×3) 🟡 | 9 (3×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A |
| `message-reactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `read-markers` | N/A | N/A | N/A | N/A | N/A | N/A | 4 (2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×4) 🟡 | 4 (2×2) 🟢 | 8 (2×4) 🟡 | N/A | 20 (4×5) 🔴 | N/A |
| `agent-channel-membership` | N/A | N/A | N/A | N/A | 5 (1×5) 🟢 | 4 (1×4) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | N/A | N/A | N/A |
| `user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 15 (5×3) 🟠 |
| `channel-directory` | 6 (3×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 4 (2×2) 🟢 | N/A | 8 (2×4) 🟡 | 20 (4×5) 🔴 | N/A |
| `user-group-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 (1×4) 🟢 | 6 (3×2) 🟢 | 8 (2×4) 🟡 | N/A | 15 (3×5) 🟠 | N/A |
| `usergroup-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (4×2) 🟡 | N/A | 8 (2×4) 🟡 | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 1 | 1 | 1 | 3 | 1 | 1 | 4 | 2 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `announcements` | 1 | 1 | 1 | 4 | 1 | 1 | 4 | 2 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `random` | 1 | 1 | 1 | 4 | 1 | 1 | 1 | 4 | 2 | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `engineering` | 2 | 1 | 1 | 4 | 1 | 1 | 1 | 3 | 3 | 4 | N/A | N/A | N/A | N/A | N/A | N/A |
| `incident-response` | 2 | N/A | 1 | 4 | 5 | 1 | 1 | 3 | 5 | 2 | N/A | N/A | N/A | N/A | 4 | N/A |
| `on-call` | 1 | N/A | 1 | 4 | 4 | 1 | 1 | 4 | 3 | 2 | N/A | N/A | N/A | N/A | 5 | N/A |
| `research-team` | 2 | N/A | 2 | 4 | 1 | 1 | 1 | 4 | 2 | 3 | N/A | N/A | N/A | N/A | 4 | N/A |
| `exec-private` | 1 | N/A | 1 | 4 | 5 | 1 | 1 | 4 | 5 | 2 | N/A | N/A | N/A | N/A | 5 | N/A |
| `hr-internal` | N/A | N/A | 1 | 4 | N/A | 1 | 1 | 3 | 4 | 2 | N/A | N/A | N/A | N/A | 5 | N/A |
| `team-leads` | 1 | 1 | 1 | 3 | 5 | 1 | 1 | 4 | 4 | 2 | N/A | N/A | 2 | 2 | 4 | N/A |
| `channel-messages` | N/A | N/A | 4 | 3 | N/A | N/A | N/A | 2 | 4 | 3 | N/A | N/A | N/A | N/A | N/A | N/A |
| `message-reactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `read-markers` | N/A | N/A | N/A | N/A | N/A | N/A | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 2 | 2 | N/A | 4 | N/A |
| `agent-channel-membership` | N/A | N/A | N/A | N/A | 1 | 1 | N/A | N/A | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A |
| `user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 |
| `channel-directory` | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 2 | N/A | 2 | 4 | N/A |
| `user-group-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 3 | 2 | N/A | 3 | N/A |
| `usergroup-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | N/A | 2 | N/A | N/A |

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
| `channels_list` | `limit` | 4 | >= 999 | can amplify data retrieval volume |
| `channels_list` | `query` | 3 | — | potentially broadens search scope via free-form input |
| `channels_list` | `channel_types` | 2 | — | limits scope to predefined types |
| `channels_list` | `query_targets` | 2 | — | limits query to specific fields, but can broaden scope |
| `channels_list` | `cursor` | 1 | — | pagination control, no amplification risk |
| `channels_list` | `sort` | 1 | — | only affects order of results, no amplification risk |
| `channels_me` | `limit` | 4 | >= 999 | can amplify the volume of data retrieved |
| `channels_me` | `channel_types` | 3 | — | controls the scope of channels queried |
| `channels_me` | `cursor` | 1 | — | used for pagination, low risk |
| `conversations_add_message` | `text` | 5 | — | Fully controllable content that can be malicious |
| `conversations_add_message` | `blocks` | 4 | — | Can contain complex, potentially malicious JSON |
| `conversations_add_message` | `thread_ts` | 3 | — | Can target specific threads, potentially amplifying scope |
| `conversations_add_message` | `channel_id` | 2 | — | Identifies target channel but doesn't control content |
| `conversations_add_message` | `content_type` | 1 | — | Limits message format, not a direct risk vector |
| `conversations_history` | `limit` | 4 | unbounded (no LIMIT) | controls the magnitude of data fetched, potentially overwhel |
| `conversations_history` | `include_activity_messages` | 3 | — | can widen the scope of messages fetched |
| `conversations_history` | `channel_id` | 2 | — | merely names the target |
| `conversations_history` | `cursor` | 1 | — | used for pagination, no amplifying effect |
| `conversations_join` | `channel_id` | 2 | — | merely names the target |
| `conversations_leave` | `channel_id` | 2 | — | merely names the target |
| `conversations_mark` | `ts` | 3 | — | can be used to mark all messages as read if not provided, po |
| `conversations_mark` | `channel_id` | 2 | — | merely names the target |
| `conversations_replies` | `limit` | 4 | unbounded (no LIMIT) | controls the magnitude of data fetched, potentially overwhel |
| `conversations_replies` | `include_activity_messages` | 3 | true | can widen the scope of messages fetched |
| `conversations_replies` | `channel_id` | 2 | — | merely names the target |
| `conversations_replies` | `thread_ts` | 2 | — | identifies a specific thread or message, not inherently risk |
| `conversations_replies` | `cursor` | 1 | — | used for pagination, not inherently risky |
| `conversations_search_messages` | `limit` | 5 | >= 100 | high fan-out control, can amplify data exposure or server lo |
| `conversations_search_messages` | `search_query` | 5 | — | free-form query with potential for broad or sensitive search |
| `conversations_search_messages` | `filter_users_with` | 4 | — | DM/MPIM user filtering, high risk due to sensitive content |
| `conversations_search_messages` | `filter_in_im_or_mpim` | 3 | — | DM/MPIM targeting, higher risk due to sensitive content |
| `conversations_search_messages` | `filter_users_from` | 3 | — | user targeting, higher risk due to potential sensitive data  |
| `conversations_search_messages` | `cursor` | 2 | — | pagination control, low risk |
| `conversations_search_messages` | `filter_date_during` | 2 | — | potentially broad date range filter |
| `conversations_search_messages` | `filter_in_channel` | 2 | — | channel targeting, moderate risk |
| `conversations_search_messages` | `filter_date_after` | 1 | — | narrow date range filter |
| `conversations_search_messages` | `filter_date_before` | 1 | — | narrow date range filter |
| `conversations_search_messages` | `filter_date_on` | 1 | — | specific date filter, low risk |
| `conversations_search_messages` | `filter_threads_only` | 1 | — | thread filtering, low risk |
| `conversations_unreads` | `max_channels` | 5 | >= 100 | controls the breadth of channel fan-out, increasing load and |
| `conversations_unreads` | `include_muted` | 4 | — | widens scope to include muted channels, potentially exposing |
| `conversations_unreads` | `max_messages_per_channel` | 4 | >= 50 | increases data volume per channel, potentially overwhelming  |
| `conversations_unreads` | `include_messages` | 3 | — | controls whether full messages are returned, increasing data |
| `conversations_unreads` | `channel_types` | 2 | — | limits scope to specific channel types |
| `conversations_unreads` | `mentions_only` | 1 | — | narrows scope to only channels with mentions, reducing risk |
| `usergroups_create` | `handle` | 4 | — | can be used to impersonate official groups |
| `usergroups_create` | `channels` | 3 | >= 10 channels | can broaden access to multiple sensitive channels |
| `usergroups_create` | `name` | 2 | — | potentially misleading or confusing text |
| `usergroups_create` | `description` | 2 | — | potentially misleading or confusing text |
| `usergroups_list` | `include_users` | 5 | — | Potentially exposes all user IDs within each group, increasi |
| `usergroups_list` | `include_disabled` | 3 | — | May expose sensitive information about disabled groups |
| `usergroups_list` | `include_count` | 2 | — | Does not significantly affect security |
| `usergroups_me` | `usergroup_id` | 4 | — | can target any group, potentially leading to unauthorized ac |
| `usergroups_me` | `action` | 3 | — | controls the operation but is limited to predefined actions |
| `usergroups_update` | `channels` | 4 | >= 10 channels | Bulk fan-out to multiple channels |
| `usergroups_update` | `handle` | 3 | — | Changes how users interact with the group |
| `usergroups_update` | `description` | 2 | — | Potentially misleading text content |
| `usergroups_update` | `name` | 2 | — | Potentially misleading display name |
| `usergroups_update` | `usergroup_id` | 1 | — | Identifies the target group, no amplification |
| `usergroups_users_update` | `users` | 5 | >= 100 users | completely replaces member list, allowing bulk manipulation |
| `usergroups_users_update` | `usergroup_id` | 2 | — | merely identifies the target |
| `users_search` | `query` | 5 | — | Fully controllable input that can be used for enumeration or |
| `users_search` | `limit` | 3 | >= 100 | Can return a large number of results |
