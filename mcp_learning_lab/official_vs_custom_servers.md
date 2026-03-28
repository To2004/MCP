# Official MCP Servers vs Custom Server — What's the Difference?

## What We Built (Custom)

Our `filesystem_server.py` is a **custom server we wrote ourselves** using the
`mcp` Python SDK. It works, follows the real MCP protocol, but:

- We wrote all the tool logic (read_file, list_directory, get_file_info)
- We decide what tools exist and how they behave
- Nobody else uses or maintains it
- It's a learning exercise, not battle-tested

## What Official Servers Are

Official MCP servers are **maintained by Anthropic and the community** at
[github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers).
They are production-grade, widely used, and trusted by tools like Claude Desktop.

### Requires: Node.js + npx

All official servers are Node.js packages. To use them you need:

1. Install Node.js from [nodejs.org](https://nodejs.org)
2. This gives you `npx`, which can run any server instantly without installing it globally

## Key Differences

| Aspect | Our Custom Server | Official Servers |
|--------|-------------------|------------------|
| **Who wrote it** | Us, for learning | Anthropic / community maintainers |
| **Language** | Python | Node.js (TypeScript) |
| **How to run** | `uv run python filesystem_server.py` | `npx @modelcontextprotocol/server-filesystem` |
| **Tools exposed** | 3 basic file tools we defined | Many more tools, well-designed, edge cases handled |
| **Used in production** | No | Yes — Claude Desktop, Cursor, other AI tools use these |
| **Security** | Basic path restriction we wrote | Proper sandboxing, permission models, audited |
| **Updates** | Only if we update it | Community maintains, fixes bugs, adds features |
| **Error handling** | Minimal | Comprehensive — handles symlinks, permissions, encoding, large files |

## Official Servers You Could Connect To

### 1. `@modelcontextprotocol/server-filesystem`

**What it does:** Full filesystem access — read, write, search, move, get info.

```bash
npx -y @modelcontextprotocol/server-filesystem C:/Users/user/Documents/GitHub/MCP
```

**Tools it exposes:**

| Tool | Description |
|------|-------------|
| `read_file` | Read complete file contents |
| `read_multiple_files` | Read several files at once |
| `write_file` | Create or overwrite a file |
| `edit_file` | Surgical edits with find/replace |
| `create_directory` | Create directories recursively |
| `list_directory` | List directory contents with metadata |
| `move_file` | Move or rename files |
| `search_files` | Regex search across files |
| `get_file_info` | File metadata (size, timestamps, permissions) |
| `list_allowed_directories` | Show which directories the server can access |

**Difference from ours:** Our server has 3 read-only tools. The official one has
10 tools including write, edit, search, and move — plus it handles symlinks,
binary files, encoding detection, and large files properly.

### 2. `@modelcontextprotocol/server-github`

**What it does:** Full GitHub API access — repos, issues, PRs, branches, files.

```bash
npx -y @modelcontextprotocol/server-github
```

Requires a `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable.

**Tools it exposes (partial list):**

| Tool | Description |
|------|-------------|
| `create_or_update_file` | Commit a file to a repo |
| `search_repositories` | Search GitHub repos |
| `create_issue` | Open a new issue |
| `create_pull_request` | Open a PR |
| `list_commits` | List commit history |
| `search_code` | Search code across GitHub |
| `fork_repository` | Fork a repo |
| `create_branch` | Create a new branch |

**Why this matters:** An AI agent connected to this server can interact with
GitHub the same way a developer does — create issues, open PRs, search code.
This is a real-world use case for MCP in production.

### 3. `@modelcontextprotocol/server-memory`

**What it does:** Persistent memory using a knowledge graph stored in a local
JSON file.

```bash
npx -y @modelcontextprotocol/server-memory
```

**Tools it exposes:**

| Tool | Description |
|------|-------------|
| `create_entities` | Add nodes to the knowledge graph |
| `create_relations` | Add edges between nodes |
| `search_nodes` | Search entities by query |
| `open_nodes` | Retrieve specific entities |
| `delete_entities` | Remove entities |
| `delete_relations` | Remove relations |

**Why this matters:** This lets an agent build up memory across conversations —
it stores facts as a graph of entities and relationships.

### 4. `@modelcontextprotocol/server-sqlite`

**What it does:** Query and manage SQLite databases.

```bash
npx -y @modelcontextprotocol/server-sqlite path/to/database.db
```

**Tools it exposes:**

| Tool | Description |
|------|-------------|
| `read_query` | Run SELECT queries |
| `write_query` | Run INSERT/UPDATE/DELETE |
| `create_table` | Create new tables |
| `list_tables` | Show all tables |
| `describe_table` | Show table schema |
| `append_insight` | Store analytical insights |

## How Our Agent Would Change

Right now our `agent.py` connects to our custom server:

```python
# Current — spawns our custom Python server
server_params = StdioServerParameters(
    command=sys.executable,
    args=[str(SERVER_SCRIPT)],
)
```

To connect to an official server, you would change just the command:

```python
# Official filesystem server (requires Node.js)
server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "C:/Users/user/Documents/GitHub/MCP"],
)
```

```python
# Official GitHub server (requires GITHUB_PERSONAL_ACCESS_TOKEN env var)
server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-github"],
    env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]},
)
```

**Everything else in `agent.py` stays the same.** The handshake, tool discovery,
and tool calling work identically — that's the whole point of MCP as a protocol.
The agent doesn't care who built the server.

## The Big Takeaway

MCP is a **protocol**, not a specific server. Any server that speaks MCP
(custom or official) works with any client that speaks MCP. Our agent can connect
to our 3-tool Python server today and the 10-tool official filesystem server
tomorrow — with zero code changes to the discovery and calling logic.

The only thing that changes is the `StdioServerParameters` line that tells the
agent which server process to spawn.

## Next Step

Install Node.js, then modify `agent.py` to point at an official server and see
the richer tool set an agent gets access to in the real world.
