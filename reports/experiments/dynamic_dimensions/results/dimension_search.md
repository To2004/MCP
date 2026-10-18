# Dimension search: 60 dimensions, 21 kinds of strange usage, 9 scenarios

## One set for all scenarios, at <= 2.0 alerted agent-days per day

| step | dimension added | mean detection over 9 scenarios |
|---|---|---|
| 1 | arg_keys_new | 28% |
| 2 | which_new_org_rare | 38% |
| 3 | user_agent_new | 47% |
| 4 | which_new_peer_rare | 48% |
| 5 | next_tool_self | 49% |
| 6 | rate_1h | 51% |
| 7 | addresses_1h | 54% |
| 8 | action_value_new | 55% |
| 9 | tool_new_peer_rare | 55% |
| 10 | reach_today | 56% |
| 11 | sens_above_own_max | 57% |
| 12 | client_context | 57% |
| 13 | call_without_list | 57% |
| 14 | call_without_init | 57% |
| 15 | addresses_in_session | 57% |
| 16 | retry_after_cancel | 57% |

Detection of the final set by kind and intensity (mild / medium / strong):

| kind | mild | medium | strong |
|---|---|---|---|
| burst | 3% | 33% | 66% |
| cancel_storm | 8% | 14% | 67% |
| client_switch | 87% | 84% | 94% |
| content_dump | 33% | 33% | 43% |
| dormant_wake | – | 63% | – |
| fan_out | 66% | 86% | 96% |
| long_span | 45% | 56% | 46% |
| loop | 1% | 18% | 59% |
| mode_switch | 86% | 83% | 81% |
| new_origin | 49% | 73% | 83% |
| off_hours | 1% | 1% | 3% |
| off_role_tool | 83% | 86% | 89% |
| over_fetch | 20% | 25% | 28% |
| page_walk | 31% | 80% | 90% |
| protocol_skip | 2% | 11% | 51% |
| recipient_blast | 72% | 60% | 70% |
| repeated_habit | 82% | 85% | 87% |
| sensitivity_escalation | 56% | 44% | 56% |
| shared_credential | 98% | 100% | 100% |
| slow_creep | – | 90% | – |
| workflow_skip | 46% | 53% | 45% |

## One set for all scenarios, at <= 4.0 alerted agent-days per day

| step | dimension added | mean detection over 9 scenarios |
|---|---|---|
| 1 | arg_keys_new | 28% |
| 2 | which_new | 44% |
| 3 | client_context | 55% |
| 4 | identical_10m | 63% |
| 5 | addresses_1h | 66% |
| 6 | calls_today | 67% |
| 7 | reach_today | 69% |
| 8 | user_agent_new | 70% |
| 9 | who_new | 70% |
| 10 | which_new_peer_rare | 70% |
| 11 | action_value_new | 70% |
| 12 | tool_new_peer_rare | 71% |
| 13 | call_without_list | 71% |
| 14 | call_without_init | 71% |
| 15 | addresses_in_session | 71% |
| 16 | unpopular_share_day | 71% |

Detection of the final set by kind and intensity (mild / medium / strong):

| kind | mild | medium | strong |
|---|---|---|---|
| burst | 11% | 33% | 82% |
| cancel_storm | 32% | 80% | 93% |
| client_switch | 94% | 92% | 97% |
| content_dump | 55% | 63% | 62% |
| dormant_wake | – | 63% | – |
| fan_out | 90% | 93% | 99% |
| long_span | 55% | 60% | 48% |
| loop | 59% | 76% | 96% |
| mode_switch | 93% | 91% | 93% |
| new_origin | 64% | 90% | 96% |
| off_hours | 5% | 7% | 3% |
| off_role_tool | 88% | 92% | 92% |
| over_fetch | 33% | 41% | 54% |
| page_walk | 58% | 90% | 93% |
| protocol_skip | 6% | 12% | 59% |
| recipient_blast | 87% | 89% | 87% |
| repeated_habit | 89% | 88% | 96% |
| sensitivity_escalation | 84% | 86% | 85% |
| shared_credential | 100% | 100% | 100% |
| slow_creep | – | 99% | – |
| workflow_skip | 44% | 59% | 53% |

## Picked inside each scenario (greedy top 10)

| dimension | scenarios (of 9) | mean position |
|---|---|---|
| arg_keys_new | 9 | 1.0 |
| user_agent_new | 8 | 4.1 |
| who_new | 7 | 6.6 |
| which_new | 6 | 2.2 |
| when_span | 6 | 7.3 |
| tool_new_peer_rare | 6 | 8.7 |
| action_value_new | 5 | 6.2 |
| who_count | 5 | 6.6 |
| call_without_list | 5 | 7.8 |
| call_without_init | 5 | 8.8 |
| client_context | 4 | 3.0 |
| address_new | 3 | 2.3 |
| addresses_in_session | 3 | 9.3 |
| unpopular_share_day | 2 | 3.0 |
| which_new_peer_rare | 2 | 3.5 |
| addresses_1h | 2 | 4.0 |
| sens_above_own_max | 2 | 5.0 |
| next_tool_self | 2 | 8.5 |
| identical_in_session | 2 | 10.0 |
| op_transition | 1 | 4.0 |
| request_bytes | 1 | 4.0 |
| retry_after_cancel | 1 | 4.0 |
| rate_1h | 1 | 5.0 |
| distinct_who_day | 1 | 9.0 |
| session_length | 1 | 10.0 |

## Best single dimension per kind (top-0.2% events; mean over scenarios where the kind exists)

| kind | best | 2nd | 3rd |
|---|---|---|---|
| burst | sessions_1h 73% | inits_1h 73% | parallel_sessions 67% |
| cancel_storm | list_to_call_delay 99% | retry_after_cancel 97% | identical_in_session 89% |
| client_switch | user_agent_new 83% | client_new 83% | client_context 82% |
| content_dump | request_bytes 76% | arg_keys_new 63% | next_tool_self 24% |
| dormant_wake | client_new 66% | client_context 65% | address_new 54% |
| fan_out | which_per_session 99% | which_new_org_rare 96% | which_new 96% |
| long_span | next_tool_self 60% | arg_keys_new 54% | tool_new_peer_rare 41% |
| loop | identical_in_session 93% | identical_10m 93% | rate_1m 63% |
| mode_switch | arg_keys_new 88% | next_tool_self 67% | tool_new_peer_rare 50% |
| new_origin | address_new 100% | client_context 74% | addresses_1h 71% |
| off_hours | hour_of_week 71% | next_tool_self 9% | next_tool_trigram 9% |
| off_role_tool | next_tool_self 99% | arg_keys_new 90% | tool_new_peer_rare 89% |
| over_fetch | how_much_value 46% | arg_keys_new 42% | reach_today 41% |
| page_walk | arg_keys_new 86% | fano_1h 74% | rate_1m 70% |
| protocol_skip | sessions_1h 62% | rate_1h 41% | parallel_sessions 38% |
| recipient_blast | arg_keys_new 89% | next_tool_self 75% | tool_new_peer_rare 60% |
| repeated_habit | monotone_run 97% | fano_1h 85% | which_per_session 83% |
| sensitivity_escalation | which_new 87% | which_new_peer_rare 86% | which_new_org_rare 86% |
| shared_credential | client_context 100% | address_new 100% | client_new 97% |
| slow_creep | next_tool_trigram 93% | which_new_org_rare 91% | which_new 91% |
| workflow_skip | write_first 92% | next_tool_self 78% | next_tool_trigram 74% |

## False alarms on legitimate change (share of those messages flagged, mean over scenarios)

| dimension | benign | back_from_vacation | client_upgrade | new_hire | new_network | night_work | redeploy | role_change | team_transfer |
|---|---|---|---|---|---|---|---|---|---|
| rate_1m | 0.17% | 0.16% | 0.16% | 0.18% | 0.12% | 6.07% | 0.17% | 0.21% | 0.19% |
| rate_10m | 0.15% | 0.22% | 0.14% | 0.16% | 0.18% | 2.87% | 0.15% | 0.18% | 0.24% |
| rate_1h | 0.15% | 0.22% | 0.15% | 0.16% | 0.19% | 0.81% | 0.14% | 0.41% | 0.27% |
| calls_today | 0.20% | 0.38% | 0.12% | 0.02% | 0.29% | 1.36% | 0.12% | 0.13% | 0.14% |
| sessions_1h | 0.19% | 0.10% | 0.18% | 0.17% | 0.10% | 0.93% | 0.20% | 0.08% | 0.15% |
| burstiness_cv | 0.20% | 0.00% | 0.21% | 0.20% | 0.00% | 0.00% | 0.22% | 0.00% | 0.00% |
| reach_today | 0.22% | 0.23% | 0.16% | 0.01% | 0.31% | 1.00% | 0.17% | 1.05% | 0.26% |
| identical_10m | 0.15% | 0.23% | 0.15% | 0.15% | 0.22% | 0.64% | 0.14% | 1.14% | 0.20% |
| identical_in_session | 0.15% | 0.22% | 0.15% | 0.15% | 0.24% | 0.19% | 0.14% | 1.06% | 0.11% |
| how_much_value | 0.20% | 0.27% | 0.19% | 0.29% | 0.27% | 0.25% | 0.19% | 0.05% | 0.19% |
| when_span | 0.07% | 0.06% | 0.07% | 0.04% | 0.05% | 0.05% | 0.07% | 0.02% | 0.03% |
| who_count | 0.03% | 0.17% | 0.03% | 0.01% | 0.16% | 0.18% | 0.00% | 0.15% | 0.05% |
| who_new | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| request_bytes | 0.20% | 0.33% | 0.19% | 0.18% | 0.32% | 0.31% | 0.18% | 0.12% | 1.19% |
| arg_keys_new | 0.02% | 0.07% | 0.02% | 0.16% | 0.06% | 0.04% | 0.02% | 0.77% | 0.02% |
| action_value_new | 0.00% | 0.01% | 0.00% | 0.00% | 0.01% | 0.01% | 0.00% | 0.03% | 0.01% |
| which_new | 0.03% | 0.16% | 0.02% | 0.37% | 0.06% | 0.08% | 0.01% | 0.12% | 0.75% |
| which_new_peer_rare | 0.02% | 0.10% | 0.02% | 0.06% | 0.05% | 0.04% | 0.01% | 0.12% | 0.74% |
| which_new_org_rare | 0.03% | 0.16% | 0.02% | 0.55% | 0.06% | 0.04% | 0.01% | 0.12% | 0.75% |
| which_per_session | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| which_per_day | 0.22% | 0.34% | 0.15% | 0.01% | 0.38% | 0.60% | 0.10% | 0.23% | 0.43% |
| sens_above_own_max | 0.00% | 0.01% | 0.00% | 0.04% | 0.00% | 0.01% | 0.00% | 0.00% | 0.02% |
| tool_asset_pair_new | 0.14% | 0.86% | 0.12% | 0.59% | 0.59% | 0.47% | 0.06% | 2.83% | 2.73% |
| next_tool_self | 0.20% | 0.95% | 0.18% | 0.31% | 0.95% | 0.86% | 0.09% | 5.28% | 1.19% |
| next_tool_peer | 0.32% | 0.68% | 0.23% | 0.18% | 0.56% | 0.75% | 0.13% | 4.56% | 0.53% |
| next_tool_trigram | 0.19% | 0.86% | 0.18% | 0.25% | 0.93% | 0.92% | 0.08% | 3.17% | 1.06% |
| op_transition | 0.02% | 0.07% | 0.02% | 0.16% | 0.05% | 0.10% | 0.02% | 0.25% | 0.04% |
| write_first | 0.18% | 0.77% | 0.18% | 0.22% | 0.80% | 0.86% | 0.08% | 1.25% | 0.53% |
| session_length | 0.16% | 0.16% | 0.15% | 0.15% | 0.18% | 0.21% | 0.15% | 0.37% | 0.27% |
| tool_new_peer_rare | 0.02% | 0.04% | 0.02% | 0.04% | 0.04% | 0.03% | 0.02% | 0.59% | 0.01% |
| hour_of_week | 0.19% | 0.55% | 0.17% | 1.06% | 0.50% | 2.66% | 0.11% | 0.71% | 0.47% |
| dormancy | 0.01% | 0.05% | 0.01% | 0.00% | 0.07% | 0.08% | 0.00% | 0.07% | 0.04% |
| address_new | 0.01% | 0.06% | 0.01% | 0.00% | 0.79% | 0.00% | 0.19% | 0.00% | 0.00% |
| addresses_1h | 0.16% | 1.75% | 0.12% | 0.70% | 1.32% | 2.40% | 0.29% | 4.42% | 1.98% |
| client_new | 0.02% | 0.11% | 0.44% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.01% |
| user_agent_new | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| parallel_sessions | 0.18% | 0.32% | 0.15% | 0.16% | 0.14% | 11.20% | 0.17% | 0.35% | 0.56% |
| call_without_list | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| call_without_init | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| inits_1h | 0.19% | 0.11% | 0.18% | 0.18% | 0.10% | 0.97% | 0.20% | 0.09% | 0.15% |
| cancels_1h | 0.02% | 0.01% | 0.02% | 0.00% | 0.02% | 0.01% | 0.02% | 0.01% | 0.04% |
| tool_mix_shift_week | 0.26% | 1.16% | 0.17% | 0.03% | 1.26% | 1.16% | 0.06% | 42.74% | 1.93% |
| scope_shift_week | 0.26% | 1.99% | 0.25% | 0.01% | 1.28% | 1.00% | 0.07% | 2.04% | 14.20% |
| fano_1h | 0.18% | 0.21% | 0.16% | 0.17% | 0.16% | 6.25% | 0.19% | 0.16% | 0.26% |
| gap_memory | 0.20% | 0.22% | 0.19% | 0.17% | 0.26% | 0.72% | 0.18% | 0.13% | 0.39% |
| low_revisit | 0.18% | 0.18% | 0.17% | 0.14% | 0.18% | 0.18% | 0.16% | 0.15% | 0.25% |
| monotone_run | 0.03% | 0.09% | 0.02% | 0.04% | 0.10% | 0.11% | 0.02% | 0.33% | 0.14% |
| asset_entropy_1h | 0.16% | 0.21% | 0.15% | 0.18% | 0.16% | 1.23% | 0.14% | 0.14% | 0.25% |
| tool_entropy_1h | 0.20% | 0.65% | 0.19% | 0.35% | 0.52% | 0.81% | 0.13% | 0.38% | 0.43% |
| unpopular_share_day | 0.06% | 0.26% | 0.08% | 0.02% | 0.33% | 0.12% | 0.01% | 0.01% | 0.64% |
| new_edges_today | 0.00% | 0.00% | 0.00% | 0.01% | 0.00% | 0.00% | 0.00% | 0.00% | 0.10% |
| cusum_calls | 0.38% | 2.34% | 0.25% | 0.41% | 2.60% | 1.76% | 0.08% | 5.19% | 0.95% |
| cusum_new_edges | 0.00% | 0.01% | 0.00% | 0.00% | 0.00% | 0.01% | 0.00% | 0.04% | 0.21% |
| addresses_in_session | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| non_dominant_client | 0.21% | 0.04% | 3.57% | 0.04% | 0.16% | 0.02% | 2.37% | 0.00% | 0.00% |
| client_context | 0.16% | 0.52% | 2.68% | 0.07% | 1.49% | 0.06% | 1.77% | 0.00% | 0.01% |
| list_to_call_delay | 0.21% | 0.23% | 0.20% | 0.20% | 0.21% | 0.21% | 0.19% | 0.32% | 0.18% |
| distinct_who_day | 0.04% | 0.19% | 0.03% | 0.02% | 0.18% | 0.19% | 0.00% | 0.21% | 0.06% |
| retry_after_cancel | 0.05% | 0.11% | 0.05% | 0.05% | 0.15% | 0.12% | 0.04% | 0.24% | 0.11% |
| non_call_share | 0.21% | 0.28% | 0.20% | 0.11% | 0.28% | 0.29% | 0.18% | 0.22% | 0.14% |
