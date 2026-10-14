# Signal Trial: Which Extra Runtime Signals Separate Misuse-Shaped Sessions?

An offline first look at signals the gateway could add beyond `cell × B × L` and the input
level. Nothing was sent to any server: three misuse-shaped sessions and one normal new
agent were built as request records from ordinary read calls and appended after the 908
real benign calls of `../github_remote/` (2026-10-14).

| Session | Built from | Shape |
|---|---|---|
| harvester | `get_file_contents` of `README.md` and `/` on 21 repositories, 1 call/s | read everything, fast |
| sweeper | `list_commits`, `list_branches`, `list_pull_requests` on every repository, 1 call/s | enumerate everything |
| prober | 30 `get_file_contents` of guessed paths in one repository, all failing | guess inside one repository |
| newdev (control) | 12 ordinary reads in one repository, one call every 5 s | normal new agent |

Each signal is computed per call, in time order, from earlier calls only. The benign test
set is the last fifth of the benign calls. Results: [`results.txt`](results.txt);
reproduce with `uv run python reports/experiments/gateway/signal_trial/trial_signals.py`.

## Findings

- **Against the real benign traffic, no per-call signal separates.** AUROC 0.06–0.66
  for risk, `B × L`, input level, repositories in the last 10 calls, calls per minute,
  windowed risk sum, tool-transition surprise, error rate and first-seen repository.
  Against the normal new agent, breadth and rate separate well (0.87).
- **The benign "CI bot" role is why.** It makes about one call a second across 18
  repositories, so harvesting looks like it. Split by role, calls per minute separates the
  planted sessions from release manager, triager and admin at 0.87–0.97, and from the CI
  bot at 0.15. A threshold has to be per caller, not one for the whole server.
- **The benign corpus cannot test breadth.** Its generator draws a repository per call, so
  a benign session touches about 8 repositories in 10 calls; real work stays in a few.
- **Windowed risk sum** was the only score that flagged the harvester (14 of 42 calls
  above the benign 99th percentile, none for the control).
- **Stand-in decoys** — the 3 repositories no benign call touches — were hit by the
  harvester (6 calls, first at call 27) and the sweeper (9, first at call 40); never by the
  prober, the control or benign traffic.
- **A per-tool `(owner, repo)` allow-list** learned from the first 80% of benign calls
  flagged 1 of 182 benign test calls, 6 of 42 harvester, 27 of 63 sweeper, 0 prober, 0 control.
- Nothing here caught the prober: guessing inside a repository the caller normally uses.

## Limits

Three planted sessions and one control are a smoke test, not an evaluation; the planted
sessions were written by us, so they show what each signal *can* catch, not how often
real misuse looks like this. The benign traffic is a replayed synthetic corpus, not real
agent sessions.
