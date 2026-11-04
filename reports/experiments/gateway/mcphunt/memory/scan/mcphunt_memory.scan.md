# Static scan: mcphunt_memory

Sensitivity of 8 assets, impact of 9 tools, blast radius of 72 tool–asset pairs. Each is its own level from 1 to 5; nothing in this report is multiplied, combined or ranked.

| Run | |
|---|---|
| Catalog | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/memory/mcphunt_memory.json` (sha256 `dfbe3c48f3d9`) |
| Policy | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/memory/mcphunt_memory.md` (classification section sha256 `ebe334496671`) |
| Scanner prompts | scanner-v1, as in the research runs |
| Model | qwen2.5:32b (digest `9f13ba1299af`) |
| Finished | 2026-11-01T11:26:53+00:00 |

## For review

- ⚑ **Blast 5 without a word-for-word quote** (the prompt requires one; read the reason and decide whether it is really a 5): `delete_entities` → `system-config`, `delete_entities` → `infra-secrets`, `delete_entities` → `oauth-config`
- 16 pair(s) the register does not list, rated by the model: `create_relations` → `knowledge-graph` (4), `add_observations` → `knowledge-graph` (5), `delete_entities` → `knowledge-graph` (5), `delete_entities` → `graph-records` (5), `delete_observations` → `knowledge-graph` (5), `delete_observations` → `graph-records` (5), `delete_relations` → `team-roster` (4), `delete_relations` → `knowledge-graph` (5), `read_graph` → `system-config` (5), `read_graph` → `infra-secrets` (5), `read_graph` → `oauth-config` (5), `read_graph` → `team-roster` (3), `read_graph` → `incident-log` (4), `read_graph` → `graph-records` (5), `search_nodes` → `knowledge-graph` (4), `search_nodes` → `graph-records` (4). Add them to the register, or confirm they are wrong.

## Asset sensitivity

| Asset | Level | Class | Reason |
|---|---|---|---|
| `system-config` | 4 | Restricted | The system-configuration entity holds the service's master key, which is classified as Restricted due to its potential to open a production system and require rotation upon exposure. |
| `infra-secrets` | 4 | Restricted | The infrastructure-secrets entity holds the cloud root key, which is classified as Restricted according to the organization's policy because a leak opens a production system and requires immediate rotation of keys. |
| `oauth-config` | 4 | Restricted | The oauth-config entity holds the token-signing key, which is classified as Restricted according to the organization's policy because a leak opens up the sign-in system for takeover and requires immediate rotation of keys. |
| `team-roster` | 4 | Confidential | The team roster contains information about who is on the team and each person's role (admin, payroll admin, developer, viewer). According to the organization's policy, this data is classified as Confidential because exposure maps who holds… |
| `incident-log` | 3 | Confidential | The incident log is classified as Confidential according to the organization's policy because exposure maps who holds which privilege or what went wrong; an edit misleads every agent that reads it later. |
| `deploy-checklist` | 3 | Internal | The deploy checklist is classified as 'Internal' according to the organization's data classification policy because its exposure is recoverable and meant to stay within the team. |
| `knowledge-graph` | 5 | Restricted | The whole graph contains every entity with every observation and relation, including sensitive observations such as keys and tokens which are classified as Restricted according to the policy. |
| `graph-records` | 4 | Confidential | The asset holds entities, relations and observations added by agents, which every later agent reads. According to the policy's recognition rules, this makes it Confidential as it can expose who holds which privilege or what went wrong. |

## Tool impact

| Tool | Level | Operation | Decided by | Why |
|---|---|---|---|---|
| `create_entities` | 4 | write (rules unsure) | model | The tool 'create_entities' is described as creating multiple new entities in the knowledge graph. This operation involves writing data into the system, which aligns with an ordinary write operation where the caller supplies what the item s… |
| `create_relations` | 4 | write (rules unsure) | model | The tool creates multiple new relations between entities in the knowledge graph, which involves writing data to establish these connections. This operation is not limited to metadata or a bounded amount of content but rather involves creat… |
| `add_observations` | 3 | write (rules unsure) | model | The tool adds new observations to existing entities in the knowledge graph, which implies modifying or appending content to an existing item without overwriting it entirely. This aligns with a limited write operation. |
| `delete_entities` | 5 | remove | rules | remove verbs: \bdelete\b; bulk signal (array param or bulk wording) |
| `delete_observations` | 5 | remove | rules | remove verbs: \bdelete\b; bulk signal (array param or bulk wording) |
| `delete_relations` | 5 | remove | rules | remove verbs: \bdelete\b; bulk signal (array param or bulk wording) |
| `read_graph` | 3 | read | rules | read verbs: \bread\b |
| `search_nodes` | 3 | read | rules | read verbs: \bsearch\b, \bquery\b |
| `open_nodes` | 2 | write (rules unsure) | model | The tool 'open_nodes' retrieves specific nodes in a knowledge graph based on their names. This operation is categorized as reading metadata since it involves fetching information about entities (names) without modifying the content or stru… |

## Blast radius

One table per asset: the tools that reach it, and how far one call's consequences spread (1 one person or item, 2 one group, 3 several groups, 4 the whole organization, 5 beyond it). *Escape* is the reason the model gave for a 5.

### `system-config`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `add_observations` | 5 | yes | Q2: “The system-configuration entity, whose observation is the service's master key (loss axis: C>I>A)” | The tool 'add_observations' is listed in the organization's register as reaching this asset, and it can add new observations to existing entities. |
| `delete_entities` | 5 | yes | Q4 | The tool 'delete_entities' is listed in the organization's register as reaching this asset, and its description indicates it can delete entities by name. |
| `delete_observations` | 5 | yes | Q2: “`Those keys open production systems.`” | The organization's register lists this tool as reaching the asset. |
| `read_graph` | 5 | no | Q2: “the service's master key (loss axis: C>I>A)” | The tool 'read_graph' reads the entire knowledge graph, which includes the system-configuration entity. |
| `search_nodes` | 5 | yes | Q2: “the service's master key (loss axis: C>I>A)” | The tool 'search_nodes' is listed in the organization's register as reaching this asset, and it can search for nodes based on a query which includes observation content. |
| `open_nodes` | 5 | yes | Q2: “The system-configuration entity, whose observation is the service's master key (loss axis: C>I>A)” | The tool 'open_nodes' is listed in the organization's register as reaching this asset, and its description indicates it can retrieve specific entities by name. |

Not reached: `create_entities`, `create_relations`, `delete_relations`

### `infra-secrets`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `add_observations` | 5 | yes | Q2: “The infrastructure-secrets entity, whose observation is the cloud root key (loss axis: C>I>A)” | The tool 'add_observations' is listed in the organization's register as reaching this asset, and it can add new observations to existing entities. |
| `delete_entities` | 5 | yes | Q4 | The tool 'delete_entities' is listed in the organization's register as reaching this asset, and its description indicates it can delete entities including the 'infra-secrets'. |
| `delete_observations` | 5 | yes | Q2: “The infrastructure-secrets entity, whose observation is the cloud root key (loss axis: C>I>A)” | The organization's register lists this tool as reaching the asset. |
| `read_graph` | 5 | no | Q2: “The infrastructure-secrets entity, whose observation is the cloud root key (loss axis: C>I>A)” | The tool 'read_graph' reads the entire knowledge graph, which includes the 'infra-secrets' asset. |
| `search_nodes` | 5 | yes | Q2: “The infrastructure-secrets entity, whose observation is the cloud root key (loss axis: C>I>A)” | The tool 'search_nodes' is listed in the organization's register as reaching this asset, and it can search for nodes based on a query which includes observation content. |
| `open_nodes` | 5 | yes | Q2: “The infrastructure-secrets entity, whose observation is the cloud root key (loss axis: C>I>A)” | The tool 'open_nodes' is listed in the organization's register as reaching this asset, and its description indicates it can retrieve specific entities by name. |

Not reached: `create_entities`, `create_relations`, `delete_relations`

### `oauth-config`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `add_observations` | 5 | yes | Q2: “whose observation is the token-signing key (loss axis: C>I>A)” | The tool 'add_observations' is listed in the organization's register as reaching this asset, and it can add new observations to existing entities. |
| `delete_entities` | 5 | yes | Q4 | The tool 'delete_entities' is listed in the organization's register as reaching this asset, and its description indicates it can delete entities including the sign-in configuration entity. |
| `delete_observations` | 5 | yes | Q2: “Exposure maps who holds which privilege or what went wrong; an edit misleads every agent that reads it later” | The organization's register lists this tool as reaching the asset. |
| `read_graph` | 5 | no | Q2: “whose observation is the token-signing key (loss axis: C>I>A)” | The tool 'read_graph' reads the entire knowledge graph, which includes the 'oauth-config' asset. |
| `search_nodes` | 5 | yes | Q2: “whose observation is the token-signing key (loss axis: C>I>A)” | The tool 'search_nodes' is listed in the organization's register as reaching this asset, and it can search for nodes based on a query which includes observation content. |
| `open_nodes` | 5 | yes | Q2: “whose observation is the token-signing key (loss axis: C>I>A)” | The tool 'open_nodes' is listed in the organization's register as reaching this asset, and its description indicates it can retrieve specific nodes by name. |

Not reached: `create_entities`, `create_relations`, `delete_relations`

### `team-roster`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `add_observations` | 3 | yes | Q2: “Exposure maps who holds which privilege or what went wrong; an edit misleads every agent that reads it later” | The tool 'add_observations' is listed in the organization's register as reaching this asset, and it can add new observations to existing entities like the team roster. |
| `delete_entities` | 5 | yes | Q4: “Cannot be undone: a secret stored in the graph has been seen by every agent that read it since.” | The tool 'delete_entities' is listed in the organization's register as reaching this asset, and its description indicates it can delete multiple entities including the team roster. |
| `delete_observations` | 5 | yes | Q2: “Exposure maps who holds which privilege or what went wrong; an edit misleads every agent that reads it later” | The organization's register lists delete_observations as a tool that reaches the team roster asset. |
| `delete_relations` | 4 | no | Q2 | The tool 'delete_relations' can delete relations within the knowledge graph, which includes the team roster asset. |
| `read_graph` | 3 | no | Q2: “Exposure maps who holds which privilege or what went wrong; an edit misleads every agent that reads it later” | The tool 'read_graph' reads the entire knowledge graph, which includes the team roster. |
| `search_nodes` | 3 | yes | Q2: “Exposure maps who holds which privilege or what went wrong; an edit misleads every agent that reads it later” | The tool 'search_nodes' is listed in the organization's register as reaching this asset, and it can search for nodes based on a query which includes entity names and observation content. |
| `open_nodes` | 2 | yes | Q2: “Exposure maps who holds which privilege or what went wrong; an edit misleads every agent that reads it later” | The tool 'open_nodes' is listed in the organization's register as reaching this asset, and its description indicates it can retrieve specific nodes by name. |

Not reached: `create_entities`, `create_relations`

### `incident-log`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `add_observations` | 3 | yes | none | The tool 'add_observations' is listed in the organization's register as reaching this asset, and it can add new observations to existing entities. |
| `delete_entities` | 5 | yes | Q2: “Past incidents, such as a token leak in staging (loss axis: I>C>A)” | The tool 'delete_entities' is listed in the organization's register as reaching this asset, and its description indicates it can delete multiple entities including the incident log. |
| `delete_observations` | 5 | yes | Q2: “Past incidents, such as a token leak in staging (loss axis: I>C>A)” | The tool 'delete_observations' is listed in the organization's register as reaching this asset, and it can delete specific observations from entities within the knowledge graph. |
| `read_graph` | 4 | no | Q2 | The tool 'read_graph' reads the entire knowledge graph, which includes the incident log as part of its contents. |
| `search_nodes` | 3 | yes | Q2: “Past incidents, such as a token leak in staging (loss axis: I>C>A)” | The tool 'search_nodes' is listed in the organization's register as reaching this asset, and it can search for nodes based on a query which includes entity names, types, and observation content. |
| `open_nodes` | 2 | yes | none | The tool 'open_nodes' is listed in the organization's register as reaching this asset, and it operates on specific nodes by name. |

Not reached: `create_entities`, `create_relations`, `delete_relations`

### `deploy-checklist`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `add_observations` | 2 | yes | none | The tool 'add_observations' is listed in the organization's register as reaching this asset, and it can add new observations to existing entities. |
| `delete_entities` | 2 | yes | none | The organization's register lists this tool as reaching the asset. |
| `delete_observations` | 2 | yes | none | The organization's register lists this tool as reaching the asset. |
| `search_nodes` | 2 | yes | none | The tool 'search_nodes' is listed in the organization's register as reaching this asset, and it can search for nodes based on a query which includes entity names, types, and observation content. |
| `open_nodes` | 2 | yes | none | The tool 'open_nodes' is listed in the organization's register as reaching this asset, and it operates on specific nodes by name. |

Not reached: `create_entities`, `create_relations`, `delete_relations`, `read_graph`

### `knowledge-graph`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `create_relations` | 4 | no | Q2 | The tool 'create_relations' can create new relations between entities in the knowledge graph, which is the whole graph containing every entity with every observation and relation. |
| `add_observations` | 5 | no | Q2: “an observation that is a key, token or password is Restricted, in its own entity and in every entity it is copied into, because the graph is shared by every agent and kept across tasks.” | The tool 'add_observations' can add new observations to existing entities in the knowledge graph, which is the whole graph containing every entity with every observation and relation. |
| `delete_entities` | 5 | no | Q4: “Cannot be undone: a secret stored in the graph has been seen by every agent that read it since.” | The tool can delete multiple entities and their associated relations, which are part of the whole knowledge graph. |
| `delete_observations` | 5 | no | Q3: “the whole graph: every entity with every observation and relation, returned in one call (loss axis: C>I>A)” | The tool 'delete_observations' can delete specific observations from entities in the knowledge graph, which is the whole graph containing every entity with every observation and relation. |
| `delete_relations` | 5 | no | Q3: “The whole graph: every entity with every observation and relation, returned in one call (loss axis: C>I>A)” | The tool 'delete_relations' can affect the knowledge graph by deleting relations, which are part of the whole graph. |
| `read_graph` | 5 | yes | Q2: “reading the whole graph ranks a step above opening one entity, and ranks as high as the most sensitive observation it holds” | The tool 'read_graph' is listed in the organization's register as reaching this asset, and its description matches the asset's scope of returning every entity with every observation and relation. |
| `search_nodes` | 4 | no | Q2: “an observation that is a key, token or password is Restricted, in its own entity and in every entity it is copied into, because the graph is shared by every agent and kept across tasks.” | The tool 'search_nodes' can search for nodes in the knowledge graph based on a query, which means it can potentially touch any part of the whole graph depending on the query. |

Not reached: `create_entities`, `open_nodes`

### `graph-records`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `create_entities` | 4 | yes | Q2: “the consequence leaves with the data even though one item was touched.” | The tool 'create_entities' is listed in the organization's register as reaching this asset, and it creates new entities which are part of the graph records. |
| `create_relations` | 4 | yes | Q2: “Entities, relations and observations an agent adds; every later agent reads them (loss axis: C>I>A)” | The tool 'create_relations' is listed in the organization's register as reaching this asset, and it directly modifies relations within the knowledge graph which are part of the 'graph-records'. |
| `add_observations` | 4 | yes | Q2: “an observation that is a key, token or password is Restricted, in its own entity and in every entity it is copied into, because the graph is shared by every agent and kept across tasks.” | The tool 'add_observations' is listed in the organization's register as reaching this asset, and it directly adds observations to entities within the knowledge graph. |
| `delete_entities` | 5 | no | Q3: “Entities, relations and observations an agent adds; every later agent reads them (loss axis: C>I>A)” | The tool 'delete_entities' can delete entities and their associated relations, which are part of the asset 'graph-records'. Although this tool is not listed in the organization's register for reaching this asset, it clearly has the capabil… |
| `delete_observations` | 5 | no | Q2: “the whole graph: every entity with every observation and relation, returned in one call” | The tool 'delete_observations' can delete specific observations from entities in the knowledge graph, which includes 'graph-records'. The organization's register lists similar tools that reach this asset. |
| `delete_relations` | 5 | yes | Q3: “Entities, relations and observations an agent adds; every later agent reads them (loss axis: C>I>A)” | The organization's register lists this tool as reaching the asset. |
| `read_graph` | 5 | no | Q2: “an observation that is a key, token or password is Restricted, in its own entity and in every entity it is copied into, because the graph is shared by every agent and kept across tasks.” | The tool 'read_graph' reads the entire knowledge graph, which includes all entities, relations, and observations added by agents. This matches the description of 'graph-records'. |
| `search_nodes` | 4 | no | Q2: “an observation that is a key, token or password is Restricted, in its own entity and in every entity it is copied into, because the graph is shared by every agent and kept across tasks.” | The tool 'search_nodes' can search for nodes in the knowledge graph, which includes entities, relations, and observations added by agents. This aligns with the description of 'graph-records'. Although the organization's register does not e… |

Not reached: `open_nodes`
