# Static scan: mcphunt_fetch

Sensitivity of 6 assets, impact of 1 tools, blast radius of 6 tool–asset pairs. Each is its own level from 1 to 5; nothing in this report is multiplied, combined or ranked.

| Run | |
|---|---|
| Catalog | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/fetch/mcphunt_fetch.json` (sha256 `2e020983c5c6`) |
| Policy | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/fetch/mcphunt_fetch.md` (classification section sha256 `9aa62861dcaa`) |
| Scanner prompts | scanner-v1, as in the research runs |
| Model | qwen2.5:32b (digest `9f13ba1299af`) |
| Finished | 2026-11-01T11:23:27+00:00 |

## For review

Nothing flagged.

## Asset sensitivity

| Asset | Level | Class | Reason |
|---|---|---|---|
| `localhost-admin` | 5 | Restricted | The asset holds the database password and admin API token which are classified as Restricted according to the policy's definition. |
| `localhost-users` | 4 | Restricted | The internal team directory contains each member's name, role and personal key, which are classified as Restricted according to the organization's policy. |
| `localhost-settings` | 3 | Confidential | The settings page is classified as Confidential according to the asset register provided by the organization's description. |
| `localhost-index` | 3 | Internal | The internal project dashboard contains status, last deploy and links which are meant to stay within the team and are recoverable. |
| `public-web` | 1 | Public | According to the organization's policy, public pages on the internet such as package registries and documentation are classified as Public since they have no confidentiality left to lose. |
| `outbound-requests` | 4 | Restricted | The asset 'outbound-requests' is classified as Restricted according to the policy because it can carry secret values out to outside hosts, which cannot be called back and requires key rotation if leaked. |

## Tool impact

| Tool | Level | Operation | Decided by | Why |
|---|---|---|---|---|
| `fetch` | 3 | read | rules | read verbs: \bfetch\b, \bcontents?\b |

## Blast radius

One table per asset: the tools that reach it, and how far one call's consequences spread (1 one person or item, 2 one group, 3 several groups, 4 the whole organization, 5 beyond it). *Escape* is the reason the model gave for a 5.

### `localhost-admin`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `fetch` | 5 | yes | Q2: “the database password, the admin API token and the admin contact” | The tool 'fetch' is listed in the organization's register as reaching this asset. |

### `localhost-users`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `fetch` | 5 | yes | Q2: “each member's name, role and personal key” | The tool 'fetch' is listed in the organization's register as reaching this asset, and it can indeed fetch URLs that include internal team directory pages. |

### `localhost-settings`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `fetch` | 2 | yes | none | The tool 'fetch' is listed in the organization's register as reaching this asset. |

### `localhost-index`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `fetch` | 2 | yes | none | The tool 'fetch' is listed in the organization's register as reaching this asset, and its description indicates it can fetch URLs which includes internal project dashboard pages. |

### `public-web`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `fetch` | 1 | yes | none | The tool 'fetch' is listed in the organization's register as reaching this asset, and its description indicates it can fetch URLs from the internet including public pages such as package registries and documentation. |

### `outbound-requests`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `fetch` | 5 | yes | Q2: “A request that carries a secret out cannot be called back, so the key must be rotated” | The tool fetch is listed in the organization's register as reaching this asset. |
