# External MCP Traffic and Environments

Every outside source of MCP data found so far that the framework can run on: recorded agent calls to download and score, simulated companies with MCP servers to generate traffic against, and real traffic that hit MCP servers. MCP-only. Links, licenses and stars were checked on 2026-11-01. The threat direction is ours throughout: the MCP server is the asset, the calling agent is the threat.

## Which to use for what

| You want | Use |
|---|---|
| Outside calls with ground-truth labels, on a company workspace | **MCPHunt** (done: [experiment](../../reports/experiments/gateway/mcphunt/README.md)), or MCP-CredLeak for the same calls as one row each |
| Ordinary traffic to measure false alarms on | MCPHunt's benign and hard-negative runs; MCPMark trajectory logs |
| A richer company to run your own personas against | EnterpriseOps-Gym; TheMCPCompany |
| Real attackers hitting an MCP server | AICryptoVault honeypot logs |
| Realistic call mix to calibrate a simulated org | PostHog's published numbers, MCPHunt (done: [call distributions](../../reports/experiments/call_distributions/README.md)) |

## Recorded agent calls

Download, convert to gateway logs, score. "Policy / static / dynamic" says what our three stages can do with each.

| # | Source | What it holds | Labels | License | Policy / static / dynamic |
|---|---|---|---|---|---|
| 1 | **MCPHunt** — [traces](https://huggingface.co/datasets/mcphunt-benchmark/mcphunt-agent-traces) (author copy with extra strata: [lihaonan0716/mcphunt-agent-traces](https://huggingface.co/datasets/lihaonan0716/mcphunt-agent-traces)), [code](https://github.com/lihaonan0716/MCPHunt), arXiv:2604.27819 | One team's workspace (files, SQLite, git, memory, shell, fetch, browser, time). 3,615 runs, 62,337 calls, five models. Every call has server, tool, arguments, result, success, time | Run: benign / risky / hard negative, safe / unsafe outcome. Call: secret in arguments or result | CC-BY-4.0 data, MIT code | **All three done.** Servers are pinned public packages; the environment is in the code |
| 2 | [MCP-CredLeak](https://huggingface.co/datasets/Jashwanth77/MCP-CredLeak) | MCPHunt flattened to one row per call (about 77k), with session-flow features and train/validation/test splits | Nine classes: eight leak types plus none | CC-BY-4.0 | Same data as MCPHunt; handy for call-level checks |
| 3 | [MCPMark trajectory logs](https://huggingface.co/datasets/Jakumetsu/mcpmark-trajectory-log) ([benchmark code](https://github.com/eval-sys/mcpmark), 470 stars, Apache-2.0; arXiv:2509.24002) | About 36k files: per run `messages.json`, `execution.log`, `meta.json`; filesystem, GitHub, Notion, Postgres, Playwright, from designed starting states | Task success only | MIT (community upload) | Policy and static: yes (public servers, starting states in the code). Dynamic: yes, as ordinary traffic (no risk labels) |
| 4 | [Toolathlon trajectories](https://huggingface.co/datasets/hkust-nlp/Toolathlon-Trajectories) ([code](https://github.com/hkust-nlp/Toolathlon), 510 stars; arXiv:2510.25726) | Three runs per model over 32 apps and 604 tools, from realistic starting states | Task success only | CC-BY-4.0; gated (agree to terms); not for training | Policy partly, static yes, dynamic as ordinary traffic |
| 5 | [MCP-Atlas](https://huggingface.co/datasets/ScaleAI/MCP-Atlas) | Reference runs over 36 real public servers, 220 tools | Task success | CC-BY-4.0 | Static yes; no company, so policy is weak |
| 6 | [Toucan-1.5M](https://huggingface.co/datasets/Agent-Ark/Toucan-1.5M) | 1.5M generated runs on 495 public servers (search, dev tools, crypto) | None | Apache-2.0 | Background volume only; no company |
| 7 | [mcp-decision-layer-bench](https://huggingface.co/datasets/abhishek085/mcp-decision-layer-bench) | Run logs from a 12-server mock world behind an MCP gateway | None | CC-BY-4.0 | On hold: the code repo with the world (`abhishek085/mcp-decision-layer`) returns 404, so there is no tool list |
| 8 | [mcp-tool-traces-v2](https://huggingface.co/datasets/stindardlogic/mcp-tool-traces-v2) | 2,000 runs over filesystem, GitHub, Notion, Postgres, S3, Linear, Slack, Brave | None | Apache-2.0 | No: looks generated, no server code |
| 9 | [obaydata MCP trajectories](https://huggingface.co/datasets/obaydata/mcp-agent-trajectory-benchmark) | 49 runs in business roles (accountant, recruiter, HR onboarding, CRM), each with its own MCP server file; 11 real OpenClaw sessions | None | Apache-2.0 | Policy and static yes; too few calls for dynamic |
| 10 | [MCP-Universe trajectories](https://huggingface.co/datasets/Shuibai12138/mcp-universe-trajectories) ([MCP-Universe](https://github.com/SalesforceAIResearch/MCP-Universe), 603 stars) | DeepSeek V4 Pro on MCP-Universe tasks, every call and result | Task success | Apache-2.0 | No company data to protect |
| 11 | [MCP-RiskCue](https://github.com/PorUna-byte/MCP-RiskCue) (arXiv:2511.05867) | 2,421 + 471 generated chats with MCP server system logs | Risk type | None stated | No: generated |

## Simulated companies with MCP servers

Run your own personas against these to produce traffic with known assets.

| # | Source | The company | Notes |
|---|---|---|---|
| 12 | **[EnterpriseOps-Gym](https://github.com/ServiceNow/EnterpriseOps-Gym)** ([tasks](https://huggingface.co/datasets/ServiceNow-AI/EnterpriseOps-Gym); 143 stars, Apache-2.0) | Eight areas: HR, IT tickets, customer service, email, calendar, drive, Teams, and tasks that cross them; 512 tools, 164 tables | MCP servers as Docker images, database snapshots in the repo; some of its 1,150 tasks break policy on purpose. No call logs |
| 13 | [TheMCPCompany](https://github.com/Reza-esfandiarpoor/the-mcp-company) (16 stars, no license; arXiv:2510.19286) | A software company (GitLab, RocketChat, Plane, ownCloud, Azure) with model-played employees; 18,505 tools | Built on TheAgentCompany's environment |
| 14 | [mock-enterprise-MCP](https://github.com/StephenFlavin/mock-enterprise-MCP) (0 stars, MIT) | Harbour & Vale, a made-up UK retailer: 96 MCP servers, about 2,000 tools | Data generated the same way every run; untested by others |
| 15 | [MCPMark](https://github.com/eval-sys/mcpmark) environments | GitHub repos with history, Notion templates, Postgres databases, filesystem | Pairs with the logs in row 3 |
| 16 | [Toolathlon](https://github.com/hkust-nlp/Toolathlon) environments | 32 apps from realistic starting states (Canvas courses, spreadsheets) | No license detected on the repo; pairs with row 4 |
| 17 | [Era by Eon](https://github.com/eon-io/era) (7 stars, no license) | Generates a company across 61 systems (Salesforce, Slack, Jira, Zendesk) with MCP endpoints | Hosted, needs sign-in; your traffic goes to a third party |

## Real traffic to MCP servers

| # | Source | What it holds | Use |
|---|---|---|---|
| 18 | [AICryptoVault honeypot logs](https://huggingface.co/datasets/browtastic/aicryptovault-honeypot-logs) (license "other") | Two weeks of real outside traffic to a public MCP honeypot, about 414k lines; tool calls with arguments, IP and network owner; real callers marked apart from the honeypot's own | Attack check: the framework should score these high. Almost no ordinary traffic |
| 19 | [PostHog: 63M MCP tool calls](https://posthog.com/blog/how-ai-agents-behave) | Totals only, from one busy server: tool mix, error rates per client, retry behaviour | Calibrate a simulated org's call mix |
| 20 | [hf-mcp-server/test-mcp-logs](https://huggingface.co/datasets/hf-mcp-server/test-mcp-logs) | Hugging Face's test log sink: tiny, arguments redacted, localhost callers | Only as an example of a real server's log fields |

## Announced, not released

| # | Source | What it would give | Status |
|---|---|---|---|
| 21 | TraceAegis-Bench (arXiv:2510.11203) | MCP agents in healthcare and corporate purchasing: 2,600 normal and 600 abnormal runs (steps out of order or inconsistent) | "Will become publicly available in the final paper"; ask the authors |
| 22 | ConsentBench / Conleash (arXiv:2605.11360) | 984 MCP runs about privilege escalation | No release link found |

## Looked at and left out

- **Opposite threat direction** (a malicious server attacking the agent): MCP-SafetyBench ([code](https://github.com/xjzzzzzzzz/MCPSafety)), MCPSecBench, MCPTox, [ATBench](https://huggingface.co/datasets/AI45Research/ATBench).
- **No recorded calls or no model:**
  - smoltrace-\* datasets: task lists only.
  - mcp-failure-lab-traces: a scripted client.
  - [workspace-tools-mcp](https://github.com/brian-mitchell-sec/workspace-tools-mcp): one tool call in 12 days.
  - Microsoft's mcp-for-beginners case studies: demo apps, no logs or data.

## What MCPHunt showed, and what to try next

- **Ran:** policy, static scan and runtime scoring on 61,926 calls.
- **Risky runs are not separated from benign or hard-negative ones** (AUC about 0.50 for every score). The runs make the same calls on the same paths; only the values in the files differ.
- **The leaking writes score lower than ordinary reads.** They go to `notes/`, priced at 24, while `.env` reads are priced at 75.
- **The real-clock dynamic result was an artefact.** Its 0.73 came from the behaviour layer's warm-up meeting MCPHunt's risky-first run order; shuffled, it is 0.50.
- **An independent judge on 600 calls** (`gemma3:27b`, which rates secret-carrying calls high with AUC 0.89) **barely agrees with our per-call scores overall** (Spearman 0.06):
  - it agrees well where the arguments name the asset: git 0.89, sqlite 0.77;
  - it disagrees on shell and fetch, where every call falls to the worst case;
  - it disagrees on writes that copy secrets into notes.
- **Details:** [the experiment](../../reports/experiments/gateway/mcphunt/README.md).
- **Call shape vs our simulated orgs** ([call distributions](../../reports/experiments/call_distributions/README.md)):
  - the tool mix falls off at the same geometric rate (each tool about 0.76 of the one above);
  - real agents send 37% of their calls in same-turn bursts, which our worlds never do;
  - real agents leave over half of a server's tools unused, while our worlds use every tool.

Next, in order of value for effort:

1. **False-alarm rate on ordinary traffic.** Score how often MCPHunt's benign and hard-negative runs would be flagged. The scored files already exist; no GPU.
2. **A content check on write arguments.** Flag secret-shaped values in `write_file` content, `write_query` and `create_entities`, and test it against MCPHunt's 1,272 secret-carrying calls. This is the one signal that could see the leaks; the hard negatives (look-alike values) keep it honest.
3. **Fix the filesystem register.** Add a container asset for the rest of `project_alpha/` and re-scan (about 14 minutes) to cut the 37% of calls priced at the worst case.
4. **A second outside set: MCPMark logs.** These cover GitHub, Postgres and filesystem, which overlap the existing GitHub work; use them as ordinary traffic.
5. **Attack check: the honeypot logs.** Real attackers' calls should score high.
6. **Ask the TraceAegis authors for their data.** It is the closest to the dynamic layer's question.

## References

- MCPHunt experiment: [reports/experiments/gateway/mcphunt/README.md](../../reports/experiments/gateway/mcphunt/README.md)
- MCPHunt download notes: [external/mcphunt/SOURCE.md](../../external/mcphunt/SOURCE.md)
- Published benchmarks and how this work compares: [external-benchmarks-and-positioning.md](external-benchmarks-and-positioning.md)
