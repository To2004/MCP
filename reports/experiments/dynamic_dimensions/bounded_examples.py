"""Worked scenarios for the per-dimension formula in DIMENSION_FORMULAS.md (no bits, no clipping).

Per dimension, a score s between 0 and 1 (0.5 = "twice his normal", the edge of ordinary):
    more than usual   s = value / (value + TOLERANCE x his average)
    rarer than usual  share = (n + 1) / (N + K),  K = different values he has used + 1
                      s = 1 / (1 + TOLERANCE x K x share)
    policy rule       s = the policy's value (default 0.9)
The strangest dimension decides: S = max s.  Multiplier M = 5^(2S-1) above 0.5, 0.7^(1-2S) below,
so M is between 0.7 and 5 and the risk static (1-5) x M between 0.7 and 25.
Warm-up: until the agent has WARMUP calls, M = 1 (still learning).

Run:  python bounded_examples.py
"""
TOLERANCE, WARMUP, RULE = 2.0, 5, 0.9
MAX_M, MIN_M = 5.0, 0.7
AVG = {"calls_1h": 12, "repeat_10m": 1.6, "size": 400}      # his 90-day averages


def more(value: float, avg: float) -> float:
    return value / (value + TOLERANCE * avg)


def rarer(n: int, total: int, used: int) -> float:
    k = used + 1
    return 1 / (1 + TOLERANCE * k * (n + 1) / (total + k))


def multiplier(s: float) -> float:
    return MAX_M ** (2 * s - 1) if s >= 0.5 else MIN_M ** (1 - 2 * s)


def case(name, tool_n, hour_n, asset_n, calls, rep, size, rules=(), total=3000, used=(12, 4, 40)):
    if total < WARMUP:
        print(f"{name:<38} warm-up ({total} of {WARMUP} calls): M = 1.00")
        return
    s = {"tool share": rarer(tool_n, total, used[0]), "time of day": rarer(hour_n, total, used[1]),
         "asset share": rarer(asset_n, total, used[2]), "calls in hour": more(calls, AVG["calls_1h"]),
         "same tool 10 min": more(rep, AVG["repeat_10m"]), "request size": more(size, AVG["size"])}
    for r in rules:
        s[r] = RULE
    top = max(s, key=lambda k: s[k])
    m = multiplier(s[top])
    print(f"{name:<38} strangest: {top:<17} S={s[top]:.2f}  M={m:.2f}  "
          f"R: static1 {m:.2f} | static3 {3 * m:.2f} | static5 {5 * m:.2f}")


case("Ordinary call", 600, 900, 150, 14, 2, 420)
case("Very familiar call", 1050, 1050, 450, 6, 1, 300)
case("Busy hour: 2x his usual calls", 600, 900, 150, 24, 2, 420)
case("Loop: same tool 40x in 10 min", 600, 900, 150, 55, 40, 420)
case("Off-role: tool never used", 0, 900, 150, 14, 1, 420)
case("Rarely used tool (1% of his calls)", 30, 900, 150, 14, 1, 420)
case("3 am call", 600, 0, 150, 3, 1, 420)
case("Big request 12 KB (usually 400 B)", 600, 900, 150, 14, 1, 12000, rules=("request > 10 KB",))
case("New IP (rule)", 600, 900, 150, 14, 2, 420, rules=("first-time IP",))
case("New user, 3 calls, new tool", 0, 1, 1, 3, 1, 420, total=3, used=(1, 1, 1))
case("New user, 5 calls, new tool", 0, 2, 2, 5, 1, 420, total=5, used=(2, 1, 2))
case("New user, 10 calls, new tool", 0, 4, 4, 6, 1, 420, total=10, used=(3, 2, 3))
case("New user, 50 calls, new tool", 0, 20, 10, 8, 1, 420, total=50, used=(5, 3, 6))
