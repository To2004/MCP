# Gateway Demo: the Remote GitHub MCP, Static and Dynamic End to End

The whole framework run once on an external server: agents call the remote GitHub MCP
(`https://api.githubcopilot.com/mcp/`) through the observe-only gateway, the gateway's own
capture of the server's tool list is scanned, and every call is scored. Run 2026-10-14.

## How it fits together

```
1,000-row org corpus ──► scripts/gateway_replay_corpus.py (6 persona sessions, reads only)
                              │
                              ▼
                 gateway 127.0.0.1:8765/github ──► api.githubcopilot.com/mcp/
                              │ every message logged
              ┌───────────────┴──────────────────┐
     tools/list reply                       tools/call + reply
              │                                   │
  github_remote.json (49 tools)                   │
  + github_helios_remote.md (org policy)          │
              │                                   │
  static-scan ─ scan/    S, impact, blast         │
             └─ inputs/  input importance         │
  scan_breadth  ─► breadth_spec/github_remote_scan.json
  static_cells  ─► github_remote.cells.json       │
  derive_input_labels --stage rules ─► rules/     │
              └───────────────┬───────────────────┘
                              ▼
          gateway/score.py: cell × B × L per call, plus the input level
```

## Files

| File | What it is | Made by |
|---|---|---|
| `github_remote.json` | The server's `tools/list`, as the gateway saw it (49 tools, sha256 `108315cf7888…`) | `gateway/catalog.py` |
| `github_helios_remote.md` | The `github_helios` org policy with tool and argument names renamed to the remote server's; wording unchanged | `gateway/github_remote.py` |
| `scan/` | Asset sensitivity, tool impact, blast radius: levels only | `static-scan --parts scan`, job 22920833 |
| `inputs/` | Input importance: which inputs can change a call's risk | `static-scan --parts inputs`, job 22922834 |
| `github_remote.cells.json` | Levels combined into cells, `S × blast × impact` (the repo's v5 formula, at most 125) | `gateway/static_cells.py` |
| `rules/` | One run-time rule per kept input, levels 1–5 | `scripts/derive_input_labels.py --stage rules`, job 22924105 |
| `../../breadth_spec/github_remote_scan.json` | Which inputs are quantities, for the runtime factor `B` | `scripts/scan_breadth.py` |

The scored calls themselves stay in `runs/gateway/full/` (gitignored): `github.jsonl` is
the raw log, `github_scored.csv` one row per call.

## Results

**Static**, qwen2.5:32b on one RTX 4090:

| Part | Result | Cost |
|---|---|---|
| Scan | 19 assets × 49 tools = 931 pairs; 217 reached, 0 unanswered | 969 model calls, 60 min |
| Bands of the 217 cells | 54 low, 88 medium, 64 high, 11 critical | |
| Impact | 31 tools by the fixed rules, 18 by the model | |
| Input importance | 155 of 292 inputs kept, 0 tools failed | 147 model calls, 19 min |
| Input rules (stage 2) | 145 of 155 kept inputs have a rule: 77 `register`, 40 `keywords`, 21 `values`, 7 `ranges`; the 10 without one are mostly `perPage` | 12 min |
| Breadth | 271 of 271 inputs classified | 6 min |

Highest cells: `pull_request_review_write` × `helios-scada-gateway` 125;
`delete_file`, `merge_pull_request`, `push_files` × the perimeter repositories 100.

**Same model, same policy, different catalog.** On the 17 tools whose names did not change
between the npx server and the remote one, against the validated v5 scan
(`v5/five_level_v2_policy_v5r_nacombo/github_helios.json`): asset sensitivity identical on
18 of 19 assets, tool impact on 15 of 17 (`search_repositories`, `search_users` moved 3 → 2
on the new descriptions), reach on 307 of 323 pairs; of the 88 pairs both scans reach, 72
have the identical cell and 83 a blast within one level.

**Dynamic**, 908 read calls through the gateway (632 ok, 276 tool errors: the same split
the original direct run recorded):

| | |
|---|---|
| Calls scored | 908 of 908 (375 were "tool not in scan" against the old 26-tool scan) |
| Asset resolution | 200 named, 5 sole candidate, **703 unresolved** (worst cell of the tool) |
| Runtime factor `B × L` | moves on 837 calls, 0.71 to 1.34 |
| Risk bands | 70 low, 386 medium, 451 high, 1 critical |
| Input level | 110 at 3 (normal), 739 at 4, 54 at 5, 5 with no rule |
| Scoring time | median ~0.1 ms per call, max ~0.3 ms (cell, `B × L` and input level) |

**Where the input level disagrees with the risk.** 53 of the 54 level-5 calls read one of
the four perimeter repositories (`helios-ot-runbooks`, `-market-bidding-engine`,
`-grid-infra-config`, `-scada-gateway`); the other reads `.env.example`, the policy's
credential-shaped path. The level comes from the `repo` rule's policy overrides, written
from the policy's input section, not from the scan, which gives those assets sensitivity
4. The cell side rates 46 of these 54 calls only *medium*: `get_file_contents` on
`helios-ot-runbooks` is 4 × 4 × 3 = 48. Most level-4 calls are the register-gap default
below (`owner` = `To2004` names no asset), not a finding.

## Known gaps

- **Most calls resolve to no asset.** The helios register names the five `helios-*`
  repositories; the corpus mostly reads the account's other repositories, so 703 of 908
  calls take the tool's worst cell. Listing those repositories in the policy, or plugging
  in the traffic-learned bindings (`mcp_security.binding.discovery`), would fix it.
- **The policy predates the remote catalog.** 28 remote tools are in no register row (the
  model judged their reach: 145 pairs outside the register), and the policy's prose still
  says no verb deletes a file, while the remote catalog has `delete_file`.
- **Merged tools share one cell.** `pull_request_read` has one cell per asset for all nine
  of its `method` values (`get_diff` and `get_status` score the same).
- **Writes were not replayed**, so every scored call is a read.
- **The input level is reported beside the risk, not inside it**: how it should combine
  with `cell × B × L` is described in `src/mcp_security/input_rules/README.md` but not
  decided.

## Reproduce

```bash
GITHUB_TOKEN=$(gh auth token) uv run python -m mcp_security.gateway.proxy \
    --config src/mcp_security/gateway/routes.example.json
uv run python scripts/gateway_replay_corpus.py
uv run python -m mcp_security.gateway.catalog --config src/mcp_security/gateway/routes.example.json --route github
sbatch --export=ALL,NAME=github_remote scripts/gateway_static_scan.sbatch
sbatch --export=ALL,NAME=github_remote,PARTS=inputs scripts/gateway_static_scan.sbatch
sbatch --gres=gpu:rtx_4090:1 --export=ALL,LABEL_SERVERS=github_remote,LABEL_FLAGS="--stage rules",MCP_INPUT_LABELS_OUT=$PWD/reports/experiments/gateway/github_remote/rules \
    scripts/derive_input_labels.sbatch
uv run python -m mcp_security.gateway.score --config src/mcp_security/gateway/routes.example.json --route github
```

Stage 2 reads `rules/github_remote.importance.json`, a link to `inputs/`.
