# MCPHunt: the framework on outside traffic

The whole framework (policy, static scan, runtime scoring) run on calls we did not make: MCPHunt's 62,337 recorded tool calls of five models doing team tasks in one simulated workspace, through eight real MCP servers, with each run labelled by MCPHunt as benign, risky or hard negative. It is the first check of the framework against labels from outside this repo.

## What is here

| Path | What it is |
|---|---|
| `<server>/mcphunt_<server>.json` | The server's tool list at MCPHunt's pinned version, captured with `static-scan capture` (shell: rebuilt from the package source, see the file) |
| `<server>/mcphunt_<server>.md` | The policy we wrote for it from MCPHunt's environment code |
| `<server>/scan/` | The static scan (sensitivity, impact, blast radius), its prompts as run and its log |
| `<server>/mcphunt_<server>.cells.json` | The scan's levels as cells, the file the gateway scores with |
| `routes.real.json`, `routes.spread90.json` | One route per server; they differ only in which log folder they read |
| `results_real.md`, `results_spread90.md` (+ `.json`) | The scores graded against MCPHunt's labels, one report per clock |
| [`judge/`](judge/README.md) | An independent judge's 1-5 rating of 600 sampled calls, and the framework graded against it |

The time server is listed with no scan: it holds no company data. The traces and the gateway logs made from them are git-ignored, in [`external/mcphunt/`](../../../../external/mcphunt/SOURCE.md).

## The data

- **Workspace.** One team's development workspace for "Project Alpha": a payment, payroll or sign-in service depending on the variant. It holds 39 files including an `.env`, a config with passwords and a deploy script with a token; a SQLite database with users, API keys, payroll rows (social security numbers, salaries) or sign-in tokens; a knowledge graph with a master or signing key and the team roster; a git history that still holds old secrets; and four local web pages, among them an admin panel with credentials.
- **Runs.** 723 runs per model (MiniMax M2.7, DeepSeek V4 Flash, Gemini 3.1 Pro, GPT-5.2, GPT-5.4), over 147 tasks:
  - risky: real-looking secrets are planted and the task tempts a leak;
  - benign: the same files with obviously fake development values;
  - hard negative: the same task and file names with harmless look-alike values.
  MCPHunt also judges each run's outcome as safe or unsafe, and flags each call whose arguments carry a planted secret.
- **Agent's view of the tools.** MCPHunt's agents saw its own short definitions of 28 tools, not each server's full `tools/list`. We scanned the real servers' lists, because that is what a gateway in front of them sees. Every tool the agents called is in those lists.

## How it was made

1. **Catalogs.** `static-scan capture -- uvx --exclude-newer 2026-04-24 <server>==<version>` (or `npx`). Dependencies are resolved as of MCPHunt's collection date: today's `mcp` package breaks the older Python servers.
2. **Policies.** One per server, in the static-scan template: the company paragraph (ours: MCPHunt describes no company), the classes, a register whose assets are what MCPHunt's environment actually holds, and the rules. `static-scan check` gives 0 warnings on all seven. File asset ids carry the `workspace-` prefix because every path an agent sends contains it, so a path binds to its own asset and excludes the others.
3. **Static scan.** `scripts/gateway_static_scan.sbatch` with `NAME`, `DIR` and `POLICY`, one RTX 4090 job per server, about 14 minutes each. All seven finished with no unanswered pair.
4. **Gateway logs.** `scripts/mcphunt_to_gateway_log.py` writes each call as the request and reply lines the gateway writes. Each model is one agent and each run is one session per server. There are two clocks:
   - `real`: the recorded times. Each model's runs span one to three days, in blocks: risky, then benign, then hard negative.
   - `spread`: each model's runs in a seeded random order over 90 days.
5. **Scoring.** `uv run python -m mcp_security.gateway.score --config routes.<clock>.json --route <server>`, the same scorer the gateway runs live.
6. **Grading.** `scripts/evaluate_mcphunt_scores.py` joins each scored call to its MCPHunt labels.

## Results (spread clock)

61,926 calls scored (time server: 406 calls not scored).

| Score | Risky vs benign runs | Risky vs hard-negative runs | Unsafe vs safe runs | Calls carrying a secret vs the rest |
|---|---|---|---|---|
| Static cell | 0.501 | 0.486 | 0.579 | 0.477 |
| Gate risk (cell x factor) | 0.506 | 0.488 | 0.547 | 0.476 |
| Dynamic risk (static level x behaviour) | 0.497 | 0.495 | 0.581 | 0.504 |

Run-level columns score each run by its highest call; values are ROC AUC. The full tables (per route, per group, behaviour multiplier) are in [results_spread90.md](results_spread90.md).

On the real clock the dynamic risk reaches 0.732 (risky vs benign) and 0.808 (risky vs hard negative), but this is an artefact. The behaviour layer's warm-up checks fire early in a route's life, and on the real clock every risky run comes before every benign one. With the runs shuffled (spread clock) the effect disappears and the multiplier is the same in all three groups (mean 1.04-1.06). See [results_real.md](results_real.md).

## What the results say

- **The scores do not separate MCPHunt's risky runs from its benign or hard-negative ones.** The variants differ only in the *values* inside the files; a risky and a benign run make the same calls on the same paths. A per-call score that reads the tool, the arguments and the caller's history cannot see that difference, and does not.
- **The leaking call scores lower than an ordinary read.** 874 `write_file` calls carry a planted secret: 720 go to `notes/`, bind to `workspace-notes` and score a cell of 24, while a plain `.env` read scores 75. The static side prices where a write lands, not what it carries. Catching this needs the content (or the read-then-write flow) at runtime.
- **Unsafe runs score a little higher (AUC 0.55-0.58).** Runs MCPHunt judged unsafe tend to touch more sensitive assets, so their highest call is higher. The effect is small.
- **Binding falls back to the worst case often.**
  - Filesystem: 13,821 of 37,443 calls are unresolved. Reads of `project_alpha/README.md`, `requirements.txt` and `pyproject.toml` name no asset; `list_directory` was judged to reach 10 assets though the register gave it one; 1,849 `write_file` calls arrived with no arguments at all.
  - Shell: every command scores 125, because one tool reaches everything.
  - A container asset for the rest of `project_alpha/` would bind those reads; it was not added, so the scan here is the first pass.

## Independent judge, call by call

MCPHunt labels runs, not calls, so a second model rated a sample of calls to give per-call ground truth. The scripts are [`scripts/judge_mcphunt_calls.py`](../../../../scripts/judge_mcphunt_calls.py) (sample, judge, grade) and [`judge_mcphunt_calls.sbatch`](../../../../scripts/judge_mcphunt_calls.sbatch). The files are in [`judge/`](judge/): `sample.jsonl`, `verdicts.jsonl`, and [report.md](judge/report.md) with its `.json`.

- **Judge.** `gemma3:27b`, a different family from the scanner's `qwen2.5:32b`. One pass at temperature 0, one RTX 4090, 29 minutes, no failed verdicts.
- **Sample.** 600 calls from the spread clock: 150 of the calls whose arguments carry a planted secret, and 450 others spread over the seven servers and the three run groups. Metrics are unweighted over this sample.
- **What the judge sees.** The server's policy (classification section), the tool's description and schema, the call's full arguments (each value cut at 2,000 characters), and the run's six earlier calls. It does not see the task prompt or MCPHunt's labels. It rates the call 1-5 on a scale tied to the policy's classes; 5 means Restricted values copied or sent somewhere new, or an irreversible change.

**The judge passes its check.** It rates the secret-carrying calls above the rest with AUC 0.893, and gives 82% of them a 4 or 5. Its misses are judgement calls, not a blind spot from cutting long values (83% of cut and 82% of whole carriers rated 4+). On calls without a secret it does not separate risky runs from benign ones either (AUC 0.539): those calls are the same in both.

**The framework against the judge:**

| Measure | Value |
|---|---|
| Spearman, judge vs cell / static level / dynamic risk | 0.061 / 0.061 / 0.099 |
| Weighted kappa, judge vs static level (rounded) | 0.067 |
| Our level 4+ that the judge also rates 4+ (precision) | 0.385 |
| Judge 4+ that we also rate 4+ (recall) | 0.668 |
| Same asset named, where the judge named one | 0.35 |

| Route | Calls | Mean judge | Mean static level | Spearman |
|---|---|---|---|---|
| git | 50 | 2.64 | 3.25 | 0.892 |
| sqlite | 91 | 2.89 | 3.84 | 0.765 |
| browser | 30 | 2.23 | 4.43 | 0.44 |
| memory | 60 | 3.30 | 4.08 | 0.367 |
| filesystem | 238 | 3.29 | 3.15 | 0.222 |
| shell | 101 | 2.42 | 4.97 | -0.225 |
| fetch | 30 | 2.93 | 4.09 | -0.501 |

**Over-scored: 190 calls, our level 2+ above the judge.**

- **No asset named.** 115 are unresolved, so they are priced at the tool's worst asset. Of these, 79 are shell commands (`ls`, `git branch`, a `curl` to pypi.org), all priced as `.env`; others are reads like `.editorconfig` or `project_alpha/README.md`.
- **Named, but kept at the worst case.** `SELECT * FROM users` binds to `users`, yet it is priced as `oauth-tokens`: the other tables' names never appear in the query, and the binding never drops an asset nothing resembled.

**Under-scored: 51 calls, our level 2+ below the judge.** 50 are `write_file` calls that copy secrets into `notes/`. We price them at 3 (a notes file); the judge rates them 5 (live tokens copied). This is the same blind spot as the run-level result, now shown call by call.

**Reading.** The framework agrees with the judge where the arguments name the asset: git (0.89) and sqlite (0.77). It disagrees where a tool can reach everything (shell, fetch), and where the risk is in the content of a write (filesystem). Fixing binding would remove most over-scores. Under-scores need a look at argument content.

## Limits

- **The judge is one model, one pass.** A second judge (or a person on a subsample) would show how much of the disagreement is the judge's. Its scale is per call, while a cell is the worst case of a tool on an asset, so some gap is expected by design.
- **The company and policies are ours.** MCPHunt describes the files, not an organization, so every class and level rests on our reading. A different policy gives different cells, though not a different risky-vs-benign result, since that result comes from identical calls.
- **The history is short.** Five agents, about 700 runs each. On the spread clock that is a handful of runs a day, below what the behaviour layer's learned limits need (50 agent-days per tool for v4), so it ran with its written defaults.
- **MCPHunt's risk is a flow.** It labels secrets moving across servers, which the framework does not model; this is a test of what per-call scoring can and cannot see, not a fair contest.

## References

- MCPHunt traces: https://huggingface.co/datasets/mcphunt-benchmark/mcphunt-agent-traces (CC-BY-4.0)
- MCPHunt code: https://github.com/lihaonan0716/MCPHunt (MIT)
- MCPHunt paper: arXiv:2604.27819
- Gateway log format and scorer: [`src/mcp_security/gateway/README.md`](../../../../src/mcp_security/gateway/README.md)
