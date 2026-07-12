# Real-Traffic Validation — Embedding Likelihood

Everything prior was synthetic (two testbeds from one generator family). This validates
the model's two most transfer-sensitive properties — **calibration** and the
**featurizer** — on genuinely real MCP traffic.

## The real corpus

No live third-party API was reachable (the GitHub / Slack / Google tokens in `Keys.zip`
are expired — GitHub returns 401, Slack/Calendar OAuth dead), so the standard synthetic
big-three could not be reproduced from live servers. Instead we captured a **local,
real MCP server that needs no external auth**:

- `scripts/capture_real_git_mcp.py` drives a live `uvx mcp-server-git` over stdio against
  this repository (223 real commits, ~real tracked files), issuing **400 real tool calls**
  whose arguments are drawn from the repo's actual history — real 40-char commit SHAs,
  real file paths, real branch names, varied `max_count`s.
- 399/400 executed successfully (`OK`); 12 real git tools exercised
  (`git_log`, `git_show`, `git_diff`, `git_status`, `git_diff_staged/unstaged`, …).
- Output: `logs/proxy/sessions/real_git_live/calls.csv`, standard schema.

This is real tool execution with real argument diversity (106 distinct call signatures
across 400 calls) — exactly the surface that synthetic data cannot vouch for.

## Result 1 — calibration holds on real traffic

Fit the embedding likelihood on the first 70% of the real calls (chronological), score
the held-out 30%:

- **Benign false-positive rate = 0.8%** (target ~1–2%). The q99 quantile-anchored ramp,
  tuned on the synthetic calendar/github/slack corpus, transfers to real git traffic
  without adjustment — mean held-out likelihood 0.107, i.e. essentially everything sits
  on the 0.1 floor as it should.
- Separation preserved: three injected clearly-anomalous calls (a 200-char commit
  message, a bare `git_reset`, a fake `exfiltrate_all` with a payload) all score
  likelihood **1.0** — the model still tells unusual from routine on real data.

## Result 2 — featurizer survives, with one real finding

All 400 real calls tokenized with no error, so the hashing featurizer is robust to real
argument shapes. But real data surfaced a genuine issue synthetic data hid:

- **155/400 real calls trip the `has_b64_blob` flag** — because git commit SHAs are
  40-char hex strings and match the base64 regex `[A-Za-z0-9+/]{20,}`. On a git server
  the "suspicious base64 payload" indicator is meaningless: it fires on ordinary SHAs.

This did **not** hurt calibration (the flag fires roughly uniformly across benign
traffic, so it becomes a near-constant token the SVD absorbs) — which is exactly why the
*learned, relative* design is robust where a hand-tuned rule engine would mis-fire.
Still, it argues two concrete follow-ups:

1. Gate `has_b64_blob` on decode-validity + non-hex content, or drop it — the kNN
   novelty already carries payload-anomaly signal without it.
2. It is a clean illustration for the report's thesis: server-appropriate normality is
   *learned per server*, not asserted by universal indicators.

## Honest scope

- This validates **calibration and featurizer robustness**, not attack detection on real
  data — the git capture is all-benign by construction (no real attack ground truth
  exists to capture). The injected anomalies are a separation sanity check, not a
  benchmark.
- One server, one session. The claim is narrow and true: the calibration transfers and
  the featurizer survives real argument diversity. Broader real validation needs live
  credentials (a fresh GitHub PAT would let `capture_real_git_mcp.py`'s approach extend
  to the real GitHub MCP server's 26-tool catalog).

## Reproduce

```
uv run python scripts/capture_real_git_mcp.py --repo /home/ovadyat/MCP --n 400
```
