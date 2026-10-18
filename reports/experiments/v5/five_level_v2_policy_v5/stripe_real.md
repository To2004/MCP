# Scan — stripe:real

_kind=stripe · provenance=llm-scan · model_reviewed=True · impact_mode=five_level_v2_v5 · bands={'low': 7, 'medium': 13, 'high': 14, 'critical': 5, 'na': 81}_

Risk derived live by the LLM from the scanned tools and assets — no checked-in table was read. Matrix colour is by RAW SCORE (0–125), scaled to this max.

## Deterministic rules applied

- sensitivity = LLM classification against the org POLICY (classify -> map; the org supplies no numbers)
- tool impact = deterministic ladder (static_impact.py); the v4 impact prompt decides only where the ladder abstains (confidence < 0.5)
- bulk twin impact: impact(bulk) >= impact(singular)
- alias twins (DEPRECATED -> canonical): max blast per asset
- gated blast floor (impact >= 4): sens 5 -> blast >= 4, sens 4 -> blast >= 3
- impact-keyed floor (one tier lower): impact 5 -> blast >= 3, impact 4 -> blast >= 2
- bulk twin blast: blast(bulk) > blast(singular) per asset (+1 on tie, cap 5)
- blast roof (impact <= 3 only, never a mutation): non-escaping read caps at 4, sens-1 caps at 4 — assets flagged hub/population/self-sufficient are exempt
- bands: band_label_v5 — pure score thresholds on the 0-125 scale (low <17, medium 17-49, high 50-99, critical >=100); no categorical overrides, so a band is explainable from its own score

## Inferred domain profile

- **mcp_kind**: payment processor
- **asset_meaning**: specific categories of data and configurations managed by Stripe's API, such as customer PII, payment instruments, account settings, and transaction records
- **blast_radius_meaning**: the extent to which a tool can affect or access different types of assets within the Stripe environment; from narrow (affecting only specific items) to broad (impacting multiple categories of data)
- **dangerous_classes**: holds secrets or PII at scale, moves real money, is executable
- **irreversible_actions**: create_refund, stripe_api_write
- **worked_example**: The tool 'create_refund' paired with the asset 'refunds' is highly severe because a refund action cannot be undone and directly impacts financial integrity.

## Tool impact

| tool | impact |
| --- | --- |
| `stripe_implementation_planner` | 5 |
| `send_stripe_mcp_feedback` | 5 |
| `search_stripe_documentation` | 3 |
| `get_stripe_account_info` | 2 |
| `create_refund` | 5 |
| `stripe_api_search` | 3 |
| `stripe_api_details` | 3 |
| `stripe_api_read` | 3 |
| `stripe_api_write` | 5 |
| `stripe_analytics` | 3 |

## Asset sensitivity

| asset | sensitivity |
| --- | --- |
| `account-config` | 5 |
| `payment-instruments` | 5 |
| `customer-pii` | 4 |
| `charges-and-payments` | 3 |
| `refunds` | 4 |
| `subscriptions-and-billing` | 3 |
| `payouts-and-bank-routing` | 5 |
| `disputes-and-evidence` | 4 |
| `products-and-prices` | 3 |
| `revenue-analytics` | 4 |
| `operation-catalog` | 2 |
| `documentation-and-planning` | 1 |

## Risk matrix (score · band)

_Each cell shows `score (sensitivity×blast×impact)`; impact_mode=five_level_v2_v5, score ranges 0–125. Colour is by raw score, scaled to this max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._

| asset \ tool | stripe_implementation_planner | send_stripe_mcp_feedback | search_stripe_documentation | get_stripe_account_info | create_refund | stripe_api_search | stripe_api_details | stripe_api_read | stripe_api_write | stripe_analytics |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `account-config` | N/A | N/A | N/A | 50 (5×5×2) 🟡 | N/A | N/A | N/A | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | N/A |
| `payment-instruments` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | 60 (5×4×3) 🟡 |
| `customer-pii` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 60 (4×5×3) 🟡 | 100 (4×5×5) 🔴 | N/A |
| `charges-and-payments` | N/A | N/A | N/A | N/A | 45 (3×3×5) 🟡 | 9 (3×1×3) 🟢 | N/A | 36 (3×4×3) 🟡 | 60 (3×4×5) 🟡 | 36 (3×4×3) 🟡 |
| `refunds` | N/A | N/A | N/A | N/A | 60 (4×3×5) 🟡 | N/A | N/A | 48 (4×4×3) 🟡 | 80 (4×4×5) 🟠 | N/A |
| `subscriptions-and-billing` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 36 (3×4×3) 🟡 | 60 (3×4×5) 🟡 | 36 (3×4×3) 🟡 |
| `payouts-and-bank-routing` | N/A | N/A | N/A | 50 (5×5×2) 🟡 | N/A | N/A | N/A | 75 (5×5×3) 🟠 | 125 (5×5×5) 🔴 | N/A |
| `disputes-and-evidence` | N/A | N/A | N/A | N/A | N/A | 12 (4×1×3) 🟢 | N/A | 48 (4×4×3) 🟡 | 80 (4×4×5) 🟠 | 48 (4×4×3) 🟡 |
| `products-and-prices` | N/A | N/A | N/A | N/A | N/A | 9 (3×1×3) 🟢 | 9 (3×1×3) 🟢 | 36 (3×4×3) 🟡 | 45 (3×3×5) 🟡 | 36 (3×4×3) 🟡 |
| `revenue-analytics` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 60 (4×5×3) 🟡 | 100 (4×5×5) 🔴 | 60 (4×5×3) 🟡 |
| `operation-catalog` | N/A | N/A | N/A | N/A | N/A | 6 (2×1×3) 🟢 | 6 (2×1×3) 🟢 | 24 (2×4×3) 🟢 | N/A | N/A |
| `documentation-and-planning` | 20 (1×4×5) 🟢 | N/A | 3 (1×1×3) 🟢 | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Blast radius (coverage · 1–5)

_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, 4 = essentially all, 5 = all + destructive) — coverage, not severity._

| asset \ tool | stripe_implementation_planner | send_stripe_mcp_feedback | search_stripe_documentation | get_stripe_account_info | create_refund | stripe_api_search | stripe_api_details | stripe_api_read | stripe_api_write | stripe_analytics |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `account-config` | N/A | N/A | N/A | 5 | N/A | N/A | N/A | 5 | 5 | N/A |
| `payment-instruments` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 | 5 | 4 |
| `customer-pii` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 | 5 | N/A |
| `charges-and-payments` | N/A | N/A | N/A | N/A | 3 | 1 | N/A | 4 | 4 | 4 |
| `refunds` | N/A | N/A | N/A | N/A | 3 | N/A | N/A | 4 | 4 | N/A |
| `subscriptions-and-billing` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 4 | 4 | 4 |
| `payouts-and-bank-routing` | N/A | N/A | N/A | 5 | N/A | N/A | N/A | 5 | 5 | N/A |
| `disputes-and-evidence` | N/A | N/A | N/A | N/A | N/A | 1 | N/A | 4 | 4 | 4 |
| `products-and-prices` | N/A | N/A | N/A | N/A | N/A | 1 | 1 | 4 | 3 | 4 |
| `revenue-analytics` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 5 | 5 | 5 |
| `operation-catalog` | N/A | N/A | N/A | N/A | N/A | 1 | 1 | 4 | N/A | N/A |
| `documentation-and-planning` | 4 | N/A | 1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Tool atomic operations

_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT the tool impact. It is a coarse lexical prior shown for reference; the domain-grounded **tool impact** (1–3) above supersedes it when they differ (e.g. a single-event delete is impact 2 there even though the DELETE verb is severity 5 here)._

| tool | atomic op | severity | all ops | source |
| --- | --- | --- | --- | --- |
| `stripe_implementation_planner` | **READ** | 2 (Low) | READ | verb-fallback |
| `send_stripe_mcp_feedback` | **BROADCAST** | 4 (High) | BROADCAST | verb-fallback |
| `search_stripe_documentation` | **SEARCH** | 2 (Low) | SEARCH | rules |
| `get_stripe_account_info` | **METADATA** | 1 (Low) | METADATA | rules |
| `create_refund` | **WRITE** | 3 (Medium) | CREATE, WRITE | rules |
| `stripe_api_search` | **SEARCH** | 2 (Low) | SEARCH | verb-fallback |
| `stripe_api_details` | **READ** | 2 (Low) | READ | verb-fallback |
| `stripe_api_read` | **READ** | 2 (Low) | READ | rules |
| `stripe_api_write` | **CREATE** | 3 (Medium) | CREATE | verb-fallback |
| `stripe_analytics` | **EXECUTE** | 5 (Critical) | DELETE, EXECUTE, OVERWRITE, SCHEMA_MODIFY, WRITE | rules |

## Tool input ranking (risk 1–5 + critical trigger)

| tool | input | risk | critical trigger | why |
| --- | --- | --- | --- | --- |
| `stripe_implementation_planner` | `message` | 4 | — | potentially contains arbitrary user input that could influen |
| `stripe_implementation_planner` | `guide_id` | 2 | — | merely identifies a specific guide |
| `stripe_implementation_planner` | `accept` | 1 | — | a simple boolean flag to finalize decisions, not inherently  |
| `send_stripe_mcp_feedback` | `quote` | 4 | >= 1000 chars | fully controlled input with potential for abuse through larg |
| `send_stripe_mcp_feedback` | `context` | 3 | — | potentially sensitive information that could be misused if n |
| `send_stripe_mcp_feedback` | `sentiment` | 2 | — | limited to predefined values |
| `send_stripe_mcp_feedback` | `source` | 2 | — | limited to predefined values (user or agent) |
| `send_stripe_mcp_feedback` | `tool_name` | 1 | — | names the target tool, limited impact |
| `search_stripe_documentation` | `search_only_api_ref` | 4 | — | can focus search on sensitive API details |
| `search_stripe_documentation` | `question` | 3 | — | potentially broadens search scope |
| `search_stripe_documentation` | `language` | 2 | — | limits but does not amplify risk |
| `create_refund` | `human_confirmation` | 5 | — | bypassing human confirmation could lead to unauthorized acti |
| `create_refund` | `amount` | 4 | amount >= 100000 | can lead to large financial loss if abused |
| `create_refund` | `reason` | 3 | — | potentially used for social engineering or logging abuse |
| `create_refund` | `payment_intent` | 2 | — | merely identifies the target |
| `stripe_api_search` | `intent` | 4 | — | can specify destructive actions |
| `stripe_api_search` | `resource` | 3 | — | defines the scope of operation |
| `stripe_api_search` | `limit` | 2 | >= 100 | controls result set size, potentially overwhelming server |
| `stripe_api_details` | `stripe_api_operation_id` | 2 | — | identifies the target operation, not inherently risky |
| `stripe_api_read` | `parameters` | 5 | unbounded (no LIMIT) | fully controlled payload with potential for bulk fan-out or  |
| `stripe_api_read` | `stripe_api_operation_id` | 2 | — | names the target operation |
| `stripe_api_write` | `parameters` | 5 | — | fully controllable payload with potential for bulk actions o |
| `stripe_api_write` | `stripe_api_operation_id` | 3 | — | can target any API operation |
| `stripe_api_write` | `human_confirmation` | 2 | — | indicates a need for manual approval, reducing immediate ris |
| `stripe_analytics` | `params` | 5 | — | fully controlled payload with potential for SQL injection or |
| `stripe_analytics` | `intent` | 3 | — | defines the scope of operation |
