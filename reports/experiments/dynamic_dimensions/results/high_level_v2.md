# High-level dimensions: no look inside any call

Same 9 organisations, 21 kinds of strange usage and scoring as the exact-content search. The dimensions here never read tool inputs or the specific asset: only which tool, its operation, the asset TYPE implied by the tool, time, volume, sessions, and (pool A) a general client and network.

## Pool A: tool + time + volume + general client/network

### At <= 2 flagged agent-days per day: 50% (exact-content reference 57%)

Chosen, in order: next_tool_self, client_family_new, tool_repeat_10m, networks_1h, tool_new_org_rare, rate_1h, network_range_new, writes_today, tool_new_tool_peer_rare, client_families_1h

| kind | mild | medium | strong |
|---|---|---|---|
| burst | 7% | 57% | 84% |
| cancel_storm | 4% | 25% | 80% |
| client_switch | 90% | 90% | 96% |
| content_dump | 13% | 11% | 26% |
| dormant_wake | – | 67% | – |
| fan_out | 1% | 4% | 49% |
| long_span | 40% | 46% | 45% |
| loop | 1% | 56% | 78% |
| mode_switch | 55% | 64% | 50% |
| new_origin | 98% | 97% | 100% |
| off_hours | 1% | 2% | 4% |
| off_role_tool | 83% | 92% | 89% |
| over_fetch | 6% | 4% | 7% |
| page_walk | 22% | 83% | 90% |
| protocol_skip | 3% | 21% | 65% |
| recipient_blast | 65% | 61% | 68% |
| repeated_habit | 30% | 45% | 70% |
| sensitivity_escalation | 2% | 1% | 2% |
| shared_credential | 98% | 100% | 100% |
| slow_creep | – | 82% | – |
| workflow_skip | 49% | 62% | 56% |

### At <= 4 flagged agent-days per day: 60% (exact-content reference 71%)

Chosen, in order: next_tool_self, tool_repeat_10m, network_range_new, client_family_new, calls_today, writes_today, tool_new_org_rare, session_duration, networks_1h, client_families_1h, asset_types_today

| kind | mild | medium | strong |
|---|---|---|---|
| burst | 13% | 54% | 91% |
| cancel_storm | 41% | 84% | 95% |
| client_switch | 92% | 94% | 99% |
| content_dump | 17% | 22% | 30% |
| dormant_wake | – | 66% | – |
| fan_out | 6% | 44% | 71% |
| long_span | 52% | 59% | 55% |
| loop | 6% | 75% | 94% |
| mode_switch | 61% | 69% | 57% |
| new_origin | 97% | 99% | 99% |
| off_hours | 8% | 7% | 10% |
| off_role_tool | 93% | 99% | 97% |
| over_fetch | 8% | 8% | 9% |
| page_walk | 50% | 90% | 100% |
| protocol_skip | 8% | 27% | 57% |
| recipient_blast | 73% | 67% | 74% |
| repeated_habit | 57% | 85% | 88% |
| sensitivity_escalation | 6% | 6% | 3% |
| shared_credential | 99% | 100% | 100% |
| slow_creep | – | 95% | – |
| workflow_skip | 61% | 74% | 70% |

## Pool B: tool + time + volume only

### At <= 2 flagged agent-days per day: 39% (exact-content reference 57%)

Chosen, in order: next_tool_self, calls_today, rate_1h, tool_new_org_rare, writes_today, asset_type_new, tool_repeat_10m

| kind | mild | medium | strong |
|---|---|---|---|
| burst | 7% | 68% | 92% |
| cancel_storm | 4% | 27% | 89% |
| client_switch | 6% | 26% | 64% |
| content_dump | 13% | 11% | 25% |
| dormant_wake | – | 40% | – |
| fan_out | 0% | 6% | 53% |
| long_span | 38% | 45% | 45% |
| loop | 2% | 65% | 90% |
| mode_switch | 51% | 64% | 47% |
| new_origin | 3% | 6% | 20% |
| off_hours | 5% | 2% | 3% |
| off_role_tool | 87% | 90% | 90% |
| over_fetch | 6% | 6% | 7% |
| page_walk | 29% | 83% | 97% |
| protocol_skip | 3% | 28% | 77% |
| recipient_blast | 64% | 58% | 66% |
| repeated_habit | 40% | 55% | 76% |
| sensitivity_escalation | 2% | 0% | 1% |
| shared_credential | 7% | 12% | 41% |
| slow_creep | – | 82% | – |
| workflow_skip | 47% | 59% | 55% |

### At <= 4 flagged agent-days per day: 50% (exact-content reference 71%)

Chosen, in order: next_tool_self, tool_repeat_10m, calls_today, tool_new_org_rare, impact_sum_today, writes_today, rate_1h, asset_type_new, cancels_1h, asset_types_today, tool_recency_gap, tool_new_tool_peer_rare

| kind | mild | medium | strong |
|---|---|---|---|
| burst | 14% | 73% | 99% |
| cancel_storm | 63% | 85% | 100% |
| client_switch | 18% | 54% | 90% |
| content_dump | 16% | 15% | 33% |
| dormant_wake | – | 49% | – |
| fan_out | 6% | 11% | 64% |
| long_span | 52% | 58% | 55% |
| loop | 7% | 72% | 99% |
| mode_switch | 61% | 71% | 57% |
| new_origin | 6% | 12% | 40% |
| off_hours | 9% | 6% | 10% |
| off_role_tool | 98% | 97% | 96% |
| over_fetch | 8% | 7% | 10% |
| page_walk | 43% | 90% | 97% |
| protocol_skip | 12% | 39% | 90% |
| recipient_blast | 73% | 69% | 74% |
| repeated_habit | 68% | 92% | 92% |
| sensitivity_escalation | 7% | 4% | 3% |
| shared_credential | 10% | 20% | 52% |
| slow_creep | – | 93% | – |
| workflow_skip | 63% | 72% | 66% |

## Best single high-level dimension per kind (top-0.2% events, mean over organisations)

| kind | best | 2nd | 3rd |
|---|---|---|---|
| burst | sessions_1h 73% | inits_1h 73% | parallel_sessions 67% |
| cancel_storm | list_to_call_delay 99% | cancels_1h 88% | session_duration 87% |
| client_switch | ua_family_new 83% | client_family_new 83% | client_families_1h 67% |
| content_dump | next_tool_self 24% | peer_next_tool 23% | tool_new_org_rare 15% |
| dormant_wake | network_range_new 54% | op_transition 45% | tool_new_org_rare 40% |
| fan_out | session_count_distance 47% | session_duration 43% | session_length 43% |
| long_span | next_tool_self 60% | peer_next_tool 52% | tool_new_org_rare 42% |
| loop | tool_rate_1m 67% | session_count_distance 67% | tool_repeat_in_session 64% |
| mode_switch | next_tool_self 67% | peer_next_tool 63% | tool_new_org_rare 52% |
| new_origin | network_range_new 100% | networks_1h 71% | context_new_on_write 26% |
| off_hours | hour_of_week 71% | call_without_list 9% | next_tool_self 9% |
| off_role_tool | next_tool_self 99% | tool_new_org_rare 90% | peer_next_tool 86% |
| over_fetch | next_tool_self 7% | tool_new_org_rare 6% | peer_next_tool 5% |
| page_walk | tool_rate_1m 94% | tool_repeat_in_session 86% | tool_repeat_10m 86% |
| protocol_skip | call_without_init 100% | sessions_1h 62% | rate_1h 41% |
| recipient_blast | next_tool_self 75% | peer_next_tool 66% | tool_new_org_rare 60% |
| repeated_habit | tool_periodicity 88% | fano_1h 85% | tool_rate_1m 80% |
| sensitivity_escalation | peer_next_tool 6% | tool_recency_gap 5% | op_escalation_session 5% |
| shared_credential | client_family_new 97% | network_range_new 91% | client_families_1h 75% |
| slow_creep | call_without_list 94% | tool_recency_gap 94% | next_tool_trigram 93% |
| workflow_skip | write_first 92% | next_tool_self 78% | peer_next_tool 78% |

## False alarms of the chosen dimensions

| dimension | benign messages flagged | worst legitimate change |
|---|---|---|
| asset_type_new | 0.01% | role_change 0.3% |
| asset_types_today | 0.21% | role_change 1.8% |
| calls_today | 0.20% | night_work 1.4% |
| cancels_1h | 0.02% | team_transfer 0.0% |
| client_families_1h | 0.03% | new_network 0.2% |
| client_family_new | 0.00% | new_network 0.0% |
| impact_sum_today | 0.18% | night_work 1.2% |
| network_range_new | 0.00% | new_network 0.8% |
| networks_1h | 0.16% | role_change 5.1% |
| next_tool_self | 0.20% | role_change 5.3% |
| rate_1h | 0.15% | night_work 0.8% |
| session_duration | 0.16% | role_change 0.7% |
| tool_new_org_rare | 0.02% | role_change 0.6% |
| tool_new_tool_peer_rare | 0.01% | role_change 0.6% |
| tool_recency_gap | 0.20% | back_from_vacation 1.9% |
| tool_repeat_10m | 0.14% | night_work 1.8% |
| writes_today | 0.18% | role_change 3.1% |
