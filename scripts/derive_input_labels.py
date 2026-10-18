"""Two-stage input analysis for one server's tools (v12).

Stage 1, importance (``docs/standards/tool-input-importance.md``): two questions
per input. Does it affect an asset (which asset, how much of it, who gets it,
what is done to it, when, or what is carried)? And how much can its value change
the risk of the call, ranked 1 to 5? The program, not the model, decides: an
input is kept when question 1 is yes and question 2 is ``KEEP_RANK`` or more.

- ``_VOTES`` independent passes (the first greedy and reproducible, the rest
  sampled); question 1 is decided by majority, question 2 by the median rank;
- an input no pass answered is asked again on its own, in a small batch, before
  anything is decided; one still unanswered is kept, never dropped for lack of
  an answer;
- an input the policy names in a special-value rule or a baseline row is kept
  whatever the answers.

Result: ``<server>.importance.json``.

Stage 2, rules (``docs/standards/tool-input-rules.md``): one run-time rule per
important input, turning its value into a level 1-5 (3 is a normal call). Each
rule is checked by ``mcp_security.input_rules.rule_problems`` as it arrives; an
input whose rule is missing or broken is asked again, alone. Result:
``<server>.json``, every input present, the important ones with their rule. At
run time ``mcp_security.input_rules.evaluate_call`` takes the max over a call's
inputs.

Both stages receive the slice of the organization's policy that applies to the
tool (``policy_context.py``); stage 2 also sees each asset's scanned level.
``--no-policy`` sends an empty policy, the ablation that shows what it adds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from input_feature_facts import facts_for  # noqa: E402
from mcp_catalogs import CATALOGS, REPO as CAT_REPO, load_tools  # noqa: E402
from mcp_security.input_rules import rule_problems  # noqa: E402
from mcp_security.llm.ollama_client import DEFAULT_OPTIONS, query_ollama  # noqa: E402
from policy_context import POLICY_SECTIONS, policy_for_tool, with_scanned_levels  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
STANDARDS = REPO / "docs" / "standards"
IMPORTANCE_PROMPT = STANDARDS / "tool-input-importance.md"
RULES_PROMPT = STANDARDS / "tool-input-rules.md"
V12 = REPO / "reports" / "experiments" / "v12"

IMPORTANCE_PLACEHOLDERS = ("{tool_json}", "{inputs_json}", "{policy_json}")
CONTEXT_PLACEHOLDERS = IMPORTANCE_PLACEHOLDERS + ("{context_inputs_json}",)

CLASSIFICATIONS = {"RANGE", "ASSET", "CONTENT", "MODE"}
_IMPORTANCE_KEYS = {"path", "affects_asset", "rank", "reason"}
EFFECTS = {"which", "how_much", "who", "action", "when", "carried", "none"}
#: Question 2 threshold: rank 3 means the riskiest value makes an ordinary call
#: clearly riskier. An input must also affect an asset (question 1) to be kept.
KEEP_RANK = 3
_RULE_KEYS = {"path", "classification", "rule", "source", "reason"}
_VOTES = 3  # independent stage 1 passes: majority for question 1, median for question 2
_VOTE_TEMPERATURE = 0.5  # sampled votes, for diversity
_RETRIES = 2  # shape-only retries within one pass
_RULE_ROUNDS = 3  # stage 2: re-ask inputs whose rule is missing or broken
_IMPORTANCE_BATCH = 25  # replies are two short answers and a sentence per input
_REASK_BATCH = 5  # inputs no pass answered, asked again in small batches
_RULES_BATCH = 8  # rules are longer than v11's flags

logger = logging.getLogger("derive_input_labels")


def _run_dir() -> Path:
    """This run's folder: pinned by the sbatch script, else the next free number.

    Stage 2 reads the importance file from the same folder, so a stage-2-only run
    must pin it with ``MCP_INPUT_LABELS_OUT``."""
    pinned = os.environ.get("MCP_INPUT_LABELS_OUT")
    if pinned:
        return Path(pinned)
    used = [int(d.name[3:]) for d in V12.glob("run*") if d.name[3:].isdigit()]
    return V12 / f"run{max(used, default=0) + 1}"


OUT_DIR = _run_dir()


# --------------------------------------------------------------------------- plumbing


def _load_prompt(path: Path, placeholders: tuple[str, ...]) -> str:
    """A prompt's text, read once so the sha256 snapshot is honest."""
    text = path.read_text(encoding="utf-8").rstrip()
    for placeholder in placeholders:
        if placeholder not in text:
            raise SystemExit(f"{path.name} has no {placeholder} placeholder")
    return text


def _snapshot(text: str, source: Path, filename: str) -> str:
    """Write a prompt beside the results; return its digest."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(text.encode()).hexdigest()
    tmp = OUT_DIR / f".{filename}-{os.getpid()}.tmp"
    tmp.write_text(f"<!-- sha256: {digest} · source: {source.relative_to(REPO)} -->\n\n{text}")
    tmp.replace(OUT_DIR / filename)
    return digest


def _fill(template: str, tool: dict, inputs: dict, policy: dict, context: dict | None = None):
    text = template.replace("{tool_json}", json.dumps(
        {"tool_name": tool["tool_name"], "description": tool.get("description", "")}, indent=1))
    text = text.replace("{inputs_json}", json.dumps(inputs, indent=1))
    if context is not None:
        text = text.replace("{context_inputs_json}", json.dumps(context, indent=1))
    return text.replace("{policy_json}", json.dumps(policy, indent=1))


def _batched(items: dict, size: int) -> list[dict]:
    pairs = list(items.items())
    return [dict(pairs[i:i + size]) for i in range(0, len(pairs), size)]


def _root(path: object) -> str:
    return str(path).split(".")[0].split("[")[0]


def _match(path: object, keys) -> str | None:
    """The key in ``keys`` that ``path`` names, ignoring ``[]`` list markers.

    An input that may be one value or a list (calendar's ``account``) is a single
    schema key, but the prompts tell the model to write list items as
    ``account[]``. Exact match wins; otherwise the first key equal up to ``[]``."""
    if path in keys:
        return str(path)
    bare = str(path).replace("[]", "")
    return next((k for k in keys if k.replace("[]", "") == bare), None)


def _options(seed: int, attempt: int) -> dict | None:
    """Decoding options. Seed 0, first attempt: greedy and reproducible. Any
    other pass or retry samples, since repeating a greedy prompt returns the
    same reply."""
    if seed == 0 and attempt == 0:
        return None
    return {**DEFAULT_OPTIONS, "temperature": _VOTE_TEMPERATURE, "seed": seed * 10 + attempt + 1}


def _keep_rejected(reply, label: str, attempt: int) -> None:
    """Save a rejected reply so a failure can be read rather than guessed at.
    ``null`` means the model's text held no parseable JSON object at all."""
    folder = OUT_DIR / "logs" / "rejected"
    folder.mkdir(parents=True, exist_ok=True)
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
    (folder / f"{slug}-attempt{attempt + 1}.json").write_text(json.dumps(reply, indent=1))


def _ask(prompt: str, required: set[str], props: dict, label: str, seed: int = 0):
    """Rows from the model, or None after every retry gave an unusable reply.

    Only the reply's shape is checked here: a dict with an ``arguments`` list
    whose rows carry ``required`` keys and name a declared input. Which rows
    answer which input is settled by the caller with ``_match``."""
    for attempt in range(1 + _RETRIES):
        reply = query_ollama(prompt, options=_options(seed, attempt))
        if (isinstance(reply, dict) and isinstance(reply.get("arguments"), list)
                and all(isinstance(a, dict) and required.issubset(a)
                        and _root(a["path"]) in props for a in reply["arguments"])):
            return reply["arguments"]
        logger.warning("     attempt %d: no usable JSON for %s", attempt + 1, label)
        _keep_rejected(reply, f"{label}-seed{seed}", attempt)
    return None


def _policy(server: str, tool_name: str, no_policy: bool) -> dict:
    """The tool's policy slice; empty for the ablation or a server with no policy."""
    if no_policy or server not in POLICY_SECTIONS:
        return {}
    return policy_for_tool(server, tool_name)


def _catalog_block(server: str) -> dict:
    catalog = CATALOGS[server]
    return {"server": server,
            "catalog": {"path": str(catalog.path.relative_to(CAT_REPO)),
                        "sha256": hashlib.sha256(catalog.path.read_bytes()).hexdigest(),
                        "package": catalog.package, "captured": catalog.captured},
            "slurm_job": os.environ.get("SLURM_JOB_ID", "")}


# --------------------------------------------------------------------------- stage 1


def _valid_answer(row: dict) -> bool:
    rank = row.get("rank")
    return (isinstance(row.get("affects_asset"), bool) and isinstance(rank, int)
            and not isinstance(rank, bool) and 1 <= rank <= 5)


def _answers(template: str, tool: dict, inputs: dict, policy: dict, props: dict, seed: int,
             batch_size: int):
    """One pass over ``inputs``: fact key -> its two answers; None if a batch failed."""
    answers: dict[str, dict] = {}
    for batch in _batched(inputs, batch_size):
        got = _ask(_fill(template, tool, batch, policy), _IMPORTANCE_KEYS, props,
                   f"{tool['tool_name']}-importance", seed)
        if got is None:
            return None
        for row in got:
            key = _match(row["path"], batch)
            if key is not None and key not in answers and _valid_answer(row):
                effect = row.get("effect") if row.get("effect") in EFFECTS else None
                answers[key] = {"affects_asset": row["affects_asset"], "rank": row["rank"],
                                "effect": effect, "reason": str(row["reason"])}
    return answers


def _reask(template: str, tool: dict, facts: dict, votes: list, policy: dict, props: dict):
    """Ask again, in small batches, for the inputs no pass answered.

    Long tools are sent 25 inputs at a time, and the model sometimes skips deep
    nested ones. Rather than keep those by default, they get one more greedy
    pass on their own; its answers count as one more vote."""
    missing = {k: v for k, v in facts.items()
               if not any(vote is not None and k in vote for vote in votes)}
    if not missing:
        return None
    return _answers(template, tool, missing, policy, props, 0, _REASK_BATCH)


def _median(values: list[int]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    return float(ordered[mid]) if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def importance_rows(facts: dict, votes: list[dict | None]) -> list[dict]:
    """One decision per input from the two questions.

    Question 1 (affects an asset) by majority of the answering passes, question
    2 (rank 1-5) by their median. Kept when question 1 is yes and the median
    rank is ``KEEP_RANK`` or more. An input no pass answered is kept."""
    rows = []
    for key in facts:
        said = [v.get(key) for v in votes if v is not None]
        answered = [a for a in said if a is not None]
        if not answered:
            rows.append({"path": key, "important": True, "decided_by": "default",
                         "reason": "no pass answered this input; kept by default",
                         "affects_asset": None, "rank": None, "effect": None, "answers": said})
            continue
        affects = sum(a["affects_asset"] for a in answered) > len(answered) / 2
        rank = _median([a["rank"] for a in answered])
        effects = [a["effect"] for a in answered if a["affects_asset"] == affects and a["effect"]]
        effect = max(set(effects), key=effects.count) if effects else None
        keep = affects and rank >= KEEP_RANK
        agreeing = [a["reason"] for a in answered
                    if a["affects_asset"] == affects and (a["rank"] >= KEEP_RANK) == keep]
        rows.append({"path": key, "important": keep, "decided_by": "two_questions",
                     "reason": (agreeing or [answered[0]["reason"]])[0],
                     "affects_asset": affects, "rank": rank, "effect": effect, "answers": said})
    return rows


def _leaf(path: str) -> str:
    """The input's own name, without its parents or list markers (``guestsCanModify``)."""
    return path.split(".")[-1].replace("[]", "")


def policy_named(policy: dict, facts: dict) -> set[str]:
    """Fact keys the policy names in a special-value rule or a baseline row.

    The organization said these matter, so stage 1 keeps them whatever the
    answers say. Names are read from the backticked inputs of the rule's
    ``arguments`` cell and matched with or without ``[]`` markers."""
    cells = [r.get("arguments", "") for r in
             policy.get("special_value_rules", []) + policy.get("baseline", [])]
    names = {n.strip() for cell in cells for n in re.findall(r"`([^`]+)`", cell)}
    return {key for key in facts if _match(key, names) is not None
            or any("." not in n and _leaf(key) == n.replace("[]", "") for n in names)}


def _apply_policy(rows: list[dict], named: set[str]) -> None:
    for row in rows:
        if row["path"] in named and not row["important"]:
            row.update(important=True, decided_by="policy",
                       reason=f"named by the policy for this tool; {row['reason']}")


def run_importance(server: str, no_policy: bool) -> int:
    """Stage 1: the two questions for every input of every tool."""
    template = _load_prompt(IMPORTANCE_PROMPT, IMPORTANCE_PLACEHOLDERS)
    digest = _snapshot(template, IMPORTANCE_PROMPT, "prompt-importance-AS-RUN.md")
    results, failed, no_schema = [], [], []
    for tool in load_tools(server):
        name = tool["tool_name"]
        props = (tool["input_schema"] or {}).get("properties", {})
        if not props:
            no_schema.append(name)
            results.append({"tool_name": name, "arguments": [], "no_declared_schema": True})
            continue
        policy = _policy(server, name, no_policy)
        facts = facts_for(tool["input_schema"])
        votes = [_answers(template, tool, facts, policy, props, seed, _IMPORTANCE_BATCH)
                 for seed in range(_VOTES)]
        if all(v is None for v in votes):
            failed.append(name)
            continue
        reasked = _reask(template, tool, facts, votes, policy, props)
        if reasked:
            votes.append(reasked)
        rows = importance_rows(facts, votes)
        _apply_policy(rows, policy_named(policy, facts))
        kept = [r["path"] for r in rows if r["important"]]
        logger.info("  [1] %s: %d of %d input(s) kept (policy %d)", name, len(kept), len(rows),
                    sum(r["decided_by"] == "policy" for r in rows))
        results.append({"tool_name": name, "arguments": rows, "shortlist": kept,
                        "votes_failed": sum(v is None for v in votes)})
    out = OUT_DIR / f"{server}.importance.json"
    out.write_text(json.dumps({
        **_catalog_block(server), "prompt_sha256": digest, "prompt": "prompt-importance-AS-RUN.md",
        "votes": _VOTES, "keep_rank": KEEP_RANK,
        "policy_section": None if no_policy else POLICY_SECTIONS.get(server),
        "tools": results, "failed": failed, "no_declared_schema": no_schema}, indent=2))
    logger.info("wrote %s: %d tool(s), %d failed", out, len(results), len(failed))
    return 1 if failed else 0


# --------------------------------------------------------------------------- stage 2


def _rules_tool(template: str, tool: dict, facts: dict, importance: dict, policy: dict,
                props: dict) -> tuple[dict, dict]:
    """Rules for the important inputs: (path -> rule row, path -> last problems).

    Each round asks only the inputs still without a usable rule, so one broken
    rule never costs the rest of the tool its answers."""
    asked = {p: {**facts[p], "why_important": importance[p]["reason"],
                 **({"effect": importance[p]["effect"]} if importance[p].get("effect") else {})}
             for p in importance if importance[p]["important"] and p in facts}
    context = {p: {"description": f.get("description")} for p, f in facts.items()
               if p not in asked}
    tool_paths = frozenset(facts)
    rules: dict[str, dict] = {}
    problems: dict[str, list[str]] = {}
    for round_ in range(_RULE_ROUNDS):
        pending = {p: v for p, v in asked.items() if p not in rules}
        if not pending:
            break
        for batch in _batched(pending, _RULES_BATCH):
            got = _ask(_fill(template, tool, batch, policy, context), _RULE_KEYS, props,
                       f"{tool['tool_name']}-rules-round{round_ + 1}", seed=round_)
            for row in got or []:
                key = _match(row["path"], batch)
                if key is None or key in rules:
                    continue
                row = {**row, "path": key}
                found = rule_problems(row, tool_paths)
                if row.get("classification") not in CLASSIFICATIONS:
                    found.append("unknown classification")
                if found:
                    problems[key] = found
                else:
                    rules[key] = row
                    problems.pop(key, None)
    return rules, problems


def run_rules(server: str, no_policy: bool) -> int:
    """Stage 2: one run-time rule per important input."""
    importance_file = OUT_DIR / f"{server}.importance.json"
    if not importance_file.exists():
        raise SystemExit(f"no importance file at {importance_file}; run stage 1 first "
                         "(pin the folder with MCP_INPUT_LABELS_OUT)")
    stage1 = {t["tool_name"]: t for t in json.loads(importance_file.read_text())["tools"]}
    template = _load_prompt(RULES_PROMPT, CONTEXT_PLACEHOLDERS)
    digest = _snapshot(template, RULES_PROMPT, "prompt-rules-AS-RUN.md")
    results, failed = [], []
    for tool in load_tools(server):
        name = tool["tool_name"]
        rated = stage1.get(name)
        if rated is None:  # stage 1 failed for this tool
            failed.append(name)
            continue
        if not rated["arguments"]:
            results.append({"tool_name": name, "arguments": [], "no_declared_schema": True})
            continue
        importance = {r["path"]: r for r in rated["arguments"]}
        facts = facts_for(tool["input_schema"])
        props = (tool["input_schema"] or {}).get("properties", {})
        policy = (with_scanned_levels(_policy(server, name, no_policy), server)
                  if server in POLICY_SECTIONS and not no_policy else {})
        rules, problems = (_rules_tool(template, tool, facts, importance, policy, props)
                           if rated["shortlist"] else ({}, {}))
        missing = [p for p in rated["shortlist"] if p not in rules]
        logger.info("  [2] %s: rules for %d of %d important input(s)", name,
                    len(rated["shortlist"]) - len(missing), len(rated["shortlist"]))
        if missing:
            logger.warning("     %s: no usable rule for %s", name, missing)
        merged = [{"path": p, "important": imp["important"], "important_reason": imp["reason"],
                   **{k: v for k, v in rules.get(p, {}).items() if k != "path"}}
                  for p, imp in importance.items()]
        results.append({"tool_name": name, "policy_slice": policy, "arguments": merged,
                        "shortlist": rated["shortlist"], "missing_rules": missing,
                        "rule_problems": problems})
    out = OUT_DIR / f"{server}.json"
    out.write_text(json.dumps({
        **_catalog_block(server), "prompt_sha256": digest, "prompt": "prompt-rules-AS-RUN.md",
        "policy_section": None if no_policy else POLICY_SECTIONS.get(server),
        "importance_file": importance_file.name, "tools": results, "failed": failed}, indent=2))
    logger.info("wrote %s: %d tool(s), %d failed", out, len(results), len(failed))
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server", required=True, choices=sorted(CATALOGS),
                    help="servers without an abstract-template policy run with an empty one")
    ap.add_argument("--stage", choices=("importance", "rules", "both"), default="importance",
                    help="importance: stage 1 only (default, so it can be reviewed); "
                         "rules: stage 2 from an existing importance file; both: in sequence")
    ap.add_argument("--no-policy", action="store_true", help="send an empty policy (the ablation)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s %(message)s")
    rc = 0
    if args.stage in ("importance", "both"):
        rc |= run_importance(args.server, args.no_policy)
    if args.stage in ("rules", "both"):
        rc |= run_rules(args.server, args.no_policy)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
