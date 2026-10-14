# Gateway Experiments

Runs of the whole framework on external MCP servers, through the observe-only gateway
(`src/mcp_security/gateway/`): the static scan is run on the tool list the gateway
captured, and every call that passed through it is scored.

| Folder | Server | What it holds |
|---|---|---|
| [github_remote/](github_remote/README.md) | Remote GitHub MCP (`api.githubcopilot.com/mcp/`, 49 tools) | Captured catalog, org policy with remote names, static scan, input importance, input rules, results |
| [signal_trial/](signal_trial/README.md) | Same traffic, offline | Which extra runtime signals separate misuse-shaped sessions (planted, offline) |
