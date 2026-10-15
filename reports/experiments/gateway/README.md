# Gateway Experiments

Runs of the whole framework on external MCP servers, through the observe-only gateway
(`src/mcp_security/gateway/`): the static scan is run on the tool list the gateway
captured, and every call that passed through it is scored.

| Folder | Server | What it holds |
|---|---|---|
| [github_remote/](github_remote/README.md) | Remote GitHub MCP (`api.githubcopilot.com/mcp/`, 49 tools) | Captured catalog, org policy with remote names, static scan, input importance, input rules, results |
| [signal_trial/](signal_trial/README.md) | Same traffic, offline | Which extra runtime signals separate misuse-shaped sessions (planted, offline) |
| [log_example/](log_example/README.md) | Remote GitHub MCP, one real run | A complete `gateway-log/3` log with every kind of line, walked through line by line |
| [scale/](scale/README.md) | Fake local servers, dedicated CPU nodes | Cost per call, many callers, throughput per process and per shard, runtime vs semi-runtime, storage, restart |
