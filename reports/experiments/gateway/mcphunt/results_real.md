# MCPHunt calls scored by the framework (real clock)

61,926 scored calls; not scored (no scan): {'time': 406}.

## Per route

| Route | Calls | Binding | Bands | Mean cell | Mean risk | Mean dynamic |
|---|---|---|---|---|---|---|
| browser | 773 | unresolved 450, named 323 | high 481, critical 292 | 89.65 | 85.58 | 9.23 |
| fetch | 630 | named 353, unresolved 277 | high 630 | 69.33 | 69.33 | 9.23 |
| filesystem | 37,443 | named 23,622, unresolved 13,821 | medium 17,054, high 11,608, low 8,781 | 38.0 | 34.46 | 6.53 |
| git | 3,297 | unresolved 1,818, sole-candidate 1,479 | medium 2,539, low 758 | 36.1 | 35.65 | 5.3 |
| memory | 1,196 | sole-candidate 681, unresolved 467, named 48 | high 1,172, critical 24 | 68.59 | 62.5 | 9.39 |
| shell | 11,253 | unresolved 7,760, named 3,493 | critical 11,248, high 3, medium 2 | 123.04 | 123.04 | 11.94 |
| sqlite | 7,334 | sole-candidate 3,708, named 3,279, unresolved 347 | low 3,708, critical 3,626 | 65.21 | 63.47 | 7.09 |

## Call scores per run group

| Group | Score | Calls | Mean | Median | p90 |
|---|---|---|---|---|---|
| benign | cell | 12,445 | 58.06 | 48.0 | 125.0 |
| benign | risk | 12,445 | 55.39 | 41.76 | 125.0 |
| benign | dynamic_risk | 12,445 | 5.86 | 4.22 | 15.28 |
| risky | cell | 33,608 | 56.99 | 48.0 | 125.0 |
| risky | risk | 33,608 | 54.51 | 41.9 | 125.0 |
| risky | dynamic_risk | 33,608 | 9.48 | 9.13 | 18.12 |
| hard_neg | cell | 15,873 | 60.58 | 48.0 | 125.0 |
| hard_neg | risk | 15,873 | 58.06 | 46.69 | 125.0 |
| hard_neg | dynamic_risk | 15,873 | 5.11 | 4.0 | 9.54 |

## Run level (highest score in a run)

3,615 runs, 844 judged unsafe by MCPHunt.

| Score | Risky vs benign | Risky vs hard negative | Unsafe vs safe |
|---|---|---|---|
| cell | 0.501 | 0.486 | 0.579 |
| risk | 0.506 | 0.488 | 0.548 |
| dynamic_risk | 0.732 | 0.808 | 0.619 |

## Call level: arguments carrying a planted secret

1,272 calls; by tool: filesystem.write_file 874, memory.create_entities 195, sqlite.write_query 138, shell.execute_command 46, memory.add_observations 19.

| Score | AUC vs every other call |
|---|---|
| cell | 0.477 |
| risk | 0.479 |
| dynamic_risk | 0.505 |

## Behaviour multiplier

| Group | Calls | Share above 1 | Mean |
|---|---|---|---|
| benign | 12,445 | 0.315 | 1.549 |
| risky | 33,608 | 0.642 | 2.488 |
| hard_neg | 15,873 | 0.294 | 1.36 |
