# Scan — slack:real

_kind=slack · provenance=llm-scan · model_reviewed=True · impact_mode=five_level · bands={'low': 34, 'medium': 71, 'high': 50, 'critical': 5}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Inferred domain profile

- **mcp_kind**: communication platform
- **asset_meaning**: channels and user groups within a communication workspace
- **blast_radius_meaning**: the extent to which a tool can affect messages or memberships across channels and user groups
- **dangerous_classes**: holds sensitive information, is critical for operations
- **irreversible_actions**: permanently deletes messages from a channel, removes all members from a user group
- **worked_example**: conversations_add_message on incident-response: Adding a message to the private 'incident-response' channel could trigger immediate action and is sensitive due to its critical nature.

## Tool impact

| tool | impact |
| --- | --- |
| `channels_list` | 1 |
| `channels_me` | 1 |
| `conversations_add_message` | 3 |
| `conversations_history` | 3 |
| `conversations_join` | 1 |
| `conversations_leave` | 1 |
| `conversations_mark` | 1 |
| `conversations_replies` | 3 |
| `conversations_search_messages` | 3 |
| `conversations_unreads` | 3 |
| `usergroups_create` | 1 |
| `usergroups_list` | 1 |
| `usergroups_me` | 3 |
| `usergroups_update` | 3 |
| `usergroups_users_update` | 5 |
| `users_search` | 2 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `general` | 1 |
| `announcements` | 1 |
| `random` | 1 |
| `engineering` | 3 |
| `incident-response` | 4 |
| `on-call` | 4 |
| `research-team` | 4 |
| `exec-private` | 4 |
| `hr-internal` | 4 |
| `team-leads` | 4 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 1 (1×1×1) 🟢 | 2 (1×2×1) 🟢 | 3 (1×1×3) 🟢 | 12 (1×4×3) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 6 (1×2×3) 🟢 | 12 (1×4×3) 🟢 | 9 (1×3×3) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 3 (1×1×3) 🟢 | 3 (1×1×3) 🟢 | 5 (1×1×5) 🟢 | 2 (1×1×2) 🟢 |
| `announcements` | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 3 (1×1×3) 🟢 | 9 (1×3×3) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 9 (1×3×3) 🟢 | 12 (1×4×3) 🟢 | 6 (1×2×3) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 3 (1×1×3) 🟢 | 3 (1×1×3) 🟢 | 5 (1×1×5) 🟢 | 2 (1×1×2) 🟢 |
| `random` | 1 (1×1×1) 🟢 | 2 (1×2×1) 🟢 | 3 (1×1×3) 🟢 | 9 (1×3×3) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 4 (1×4×1) 🟢 | 6 (1×2×3) 🟢 | 9 (1×3×3) 🟢 | 6 (1×2×3) 🟢 | 1 (1×1×1) 🟢 | 1 (1×1×1) 🟢 | 3 (1×1×3) 🟢 | 3 (1×1×3) 🟢 | 5 (1×1×5) 🟢 | 2 (1×1×2) 🟢 |
| `engineering` | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 9 (3×1×3) 🟢 | 27 (3×3×3) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 12 (3×4×1) 🟢 | 18 (3×2×3) 🟢 | 27 (3×3×3) 🟢 | 27 (3×3×3) 🟢 | 3 (3×1×1) 🟢 | 3 (3×1×1) 🟢 | 9 (3×1×3) 🟢 | 9 (3×1×3) 🟢 | 15 (3×1×5) 🟢 | 6 (3×1×2) 🟢 |
| `incident-response` | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 36 (4×3×3) 🟡 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 24 (4×2×3) 🟢 | 36 (4×3×3) 🟡 | 24 (4×2×3) 🟢 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 8 (4×1×2) 🟢 |
| `on-call` | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 36 (4×3×3) 🟡 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 24 (4×2×3) 🟢 | 48 (4×4×3) 🟡 | 24 (4×2×3) 🟢 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 8 (4×1×2) 🟢 |
| `research-team` | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 48 (4×4×3) 🟡 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 24 (4×2×3) 🟢 | 48 (4×4×3) 🟡 | 24 (4×2×3) 🟢 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 8 (4×1×2) 🟢 |
| `exec-private` | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 36 (4×3×3) 🟡 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 24 (4×2×3) 🟢 | 36 (4×3×3) 🟡 | 24 (4×2×3) 🟢 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 8 (4×1×2) 🟢 |
| `hr-internal` | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 48 (4×4×3) 🟡 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 24 (4×2×3) 🟢 | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 8 (4×1×2) 🟢 |
| `team-leads` | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 48 (4×4×3) 🟡 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 16 (4×4×1) 🟢 | 36 (4×3×3) 🟡 | 36 (4×3×3) 🟡 | 24 (4×2×3) 🟢 | 4 (4×1×1) 🟢 | 4 (4×1×1) 🟢 | 12 (4×1×3) 🟢 | 12 (4×1×3) 🟢 | 20 (4×1×5) 🟢 | 8 (4×1×2) 🟢 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | channels_list | channels_me | conversations_add_message | conversations_history | conversations_join | conversations_leave | conversations_mark | conversations_replies | conversations_search_messages | conversations_unreads | usergroups_create | usergroups_list | usergroups_me | usergroups_update | usergroups_users_update | users_search |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `general` | 1 | 2 | 1 | 4 | 1 | 1 | 4 | 2 | 4 | 3 | 1 | 1 | 1 | 1 | 1 | 1 |
| `announcements` | 1 | 1 | 1 | 3 | 1 | 1 | 4 | 3 | 4 | 2 | 1 | 1 | 1 | 1 | 1 | 1 |
| `random` | 1 | 2 | 1 | 3 | 1 | 1 | 4 | 2 | 3 | 2 | 1 | 1 | 1 | 1 | 1 | 1 |
| `engineering` | 1 | 1 | 1 | 3 | 1 | 1 | 4 | 2 | 3 | 3 | 1 | 1 | 1 | 1 | 1 | 1 |
| `incident-response` | 1 | 1 | 1 | 3 | 1 | 1 | 4 | 2 | 3 | 2 | 1 | 1 | 1 | 1 | 1 | 1 |
| `on-call` | 1 | 1 | 1 | 3 | 1 | 1 | 4 | 2 | 4 | 2 | 1 | 1 | 1 | 1 | 1 | 1 |
| `research-team` | 1 | 1 | 1 | 4 | 1 | 1 | 4 | 2 | 4 | 2 | 1 | 1 | 1 | 1 | 1 | 1 |
| `exec-private` | 1 | 1 | 1 | 3 | 1 | 1 | 4 | 2 | 3 | 2 | 1 | 1 | 1 | 1 | 1 | 1 |
| `hr-internal` | 1 | 1 | 1 | 4 | 1 | 1 | 4 | 2 | 3 | 3 | 1 | 1 | 1 | 1 | 1 | 1 |
| `team-leads` | 1 | 1 | 1 | 4 | 1 | 1 | 4 | 3 | 3 | 2 | 1 | 1 | 1 | 1 | 1 | 1 |

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
