# MCP Server Catalog

A domain-categorized catalog of notable Model Context Protocol (MCP) servers.
Each row lists the server name, a sample of its tools, the upstream link,
and an evidence tag explaining why the server is in the catalog.

## How to read this catalog

- **Asset domain (section heading)** — the class of asset the server exposes
  to agents (filesystem, source code, database, etc.). This is the catalog's
  primary axis.
- **Tools** — sample of tool names registered by the server. Long tool sets
  are truncated with `…`. Where the upstream README does not enumerate tools
  cleanly, the cell shows `(not enumerated)`.
- **Evidence** — why this server appears in the catalog:
  - `official-reference` — currently maintained reference server in
    `modelcontextprotocol/servers`
  - `official-archived` — moved to `modelcontextprotocol/servers-archived`
  - `official-vendor` — first-party server published by the vendor
    (Microsoft, Cloudflare, Stripe, HashiCorp, etc.)
  - `paper-cited` — appears in MCP security papers tracked in
    `docs/project/annotated-bibliography-mcp-security.md`
  - `community-popular` — broadly referenced community server

Operation-class colouring of tools (read/write/execute/search/admin/…) lives
in [`domain-graph.md`](domain-graph.md) and reuses the taxonomy from
[`../standards/atomic-op-classification.md`](../standards/atomic-op-classification.md).

---

## 1. Local filesystem

Servers that expose the host filesystem to an agent.

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `filesystem` (official) | `read_text_file`, `read_media_file`, `read_multiple_files`, `write_file`, `edit_file`, `list_directory`, `directory_tree`, `search_files`, `move_file`, `get_file_info`, `create_directory`, `list_allowed_directories` | [servers-archived/src/filesystem](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/filesystem) | official-archived, paper-cited |
| `mark3labs/mcp-filesystem-server` | (not enumerated) | [mark3labs/mcp-filesystem-server](https://github.com/mark3labs/mcp-filesystem-server) | community-popular |
| `box/mcp-server-box-remote` | (not enumerated) | [box/mcp-server-box-remote](https://github.com/box/mcp-server-box-remote) | official-vendor |
| `microsoft/markitdown` | (not enumerated) | [microsoft/markitdown](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp) | official-vendor |

## 2. Source code & version control

Servers that expose Git repositories, code-hosting platforms, or developer
workflow systems.

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `git` (official reference) | `git_log`, `git_status`, `git_diff`, `git_show`, `git_search`, … | [servers/src/git](https://github.com/modelcontextprotocol/servers/blob/main/src/git) | official-reference |
| `github` (archived) | `get_file_contents`, `search_code`, `create_or_update_file`, `push_files`, `create_pull_request`, `merge_pull_request`, `fork_repository`, `actions_run_trigger`, … | [servers-archived/src/github](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/github) | official-archived, paper-cited |
| `github/github-mcp-server` | `get_me`, `list_issues`, `create_pull_request`, `merge_pull_request`, `search_code`, `get_file_contents`, `create_or_update_file`, `push_files`, `list_code_scanning_alerts`, `list_secret_scanning_alerts`, `actions_run_trigger`, … (~80+) | [github/github-mcp-server](https://github.com/github/github-mcp-server) | official-vendor |
| `gitlab` (archived) | (not enumerated) | [servers-archived/src/gitlab](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/gitlab) | official-archived |
| `gitea/gitea-mcp` | (not enumerated) | [gitea/gitea-mcp](https://gitea.com/gitea/gitea-mcp) | official-vendor |
| `Tiberriver256/mcp-server-azure-devops` | (not enumerated) | [Tiberriver256/mcp-server-azure-devops](https://github.com/Tiberriver256/mcp-server-azure-devops) | community-popular |
| `aashari/mcp-server-atlassian-bitbucket` | (not enumerated) | [aashari/.../bitbucket](https://github.com/aashari/mcp-server-atlassian-bitbucket) | community-popular |

## 3. Databases (SQL, NoSQL, vector, graph, streaming)

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `sqlite` (archived) | `read_query`, `write_query`, `create_table`, `list_tables`, `describe_table`, `append_insight` | [servers-archived/src/sqlite](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/sqlite) | official-archived, paper-cited |
| `postgres` (archived) | (not enumerated) | [servers-archived/src/postgres](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/postgres) | official-archived, paper-cited |
| `redis` (archived) | (not enumerated) | [servers-archived/src/redis](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/redis) | official-archived |
| `redis/mcp-redis` | `string_*`, `hash_*`, `list_*`, `set_*`, `sorted_set_*`, `pub_sub_*`, `streams_*`, `JSON_*`, `query_engine`, `server_management` | [redis/mcp-redis](https://github.com/redis/mcp-redis) | official-vendor |
| `supabase-community/supabase-mcp` | `list_projects`, `execute_sql`, `apply_migration`, `list_tables`, `get_logs`, `deploy_edge_function`, `list_storage_buckets`, … | [supabase-community/supabase-mcp](https://github.com/supabase-community/supabase-mcp) | official-vendor |
| `neondatabase/mcp-server-neon` | `list_projects`, `create_branch`, `run_sql`, `run_sql_transaction`, `describe_table_schema`, `prepare_database_migration`, `list_slow_queries`, `explain_sql_statement`, … | [neondatabase/mcp-server-neon](https://github.com/neondatabase/mcp-server-neon) | official-vendor |
| `planetscale/cli` (MCP) | (not enumerated) | [planetscale/cli](https://github.com/planetscale/cli) | official-vendor |
| `prisma/mcp` | (not enumerated) | [prisma/mcp](https://github.com/prisma/mcp) | official-vendor |
| `crystaldba/postgres-mcp` | (not enumerated) | [crystaldba/postgres-mcp](https://github.com/crystaldba/postgres-mcp) | community-popular |
| `ClickHouse/mcp-clickhouse` | (not enumerated) | [ClickHouse/mcp-clickhouse](https://github.com/ClickHouse/mcp-clickhouse) | official-vendor |
| `Snowflake-Labs/mcp` | (not enumerated) | [Snowflake-Labs/mcp](https://github.com/Snowflake-Labs/mcp) | official-vendor |
| `InfluxData/influxdb3_mcp_server` | (not enumerated) | [influxdata/influxdb3_mcp_server](https://github.com/influxdata/influxdb3_mcp_server) | official-vendor |
| `chroma-core/chroma-mcp` | (not enumerated) | [chroma-core/chroma-mcp](https://github.com/chroma-core/chroma-mcp) | official-vendor |
| `qdrant/mcp-server-qdrant` | (not enumerated) | [qdrant/mcp-server-qdrant](https://github.com/qdrant/mcp-server-qdrant) | official-vendor |
| `weaviate/mcp-server-weaviate` | (not enumerated) | [weaviate/mcp-server-weaviate](https://github.com/weaviate/mcp-server-weaviate) | official-vendor |
| `zilliztech/mcp-server-milvus` | (not enumerated) | [zilliztech/mcp-server-milvus](https://github.com/zilliztech/mcp-server-milvus) | official-vendor |
| `sirmews/mcp-pinecone` | (not enumerated) | [sirmews/mcp-pinecone](https://github.com/sirmews/mcp-pinecone) | community-popular |
| `neo4j-contrib/mcp-neo4j` | (not enumerated) | [neo4j-contrib/mcp-neo4j](https://github.com/neo4j-contrib/mcp-neo4j) | official-vendor |
| `memgraph/mcp-memgraph` | (not enumerated) | [memgraph/ai-toolkit/.../mcp-memgraph](https://github.com/memgraph/ai-toolkit/tree/main/integrations/mcp-memgraph) | official-vendor |
| `Couchbase-Ecosystem/mcp-server-couchbase` | (not enumerated) | [Couchbase-Ecosystem/mcp-server-couchbase](https://github.com/Couchbase-Ecosystem/mcp-server-couchbase) | official-vendor |
| `Aiven-Open/mcp-aiven` | (not enumerated) | [Aiven-Open/mcp-aiven](https://github.com/Aiven-Open/mcp-aiven) | official-vendor |
| `confluentinc/mcp-confluent` | (not enumerated) | [confluentinc/mcp-confluent](https://github.com/confluentinc/mcp-confluent) | official-vendor |
| `kiliczsh/mcp-mongo-server` | (not enumerated) | [kiliczsh/mcp-mongo-server](https://github.com/kiliczsh/mcp-mongo-server) | community-popular |
| `googleapis/genai-toolbox` | (not enumerated) | [googleapis/genai-toolbox](https://github.com/googleapis/genai-toolbox) | official-vendor |
| `domdomegg/airtable-mcp-server` | (not enumerated) | [domdomegg/airtable-mcp-server](https://github.com/domdomegg/airtable-mcp-server) | community-popular |
| `dbt-labs/dbt-mcp` | `execute_sql`, `text_to_sql`, `query_metrics`, `list_metrics`, `get_dimensions`, `get_lineage`, `get_model_details`, `build`, `run`, `test`, `trigger_job_run`, … (~50) | [dbt-labs/dbt-mcp](https://github.com/dbt-labs/dbt-mcp) | official-vendor |
| `JordiNeil/mcp-databricks-server` | (not enumerated) | [JordiNeil/mcp-databricks-server](https://github.com/JordiNeil/mcp-databricks-server) | community-popular |
| `keboola/keboola-mcp-server` | (not enumerated) | [keboola/keboola-mcp-server](https://github.com/keboola/keboola-mcp-server) | official-vendor |

## 4. Messaging & communication

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `slack` (archived) | `slack_post_message`, `slack_reply_to_thread`, `slack_get_users`, `slack_get_channel_history`, `slack_get_thread_replies`, `slack_get_user_profile`, `slack_list_channels`, `slack_add_reaction` | [servers-archived/src/slack](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/slack) | official-archived, paper-cited |
| `korotovsky/slack-mcp-server` | (not enumerated) | [korotovsky/slack-mcp-server](https://github.com/korotovsky/slack-mcp-server) | community-popular |
| `InditexTech/mcp-teams-server` | (not enumerated) | [InditexTech/mcp-teams-server](https://github.com/InditexTech/mcp-teams-server) | community-popular |
| `softeria/ms-365-mcp-server` | (not enumerated) | [softeria/ms-365-mcp-server](https://github.com/softeria/ms-365-mcp-server) | community-popular |
| `line/line-bot-mcp-server` | (not enumerated) | [line/line-bot-mcp-server](https://github.com/line/line-bot-mcp-server) | official-vendor |
| `infobip/mcp` | (not enumerated) | [infobip/mcp](https://github.com/infobip/mcp) | official-vendor |
| `chaindead/telegram-mcp` | (not enumerated) | [chaindead/telegram-mcp](https://github.com/chaindead/telegram-mcp) | community-popular |
| `lharries/whatsapp-mcp` | (not enumerated) | [lharries/whatsapp-mcp](https://github.com/lharries/whatsapp-mcp) | community-popular |
| `SaseQ/discord-mcp` | (not enumerated) | [SaseQ/discord-mcp](https://github.com/SaseQ/discord-mcp) | community-popular |
| `agentmail-toolkit/mcp` | (not enumerated) | [agentmail-to/agentmail-toolkit](https://github.com/agentmail-to/agentmail-toolkit/tree/main/mcp) | community-popular |
| `trycourier/courier-mcp` | (not enumerated) | [trycourier/courier-mcp](https://github.com/trycourier/courier-mcp) | official-vendor |
| `discourse/discourse-mcp` | (not enumerated) | [discourse/discourse-mcp](https://github.com/discourse/discourse-mcp) | official-vendor |

## 5. Productivity, docs & calendar

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `gdrive` (archived) | `gdrive_search`, `gdrive_read_file`, `gdrive_list_files`, `gdrive_update_file`, `gdrive_create_file`, `gdrive_copy_file`, `gdrive_export_file`, `gdrive_delete_file`, `gdrive_move_file`, `gdrive_create_folder`, `share_file` | [servers-archived/src/gdrive](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/gdrive) | official-archived, paper-cited |
| `isaacphi/mcp-gdrive` | (not enumerated) | [isaacphi/mcp-gdrive](https://github.com/isaacphi/mcp-gdrive) | community-popular |
| `makenotion/notion-mcp-server` | `search-pages`, `retrieve-page`, `create-page`, `update-page`, `query-data-source`, `retrieve-a-database`, `append-block`, `retrieve-block-children`, `update-block`, `delete-block`, `create-comment`, … | [makenotion/notion-mcp-server](https://github.com/makenotion/notion-mcp-server) | official-vendor |
| `aashari/mcp-server-atlassian-jira` | (not enumerated) | [aashari/.../jira](https://github.com/aashari/mcp-server-atlassian-jira) | community-popular |
| `aashari/mcp-server-atlassian-confluence` | (not enumerated) | [aashari/.../confluence](https://github.com/aashari/mcp-server-atlassian-confluence) | community-popular |
| `taylorwilsdon/google_workspace_mcp` | (not enumerated) | [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) | community-popular |
| `MarkusPfundstein/mcp-gsuite` | (not enumerated) | [MarkusPfundstein/mcp-gsuite](https://github.com/MarkusPfundstein/mcp-gsuite) | community-popular |
| `zcaceres/gtasks-mcp` | (not enumerated) | [zcaceres/gtasks-mcp](https://github.com/zcaceres/gtasks-mcp) | community-popular |
| `takumi0706/google-calendar-mcp` | (not enumerated) | [takumi0706/google-calendar-mcp](https://github.com/takumi0706/google-calendar-mcp) | community-popular |
| `teamwork/mcp` | (not enumerated) | [teamwork/mcp](https://github.com/teamwork/mcp) | official-vendor |

## 6. Browser & web automation

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `fetch` (official reference) | `fetch` | [servers/src/fetch](https://github.com/modelcontextprotocol/servers/blob/main/src/fetch) | official-reference |
| `puppeteer` (archived) | (not enumerated) | [servers-archived/src/puppeteer](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/puppeteer) | official-archived, paper-cited |
| `microsoft/playwright-mcp` | `browser_navigate`, `browser_click`, `browser_fill_form`, `browser_type`, `browser_snapshot`, `browser_take_screenshot`, `browser_evaluate`, `browser_press_key`, `browser_wait_for`, `browser_file_upload`, `browser_network_requests`, `browser_console_messages`, `browser_pdf_save`, `browser_cookie_get`, `browser_cookie_set`, … (~40+) | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | official-vendor |
| `browserbase/mcp-server-browserbase` | (not enumerated) | [browserbase/mcp-server-browserbase](https://github.com/browserbase/mcp-server-browserbase) | official-vendor |
| `automatalabs/mcp-server-playwright` | (not enumerated) | [automatalabs/mcp-server-playwright](https://github.com/Automata-Labs-team/MCP-Server-Playwright) | community-popular |
| `co-browser/browser-use-mcp-server` | (not enumerated) | [co-browser/browser-use-mcp-server](https://github.com/co-browser/browser-use-mcp-server) | community-popular |
| `browsermcp/mcp` | (not enumerated) | [browsermcp/mcp](https://github.com/browsermcp/mcp) | community-popular |

## 7. Cloud infrastructure & IaC

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `awslabs/mcp` | (multi-server suite) | [awslabs/mcp](https://github.com/awslabs/mcp) | official-vendor |
| `aws-kb-retrieval` (archived) | (not enumerated) | [servers-archived/src/aws-kb-retrieval-server](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/aws-kb-retrieval-server) | official-archived |
| `cloudflare/mcp-server-cloudflare` | Workers, KV, R2, D1, Observability, AI Gateway, Browser Rendering, Logpush, DNS Analytics, DEX, CASB, GraphQL | [cloudflare/mcp-server-cloudflare](https://github.com/cloudflare/mcp-server-cloudflare) | official-vendor |
| `hashicorp/terraform-mcp-server` | `search_providers`, `get_provider_details`, `list_workspaces`, … | [hashicorp/terraform-mcp-server](https://github.com/hashicorp/terraform-mcp-server) | official-vendor |
| `pulumi/mcp-server` | (not enumerated) | [pulumi/mcp-server](https://github.com/pulumi/mcp-server) | official-vendor |
| `aliyun/alibaba-cloud-ops-mcp-server` | (not enumerated) | [aliyun/alibaba-cloud-ops-mcp-server](https://github.com/aliyun/alibaba-cloud-ops-mcp-server) | official-vendor |
| `alexei-led/aws-mcp-server` | (not enumerated) | [alexei-led/aws-mcp-server](https://github.com/alexei-led/aws-mcp-server) | community-popular |
| `alexei-led/k8s-mcp-server` | (not enumerated) | [alexei-led/k8s-mcp-server](https://github.com/alexei-led/k8s-mcp-server) | community-popular |
| `flux159/mcp-server-kubernetes` | (not enumerated) | [Flux159/mcp-server-kubernetes](https://github.com/Flux159/mcp-server-kubernetes) | community-popular |
| `manusa/kubernetes-mcp-server` | (not enumerated) | [manusa/kubernetes-mcp-server](https://github.com/manusa/kubernetes-mcp-server) | community-popular |
| `azure-cli-mcp` | (not enumerated) | [jdubois/azure-cli-mcp](https://github.com/jdubois/azure-cli-mcp) | community-popular |
| `localstack/localstack-mcp-server` | (not enumerated) | [localstack/localstack-mcp-server](https://github.com/localstack/localstack-mcp-server) | official-vendor |
| `portainer/portainer-mcp` | (not enumerated) | [portainer/portainer-mcp](https://github.com/portainer/portainer-mcp) | official-vendor |

## 8. Search & data extraction

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `brave-search` (archived) | `brave_web_search`, `brave_local_search` | [servers-archived/src/brave-search](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/brave-search) | official-archived |
| `brave/brave-search-mcp-server` | `brave_web_search`, `brave_local_search`, `brave_video_search`, `brave_image_search`, `brave_news_search`, `brave_summarizer`, `brave_place_search`, `brave_llm_context` | [brave/brave-search-mcp-server](https://github.com/brave/brave-search-mcp-server) | official-vendor |
| `exa-labs/exa-mcp-server` | `web_search_exa`, `web_fetch_exa`, `web_search_advanced_exa`, `get_code_context_exa`, `company_research_exa`, `crawling_exa`, `people_search_exa`, `linkedin_search_exa`, `deep_researcher_start`, … | [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server) | official-vendor |
| `kshern/mcp-tavily` | `search`, `extract`, `map`, `crawl` | [kshern/mcp-tavily](https://github.com/kshern/mcp-tavily) | community-popular |
| `mendableai/firecrawl-mcp-server` | `firecrawl_scrape`, `firecrawl_batch_scrape`, `firecrawl_map`, `firecrawl_search`, `firecrawl_crawl`, `firecrawl_extract`, `firecrawl_agent`, `firecrawl_interact`, … | [mendableai/firecrawl-mcp-server](https://github.com/mendableai/firecrawl-mcp-server) | official-vendor |
| `apify/actors-mcp-server` | (3000+ Actors) | [apify/actors-mcp-server](https://github.com/apify/actors-mcp-server) | official-vendor |
| `luminati-io/brightdata-mcp` | (not enumerated) | [luminati-io/brightdata-mcp](https://github.com/luminati-io/brightdata-mcp) | official-vendor |
| `kagisearch/kagimcp` | (not enumerated) | [kagisearch/kagimcp](https://github.com/kagisearch/kagimcp) | official-vendor |
| `adawalli/nexus` (Perplexity Sonar) | (not enumerated) | [adawalli/nexus](https://github.com/adawalli/nexus) | community-popular |
| `parallel-web/search-mcp` | (not enumerated) | [parallel-web/search-mcp](https://github.com/parallel-web/search-mcp) | official-vendor |
| `vectorize-io/vectorize-mcp-server` | (not enumerated) | [vectorize-io/vectorize-mcp-server](https://github.com/vectorize-io/vectorize-mcp-server) | official-vendor |
| `tinyfish-io/agentql-mcp` | (not enumerated) | [tinyfish-io/agentql-mcp](https://github.com/tinyfish-io/agentql-mcp) | official-vendor |
| `olostep/olostep-mcp-server` | (not enumerated) | [olostep/olostep-mcp-server](https://github.com/olostep/olostep-mcp-server) | official-vendor |

## 9. AI / ML services

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `everart` (archived) | (not enumerated) | [servers-archived/src/everart](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/everart) | official-archived |
| `imagen3-mcp` | (not enumerated) | [hamflx/imagen3-mcp](https://github.com/hamflx/imagen3-mcp) | community-popular |
| `fal-mcp-server` | (not enumerated) | [raveenb/fal-mcp-server](https://github.com/raveenb/fal-mcp-server) | community-popular |
| `SureScaleAI/openai-gpt-image-mcp` | (not enumerated) | [SureScaleAI/openai-gpt-image-mcp](https://github.com/SureScaleAI/openai-gpt-image-mcp) | community-popular |
| `merterbak/Grok-MCP` | (not enumerated) | [merterbak/Grok-MCP](https://github.com/merterbak/Grok-MCP) | community-popular |
| `jaspertvdm/mcp-server-gemini-bridge` | (not enumerated) | [jaspertvdm/mcp-server-gemini-bridge](https://github.com/jaspertvdm/mcp-server-gemini-bridge) | community-popular |
| `jaspertvdm/mcp-server-openai-bridge` | (not enumerated) | [jaspertvdm/mcp-server-openai-bridge](https://github.com/jaspertvdm/mcp-server-openai-bridge) | community-popular |
| `jaspertvdm/mcp-server-ollama-bridge` | (not enumerated) | [jaspertvdm/mcp-server-ollama-bridge](https://github.com/jaspertvdm/mcp-server-ollama-bridge) | community-popular |

## 10. Finance & payments

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `stripe/agent-toolkit` | (Stripe payments, customers, products) | [stripe/agent-toolkit](https://github.com/stripe/agent-toolkit) | official-vendor |
| `polygon-io/mcp_polygon` | (not enumerated) | [polygon-io/mcp_polygon](https://github.com/polygon-io/mcp_polygon) | official-vendor |
| `base/base-mcp` | (not enumerated) | [base/base-mcp](https://github.com/base/base-mcp) | official-vendor |
| `laukikk/alpaca-mcp` | (not enumerated) | [laukikk/alpaca-mcp](https://github.com/laukikk/alpaca-mcp) | community-popular |
| `ferdousbhai/investor-agent` | (Yahoo Finance + options) | [ferdousbhai/investor-agent](https://github.com/ferdousbhai/investor-agent) | community-popular |

## 11. Monitoring & observability

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `sentry` (archived) | (not enumerated) | [servers-archived/src/sentry](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/sentry) | official-archived |
| `getsentry/sentry-mcp` | (not enumerated) | [getsentry/sentry-mcp](https://github.com/getsentry/sentry-mcp) | official-vendor |
| `grafana/mcp-grafana` | `search_dashboards`, `get_dashboard_by_uid`, `list_datasources`, `query_prometheus`, `query_loki_logs`, `list_incidents`, `create_incident`, `get_current_oncall_users`, `find_slow_requests`, `query_pyroscope`, … (~70+) | [grafana/mcp-grafana](https://github.com/grafana/mcp-grafana) | official-vendor |
| `pab1it0/prometheus-mcp-server` | (not enumerated) | [pab1it0/prometheus-mcp-server](https://github.com/pab1it0/prometheus-mcp-server) | community-popular |
| `dynatrace-oss/dynatrace-mcp` | (not enumerated) | [dynatrace-oss/dynatrace-mcp](https://github.com/dynatrace-oss/dynatrace-mcp) | official-vendor |
| `pydantic/logfire-mcp` | (not enumerated) | [pydantic/logfire-mcp](https://github.com/pydantic/logfire-mcp) | official-vendor |
| `MindscapeHQ/mcp-server-raygun` | (not enumerated) | [MindscapeHQ/mcp-server-raygun](https://github.com/MindscapeHQ/mcp-server-raygun) | official-vendor |
| `panther-labs/mcp-panther` | (not enumerated) | [panther-labs/mcp-panther](https://github.com/panther-labs/mcp-panther) | official-vendor |
| `mpeirone/zabbix-mcp-server` | (not enumerated) | [mpeirone/zabbix-mcp-server](https://github.com/mpeirone/zabbix-mcp-server) | community-popular |
| `netdata/netdata` (MCP) | (not enumerated) | [netdata/netdata](https://github.com/netdata/netdata) | official-vendor |

## 12. Identity, secrets & code security

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `dkvdm/onepassword-mcp-server` | (not enumerated) | [dkvdm/onepassword-mcp-server](https://github.com/dkvdm/onepassword-mcp-server) | community-popular |
| `semgrep/mcp` | (not enumerated) | [semgrep/mcp](https://github.com/semgrep/mcp) | official-vendor |
| `snyk/studio-mcp` | (not enumerated) | [snyk/studio-mcp](https://github.com/snyk/studio-mcp) | official-vendor |
| `StacklokLabs/osv-mcp` | (OSV vulnerability DB) | [StacklokLabs/osv-mcp](https://github.com/StacklokLabs/osv-mcp) | community-popular |
| `safedep/vet` | (vet-mcp package vetting) | [safedep/vet](https://github.com/safedep/vet) | official-vendor |
| `BurtTheCoder/mcp-shodan` | (not enumerated) | [BurtTheCoder/mcp-shodan](https://github.com/BurtTheCoder/mcp-shodan) | community-popular |
| `BurtTheCoder/mcp-virustotal` | (not enumerated) | [BurtTheCoder/mcp-virustotal](https://github.com/BurtTheCoder/mcp-virustotal) | community-popular |
| `BurtTheCoder/mcp-maigret` | (not enumerated) | [BurtTheCoder/mcp-maigret](https://github.com/BurtTheCoder/mcp-maigret) | community-popular |
| `fr0gger/MCP_Security` | (ORKL threat intel) | [fr0gger/MCP_Security](https://github.com/fr0gger/MCP_Security) | community-popular |
| `roadwy/cve-search_mcp` | (not enumerated) | [roadwy/cve-search_mcp](https://github.com/roadwy/cve-search_mcp) | community-popular |

## 13. Code execution & sandboxing

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `yepcode/mcp-server-js` | (not enumerated) | [yepcode/mcp-server-js](https://github.com/yepcode/mcp-server-js) | community-popular |
| `pydantic/mcp-run-python` | (not enumerated) | [pydantic-ai/mcp-run-python](https://github.com/pydantic/pydantic-ai/tree/main/mcp-run-python) | official-vendor |
| `asif-nvc/e2b-sandbox-mcp` | (~29 tools, E2B sandboxes) | [asif-nvc/e2b-sandbox-mcp](https://github.com/asif-nvc/e2b-sandbox-mcp) | community-popular |
| `dagger/container-use` | (not enumerated) | [dagger/container-use](https://github.com/dagger/container-use) | official-vendor |
| `wonderwhy-er/DesktopCommanderMCP` | (file/process/code control) | [wonderwhy-er/DesktopCommanderMCP](https://github.com/wonderwhy-er/DesktopCommanderMCP) | community-popular |
| `oraios/serena` | (LSP-backed code agent) | [oraios/serena](https://github.com/oraios/serena) | community-popular |
| `juehang/vscode-mcp-server` | (not enumerated) | [juehang/vscode-mcp-server](https://github.com/juehang/vscode-mcp-server) | community-popular |
| `ferrislucas/iterm-mcp` | (not enumerated) | [ferrislucas/iterm-mcp](https://github.com/ferrislucas/iterm-mcp) | community-popular |

## 14. Knowledge & memory

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `memory` (official reference) | `create_entities`, `create_relations`, `add_observations`, `delete_entities`, `read_graph`, `search_nodes`, `open_nodes`, … | [servers/src/memory](https://github.com/modelcontextprotocol/servers/blob/main/src/memory) | official-reference |
| `sequentialthinking` (official reference) | `sequentialthinking` | [servers/src/sequentialthinking](https://github.com/modelcontextprotocol/servers/blob/main/src/sequentialthinking) | official-reference |
| `graphlit/graphlit-mcp-server` | (Slack/Drive/Linear/GitHub ingest) | [graphlit/graphlit-mcp-server](https://github.com/graphlit/graphlit-mcp-server) | official-vendor |
| `doobidoo/mcp-memory-service` | (persistent semantic memory) | [doobidoo/mcp-memory-service](https://github.com/doobidoo/mcp-memory-service) | community-popular |
| `kaliaboi/mcp-zotero` | (Zotero Cloud collections) | [kaliaboi/mcp-zotero](https://github.com/kaliaboi/mcp-zotero) | community-popular |

## 15. Maps & location

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `google-maps` (archived) | (not enumerated) | [servers-archived/src/google-maps](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/google-maps) | official-archived |

## 16. Utility & reference

| Server | Tools (sample) | Link | Evidence |
|---|---|---|---|
| `everything` (official reference) | `echo`, `add`, `sample_llm`, `get_tiny_image`, `print_env`, `long_running_operation`, `annotated_message`, `get_resource_reference`, … | [servers/src/everything](https://github.com/modelcontextprotocol/servers/blob/main/src/everything) | official-reference |
| `time` (official reference) | `get_current_time`, `convert_time` | [servers/src/time](https://github.com/modelcontextprotocol/servers/blob/main/src/time) | official-reference |

---

## Excluded entries

These show up in source lists but were not catalogued:

- **Meta-MCP / aggregators** (1mcp, NCP, magg, MCPX, pluggedin-mcp-proxy,
  mcpproxy-go, metatool-app, mcgravity, roundtable) — these bundle other
  MCPs rather than exposing a distinct asset; out of scope for asset-domain
  classification.
- **x402 micropayment middleware** (coinopai, alderpost, agoragentic,
  blockrun, gpu-bridge, x402search, x402-discovery, satring, sF1nX, etc.) —
  payment-routing fabric, not a target asset.
- **Personal fan projects with near-duplicate functionality** (Spotify
  bulk-action clones, Bilibili scrapers, niche music-DAW connectors) —
  long tail not representative.
- **Niche art / cultural servers** (Shahnameh, oorlogsbronnen, bazi
  astrology, Apple Music personal, individual museum APIs) — domain
  coverage is small and idiosyncratic.

Tally: **~120 catalogued servers** across 16 asset domains. The long tail
of the awesome-mcp-servers list (4000+ entries) is intentionally not
included.

## Sources

- Official current: [`modelcontextprotocol/servers`](https://github.com/modelcontextprotocol/servers)
- Official archived: [`modelcontextprotocol/servers-archived`](https://github.com/modelcontextprotocol/servers-archived)
- Community list: [`punkpeye/awesome-mcp-servers`](https://github.com/punkpeye/awesome-mcp-servers)
- Internal references:
  - [`docs/standards/mcp-tool-risk-ratings.csv`](../standards/mcp-tool-risk-ratings.csv)
  - [`docs/standards/atomic-op-classification.md`](../standards/atomic-op-classification.md)
  - [`docs/project/annotated-bibliography-mcp-security.md`](../project/annotated-bibliography-mcp-security.md)
