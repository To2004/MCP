# Mostly-ordinary organisation: results

150 agents, 180 days (scored: days 90-179), 3,537,070 messages, 79 gray episodes. Shipped-engine mirror checked on 232,628 messages.

Doc limits: burst > 20 a minute, request > 10 KB. Learned limits (policy.py, first 30 days): {'burst_per_minute': 48, 'request_limit_bytes': 618000, 'requires_before': {}}.

## False alarms and gray episodes

| Engine | Ordinary days ≥x3 | people | bots | ordinary calls ≥x3 | alerts/day (ordinary · change · gray) | gray caught ≥x3 | top causes on ordinary days |
|---|---|---|---|---|---|---|---|
| v2 | 64.2% | 72.2% | 25.2% | 3.7% | 46.4 · 22.7 · 1.2 | 38.0% | request_too_big 83%, sequence 12%, burst 4% |
| v2, learned limits | 20.0% | 23.3% | 3.9% | 1.9% | 14.5 · 13.3 · 0.7 | 19.0% | sequence 91%, burst 3%, new_tool 2% |
| v3 | 5.6% | 6.1% | 3.4% | 0.1% | 4.1 · 4.7 · 0.8 | 78.5% | sensitive_first_look 52%, request_too_big 30%, new_network 7% |
| v3 final | 2.7% | 2.6% | 3.4% | 0.1% | 1.9 · 4.0 · 0.7 | 78.5% | request_too_big 62%, new_network 16%, tool 10% |
| v3 final, flat first-look rule | 5.5% | 6.0% | 3.4% | 0.1% | 4.0 · 4.7 · 0.8 | 81.0% | sensitive_first_look 53%, request_too_big 30%, new_network 7% |
| v3 final, first look by asset only | 2.7% | 2.6% | 3.4% | 0.1% | 1.9 · 4.0 · 0.7 | 78.5% | request_too_big 62%, new_network 16%, tool 10% |
| v3 final, 5-call warm-up | 2.7% | 2.6% | 3.4% | 0.1% | 1.9 · 4.0 · 0.7 | 78.5% | request_too_big 62%, new_network 16%, tool 10% |
| v3 final, size limits per agent-day | 2.2% | 2.3% | 1.5% | 0.1% | 1.6 · 3.5 · 0.7 | 78.5% | request_too_big 54%, new_network 19%, tool 12% |
| v3 final, first look anchored at a read | 3.6% | 3.7% | 3.4% | 0.1% | 2.6 · 4.2 · 0.7 | 78.5% | request_too_big 47%, sensitive_first_look 23%, new_network 11% |
| v3 final, read anchor, sizes per agent-day | 3.1% | 3.5% | 1.5% | 0.1% | 2.3 · 3.7 · 0.7 | 78.5% | request_too_big 38%, sensitive_first_look 27%, new_network 13% |
| v3 (decided), org discount on first looks | 2.1% | 2.3% | 1.5% | 0.1% | 1.5 · 3.5 · 0.7 | 78.5% | request_too_big 55%, new_network 19%, new_tool 11% |
| v3 (decided) | 2.3% | 2.5% | 1.5% | 0.1% | 1.7 · 3.4 · 0.7 | 78.5% | request_too_big 52%, new_network 18%, new_tool 11% |
| v4 | 1.8% | 1.9% | 1.5% | 0.0% | 1.3 · 3.1 · 0.7 | 78.5% | request_too_big 65%, tool 22%, sequence 10% |
| v3 (decided), network and app in Footprint | 1.9% | 1.9% | 1.5% | 0.0% | 1.3 · 3.3 · 0.7 | 78.5% | request_too_big 65%, new_tool 14%, tool 12% |
| v3 (decided), new tool through tool rarity | 2.1% | 2.3% | 1.5% | 0.1% | 1.5 · 3.4 · 0.7 | 78.5% | request_too_big 56%, new_network 19%, tool 18% |

## Daily review list

Gray episodes caught when someone reviews the top-k agent-days each day (150 agents).

| Engine | list | gray caught | cut in a tie | list filled by ordinary · change · gray |
|---|---|---|---|---|
| v2 | top 4 | M, ties at random | 9.0% | 94.5% | 46.0% · 51.9% · 2.1% |
| v2 | top 4 | M, then strange dimensions | 12.7% | 76.9% | 38.3% · 58.5% · 3.1% |
| v2 | top 4 | M, then second score | 15.2% | 26.4% | 39.2% · 57.1% · 3.7% |
| v2 | top 4 | static x M | 7.5% | 96.7% | 54.3% · 43.8% · 1.8% |
| v2 | top 8 | M, ties at random | 14.4% | 91.2% | 50.9% · 47.0% · 1.8% |
| v2 | top 8 | M, then strange dimensions | 22.4% | 76.9% | 45.4% · 51.5% · 2.9% |
| v2 | top 8 | M, then second score | 26.4% | 12.1% | 46.9% · 49.4% · 3.4% |
| v2 | top 8 | static x M | 11.7% | 85.7% | 58.0% · 40.1% · 1.6% |
| v2, learned limits | top 4 | M, ties at random | 10.3% | 91.2% | 33.2% · 64.4% · 2.4% |
| v2, learned limits | top 4 | M, then strange dimensions | 13.3% | 76.9% | 32.4% · 64.3% · 3.3% |
| v2, learned limits | top 4 | M, then second score | 12.7% | 3.3% | 36.3% · 60.4% · 3.3% |
| v2, learned limits | top 4 | static x M | 8.4% | 90.1% | 41.6% · 56.3% · 2.1% |
| v2, learned limits | top 8 | M, ties at random | 19.6% | 80.2% | 41.6% · 55.7% · 2.4% |
| v2, learned limits | top 8 | M, then strange dimensions | 24.9% | 64.8% | 42.1% · 54.4% · 3.2% |
| v2, learned limits | top 8 | M, then second score | 24.1% | 8.8% | 43.4% · 53.4% · 2.9% |
| v2, learned limits | top 8 | static x M | 17.2% | 73.6% | 49.7% · 47.6% · 2.4% |
| v3 | top 4 | M, ties at random | 40.4% | 72.5% | 42.3% · 48.8% · 8.9% |
| v3 | top 4 | M, then strange dimensions | 39.1% | 29.7% | 43.4% · 47.6% · 8.9% |
| v3 | top 4 | M, then second score | 48.1% | 5.5% | 43.0% · 46.0% · 11.0% |
| v3 | top 4 | static x M | 33.2% | 45.1% | 42.2% · 50.3% · 7.5% |
| v3 | top 8 | M, ties at random | 61.9% | 53.8% | 48.1% · 44.4% · 7.3% |
| v3 | top 8 | M, then strange dimensions | 61.3% | 26.4% | 48.8% · 43.7% · 7.2% |
| v3 | top 8 | M, then second score | 62.0% | 9.9% | 50.7% · 41.7% · 7.3% |
| v3 | top 8 | static x M | 49.9% | 31.9% | 46.8% · 47.0% · 6.0% |
| v3 final | top 4 | M, ties at random | 46.7% | 56.0% | 35.6% · 54.2% · 10.1% |
| v3 final | top 4 | M, then strange dimensions | 49.4% | 22.0% | 36.1% · 53.1% · 10.7% |
| v3 final | top 4 | M, then second score | 51.9% | 5.5% | 36.0% · 52.8% · 11.3% |
| v3 final | top 4 | static x M | 35.9% | 36.3% | 37.7% · 54.0% · 8.3% |
| v3 final | top 8 | M, ties at random | 63.2% | 27.5% | 43.8% · 48.8% · 7.1% |
| v3 final | top 8 | M, then strange dimensions | 62.0% | 14.3% | 43.9% · 48.8% · 7.0% |
| v3 final | top 8 | M, then second score | 65.8% | 5.5% | 43.7% · 48.6% · 7.4% |
| v3 final | top 8 | static x M | 54.5% | 19.8% | 44.1% · 49.3% · 6.3% |
| v3 final, flat first-look rule | top 4 | M, ties at random | 42.3% | 70.3% | 41.3% · 49.4% · 9.4% |
| v3 final, flat first-look rule | top 4 | M, then strange dimensions | 41.4% | 30.8% | 42.4% · 48.2% · 9.4% |
| v3 final, flat first-look rule | top 4 | M, then second score | 49.4% | 4.4% | 42.2% · 46.6% · 11.3% |
| v3 final, flat first-look rule | top 4 | static x M | 33.3% | 47.3% | 40.6% · 51.9% · 7.5% |
| v3 final, flat first-look rule | top 8 | M, ties at random | 62.9% | 51.6% | 47.5% · 44.8% · 7.4% |
| v3 final, flat first-look rule | top 8 | M, then strange dimensions | 62.4% | 24.2% | 48.3% · 44.0% · 7.4% |
| v3 final, flat first-look rule | top 8 | M, then second score | 63.3% | 7.7% | 50.1% · 42.2% · 7.4% |
| v3 final, flat first-look rule | top 8 | static x M | 52.6% | 37.4% | 46.2% · 47.2% · 6.3% |
| v3 final, first look by asset only | top 4 | M, ties at random | 50.6% | 59.3% | 35.0% · 54.0% · 11.0% |
| v3 final, first look by asset only | top 4 | M, then strange dimensions | 53.4% | 20.9% | 35.9% · 52.5% · 11.6% |
| v3 final, first look by asset only | top 4 | M, then second score | 57.0% | 5.5% | 35.1% · 52.5% · 12.4% |
| v3 final, first look by asset only | top 4 | static x M | 35.9% | 36.3% | 37.7% · 54.0% · 8.3% |
| v3 final, first look by asset only | top 8 | M, ties at random | 68.7% | 37.4% | 43.5% · 48.4% · 7.8% |
| v3 final, first look by asset only | top 8 | M, then strange dimensions | 65.8% | 14.3% | 43.5% · 48.6% · 7.7% |
| v3 final, first look by asset only | top 8 | M, then second score | 72.2% | 5.5% | 42.6% · 48.8% · 8.4% |
| v3 final, first look by asset only | top 8 | static x M | 58.9% | 19.8% | 43.6% · 49.3% · 6.8% |
| v3 final, 5-call warm-up | top 4 | M, ties at random | 46.7% | 56.0% | 35.5% · 54.4% · 10.1% |
| v3 final, 5-call warm-up | top 4 | M, then strange dimensions | 49.4% | 22.0% | 36.1% · 53.1% · 10.7% |
| v3 final, 5-call warm-up | top 4 | M, then second score | 51.9% | 5.5% | 36.0% · 52.8% · 11.3% |
| v3 final, 5-call warm-up | top 4 | static x M | 35.9% | 36.3% | 37.3% · 54.3% · 8.3% |
| v3 final, 5-call warm-up | top 8 | M, ties at random | 63.2% | 27.5% | 43.7% · 48.9% · 7.1% |
| v3 final, 5-call warm-up | top 8 | M, then strange dimensions | 62.0% | 14.3% | 43.8% · 48.9% · 7.0% |
| v3 final, 5-call warm-up | top 8 | M, then second score | 65.8% | 5.5% | 43.6% · 48.8% · 7.4% |
| v3 final, 5-call warm-up | top 8 | static x M | 54.5% | 20.9% | 43.9% · 49.5% · 6.3% |
| v3 final, size limits per agent-day | top 4 | M, ties at random | 51.3% | 41.8% | 35.8% · 53.0% · 11.1% |
| v3 final, size limits per agent-day | top 4 | M, then strange dimensions | 52.2% | 9.9% | 35.8% · 52.9% · 11.3% |
| v3 final, size limits per agent-day | top 4 | M, then second score | 55.7% | 7.7% | 36.3% · 51.6% · 12.1% |
| v3 final, size limits per agent-day | top 4 | static x M | 36.2% | 28.6% | 39.9% · 51.9% · 8.1% |
| v3 final, size limits per agent-day | top 8 | M, ties at random | 65.6% | 30.8% | 44.9% · 47.4% · 7.4% |
| v3 final, size limits per agent-day | top 8 | M, then strange dimensions | 64.6% | 13.2% | 45.1% · 47.2% · 7.4% |
| v3 final, size limits per agent-day | top 8 | M, then second score | 67.1% | 6.6% | 45.2% · 46.9% · 7.6% |
| v3 final, size limits per agent-day | top 8 | static x M | 54.4% | 15.4% | 45.6% · 47.9% · 6.3% |
| v3 final, first look anchored at a read | top 4 | M, ties at random | 50.1% | 58.2% | 35.6% · 53.6% · 10.9% |
| v3 final, first look anchored at a read | top 4 | M, then strange dimensions | 54.1% | 17.6% | 36.1% · 52.2% · 11.7% |
| v3 final, first look anchored at a read | top 4 | M, then second score | 57.0% | 5.5% | 35.4% · 52.2% · 12.4% |
| v3 final, first look anchored at a read | top 4 | static x M | 35.6% | 35.2% | 39.3% · 52.7% · 8.0% |
| v3 final, first look anchored at a read | top 8 | M, ties at random | 68.9% | 36.3% | 44.8% · 47.1% · 7.8% |
| v3 final, first look anchored at a read | top 8 | M, then strange dimensions | 66.5% | 14.3% | 44.9% · 47.2% · 7.6% |
| v3 final, first look anchored at a read | top 8 | M, then second score | 72.2% | 7.7% | 44.4% · 47.2% · 8.1% |
| v3 final, first look anchored at a read | top 8 | static x M | 51.6% | 23.1% | 46.1% · 47.5% · 6.2% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, ties at random | 53.7% | 42.9% | 36.3% · 52.0% · 11.7% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, then strange dimensions | 55.7% | 8.8% | 36.5% · 51.4% · 12.1% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, then second score | 58.2% | 7.7% | 36.9% · 50.5% · 12.6% |
| v3 final, read anchor, sizes per agent-day | top 4 | static x M | 36.2% | 28.6% | 40.4% · 51.5% · 8.1% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, ties at random | 70.6% | 40.7% | 46.7% · 45.0% · 8.1% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, then strange dimensions | 69.0% | 19.8% | 46.9% · 44.9% · 7.9% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, then second score | 72.2% | 8.8% | 47.0% · 44.5% · 8.2% |
| v3 final, read anchor, sizes per agent-day | top 8 | static x M | 55.0% | 13.2% | 47.3% · 45.9% · 6.5% |
| v3 (decided), org discount on first looks | top 4 | M, ties at random | 54.4% | 46.2% | 34.9% · 53.2% · 11.8% |
| v3 (decided), org discount on first looks | top 4 | M, then strange dimensions | 57.0% | 13.2% | 34.8% · 52.6% · 12.5% |
| v3 (decided), org discount on first looks | top 4 | M, then second score | 59.5% | 7.7% | 35.2% · 51.9% · 12.9% |
| v3 (decided), org discount on first looks | top 4 | static x M | 34.9% | 26.4% | 39.9% · 52.6% · 7.6% |
| v3 (decided), org discount on first looks | top 8 | M, ties at random | 70.2% | 46.2% | 44.7% · 46.9% · 8.1% |
| v3 (decided), org discount on first looks | top 8 | M, then strange dimensions | 67.0% | 19.8% | 44.9% · 47.0% · 7.8% |
| v3 (decided), org discount on first looks | top 8 | M, then second score | 72.2% | 8.8% | 44.5% · 46.8% · 8.4% |
| v3 (decided), org discount on first looks | top 8 | static x M | 60.9% | 16.5% | 45.3% · 47.4% · 7.0% |
| v3 (decided) | top 4 | M, ties at random | 54.2% | 46.2% | 37.2% · 51.0% · 11.8% |
| v3 (decided) | top 4 | M, then strange dimensions | 55.5% | 15.4% | 37.5% · 50.4% · 12.0% |
| v3 (decided) | top 4 | M, then second score | 59.5% | 7.7% | 37.4% · 49.7% · 12.9% |
| v3 (decided) | top 4 | static x M | 35.8% | 29.7% | 40.9% · 51.1% · 8.0% |
| v3 (decided) | top 8 | M, ties at random | 69.9% | 50.5% | 46.0% · 45.8% · 8.0% |
| v3 (decided) | top 8 | M, then strange dimensions | 67.1% | 26.4% | 46.4% · 45.6% · 7.7% |
| v3 (decided) | top 8 | M, then second score | 72.2% | 8.8% | 45.7% · 45.6% · 8.4% |
| v3 (decided) | top 8 | static x M | 59.7% | 24.2% | 46.5% · 46.3% · 6.9% |
| v4 | top 4 | M, ties at random | 57.7% | 31.9% | 38.1% · 49.1% · 12.8% |
| v4 | top 4 | M, then strange dimensions | 57.6% | 7.7% | 38.1% · 49.1% · 12.8% |
| v4 | top 4 | M, then second score | 54.4% | 2.2% | 39.0% · 48.9% · 12.1% |
| v4 | top 4 | static x M | 39.1% | 22.0% | 42.0% · 49.0% · 9.0% |
| v4 | top 8 | M, ties at random | 72.4% | 36.3% | 46.2% · 45.2% · 8.3% |
| v4 | top 8 | M, then strange dimensions | 70.9% | 9.9% | 46.6% · 45.1% · 8.1% |
| v4 | top 8 | M, then second score | 72.2% | 0.0% | 46.0% · 45.3% · 8.4% |
| v4 | top 8 | static x M | 61.2% | 18.7% | 47.8% · 44.8% · 7.1% |
| v3 (decided), network and app in Footprint | top 4 | M, ties at random | 57.5% | 36.3% | 36.6% · 50.9% · 12.5% |
| v3 (decided), network and app in Footprint | top 4 | M, then strange dimensions | 55.7% | 9.9% | 36.7% · 51.2% · 12.1% |
| v3 (decided), network and app in Footprint | top 4 | M, then second score | 59.5% | 2.2% | 36.3% · 50.8% · 12.9% |
| v3 (decided), network and app in Footprint | top 4 | static x M | 39.5% | 20.9% | 42.6% · 48.6% · 8.8% |
| v3 (decided), network and app in Footprint | top 8 | M, ties at random | 72.3% | 38.5% | 45.2% · 46.3% · 8.2% |
| v3 (decided), network and app in Footprint | top 8 | M, then strange dimensions | 69.4% | 13.2% | 45.6% · 46.2% · 7.9% |
| v3 (decided), network and app in Footprint | top 8 | M, then second score | 70.9% | 3.3% | 45.0% · 46.6% · 8.1% |
| v3 (decided), network and app in Footprint | top 8 | static x M | 62.5% | 17.6% | 45.6% · 46.8% · 7.3% |
| v3 (decided), new tool through tool rarity | top 4 | M, ties at random | 54.4% | 39.6% | 35.9% · 52.2% · 11.8% |
| v3 (decided), new tool through tool rarity | top 4 | M, then strange dimensions | 55.7% | 9.9% | 36.0% · 51.9% · 12.1% |
| v3 (decided), new tool through tool rarity | top 4 | M, then second score | 62.0% | 5.5% | 35.9% · 50.6% · 13.5% |
| v3 (decided), new tool through tool rarity | top 4 | static x M | 38.5% | 24.2% | 39.9% · 51.5% · 8.6% |
| v3 (decided), new tool through tool rarity | top 8 | M, ties at random | 71.0% | 47.3% | 45.2% · 46.5% · 8.1% |
| v3 (decided), new tool through tool rarity | top 8 | M, then strange dimensions | 69.0% | 22.0% | 45.4% · 46.4% · 7.9% |
| v3 (decided), new tool through tool rarity | top 8 | M, then second score | 70.9% | 11.0% | 44.9% · 46.7% · 8.1% |
| v3 (decided), new tool through tool rarity | top 8 | static x M | 59.5% | 18.7% | 45.2% · 47.6% · 7.0% |

## Ordinary life and org-wide changes at x3 or more

| Change | days | v2 | v2, learned limits | v3 | v3 final | v3 final, flat first-look rule | v3 final, first look by asset only | v3 final, 5-call warm-up | v3 final, size limits per agent-day | v3 final, first look anchored at a read | v3 final, read anchor, sizes per agent-day | v3 (decided), org discount on first looks | v3 (decided) | v4 | v3 (decided), network and app in Footprint | v3 (decided), new tool through tool rarity |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| back_from_vacation | 181 | 78.5% (request_too_big) | 36.5% (sequence) | 12.7% (request_too_big) | 10.5% (request_too_big) | 12.7% (request_too_big) | 10.5% (request_too_big) | 10.5% (request_too_big) | 9.4% (request_too_big) | 11.0% (request_too_big) | 9.9% (request_too_big) | 10.5% (request_too_big) | 9.4% (request_too_big) | 7.2% (request_too_big) | 8.3% (request_too_big) | 9.4% (request_too_big) |
| client_switch | 27 | 81.5% (new_client) | 59.3% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 48.1% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 48.1% (new_client) | 48.1% (new_client) | 44.4% (new_client) | 44.4% (new_client) | 44.4% (client) | 44.4% (client) | 44.4% (new_client) |
| isp_change | 7 | 57.1% (request_too_big) | 28.6% (sequence) | 14.3% (new_network) | 14.3% (new_network) | 14.3% (new_network) | 14.3% (new_network) | 14.3% (new_network) | 14.3% (new_network) | 14.3% (new_network) | 14.3% (new_network) | 14.3% (new_network) | 14.3% (new_network) | 14.3% (network) | 14.3% (network) | 14.3% (new_network) |
| monthly_report | 15 | 100.0% (asset) | 100.0% (asset) | 66.7% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (many_assets) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) |
| new_hire | 65 | 98.5% (request_too_big) | 58.5% (sequence) | 52.3% (sensitive_first_look) | 30.8% (new_tool) | 50.8% (sensitive_first_look) | 30.8% (new_tool) | 35.4% (new_tool) | 30.8% (new_tool) | 35.4% (new_tool) | 35.4% (new_tool) | 29.2% (new_tool) | 29.2% (new_tool) | 13.8% (sequence) | 27.7% (new_tool) | 21.5% (sequence) |
| new_project | 1781 | 71.8% (request_too_big) | 41.0% (sequence) | 11.8% (request_too_big) | 10.2% (request_too_big) | 11.9% (request_too_big) | 10.2% (request_too_big) | 10.2% (request_too_big) | 8.0% (asset) | 11.1% (request_too_big) | 9.0% (asset) | 8.0% (asset) | 7.9% (asset) | 7.4% (asset) | 7.6% (asset) | 7.8% (asset) |
| on_call_incident | 48 | 100.0% (sequence) | 100.0% (sequence) | 25.0% (time_of_day) | 18.8% (time_of_day) | 25.0% (time_of_day) | 18.8% (time_of_day) | 18.8% (time_of_day) | 16.7% (time_of_day) | 20.8% (time_of_day) | 18.8% (time_of_day) | 16.7% (time_of_day) | 16.7% (time_of_day) | 16.7% (time_of_day) | 16.7% (time_of_day) | 16.7% (time_of_day) |
| org_repo_migration | 147 | 70.1% (request_too_big) | 40.8% (asset) | 23.1% (asset) | 21.7% (asset) | 24.5% (asset) | 21.7% (asset) | 21.7% (asset) | 19.6% (asset) | 20.5% (asset) | 19.9% (asset) | 17.6% (asset) | 17.4% (asset) | 17.4% (asset) | 19.4% (asset) | 19.4% (asset) |
| org_tool_rollout | 162 | 87.7% (request_too_big) | 75.9% (new_tool) | 17.9% (request_too_big) | 14.2% (request_too_big) | 17.9% (request_too_big) | 14.2% (request_too_big) | 14.2% (request_too_big) | 13.0% (new_tool) | 14.2% (request_too_big) | 13.0% (new_tool) | 13.0% (new_tool) | 13.0% (new_tool) | 11.7% (tool) | 11.7% (new_tool) | 13.0% (tool) |
| org_vpn_change | 130 | 99.2% (new_network) | 98.5% (new_network) | 22.3% (new_network) | 17.7% (new_network) | 21.5% (new_network) | 17.7% (new_network) | 18.5% (new_network) | 17.7% (new_network) | 18.5% (new_network) | 18.5% (new_network) | 18.5% (new_network) | 18.5% (new_network) | 14.6% (network) | 14.6% (network) | 16.2% (new_network) |
| release_crunch | 314 | 93.0% (request_too_big) | 42.4% (sequence) | 33.8% (time_of_day) | 31.8% (time_of_day) | 33.1% (time_of_day) | 31.8% (time_of_day) | 31.8% (time_of_day) | 29.9% (time_of_day) | 32.2% (time_of_day) | 30.3% (time_of_day) | 29.9% (time_of_day) | 29.9% (time_of_day) | 29.3% (time_of_day) | 29.9% (time_of_day) | 29.9% (time_of_day) |
| role_change | 20 | 90.0% (request_too_big) | 65.0% (sequence) | 15.0% (time_of_day) | 10.0% (time_of_day) | 15.0% (time_of_day) | 10.0% (time_of_day) | 10.0% (time_of_day) | 10.0% (time_of_day) | 10.0% (time_of_day) | 10.0% (time_of_day) | 10.0% (time_of_day) | 10.0% (time_of_day) | 5.0% (time_of_day) | 10.0% (time_of_day) | 5.0% (time_of_day) |
| team_transfer | 30 | 50.0% (request_too_big) | 16.7% (sequence) | 13.3% (sensitive_first_look) | 3.3% (request_too_big) | 13.3% (sensitive_first_look) | 3.3% (request_too_big) | 3.3% (request_too_big) | 3.3% (request_too_big) | 6.7% (request_too_big) | 6.7% (request_too_big) | 3.3% (request_too_big) | 3.3% (request_too_big) | 3.3% (request_too_big) | 3.3% (request_too_big) | 3.3% (request_too_big) |
| travel | 39 | 87.2% (request_too_big) | 56.4% (time_of_day) | 43.6% (time_of_day) | 38.5% (time_of_day) | 41.0% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) | 38.5% (time_of_day) |

## Gray episodes by kind

| Kind | episodes | v2: caught · calls ≥x3 | v2, learned limits: caught · calls ≥x3 | v3: caught · calls ≥x3 | v3 final: caught · calls ≥x3 | v3 final, flat first-look rule: caught · calls ≥x3 | v3 final, first look by asset only: caught · calls ≥x3 | v3 final, 5-call warm-up: caught · calls ≥x3 | v3 final, size limits per agent-day: caught · calls ≥x3 | v3 final, first look anchored at a read: caught · calls ≥x3 | v3 final, read anchor, sizes per agent-day: caught · calls ≥x3 | v3 (decided), org discount on first looks: caught · calls ≥x3 | v3 (decided): caught · calls ≥x3 | v4: caught · calls ≥x3 | v3 (decided), network and app in Footprint: caught · calls ≥x3 | v3 (decided), new tool through tool rarity: caught · calls ≥x3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| big_paste | 15 | 100.0% · 100.0% | 0.0% · 0.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| bot_loop | 3 | 100.0% · 97.1% | 100.0% · 93.0% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% |
| bulk_export | 10 | 0.0% · 0.0% | 0.0% · 0.0% | 90.0% · 6.3% | 100.0% · 80.3% | 100.0% · 80.8% | 100.0% · 80.5% | 100.0% · 80.3% | 100.0% · 80.3% | 100.0% · 80.5% | 100.0% · 80.5% | 100.0% · 80.5% | 100.0% · 80.5% | 100.0% · 80.5% | 100.0% · 80.3% | 100.0% · 80.3% |
| cross_copy | 7 | 100.0% · 41.8% | 100.0% · 41.8% | 85.7% · 45.9% | 85.7% · 45.9% | 85.7% · 45.9% | 85.7% · 45.9% | 85.7% · 45.9% | 85.7% · 45.9% | 85.7% · 45.9% | 85.7% · 45.9% | 85.7% · 45.9% | 85.7% · 45.9% | 85.7% · 45.9% | 85.7% · 45.9% | 85.7% · 45.9% |
| mass_cleanup | 5 | 0.0% · 0.0% | 0.0% · 0.0% | 20.0% · 8.7% | 20.0% · 8.7% | 20.0% · 8.7% | 20.0% · 8.7% | 20.0% · 8.7% | 20.0% · 8.7% | 20.0% · 8.7% | 20.0% · 8.7% | 20.0% · 8.7% | 20.0% · 8.7% | 20.0% · 8.7% | 20.0% · 8.7% | 20.0% · 8.7% |
| off_hours_batch | 5 | 20.0% · 0.9% | 20.0% · 0.9% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| overfetch | 6 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% |
| scope_creep | 8 | 0.0% · 0.0% | 0.0% · 0.0% | 50.0% · 2.7% | 37.5% · 0.8% | 62.5% · 2.9% | 37.5% · 0.8% | 37.5% · 0.8% | 37.5% · 0.8% | 37.5% · 0.8% | 37.5% · 0.8% | 37.5% · 0.8% | 37.5% · 0.8% | 37.5% · 0.8% | 37.5% · 0.8% | 37.5% · 0.8% |
| sensitive_peek | 9 | 11.1% · 3.7% | 11.1% · 3.7% | 88.9% · 88.9% | 88.9% · 88.9% | 88.9% · 88.9% | 88.9% · 88.9% | 88.9% · 88.9% | 88.9% · 88.9% | 88.9% · 88.9% | 88.9% · 88.9% | 88.9% · 88.9% | 88.9% · 88.9% | 88.9% · 88.9% | 88.9% · 88.9% | 88.9% · 88.9% |
| shadow_script | 3 | 100.0% · 6.8% | 100.0% · 6.8% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| slow_loop | 8 | 0.0% · 0.0% | 0.0% · 0.0% | 100.0% · 81.9% | 100.0% · 81.9% | 100.0% · 81.9% | 100.0% · 81.9% | 100.0% · 81.9% | 100.0% · 81.9% | 100.0% · 81.9% | 100.0% · 81.9% | 100.0% · 81.9% | 100.0% · 82.1% | 100.0% · 82.1% | 100.0% · 82.0% | 100.0% · 82.0% |

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
