# Scan — sqlite:cbg_sqlite

_kind=sqlite · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v4 · bands={'low': 12, 'medium': 19, 'high': 3, 'critical': 4, 'na': 17}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Deterministic rules applied

- sensitivity = org profile table (never LLM-scored)
- bulk twin impact: impact(bulk) >= impact(singular)
- alias twins (DEPRECATED -> canonical): max blast per asset
- gated blast floor (impact >= 4): sens 5 -> blast >= 4, sens 4 -> blast >= 3
- impact-keyed floor (one tier lower): impact 5 -> blast >= 3, impact 4 -> blast >= 2
- bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)
- blast roof (impact <= 3 only, never a mutation): non-escaping read caps at 4, sens-1 caps at 4 — assets flagged hub/population/self-sufficient are exempt
- bands: band_label_v5 — pure score thresholds on the 0-125 scale (low <17, medium 17-49, high 50-99, critical >=100); no categorical overrides, so a band is explainable from its own score

## Inferred domain profile

- **mcp_kind**: SQL database
- **asset_meaning**: A table within the CBG research-arm database.
- **blast_radius_meaning**: The extent of rows or tables a tool can affect; from affecting one row to potentially altering all records across multiple tables.
- **dangerous_classes**: holds secrets, holds PII at scale, is executable
- **irreversible_actions**: write_query, insert_row
- **worked_example**: The `write_query` tool on the `api_keys` asset can irreversibly alter or delete sensitive credentials, escalating severity.

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
| `publications` | 2 |
| `table-catalog` | 2 |
| `table-metadata` | 2 |
| `database-records` | 4 |
| `table-records` | 3 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v4, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `api_keys` | N/A | 10 (5×1×2) 🟢 | 45 (5×3×3) 🟡 | 125 (5×5×5) 🔴 | 100 (5×5×4) 🔴 |
| `employees` | N/A | 8 (4×1×2) 🟢 | 48 (4×4×3) 🟡 | 100 (4×5×5) 🔴 | 48 (4×3×4) 🟡 |
| `grants` | N/A | 8 (4×1×2) 🟢 | 36 (4×3×3) 🟡 | 80 (4×4×5) 🟠 | 48 (4×3×4) 🟡 |
| `datasets` | N/A | 6 (3×1×2) 🟢 | 27 (3×3×3) 🟢 | 45 (3×3×5) 🟡 | 24 (3×2×4) 🟢 |
| `experiments` | N/A | 6 (3×1×2) 🟢 | 27 (3×3×3) 🟢 | 45 (3×3×5) 🟡 | 24 (3×2×4) 🟢 |
| `projects` | N/A | 6 (3×1×2) 🟢 | 27 (3×3×3) 🟢 | 45 (3×3×5) 🟡 | 24 (3×2×4) 🟢 |
| `publications` | N/A | 4 (2×1×2) 🟢 | 18 (2×3×3) 🟢 | 40 (2×4×5) 🟡 | 16 (2×2×4) 🟢 |
| `table-catalog` | 4 (2×1×2) 🟢 | N/A | 6 (2×1×3) 🟢 | N/A | N/A |
| `table-metadata` | N/A | 4 (2×1×2) 🟢 | 6 (2×1×3) 🟢 | 30 (2×3×5) 🟢 | N/A |
| `database-records` | N/A | N/A | 60 (4×5×3) 🟡 | 100 (4×5×5) 🔴 | 80 (4×5×4) 🟠 |
| `table-records` | N/A | N/A | N/A | 45 (3×3×5) 🟡 | 36 (3×3×4) 🟡 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `api_keys` | N/A | 1 | 3 | 5 | 5 |
| `employees` | N/A | 1 | 4 | 5 | 3 |
| `grants` | N/A | 1 | 3 | 4 | 3 |
| `datasets` | N/A | 1 | 3 | 3 | 2 |
| `experiments` | N/A | 1 | 3 | 3 | 2 |
| `projects` | N/A | 1 | 3 | 3 | 2 |
| `publications` | N/A | 1 | 3 | 4 | 2 |
| `table-catalog` | 1 | N/A | 1 | N/A | N/A |
| `table-metadata` | N/A | 1 | 1 | 3 | N/A |
| `database-records` | N/A | N/A | 5 | 5 | 5 |
| `table-records` | N/A | N/A | N/A | 3 | 3 |

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
