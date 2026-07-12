# Dynamic Scoring Design

The static side (`scanner/`, `static_scoring/`, `call_scoring/`, `param_scoring/`)
answers *"how bad would this call be if it happened?"* — a design-time heatmap
over `(tool, asset)`. It cannot see the agent, the session, or whether the
specific call is normal for that agent. This document is the design for the
side that does: **dynamic scoring from captured agent logs**.

## The model: impact × likelihood, not two separate scores

- **Static = impact.** The scanned `(tool, asset)` band already answers "if this
  happens, how bad is it" (`reports/scan/<server>.json`, `call_scoring`).
- **Dynamic = likelihood / anomaly.** "How abnormal is this call, from *this*
  agent, in *this* session, given its actual input?" — derived from captured
  agent logs (`logs/proxy/sessions/*/calls.csv`), not from a benchmark.
- **Final score = static ⊗ dynamic.** Two compositions exist side by side:
  the band signals (baseline / sequence / judge) fuse via the escalation
  arithmetic the framework already uses for parameters
  (`param_scoring/combine.py::escalate`) — they can only **raise** a call's
  risk above its static floor. The **embedding likelihood**
  (`dynamic/embedding.py`) instead fills the `likelihood(1.0)` slot the v6 scan
  formula already reserves: `final_risk = static_score × likelihood`, with
  likelihood in `[0.1, 1.0]` — NIST-style impact × likelihood. Its 0.1 floor
  bounds the discount: a scanned-critical cell keeps a tenth of its risk even
  when the call looks demonstrated-normal, and a call with **no** benign
  history behind it keeps full static risk (likelihood 1.0).

This deliberately does **not** need an external labeled benchmark (see
`reports/severity_eval/SUMMARY.md` for why one barely exists for this task).
Anomaly is defined relative to an agent's *own* observed normal behavior, and
correctness is demonstrated by a **discrimination test**: does the combined
score separate labeled-benign sessions from labeled-adversarial sessions in the
synthetic testbed, where static alone does not? See
`reports/dynamic_eval/SUMMARY.md` for the current result.

## Four signals, cheap → expensive

0. **Embedding likelihood** (`src/mcp_security/dynamic/embedding.py`, no LLM).
   Embed each call (hashing vectorizer over tool + arg tokens + structural
   flags), reduce to a latent with TruncatedSVD fit on the server's observed
   history, score novelty as mean distance to the 5 nearest historical calls,
   calibrate against the history's own quantiles (q99 → z = 2), and map to a
   likelihood in `[0.1, 1.0]` that multiplies the static score. Fit on benign
   history only when labels are curated; on an unlabeled stream a label-free
   self-trimming pass (`trim_z`) drops the history calls the model itself
   flags before refitting. Fit < 0.5 s per server, scoring ~0.05 ms per call.
   Architecture comparison, calibration findings, and the full evaluation:
   `reports/dynamic_eval/embedding/EMBEDDING_LIKELIHOOD.md`.

1. **Behavioral baseline** (`src/mcp_security/dynamic/baseline.py`, no LLM).
   From an agent's/persona's own call history: which tools it normally calls,
   which assets/sensitivities it normally touches, typical call volume. A new
   call is scored by deviation — unseen tool for this persona, first-ever touch
   of a high-sensitivity asset, or a burst far above the persona's normal rate.
   This is the cheapest signal and needs no benchmark, only history.

2. **Session sequence risk** (`src/mcp_security/dynamic/sequence.py`, no LLM).
   Static and baseline are both per-call; neither sees that "read
   `customers.csv`" followed by "post to an external channel" is critical *as a
   sequence* even though each call alone is medium. Tracks cumulative
   sensitivity touched in a session and flags specific risky patterns
   (sensitive-read → external-write within a short window).

3. **LLM judge** (`src/mcp_security/dynamic/judge.py`, optional escalator).
   For calls the first two signals flag as unusual, decode/normalize the
   arguments (base64, hex, shell-variable expansion — the exact gap
   `severity_analysis.md` identified: obfuscation defeats a regex extractor) and
   ask the local model (`mcp_security.llm.ollama_client`, qwen2.5:32b) to
   classify intent. Escalation-only, same as the other signals; degrades to "no
   opinion" if Ollama is unreachable, per the project's no-cloud-fallback rule.
   Not run by default in the testbed report (would need a GPU job) — wired and
   ready, invoked opportunistically.

`src/mcp_security/dynamic/combine.py` composes all signals present via
`escalate()`, reusing `param_scoring.combine` rather than re-implementing band
arithmetic.

## Why no benchmark, and what stands in for one

Unlike the static severity work, there is no external per-call "this agent
session is malicious" ground truth to grade against. Building one honestly
would take external labeled telemetry the project doesn't have. Instead:

- **Labels come from the testbed, not a claimed oracle.** The synthetic
  multi-company sessions (`scripts/make_dynamic_testbed.py`) are generated with
  a known label (`benign` / `adversarial`) baked in by construction — the
  adversarial generator deliberately reproduces the failure cases
  `severity_analysis.md` found the static scorer blind to (base64-wrapped
  exfil, DNS tunneling, benign-tool exfil via `mail`, fork bombs).
- **The claim under test:** *does adding the dynamic signal separate benign
  from adversarial sessions better than the static score alone?* This is a
  weaker, more honest claim than "we match ground truth severity" — it is a
  relative, self-generated comparison, not an absolute one. `reports/dynamic_eval/`
  reports it explicitly as such, with the static-only baseline shown alongside.

## Layout

```
src/mcp_security/dynamic/
  embedding.py  embedding novelty -> likelihood factor (static x likelihood)
  baseline.py   per-(persona, server) profile + deviation scoring
  sequence.py   session-level cumulative/pattern risk
  judge.py      optional LLM escalation on normalized/decoded args
  combine.py    fuse static band + all present dynamic signals via escalate()
  __main__.py   CLI: score one session's calls.csv against a scan + baseline

scripts/make_dynamic_testbed.py       multi-company synthetic benign+adversarial logs
scripts/eval_embedding_likelihood.py  likelihood eval + stream/test formula CSVs
reports/dynamic_eval/                 discrimination-test report (benign vs adversarial)
reports/dynamic_eval/embedding/       likelihood eval report, metrics, formula CSVs
```

## Relationship to `tests/testbed/`

`tests/testbed/harness/scorer_bridge.py` was already scaffolded with this exact
contract (`static`, `dynamic`, `combined`) as a stub returning `None`s, waiting
for a real scorer. It now calls `mcp_security.dynamic.combine`. This makes the
live attack harness (real MCP server profiles under `tests/testbed/servers/`)
scoring-ready for whenever it's run against real servers — out of scope for
this round, which stays fully synthetic/offline per project decision.

## Non-goals

- No *supervised* classifier — nothing is ever trained on attack labels. The
  embedding likelihood is a novelty model fit on observed history only, and it
  stays auditable (hashing + SVD + nearest-neighbor distance, a two-line
  z-to-likelihood ramp), consistent with the framework's "no black-box
  scoring" stance (`docs/project/overview.md`). The band signals remain plain
  statistics over the persona's own history.
- The LLM judge stage is an escalator, never the sole basis for a score — same
  rule the static side already follows for parameters.
