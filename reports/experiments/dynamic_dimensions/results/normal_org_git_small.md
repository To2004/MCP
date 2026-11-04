# Mostly-ordinary organisation: results

60 agents, 180 days (scored: days 90-179), 2,220,054 messages, 35 gray episodes. Shipped-engine mirror checked on 225,196 messages.

Doc limits: burst > 20 a minute, request > 10 KB. Learned limits (policy.py, first 30 days): {'burst_per_minute': 48, 'request_limit_bytes': 68000, 'requires_before': {}}.

## False alarms and gray episodes

| Engine | Ordinary days ≥x3 | people | bots | ordinary calls ≥x3 | alerts/day (ordinary · change · gray) | gray caught ≥x3 | top causes on ordinary days |
|---|---|---|---|---|---|---|---|
| v2 | 43.0% | 61.2% | 17.4% | 2.2% | 12.0 · 10.2 · 0.5 | 51.4% | request_too_big 68%, sequence 23%, burst 7% |
| v2, learned limits | 18.0% | 28.0% | 3.9% | 1.8% | 5.0 · 7.8 · 0.4 | 37.1% | sequence 80%, request_too_big 7%, burst 5% |
| v3 | 7.8% | 10.6% | 4.0% | 0.1% | 2.2 · 2.9 · 0.4 | 77.1% | request_too_big 46%, sensitive_first_look 37%, new_network 8% |
| v3 final | 5.2% | 6.0% | 4.0% | 0.1% | 1.5 · 2.5 · 0.3 | 74.3% | request_too_big 71%, new_network 12%, asset 6% |
| v3 final, flat first-look rule | 7.8% | 10.5% | 4.0% | 0.1% | 2.2 · 2.9 · 0.4 | 77.1% | request_too_big 46%, sensitive_first_look 36%, new_network 8% |
| v3 final, first look by asset only | 5.2% | 6.0% | 4.0% | 0.1% | 1.5 · 2.5 · 0.3 | 74.3% | request_too_big 71%, new_network 12%, asset 6% |
| v3 final, 5-call warm-up | 5.2% | 6.0% | 4.0% | 0.1% | 1.5 · 2.6 · 0.3 | 74.3% | request_too_big 71%, new_network 12%, asset 6% |
| v3 final, size limits per agent-day | 3.2% | 5.0% | 0.8% | 0.1% | 0.9 · 2.1 · 0.3 | 74.3% | request_too_big 52%, new_network 20%, asset 10% |
| v3 final, first look anchored at a read | 5.8% | 7.1% | 4.0% | 0.1% | 1.6 · 2.7 · 0.3 | 74.3% | request_too_big 64%, sensitive_first_look 11%, new_network 10% |
| v3 final, read anchor, sizes per agent-day | 3.8% | 6.0% | 0.8% | 0.1% | 1.1 · 2.3 · 0.3 | 74.3% | request_too_big 44%, sensitive_first_look 16%, new_network 16% |
| v3 (decided), org discount on first looks | 3.2% | 4.9% | 0.8% | 0.1% | 0.9 · 2.1 · 0.3 | 74.3% | request_too_big 52%, new_network 18%, asset 10% |
| v3 (decided) | 3.2% | 5.0% | 0.8% | 0.1% | 0.9 · 2.1 · 0.3 | 74.3% | request_too_big 52%, new_network 18%, asset 10% |
| v4 | 2.5% | 3.8% | 0.8% | 0.0% | 0.7 · 1.7 · 0.3 | 74.3% | request_too_big 70%, asset 14%, tool 11% |
| v3 (decided), network and app in Footprint | 2.6% | 4.0% | 0.8% | 0.0% | 0.7 · 2.0 · 0.3 | 74.3% | request_too_big 67%, asset 12%, new_tool 10% |
| v3 (decided), new tool through tool rarity | 3.1% | 4.8% | 0.8% | 0.1% | 0.9 · 1.9 · 0.3 | 74.3% | request_too_big 56%, new_network 19%, asset 10% |

## Daily review list

Gray episodes caught when someone reviews the top-k agent-days each day (60 agents).

| Engine | list | gray caught | cut in a tie | list filled by ordinary · change · gray |
|---|---|---|---|---|
| v2 | top 4 | M, ties at random | 17.8% | 89.0% | 38.7% · 59.4% · 1.8% |
| v2 | top 4 | M, then strange dimensions | 34.6% | 65.9% | 39.9% · 56.4% · 3.7% |
| v2 | top 4 | M, then second score | 20.0% | 2.2% | 43.7% · 54.4% · 1.9% |
| v2 | top 4 | static x M | 15.2% | 87.9% | 42.4% · 55.9% · 1.7% |
| v2 | top 8 | M, ties at random | 29.2% | 87.9% | 44.2% · 53.6% · 1.8% |
| v2 | top 8 | M, then strange dimensions | 49.1% | 71.4% | 45.8% · 50.7% · 3.0% |
| v2 | top 8 | M, then second score | 31.4% | 17.6% | 46.1% · 51.5% · 1.9% |
| v2 | top 8 | static x M | 28.4% | 73.6% | 47.7% · 50.0% · 2.0% |
| v2, learned limits | top 4 | M, ties at random | 21.3% | 81.3% | 29.6% · 68.2% · 2.2% |
| v2, learned limits | top 4 | M, then strange dimensions | 34.3% | 62.6% | 36.4% · 60.2% · 3.4% |
| v2, learned limits | top 4 | M, then second score | 22.9% | 2.2% | 31.6% · 66.2% · 2.2% |
| v2, learned limits | top 4 | static x M | 18.2% | 83.5% | 32.8% · 65.1% · 2.0% |
| v2, learned limits | top 8 | M, ties at random | 35.7% | 90.1% | 36.5% · 60.9% · 2.2% |
| v2, learned limits | top 8 | M, then strange dimensions | 47.4% | 81.3% | 39.7% · 56.8% · 3.0% |
| v2, learned limits | top 8 | M, then second score | 31.4% | 20.9% | 33.5% · 64.5% · 1.6% |
| v2, learned limits | top 8 | static x M | 34.9% | 70.3% | 39.2% · 58.0% · 2.4% |
| v3 | top 4 | M, ties at random | 56.2% | 54.9% | 44.3% · 50.0% · 5.6% |
| v3 | top 4 | M, then strange dimensions | 66.9% | 28.6% | 44.1% · 49.0% · 6.9% |
| v3 | top 4 | M, then second score | 62.9% | 2.2% | 45.2% · 48.2% · 6.6% |
| v3 | top 4 | static x M | 46.9% | 28.6% | 40.0% · 55.3% · 4.6% |
| v3 | top 8 | M, ties at random | 78.6% | 30.8% | 46.6% · 48.2% · 4.8% |
| v3 | top 8 | M, then strange dimensions | 80.0% | 20.9% | 46.7% · 48.0% · 4.9% |
| v3 | top 8 | M, then second score | 82.9% | 16.5% | 46.4% · 48.3% · 4.9% |
| v3 | top 8 | static x M | 70.5% | 15.4% | 43.7% · 51.7% · 4.2% |
| v3 final | top 4 | M, ties at random | 57.5% | 31.9% | 40.4% · 54.0% · 5.5% |
| v3 final | top 4 | M, then strange dimensions | 65.7% | 13.2% | 40.6% · 53.1% · 6.3% |
| v3 final | top 4 | M, then second score | 60.0% | 4.4% | 40.4% · 53.9% · 5.8% |
| v3 final | top 4 | static x M | 56.6% | 24.2% | 38.4% · 56.1% · 5.5% |
| v3 final | top 8 | M, ties at random | 72.7% | 26.4% | 45.6% · 49.8% · 4.2% |
| v3 final | top 8 | M, then strange dimensions | 71.4% | 17.6% | 45.8% · 49.7% · 4.1% |
| v3 final | top 8 | M, then second score | 74.3% | 14.3% | 45.4% · 49.9% · 4.3% |
| v3 final | top 8 | static x M | 71.9% | 15.4% | 44.2% · 51.4% · 4.0% |
| v3 final, flat first-look rule | top 4 | M, ties at random | 56.7% | 54.9% | 44.1% · 50.2% · 5.7% |
| v3 final, flat first-look rule | top 4 | M, then strange dimensions | 65.5% | 26.4% | 44.4% · 48.7% · 6.8% |
| v3 final, flat first-look rule | top 4 | M, then second score | 60.0% | 2.2% | 46.0% · 48.0% · 6.0% |
| v3 final, flat first-look rule | top 4 | static x M | 52.8% | 28.6% | 39.9% · 54.9% · 5.2% |
| v3 final, flat first-look rule | top 8 | M, ties at random | 78.2% | 31.9% | 46.6% · 48.1% · 4.8% |
| v3 final, flat first-look rule | top 8 | M, then strange dimensions | 80.0% | 20.9% | 46.8% · 47.9% · 4.9% |
| v3 final, flat first-look rule | top 8 | M, then second score | 82.9% | 17.6% | 46.4% · 48.3% · 4.9% |
| v3 final, flat first-look rule | top 8 | static x M | 75.8% | 15.4% | 44.0% · 51.1% · 4.5% |
| v3 final, first look by asset only | top 4 | M, ties at random | 61.4% | 39.6% | 40.1% · 53.9% · 6.0% |
| v3 final, first look by asset only | top 4 | M, then strange dimensions | 68.6% | 13.2% | 39.9% · 53.3% · 6.7% |
| v3 final, first look by asset only | top 4 | M, then second score | 65.7% | 4.4% | 39.3% · 54.2% · 6.6% |
| v3 final, first look by asset only | top 4 | static x M | 56.2% | 22.0% | 38.4% · 56.0% · 5.5% |
| v3 final, first look by asset only | top 8 | M, ties at random | 74.1% | 29.7% | 45.9% · 49.2% · 4.4% |
| v3 final, first look by asset only | top 8 | M, then strange dimensions | 72.4% | 19.8% | 46.2% · 49.0% · 4.3% |
| v3 final, first look by asset only | top 8 | M, then second score | 74.3% | 15.4% | 46.0% · 49.2% · 4.4% |
| v3 final, first look by asset only | top 8 | static x M | 71.9% | 15.4% | 44.2% · 51.2% · 4.1% |
| v3 final, 5-call warm-up | top 4 | M, ties at random | 57.5% | 33.0% | 40.0% · 54.4% · 5.5% |
| v3 final, 5-call warm-up | top 4 | M, then strange dimensions | 65.7% | 14.3% | 40.4% · 53.3% · 6.3% |
| v3 final, 5-call warm-up | top 4 | M, then second score | 60.0% | 3.3% | 40.1% · 54.2% · 5.8% |
| v3 final, 5-call warm-up | top 4 | static x M | 56.6% | 22.0% | 38.0% · 56.5% · 5.5% |
| v3 final, 5-call warm-up | top 8 | M, ties at random | 72.7% | 26.4% | 45.4% · 49.9% · 4.2% |
| v3 final, 5-call warm-up | top 8 | M, then strange dimensions | 71.4% | 16.5% | 45.6% · 49.8% · 4.1% |
| v3 final, 5-call warm-up | top 8 | M, then second score | 74.3% | 14.3% | 45.3% · 50.1% · 4.3% |
| v3 final, 5-call warm-up | top 8 | static x M | 70.5% | 14.3% | 44.1% · 51.6% · 3.9% |
| v3 final, size limits per agent-day | top 4 | M, ties at random | 65.8% | 24.2% | 40.3% · 53.1% · 6.6% |
| v3 final, size limits per agent-day | top 4 | M, then strange dimensions | 68.6% | 9.9% | 40.3% · 52.7% · 7.0% |
| v3 final, size limits per agent-day | top 4 | M, then second score | 65.7% | 6.6% | 40.5% · 52.6% · 6.9% |
| v3 final, size limits per agent-day | top 4 | static x M | 56.7% | 18.7% | 37.1% · 57.1% · 5.8% |
| v3 final, size limits per agent-day | top 8 | M, ties at random | 76.1% | 26.4% | 45.8% · 49.1% · 4.6% |
| v3 final, size limits per agent-day | top 8 | M, then strange dimensions | 75.2% | 16.5% | 46.0% · 49.0% · 4.6% |
| v3 final, size limits per agent-day | top 8 | M, then second score | 77.1% | 13.2% | 46.0% · 48.9% · 4.7% |
| v3 final, size limits per agent-day | top 8 | static x M | 75.7% | 14.3% | 43.9% · 51.4% · 4.3% |
| v3 final, first look anchored at a read | top 4 | M, ties at random | 61.4% | 33.0% | 40.6% · 53.5% · 5.9% |
| v3 final, first look anchored at a read | top 4 | M, then strange dimensions | 68.6% | 11.0% | 40.6% · 52.8% · 6.6% |
| v3 final, first look anchored at a read | top 4 | M, then second score | 65.7% | 4.4% | 40.4% · 53.3% · 6.3% |
| v3 final, first look anchored at a read | top 4 | static x M | 51.7% | 23.1% | 38.8% · 56.1% · 5.1% |
| v3 final, first look anchored at a read | top 8 | M, ties at random | 74.4% | 33.0% | 45.7% · 49.5% · 4.4% |
| v3 final, first look anchored at a read | top 8 | M, then strange dimensions | 72.9% | 19.8% | 45.5% · 49.8% · 4.3% |
| v3 final, first look anchored at a read | top 8 | M, then second score | 77.1% | 15.4% | 45.7% · 49.4% · 4.5% |
| v3 final, first look anchored at a read | top 8 | static x M | 74.7% | 15.4% | 43.8% · 51.5% · 4.3% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, ties at random | 68.3% | 27.5% | 40.1% · 53.1% · 6.8% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, then strange dimensions | 71.4% | 8.8% | 40.1% · 52.7% · 7.1% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, then second score | 68.6% | 5.5% | 40.3% · 52.6% · 7.1% |
| v3 final, read anchor, sizes per agent-day | top 4 | static x M | 56.4% | 14.3% | 37.1% · 57.0% · 5.9% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, ties at random | 77.8% | 30.8% | 45.9% · 49.0% · 4.7% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, then strange dimensions | 76.7% | 18.7% | 45.8% · 49.1% · 4.6% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, then second score | 80.0% | 13.2% | 45.8% · 49.0% · 4.8% |
| v3 final, read anchor, sizes per agent-day | top 8 | static x M | 77.1% | 6.6% | 43.4% · 51.6% · 4.5% |
| v3 (decided), org discount on first looks | top 4 | M, ties at random | 68.7% | 31.9% | 40.2% · 52.9% · 6.9% |
| v3 (decided), org discount on first looks | top 4 | M, then strange dimensions | 71.4% | 11.0% | 40.1% · 52.5% · 7.4% |
| v3 (decided), org discount on first looks | top 4 | M, then second score | 68.6% | 5.5% | 40.3% · 52.6% · 7.1% |
| v3 (decided), org discount on first looks | top 4 | static x M | 62.4% | 16.5% | 35.5% · 58.1% · 6.4% |
| v3 (decided), org discount on first looks | top 8 | M, ties at random | 76.1% | 30.8% | 46.4% · 48.5% · 4.6% |
| v3 (decided), org discount on first looks | top 8 | M, then strange dimensions | 76.2% | 18.7% | 46.6% · 48.3% · 4.6% |
| v3 (decided), org discount on first looks | top 8 | M, then second score | 80.0% | 13.2% | 46.4% · 48.3% · 4.8% |
| v3 (decided), org discount on first looks | top 8 | static x M | 75.7% | 11.0% | 44.0% · 51.1% · 4.5% |
| v3 (decided) | top 4 | M, ties at random | 68.7% | 29.7% | 41.2% · 51.9% · 6.9% |
| v3 (decided) | top 4 | M, then strange dimensions | 71.4% | 9.9% | 41.6% · 51.3% · 7.1% |
| v3 (decided) | top 4 | M, then second score | 68.6% | 5.5% | 41.1% · 51.8% · 7.1% |
| v3 (decided) | top 4 | static x M | 62.4% | 13.2% | 37.0% · 56.6% · 6.5% |
| v3 (decided) | top 8 | M, ties at random | 76.1% | 30.8% | 46.7% · 48.3% · 4.6% |
| v3 (decided) | top 8 | M, then strange dimensions | 76.2% | 20.9% | 46.7% · 48.3% · 4.6% |
| v3 (decided) | top 8 | M, then second score | 80.0% | 13.2% | 46.7% · 48.1% · 4.8% |
| v3 (decided) | top 8 | static x M | 75.7% | 9.9% | 44.0% · 51.2% · 4.5% |
| v4 | top 4 | M, ties at random | 71.4% | 24.2% | 42.8% · 49.7% · 7.5% |
| v4 | top 4 | M, then strange dimensions | 71.4% | 14.3% | 42.8% · 49.5% · 7.7% |
| v4 | top 4 | M, then second score | 71.4% | 3.3% | 42.5% · 49.8% · 7.7% |
| v4 | top 4 | static x M | 67.1% | 11.0% | 38.5% · 54.9% · 6.7% |
| v4 | top 8 | M, ties at random | 75.0% | 14.3% | 45.7% · 49.4% · 4.5% |
| v4 | top 8 | M, then strange dimensions | 74.3% | 5.5% | 45.8% · 49.3% · 4.5% |
| v4 | top 8 | M, then second score | 77.1% | 0.0% | 45.7% · 49.2% · 4.7% |
| v4 | top 8 | static x M | 72.9% | 5.5% | 45.8% · 49.5% · 4.3% |
| v3 (decided), network and app in Footprint | top 4 | M, ties at random | 69.3% | 27.5% | 40.9% · 51.8% · 7.3% |
| v3 (decided), network and app in Footprint | top 4 | M, then strange dimensions | 71.4% | 11.0% | 41.3% · 51.1% · 7.6% |
| v3 (decided), network and app in Footprint | top 4 | M, then second score | 68.6% | 3.3% | 41.4% · 51.2% · 7.4% |
| v3 (decided), network and app in Footprint | top 4 | static x M | 64.8% | 12.1% | 37.0% · 56.4% · 6.6% |
| v3 (decided), network and app in Footprint | top 8 | M, ties at random | 76.1% | 16.5% | 45.1% · 49.9% · 4.6% |
| v3 (decided), network and app in Footprint | top 8 | M, then strange dimensions | 76.2% | 7.7% | 45.3% · 49.7% · 4.6% |
| v3 (decided), network and app in Footprint | top 8 | M, then second score | 77.1% | 0.0% | 45.3% · 49.6% · 4.7% |
| v3 (decided), network and app in Footprint | top 8 | static x M | 75.7% | 5.5% | 45.1% · 50.0% · 4.5% |
| v3 (decided), new tool through tool rarity | top 4 | M, ties at random | 71.4% | 30.8% | 43.1% · 49.7% · 7.2% |
| v3 (decided), new tool through tool rarity | top 4 | M, then strange dimensions | 71.4% | 13.2% | 43.5% · 49.2% · 7.3% |
| v3 (decided), new tool through tool rarity | top 4 | M, then second score | 71.4% | 5.5% | 43.3% · 49.3% · 7.4% |
| v3 (decided), new tool through tool rarity | top 4 | static x M | 64.3% | 12.1% | 38.7% · 54.9% · 6.4% |
| v3 (decided), new tool through tool rarity | top 8 | M, ties at random | 75.0% | 25.3% | 47.2% · 47.9% · 4.5% |
| v3 (decided), new tool through tool rarity | top 8 | M, then strange dimensions | 76.2% | 17.6% | 47.2% · 47.8% · 4.6% |
| v3 (decided), new tool through tool rarity | top 8 | M, then second score | 77.1% | 13.2% | 47.3% · 47.7% · 4.7% |
| v3 (decided), new tool through tool rarity | top 8 | static x M | 72.9% | 6.6% | 45.3% · 50.0% · 4.3% |

## Ordinary life and org-wide changes at x3 or more

| Change | days | v2 | v2, learned limits | v3 | v3 final | v3 final, flat first-look rule | v3 final, first look by asset only | v3 final, 5-call warm-up | v3 final, size limits per agent-day | v3 final, first look anchored at a read | v3 final, read anchor, sizes per agent-day | v3 (decided), org discount on first looks | v3 (decided) | v4 | v3 (decided), network and app in Footprint | v3 (decided), new tool through tool rarity |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| back_from_vacation | 62 | 51.6% (request_too_big) | 30.6% (sequence) | 12.9% (new_tool) | 9.7% (new_tool) | 12.9% (new_tool) | 9.7% (new_tool) | 9.7% (new_tool) | 8.1% (new_tool) | 11.3% (new_tool) | 9.7% (new_tool) | 8.1% (new_tool) | 8.1% (new_tool) | 4.8% (tool) | 8.1% (new_tool) | 4.8% (tool) |
| client_switch | 9 | 88.9% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (client) | 44.4% (client) | 44.4% (new_client) |
| isp_change | 2 | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 50.0% (network) | 50.0% (network) | 100.0% (new_network) |
| monthly_report | 15 | 100.0% (asset) | 100.0% (asset) | 73.3% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) |
| new_hire | 69 | 72.5% (request_too_big) | 42.0% (new_tool) | 46.4% (new_tool) | 33.3% (new_tool) | 43.5% (sensitive_first_look) | 33.3% (new_tool) | 39.1% (new_tool) | 31.9% (new_tool) | 36.2% (new_tool) | 34.8% (new_tool) | 31.9% (new_tool) | 31.9% (new_tool) | 17.4% (sequence) | 27.5% (new_tool) | 23.2% (sequence) |
| new_project | 1110 | 62.3% (sequence) | 48.5% (sequence) | 14.0% (asset) | 12.9% (asset) | 14.6% (asset) | 12.9% (asset) | 12.9% (asset) | 9.8% (asset) | 13.2% (asset) | 10.3% (asset) | 9.5% (asset) | 9.7% (asset) | 8.8% (asset) | 8.9% (asset) | 9.3% (asset) |
| on_call_incident | 11 | 100.0% (sequence) | 100.0% (sequence) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) |
| org_repo_migration | 81 | 60.5% (asset) | 49.4% (asset) | 32.1% (asset) | 27.6% (asset) | 33.3% (asset) | 27.6% (asset) | 27.6% (asset) | 26.4% (asset) | 26.4% (asset) | 25.3% (asset) | 26.7% (asset) | 25.0% (asset) | 25.9% (asset) | 25.9% (asset) | 25.9% (asset) |
| org_tool_rollout | 67 | 74.6% (new_tool) | 68.7% (new_tool) | 44.8% (new_tool) | 43.3% (new_tool) | 44.8% (new_tool) | 43.3% (new_tool) | 43.3% (new_tool) | 43.3% (new_tool) | 43.3% (new_tool) | 43.3% (new_tool) | 43.3% (new_tool) | 43.3% (new_tool) | 29.9% (tool) | 43.3% (new_tool) | 29.9% (tool) |
| org_vpn_change | 38 | 100.0% (new_network) | 100.0% (new_network) | 31.6% (new_network) | 21.1% (new_network) | 28.9% (sensitive_first_look) | 21.1% (new_network) | 28.9% (new_network) | 21.1% (new_network) | 21.1% (new_network) | 21.1% (new_network) | 18.4% (new_network) | 18.4% (new_network) | 15.8% (network) | 18.4% (network) | 18.4% (new_network) |
| release_crunch | 88 | 92.0% (request_too_big) | 53.4% (sequence) | 46.6% (time_of_day) | 37.5% (time_of_day) | 46.6% (time_of_day) | 37.5% (time_of_day) | 37.5% (time_of_day) | 33.0% (time_of_day) | 42.0% (time_of_day) | 37.5% (time_of_day) | 34.1% (time_of_day) | 33.0% (time_of_day) | 33.0% (time_of_day) | 33.0% (time_of_day) | 33.0% (time_of_day) |
| role_change | 27 | 92.6% (request_too_big) | 66.7% (sequence) | 25.9% (new_tool) | 18.5% (new_tool) | 25.9% (new_tool) | 18.5% (new_tool) | 18.5% (new_tool) | 18.5% (new_tool) | 22.2% (new_tool) | 22.2% (new_tool) | 18.5% (new_tool) | 18.5% (new_tool) | 11.1% (request_too_big) | 18.5% (new_tool) | 11.1% (request_too_big) |

## Gray episodes by kind

| Kind | episodes | v2: caught · calls ≥x3 | v2, learned limits: caught · calls ≥x3 | v3: caught · calls ≥x3 | v3 final: caught · calls ≥x3 | v3 final, flat first-look rule: caught · calls ≥x3 | v3 final, first look by asset only: caught · calls ≥x3 | v3 final, 5-call warm-up: caught · calls ≥x3 | v3 final, size limits per agent-day: caught · calls ≥x3 | v3 final, first look anchored at a read: caught · calls ≥x3 | v3 final, read anchor, sizes per agent-day: caught · calls ≥x3 | v3 (decided), org discount on first looks: caught · calls ≥x3 | v3 (decided): caught · calls ≥x3 | v4: caught · calls ≥x3 | v3 (decided), network and app in Footprint: caught · calls ≥x3 | v3 (decided), new tool through tool rarity: caught · calls ≥x3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| big_paste | 6 | 100.0% · 100.0% | 16.7% · 16.7% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| bot_loop | 3 | 100.0% · 96.4% | 100.0% · 91.3% | 100.0% · 96.0% | 100.0% · 96.0% | 100.0% · 96.0% | 100.0% · 96.0% | 100.0% · 96.0% | 100.0% · 96.0% | 100.0% · 96.0% | 100.0% · 96.0% | 100.0% · 96.0% | 100.0% · 96.0% | 100.0% · 96.0% | 100.0% · 96.0% | 100.0% · 96.0% |
| bulk_export | 5 | 0.0% · 0.0% | 0.0% · 0.0% | 100.0% · 13.1% | 100.0% · 78.0% | 100.0% · 79.7% | 100.0% · 78.0% | 100.0% · 78.0% | 100.0% · 78.0% | 100.0% · 78.0% | 100.0% · 78.0% | 100.0% · 78.0% | 100.0% · 78.0% | 100.0% · 78.0% | 100.0% · 78.0% | 100.0% · 78.0% |
| cross_copy | 5 | 100.0% · 36.1% | 100.0% · 36.1% | 60.0% · 32.5% | 60.0% · 32.5% | 60.0% · 32.5% | 60.0% · 32.5% | 60.0% · 32.5% | 60.0% · 32.5% | 60.0% · 32.5% | 60.0% · 32.5% | 60.0% · 32.5% | 60.0% · 32.5% | 60.0% · 32.5% | 60.0% · 32.5% | 60.0% · 32.5% |
| mass_cleanup | 3 | 0.0% · 0.0% | 0.0% · 0.0% | 33.3% · 15.9% | 33.3% · 15.9% | 33.3% · 15.9% | 33.3% · 15.9% | 33.3% · 15.9% | 33.3% · 15.9% | 33.3% · 15.9% | 33.3% · 15.9% | 33.3% · 15.9% | 33.3% · 15.9% | 33.3% · 15.9% | 33.3% · 15.9% | 33.3% · 15.9% |
| overfetch | 4 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% |
| scope_creep | 3 | 0.0% · 0.0% | 0.0% · 0.0% | 100.0% · 12.6% | 66.7% · 8.1% | 100.0% · 13.3% | 66.7% · 8.1% | 66.7% · 8.1% | 66.7% · 8.1% | 66.7% · 5.5% | 66.7% · 5.5% | 66.7% · 8.1% | 66.7% · 5.5% | 66.7% · 8.1% | 66.7% · 8.1% | 66.7% · 8.1% |
| sensitive_peek | 2 | 50.0% · 33.3% | 50.0% · 33.3% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| shadow_script | 2 | 100.0% · 2.8% | 100.0% · 2.8% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| slow_loop | 2 | 50.0% · 24.3% | 50.0% · 24.3% | 100.0% · 88.3% | 100.0% · 88.3% | 100.0% · 88.3% | 100.0% · 88.3% | 100.0% · 88.3% | 100.0% · 88.3% | 100.0% · 88.1% | 100.0% · 88.1% | 100.0% · 88.3% | 100.0% · 88.3% | 100.0% · 88.3% | 100.0% · 88.3% | 100.0% · 88.3% |

## Hand-made scenarios

**One night of 30 calls at 3 a.m. (day 10); a 3 a.m. call on day 45** (max M of the 3 a.m. calls)

- v1 (shipped): x0.97 (calls_last_hour)
- v2: x0.97 (calls_last_hour)
- v2 + days: x3.84 (time_of_day)
- control (no earlier night), v2: x4.36 (time_of_day)

**New folder q4-plan, 12 calls on its first day** (M per call, v2)

- sequence: 4.4 3.9 3.4 3.1 2.8 2.6 2.4 2.2 2.0 1.9 1.8 1.7

**New folder q4-plan, 12 calls on its first day** (M per call, v2 + daily update)

- sequence: 4.4 4.4 4.4 4.4 4.4 4.4 4.4 4.4 4.4 4.4 4.4 4.4

**New hire explores ~30 repos in 2 weeks; first look at payroll on day 73** (M of the payroll call)

- v1 (shipped): x0.90 (asset)
- v2: x0.90 (asset)
- v2 + 14-day onboarding: x4.46 (asset)
- control (no exploration), v2: x4.46 (asset)

**First use of a tool he never used** (M)

- habitual agent, v1: x3.20 (tool)
- habitual agent, v2: x3.62 (new_tool)
- tries a new tool every week, v1: x1.49 (tool)
- tries a new tool every week, v2: x3.62 (new_tool)
- new hire on day 2, v1: x0.96 (tool)
- new hire on day 2, v2: x3.62 (new_tool)

**Fresh identity: 5 warm-up calls, 20 repos on day 1** (M)

- payroll on day 1, v2: x1.02 (calls_last_hour)
- customer data on day 2, v2: x0.74 (calls_last_hour)
- same agent with 60 quiet days first, customer data, v2: x4.36 (asset)

**Day worker who never worked a weekend: Saturday 2 a.m.** (max M)

- v2: x0.96 (calls_last_hour)
- v2 + weekend falls back to all days: x4.36 (time_of_day)
- same hour on a weekday (day 66), v2: x4.36 (time_of_day)

**Explorer (a new repo every other weekday): first look at payroll** (M)

- v2: x1.15 (asset)
- v2 + sensitive assets also scored on this thing only: x4.36 (asset)
- focused agent (no exploring), v2: x4.36 (asset)

**First look at a sensitive asset: explorer** (M: flat 0.9 -> by asset (v3) -> by asset and tool, anchored at a write -> at a read)

- payroll (5), read file: x3.62 (sensitive_first_look) -> x3.62 (sensitive_first_look) -> x3.09 (sensitive_first_look) -> x3.62 (sensitive_first_look)
- payroll (5), list commits: x3.62 (sensitive_first_look) -> x3.62 (sensitive_first_look) -> x2.63 (sensitive_first_look) -> x3.09 (sensitive_first_look)
- payroll (5), write file: x3.62 (sensitive_first_look) -> x3.62 (sensitive_first_look) -> x3.62 (sensitive_first_look) -> x4.26 (sensitive_first_look)
- team deploy repo (4), read file: x3.62 (sensitive_first_look) -> x2.63 (sensitive_first_look) -> x2.24 (sensitive_first_look) -> x2.63 (sensitive_first_look)
- team deploy repo (4), list commits: x3.62 (sensitive_first_look) -> x2.63 (sensitive_first_look) -> x1.90 (sensitive_first_look) -> x2.24 (sensitive_first_look)
- team deploy repo (4), write file: x3.62 (sensitive_first_look) -> x3.62 (sequence) -> x3.62 (sequence) -> x3.62 (sequence)

**First look at a sensitive asset: new hire, day 3** (M: flat 0.9 -> by asset (v3) -> by asset and tool, anchored at a write -> at a read)

- payroll (5), read file: x3.62 (sensitive_first_look) -> x3.62 (sensitive_first_look) -> x3.09 (sensitive_first_look) -> x3.62 (sensitive_first_look)
- payroll (5), list commits: x3.62 (sensitive_first_look) -> x3.62 (sensitive_first_look) -> x2.63 (sensitive_first_look) -> x3.09 (sensitive_first_look)
- payroll (5), write file: x3.62 (sensitive_first_look) -> x3.62 (sensitive_first_look) -> x3.62 (sensitive_first_look) -> x4.26 (sensitive_first_look)
- team deploy repo (4), read file: x3.62 (sensitive_first_look) -> x2.63 (sensitive_first_look) -> x2.24 (sensitive_first_look) -> x2.63 (sensitive_first_look)
- team deploy repo (4), list commits: x3.62 (sensitive_first_look) -> x2.63 (sensitive_first_look) -> x1.90 (sensitive_first_look) -> x2.24 (sensitive_first_look)
- team deploy repo (4), write file: x3.62 (sensitive_first_look) -> x3.62 (sequence) -> x3.62 (sequence) -> x3.62 (sequence)

**Fresh identity: 25 calls on day 1, then one more call that day** (M under the warm-up: 5 calls / first day / first day, rules on)

- an ordinary call with a tool new today: x3.62 (new_tool) / x1.00 (None) / x1.00 (None)
- payroll (5), read file: x3.62 (new_tool) / x1.00 (None) / x3.62 (sensitive_first_look)
- payroll (5), write file: x3.62 (new_tool) / x1.00 (None) / x3.62 (sensitive_first_look)
- team deploy repo (4), read file: x3.62 (new_tool) / x1.00 (None) / x2.63 (sensitive_first_look)
- team deploy repo (4), list commits: x3.62 (new_tool) / x1.00 (None) / x2.63 (sensitive_first_look)

**Weekend mode: split** (max M)

- day worker, first Saturday ever, 2 a.m.: x0.96 (calls_last_hour)
- day worker, first Saturday ever, 10 a.m.: x0.96 (calls_last_hour)
- works every Saturday 10-14, Saturday 2 a.m.: x2.92 (time_of_day)
- works every Saturday 10-14, Saturday 10 a.m.: x0.96 (calls_last_hour)

**Weekend mode: fallback** (max M)

- day worker, first Saturday ever, 2 a.m.: x4.36 (time_of_day)
- day worker, first Saturday ever, 10 a.m.: x0.96 (calls_last_hour)
- works every Saturday 10-14, Saturday 2 a.m.: x2.92 (time_of_day)
- works every Saturday 10-14, Saturday 10 a.m.: x0.96 (calls_last_hour)

**Weekend mode: blend** (max M)

- day worker, first Saturday ever, 2 a.m.: x4.36 (time_of_day)
- day worker, first Saturday ever, 10 a.m.: x0.96 (calls_last_hour)
- works every Saturday 10-14, Saturday 2 a.m.: x4.82 (time_of_day)
- works every Saturday 10-14, Saturday 10 a.m.: x0.96 (calls_last_hour)

**Weekend mode: flag** (max M)

- day worker, first Saturday ever, 2 a.m.: x4.36 (time_of_day)
- day worker, first Saturday ever, 10 a.m.: x1.90 (weekend_work)
- works every Saturday 10-14, Saturday 2 a.m.: x4.46 (time_of_day)
- works every Saturday 10-14, Saturday 10 a.m.: x0.96 (calls_last_hour)

**CI bot, 30 jobs a day, each from a random /16 of its cloud pool** (days with a new network (x3.6))

- 40 /16s: 0% of days
- 400 /16s: 3% of days
- 1500 /16s: 98% of days
