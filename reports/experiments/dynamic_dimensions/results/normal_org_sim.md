# Mostly-ordinary organisation: results

150 agents, 180 days (scored: days 90-179), 3,495,900 messages, 79 gray episodes. Shipped-engine mirror checked on 217,619 messages.

Doc limits: burst > 20 a minute, request > 10 KB. Learned limits (policy.py, first 30 days): {'burst_per_minute': 48, 'request_limit_bytes': 102000, 'requires_before': {}}.

## False alarms and gray episodes

| Engine | Ordinary days ≥x3 | people | bots | ordinary calls ≥x3 | alerts/day (ordinary · change · gray) | gray caught ≥x3 | top causes on ordinary days |
|---|---|---|---|---|---|---|---|
| v1 (shipped) | 52.1% | 58.0% | 22.5% | 2.5% | 40.6 · 17.9 · 1.2 | 27.8% | request_too_big 68%, sequence 27%, burst 3% |
| v2 | 52.2% | 58.1% | 22.5% | 2.5% | 40.7 · 18.0 · 1.2 | 27.8% | request_too_big 68%, sequence 27%, burst 3% |
| v2 + days | 52.9% | 58.2% | 26.5% | 2.6% | 41.2 · 19.9 · 1.2 | 27.8% | request_too_big 67%, sequence 26%, burst 3% |
| v2 + daily update | 52.2% | 58.1% | 22.5% | 2.7% | 40.7 · 18.0 · 1.2 | 31.6% | request_too_big 68%, sequence 27%, burst 3% |
| v2 + tie-break | 52.3% | 58.3% | 22.5% | 2.5% | 40.8 · 18.1 · 1.2 | 29.1% | request_too_big 71%, sequence 24%, burst 3% |
| v2 + rule rarity | 2.6% | 2.6% | 2.6% | 0.0% | 2.0 · 5.2 · 0.2 | 17.7% | new_tool 25%, new_network 20%, burst 19% |
| v2 + org discount | 52.0% | 57.9% | 22.5% | 2.5% | 40.6 · 17.3 · 1.2 | 27.8% | request_too_big 68%, sequence 27%, burst 3% |
| v2 + 14-day onboarding | 52.2% | 58.1% | 22.5% | 2.5% | 40.7 · 18.0 · 1.2 | 27.8% | request_too_big 68%, sequence 27%, burst 3% |
| v2 + all fixes | 5.1% | 4.3% | 9.2% | 0.5% | 4.0 · 10.2 · 0.3 | 22.8% | tool 38%, asset 17%, burst 11% |
| v1, learned limits | 23.0% | 26.4% | 5.8% | 2.0% | 17.9 · 12.2 · 0.8 | 27.8% | sequence 87%, request_size 7%, tool 3% |
| v2, learned limits | 22.1% | 25.4% | 5.6% | 1.9% | 17.2 · 12.3 · 0.8 | 27.8% | sequence 91%, new_tool 3%, request_too_big 2% |
| v2 + all fixes, learned limits | 4.9% | 4.6% | 6.5% | 0.5% | 3.9 · 10.3 · 0.4 | 25.3% | tool 40%, asset 18%, request_too_big 13% |
| v2 + new detectors, learned limits | 26.0% | 29.6% | 7.8% | 2.0% | 20.2 · 13.1 · 1.1 | 72.2% | sequence 47%, asset 42%, request_too_big 6% |
| v2 + recommended, learned limits | 14.8% | 17.2% | 3.0% | 0.4% | 11.5 · 6.6 · 1.0 | 73.4% | asset 77%, request_too_big 12%, tool 5% |
| v2 + recommended + days, learned limits | 20.4% | 22.2% | 11.4% | 1.2% | 15.9 · 13.3 · 1.1 | 77.2% | asset 79%, request_too_big 9%, tool 8% |
| v2 + recommended (first look only), learned limits | 7.1% | 7.9% | 3.0% | 0.2% | 5.5 · 4.7 · 0.7 | 65.8% | asset 44%, request_too_big 29%, tool 12% |
| v3 | 6.2% | 6.9% | 2.9% | 0.2% | 4.9 · 4.4 · 0.7 | 64.6% | sensitive_first_look 47%, request_too_big 33%, new_network 8% |
| v3, assets/hour as a rule | 6.2% | 6.9% | 2.9% | 0.2% | 4.9 · 4.4 · 0.7 | 68.4% | sensitive_first_look 46%, request_too_big 33%, new_network 8% |
| v3, weekend split | 6.2% | 6.9% | 2.9% | 0.2% | 4.9 · 4.4 · 0.6 | 57.0% | sensitive_first_look 46%, request_too_big 33%, new_network 8% |
| v3, weekend fallback | 6.2% | 6.9% | 2.9% | 0.2% | 4.9 · 4.4 · 0.6 | 63.3% | sensitive_first_look 46%, request_too_big 33%, new_network 8% |
| v3, weekend flag | 6.2% | 6.9% | 2.9% | 0.2% | 4.9 · 4.4 · 0.7 | 64.6% | sensitive_first_look 47%, request_too_big 33%, new_network 8% |
| v3 without writes/hour | 6.2% | 6.9% | 2.9% | 0.2% | 4.9 · 4.4 · 0.6 | 63.3% | sensitive_first_look 47%, request_too_big 33%, new_network 8% |
| v3 + tie-break formula | 7.0% | 7.8% | 3.0% | 0.3% | 5.4 · 4.9 · 0.7 | 68.4% | sensitive_first_look 42%, request_too_big 29%, tool 12% |
| v3 final | 3.5% | 3.7% | 2.9% | 0.2% | 2.8 · 3.5 · 0.6 | 64.6% | request_too_big 60%, new_network 14%, tool 10% |
| v3 final, 5-call warm-up | 3.5% | 3.7% | 2.9% | 0.2% | 2.8 · 3.5 · 0.6 | 64.6% | request_too_big 60%, new_network 14%, tool 10% |
| v3 final, first-day warm-up without rules | 3.5% | 3.7% | 2.9% | 0.2% | 2.8 · 3.5 · 0.6 | 64.6% | request_too_big 60%, new_network 14%, tool 10% |
| v3 final, flat first-look rule | 6.3% | 7.0% | 2.9% | 0.2% | 4.9 · 4.3 · 0.7 | 67.1% | sensitive_first_look 46%, request_too_big 33%, new_network 8% |
| v3 final, first look by asset only | 3.5% | 3.7% | 2.9% | 0.2% | 2.8 · 3.5 · 0.6 | 64.6% | request_too_big 60%, new_network 14%, tool 10% |
| v3 final, first look tool step 0.1 | 3.5% | 3.6% | 2.9% | 0.2% | 2.7 · 3.5 · 0.5 | 55.7% | request_too_big 60%, new_network 14%, tool 10% |
| v3 final, size limits per agent-day | 3.3% | 3.5% | 2.0% | 0.2% | 2.5 · 3.5 · 0.6 | 64.6% | request_too_big 56%, new_network 16%, tool 11% |
| v3 final, first look anchored at a read | 4.1% | 4.4% | 2.9% | 0.2% | 3.2 · 3.8 · 0.6 | 64.6% | request_too_big 51%, sensitive_first_look 18%, new_network 12% |
| v3 final, read anchor, sizes per agent-day | 3.9% | 4.2% | 2.0% | 0.2% | 3.0 · 3.7 · 0.6 | 64.6% | request_too_big 47%, sensitive_first_look 19%, new_network 13% |
| v3 (decided), org discount on first looks | 3.2% | 3.5% | 2.0% | 0.2% | 2.5 · 3.5 · 0.6 | 64.6% | request_too_big 57%, new_network 15%, tool 11% |
| v3 (decided) | 3.2% | 3.4% | 2.0% | 0.2% | 2.5 · 3.4 · 0.6 | 63.3% | request_too_big 59%, new_network 15%, tool 11% |
| v4 | 2.7% | 2.8% | 2.0% | 0.1% | 2.1 · 3.1 · 0.6 | 63.3% | request_too_big 72%, tool 20%, sequence 3% |
| v3 (decided), network and app in Footprint | 2.7% | 2.9% | 2.0% | 0.1% | 2.1 · 3.3 · 0.6 | 63.3% | request_too_big 70%, tool 14%, new_tool 9% |
| v3 (decided), new tool through tool rarity | 3.1% | 3.4% | 2.0% | 0.2% | 2.5 · 3.3 · 0.6 | 64.6% | request_too_big 61%, tool 17%, new_network 15% |

## Daily review list

Gray episodes caught when someone reviews the top-k agent-days each day (150 agents).

| Engine | list | gray caught | cut in a tie | list filled by ordinary · change · gray |
|---|---|---|---|---|
| v1 (shipped) | top 4 | M, ties at random | 19.0% | 87.9% | 48.2% · 47.2% · 4.3% |
| v1 (shipped) | top 4 | M, then strange dimensions | 25.8% | 68.1% | 41.0% · 52.3% · 6.4% |
| v1 (shipped) | top 4 | static x M | 11.1% | 94.5% | 57.7% · 39.3% · 2.7% |
| v1 (shipped) | top 8 | M, ties at random | 22.7% | 79.1% | 52.7% · 43.9% · 2.7% |
| v1 (shipped) | top 8 | M, then strange dimensions | 31.8% | 71.4% | 50.5% · 44.3% · 4.6% |
| v1 (shipped) | top 8 | static x M | 16.9% | 79.1% | 60.7% · 36.4% · 2.2% |
| v2 | top 4 | M, ties at random | 13.8% | 92.3% | 48.3% · 48.4% · 3.0% |
| v2 | top 4 | M, then strange dimensions | 23.1% | 67.0% | 41.5% · 52.7% · 5.5% |
| v2 | top 4 | static x M | 6.1% | 97.8% | 58.7% · 39.6% · 1.4% |
| v2 | top 8 | M, ties at random | 19.0% | 82.4% | 52.9% · 44.2% · 2.2% |
| v2 | top 8 | M, then strange dimensions | 30.0% | 68.1% | 50.0% · 45.2% · 4.1% |
| v2 | top 8 | static x M | 12.8% | 79.1% | 61.2% · 36.5% · 1.6% |
| v2 + days | top 4 | M, ties at random | 12.3% | 83.5% | 27.9% · 69.1% · 2.7% |
| v2 + days | top 4 | M, then strange dimensions | 16.6% | 61.5% | 24.9% · 71.1% · 3.8% |
| v2 + days | top 4 | static x M | 3.7% | 92.3% | 41.3% · 57.6% · 0.8% |
| v2 + days | top 8 | M, ties at random | 17.4% | 75.8% | 37.4% · 59.9% · 1.9% |
| v2 + days | top 8 | M, then strange dimensions | 27.4% | 56.0% | 35.0% · 60.6% · 3.7% |
| v2 + days | top 8 | static x M | 10.7% | 80.2% | 50.3% · 47.7% · 1.3% |
| v2 + daily update | top 4 | M, ties at random | 15.3% | 94.5% | 54.3% · 42.0% · 3.4% |
| v2 + daily update | top 4 | M, then strange dimensions | 24.7% | 74.7% | 48.0% · 45.7% · 6.1% |
| v2 + daily update | top 4 | static x M | 5.7% | 96.7% | 57.1% · 41.2% · 1.3% |
| v2 + daily update | top 8 | M, ties at random | 21.0% | 84.6% | 57.6% · 39.2% · 2.5% |
| v2 + daily update | top 8 | M, then strange dimensions | 31.7% | 73.6% | 55.1% · 39.6% · 4.6% |
| v2 + daily update | top 8 | static x M | 13.1% | 79.1% | 59.4% · 38.3% · 1.6% |
| v2 + tie-break | top 4 | M, ties at random | 18.5% | 58.2% | 45.5% · 49.9% · 4.2% |
| v2 + tie-break | top 4 | M, then strange dimensions | 25.0% | 36.3% | 43.7% · 50.3% · 5.8% |
| v2 + tie-break | top 4 | static x M | 9.5% | 68.1% | 55.8% · 41.5% · 2.4% |
| v2 + tie-break | top 8 | M, ties at random | 26.8% | 57.1% | 50.6% · 45.1% · 3.6% |
| v2 + tie-break | top 8 | M, then strange dimensions | 31.1% | 42.9% | 50.2% · 44.9% · 4.2% |
| v2 + tie-break | top 8 | static x M | 19.4% | 58.2% | 59.1% · 37.4% · 2.9% |
| v2 + rule rarity | top 4 | M, ties at random | 18.6% | 47.3% | 34.7% · 61.0% · 4.0% |
| v2 + rule rarity | top 4 | M, then strange dimensions | 19.8% | 27.5% | 34.5% · 60.9% · 4.3% |
| v2 + rule rarity | top 4 | static x M | 16.6% | 15.4% | 45.1% · 51.0% · 3.6% |
| v2 + rule rarity | top 8 | M, ties at random | 32.6% | 34.1% | 40.3% · 55.5% · 3.5% |
| v2 + rule rarity | top 8 | M, then strange dimensions | 33.7% | 23.1% | 39.7% · 55.9% · 3.7% |
| v2 + rule rarity | top 8 | static x M | 29.1% | 4.4% | 48.1% · 48.0% · 3.2% |
| v2 + org discount | top 4 | M, ties at random | 13.8% | 93.4% | 49.1% · 47.6% · 3.0% |
| v2 + org discount | top 4 | M, then strange dimensions | 24.3% | 68.1% | 43.9% · 49.9% · 5.9% |
| v2 + org discount | top 4 | static x M | 6.1% | 97.8% | 58.8% · 39.5% · 1.4% |
| v2 + org discount | top 8 | M, ties at random | 20.4% | 83.5% | 53.6% · 43.4% · 2.3% |
| v2 + org discount | top 8 | M, then strange dimensions | 32.3% | 70.3% | 52.5% · 42.4% · 4.4% |
| v2 + org discount | top 8 | static x M | 12.9% | 79.1% | 61.3% · 36.4% · 1.6% |
| v2 + 14-day onboarding | top 4 | M, ties at random | 13.8% | 92.3% | 48.3% · 48.4% · 3.0% |
| v2 + 14-day onboarding | top 4 | M, then strange dimensions | 23.0% | 65.9% | 40.9% · 53.4% · 5.5% |
| v2 + 14-day onboarding | top 4 | static x M | 6.1% | 97.8% | 58.7% · 39.6% · 1.4% |
| v2 + 14-day onboarding | top 8 | M, ties at random | 19.0% | 82.4% | 52.9% · 44.2% · 2.2% |
| v2 + 14-day onboarding | top 8 | M, then strange dimensions | 29.7% | 68.1% | 49.2% · 46.1% · 4.1% |
| v2 + 14-day onboarding | top 8 | static x M | 12.8% | 79.1% | 61.2% · 36.5% · 1.6% |
| v2 + all fixes | top 4 | M, ties at random | 15.2% | 1.1% | 18.1% · 78.3% · 3.3% |
| v2 + all fixes | top 4 | M, then strange dimensions | 15.2% | 1.1% | 18.1% · 78.3% · 3.3% |
| v2 + all fixes | top 4 | static x M | 6.3% | 0.0% | 22.3% · 76.1% · 1.4% |
| v2 + all fixes | top 8 | M, ties at random | 17.7% | 4.4% | 24.9% · 72.5% · 1.9% |
| v2 + all fixes | top 8 | M, then strange dimensions | 17.7% | 4.4% | 24.9% · 72.5% · 1.9% |
| v2 + all fixes | top 8 | static x M | 17.7% | 0.0% | 29.8% · 67.6% · 1.9% |
| v1, learned limits | top 4 | M, ties at random | 19.9% | 83.5% | 40.7% · 54.4% · 4.6% |
| v1, learned limits | top 4 | M, then strange dimensions | 25.2% | 63.7% | 37.0% · 56.4% · 6.3% |
| v1, learned limits | top 4 | static x M | 12.3% | 87.9% | 51.0% · 45.6% · 3.1% |
| v1, learned limits | top 8 | M, ties at random | 26.0% | 69.2% | 48.0% · 48.0% · 3.3% |
| v1, learned limits | top 8 | M, then strange dimensions | 31.8% | 57.1% | 49.3% · 45.3% · 4.8% |
| v1, learned limits | top 8 | static x M | 20.3% | 73.6% | 57.0% · 39.4% · 2.9% |
| v2, learned limits | top 4 | M, ties at random | 15.8% | 89.0% | 39.7% · 56.5% · 3.6% |
| v2, learned limits | top 4 | M, then strange dimensions | 23.7% | 67.0% | 37.6% · 56.6% · 5.6% |
| v2, learned limits | top 4 | static x M | 8.0% | 92.3% | 51.2% · 46.5% · 2.0% |
| v2, learned limits | top 8 | M, ties at random | 26.0% | 75.8% | 47.1% · 49.1% · 3.1% |
| v2, learned limits | top 8 | M, then strange dimensions | 33.6% | 63.7% | 48.6% · 46.2% · 4.5% |
| v2, learned limits | top 8 | static x M | 22.2% | 73.6% | 56.8% · 39.6% · 2.9% |
| v2 + all fixes, learned limits | top 4 | M, ties at random | 15.2% | 1.1% | 18.4% · 78.0% · 3.3% |
| v2 + all fixes, learned limits | top 4 | M, then strange dimensions | 15.2% | 1.1% | 18.4% · 78.0% · 3.3% |
| v2 + all fixes, learned limits | top 4 | static x M | 7.6% | 0.0% | 23.6% · 74.5% · 1.6% |
| v2 + all fixes, learned limits | top 8 | M, ties at random | 22.8% | 5.5% | 23.4% · 73.5% · 2.5% |
| v2 + all fixes, learned limits | top 8 | M, then strange dimensions | 22.8% | 5.5% | 23.4% · 73.5% · 2.5% |
| v2 + all fixes, learned limits | top 8 | static x M | 25.3% | 0.0% | 30.2% · 66.3% · 2.7% |
| v2 + new detectors, learned limits | top 4 | M, ties at random | 30.4% | 40.7% | 57.3% · 34.9% · 7.6% |
| v2 + new detectors, learned limits | top 4 | M, then strange dimensions | 30.4% | 22.0% | 55.9% · 36.1% · 7.7% |
| v2 + new detectors, learned limits | top 4 | static x M | 5.9% | 62.6% | 55.3% · 43.1% · 1.3% |
| v2 + new detectors, learned limits | top 8 | M, ties at random | 45.1% | 24.2% | 58.1% · 35.7% · 5.5% |
| v2 + new detectors, learned limits | top 8 | M, then strange dimensions | 44.3% | 16.5% | 57.7% · 36.1% · 5.5% |
| v2 + new detectors, learned limits | top 8 | static x M | 22.6% | 70.3% | 58.2% · 38.4% · 2.7% |
| v2 + recommended, learned limits | top 4 | M, ties at random | 41.8% | 0.0% | 60.4% · 29.7% · 9.6% |
| v2 + recommended, learned limits | top 4 | M, then strange dimensions | 41.8% | 0.0% | 60.4% · 29.7% · 9.6% |
| v2 + recommended, learned limits | top 4 | static x M | 15.2% | 2.2% | 58.0% · 38.5% · 3.3% |
| v2 + recommended, learned limits | top 8 | M, ties at random | 53.2% | 4.4% | 61.4% · 31.0% · 6.9% |
| v2 + recommended, learned limits | top 8 | M, then strange dimensions | 53.2% | 3.3% | 61.4% · 31.0% · 6.9% |
| v2 + recommended, learned limits | top 8 | static x M | 41.8% | 1.1% | 57.8% · 36.7% · 4.8% |
| v2 + recommended + days, learned limits | top 4 | M, ties at random | 41.8% | 2.2% | 50.0% · 40.1% · 9.6% |
| v2 + recommended + days, learned limits | top 4 | M, then strange dimensions | 41.8% | 2.2% | 50.0% · 40.1% · 9.6% |
| v2 + recommended + days, learned limits | top 4 | static x M | 7.6% | 3.3% | 47.7% · 50.4% · 1.6% |
| v2 + recommended + days, learned limits | top 8 | M, ties at random | 51.9% | 3.3% | 49.9% · 43.1% · 6.3% |
| v2 + recommended + days, learned limits | top 8 | M, then strange dimensions | 51.9% | 0.0% | 49.9% · 43.1% · 6.3% |
| v2 + recommended + days, learned limits | top 8 | static x M | 27.8% | 0.0% | 46.4% · 49.9% · 3.0% |
| v2 + recommended (first look only), learned limits | top 4 | M, ties at random | 40.5% | 0.0% | 59.3% · 31.3% · 9.1% |
| v2 + recommended (first look only), learned limits | top 4 | M, then strange dimensions | 40.5% | 0.0% | 59.3% · 31.3% · 9.1% |
| v2 + recommended (first look only), learned limits | top 4 | static x M | 19.0% | 1.1% | 53.6% · 42.0% · 4.1% |
| v2 + recommended (first look only), learned limits | top 8 | M, ties at random | 60.8% | 0.0% | 57.4% · 35.0% · 6.9% |
| v2 + recommended (first look only), learned limits | top 8 | M, then strange dimensions | 60.8% | 0.0% | 57.4% · 35.0% · 6.9% |
| v2 + recommended (first look only), learned limits | top 8 | static x M | 49.4% | 1.1% | 55.4% · 38.5% · 5.5% |
| v3 | top 4 | M, ties at random | 44.1% | 69.2% | 52.2% · 37.7% · 9.8% |
| v3 | top 4 | M, then strange dimensions | 48.8% | 31.9% | 50.8% · 37.4% · 11.5% |
| v3 | top 4 | M, then second score | 53.2% | 1.1% | 50.8% · 36.8% · 12.1% |
| v3 | top 4 | static x M | 27.2% | 46.2% | 50.9% · 42.9% · 6.0% |
| v3 | top 8 | M, ties at random | 57.4% | 46.2% | 55.3% · 37.2% · 6.8% |
| v3 | top 8 | M, then strange dimensions | 62.1% | 30.8% | 55.1% · 36.6% · 7.6% |
| v3 | top 8 | M, then second score | 65.8% | 8.8% | 54.9% · 36.8% · 7.7% |
| v3 | top 8 | static x M | 44.9% | 30.8% | 53.7% · 40.6% · 5.1% |
| v3, assets/hour as a rule | top 4 | M, ties at random | 45.3% | 69.2% | 52.0% · 37.6% · 10.1% |
| v3, assets/hour as a rule | top 4 | M, then strange dimensions | 50.9% | 31.9% | 50.9% · 37.0% · 11.8% |
| v3, assets/hour as a rule | top 4 | M, then second score | 48.1% | 2.2% | 51.6% · 37.1% · 11.0% |
| v3, assets/hour as a rule | top 4 | static x M | 33.8% | 47.3% | 50.0% · 42.4% · 7.4% |
| v3, assets/hour as a rule | top 8 | M, ties at random | 60.0% | 47.3% | 55.4% · 36.9% · 7.1% |
| v3, assets/hour as a rule | top 8 | M, then strange dimensions | 65.6% | 34.1% | 55.3% · 36.1% · 7.9% |
| v3, assets/hour as a rule | top 8 | M, then second score | 65.8% | 8.8% | 55.0% · 36.6% · 7.7% |
| v3, assets/hour as a rule | top 8 | static x M | 51.8% | 29.7% | 53.0% · 40.3% · 6.1% |
| v3, weekend split | top 4 | M, ties at random | 39.0% | 70.3% | 52.8% · 38.1% · 8.7% |
| v3, weekend split | top 4 | M, then strange dimensions | 43.8% | 35.2% | 51.5% · 37.8% · 10.4% |
| v3, weekend split | top 4 | M, then second score | 48.1% | 2.2% | 51.4% · 37.4% · 11.0% |
| v3, weekend split | top 4 | static x M | 13.5% | 51.6% | 53.1% · 43.7% · 3.0% |
| v3, weekend split | top 8 | M, ties at random | 55.8% | 47.3% | 55.4% · 37.3% · 6.6% |
| v3, weekend split | top 8 | M, then strange dimensions | 60.0% | 30.8% | 55.2% · 36.8% · 7.3% |
| v3, weekend split | top 8 | M, then second score | 64.6% | 8.8% | 54.9% · 36.9% · 7.6% |
| v3, weekend split | top 8 | static x M | 38.0% | 33.0% | 55.0% · 40.0% · 4.3% |
| v3, weekend fallback | top 4 | M, ties at random | 42.8% | 69.2% | 52.4% · 37.7% · 9.6% |
| v3, weekend fallback | top 4 | M, then strange dimensions | 47.6% | 34.1% | 51.1% · 37.4% · 11.2% |
| v3, weekend fallback | top 4 | M, then second score | 51.9% | 2.2% | 51.1% · 36.8% · 11.8% |
| v3, weekend fallback | top 4 | static x M | 19.8% | 46.2% | 52.2% · 43.2% · 4.4% |
| v3, weekend fallback | top 8 | M, ties at random | 57.1% | 47.3% | 55.3% · 37.2% · 6.8% |
| v3, weekend fallback | top 8 | M, then strange dimensions | 61.2% | 30.8% | 55.2% · 36.7% · 7.5% |
| v3, weekend fallback | top 8 | M, then second score | 65.8% | 8.8% | 54.9% · 36.8% · 7.7% |
| v3, weekend fallback | top 8 | static x M | 40.5% | 33.0% | 54.0% · 40.7% · 4.6% |
| v3, weekend flag | top 4 | M, ties at random | 43.4% | 86.8% | 54.9% · 35.1% · 9.7% |
| v3, weekend flag | top 4 | M, then strange dimensions | 50.1% | 41.8% | 53.2% · 34.7% · 11.8% |
| v3, weekend flag | top 4 | M, then second score | 53.2% | 1.1% | 53.6% · 34.1% · 12.1% |
| v3, weekend flag | top 4 | static x M | 18.8% | 65.9% | 58.9% · 36.7% · 4.1% |
| v3, weekend flag | top 8 | M, ties at random | 57.3% | 61.5% | 59.0% · 33.5% · 6.8% |
| v3, weekend flag | top 8 | M, then strange dimensions | 62.1% | 42.9% | 58.6% · 33.2% · 7.6% |
| v3, weekend flag | top 8 | M, then second score | 65.8% | 6.6% | 58.4% · 33.2% · 7.7% |
| v3, weekend flag | top 8 | static x M | 41.1% | 48.4% | 60.1% · 34.5% · 4.7% |
| v3 without writes/hour | top 4 | M, ties at random | 43.0% | 69.2% | 52.3% · 37.8% · 9.6% |
| v3 without writes/hour | top 4 | M, then strange dimensions | 48.8% | 26.4% | 51.0% · 37.2% · 11.5% |
| v3 without writes/hour | top 4 | M, then second score | 51.9% | 1.1% | 51.4% · 36.5% · 11.8% |
| v3 without writes/hour | top 4 | static x M | 26.0% | 46.2% | 51.8% · 42.2% · 5.7% |
| v3 without writes/hour | top 8 | M, ties at random | 56.3% | 50.5% | 56.1% · 36.6% · 6.7% |
| v3 without writes/hour | top 8 | M, then strange dimensions | 61.6% | 35.2% | 55.9% · 35.9% · 7.5% |
| v3 without writes/hour | top 8 | M, then second score | 64.6% | 12.1% | 55.7% · 36.1% · 7.6% |
| v3 without writes/hour | top 8 | static x M | 41.1% | 30.8% | 54.4% · 40.3% · 4.7% |
| v3 + tie-break formula | top 4 | M, ties at random | 54.4% | 0.0% | 46.2% · 41.5% · 12.1% |
| v3 + tie-break formula | top 4 | M, then strange dimensions | 54.4% | 0.0% | 46.2% · 41.5% · 12.1% |
| v3 + tie-break formula | top 4 | M, then second score | 54.4% | 0.0% | 46.2% · 41.5% · 12.1% |
| v3 + tie-break formula | top 4 | static x M | 20.3% | 0.0% | 49.2% · 46.2% · 4.4% |
| v3 + tie-break formula | top 8 | M, ties at random | 63.3% | 1.1% | 53.0% · 39.0% · 7.3% |
| v3 + tie-break formula | top 8 | M, then strange dimensions | 63.3% | 1.1% | 53.0% · 39.0% · 7.3% |
| v3 + tie-break formula | top 8 | M, then second score | 63.3% | 1.1% | 53.0% · 39.0% · 7.3% |
| v3 + tie-break formula | top 8 | static x M | 45.6% | 0.0% | 53.3% · 40.9% · 5.1% |
| v3 final | top 4 | M, ties at random | 47.4% | 50.5% | 50.1% · 39.2% · 10.4% |
| v3 final | top 4 | M, then strange dimensions | 56.3% | 19.8% | 50.2% · 37.3% · 12.2% |
| v3 final | top 4 | M, then second score | 57.0% | 6.6% | 49.7% · 37.6% · 12.4% |
| v3 final | top 4 | static x M | 35.4% | 31.9% | 51.3% · 40.6% · 7.8% |
| v3 final | top 8 | M, ties at random | 64.9% | 23.1% | 53.4% · 38.8% · 7.2% |
| v3 final | top 8 | M, then strange dimensions | 67.1% | 9.9% | 52.9% · 39.0% · 7.4% |
| v3 final | top 8 | M, then second score | 67.1% | 4.4% | 53.2% · 38.7% · 7.4% |
| v3 final | top 8 | static x M | 54.2% | 9.9% | 53.6% · 39.6% · 6.2% |
| v3 final, 5-call warm-up | top 4 | M, ties at random | 47.2% | 50.5% | 49.7% · 39.7% · 10.3% |
| v3 final, 5-call warm-up | top 4 | M, then strange dimensions | 56.3% | 19.8% | 50.1% · 37.4% · 12.2% |
| v3 final, 5-call warm-up | top 4 | M, then second score | 57.0% | 5.5% | 49.2% · 38.2% · 12.4% |
| v3 final, 5-call warm-up | top 4 | static x M | 35.3% | 33.0% | 50.8% · 41.1% · 7.8% |
| v3 final, 5-call warm-up | top 8 | M, ties at random | 64.6% | 23.1% | 53.1% · 39.1% · 7.1% |
| v3 final, 5-call warm-up | top 8 | M, then strange dimensions | 67.1% | 9.9% | 52.6% · 39.3% · 7.4% |
| v3 final, 5-call warm-up | top 8 | M, then second score | 67.1% | 4.4% | 52.9% · 39.0% · 7.4% |
| v3 final, 5-call warm-up | top 8 | static x M | 54.2% | 9.9% | 53.3% · 39.8% · 6.2% |
| v3 final, first-day warm-up without rules | top 4 | M, ties at random | 47.4% | 50.5% | 50.4% · 39.0% · 10.4% |
| v3 final, first-day warm-up without rules | top 4 | M, then strange dimensions | 56.3% | 19.8% | 50.4% · 37.1% · 12.2% |
| v3 final, first-day warm-up without rules | top 4 | M, then second score | 57.0% | 6.6% | 49.7% · 37.6% · 12.4% |
| v3 final, first-day warm-up without rules | top 4 | static x M | 35.4% | 31.9% | 51.6% · 40.3% · 7.8% |
| v3 final, first-day warm-up without rules | top 8 | M, ties at random | 64.9% | 23.1% | 53.4% · 38.8% · 7.2% |
| v3 final, first-day warm-up without rules | top 8 | M, then strange dimensions | 67.1% | 9.9% | 52.9% · 39.0% · 7.4% |
| v3 final, first-day warm-up without rules | top 8 | M, then second score | 67.1% | 4.4% | 53.2% · 38.7% · 7.4% |
| v3 final, first-day warm-up without rules | top 8 | static x M | 54.2% | 9.9% | 53.7% · 39.4% · 6.2% |
| v3 final, flat first-look rule | top 4 | M, ties at random | 44.8% | 68.1% | 53.0% · 36.9% · 9.9% |
| v3 final, flat first-look rule | top 4 | M, then strange dimensions | 53.4% | 28.6% | 50.0% · 37.2% · 12.5% |
| v3 final, flat first-look rule | top 4 | M, then second score | 55.7% | 2.2% | 51.1% · 36.3% · 12.4% |
| v3 final, flat first-look rule | top 4 | static x M | 34.7% | 46.2% | 51.3% · 40.8% · 7.6% |
| v3 final, flat first-look rule | top 8 | M, ties at random | 59.6% | 48.4% | 56.8% · 35.7% · 6.9% |
| v3 final, flat first-look rule | top 8 | M, then strange dimensions | 67.1% | 29.7% | 56.6% · 34.9% · 7.8% |
| v3 final, flat first-look rule | top 8 | M, then second score | 68.4% | 6.6% | 56.6% · 34.8% · 7.8% |
| v3 final, flat first-look rule | top 8 | static x M | 52.6% | 27.5% | 54.1% · 39.1% · 6.1% |
| v3 final, first look by asset only | top 4 | M, ties at random | 49.4% | 52.7% | 50.2% · 38.7% · 10.8% |
| v3 final, first look by asset only | top 4 | M, then strange dimensions | 58.4% | 23.1% | 50.4% · 36.7% · 12.7% |
| v3 final, first look by asset only | top 4 | M, then second score | 62.0% | 6.6% | 49.5% · 36.8% · 13.5% |
| v3 final, first look by asset only | top 4 | static x M | 35.4% | 31.9% | 51.3% · 40.6% · 7.8% |
| v3 final, first look by asset only | top 8 | M, ties at random | 66.6% | 30.8% | 53.4% · 38.4% · 7.5% |
| v3 final, first look by asset only | top 8 | M, then strange dimensions | 68.4% | 14.3% | 53.2% · 38.5% · 7.7% |
| v3 final, first look by asset only | top 8 | M, then second score | 70.9% | 4.4% | 53.3% · 38.0% · 8.0% |
| v3 final, first look by asset only | top 8 | static x M | 55.9% | 9.9% | 53.4% · 39.5% · 6.3% |
| v3 final, first look tool step 0.1 | top 4 | M, ties at random | 44.8% | 50.5% | 50.6% · 39.2% · 9.9% |
| v3 final, first look tool step 0.1 | top 4 | M, then strange dimensions | 53.8% | 19.8% | 50.7% · 37.3% · 11.7% |
| v3 final, first look tool step 0.1 | top 4 | M, then second score | 54.4% | 6.6% | 50.3% · 37.6% · 11.8% |
| v3 final, first look tool step 0.1 | top 4 | static x M | 35.4% | 31.9% | 51.3% · 40.6% · 7.8% |
| v3 final, first look tool step 0.1 | top 8 | M, ties at random | 63.7% | 20.9% | 53.4% · 38.9% · 7.0% |
| v3 final, first look tool step 0.1 | top 8 | M, then strange dimensions | 65.8% | 9.9% | 53.0% · 39.0% · 7.3% |
| v3 final, first look tool step 0.1 | top 8 | M, then second score | 65.8% | 4.4% | 53.3% · 38.7% · 7.3% |
| v3 final, first look tool step 0.1 | top 8 | static x M | 53.0% | 9.9% | 53.7% · 39.6% · 6.0% |
| v3 final, size limits per agent-day | top 4 | M, ties at random | 48.1% | 47.3% | 50.0% · 39.1% · 10.5% |
| v3 final, size limits per agent-day | top 4 | M, then strange dimensions | 53.0% | 16.5% | 49.9% · 38.1% · 11.8% |
| v3 final, size limits per agent-day | top 4 | M, then second score | 55.7% | 7.7% | 49.3% · 38.0% · 12.4% |
| v3 final, size limits per agent-day | top 4 | static x M | 35.2% | 35.2% | 50.5% · 41.4% · 7.9% |
| v3 final, size limits per agent-day | top 8 | M, ties at random | 63.6% | 23.1% | 52.7% · 39.6% · 7.0% |
| v3 final, size limits per agent-day | top 8 | M, then strange dimensions | 65.8% | 14.3% | 52.4% · 39.6% · 7.3% |
| v3 final, size limits per agent-day | top 8 | M, then second score | 65.8% | 6.6% | 52.2% · 39.8% · 7.3% |
| v3 final, size limits per agent-day | top 8 | static x M | 54.2% | 9.9% | 54.2% · 39.1% · 6.0% |
| v3 final, first look anchored at a read | top 4 | M, ties at random | 50.6% | 54.9% | 49.1% · 39.5% · 11.1% |
| v3 final, first look anchored at a read | top 4 | M, then strange dimensions | 59.7% | 23.1% | 48.6% · 38.2% · 13.0% |
| v3 final, first look anchored at a read | top 4 | M, then second score | 63.3% | 5.5% | 48.2% · 37.8% · 13.7% |
| v3 final, first look anchored at a read | top 4 | static x M | 38.5% | 38.5% | 49.0% · 42.3% · 8.5% |
| v3 final, first look anchored at a read | top 8 | M, ties at random | 67.8% | 31.9% | 52.1% · 39.7% · 7.6% |
| v3 final, first look anchored at a read | top 8 | M, then strange dimensions | 69.6% | 14.3% | 52.1% · 39.4% · 7.8% |
| v3 final, first look anchored at a read | top 8 | M, then second score | 72.2% | 4.4% | 51.8% · 39.4% · 8.1% |
| v3 final, first look anchored at a read | top 8 | static x M | 57.2% | 11.0% | 52.6% · 40.2% · 6.5% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, ties at random | 51.5% | 51.6% | 48.6% · 39.9% · 11.3% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, then strange dimensions | 56.5% | 17.6% | 48.4% · 38.8% · 12.5% |
| v3 final, read anchor, sizes per agent-day | top 4 | M, then second score | 62.0% | 8.8% | 47.4% · 38.6% · 13.7% |
| v3 final, read anchor, sizes per agent-day | top 4 | static x M | 36.9% | 40.7% | 49.5% · 41.9% · 8.2% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, ties at random | 65.1% | 25.3% | 51.8% · 40.2% · 7.3% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, then strange dimensions | 67.1% | 13.2% | 51.7% · 40.0% · 7.6% |
| v3 final, read anchor, sizes per agent-day | top 8 | M, then second score | 69.6% | 4.4% | 51.2% · 40.3% · 7.8% |
| v3 final, read anchor, sizes per agent-day | top 8 | static x M | 55.9% | 6.6% | 53.2% · 39.9% · 6.2% |
| v3 (decided), org discount on first looks | top 4 | M, ties at random | 51.8% | 49.5% | 48.8% · 39.5% · 11.3% |
| v3 (decided), org discount on first looks | top 4 | M, then strange dimensions | 56.5% | 17.6% | 48.8% · 38.4% · 12.5% |
| v3 (decided), org discount on first looks | top 4 | M, then second score | 62.0% | 8.8% | 47.4% · 38.6% · 13.7% |
| v3 (decided), org discount on first looks | top 4 | static x M | 35.7% | 35.2% | 49.4% · 42.3% · 8.0% |
| v3 (decided), org discount on first looks | top 8 | M, ties at random | 65.2% | 29.7% | 51.9% · 40.2% · 7.3% |
| v3 (decided), org discount on first looks | top 8 | M, then strange dimensions | 67.1% | 17.6% | 51.8% · 40.0% · 7.6% |
| v3 (decided), org discount on first looks | top 8 | M, then second score | 69.6% | 5.5% | 51.2% · 40.4% · 7.7% |
| v3 (decided), org discount on first looks | top 8 | static x M | 57.1% | 8.8% | 53.3% · 39.5% · 6.5% |
| v3 (decided) | top 4 | M, ties at random | 50.2% | 47.3% | 49.2% · 39.5% · 11.0% |
| v3 (decided) | top 4 | M, then strange dimensions | 55.5% | 17.6% | 49.1% · 38.3% · 12.3% |
| v3 (decided) | top 4 | M, then second score | 59.5% | 7.7% | 47.9% · 38.6% · 13.2% |
| v3 (decided) | top 4 | static x M | 34.1% | 33.0% | 48.5% · 43.6% · 7.7% |
| v3 (decided) | top 8 | M, ties at random | 64.1% | 39.6% | 52.1% · 40.0% · 7.2% |
| v3 (decided) | top 8 | M, then strange dimensions | 65.8% | 20.9% | 52.2% · 39.7% · 7.4% |
| v3 (decided) | top 8 | M, then second score | 68.4% | 5.5% | 51.1% · 40.5% · 7.7% |
| v3 (decided) | top 8 | static x M | 57.0% | 12.1% | 52.8% · 40.0% · 6.5% |
| v4 | top 4 | M, ties at random | 53.2% | 35.2% | 51.3% · 36.7% · 11.8% |
| v4 | top 4 | M, then strange dimensions | 56.5% | 7.7% | 51.3% · 35.6% · 12.8% |
| v4 | top 4 | M, then second score | 58.2% | 2.2% | 49.7% · 37.1% · 12.9% |
| v4 | top 4 | static x M | 36.7% | 19.8% | 54.7% · 36.8% · 8.2% |
| v4 | top 8 | M, ties at random | 69.1% | 34.1% | 52.9% · 38.6% · 7.8% |
| v4 | top 8 | M, then strange dimensions | 72.2% | 13.2% | 53.0% · 38.4% · 8.0% |
| v4 | top 8 | M, then second score | 70.9% | 4.4% | 53.1% · 38.4% · 7.8% |
| v4 | top 8 | static x M | 62.4% | 11.0% | 54.3% · 38.1% · 6.9% |
| v3 (decided), network and app in Footprint | top 4 | M, ties at random | 50.3% | 39.6% | 50.5% · 38.1% · 11.1% |
| v3 (decided), network and app in Footprint | top 4 | M, then strange dimensions | 54.9% | 11.0% | 50.5% · 36.8% · 12.5% |
| v3 (decided), network and app in Footprint | top 4 | M, then second score | 57.0% | 2.2% | 48.1% · 39.0% · 12.6% |
| v3 (decided), network and app in Footprint | top 4 | static x M | 35.2% | 26.4% | 53.3% · 38.6% · 7.9% |
| v3 (decided), network and app in Footprint | top 8 | M, ties at random | 67.6% | 38.5% | 52.3% · 39.4% · 7.6% |
| v3 (decided), network and app in Footprint | top 8 | M, then strange dimensions | 69.6% | 16.5% | 52.3% · 39.3% · 7.7% |
| v3 (decided), network and app in Footprint | top 8 | M, then second score | 72.2% | 4.4% | 52.0% · 39.4% · 8.0% |
| v3 (decided), network and app in Footprint | top 8 | static x M | 61.6% | 13.2% | 53.5% · 39.0% · 6.8% |
| v3 (decided), new tool through tool rarity | top 4 | M, ties at random | 51.8% | 40.7% | 50.6% · 37.8% · 11.4% |
| v3 (decided), new tool through tool rarity | top 4 | M, then strange dimensions | 58.0% | 13.2% | 50.4% · 36.5% · 12.9% |
| v3 (decided), new tool through tool rarity | top 4 | M, then second score | 62.0% | 4.4% | 48.9% · 37.1% · 13.7% |
| v3 (decided), new tool through tool rarity | top 4 | static x M | 34.2% | 27.5% | 52.7% · 39.3% · 7.7% |
| v3 (decided), new tool through tool rarity | top 8 | M, ties at random | 66.1% | 38.5% | 53.2% · 38.7% · 7.4% |
| v3 (decided), new tool through tool rarity | top 8 | M, then strange dimensions | 67.1% | 23.1% | 53.3% · 38.4% · 7.6% |
| v3 (decided), new tool through tool rarity | top 8 | M, then second score | 68.4% | 7.7% | 52.7% · 38.9% · 7.7% |
| v3 (decided), new tool through tool rarity | top 8 | static x M | 59.7% | 12.1% | 54.3% · 38.4% · 6.6% |

## Ordinary life and org-wide changes at x3 or more

| Change | days | v1 (shipped) | v2 | v2 + days | v2 + daily update | v2 + tie-break | v2 + rule rarity | v2 + org discount | v2 + 14-day onboarding | v2 + all fixes | v1, learned limits | v2, learned limits | v2 + all fixes, learned limits | v2 + new detectors, learned limits | v2 + recommended, learned limits | v2 + recommended + days, learned limits | v2 + recommended (first look only), learned limits | v3 | v3, assets/hour as a rule | v3, weekend split | v3, weekend fallback | v3, weekend flag | v3 without writes/hour | v3 + tie-break formula | v3 final | v3 final, 5-call warm-up | v3 final, first-day warm-up without rules | v3 final, flat first-look rule | v3 final, first look by asset only | v3 final, first look tool step 0.1 | v3 final, size limits per agent-day | v3 final, first look anchored at a read | v3 final, read anchor, sizes per agent-day | v3 (decided), org discount on first looks | v3 (decided) | v4 | v3 (decided), network and app in Footprint | v3 (decided), new tool through tool rarity |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| back_from_vacation | 148 | 61.5% (request_too_big) | 63.5% (request_too_big) | 64.2% (request_too_big) | 63.5% (request_too_big) | 64.2% (request_too_big) | 13.5% (new_tool) | 60.1% (request_too_big) | 63.5% (request_too_big) | 12.2% (tool) | 34.5% (sequence) | 35.1% (sequence) | 12.2% (tool) | 39.2% (asset) | 20.3% (asset) | 28.4% (asset) | 11.5% (request_too_big) | 10.8% (request_too_big) | 10.8% (request_too_big) | 10.8% (request_too_big) | 10.8% (request_too_big) | 10.8% (request_too_big) | 10.8% (request_too_big) | 12.2% (request_too_big) | 8.1% (request_too_big) | 8.1% (request_too_big) | 8.1% (request_too_big) | 10.1% (request_too_big) | 8.1% (request_too_big) | 8.1% (request_too_big) | 7.4% (request_too_big) | 10.1% (request_too_big) | 9.5% (request_too_big) | 7.4% (request_too_big) | 7.4% (request_too_big) | 4.7% (request_too_big) | 6.8% (request_too_big) | 5.4% (request_too_big) |
| client_switch | 16 | 87.5% (new_client) | 87.5% (new_client) | 87.5% (new_client) | 87.5% (new_client) | 87.5% (request_too_big) | 56.2% (new_client) | 87.5% (new_client) | 87.5% (new_client) | 50.0% (new_client) | 75.0% (new_client) | 75.0% (new_client) | 50.0% (new_client) | 81.2% (new_client) | 62.5% (new_client) | 68.8% (new_client) | 62.5% (new_client) | 68.8% (new_client) | 68.8% (new_client) | 68.8% (new_client) | 68.8% (new_client) | 68.8% (new_client) | 68.8% (new_client) | 68.8% (new_client) | 56.2% (new_client) | 56.2% (new_client) | 56.2% (new_client) | 68.8% (new_client) | 56.2% (new_client) | 56.2% (new_client) | 56.2% (new_client) | 56.2% (new_client) | 56.2% (new_client) | 56.2% (new_client) | 56.2% (new_client) | 43.8% (client) | 43.8% (client) | 56.2% (new_client) |
| isp_change | 2 | 100.0% (request_too_big) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (request_too_big) | 100.0% (request_too_big) | 50.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 50.0% (new_network) | 0.0% (-) | 0.0% (-) | 50.0% (new_network) |
| monthly_report | 15 | 100.0% (asset) | 100.0% (asset) | 100.0% (asset) | 100.0% (burst) | 100.0% (asset) | 93.3% (asset) | 100.0% (asset) | 100.0% (asset) | 93.3% (asset) | 100.0% (asset) | 100.0% (asset) | 93.3% (asset) | 100.0% (asset) | 93.3% (burst) | 100.0% (asset) | 93.3% (burst) | 86.7% (burst) | 100.0% (burst) | 86.7% (burst) | 86.7% (burst) | 86.7% (burst) | 86.7% (burst) | 93.3% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) | 100.0% (burst) |
| new_hire | 72 | 83.3% (request_too_big) | 86.1% (request_too_big) | 86.1% (request_too_big) | 86.1% (request_too_big) | 86.1% (request_too_big) | 34.7% (new_tool) | 86.1% (request_too_big) | 86.1% (request_too_big) | 48.6% (new_tool) | 40.3% (sequence) | 50.0% (sequence) | 48.6% (new_tool) | 52.8% (sequence) | 52.8% (asset) | 52.8% (asset) | 52.8% (asset) | 54.2% (sensitive_first_look) | 54.2% (sensitive_first_look) | 52.8% (sensitive_first_look) | 52.8% (sensitive_first_look) | 52.8% (sensitive_first_look) | 54.2% (sensitive_first_look) | 59.7% (sensitive_first_look) | 36.1% (new_network) | 41.7% (new_tool) | 34.7% (new_network) | 43.1% (sensitive_first_look) | 36.1% (new_network) | 36.1% (new_network) | 36.1% (new_network) | 44.4% (new_network) | 44.4% (new_network) | 34.7% (new_network) | 31.9% (new_network) | 12.5% (sequence) | 23.6% (new_tool) | 23.6% (new_network) |
| new_project | 1278 | 64.1% (sequence) | 64.1% (sequence) | 72.5% (request_too_big) | 63.9% (sequence) | 64.2% (request_too_big) | 11.2% (asset) | 63.5% (sequence) | 64.1% (sequence) | 35.6% (asset) | 42.5% (sequence) | 42.2% (sequence) | 36.1% (asset) | 44.8% (sequence) | 17.4% (asset) | 46.8% (asset) | 11.5% (asset) | 11.2% (asset) | 11.3% (asset) | 11.2% (asset) | 11.2% (asset) | 11.2% (asset) | 11.2% (asset) | 12.6% (asset) | 8.5% (asset) | 8.6% (asset) | 8.5% (asset) | 10.8% (asset) | 8.5% (asset) | 8.5% (asset) | 7.9% (asset) | 9.2% (asset) | 8.7% (asset) | 8.2% (asset) | 8.1% (asset) | 7.5% (asset) | 7.5% (asset) | 7.9% (asset) |
| on_call_incident | 56 | 100.0% (sequence) | 100.0% (sequence) | 100.0% (sequence) | 100.0% (sequence) | 100.0% (sequence) | 10.7% (time_of_day) | 100.0% (sequence) | 100.0% (sequence) | 66.1% (time_of_day) | 100.0% (sequence) | 100.0% (sequence) | 66.1% (time_of_day) | 100.0% (sequence) | 21.4% (asset) | 94.6% (time_of_day) | 14.3% (time_of_day) | 14.3% (time_of_day) | 14.3% (time_of_day) | 12.5% (time_of_day) | 14.3% (time_of_day) | 14.3% (time_of_day) | 14.3% (time_of_day) | 14.3% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) | 12.5% (time_of_day) |
| org_repo_migration | 145 | 67.6% (request_too_big) | 67.6% (request_too_big) | 80.0% (asset) | 67.6% (request_too_big) | 67.6% (request_too_big) | 28.3% (asset) | 67.6% (request_too_big) | 67.6% (request_too_big) | 37.2% (asset) | 44.8% (asset) | 45.5% (asset) | 36.6% (asset) | 50.0% (asset) | 25.7% (asset) | 45.4% (asset) | 20.0% (asset) | 18.4% (asset) | 18.4% (asset) | 18.4% (asset) | 18.4% (asset) | 18.4% (asset) | 18.4% (asset) | 18.4% (asset) | 18.5% (asset) | 18.5% (asset) | 18.5% (asset) | 18.5% (asset) | 18.5% (asset) | 18.5% (asset) | 17.9% (asset) | 18.7% (asset) | 17.5% (asset) | 16.0% (asset) | 17.9% (asset) | 16.4% (asset) | 16.4% (asset) | 17.0% (asset) |
| org_tool_rollout | 156 | 84.0% (request_too_big) | 85.9% (new_tool) | 97.4% (new_tool) | 84.6% (new_tool) | 87.2% (request_too_big) | 71.2% (new_tool) | 76.9% (request_too_big) | 85.9% (new_tool) | 44.2% (tool) | 68.6% (tool) | 78.2% (new_tool) | 44.9% (tool) | 78.8% (new_tool) | 36.5% (asset) | 57.7% (tool) | 26.9% (tool) | 19.9% (new_tool) | 19.9% (new_tool) | 19.9% (new_tool) | 19.9% (new_tool) | 19.9% (new_tool) | 19.9% (new_tool) | 27.6% (tool) | 16.0% (new_tool) | 16.0% (new_tool) | 16.0% (new_tool) | 19.9% (new_tool) | 16.0% (new_tool) | 16.0% (new_tool) | 16.0% (new_tool) | 16.7% (new_tool) | 16.7% (new_tool) | 16.0% (new_tool) | 16.0% (new_tool) | 13.5% (tool) | 16.0% (new_tool) | 13.5% (tool) |
| org_vpn_change | 128 | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (new_network) | 100.0% (request_too_big) | 97.7% (new_network) | 61.7% (request_too_big) | 100.0% (new_network) | 11.7% (time_of_day) | 99.2% (new_network) | 99.2% (new_network) | 12.5% (time_of_day) | 99.2% (new_network) | 24.2% (asset) | 33.6% (asset) | 10.2% (new_network) | 9.4% (new_network) | 9.4% (new_network) | 9.4% (new_network) | 9.4% (new_network) | 9.4% (new_network) | 9.4% (new_network) | 11.7% (new_network) | 7.0% (new_network) | 7.0% (new_network) | 7.0% (new_network) | 9.4% (new_network) | 7.0% (new_network) | 7.0% (new_network) | 7.8% (new_network) | 8.6% (new_network) | 9.4% (new_network) | 7.8% (new_network) | 7.8% (new_network) | 5.5% (request_too_big) | 5.5% (request_too_big) | 7.8% (new_network) |
| release_crunch | 347 | 84.1% (request_too_big) | 84.1% (request_too_big) | 92.8% (time_of_day) | 85.9% (request_too_big) | 84.7% (request_too_big) | 14.4% (time_of_day) | 83.6% (request_too_big) | 84.1% (request_too_big) | 78.1% (time_of_day) | 51.0% (sequence) | 47.8% (sequence) | 79.3% (time_of_day) | 52.4% (asset) | 54.8% (time_of_day) | 86.2% (time_of_day) | 43.2% (time_of_day) | 39.5% (time_of_day) | 39.5% (time_of_day) | 39.2% (time_of_day) | 39.8% (time_of_day) | 39.2% (time_of_day) | 39.5% (time_of_day) | 42.4% (time_of_day) | 33.1% (time_of_day) | 33.1% (time_of_day) | 33.1% (time_of_day) | 39.5% (time_of_day) | 33.1% (time_of_day) | 33.1% (time_of_day) | 34.0% (time_of_day) | 34.3% (time_of_day) | 35.2% (time_of_day) | 34.0% (time_of_day) | 33.7% (time_of_day) | 33.7% (time_of_day) | 33.7% (time_of_day) | 34.0% (time_of_day) |
| role_change | 15 | 86.7% (sequence) | 86.7% (sequence) | 86.7% (sequence) | 86.7% (sequence) | 86.7% (request_too_big) | 13.3% (new_tool) | 86.7% (sequence) | 86.7% (sequence) | 20.0% (new_tool) | 66.7% (sequence) | 66.7% (sequence) | 20.0% (new_tool) | 66.7% (sequence) | 33.3% (asset) | 66.7% (asset) | 26.7% (asset) | 20.0% (new_tool) | 20.0% (sensitive_first_look) | 20.0% (new_tool) | 20.0% (new_tool) | 20.0% (new_tool) | 20.0% (new_tool) | 20.0% (new_tool) | 13.3% (new_tool) | 13.3% (new_tool) | 13.3% (new_tool) | 20.0% (new_tool) | 13.3% (new_tool) | 13.3% (new_tool) | 13.3% (new_tool) | 20.0% (new_tool) | 20.0% (new_tool) | 13.3% (new_tool) | 13.3% (new_tool) | 13.3% (tool) | 13.3% (new_tool) | 13.3% (tool) |
| team_transfer | 33 | 66.7% (request_too_big) | 66.7% (request_too_big) | 66.7% (request_too_big) | 66.7% (request_too_big) | 66.7% (request_too_big) | 3.0% (new_network) | 66.7% (request_too_big) | 66.7% (request_too_big) | 12.1% (time_of_day) | 18.2% (sequence) | 18.2% (sequence) | 15.2% (time_of_day) | 30.3% (asset) | 27.3% (asset) | 36.4% (asset) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (request_too_big) | 9.1% (sensitive_first_look) | 9.1% (request_too_big) | 9.1% (sensitive_first_look) | 9.1% (request_too_big) | 9.1% (request_too_big) | 6.1% (new_network) | 6.1% (new_network) | 6.1% (new_network) | 9.1% (new_network) | 6.1% (request_too_big) | 6.1% (request_too_big) | 6.1% (new_network) | 9.1% (request_too_big) | 9.1% (request_too_big) | 6.1% (request_too_big) | 6.1% (request_too_big) | 3.0% (request_too_big) | 3.0% (request_too_big) | 6.1% (new_network) |
| travel | 15 | 80.0% (time_of_day) | 80.0% (time_of_day) | 100.0% (time_of_day) | 80.0% (time_of_day) | 80.0% (time_of_day) | 40.0% (time_of_day) | 80.0% (time_of_day) | 80.0% (time_of_day) | 100.0% (time_of_day) | 66.7% (time_of_day) | 66.7% (time_of_day) | 100.0% (time_of_day) | 66.7% (time_of_day) | 66.7% (time_of_day) | 100.0% (time_of_day) | 53.3% (time_of_day) | 53.3% (time_of_day) | 53.3% (time_of_day) | 53.3% (time_of_day) | 53.3% (time_of_day) | 53.3% (time_of_day) | 53.3% (time_of_day) | 53.3% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 53.3% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) | 40.0% (time_of_day) |

## Gray episodes by kind

| Kind | episodes | v1 (shipped): caught · calls ≥x3 | v2: caught · calls ≥x3 | v2 + days: caught · calls ≥x3 | v2 + daily update: caught · calls ≥x3 | v2 + tie-break: caught · calls ≥x3 | v2 + rule rarity: caught · calls ≥x3 | v2 + org discount: caught · calls ≥x3 | v2 + 14-day onboarding: caught · calls ≥x3 | v2 + all fixes: caught · calls ≥x3 | v1, learned limits: caught · calls ≥x3 | v2, learned limits: caught · calls ≥x3 | v2 + all fixes, learned limits: caught · calls ≥x3 | v2 + new detectors, learned limits: caught · calls ≥x3 | v2 + recommended, learned limits: caught · calls ≥x3 | v2 + recommended + days, learned limits: caught · calls ≥x3 | v2 + recommended (first look only), learned limits: caught · calls ≥x3 | v3: caught · calls ≥x3 | v3, assets/hour as a rule: caught · calls ≥x3 | v3, weekend split: caught · calls ≥x3 | v3, weekend fallback: caught · calls ≥x3 | v3, weekend flag: caught · calls ≥x3 | v3 without writes/hour: caught · calls ≥x3 | v3 + tie-break formula: caught · calls ≥x3 | v3 final: caught · calls ≥x3 | v3 final, 5-call warm-up: caught · calls ≥x3 | v3 final, first-day warm-up without rules: caught · calls ≥x3 | v3 final, flat first-look rule: caught · calls ≥x3 | v3 final, first look by asset only: caught · calls ≥x3 | v3 final, first look tool step 0.1: caught · calls ≥x3 | v3 final, size limits per agent-day: caught · calls ≥x3 | v3 final, first look anchored at a read: caught · calls ≥x3 | v3 final, read anchor, sizes per agent-day: caught · calls ≥x3 | v3 (decided), org discount on first looks: caught · calls ≥x3 | v3 (decided): caught · calls ≥x3 | v4: caught · calls ≥x3 | v3 (decided), network and app in Footprint: caught · calls ≥x3 | v3 (decided), new tool through tool rarity: caught · calls ≥x3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| big_paste | 4 | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 25.0% · 25.0% | 100.0% · 100.0% | 100.0% · 100.0% | 50.0% · 50.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| bot_loop | 3 | 100.0% · 96.9% | 100.0% · 96.9% | 100.0% · 96.9% | 100.0% · 96.9% | 100.0% · 96.9% | 100.0% · 96.9% | 100.0% · 96.9% | 100.0% · 96.9% | 100.0% · 96.9% | 100.0% · 91.3% | 100.0% · 91.3% | 100.0% · 91.3% | 100.0% · 95.8% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 96.6% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 96.6% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% | 100.0% · 95.8% |
| bulk_export | 11 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 9.1% · 0.6% | 0.0% · 0.0% | 0.0% · 0.0% | 9.1% · 0.6% | 90.9% · 12.1% | 90.9% · 24.1% | 100.0% · 25.2% | 81.8% · 19.3% | 81.8% · 8.6% | 100.0% · 79.4% | 81.8% · 8.6% | 81.8% · 8.6% | 81.8% · 8.6% | 81.8% · 8.6% | 81.8% · 19.5% | 100.0% · 77.3% | 100.0% · 77.3% | 100.0% · 77.3% | 100.0% · 79.2% | 100.0% · 77.6% | 100.0% · 76.9% | 100.0% · 77.3% | 100.0% · 78.2% | 100.0% · 78.2% | 100.0% · 77.8% | 100.0% · 77.9% | 100.0% · 78.0% | 100.0% · 78.0% | 100.0% · 78.0% |
| cross_copy | 6 | 100.0% · 44.6% | 100.0% · 44.6% | 100.0% · 44.6% | 100.0% · 44.6% | 100.0% · 44.6% | 16.7% · 4.8% | 100.0% · 44.6% | 100.0% · 44.6% | 16.7% · 7.1% | 100.0% · 44.6% | 100.0% · 44.6% | 16.7% · 7.1% | 100.0% · 81.2% | 50.0% · 35.4% | 50.0% · 35.4% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 16.7% · 7.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% | 33.3% · 27.1% |
| mass_cleanup | 9 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 11.1% · 11.1% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 11.1% · 11.1% | 0.0% · 0.0% | 0.0% · 0.0% | 11.1% · 11.1% | 11.1% · 5.7% | 55.6% · 20.1% | 55.6% · 20.1% | 55.6% · 20.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 11.1% · 11.1% | 55.6% · 20.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 22.2% · 17.1% | 11.1% · 6.0% | 11.1% · 6.0% | 22.2% · 17.1% |
| off_hours_batch | 10 | 20.0% · 1.6% | 20.0% · 1.6% | 20.0% · 13.5% | 20.0% · 13.5% | 20.0% · 1.6% | 20.0% · 1.6% | 20.0% · 1.6% | 20.0% · 1.6% | 20.0% · 13.5% | 20.0% · 1.6% | 20.0% · 1.6% | 20.0% · 13.5% | 70.0% · 7.0% | 70.0% · 70.0% | 90.0% · 90.0% | 70.0% · 70.0% | 80.0% · 80.0% | 80.0% · 80.0% | 20.0% · 13.5% | 70.0% · 70.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% | 80.0% · 80.0% |
| overfetch | 10 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% |
| scope_creep | 8 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 12.5% · 0.4% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 100.0% · 11.3% | 100.0% · 10.1% | 100.0% · 11.2% | 50.0% · 1.3% | 62.5% · 1.5% | 75.0% · 3.6% | 62.5% · 1.5% | 62.5% · 1.5% | 62.5% · 1.5% | 62.5% · 1.5% | 62.5% · 1.5% | 37.5% · 2.2% | 37.5% · 2.2% | 37.5% · 2.2% | 62.5% · 3.1% | 37.5% · 2.2% | 37.5% · 2.2% | 37.5% · 2.2% | 37.5% · 2.2% | 37.5% · 2.2% | 37.5% · 2.2% | 25.0% · 2.0% | 37.5% · 2.2% | 37.5% · 2.2% | 37.5% · 2.2% |
| sensitive_peek | 6 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 100.0% · 80.6% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 0.0% · 0.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| shadow_script | 7 | 100.0% · 4.7% | 100.0% · 4.7% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 6.3% | 100.0% · 4.7% | 100.0% · 4.7% | 100.0% · 4.7% | 100.0% · 100.0% | 100.0% · 4.7% | 100.0% · 4.7% | 100.0% · 100.0% | 100.0% · 11.7% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% | 100.0% · 100.0% |
| slow_loop | 5 | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 20.0% · 5.2% | 20.0% · 3.8% | 0.0% · 0.0% | 0.0% · 0.0% | 0.0% · 0.0% | 20.0% · 8.3% | 0.0% · 0.0% | 0.0% · 0.0% | 20.0% · 8.3% | 100.0% · 77.1% | 100.0% · 86.5% | 100.0% · 86.8% | 100.0% · 86.6% | 100.0% · 84.5% | 100.0% · 84.5% | 100.0% · 84.5% | 100.0% · 84.5% | 100.0% · 84.5% | 100.0% · 84.5% | 100.0% · 86.6% | 100.0% · 84.5% | 100.0% · 84.5% | 100.0% · 84.5% | 100.0% · 84.5% | 100.0% · 84.5% | 100.0% · 84.5% | 100.0% · 84.5% | 100.0% · 84.6% | 100.0% · 84.6% | 100.0% · 84.6% | 100.0% · 84.5% | 100.0% · 84.4% | 100.0% · 84.4% | 100.0% · 84.4% |

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
