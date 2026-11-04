# MCPHunt calls scored by the framework (spread clock)

61,926 scored calls; not scored (no scan): {'time': 406}.

## Per route

| Route | Calls | Binding | Bands | Mean cell | Mean risk | Mean dynamic |
|---|---|---|---|---|---|---|
| browser | 773 | unresolved 450, named 323 | high 481, critical 292 | 89.65 | 85.1 | 5.18 |
| fetch | 630 | named 353, unresolved 277 | high 630 | 69.33 | 69.33 | 4.67 |
| filesystem | 37,443 | named 23,622, unresolved 13,821 | medium 17,054, high 11,608, low 8,781 | 38.0 | 34.13 | 3.43 |
| git | 3,297 | unresolved 1,818, sole-candidate 1,479 | medium 2,539, low 758 | 36.1 | 35.94 | 3.09 |
| memory | 1,196 | sole-candidate 681, unresolved 467, named 48 | high 1,172, critical 24 | 68.59 | 63.0 | 4.5 |
| shell | 11,253 | unresolved 7,760, named 3,493 | critical 11,248, high 3, medium 2 | 123.04 | 123.04 | 5.26 |
| sqlite | 7,334 | sole-candidate 3,708, named 3,279, unresolved 347 | low 3,708, critical 3,626 | 65.21 | 64.03 | 3.57 |

## Call scores per run group

| Group | Score | Calls | Mean | Median | p90 |
|---|---|---|---|---|---|
| benign | cell | 12,445 | 58.06 | 48.0 | 125.0 |
| benign | risk | 12,445 | 55.41 | 41.74 | 125.0 |
| benign | dynamic_risk | 12,445 | 3.84 | 3.48 | 5.41 |
| risky | cell | 33,608 | 56.99 | 48.0 | 125.0 |
| risky | risk | 33,608 | 54.25 | 41.66 | 125.0 |
| risky | dynamic_risk | 33,608 | 3.76 | 3.4 | 5.37 |
| hard_neg | cell | 15,873 | 60.58 | 48.0 | 125.0 |
| hard_neg | risk | 15,873 | 58.13 | 46.84 | 125.0 |
| hard_neg | dynamic_risk | 15,873 | 3.9 | 3.6 | 5.67 |

## Run level (highest score in a run)

3,615 runs, 844 judged unsafe by MCPHunt.

| Score | Risky vs benign | Risky vs hard negative | Unsafe vs safe |
|---|---|---|---|
| cell | 0.501 | 0.486 | 0.579 |
| risk | 0.506 | 0.488 | 0.547 |
| dynamic_risk | 0.497 | 0.495 | 0.581 |

## Call level: arguments carrying a planted secret

1,272 calls; by tool: filesystem.write_file 874, memory.create_entities 195, sqlite.write_query 138, shell.execute_command 46, memory.add_observations 19.

| Score | AUC vs every other call |
|---|---|
| cell | 0.477 |
| risk | 0.476 |
| dynamic_risk | 0.504 |

## Behaviour multiplier

| Group | Calls | Share above 1 | Mean |
|---|---|---|---|
| benign | 12,445 | 0.207 | 1.054 |
| risky | 33,608 | 0.194 | 1.039 |
| hard_neg | 15,873 | 0.221 | 1.056 |
