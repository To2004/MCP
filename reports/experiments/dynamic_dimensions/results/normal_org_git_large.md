# Mostly-ordinary organisation: results

300 agents, 180 days (scored: days 90-179), 5,796,994 messages, 183 gray episodes. Shipped-engine mirror checked on 227,675 messages.

Doc limits: burst > 20 a minute, request > 10 KB. Learned limits (policy.py, first 30 days): {'burst_per_minute': 29, 'request_limit_bytes': 101000, 'requires_before': {}}.

## False alarms and gray episodes

| Engine | Ordinary days ≥x3 | people | bots | ordinary calls ≥x3 | alerts/day (ordinary · change · gray) | gray caught ≥x3 | top causes on ordinary days |
|---|---|---|---|---|---|---|---|
| v2 | 54.4% | 57.7% | 22.4% | 2.7% | 86.9 · 30.0 · 2.4 | 36.1% | request_too_big 67%, sequence 30%, burst 1% |
| v2, learned limits | 25.1% | 26.4% | 12.6% | 2.1% | 40.0 · 20.3 · 1.6 | 22.4% | sequence 90%, new_tool 2%, request_too_big 2% |
| v3 | 4.5% | 4.5% | 4.9% | 0.2% | 7.2 · 6.0 · 1.5 | 65.0% | request_too_big 46%, sensitive_first_look 24%, new_network 13% |
| v3 final | 3.5% | 3.3% | 5.0% | 0.2% | 5.5 · 5.7 · 1.5 | 69.4% | request_too_big 60%, new_network 17%, tool 12% |
| v3 final, flat first-look rule | 4.5% | 4.5% | 5.0% | 0.2% | 7.2 · 6.2 · 1.6 | 71.6% | request_too_big 46%, sensitive_first_look 24%, new_network 13% |
| v3 final, first look by asset only | 3.5% | 3.3% | 5.0% | 0.2% | 5.5 · 5.7 · 1.5 | 69.4% | request_too_big 60%, new_network 17%, tool 12% |
| v3 final, 5-call warm-up | 3.5% | 3.3% | 5.0% | 0.2% | 5.5 · 5.7 · 1.5 | 69.4% | request_too_big 60%, new_network 17%, tool 12% |
| v3 final, size limits per agent-day | 3.1% | 3.1% | 3.5% | 0.2% | 5.0 · 5.4 · 1.5 | 69.4% | request_too_big 56%, new_network 18%, tool 14% |
| v3 final, first look anchored at a read | 3.7% | 3.6% | 5.0% | 0.2% | 6.0 · 5.8 · 1.5 | 69.4% | request_too_big 56%, new_network 15%, tool 12% |
| v3 final, read anchor, sizes per agent-day | 3.4% | 3.4% | 3.5% | 0.2% | 5.4 · 5.5 · 1.5 | 69.4% | request_too_big 51%, new_network 17%, tool 13% |
| v3 (decided), org discount on first looks | 3.1% | 3.0% | 3.5% | 0.2% | 4.9 · 5.4 · 1.5 | 69.4% | request_too_big 56%, new_network 19%, tool 14% |
| v3 (decided) | 3.0% | 2.9% | 3.5% | 0.2% | 4.8 · 5.3 · 1.5 | 72.1% | request_too_big 59%, new_network 17%, tool 14% |
| v4 | 2.5% | 2.4% | 3.5% | 0.1% | 3.9 · 5.0 · 1.5 | 72.1% | request_too_big 72%, tool 20%, sequence 4% |
| v3 (decided), network and app in Footprint | 2.5% | 2.4% | 3.5% | 0.1% | 4.1 · 5.2 · 1.5 | 72.1% | request_too_big 69%, tool 17%, new_tool 6% |
| v3 (decided), new tool through tool rarity | 3.0% | 2.9% | 3.5% | 0.2% | 4.7 · 5.2 · 1.5 | 72.1% | request_too_big 59%, new_network 17%, tool 17% |

## Daily review list

Gray episodes caught when someone reviews the top-k agent-days each day (300 agents).

| Engine | list | gray caught | cut in a tie | list filled by ordinary · change · gray |
|---|---|---|---|---|
| v2 | top 4 | M, ties at random | 8.5% | 92.3% | 56.5% · 39.2% · 4.3% |
| v2 | top 4 | M, then strange dimensions | 12.4% | 74.7% | 47.5% · 46.2% · 6.3% |
| v2 | top 4 | M, then second score | 12.4% | 36.3% | 55.7% · 37.8% · 6.4% |
| v2 | top 4 | static x M | 3.7% | 95.6% | 64.7% · 33.4% · 1.9% |
| v2 | top 8 | M, ties at random | 11.4% | 94.5% | 61.2% · 35.7% · 3.1% |
| v2 | top 8 | M, then strange dimensions | 17.4% | 82.4% | 54.0% · 41.3% · 4.7% |
| v2 | top 8 | M, then second score | 16.4% | 19.8% | 61.2% · 34.2% · 4.5% |
| v2 | top 8 | static x M | 6.4% | 95.6% | 67.4% · 30.7% · 1.9% |
| v2, learned limits | top 4 | M, ties at random | 9.0% | 91.2% | 49.3% · 46.1% · 4.6% |
| v2, learned limits | top 4 | M, then strange dimensions | 13.4% | 73.6% | 43.0% · 49.9% · 7.1% |
| v2, learned limits | top 4 | M, then second score | 14.0% | 14.3% | 50.5% · 42.0% · 7.5% |
| v2, learned limits | top 4 | static x M | 4.4% | 94.5% | 58.2% · 39.5% · 2.3% |
| v2, learned limits | top 8 | M, ties at random | 13.0% | 83.5% | 55.5% · 40.9% · 3.6% |
| v2, learned limits | top 8 | M, then strange dimensions | 19.9% | 79.1% | 51.4% · 42.8% · 5.8% |
| v2, learned limits | top 8 | M, then second score | 18.1% | 5.5% | 57.4% · 37.2% · 5.4% |
| v2, learned limits | top 8 | static x M | 8.3% | 82.4% | 62.7% · 34.8% · 2.5% |
| v3 | top 4 | M, ties at random | 26.1% | 71.4% | 52.9% · 34.1% · 13.0% |
| v3 | top 4 | M, then strange dimensions | 28.4% | 42.9% | 50.9% · 35.1% · 14.0% |
| v3 | top 4 | M, then second score | 31.1% | 0.0% | 49.5% · 34.9% · 15.7% |
| v3 | top 4 | static x M | 16.3% | 59.3% | 54.7% · 37.0% · 8.3% |
| v3 | top 8 | M, ties at random | 39.2% | 61.5% | 59.0% · 31.1% · 9.9% |
| v3 | top 8 | M, then strange dimensions | 44.1% | 37.4% | 58.2% · 30.7% · 11.1% |
| v3 | top 8 | M, then second score | 44.8% | 1.1% | 58.3% · 30.3% · 11.4% |
| v3 | top 8 | static x M | 29.7% | 36.3% | 57.8% · 34.5% · 7.7% |
| v3 final | top 4 | M, ties at random | 26.4% | 70.3% | 52.7% · 34.3% · 13.1% |
| v3 final | top 4 | M, then strange dimensions | 32.0% | 40.7% | 51.1% · 32.9% · 16.1% |
| v3 final | top 4 | M, then second score | 32.8% | 1.1% | 50.2% · 33.1% · 16.8% |
| v3 final | top 4 | static x M | 18.7% | 54.9% | 54.1% · 36.4% · 9.4% |
| v3 final | top 8 | M, ties at random | 42.8% | 47.3% | 58.3% · 30.9% · 10.7% |
| v3 final | top 8 | M, then strange dimensions | 47.4% | 18.7% | 57.7% · 30.6% · 11.8% |
| v3 final | top 8 | M, then second score | 48.6% | 6.6% | 57.9% · 29.7% · 12.4% |
| v3 final | top 8 | static x M | 34.4% | 31.9% | 57.3% · 33.9% · 8.8% |
| v3 final, flat first-look rule | top 4 | M, ties at random | 27.1% | 70.3% | 52.4% · 34.2% · 13.4% |
| v3 final, flat first-look rule | top 4 | M, then strange dimensions | 31.8% | 41.8% | 48.1% · 35.9% · 16.0% |
| v3 final, flat first-look rule | top 4 | M, then second score | 33.3% | 1.1% | 48.9% · 34.1% · 17.0% |
| v3 final, flat first-look rule | top 4 | static x M | 17.5% | 60.4% | 54.0% · 37.0% · 8.9% |
| v3 final, flat first-look rule | top 8 | M, ties at random | 41.4% | 62.6% | 58.6% · 31.0% · 10.5% |
| v3 final, flat first-look rule | top 8 | M, then strange dimensions | 48.2% | 36.3% | 56.3% · 31.5% · 12.2% |
| v3 final, flat first-look rule | top 8 | M, then second score | 49.7% | 2.2% | 57.6% · 29.8% · 12.6% |
| v3 final, flat first-look rule | top 8 | static x M | 32.3% | 37.4% | 57.2% · 34.4% · 8.4% |
| v3 final, first look by asset only | top 4 | M, ties at random | 29.3% | 70.3% | 51.5% · 33.9% · 14.6% |
| v3 final, first look by asset only | top 4 | M, then strange dimensions | 35.1% | 40.7% | 49.9% · 32.5% · 17.7% |
| v3 final, first look by asset only | top 4 | M, then second score | 39.3% | 0.0% | 48.1% · 32.1% · 19.8% |
| v3 final, first look by asset only | top 4 | static x M | 18.7% | 54.9% | 54.1% · 36.4% · 9.4% |
| v3 final, first look by asset only | top 8 | M, ties at random | 46.9% | 49.5% | 57.6% · 30.7% · 11.8% |
| v3 final, first look by asset only | top 8 | M, then strange dimensions | 51.0% | 19.8% | 57.0% · 30.3% · 12.7% |
| v3 final, first look by asset only | top 8 | M, then second score | 54.6% | 7.7% | 57.1% · 29.2% · 13.7% |
| v3 final, first look by asset only | top 8 | static x M | 35.8% | 34.1% | 57.0% · 33.8% · 9.2% |
| v3 final, 5-call warm-up | top 4 | M, ties at random | 26.4% | 70.3% | 52.6% · 34.3% · 13.1% |
| v3 final, 5-call warm-up | top 4 | M, then strange dimensions | 32.0% | 40.7% | 50.8% · 33.1% · 16.1% |
| v3 final, 5-call warm-up | top 4 | M, then second score | 32.8% | 1.1% | 50.2% · 33.1% · 16.8% |
| v3 final, 5-call warm-up | top 4 | static x M | 18.7% | 54.9% | 54.0% · 36.5% · 9.4% |
| v3 final, 5-call warm-up | top 8 | M, ties at random | 42.8% | 47.3% | 58.3% · 31.0% · 10.7% |
| v3 final, 5-call warm-up | top 8 | M, then strange dimensions | 47.4% | 17.6% | 57.5% · 30.7% · 11.8% |
| v3 final, 5-call warm-up | top 8 | M, then second score | 48.6% | 5.5% | 57.9% · 29.7% · 12.4% |
| v3 final, 5-call warm-up | top 8 | static x M | 34.4% | 31.9% | 57.3% · 33.9% · 8.8% |
| v3 final, size limits per agent-day | top 4 | M, ties at random | 27.7% | 68.1% | 52.3% · 33.9% · 13.7% |
| v3 final, size limits per agent-day | top 4 | M, then strange dimensions | 33.2% | 40.7% | 52.0% · 31.5% · 16.5% |
| v3 final, size limits per agent-day | top 4 | M, then second score | 33.3% | 1.1% | 51.6% · 31.3% · 17.0% |
| v3 final, size limits per agent-day | top 4 | static x M | 18.0% | 57.1% | 55.1% · 35.8% · 9.1% |
| v3 final, size limits per agent-day | top 8 | M, ties at random | 44.5% | 44.0% | 58.5% · 30.3% · 11.3% |
| v3 final, size limits per agent-day | top 8 | M, then strange dimensions | 49.0% | 20.9% | 57.8% · 29.9% · 12.3% |
| v3 final, size limits per agent-day | top 8 | M, then second score | 49.7% | 6.6% | 58.5% · 28.7% · 12.8% |
| v3 final, size limits per agent-day | top 8 | static x M | 34.4% | 30.8% | 57.7% · 33.3% · 9.0% |
| v3 final, first look anchored at a read | top 4 | M, ties at random | 29.3% | 71.4% | 51.1% · 34.4% · 14.5% |
| v3 final, first look anchored at a read | top 4 | M, then strange dimensions | 35.0% | 39.6% | 50.0% · 32.6% · 17.5% |
| v3 final, first look anchored at a read | top 4 | M, then second score | 39.9% | 0.0% | 47.8% · 32.1% · 20.1% |
| v3 final, first look anchored at a read | top 4 | static x M | 18.6% | 56.0% | 54.3% · 36.4% · 9.4% |
| v3 final, first look anchored at a read | top 8 | M, ties at random | 46.9% | 52.7% | 57.7% · 30.6% · 11.8% |
| v3 final, first look anchored at a read | top 8 | M, then strange dimensions | 51.1% | 22.0% | 57.2% · 30.0% · 12.8% |
| v3 final, first look anchored at a read | top 8 | M, then second score | 55.2% | 6.6% | 56.8% · 29.3% · 13.9% |
| v3 final, first look anchored at a read | top 8 | static x M | 33.7% | 35.2% | 57.3% · 34.0% · 8.7% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, ties at random | 30.4% | 67.0% | 50.6% · 34.4% · 15.1% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, then strange dimensions | 36.2% | 38.5% | 50.5% · 31.6% · 17.9% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, then second score | 40.4% | 1.1% | 48.1% · 31.6% · 20.3% |
| v3 final, read anchor, sizes per agent-day | top 4 | static x M | 18.1% | 60.4% | 54.4% · 36.5% · 9.1% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, ties at random | 48.7% | 45.1% | 57.0% · 30.6% · 12.3% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, then strange dimensions | 53.1% | 23.1% | 56.6% · 30.0% · 13.4% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, then second score | 56.3% | 7.7% | 56.4% · 29.3% · 14.3% |
| v3 final, read anchor, sizes per agent-day | top 8 | static x M | 34.7% | 34.1% | 57.1% · 33.8% · 9.1% |
| v3 (decided), org discount on first looks | top 4 | M, ties at random | 30.6% | 68.1% | 50.7% · 34.1% · 15.2% |
| v3 (decided), org discount on first looks | top 4 | M, then strange dimensions | 36.4% | 35.2% | 50.1% · 31.8% · 18.1% |
| v3 (decided), org discount on first looks | top 4 | M, then second score | 39.9% | 1.1% | 48.1% · 31.9% · 20.1% |
| v3 (decided), org discount on first looks | top 4 | static x M | 18.3% | 58.2% | 54.0% · 36.8% · 9.2% |
| v3 (decided), org discount on first looks | top 8 | M, ties at random | 48.9% | 47.3% | 56.5% · 31.1% · 12.4% |
| v3 (decided), org discount on first looks | top 8 | M, then strange dimensions | 52.6% | 25.3% | 55.9% · 30.8% · 13.3% |
| v3 (decided), org discount on first looks | top 8 | M, then second score | 57.9% | 7.7% | 55.6% · 29.7% · 14.7% |
| v3 (decided), org discount on first looks | top 8 | static x M | 35.2% | 29.7% | 57.3% · 33.5% · 9.2% |
| v3 (decided) | top 4 | M, ties at random | 30.8% | 63.7% | 50.5% · 34.2% · 15.3% |
| v3 (decided) | top 4 | M, then strange dimensions | 36.8% | 28.6% | 50.0% · 32.0% · 18.1% |
| v3 (decided) | top 4 | M, then second score | 41.3% | 2.2% | 47.8% · 31.5% · 20.7% |
| v3 (decided) | top 4 | static x M | 18.3% | 58.2% | 54.7% · 36.1% · 9.2% |
| v3 (decided) | top 8 | M, ties at random | 49.5% | 47.3% | 56.7% · 30.7% · 12.6% |
| v3 (decided) | top 8 | M, then strange dimensions | 53.6% | 25.3% | 56.1% · 30.5% · 13.5% |
| v3 (decided) | top 8 | M, then second score | 57.4% | 6.6% | 56.3% · 29.1% · 14.6% |
| v3 (decided) | top 8 | static x M | 37.6% | 31.9% | 57.3% · 32.9% · 9.8% |
| v4 | top 4 | M, ties at random | 35.2% | 58.2% | 51.7% · 30.7% · 17.6% |
| v4 | top 4 | M, then strange dimensions | 38.3% | 28.6% | 51.2% · 29.9% · 18.9% |
| v4 | top 4 | M, then second score | 36.6% | 0.0% | 48.9% · 32.7% · 18.4% |
| v4 | top 4 | static x M | 21.6% | 37.4% | 55.6% · 33.4% · 11.0% |
| v4 | top 8 | M, ties at random | 56.9% | 27.5% | 56.5% · 29.0% · 14.5% |
| v4 | top 8 | M, then strange dimensions | 56.9% | 18.7% | 56.7% · 29.0% · 14.3% |
| v4 | top 8 | M, then second score | 57.4% | 1.1% | 56.3% · 29.0% · 14.7% |
| v4 | top 8 | static x M | 41.2% | 17.6% | 56.8% · 32.3% · 10.9% |
| v3 (decided), network and app in Footprint | top 4 | M, ties at random | 34.2% | 63.7% | 50.8% · 32.2% · 17.0% |
| v3 (decided), network and app in Footprint | top 4 | M, then strange dimensions | 38.8% | 26.4% | 49.4% · 31.6% · 19.0% |
| v3 (decided), network and app in Footprint | top 4 | M, then second score | 41.8% | 1.1% | 47.0% · 32.0% · 21.0% |
| v3 (decided), network and app in Footprint | top 4 | static x M | 20.8% | 45.1% | 55.4% · 34.1% · 10.5% |
| v3 (decided), network and app in Footprint | top 8 | M, ties at random | 55.5% | 35.2% | 56.0% · 30.0% · 14.1% |
| v3 (decided), network and app in Footprint | top 8 | M, then strange dimensions | 56.4% | 22.0% | 55.8% · 29.9% · 14.2% |
| v3 (decided), network and app in Footprint | top 8 | M, then second score | 59.6% | 1.1% | 55.4% · 29.5% · 15.1% |
| v3 (decided), network and app in Footprint | top 8 | static x M | 40.7% | 19.8% | 56.7% · 32.6% · 10.8% |
| v3 (decided), new tool through tool rarity | top 4 | M, ties at random | 31.7% | 67.0% | 50.8% · 33.4% · 15.8% |
| v3 (decided), new tool through tool rarity | top 4 | M, then strange dimensions | 38.0% | 34.1% | 49.8% · 31.4% · 18.8% |
| v3 (decided), new tool through tool rarity | top 4 | M, then second score | 41.5% | 3.3% | 47.7% · 31.4% · 20.9% |
| v3 (decided), new tool through tool rarity | top 4 | static x M | 17.5% | 50.5% | 55.6% · 35.5% · 8.9% |
| v3 (decided), new tool through tool rarity | top 8 | M, ties at random | 51.6% | 41.8% | 57.2% · 29.7% · 13.1% |
| v3 (decided), new tool through tool rarity | top 8 | M, then strange dimensions | 55.4% | 26.4% | 56.7% · 29.3% · 14.0% |
| v3 (decided), new tool through tool rarity | top 8 | M, then second score | 59.6% | 5.5% | 57.0% · 27.9% · 15.1% |
| v3 (decided), new tool through tool rarity | top 8 | static x M | 37.0% | 28.6% | 57.8% · 32.5% · 9.7% |

## Ordinary life and org-wide changes at x3 or more

| Change | days | v2 | v2, learned limits | v3 | v3 final | v3 final, flat first-look rule | v3 final, first look by asset only | v3 final, 5-call warm-up | v3 final, size limits per agent-day | v3 final, first look anchored at a read | v3 final, read anchor, sizes per agent-day | v3 (decided), org discount on first looks | v3 (decided) | v4 | v3 (decided), network and app in Footprint | v3 (decided), new tool through tool rarity |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| back_from_vacation | 372 | 70.2% (request_too_big) | 42.5% (sequence) | 11.0% (sensitive_first_look) | 8.3% (time_of_day) | 11.0% (sensitive_first_look) | 8.3% (request_too_big) | 8.3% (time_of_day) | 8.3% (request_too_big) | 8.9% (time_of_day) | 8.9% (request_too_big) | 8.1% (request_too_big) | 8.1% (request_too_big) | 6.7% (request_too_big) | 7.5% (request_too_big) | 7.3% (request_too_big) |
| client_switch | 47 | 76.6% (new_client) | 66.0% (new_client) | 48.9% (new_client) | 48.9% (new_client) | 48.9% (new_client) | 48.9% (new_client) | 48.9% (new_client) | 48.9% (new_client) | 48.9% (new_client) | 48.9% (new_client) | 48.9% (new_client) | 48.9% (new_client) | 48.9% (client) | 48.9% (client) | 48.9% (new_client) |
| isp_change | 19 | 78.9% (request_too_big) | 42.1% (new_network) | 36.8% (new_network) | 36.8% (new_network) | 36.8% (new_network) | 36.8% (new_network) | 36.8% (new_network) | 36.8% (new_network) | 36.8% (new_network) | 36.8% (new_network) | 36.8% (new_network) | 36.8% (new_network) | 26.3% (network) | 26.3% (network) | 36.8% (new_network) |
| monthly_report | 15 | 100.0% (asset) | 100.0% (asset) | 13.3% (asset) | 100.0% (many_assets) | 100.0% (many_assets) | 100.0% (many_assets) | 100.0% (many_assets) | 100.0% (many_assets) | 100.0% (many_assets) | 100.0% (many_assets) | 100.0% (many_assets) | 100.0% (many_assets) | 100.0% (many_assets) | 100.0% (many_assets) | 100.0% (many_assets) |
| new_hire | 74 | 79.7% (request_too_big) | 48.6% (sequence) | 29.7% (new_tool) | 21.6% (sequence) | 27.0% (sequence) | 21.6% (sequence) | 24.3% (new_tool) | 20.3% (sequence) | 23.0% (sequence) | 21.6% (sequence) | 20.3% (sequence) | 17.6% (request_too_big) | 13.5% (sequence) | 17.6% (new_tool) | 17.6% (sequence) |
| new_project | 1771 | 62.6% (request_too_big) | 39.0% (sequence) | 10.5% (request_too_big) | 9.9% (request_too_big) | 11.1% (request_too_big) | 9.9% (request_too_big) | 9.9% (request_too_big) | 8.6% (time_of_day) | 10.1% (request_too_big) | 8.9% (time_of_day) | 9.1% (time_of_day) | 8.4% (time_of_day) | 8.3% (time_of_day) | 8.4% (time_of_day) | 8.5% (time_of_day) |
| on_call_incident | 134 | 100.0% (sequence) | 100.0% (sequence) | 10.4% (time_of_day) | 9.7% (time_of_day) | 10.4% (time_of_day) | 9.7% (time_of_day) | 9.7% (time_of_day) | 9.7% (time_of_day) | 10.4% (time_of_day) | 10.4% (time_of_day) | 9.7% (time_of_day) | 9.7% (time_of_day) | 8.2% (time_of_day) | 8.2% (time_of_day) | 9.7% (time_of_day) |
| org_repo_migration | 277 | 65.7% (request_too_big) | 36.5% (sequence) | 9.4% (asset) | 9.4% (asset) | 11.7% (asset) | 9.4% (asset) | 9.4% (asset) | 9.7% (asset) | 10.8% (asset) | 11.2% (asset) | 9.0% (asset) | 9.2% (asset) | 9.4% (asset) | 9.4% (asset) | 9.8% (asset) |
| org_tool_rollout | 299 | 89.3% (new_tool) | 80.6% (new_tool) | 16.7% (tool) | 14.4% (tool) | 17.4% (tool) | 14.4% (tool) | 14.4% (tool) | 13.7% (tool) | 15.4% (tool) | 14.7% (tool) | 13.7% (tool) | 13.7% (tool) | 11.7% (tool) | 12.4% (tool) | 13.0% (tool) |
| org_vpn_change | 284 | 98.6% (new_network) | 97.2% (new_network) | 7.4% (time_of_day) | 7.7% (time_of_day) | 7.7% (time_of_day) | 7.7% (time_of_day) | 7.7% (time_of_day) | 7.4% (time_of_day) | 7.4% (time_of_day) | 7.0% (time_of_day) | 7.4% (time_of_day) | 7.4% (time_of_day) | 7.0% (time_of_day) | 7.0% (time_of_day) | 7.4% (time_of_day) |
| release_crunch | 796 | 81.0% (request_too_big) | 45.9% (sequence) | 31.2% (time_of_day) | 31.0% (time_of_day) | 31.2% (time_of_day) | 31.0% (time_of_day) | 31.2% (time_of_day) | 30.5% (time_of_day) | 30.9% (time_of_day) | 30.4% (time_of_day) | 30.4% (time_of_day) | 30.4% (time_of_day) | 30.3% (time_of_day) | 30.3% (time_of_day) | 30.4% (time_of_day) |
| role_change | 33 | 97.0% (sequence) | 84.8% (sequence) | 18.2% (new_tool) | 15.2% (new_tool) | 18.2% (new_tool) | 18.2% (new_tool) | 15.2% (new_tool) | 15.2% (new_tool) | 18.2% (new_tool) | 18.2% (new_tool) | 18.2% (new_tool) | 18.2% (new_tool) | 15.2% (tool) | 18.2% (new_tool) | 15.2% (tool) |
| team_transfer | 55 | 43.6% (request_too_big) | 18.2% (sequence) | 5.5% (sensitive_first_look) | 3.6% (request_too_big) | 5.5% (sensitive_first_look) | 3.6% (sequence) | 3.6% (request_too_big) | 3.6% (request_too_big) | 3.6% (request_too_big) | 3.6% (request_too_big) | 3.6% (sequence) | 1.8% (request_too_big) | 1.8% (request_too_big) | 1.8% (request_too_big) | 1.8% (request_too_big) |
| travel | 52 | 86.5% (request_too_big) | 57.7% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) |

## Gray episodes by kind

| Kind | episodes | v2: caught · calls ≥x3 | v2, learned limits: caught · calls ≥x3 | v3: caught · calls ≥x3 | v3 final: caught · calls ≥x3 | v3 final, flat first-look rule: caught · calls ≥x3 | v3 final, first look by asset only: caught · calls ≥x3 | v3 final, 5-call warm-up: caught · calls ≥x3 | v3 final, size limits per agent-day: caught · calls ≥x3 | v3 final, first look anchored at a read: caught · calls ≥x3 | v3 final, read anchor, sizes per agent-day: caught · calls ≥x3 | v3 (decided), org discount on first looks: caught · calls ≥x3 | v3 (decided): caught · calls ≥x3 | v4: caught · calls ≥x3 | v3 (decided), network and app in Footprint: caught · calls ≥x3 | v3 (decided), new tool through tool rarity: caught · calls ≥x3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| big_paste | 28 | 100.0% · 100.0% | 10.7% · 10.7% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| bot_loop | 3 | 100.0% · 97.2% | 100.0% · 95.9% | 100.0% · 96.5% | 100.0% · 96.5% | 100.0% · 96.5% | 100.0% · 96.5% | 100.0% · 96.5% | 100.0% · 96.5% | 100.0% · 96.5% | 100.0% · 96.5% | 100.0% · 96.5% | 100.0% · 96.5% | 100.0% · 96.5% | 100.0% · 96.5% | 100.0% · 96.5% |
| bulk_export | 26 | 3.8% · 0.2% | 3.8% · 0.2% | 65.4% · 6.1% | 100.0% · 77.4% | 100.0% · 77.6% | 100.0% · 77.6% | 100.0% · 77.4% | 100.0% · 77.4% | 100.0% · 77.5% | 100.0% · 77.5% | 100.0% · 77.3% | 100.0% · 77.4% | 100.0% · 77.7% | 100.0% · 77.7% | 100.0% · 77.7% |
| cross_copy | 17 | 100.0% · 38.5% | 100.0% · 38.5% | 47.1% · 28.6% | 41.2% · 25.1% | 47.1% · 28.6% | 41.2% · 25.1% | 41.2% · 25.1% | 41.2% · 25.1% | 41.2% · 25.1% | 41.2% · 25.1% | 41.2% · 25.1% | 47.1% · 29.3% | 47.1% · 29.3% | 47.1% · 29.3% | 47.1% · 29.3% |
| mass_cleanup | 11 | 0.0% · 0.0% | 0.0% · 0.0% | 18.2% · 6.4% | 18.2% · 6.4% | 18.2% · 6.4% | 18.2% · 6.4% | 18.2% · 6.4% | 18.2% · 6.4% | 18.2% · 6.4% | 18.2% · 6.4% | 18.2% · 6.4% | 18.2% · 6.4% | 18.2% · 6.4% | 18.2% · 6.4% | 18.2% · 6.4% |
| off_hours_batch | 9 | 22.2% · 0.7% | 22.2% · 0.7% | 77.8% · 77.8% | 77.8% · 77.8% | 77.8% · 77.8% | 77.8% · 77.8% | 77.8% · 77.8% | 77.8% · 77.8% | 77.8% · 77.8% | 77.8% · 77.8% | 77.8% · 77.8% | 77.8% · 77.8% | 77.8% · 77.8% | 77.8% · 77.8% | 77.8% · 77.8% |
| overfetch | 15 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% |
| scope_creep | 16 | 0.0% · 0.0% | 0.0% · 0.0% | 18.8% · 0.9% | 18.8% · 1.1% | 37.5% · 1.7% | 18.8% · 1.1% | 18.8% · 1.1% | 18.8% · 1.1% | 18.8% · 1.2% | 18.8% · 1.2% | 18.8% · 1.1% | 18.8% · 1.3% | 18.8% · 1.3% | 18.8% · 1.3% | 18.8% · 1.3% |
| sensitive_peek | 31 | 6.5% · 2.6% | 6.5% · 2.6% | 77.4% · 77.4% | 77.4% · 77.4% | 77.4% · 77.4% | 77.4% · 77.4% | 77.4% · 77.4% | 77.4% · 77.4% | 77.4% · 77.4% | 77.4% · 77.4% | 77.4% · 77.4% | 90.3% · 90.3% | 90.3% · 90.3% | 90.3% · 90.3% | 90.3% · 90.3% |
| shadow_script | 12 | 100.0% · 4.3% | 100.0% · 4.3% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| slow_loop | 15 | 6.7% · 2.4% | 6.7% · 2.4% | 100.0% · 80.8% | 100.0% · 80.7% | 100.0% · 80.7% | 100.0% · 80.7% | 100.0% · 80.7% | 100.0% · 80.7% | 100.0% · 80.8% | 100.0% · 80.8% | 100.0% · 80.8% | 100.0% · 80.8% | 100.0% · 80.8% | 100.0% · 80.8% | 100.0% · 80.8% |

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
