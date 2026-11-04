# Call distributions: generated tables

Written by `scripts/call_distributions.py`; see [README.md](README.md) for what they mean.

## Tool mix

| Corpus | Kind | Calls | Tools used / catalog | Top-1 | Top-3 | Tools for 80% | Zipf R² | Geometric R² | Shape | Failure rate |
|---|---|---|---|---|---|---|---|---|---|---|
| MCPHunt (5 models) | outside agents | 62,332 | 28 / 66 | 0.317 | 0.626 | 6 | 0.699 | 0.878 | geometric | 0.118 |
| Normal org world (GitHub, 150 agents, 180 days) | simulated org | 3,317,587 | 30 / 30 | 0.180 | 0.428 | 10 | 0.698 | 0.937 | geometric | — |
| World2 github (50 agents, 730 days) | simulated org | 1,620,208 | 26 / — | 0.355 | 0.718 | 5 | 0.924 | 0.971 | geometric | — |
| World2 slack (50 agents, 730 days) | simulated org | 1,558,958 | 16 / — | 0.588 | 0.838 | 3 | 0.958 | 0.948 | zipf | — |
| World2 calendar (50 agents, 730 days) | simulated org | 1,846,182 | 13 / — | 0.539 | 0.837 | 3 | 0.868 | 0.978 | geometric | — |
| Persona corpus GitHub (100k) | persona corpus | 100,000 | 26 / — | 0.176 | 0.488 | 9 | 0.898 | 0.981 | geometric | — |
| Scripted real GitHub (1k) | scripted real calls | 1,000 | 8 / — | 0.145 | 0.411 | 7 | 0.858 | 0.903 | geometric | 0.212 |
| Persona corpus Slack (100k) | persona corpus | 100,000 | 16 / — | 0.267 | 0.519 | 7 | 0.875 | 0.984 | geometric | — |
| Scripted real Slack (1k) | scripted real calls | 1,000 | 7 / — | 0.251 | 0.521 | 6 | 0.811 | 0.616 | zipf | 0.000 |
| Persona corpus Calendar (100k) | persona corpus | 100,000 | 13 / — | 0.330 | 0.623 | 5 | 0.882 | 0.979 | geometric | — |
| Scripted real Calendar (1k) | scripted real calls | 1,000 | 6 / — | 0.186 | 0.523 | 5 | 0.938 | 0.904 | zipf | 0.042 |
| Scripted real finance_tools_orbit | scripted real calls | 600 | 16 / — | 0.077 | 0.218 | 13 | 0.832 | 0.959 | geometric | 0.307 |
| Scripted real maverick_talon | scripted real calls | 600 | 94 / — | 0.025 | 0.070 | 61 | 0.651 | 0.845 | geometric | 0.135 |
| Scripted real openbb_atlas | scripted real calls | 600 | 27 / — | 0.052 | 0.152 | 20 | 0.713 | 0.942 | geometric | 0.402 |
| Scripted real sec_edgar_ledger | scripted real calls | 600 | 21 / — | 0.062 | 0.178 | 16 | 0.859 | 0.965 | geometric | 0.030 |
| Scripted real yahoo_finance_kestrel | scripted real calls | 600 | 9 / — | 0.125 | 0.368 | 7 | 0.879 | 0.967 | geometric | 0.000 |

## Calls per session

| Corpus | n | Mean | Median | p90 | p99 | Max | Best fit (AIC) | KS of best | Tail index |
|---|---|---|---|---|---|---|---|---|---|
| MCPHunt (5 models) | 3,615 | 17.24 | 11.00 | 38.00 | 79.00 | 112.00 | lognorm | 0.043 | 3.98 |
| Normal org world (GitHub, 150 agents, 180 days) | 271,934 | 12.20 | 6.00 | 13.00 | 133.00 | 1,667 | lognorm | 0.238 | 1.33 |
| World2 github (50 agents, 730 days) | 494,504 | 3.28 | 3.00 | 6.00 | 11.00 | 107.00 | lognorm | 0.137 | 3.24 |
| World2 slack (50 agents, 730 days) | 474,521 | 3.29 | 3.00 | 6.00 | 11.00 | 107.00 | lognorm | 0.135 | 3.13 |
| World2 calendar (50 agents, 730 days) | 579,326 | 3.19 | 3.00 | 6.00 | 11.00 | 106.00 | lognorm | 0.141 | 3.75 |

## Seconds between calls in a session

| Corpus | n | Mean | Median | p90 | p99 | Max | Best fit (AIC) | KS of best | Tail index |
|---|---|---|---|---|---|---|---|---|---|
| MCPHunt (5 models) | 58,717 | 3.16 | 1.97 | 6.48 | 28.26 | 303.96 | gamma | 0.214 | 1.57 |
| Normal org world (GitHub, 150 agents, 180 days) | 3,045,653 | 56.93 | 1.91 | 164.75 | 803.66 | 17,452 | lognorm | 0.206 | 1.83 |
| World2 github (50 agents, 730 days) | 1,125,704 | 4.41 | 2.38 | 9.75 | 32.36 | 334.83 | lognorm | 0.041 | 2.16 |
| World2 slack (50 agents, 730 days) | 1,084,437 | 4.52 | 2.41 | 10.07 | 33.17 | 290.54 | lognorm | 0.041 | 2.20 |
| World2 calendar (50 agents, 730 days) | 1,266,856 | 3.81 | 2.22 | 7.93 | 27.34 | 546.09 | lognorm | 0.036 | 2.06 |

Share of gaps under 0.1 s (calls sent together): MCPHunt (5 models) 0.367; Normal org world (GitHub, 150 agents, 180 days) 0.002; World2 github (50 agents, 730 days) 0.000; World2 slack (50 agents, 730 days) 0.000; World2 calendar (50 agents, 730 days) 0.000

## Reply size per call

| Corpus | n | Mean | Median | p90 | p99 | Max | Best fit (AIC) | KS of best | Tail index |
|---|---|---|---|---|---|---|---|---|---|
| MCPHunt (5 models) | 62,332 | 1,376 | 138.00 | 488.00 | 7,857 | 11,944,623 | lognorm | 0.088 | 0.96 |
| Normal org world (GitHub, 150 agents, 180 days) | 3,317,587 | 17,155 | 5,753 | 49,393 | 127,517 | 1,000,060 | lognorm | 0.104 | 2.90 |

| Corpus | Unit | Top 0.5% of calls carry | Top 1% carry | Weekend share |
|---|---|---|---|---|
| MCPHunt (5 models) | chars | 0.744 | 0.775 | 0.411 |
| Normal org world (GitHub, 150 agents, 180 days) | bytes | 0.057 | 0.098 | 0.081 |
| World2 github (50 agents, 730 days) | — | — | — | 0.139 |
| World2 slack (50 agents, 730 days) | — | — | — | 0.137 |
| World2 calendar (50 agents, 730 days) | — | — | — | 0.148 |
