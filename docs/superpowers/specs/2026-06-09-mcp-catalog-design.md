---
title: MCP Server Catalog — Design Spec
date: 2026-06-09
status: approved
---

# MCP Server Catalog — Design Spec

## Goal

Produce a domain-categorized catalog of real-world MCP servers, with each
server's tool list captured, so the thesis project can:

1. Show the breadth of the MCP ecosystem this framework targets.
2. Cluster servers by the asset class they expose to agents.
3. Connect each server's tool set back to the existing atomic operation
   classification used by the scoring framework.

Target size: aim for ~100+ servers from the awesome-mcp-servers list,
the archived `modelcontextprotocol/servers` repo, and MCPs cited in
papers already in `docs/project/`. If breadth is unreachable, fewer
entries are acceptable — quality of categorization beats raw count.

## Out of scope

- Deep per-tool documentation (the four servers in `docs/mcp-tools/`
  already have this — filesystem, github, slack, sqlite).
- Risk scoring per server — downstream artifact, not part of this work.
- Installation, smoke testing, or live tool calls. Descriptions only.

## Two-level taxonomy

### Level 1 — Asset domain (per MCP server)

What asset class the server exposes to agents:

- Local filesystem
- Source code & dev (Git, GitHub, GitLab, code search, IDE)
- Databases (SQL, NoSQL, vector)
- Messaging & communication (Slack, Discord, email, Teams)
- Productivity & docs (Notion, Drive, Confluence, calendar)
- Browser & web (Puppeteer, Playwright, scraping)
- Cloud infrastructure (AWS, GCP, Azure, k8s, Docker)
- Search & retrieval (Brave, Tavily, semantic search)
- AI / ML services (embeddings, image gen, LLM proxies)
- Finance & payments (Stripe, banking, crypto)
- Monitoring & observability (logs, metrics, traces)
- Identity & secrets (auth, vaults, API keys)
- Other / niche (catch-all)

The list may shrink or grow once data lands — domains with one or two
entries can fold into "Other", and a domain with 15+ entries may split.

### Level 2 — Operation type (per tool inside a server)

Reuse the existing classification in
`docs/standards/atomic-op-classification.md` and the operation list in
`docs/standards/mcp-primitive-operations.csv`. Do not invent a new
taxonomy. Operation classes shown in the graph view, not the catalog
table (catalog stays scannable).

## Deliverables

### 1. `docs/mcp-tools/catalog.md`

One file. Section per asset domain. Each section has a table:

| Server | Tools | Link | Evidence |
|--------|-------|------|----------|

- **Server** — display name, e.g., `filesystem (official)`.
- **Tools** — comma-separated tool names. If a README does not enumerate
  tools, write `(not enumerated)` and link the README.
- **Link** — repo or documentation URL.
- **Evidence** — why this server is in the catalog. One or more of:
  - `official` — appears in the official archived `modelcontextprotocol/servers` list.
  - `paper-cited` — appears in a paper cited in `docs/project/annotated-bibliography-mcp-security.md`
    or in a benchmark catalogued in `docs/project/`.
  - `awesome-list` — appears in the community awesome-mcp-servers list.
  - `community-popular` — broadly referenced in MCP discussions but not
    in either canonical list.

Short intro at the top of the file explains the taxonomy and how to
read the tables. A short footer lists excluded entries with one-line
reasons (dead link, not an MCP, duplicate).

### 2. `docs/mcp-tools/domain-graph.md`

Two Mermaid views:

- **View 1 — Domain → Servers**: each asset domain is a parent node,
  individual MCPs are children. Lets a reader see clustering at a glance.
- **View 2 — Domain → Operation types**: for each domain, which
  operation classes from the atomic taxonomy show up. Connects the
  catalog to the scoring framework.

Both views use the same domain names as the catalog. The file should
remain readable in plain-text Mermaid (no external rendering required
for the spec to be useful).

### 3. `docs/mcp-tools/README.md` — index update

Add links to `catalog.md` and `domain-graph.md` alongside the existing
references to the four deep-doc servers. Do not remove the existing
links.

## Sourcing process

1. Fetch the awesome-mcp-servers index. Extract server list with repo
   URLs.
2. Fetch the archived `modelcontextprotocol/servers` repo README.
   Cross-reference with the awesome list.
3. Cross-reference papers and benchmarks already in
   `docs/project/annotated-bibliography-mcp-security.md`,
   `docs/project/compass_survey_comparison.md`,
   `docs/project/testbed-tools-comparison.md` for paper-cited servers.
4. For each unique server, WebFetch the README and extract the tool
   list. Prefer tool names that appear in code blocks or tables.
5. Skip entries that are clients, frameworks, or non-MCP. Note them in
   the excluded footer.

## Quality bar

- Every entry has a domain assignment, even if "Other".
- Every entry has a working link or is moved to the excluded footer.
- Tool lists are factual — never invented. Missing tools become
  `(not enumerated)` rather than guessed.
- Catalog file stays below ~1000 lines. If it grows past that, split
  by domain into `docs/mcp-tools/catalog/<domain>.md` and keep
  `catalog.md` as an index. Do not pre-emptively split.

## Acceptance

The work is done when:

- `catalog.md` lists every sourced server, each with a domain and a
  link, sorted into domain sections.
- `domain-graph.md` renders both Mermaid views with the same server
  set as the catalog.
- `README.md` links the new files.
- The excluded footer in `catalog.md` lists every entry that was
  skipped and why.
