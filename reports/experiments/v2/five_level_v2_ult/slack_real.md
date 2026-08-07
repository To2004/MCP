# Scan — slack:real

_kind=slack · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_ult · bands={'low': 62, 'medium': 41, 'high': 28, 'critical': 0, 'na': 173}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Inferred domain profile

- **mcp_kind**: communication platform
- **asset_meaning**: Slack channels and user groups
- **blast_radius_meaning**: The extent to which a tool can affect the membership or content of Slack channels and user groups, from affecting individual messages to altering access control for sensitive channels.
- **dangerous_classes**: holds sensitive discussions (e.g., compensation, unreleased strategy), contains PII data (user directory)
- **worked_example**: The tool 'conversations_join' paired with the asset 'exec-private' can escalate severity because joining a high-sensitivity channel like exec-private allows access to confidential discussions.

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
| `usergroups_me` | 4 |
| `usergroups_update` | 4 |
| `usergroups_users_update` | 4 |
| `users_search` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `exec-private` | 4 |
| `hr-internal` | 4 |
| `incident-response` | 4 |
| `on-call` | 4 |
| `team-leads` | 4 |
| `channel-messages` | 4 |
| `usergroup-membership` | 4 |
| `user-group-membership` | 4 |
| `agent-channel-membership` | 4 |
| `user-directory` | 4 |
| `engineering` | 3 |
| `research-team` | 3 |
| `message-reactions` | 2 |
| `read-markers` | 2 |
| `channel-directory` | 2 |
| `usergroup-directory` | 2 |
| `usergroup-metadata` | 2 |
| `general` | 1 |
| `announcements` | 1 |
| `random` | 1 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_ult, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 4 (1×1×4) 🟢 | 12 (1×4×3) 🟢 | 4 (1×1×4) 🟢 | 4 (1×1×4) 🟢 | 2 (1×1×2) 🟢 | 6 (1×2×3) 🟢 | 9 (1×3×3) 🟢 | 6 (1×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `announcements` | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 4 (1×1×4) 🟢 | 12 (1×4×3) 🟢 | 4 (1×1×4) 🟢 | 4 (1×1×4) 🟢 | 2 (1×1×2) 🟢 | 9 (1×3×3) 🟢 | 12 (1×4×3) 🟢 | 3 (1×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `random` | 2 (1×1×2) 🟢 | 2 (1×1×2) 🟢 | 4 (1×1×4) 🟢 | 12 (1×4×3) 🟢 | 4 (1×1×4) 🟢 | 4 (1×1×4) 🟢 | 4 (1×2×2) 🟢 | 6 (1×2×3) 🟢 | 12 (1×4×3) 🟢 | 6 (1×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `engineering` | 6 (3×1×2) 🟢 | 12 (3×2×2) 🟢 | 12 (3×1×4) 🟢 | 36 (3×4×3) 🟡 | 48 (3×4×4) 🟡 | 12 (3×1×4) 🟢 | 24 (3×4×2) 🟢 | 27 (3×3×3) 🟢 | 36 (3×4×3) 🟡 | 18 (3×2×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A |
| `incident-response` | 16 (4×2×2) 🟢 | 8 (4×1×2) 🟢 | 48 (4×3×4) 🟡 | 48 (4×4×3) 🟡 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 16 (4×2×2) 🟢 | 36 (4×3×3) 🟡 | 48 (4×4×3) 🟡 | 48 (4×4×3) 🟡 | N/A | N/A | N/A | N/A | 80 (4×5×4) 🟠 | N/A |
| `on-call` | 16 (4×2×2) 🟢 | 8 (4×1×2) 🟢 | 48 (4×3×4) 🟡 | 36 (4×3×3) 🟡 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 32 (4×4×2) 🟢 | 36 (4×3×3) 🟡 | 48 (4×4×3) 🟡 | 48 (4×4×3) 🟡 | N/A | N/A | N/A | N/A | 80 (4×5×4) 🟠 | N/A |
| `research-team` | 12 (3×2×2) 🟢 | 12 (3×2×2) 🟢 | 12 (3×1×4) 🟢 | 36 (3×4×3) 🟡 | 48 (3×4×4) 🟡 | 12 (3×1×4) 🟢 | 24 (3×4×2) 🟢 | 36 (3×4×3) 🟡 | 27 (3×3×3) 🟢 | 18 (3×2×3) 🟢 | N/A | N/A | N/A | N/A | 24 (3×2×4) 🟢 | N/A |
| `exec-private` | 16 (4×2×2) 🟢 | 8 (4×1×2) 🟢 | 48 (4×3×4) 🟡 | 48 (4×4×3) 🟡 | 80 (4×5×4) 🟠 | 48 (4×3×4) 🟡 | 16 (4×2×2) 🟢 | 48 (4×4×3) 🟡 | 48 (4×4×3) 🟡 | 24 (4×2×3) 🟢 | N/A | N/A | N/A | N/A | 80 (4×5×4) 🟠 | N/A |
| `hr-internal` | 16 (4×2×2) 🟢 | 8 (4×1×2) 🟢 | 48 (4×3×4) 🟡 | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 8 (4×1×2) 🟢 | 48 (4×4×3) 🟡 | 48 (4×4×3) 🟡 | 24 (4×2×3) 🟢 | N/A | N/A | N/A | N/A | 80 (4×5×4) 🟠 | N/A |
| `team-leads` | 16 (4×2×2) 🟢 | 8 (4×1×2) 🟢 | 48 (4×3×4) 🟡 | 48 (4×4×3) 🟡 | 64 (4×4×4) 🟡 | 48 (4×3×4) 🟡 | 16 (4×2×2) 🟢 | 48 (4×4×3) 🟡 | 48 (4×4×3) 🟡 | 24 (4×2×3) 🟢 | N/A | N/A | 48 (4×3×4) 🟡 | N/A | 80 (4×5×4) 🟠 | N/A |
| `channel-messages` | N/A | N/A | 48 (4×3×4) 🟡 | 48 (4×4×3) 🟡 | 48 (4×3×4) 🟡 | N/A | N/A | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 48 (4×4×3) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A |
| `message-reactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `read-markers` | N/A | N/A | N/A | N/A | N/A | N/A | 16 (2×4×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 48 (4×3×4) 🟡 | 16 (4×2×2) 🟢 | 48 (4×3×4) 🟡 | N/A | 80 (4×5×4) 🟠 | N/A |
| `agent-channel-membership` | N/A | 32 (4×4×2) 🟢 | N/A | N/A | 48 (4×3×4) 🟡 | 48 (4×3×4) 🟡 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 60 (4×5×3) 🟡 |
| `channel-directory` | 16 (2×4×2) 🟢 | 8 (2×2×2) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 8 (2×1×4) 🟢 | 16 (2×4×2) 🟢 | N/A | 16 (2×2×4) 🟢 | 32 (2×4×4) 🟢 | N/A |
| `usergroup-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 16 (2×2×4) 🟢 | 16 (2×4×2) 🟢 | N/A | 8 (2×1×4) 🟢 | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 1 | 1 | 1 | 4 | 1 | 1 | 1 | 2 | 3 | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `announcements` | 1 | 1 | 1 | 4 | 1 | 1 | 1 | 3 | 4 | 1 | N/A | N/A | N/A | N/A | N/A | N/A |
| `random` | 1 | 1 | 1 | 4 | 1 | 1 | 2 | 2 | 4 | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `engineering` | 1 | 2 | 1 | 4 | 4 | 1 | 4 | 3 | 4 | 2 | N/A | N/A | N/A | N/A | N/A | N/A |
| `incident-response` | 2 | 1 | 3 | 4 | 5 | 3 | 2 | 3 | 4 | 4 | N/A | N/A | N/A | N/A | 5 | N/A |
| `on-call` | 2 | 1 | 3 | 3 | 5 | 3 | 4 | 3 | 4 | 4 | N/A | N/A | N/A | N/A | 5 | N/A |
| `research-team` | 2 | 2 | 1 | 4 | 4 | 1 | 4 | 4 | 3 | 2 | N/A | N/A | N/A | N/A | 2 | N/A |
| `exec-private` | 2 | 1 | 3 | 4 | 5 | 3 | 2 | 4 | 4 | 2 | N/A | N/A | N/A | N/A | 5 | N/A |
| `hr-internal` | 2 | 1 | 3 | 4 | 4 | 3 | 1 | 4 | 4 | 2 | N/A | N/A | N/A | N/A | 5 | N/A |
| `team-leads` | 2 | 1 | 3 | 4 | 4 | 3 | 2 | 4 | 4 | 2 | N/A | N/A | 3 | N/A | 5 | N/A |
| `channel-messages` | N/A | N/A | 3 | 4 | 3 | N/A | N/A | 3 | 3 | 4 | N/A | N/A | N/A | N/A | N/A | N/A |
| `message-reactions` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `read-markers` | N/A | N/A | N/A | N/A | N/A | N/A | 4 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-membership` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3 | 2 | 3 | N/A | 5 | N/A |
| `agent-channel-membership` | N/A | 4 | N/A | N/A | 3 | 3 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `user-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 |
| `channel-directory` | 4 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| `usergroup-directory` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 1 | 4 | N/A | 2 | 4 | N/A |
| `usergroup-metadata` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 2 | 4 | N/A | 1 | N/A | N/A |

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
| `channels_list` | `query` | 3 | — | allows for broad or specific channel filtering |
| `channels_list` | `channel_types` | 2 | — | limits scope to predefined types |
| `channels_list` | `query_targets` | 2 | — | limits query scope to predefined fields |
| `channels_list` | `cursor` | 1 | — | pagination control, no amplification risk |
| `channels_list` | `sort` | 1 | — | only affects order, not volume or content |
| `channels_me` | `limit` | 4 | >= 999 | can amplify the volume of data retrieved |
| `channels_me` | `channel_types` | 3 | — | controls the scope of channels queried |
| `channels_me` | `cursor` | 1 | — | used for pagination, low risk |
| `conversations_add_message` | `text` | 5 | — | Fully controlled payload for the message content |
| `conversations_add_message` | `blocks` | 4 | — | Can contain arbitrary JSON for rich message formatting |
| `conversations_add_message` | `thread_ts` | 3 | — | Can target specific threads, potentially amplifying scope |
| `conversations_add_message` | `channel_id` | 2 | — | Identifies the target channel but does not control content |
| `conversations_add_message` | `content_type` | 1 | — | Limits message format, no direct amplification of risk |
| `conversations_history` | `limit` | 5 | unbounded (no LIMIT) | controls the magnitude of data fetched, potentially overwhel |
| `conversations_history` | `include_activity_messages` | 3 | — | can widen the scope of data retrieved |
| `conversations_history` | `channel_id` | 2 | — | merely names the target |
| `conversations_history` | `cursor` | 1 | — | used for pagination, no amplification of risk |
| `conversations_join` | `channel_id` | 2 | — | merely names the target |
| `conversations_leave` | `channel_id` | 2 | — | merely names the target |
| `conversations_mark` | `ts` | 3 | — | can be used to mark all messages as read if not provided, po |
| `conversations_mark` | `channel_id` | 2 | — | merely names the target |
| `conversations_replies` | `limit` | 4 | unbounded (no LIMIT) | controls the magnitude of data fetched, unbounded can overwh |
| `conversations_replies` | `include_activity_messages` | 3 | — | can widen the scope of messages fetched |
| `conversations_replies` | `channel_id` | 2 | — | merely names the target |
| `conversations_replies` | `thread_ts` | 2 | — | identifies a specific thread or message, not inherently risk |
| `conversations_replies` | `cursor` | 1 | — | used for pagination, not inherently risky |
| `conversations_search_messages` | `limit` | 5 | >= 100 | high fan-out control, can amplify call's impact significantl |
| `conversations_search_messages` | `search_query` | 5 | — | free-form query with full caller control, high risk of abuse |
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
| `conversations_unreads` | `include_messages` | 3 | — | controls whether actual messages are returned, increasing da |
| `conversations_unreads` | `channel_types` | 2 | — | limits scope to specific channel types |
| `conversations_unreads` | `mentions_only` | 1 | — | narrows scope to only channels with mentions, reducing risk |
| `usergroups_create` | `handle` | 4 | — | can be used for impersonation or phishing attempts |
| `usergroups_create` | `channels` | 3 | >= 10 channels | can broaden access to multiple sensitive channels |
| `usergroups_create` | `name` | 2 | — | potentially misleading group name |
| `usergroups_create` | `description` | 2 | — | potentially misleading or confusing text |
| `usergroups_list` | `include_users` | 5 | — | Potentially exposes a large list of user IDs, increasing ris |
| `usergroups_list` | `include_disabled` | 3 | — | May expose sensitive information about archived groups |
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
