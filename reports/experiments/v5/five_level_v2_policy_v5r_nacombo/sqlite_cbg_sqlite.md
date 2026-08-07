# Scan — sqlite:cbg_sqlite

_kind=sqlite · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v5r_nacombo · bands={'low': 13, 'medium': 13, 'high': 7, 'critical': 4, 'na': 18}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Deterministic rules applied

- sensitivity = LLM classification against the org POLICY (classify -> map; the org supplies no numbers)
- tool impact = deterministic ladder (static_impact.py); the v4 impact prompt decides only where the ladder abstains (confidence < 0.5)
- bulk twin impact: impact(bulk) >= impact(singular)
- alias twins (DEPRECATED -> canonical): max blast per asset
- blast floor, UNGATED: 
- bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)
- blast roof: REMOVED in this mode (a cap can only under-score)
- bands: band_label_v5 — pure score thresholds on the 0-125 scale (low <17, medium 17-49, high 50-99, critical >=100); no categorical overrides, so a band is explainable from its own score

## Inferred domain profile

- **mcp_kind**: SQL database

## Tool impact

| tool | impact |
| --- | --- |
| `list_tables` | 2 |
| `describe_table` | 2 |
| `read_query` | 3 |
| `write_query` | 5 |
| `insert_row` | 4 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `api_keys` | 5 |
| `employees` | 4 |
| `grants` | 4 |
| `datasets` | 3 |
| `experiments` | 3 |
| `projects` | 3 |
| `publications` | 1 |
| `database-records` | 5 |
| `table-records` | 3 |
| `table-catalog` | 3 |
| `table-metadata` | 2 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v5r_nacombo, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `api_keys` | N/A | 50 (5×5×2) 🟡 | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | 100 (5×5×4) 🔴 |
| `employees` | N/A | 16 (4×2×2) 🟢 | 48 (4×4×3) 🟡 | 100 (4×5×5) 🔴 | 32 (4×2×4) 🟢 |
| `grants` | N/A | 16 (4×2×2) 🟢 | 36 (4×3×3) 🟡 | 80 (4×4×5) 🟠 | 64 (4×4×4) 🟡 |
| `datasets` | N/A | 6 (3×1×2) 🟢 | 27 (3×3×3) 🟢 | 30 (3×2×5) 🟢 | 24 (3×2×4) 🟢 |
| `experiments` | N/A | 12 (3×2×2) 🟢 | 27 (3×3×3) 🟢 | 60 (3×4×5) 🟡 | 36 (3×3×4) 🟡 |
| `projects` | N/A | 12 (3×2×2) 🟢 | 18 (3×2×3) 🟢 | 30 (3×2×5) 🟢 | 24 (3×2×4) 🟢 |
| `publications` | N/A | 4 (1×2×2) 🟢 | 6 (1×2×3) 🟢 | 10 (1×2×5) 🟢 | 8 (1×2×4) 🟢 |
| `database-records` | N/A | 10 (5×1×2) 🟢 | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | N/A |
| `table-records` | N/A | N/A | N/A | 75 (3×5×5) 🟠 | 48 (3×4×4) 🟡 |
| `table-catalog` | 12 (3×2×2) 🟢 | N/A | 27 (3×3×3) 🟢 | N/A | N/A |
| `table-metadata` | N/A | 8 (2×2×2) 🟢 | 6 (2×1×3) 🟢 | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `api_keys` | N/A | 5 | 5 | 5 | 5 |
| `employees` | N/A | 2 | 4 | 5 | 2 |
| `grants` | N/A | 2 | 3 | 4 | 4 |
| `datasets` | N/A | 1 | 3 | 2 | 2 |
| `experiments` | N/A | 2 | 3 | 4 | 3 |
| `projects` | N/A | 2 | 2 | 2 | 2 |
| `publications` | N/A | 2 | 2 | 2 | 2 |
| `database-records` | N/A | 1 | 5 | 5 | N/A |
| `table-records` | N/A | N/A | N/A | 5 | 4 |
| `table-catalog` | 2 | N/A | 3 | N/A | N/A |
| `table-metadata` | N/A | 2 | 1 | N/A | N/A |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `list_tables` | **LIST** | 1 (Low) | LIST | rules |
| `describe_table` | **METADATA** | 1 (Low) | METADATA | rules |
| `read_query` | **READ** | 2 (Low) | READ | rules |
| `write_query` | **EXECUTE** | 5 (Critical) | DELETE, EXECUTE, OVERWRITE, SCHEMA_MODIFY, WRITE | rules |
| `insert_row` | **WRITE** | 3 (Medium) | WRITE | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `describe_table` | `table` | 2 | — | merely names the target |
| `read_query` | `sql` | 5 | null | fully controllable free-form query |
| `write_query` | `sql` | 5 | — | fully controllable query with potential for bulk operations |
| `insert_row` | `values` | 5 | — | fully controlled payload by caller |
| `insert_row` | `table` | 2 | — | merely names the target |
