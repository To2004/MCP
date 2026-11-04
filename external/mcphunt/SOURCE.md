# MCPHunt agent traces (downloaded, not committed)

Recorded tool calls from MCPHunt, used as outside traffic for the framework: five models doing everyday team tasks in one simulated workspace through eight real MCP servers, each run labelled benign, risky or hard negative. The experiment that uses them is [reports/experiments/gateway/mcphunt/](../../reports/experiments/gateway/mcphunt/README.md).

## Source

- Dataset: https://huggingface.co/datasets/mcphunt-benchmark/mcphunt-agent-traces (`main/`, one JSON file per model)
- Code: https://github.com/lihaonan0716/MCPHunt (MIT); environment in `src/mcphunt/environments.py`, server versions in `configs/mcp_server_versions.json`
- Paper: "MCPHunt: An Evaluation Framework for Cross-Boundary Data Propagation in Multi-Server MCP Agents", arXiv:2604.27819
- License: CC-BY-4.0
- Downloaded: 2026-11-01. The SHA-256 of each file is in `gateway_logs/<clock>/meta.json`.

## Folders

Both folders are git-ignored and can be re-created from the commands below.

| Folder | Contents |
|---|---|
| `traces/` | The five `main/` files: 3,615 runs, 62,337 tool calls, about 270 MB |
| `gateway_logs/real/` | One `gateway-log/3` file per server on the recorded clock, plus `calls.csv` (MCPHunt's labels per call) and `meta.json` |
| `gateway_logs/spread90/` | The same calls with the runs spread over 90 days in a seeded random order |

## Re-create

```bash
mkdir -p external/mcphunt/traces
for m in MiniMax_M2_7 deepseek_v4_flash gemini_3_1_pro_preview gpt_5_2 gpt_5_4; do
  curl -sSL -o external/mcphunt/traces/$m.json \
    "https://huggingface.co/datasets/mcphunt-benchmark/mcphunt-agent-traces/resolve/main/main/$m.json"
done
uv run python scripts/mcphunt_to_gateway_log.py --traces external/mcphunt/traces \
    --out external/mcphunt/gateway_logs/real --clock real
uv run python scripts/mcphunt_to_gateway_log.py --traces external/mcphunt/traces \
    --out external/mcphunt/gateway_logs/spread90 --clock spread --days 90
```
