# Scan — sqlite:devops_sqlite

_kind=sqlite · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_desc · bands={'low': 10, 'medium': 5, 'high': 9, 'critical': 5, 'na': 16}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–25), scaled to this max.

## Inferred domain profile

- **mcp_kind**: SQL database
- **asset_meaning**: Tables within the CBG SQLite control-plane record for deployments and authentication.
- **blast_radius_meaning**: The extent of impact a tool can have on an asset, from reading a few rows to modifying or deleting entire tables.
- **dangerous_classes**: Holds secrets, Holds PII at scale, Is executable
- **irreversible_actions**: write_query, insert_row
- **worked_example**: The 'write_query' tool paired with the 'api_tokens' asset can insert a new token, granting unauthorized access.

## Tool impact

| tool | impact |
| --- | --- |
| `list_tables` | 2 |
| `describe_table` | 2 |
| `read_query` | 3 |
| `write_query` | 5 |
| `insert_row` | 4 |

## Asset sensitivity

_Not scored in `impact_mode=five_level_v2_desc`: the organization's written description of this server states how severe each asset is, so no separate 1–5 sensitivity primitive is derived. The 9 assets below still form the matrix axis; the score is `blast × impact`._

| asset | sensitivity |
| --- | --- |
| `users` | — |
| `api_tokens` | — |
| `deployments` | — |
| `audit_log` | — |
| `public_metrics` | — |
| `table-catalog` | — |
| `table-metadata` | — |
| `database-records` | — |
| `table-records` | — |

## Risk matrix (score · band)

_Each cell shows `score (blast×impact)` — sensitivity is not scored in this mode; impact_mode=five_level_v2_desc, score ranges 0–25. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `users` | N/A | 2 (1×2) 🟢 | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 |
| `api_tokens` | N/A | 2 (1×2) 🟢 | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 |
| `deployments` | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 6 (2×3) 🟢 | 20 (4×5) 🔴 | 4 (1×4) 🟢 |
| `audit_log` | 2 (1×2) 🟢 | 2 (1×2) 🟢 | 6 (2×3) 🟢 | 25 (5×5) 🔴 | 12 (3×4) 🟡 |
| `public_metrics` | N/A | 2 (1×2) 🟢 | 6 (2×3) 🟢 | 10 (2×5) 🟡 | 4 (1×4) 🟢 |
| `table-catalog` | 2 (1×2) 🟢 | N/A | N/A | N/A | N/A |
| `table-metadata` | 2 (1×2) 🟢 | 2 (1×2) 🟢 | N/A | N/A | N/A |
| `database-records` | N/A | N/A | 15 (5×3) 🟠 | N/A | N/A |
| `table-records` | N/A | N/A | 15 (5×3) 🟠 | 25 (5×5) 🔴 | 20 (5×4) 🔴 |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | list_tables | describe_table | read_query | write_query | insert_row |
| --- | --- | --- | --- | --- | --- |
| `users` | N/A | 1 | 5 | 5 | 5 |
| `api_tokens` | N/A | 1 | 5 | 5 | 5 |
| `deployments` | 1 | 1 | 2 | 4 | 1 |
| `audit_log` | 1 | 1 | 2 | 5 | 3 |
| `public_metrics` | N/A | 1 | 2 | 2 | 1 |
| `table-catalog` | 1 | N/A | N/A | N/A | N/A |
| `table-metadata` | 1 | 1 | N/A | N/A | N/A |
| `database-records` | N/A | N/A | 5 | N/A | N/A |
| `table-records` | N/A | N/A | 5 | 5 | 5 |

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
