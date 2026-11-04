# Mostly-ordinary organisation: results

150 agents, 180 days (scored: days 90-179), 3,549,732 messages, 84 gray episodes. Shipped-engine mirror checked on 237,091 messages.

Doc limits: burst > 20 a minute, request > 10 KB. Learned limits (policy.py, first 30 days): {'burst_per_minute': 48, 'request_limit_bytes': 110000, 'requires_before': {'fork_repository': ['get_file_contents']}}.

## False alarms and gray episodes

| Engine | Ordinary days ≥x3 | people | bots | ordinary calls ≥x3 | alerts/day (ordinary · change · gray) | gray caught ≥x3 | top causes on ordinary days |
|---|---|---|---|---|---|---|---|
| v1 (shipped) | 51.9% | 59.0% | 21.5% | 2.5% | 41.5 · 15.9 · 1.1 | 32.1% | request_too_big 68%, sequence 28%, burst 2% |
| v2 | 51.9% | 59.0% | 21.5% | 2.5% | 41.6 · 16.0 · 1.1 | 32.1% | request_too_big 68%, sequence 28%, burst 2% |
| v2, learned limits | 22.8% | 25.6% | 10.8% | 2.0% | 18.3 · 11.5 · 0.8 | 32.1% | sequence 90%, new_tool 3%, new_network 2% |
| v2 + recommended (first look only), learned limits | 7.3% | 8.0% | 4.7% | 0.3% | 5.9 · 4.8 · 0.7 | 70.2% | asset 42%, request_too_big 31%, tool 13% |
| v3 | 6.5% | 6.9% | 4.7% | 0.2% | 5.2 · 4.4 · 0.7 | 65.5% | sensitive_first_look 48%, request_too_big 35%, new_network 8% |
| v3 final | 3.4% | 3.1% | 4.8% | 0.2% | 2.7 · 3.8 · 0.6 | 64.3% | request_too_big 66%, new_network 14%, tool 9% |
| v3 final, flat first-look rule | 6.4% | 6.8% | 4.8% | 0.2% | 5.1 · 4.5 · 0.7 | 69.0% | sensitive_first_look 47%, request_too_big 35%, new_network 8% |
| v3 final, first look by asset only | 3.4% | 3.1% | 4.8% | 0.2% | 2.7 · 3.8 · 0.6 | 64.3% | request_too_big 66%, new_network 14%, tool 9% |
| v3 final, 5-call warm-up | 3.4% | 3.1% | 4.8% | 0.2% | 2.7 · 3.8 · 0.6 | 64.3% | request_too_big 66%, new_network 14%, tool 9% |
| v3 final, size limits per agent-day | 3.4% | 3.3% | 3.8% | 0.2% | 2.7 · 3.5 · 0.6 | 64.3% | request_too_big 66%, new_network 14%, tool 9% |
| v3 final, first look anchored at a read | 4.3% | 4.1% | 4.8% | 0.2% | 3.4 · 4.0 · 0.7 | 64.3% | request_too_big 53%, sensitive_first_look 18%, new_network 12% |
| v3 final, read anchor, sizes per agent-day | 4.2% | 4.3% | 3.8% | 0.2% | 3.4 · 3.7 · 0.6 | 64.3% | request_too_big 53%, sensitive_first_look 18%, new_network 12% |
| v3 (decided), org discount on first looks | 3.3% | 3.2% | 3.8% | 0.2% | 2.7 · 3.5 · 0.6 | 64.3% | request_too_big 66%, new_network 14%, tool 9% |
| v3 (decided) | 3.4% | 3.3% | 3.8% | 0.2% | 2.7 · 3.4 · 0.6 | 65.5% | request_too_big 66%, new_network 14%, tool 9% |
| v4 | 2.8% | 2.6% | 3.8% | 0.1% | 2.3 · 3.2 · 0.6 | 65.5% | request_too_big 78%, tool 16%, network 2% |
| v3 (decided), network and app in Footprint | 2.9% | 2.7% | 3.8% | 0.1% | 2.3 · 3.3 · 0.6 | 65.5% | request_too_big 76%, tool 10%, new_tool 8% |
| v3 (decided), new tool through tool rarity | 3.3% | 3.1% | 3.8% | 0.2% | 2.6 · 3.3 · 0.6 | 65.5% | request_too_big 67%, new_network 15%, tool 14% |

## Daily review list

Gray episodes caught when someone reviews the top-k agent-days each day (150 agents).

| Engine | list | gray caught | cut in a tie | list filled by ordinary · change · gray |
|---|---|---|---|---|
| v1 (shipped) | top 4 | M, ties at random | 19.6% | 87.9% | 56.2% · 39.2% · 4.6% |
| v1 (shipped) | top 4 | M, then strange dimensions | 20.0% | 73.6% | 52.8% · 42.4% · 4.7% |
| v1 (shipped) | top 4 | static x M | 13.9% | 92.3% | 62.9% · 33.8% · 3.3% |
| v1 (shipped) | top 8 | M, ties at random | 24.6% | 84.6% | 60.1% · 36.5% · 3.0% |
| v1 (shipped) | top 8 | M, then strange dimensions | 24.6% | 63.7% | 57.5% · 38.7% · 3.4% |
| v1 (shipped) | top 8 | static x M | 17.7% | 81.3% | 65.0% · 32.4% · 2.2% |
| v2 | top 4 | M, ties at random | 14.3% | 93.4% | 56.3% · 40.3% · 3.4% |
| v2 | top 4 | M, then strange dimensions | 16.5% | 71.4% | 49.0% · 47.1% · 3.9% |
| v2 | top 4 | static x M | 5.8% | 94.5% | 62.8% · 35.7% · 1.4% |
| v2 | top 8 | M, ties at random | 19.2% | 89.0% | 60.0% · 37.2% · 2.4% |
| v2 | top 8 | M, then strange dimensions | 22.8% | 75.8% | 55.3% · 41.1% · 3.2% |
| v2 | top 8 | static x M | 10.2% | 82.4% | 65.4% · 32.8% · 1.4% |
| v2, learned limits | top 4 | M, ties at random | 15.9% | 90.1% | 48.9% · 47.3% · 3.8% |
| v2, learned limits | top 4 | M, then strange dimensions | 19.7% | 74.7% | 46.7% · 48.4% · 4.8% |
| v2, learned limits | top 4 | static x M | 6.8% | 91.2% | 56.0% · 42.3% · 1.8% |
| v2, learned limits | top 8 | M, ties at random | 21.9% | 82.4% | 54.0% · 42.8% · 2.8% |
| v2, learned limits | top 8 | M, then strange dimensions | 26.1% | 65.9% | 53.0% · 42.9% · 3.7% |
| v2, learned limits | top 8 | static x M | 12.7% | 74.7% | 60.1% · 37.7% · 1.8% |
| v2 + recommended (first look only), learned limits | top 4 | M, ties at random | 39.3% | 0.0% | 57.4% · 33.5% · 9.1% |
| v2 + recommended (first look only), learned limits | top 4 | M, then strange dimensions | 39.3% | 0.0% | 57.4% · 33.5% · 9.1% |
| v2 + recommended (first look only), learned limits | top 4 | static x M | 21.4% | 0.0% | 53.6% · 41.2% · 5.2% |
| v2 + recommended (first look only), learned limits | top 8 | M, ties at random | 53.6% | 0.0% | 60.3% · 32.8% · 6.5% |
| v2 + recommended (first look only), learned limits | top 8 | M, then strange dimensions | 53.6% | 0.0% | 60.3% · 32.8% · 6.5% |
| v2 + recommended (first look only), learned limits | top 8 | static x M | 46.4% | 0.0% | 57.0% · 36.7% · 5.9% |
| v3 | top 4 | M, ties at random | 31.9% | 64.8% | 53.3% · 39.2% · 7.5% |
| v3 | top 4 | M, then strange dimensions | 34.9% | 24.2% | 53.1% · 38.8% · 8.0% |
| v3 | top 4 | M, then second score | 32.1% | 1.1% | 54.8% · 37.8% · 7.4% |
| v3 | top 4 | static x M | 25.2% | 46.2% | 52.4% · 41.6% · 6.0% |
| v3 | top 8 | M, ties at random | 48.9% | 57.1% | 58.0% · 35.7% · 5.9% |
| v3 | top 8 | M, then strange dimensions | 51.5% | 36.3% | 58.5% · 34.9% · 6.2% |
| v3 | top 8 | M, then second score | 50.0% | 8.8% | 58.9% · 34.6% · 6.0% |
| v3 | top 8 | static x M | 41.1% | 37.4% | 55.0% · 39.6% · 4.9% |
| v3 final | top 4 | M, ties at random | 38.0% | 42.9% | 48.7% · 42.6% · 8.7% |
| v3 final | top 4 | M, then strange dimensions | 41.3% | 24.2% | 48.4% · 42.1% · 9.5% |
| v3 final | top 4 | M, then second score | 42.3% | 4.4% | 48.7% · 41.6% · 9.8% |
| v3 final | top 4 | static x M | 32.8% | 27.5% | 51.1% · 41.4% · 7.6% |
| v3 final | top 8 | M, ties at random | 57.2% | 30.8% | 53.2% · 39.6% · 6.7% |
| v3 final | top 8 | M, then strange dimensions | 58.3% | 18.7% | 53.1% · 39.6% · 6.9% |
| v3 final | top 8 | M, then second score | 58.3% | 8.8% | 53.2% · 39.6% · 6.9% |
| v3 final | top 8 | static x M | 42.9% | 26.4% | 54.3% · 40.2% · 5.1% |
| v3 final, flat first-look rule | top 4 | M, ties at random | 32.0% | 64.8% | 53.3% · 39.2% · 7.5% |
| v3 final, flat first-look rule | top 4 | M, then strange dimensions | 37.0% | 26.4% | 52.5% · 39.0% · 8.5% |
| v3 final, flat first-look rule | top 4 | M, then second score | 31.0% | 1.1% | 54.0% · 38.9% · 7.1% |
| v3 final, flat first-look rule | top 4 | static x M | 28.7% | 48.4% | 52.2% · 41.0% · 6.8% |
| v3 final, flat first-look rule | top 8 | M, ties at random | 49.7% | 56.0% | 57.8% · 35.8% · 5.9% |
| v3 final, flat first-look rule | top 8 | M, then strange dimensions | 52.9% | 37.4% | 58.3% · 34.9% · 6.4% |
| v3 final, flat first-look rule | top 8 | M, then second score | 52.4% | 11.0% | 58.2% · 35.1% · 6.3% |
| v3 final, flat first-look rule | top 8 | static x M | 43.9% | 41.8% | 54.8% · 39.5% · 5.2% |
| v3 final, first look by asset only | top 4 | M, ties at random | 42.6% | 44.0% | 48.2% · 42.0% · 9.8% |
| v3 final, first look by asset only | top 4 | M, then strange dimensions | 46.6% | 22.0% | 47.9% · 41.4% · 10.8% |
| v3 final, first look by asset only | top 4 | M, then second score | 48.2% | 3.3% | 47.4% · 41.5% · 11.1% |
| v3 final, first look by asset only | top 4 | static x M | 33.0% | 27.5% | 51.0% · 41.4% · 7.6% |
| v3 final, first look by asset only | top 8 | M, ties at random | 60.7% | 36.3% | 53.6% · 38.9% · 7.1% |
| v3 final, first look by asset only | top 8 | M, then strange dimensions | 63.1% | 16.5% | 53.6% · 38.6% · 7.4% |
| v3 final, first look by asset only | top 8 | M, then second score | 61.9% | 7.7% | 53.4% · 38.9% · 7.3% |
| v3 final, first look by asset only | top 8 | static x M | 49.4% | 26.4% | 54.0% · 39.7% · 5.9% |
| v3 final, 5-call warm-up | top 4 | M, ties at random | 37.8% | 42.9% | 48.6% · 42.7% · 8.7% |
| v3 final, 5-call warm-up | top 4 | M, then strange dimensions | 41.2% | 24.2% | 48.2% · 42.3% · 9.5% |
| v3 final, 5-call warm-up | top 4 | M, then second score | 42.3% | 4.4% | 48.7% · 41.6% · 9.8% |
| v3 final, 5-call warm-up | top 4 | static x M | 32.5% | 28.6% | 50.9% · 41.6% · 7.5% |
| v3 final, 5-call warm-up | top 8 | M, ties at random | 57.2% | 30.8% | 53.1% · 39.8% · 6.7% |
| v3 final, 5-call warm-up | top 8 | M, then strange dimensions | 58.3% | 15.4% | 52.8% · 40.0% · 6.9% |
| v3 final, 5-call warm-up | top 8 | M, then second score | 58.3% | 7.7% | 52.8% · 39.9% · 6.9% |
| v3 final, 5-call warm-up | top 8 | static x M | 42.9% | 26.4% | 54.2% · 40.3% · 5.1% |
| v3 final, size limits per agent-day | top 4 | M, ties at random | 36.9% | 41.8% | 51.8% · 39.8% · 8.4% |
| v3 final, size limits per agent-day | top 4 | M, then strange dimensions | 40.7% | 20.9% | 51.9% · 39.0% · 9.1% |
| v3 final, size limits per agent-day | top 4 | M, then second score | 41.7% | 4.4% | 52.4% · 38.3% · 9.3% |
| v3 final, size limits per agent-day | top 4 | static x M | 30.0% | 27.5% | 53.7% · 39.4% · 6.9% |
| v3 final, size limits per agent-day | top 8 | M, ties at random | 58.7% | 26.4% | 55.4% · 37.2% · 6.9% |
| v3 final, size limits per agent-day | top 8 | M, then strange dimensions | 59.5% | 14.3% | 55.4% · 37.2% · 7.0% |
| v3 final, size limits per agent-day | top 8 | M, then second score | 60.7% | 5.5% | 55.3% · 37.1% · 7.1% |
| v3 final, size limits per agent-day | top 8 | static x M | 40.9% | 18.7% | 56.4% · 38.3% · 4.9% |
| v3 final, first look anchored at a read | top 4 | M, ties at random | 42.6% | 48.4% | 48.8% · 41.3% · 9.9% |
| v3 final, first look anchored at a read | top 4 | M, then strange dimensions | 46.6% | 22.0% | 48.6% · 40.6% · 10.8% |
| v3 final, first look anchored at a read | top 4 | M, then second score | 48.2% | 3.3% | 47.9% · 40.9% · 11.1% |
| v3 final, first look anchored at a read | top 4 | static x M | 32.1% | 33.0% | 52.7% · 39.8% · 7.5% |
| v3 final, first look anchored at a read | top 8 | M, ties at random | 59.9% | 31.9% | 55.2% · 37.4% · 7.0% |
| v3 final, first look anchored at a read | top 8 | M, then strange dimensions | 63.1% | 17.6% | 55.1% · 37.0% · 7.4% |
| v3 final, first look anchored at a read | top 8 | M, then second score | 60.7% | 7.7% | 55.1% · 37.4% · 7.1% |
| v3 final, first look anchored at a read | top 8 | static x M | 44.1% | 23.1% | 55.1% · 39.2% · 5.4% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, ties at random | 41.9% | 46.2% | 51.6% · 38.7% · 9.7% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, then strange dimensions | 46.0% | 22.0% | 52.0% · 37.6% · 10.3% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, then second score | 47.6% | 3.3% | 51.9% · 37.1% · 11.0% |
| v3 final, read anchor, sizes per agent-day | top 4 | static x M | 30.0% | 31.9% | 54.3% · 38.7% · 7.0% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, ties at random | 60.6% | 30.8% | 57.1% · 35.3% · 7.2% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, then strange dimensions | 63.1% | 14.3% | 56.9% · 35.3% · 7.4% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, then second score | 60.7% | 6.6% | 57.3% · 35.0% · 7.3% |
| v3 final, read anchor, sizes per agent-day | top 8 | static x M | 42.2% | 16.5% | 56.4% · 38.0% · 5.1% |
| v3 (decided), org discount on first looks | top 4 | M, ties at random | 42.2% | 41.8% | 51.2% · 39.1% · 9.7% |
| v3 (decided), org discount on first looks | top 4 | M, then strange dimensions | 45.8% | 18.7% | 51.5% · 38.2% · 10.3% |
| v3 (decided), org discount on first looks | top 4 | M, then second score | 47.6% | 3.3% | 51.4% · 37.6% · 11.0% |
| v3 (decided), org discount on first looks | top 4 | static x M | 31.2% | 26.4% | 53.7% · 39.1% · 7.2% |
| v3 (decided), org discount on first looks | top 8 | M, ties at random | 62.6% | 35.2% | 55.2% · 37.0% · 7.4% |
| v3 (decided), org discount on first looks | top 8 | M, then strange dimensions | 65.5% | 14.3% | 55.2% · 36.7% · 7.7% |
| v3 (decided), org discount on first looks | top 8 | M, then second score | 63.1% | 6.6% | 55.4% · 36.6% · 7.6% |
| v3 (decided), org discount on first looks | top 8 | static x M | 49.1% | 20.9% | 56.4% · 37.4% · 5.8% |
| v3 (decided) | top 4 | M, ties at random | 44.3% | 41.8% | 51.7% · 38.2% · 10.2% |
| v3 (decided) | top 4 | M, then strange dimensions | 48.8% | 19.8% | 51.9% · 37.1% · 11.0% |
| v3 (decided) | top 4 | M, then second score | 50.0% | 2.2% | 51.9% · 36.5% · 11.5% |
| v3 (decided) | top 4 | static x M | 31.0% | 27.5% | 54.4% · 38.4% · 7.2% |
| v3 (decided) | top 8 | M, ties at random | 62.8% | 39.6% | 55.8% · 36.3% · 7.5% |
| v3 (decided) | top 8 | M, then strange dimensions | 66.1% | 16.5% | 55.5% · 36.3% · 7.8% |
| v3 (decided) | top 8 | M, then second score | 61.9% | 7.7% | 56.2% · 36.0% · 7.4% |
| v3 (decided) | top 8 | static x M | 48.5% | 28.6% | 56.3% · 37.5% · 5.8% |
| v4 | top 4 | M, ties at random | 47.1% | 29.7% | 52.7% · 36.5% · 10.8% |
| v4 | top 4 | M, then strange dimensions | 51.2% | 11.0% | 52.4% · 36.0% · 11.6% |
| v4 | top 4 | M, then second score | 47.6% | 0.0% | 53.0% · 36.0% · 11.0% |
| v4 | top 4 | static x M | 32.8% | 14.3% | 53.3% · 39.1% · 7.6% |
| v4 | top 8 | M, ties at random | 63.8% | 33.0% | 55.0% · 37.0% · 7.6% |
| v4 | top 8 | M, then strange dimensions | 65.5% | 11.0% | 54.9% · 37.0% · 7.7% |
| v4 | top 8 | M, then second score | 64.3% | 2.2% | 54.7% · 37.2% · 7.7% |
| v4 | top 8 | static x M | 50.8% | 20.9% | 55.9% · 37.6% · 6.1% |
| v3 (decided), network and app in Footprint | top 4 | M, ties at random | 47.3% | 33.0% | 51.4% · 37.8% · 10.8% |
| v3 (decided), network and app in Footprint | top 4 | M, then strange dimensions | 52.8% | 13.2% | 51.2% · 36.9% · 11.9% |
| v3 (decided), network and app in Footprint | top 4 | M, then second score | 51.2% | 0.0% | 51.4% · 36.8% · 11.8% |
| v3 (decided), network and app in Footprint | top 4 | static x M | 33.6% | 15.4% | 51.8% · 40.5% · 7.8% |
| v3 (decided), network and app in Footprint | top 8 | M, ties at random | 63.2% | 37.4% | 54.5% · 37.6% · 7.5% |
| v3 (decided), network and app in Footprint | top 8 | M, then strange dimensions | 65.5% | 14.3% | 54.4% · 37.5% · 7.7% |
| v3 (decided), network and app in Footprint | top 8 | M, then second score | 63.1% | 2.2% | 54.3% · 37.8% · 7.6% |
| v3 (decided), network and app in Footprint | top 8 | static x M | 50.2% | 23.1% | 55.1% · 38.5% · 6.0% |
| v3 (decided), new tool through tool rarity | top 4 | M, ties at random | 43.7% | 35.2% | 53.0% · 36.9% · 10.0% |
| v3 (decided), new tool through tool rarity | top 4 | M, then strange dimensions | 48.8% | 15.4% | 53.2% · 35.8% · 11.0% |
| v3 (decided), new tool through tool rarity | top 4 | M, then second score | 47.6% | 1.1% | 53.6% · 35.4% · 11.0% |
| v3 (decided), new tool through tool rarity | top 4 | static x M | 31.1% | 24.2% | 54.7% · 38.1% · 7.2% |
| v3 (decided), new tool through tool rarity | top 8 | M, ties at random | 62.8% | 39.6% | 56.4% · 35.9% · 7.3% |
| v3 (decided), new tool through tool rarity | top 8 | M, then strange dimensions | 65.5% | 20.9% | 56.2% · 35.9% · 7.6% |
| v3 (decided), new tool through tool rarity | top 8 | M, then second score | 63.1% | 7.7% | 56.4% · 35.8% · 7.4% |
| v3 (decided), new tool through tool rarity | top 8 | static x M | 50.0% | 24.2% | 56.0% · 37.6% · 6.0% |

## Ordinary life and org-wide changes at x3 or more

| Change | days | v1 (shipped) | v2 | v2, learned limits | v2 + recommended (first look only), learned limits | v3 | v3 final | v3 final, flat first-look rule | v3 final, first look by asset only | v3 final, 5-call warm-up | v3 final, size limits per agent-day | v3 final, first look anchored at a read | v3 final, read anchor, sizes per agent-day | v3 (decided), org discount on first looks | v3 (decided) | v4 | v3 (decided), network and app in Footprint | v3 (decided), new tool through tool rarity |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| back_from_vacation | 186 | 63.4% (request_too_big) | 64.0% (request_too_big) | 37.6% (sequence) | 14.0% (asset) | 11.8% (sensitive_first_look) | 7.5% (request_too_big) | 11.8% (sensitive_first_look) | 7.5% (request_too_big) | 7.5% (request_too_big) | 5.9% (request_too_big) | 7.5% (request_too_big) | 5.9% (request_too_big) | 5.9% (request_too_big) | 5.4% (request_too_big) | 4.8% (request_too_big) | 5.4% (request_too_big) | 4.8% (request_too_big) |
| client_switch | 20 | 85.0% (new_client) | 85.0% (new_client) | 65.0% (new_client) | 50.0% (new_client) | 50.0% (new_client) | 50.0% (new_client) | 50.0% (new_client) | 50.0% (new_client) | 50.0% (new_client) | 50.0% (new_client) | 50.0% (new_client) | 50.0% (new_client) | 50.0% (new_client) | 50.0% (new_client) | 40.0% (client) | 40.0% (client) | 50.0% (new_client) |
| isp_change | 12 | 75.0% (sequence) | 75.0% (sequence) | 66.7% (sequence) | 50.0% (new_network) | 50.0% (new_network) | 41.7% (new_network) | 50.0% (new_network) | 41.7% (new_network) | 41.7% (new_network) | 41.7% (new_network) | 41.7% (new_network) | 41.7% (new_network) | 41.7% (new_network) | 41.7% (new_network) | 25.0% (network) | 25.0% (network) | 41.7% (new_network) |
| monthly_report | 15 | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 86.7% (burst) | 73.3% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) |
| new_hire | 67 | 74.6% (request_too_big) | 77.6% (request_too_big) | 53.7% (sequence) | 44.8% (new_tool) | 52.2% (new_tool) | 31.3% (new_tool) | 50.7% (sensitive_first_look) | 31.3% (new_tool) | 32.8% (new_tool) | 31.3% (new_tool) | 46.3% (new_tool) | 46.3% (new_tool) | 32.8% (new_tool) | 31.3% (new_tool) | 16.4% (sequence) | 28.4% (new_tool) | 20.9% (sequence) |
| new_project | 948 | 63.4% (sequence) | 63.7% (sequence) | 44.3% (sequence) | 16.5% (asset) | 14.5% (request_too_big) | 12.1% (request_too_big) | 14.3% (request_too_big) | 12.1% (request_too_big) | 12.2% (request_too_big) | 10.1% (asset) | 13.2% (request_too_big) | 11.0% (asset) | 10.6% (asset) | 10.4% (asset) | 10.2% (asset) | 10.5% (asset) | 10.2% (asset) |
| on_call_incident | 74 | 100.0% (sequence) | 100.0% (sequence) | 100.0% (sequence) | 14.9% (tool) | 9.5% (time_of_day) | 9.5% (time_of_day) | 9.5% (time_of_day) | 9.5% (time_of_day) | 9.5% (time_of_day) | 9.5% (time_of_day) | 9.5% (time_of_day) | 9.5% (time_of_day) | 9.5% (time_of_day) | 9.5% (time_of_day) | 9.5% (time_of_day) | 9.5% (time_of_day) | 9.5% (time_of_day) |
| org_repo_migration | 162 | 61.7% (request_too_big) | 61.7% (request_too_big) | 43.2% (sequence) | 19.1% (asset) | 17.0% (asset) | 17.7% (asset) | 18.3% (asset) | 17.7% (asset) | 17.7% (asset) | 18.3% (asset) | 17.7% (asset) | 18.4% (asset) | 19.4% (asset) | 17.5% (asset) | 18.2% (asset) | 18.2% (asset) | 18.2% (asset) |
| org_tool_rollout | 159 | 79.9% (request_too_big) | 85.5% (new_tool) | 76.7% (new_tool) | 22.6% (tool) | 18.2% (new_tool) | 16.4% (new_tool) | 18.2% (new_tool) | 16.4% (new_tool) | 16.4% (new_tool) | 16.4% (new_tool) | 17.0% (new_tool) | 17.0% (new_tool) | 16.4% (new_tool) | 16.4% (new_tool) | 13.2% (tool) | 15.1% (new_tool) | 14.5% (tool) |
| org_vpn_change | 131 | 97.7% (new_network) | 97.7% (new_network) | 96.2% (new_network) | 19.1% (asset) | 18.3% (sensitive_first_look) | 13.7% (request_too_big) | 18.3% (sensitive_first_look) | 13.7% (request_too_big) | 14.5% (request_too_big) | 13.7% (request_too_big) | 15.3% (request_too_big) | 15.3% (request_too_big) | 13.0% (request_too_big) | 13.0% (request_too_big) | 9.9% (request_too_big) | 12.2% (request_too_big) | 11.5% (request_too_big) |
| release_crunch | 372 | 83.1% (request_too_big) | 83.1% (request_too_big) | 47.3% (sequence) | 40.3% (time_of_day) | 38.2% (time_of_day) | 35.5% (time_of_day) | 37.6% (time_of_day) | 35.5% (time_of_day) | 35.5% (time_of_day) | 34.9% (time_of_day) | 36.8% (time_of_day) | 36.6% (time_of_day) | 35.5% (time_of_day) | 34.9% (time_of_day) | 34.4% (time_of_day) | 34.4% (time_of_day) | 34.9% (time_of_day) |
| role_change | 45 | 97.8% (sequence) | 97.8% (sequence) | 91.1% (sequence) | 33.3% (asset) | 26.7% (time_of_day) | 22.2% (time_of_day) | 24.4% (time_of_day) | 22.2% (time_of_day) | 22.2% (time_of_day) | 22.2% (time_of_day) | 26.7% (time_of_day) | 26.7% (time_of_day) | 22.2% (time_of_day) | 22.2% (time_of_day) | 20.0% (time_of_day) | 24.4% (time_of_day) | 20.0% (time_of_day) |
| team_transfer | 44 | 70.5% (request_too_big) | 70.5% (request_too_big) | 27.3% (sequence) | 9.1% (asset) | 11.4% (sensitive_first_look) | 2.3% (request_too_big) | 11.4% (sensitive_first_look) | 2.3% (request_too_big) | 2.3% (request_too_big) | 0.0% (-) | 6.8% (sensitive_first_look) | 4.5% (sensitive_first_look) | 0.0% (-) | 0.0% (-) | 0.0% (-) | 0.0% (-) | 0.0% (-) |
| travel | 15 | 66.7% (time_of_day) | 66.7% (time_of_day) | 66.7% (time_of_day) | 46.7% (time_of_day) | 46.7% (time_of_day) | 40.0% (time_of_day) | 46.7% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) |

## Gray episodes by kind

| Kind | episodes | v1 (shipped): caught · calls ≥x3 | v2: caught · calls ≥x3 | v2, learned limits: caught · calls ≥x3 | v2 + recommended (first look only), learned limits: caught · calls ≥x3 | v3: caught · calls ≥x3 | v3 final: caught · calls ≥x3 | v3 final, flat first-look rule: caught · calls ≥x3 | v3 final, first look by asset only: caught · calls ≥x3 | v3 final, 5-call warm-up: caught · calls ≥x3 | v3 final, size limits per agent-day: caught · calls ≥x3 | v3 final, first look anchored at a read: caught · calls ≥x3 | v3 final, read anchor, sizes per agent-day: caught · calls ≥x3 | v3 (decided), org discount on first looks: caught · calls ≥x3 | v3 (decided): caught · calls ≥x3 | v4: caught · calls ≥x3 | v3 (decided), network and app in Footprint: caught · calls ≥x3 | v3 (decided), new tool through tool rarity: caught · calls ≥x3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| big_paste | 6 | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| bot_loop | 3 | 100.0% · 96.4% | 100.0% · 96.4% | 100.0% · 91.3% | 100.0% · 96.5% | 100.0% · 95.7% | 100.0% · 95.7% | 100.0% · 95.7% | 100.0% · 95.7% | 100.0% · 95.7% | 100.0% · 95.7% | 100.0% · 95.7% | 100.0% · 95.7% | 100.0% · 95.7% | 100.0% · 95.7% | 100.0% · 95.7% | 100.0% · 95.7% | 100.0% · 95.7% |
| bulk_export | 12 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 91.7% · 23.8% | 83.3% · 12.8% | 100.0% · 80.4% | 100.0% · 80.7% | 100.0% · 80.6% | 100.0% · 80.4% | 100.0% · 80.4% | 100.0% · 80.6% | 100.0% · 80.6% | 100.0% · 80.8% | 100.0% · 80.8% | 100.0% · 80.8% | 100.0% · 80.8% | 100.0% · 80.8% |
| cross_copy | 7 | 100.0% · 38.5% | 100.0% · 38.5% | 100.0% · 38.5% | 28.6% · 15.0% | 28.6% · 15.0% | 14.3% · 4.8% | 28.6% · 15.0% | 14.3% · 4.8% | 14.3% · 4.8% | 14.3% · 4.8% | 14.3% · 4.8% | 14.3% · 4.8% | 14.3% · 4.8% | 14.3% · 4.8% | 14.3% · 4.8% | 14.3% · 4.8% | 14.3% · 4.8% |
| mass_cleanup | 6 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 66.7% · 23.2% | 50.0% · 12.1% | 50.0% · 12.1% | 50.0% · 12.1% | 50.0% · 12.1% | 50.0% · 12.1% | 50.0% · 12.1% | 50.0% · 12.1% | 50.0% · 12.1% | 50.0% · 12.1% | 50.0% · 12.1% | 50.0% · 12.1% | 50.0% · 12.1% | 50.0% · 12.1% |
| off_hours_batch | 5 | 20.0% · 0.3% | 20.0% · 0.3% | 20.0% · 0.3% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% | 60.0% · 60.0% |
| overfetch | 12 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% |
| scope_creep | 5 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 100.0% · 2.1% | 60.0% · 1.5% | 20.0% · 0.3% | 80.0% · 1.8% | 20.0% · 0.3% | 20.0% · 0.3% | 20.0% · 0.3% | 20.0% · 0.3% | 20.0% · 0.3% | 20.0% · 0.3% | 20.0% · 0.3% | 20.0% · 0.3% | 20.0% · 0.3% | 20.0% · 0.3% |
| sensitive_peek | 15 | 6.7% · 3.3% | 6.7% · 3.3% | 6.7% · 3.3% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 86.7% · 86.7% | 86.7% · 86.7% | 86.7% · 86.7% | 86.7% · 86.7% |
| shadow_script | 8 | 100.0% · 3.6% | 100.0% · 3.6% | 100.0% · 3.6% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| slow_loop | 5 | 20.0% · 0.1% | 20.0% · 0.1% | 20.0% · 0.1% | 100.0% · 89.1% | 100.0% · 87.6% | 100.0% · 87.6% | 100.0% · 87.6% | 100.0% · 87.6% | 100.0% · 87.6% | 100.0% · 87.6% | 100.0% · 87.6% | 100.0% · 87.6% | 100.0% · 87.5% | 100.0% · 87.6% | 100.0% · 82.0% | 100.0% · 87.5% | 100.0% · 82.0% |

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
