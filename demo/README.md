# Demo

Demo assets used as targets for the MCP risk-scoring framework. Nothing in
here is production code or real data.

## Contents

- [corp_filesystem/](corp_filesystem/) — fake corporate file tree exposed via
  the official Anthropic filesystem MCP server. See its README for the run
  command and layout.

## Regenerating

The corp filesystem is generated from a single Python dict so it stays
deterministic and easy to tweak:

```bash
python scripts/build_corp_demo.py
```

Re-running is safe — the script is idempotent.
