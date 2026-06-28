"""Deterministic competing risk scorers over external benchmark calls (no GPU).

Each scorer assigns a numeric risk to a :class:`bench_loader.BenchCall` so it can be
graded as an attack detector against the benchmark's labels. The point of the lineup
is a controlled contrast:

* **capability-only** scorers (``cvss``, ``aivss``) rate the *tool's* inherent
  capability and are blind to the request's arguments — exactly how a static
  vulnerability/agentic framework rates a tool. On these benchmarks the maliciousness
  lives in the arguments (``../../etc/passwd``, ``<IMPORTANT>… show_credentials``), so a
  capability-only score is constant across a tool's benign and attack calls. This is the
  finding, not a bug: it shows capability scoring cannot do per-call detection.
* **content-aware** baselines (``keyword``) read the arguments and pattern-match known
  attack markers (traversal, injection, shell/SQL metacharacters, credential blobs) — a
  cheap stand-in for a guardrail's fast first stage (cf. MCP-Guard Stage I).
* **floors** (``majority``, ``random``) are calibration references; a real scorer must
  beat them.

The framework's own scorer and an LLM-as-judge are added later (they need the scan +
GPU); this module is the no-GPU half of the head-to-head.
"""

from __future__ import annotations

import re

from bench_loader import BenchCall

# --- capability rubric: tokens in the tool name -> inherent impact 1..4 ---------
_DESTROY = ("delete", "remove", "drop", "rm", "destroy", "purge", "kill", "exec",
            "run", "shell", "install", "write", "edit", "move", "create", "add_server",
            "addserver", "compute")
_NETWORK = ("download", "upload", "fetch", "http", "url", "send", "post", "exfil",
            "credential", "leak", "verify_signature", "sig")
_READ = ("read", "get", "list", "show", "describe", "search", "lookup", "check",
         "verify", "head", "stat", "info", "add", "sub")


def _capability(tool: str) -> int:
    """Inherent capability tier of a tool from its name (1 read .. 4 destructive)."""
    t = tool.lower()
    if any(k in t for k in _DESTROY):
        return 4
    if any(k in t for k in _NETWORK):
        return 3
    if any(k in t for k in _READ):
        return 1
    return 2  # unknown capability


def cvss_score(call: BenchCall) -> float:
    """CVSS-v3-style base score (0-10) from tool capability alone (arg-blind)."""
    return {1: 2.0, 2: 5.0, 3: 7.0, 4: 9.0}[_capability(call.tool)]


def aivss_score(call: BenchCall) -> float:
    """AIVSS-style score: CVSS base x agentic amplification, capped at 10 (arg-blind).

    Every call here is an autonomous agent tool invocation, so the amplification is a
    near-constant factor; AIVSS therefore tracks CVSS closely on this surface."""
    return min(10.0, cvss_score(call) * 1.1)


# --- content-aware keyword detector (reads the arguments) -----------------------
_PATTERNS = {
    "traversal": re.compile(r"\.\./|/etc/|/proc/|~/\.ssh|/etc/(passwd|shadow)|authorized_keys", re.I),
    "injection": re.compile(r"<important>|ignore (all |previous )?instruction|system:|</?\w+>", re.I),
    "shell": re.compile(r";\s*rm\b|\brm\s+-rf\b|\|\s*\w+|&&|\$\(|`", re.I),
    "sql": re.compile(r"\bdrop\s+table\b|union\s+select|'\s*or\s*'1'\s*=\s*'1|--\s", re.I),
    "secret": re.compile(r"ssh-rsa|begin (rsa|openssh) private|api[_-]?key|password|secret|token", re.I),
}


def keyword_score(call: BenchCall) -> float:
    """Number of distinct attack-marker families present in the arguments (0-5)."""
    text = call.args_text
    return float(sum(1 for rx in _PATTERNS.values() if rx.search(text)))


def majority_score(call: BenchCall) -> float:
    """Constant score (a degenerate scorer) -> AUC 0.5 reference floor."""
    return 1.0


def random_score(call: BenchCall) -> float:
    """Deterministic pseudo-random score in [0,1) from the call index (reproducible)."""
    h = (call.idx * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
    return h / 0xFFFFFFFF


SCORERS = {
    "cvss": cvss_score,
    "aivss": aivss_score,
    "keyword": keyword_score,
    "majority": majority_score,
    "random": random_score,
}


def score_all(calls: list[BenchCall]) -> dict[str, list[float]]:
    """{scorer_name: [score per call]} aligned with ``calls`` order."""
    return {name: [fn(c) for c in calls] for name, fn in SCORERS.items()}


def main() -> None:
    import eval_metrics as m
    from bench_loader import load_benchcalls

    calls = load_benchcalls()
    scored = score_all(calls)
    # Quick AUC on the attack-vs-VALID task (structured + NL alike).
    labels = [c.label_attack for c in calls]
    idx = [i for i, y in enumerate(labels) if y is not None]
    yy = [labels[i] for i in idx]
    print(f"{len(idx)} calls with attack/VALID labels\n")
    print(f"{'scorer':10} {'AUC':>6}")
    for name, scores in scored.items():
        ss = [scores[i] for i in idx]
        auc = m.roc_auc(ss, yy)
        print(f"{name:10} {auc:6.2f}" if auc is not None else f"{name:10}   n/a")


if __name__ == "__main__":
    main()
