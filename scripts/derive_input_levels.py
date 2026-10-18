"""One-step input levels for one server's tools (v13).

For each input of each tool, the model names what the input decides, then
either writes a rule that turns the input's value into a level 1 to 5,
reaching every level, or answers ``null`` (``docs/standards/tool-input-levels.md``).
The program keeps an input when its rule passes
``mcp_security.input_rules.rule_problems`` with ``all_levels``; an input with no
answer, a broken rule or a level gap is asked again on its own, sampled, up to
``_ROUNDS`` passes in all. An input with fewer than five possible values (a
boolean, a short enum) cannot reach five levels: the program answers ``null``
for it without asking. There is no separate importance stage and no voting.

The model sees everything the organization's policy says that applies to the
tool (``policy_context.org_for_tool``): its description and normal workflow, the
assets the tool can reach with their scanned level, the special-value rules and
baseline rows naming the tool, and the rest of the asset register by name and
level; plus which levels those assets reach and which ones name words must add.
The model turns what the policy says into levels; numbers and cut-offs the
policy does not give are its own.

Before checking a rule the program repairs it (``mcp_security.input_rules.repairs``):
an asset-name rule looks names up in the policy's whole register, whatever the
tool, and keeps the model's name words only at levels no asset reaches; a text
rule gets the credential words at level 5.

Result: ``<server>.json`` in the run folder, one row per input with its
``status`` (``rule``, ``null``, ``broken`` or ``unanswered``); the shape
``scripts/evaluate_input_rules.py`` reads.

Usage::

    MCP_INPUT_LEVELS_OUT=reports/experiments/v13/run1 \\
        uv run python scripts/derive_input_levels.py --server github -v
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
from mcp_security.input_rules import (  # noqa: E402
    ORDINARY_TOP,
    drop_clashing_name_words,
    dropped_name_words,
    rule_problems,
    with_credential_words,
    with_register_assets,
)
from mcp_security.llm.ollama_client import DEFAULT_OPTIONS, query_ollama  # noqa: E402
from policy_context import POLICY_SECTIONS, org_for_tool, register_assets  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
#: The prompt; ``MCP_INPUT_LEVELS_PROMPT`` points to another file (an earlier
#: run's ``prompt-levels-AS-RUN.md``) to rerun it with the current code.
PROMPT = Path(os.environ.get("MCP_INPUT_LEVELS_PROMPT")
              or REPO / "docs" / "standards" / "tool-input-levels.md")
PROMPT_SNAPSHOT = "prompt-levels-AS-RUN.md"
V13 = REPO / "reports" / "experiments" / "v13"
PLACEHOLDERS = ("{tool_json}", "{inputs_json}", "{context_inputs_json}", "{policy_json}")
_REQUIRED_KEYS = {"path", "rule", "reason"}
_ROUNDS = 6  # the first pass, then up to five re-asks of the few inputs still without a rule
_BATCH = 10  # a rule is a few lines; ten inputs fit one reply
_REASK_BATCH = 3  # re-asks go out in small batches, the problems quoted
_SAMPLED_TEMPERATURE = 0.5  # a re-ask must sample: a greedy repeat returns the same reply
#: An input with fewer possible values than this cannot reach five levels.
FIVE_LEVELS = 5
#: Name endings that make two inputs the ends of one read window (``timeMin`` and
#: ``timeMax``). An event's own ``start`` and ``end`` are not a read window: when a
#: meeting happens is rated by the hour of day.
WINDOW_PAIRS = (("min", "max"), ("after", "before"), ("since", "until"), ("from", "to"))
LEVELS = (1, 2, 3, 4, 5)
#: "with no `filter_in_channel`" in a policy row: leaving that input out is the risk.
_LEFT_OUT = re.compile(r"\bno `([^`]+)`")
#: The lowest ``when_absent`` for an input the policy names as risky when left out (unusual).
POLICY_ABSENT_FLOOR = 4
#: Input names that only page, sort or set a time zone: no rule, decided without asking.
#: Compared with the last part of the path, lowercased, ``_`` removed.
PAGING_AND_DISPLAY = frozenset({
    "cursor", "nextcursor", "page", "pagetoken", "nextpagetoken", "offset", "timezone", "tz",
    "sort", "sortby", "sortorder", "orderby"})
#: Last words of an input name that make it an identifier: ``channel_id``,
#: ``calendarId``, ``pull_number``. The policy tells one id from another only
#: when the id names an asset of its register.
ID_WORDS = frozenset({"id", "ids", "number", "numbers"})
_WORD = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")
#: Input names that hold an email address; their rule is the fixed ``email`` ladder.
EMAIL_NAMES = frozenset({"email", "emails", "emailaddress"})
EFFECTS = ("which", "how_much", "who", "action", "when", "carried", "none")
#: The reply's shape, enforced by the server while the model writes: ``reason``
#: comes before ``rule``, so the model says what decides the levels first.
REPLY_SCHEMA = {
    "type": "object",
    "properties": {"inputs": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "effect": {"type": "string", "enum": list(EFFECTS)},
            "reason": {"type": "string"},
            "rule": {"anyOf": [{"type": "object"}, {"type": "null"}]},
            "when_absent": {"anyOf": [{"type": "integer", "minimum": 1, "maximum": 5},
                                      {"type": "null"}]}},
        "required": ["path", "effect", "reason", "rule", "when_absent"]}}},
    "required": ["inputs"],
}

logger = logging.getLogger("derive_input_levels")


def _run_dir() -> Path:
    """This run's folder: pinned with ``MCP_INPUT_LEVELS_OUT``, else the next free number."""
    pinned = os.environ.get("MCP_INPUT_LEVELS_OUT")
    if pinned:
        return Path(pinned)
    used = [int(d.name[3:]) for d in V13.glob("run*") if d.name[3:].isdigit()]
    return V13 / f"run{max(used, default=0) + 1}"


# --------------------------------------------------------------------------- plumbing


def load_prompt() -> str:
    """The prompt's text, checked for its placeholders. The digest line an
    ``AS-RUN`` snapshot starts with is not part of the prompt and is dropped."""
    text = PROMPT.read_text(encoding="utf-8").rstrip()
    if text.startswith("<!-- sha256:"):
        text = text.split("\n", 1)[1].lstrip("\n")
    for placeholder in PLACEHOLDERS:
        if placeholder not in text:
            raise SystemExit(f"{PROMPT.name} has no {placeholder} placeholder")
    return text


def snapshot(text: str, out_dir: Path) -> str:
    """Write the prompt as run beside the results; return its digest."""
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(text.encode()).hexdigest()
    tmp = out_dir / f".{PROMPT_SNAPSHOT}-{os.getpid()}.tmp"
    source = PROMPT.relative_to(REPO) if PROMPT.is_relative_to(REPO) else PROMPT
    tmp.write_text(f"<!-- sha256: {digest} · source: {source} -->\n\n{text}")
    tmp.replace(out_dir / PROMPT_SNAPSHOT)
    return digest


def fill(template: str, tool: dict, inputs: dict, context: dict, org: dict) -> str:
    """The prompt for one batch of one tool's inputs."""
    text = template.replace("{tool_json}", json.dumps(
        {"tool_name": tool["tool_name"], "description": tool.get("description", "")}, indent=1))
    text = text.replace("{inputs_json}", json.dumps(inputs, indent=1))
    text = text.replace("{context_inputs_json}", json.dumps(context, indent=1))
    return text.replace("{policy_json}", json.dumps(org, indent=1))


def with_level_hint(org: dict, register: dict[str, int]) -> dict:
    """``org`` plus the levels the register's assets reach and the ones name words must add.

    A ``register`` rule needs an entry at every level; the assets' scanned
    levels count, so the model is told exactly which levels are left to it."""
    levels = set(register.values())
    if not levels:
        return org
    return {**org, "asset_levels": sorted(levels),
            "name_words_needed_for": [lv for lv in LEVELS if lv not in levels]}


def batched(items: dict, size: int) -> list[dict]:
    """``items`` split into dicts of at most ``size`` entries, order kept."""
    pairs = list(items.items())
    return [dict(pairs[i:i + size]) for i in range(0, len(pairs), size)]


def match_path(path: object, keys) -> str | None:
    """The key in ``keys`` that ``path`` names, ignoring ``[]`` list markers."""
    if path in keys:
        return str(path)
    bare = str(path).replace("[]", "")
    return next((k for k in keys if k.replace("[]", "") == bare), None)


def choices(fact: dict) -> int | None:
    """How many values the schema allows: 2 for a boolean, the enum's size, else None."""
    if fact.get("enum"):
        return len(fact["enum"])
    if "boolean" in (fact.get("type") or []):
        return 2
    return None


def is_switch(fact: dict) -> bool:
    """True when the schema allows fewer than five values: no rule can reach five levels."""
    n = choices(fact)
    return n is not None and n < FIVE_LEVELS


def _last_name(path: str) -> str:
    return path.replace("[]", "").rsplit(".", 1)[-1].casefold().replace("_", "")


def is_identifier(path: str) -> bool:
    """True when the input's name ends in ``id`` or ``number``: ``channel_id``,
    ``eventId``, ``pull_number``, ``calendars[].id``."""
    last = path.replace("[]", "").rsplit(".", 1)[-1]
    words = [w.casefold() for w in _WORD.findall(last)]
    return bool(words) and words[-1] in ID_WORDS


def named_by_policy(org: dict, facts: dict) -> frozenset[str]:
    """Inputs a special-value rule or a baseline row of the policy names."""
    rows = [*org.get("special_value_rules", []), *org.get("baseline", [])]
    names = {n for row in rows for n in re.findall(r"`([^`]+)`", str(row.get("arguments", "")))}
    return frozenset(p for n in names if (p := match_path(n, facts)) is not None)


def _number_typed(fact: dict) -> bool:
    return bool({"integer", "number"} & set(fact.get("type") or []))


def decided_by_program(path: str, fact: dict,
                       policy_named: frozenset[str] = frozenset()) -> dict | None:
    """The row for an input the program decides without asking, or None.

    Fewer than five values (no five levels), paging, sorting or a time zone
    (no rule), a record number the policy does not name (an issue or pull
    request number is never an asset's name), and an email address (the fixed
    ladder)."""
    if is_identifier(path) and _number_typed(fact) and path not in policy_named:
        return {"path": path, "status": "null", "important": False, "effect": "none",
                "reason": "a record number: the policy cannot tell one from another; "
                          "decided by the program"}
    if is_switch(fact):
        return {"path": path, "status": "null", "important": False, "effect": None,
                "reason": "fewer than five possible values; decided by the program"}
    name = _last_name(path)
    if name in PAGING_AND_DISPLAY:
        return {"path": path, "status": "null", "important": False, "effect": "none",
                "reason": "paging, sorting or a time zone; decided by the program"}
    if (fact.get("format") == "email" or name in EMAIL_NAMES) and "array" not in (
            fact.get("type") or []):
        return {"path": path, "rule": {"kind": "email"}, "when_absent": None, "status": "rule",
                "important": True, "effect": "who",
                "reason": "an email address: the fixed ladder; decided by the program"}
    return None


def invented_values(rule: object, fact: dict | None) -> list[str]:
    """A ``values`` entry the input cannot take: not in its enum, or, with no enum,
    not named in its description. The five-level check must not be met by an
    invented value."""
    if not (isinstance(rule, dict) and rule.get("kind") == "values" and fact):
        return []
    enum = fact.get("enum")
    allowed = {str(v).casefold() for v in enum} if enum else None
    text = str(fact.get("description") or "").casefold()
    bad = sorted({str(e.get("value")) for e in rule.get("values") or [] if isinstance(e, dict)
                  and (str(e.get("value")).casefold() not in allowed if allowed is not None
                       else str(e.get("value")).casefold() not in text)})
    if not bad:
        return []
    return [f"values {bad} are not values this input takes (not in its enum or description); "
            "list only real values, and if it has fewer than five, answer null"]


def unreachable_levels(rule: object, fact: dict | None) -> list[str]:
    """Levels whose only ranges lie outside the schema's minimum and maximum."""
    if not (isinstance(rule, dict) and rule.get("kind") == "ranges"
            and rule.get("measure") == "value" and fact):
        return []
    lo, hi = fact.get("minimum"), fact.get("maximum")
    if lo is None and hi is None:
        return []
    def reachable(r: dict) -> bool:
        a, b = r.get("min"), r.get("max")
        return (hi is None or a is None or a <= hi) and (lo is None or b is None or b > lo)
    ranges = [r for r in rule.get("ranges") or [] if isinstance(r, dict)]
    levels = {r.get("level") for r in ranges}
    dead = sorted(lv for lv in levels if isinstance(lv, int)
                  and not any(reachable(r) for r in ranges if r.get("level") == lv))
    if not dead:
        return []
    return [f"levels {dead} cannot occur: this input takes values from {lo} to {hi}; "
            "spread the five levels over that span"]


def window_pairs(facts: dict) -> dict[str, str]:
    """Input path -> the other end of its read window, matched by name ending."""
    by_name = {p.casefold(): p for p in facts}
    pairs: dict[str, str] = {}
    for path in facts:
        low = path.casefold()
        for a, b in WINDOW_PAIRS:
            for mine, other in ((a, b), (b, a)):
                if low.endswith(mine) and (sibling := by_name.get(low[: -len(mine)] + other)):
                    pairs[path] = sibling
    return pairs


def window_problems(rule: object, sibling: str | None) -> list[str]:
    """A read window's end must be rated by the window's length."""
    if sibling is None:
        return []
    ok = (isinstance(rule, dict) and rule.get("kind") == "ranges"
          and rule.get("measure") == "span_hours" and rule.get("with") == sibling)
    return [] if ok else [f"this input is one end of a read window with {sibling}: rate the "
                          f"window's length, ranges on span_hours with {sibling}"]


def left_out_in_policy(org: dict, facts: dict) -> dict[str, str]:
    """Input path -> the policy row that calls leaving it out risky ("with no `x`")."""
    rows = [*org.get("special_value_rules", []), *org.get("baseline", [])]
    found: dict[str, str] = {}
    for row in rows:
        text = " ".join(str(v) for v in row.values())
        for name in _LEFT_OUT.findall(text):
            path = match_path(name, facts)
            if path is not None:
                found.setdefault(path, str(row.get("rule") or row.get("unusual") or text))
    return found


def absent_problems(rule: object, when_absent: object, policy_row: str | None) -> list[str]:
    """An input the policy calls risky when left out needs a rule and a high ``when_absent``."""
    if policy_row is None:
        return []
    if not isinstance(rule, dict):
        return [f"the policy calls leaving this input out risky ({policy_row}); it needs a rule"]
    if isinstance(when_absent, int) and when_absent >= POLICY_ABSENT_FLOOR:
        return []
    return [f"the policy calls leaving this input out risky ({policy_row}); set when_absent "
            f"to {POLICY_ABSENT_FLOOR} (unusual) or 5 (the heaviest case)"]


def _options(round_: int) -> dict | None:
    """Greedy and reproducible on the first pass; sampled on a re-ask."""
    if round_ == 0:
        return None
    return {**DEFAULT_OPTIONS, "temperature": _SAMPLED_TEMPERATURE, "seed": round_}


def _slug(label: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in label)


def log_call(prompt: str, reply: object, label: str, round_: int, out_dir: Path) -> Path:
    """Save one model call, the prompt exactly as sent and the reply, under ``logs/calls``.

    The name carries the round and a digest of the prompt, so the batches of
    one tool in one round do not overwrite each other."""
    folder = out_dir / "logs" / "calls"
    folder.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(prompt.encode()).hexdigest()[:8]
    path = folder / f"{_slug(label)}-round{round_ + 1}-{digest}.json"
    path.write_text(json.dumps({"label": label, "round": round_ + 1, "options": _options(round_),
                                "prompt": prompt, "reply": reply}, indent=1))
    return path


def _ask(prompt: str, props: dict, label: str, round_: int, out_dir: Path) -> list[dict]:
    """The model's rows for one batch; an empty list when the reply is unusable.

    Every call is saved (``log_call``). Only the reply's shape is checked here.
    An unusable reply is also saved under ``logs/rejected`` so a failure can be
    read rather than guessed at."""
    reply = query_ollama(prompt, options=_options(round_), json_schema=REPLY_SCHEMA)
    log_call(prompt, reply, label, round_, out_dir)
    rows = reply.get("inputs") if isinstance(reply, dict) else None
    if isinstance(rows, list) and all(isinstance(r, dict) and _REQUIRED_KEYS <= set(r)
                                      for r in rows):
        return [r for r in rows if str(r["path"]).split(".")[0].split("[")[0] in props]
    logger.warning("     round %d: no usable JSON for %s", round_ + 1, label)
    folder = out_dir / "logs" / "rejected"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_slug(label)}-round{round_ + 1}.json").write_text(json.dumps(reply, indent=1))
    return []


# --------------------------------------------------------------------------- one tool


#: A quoted placeholder in the prompt's examples: ``"<safest words>"``.
_PLACEHOLDER = re.compile(r'"<([^"<>]+)>"')


def placeholder_phrases(template: str) -> frozenset[str]:
    """The prompt's placeholder phrases of two or more words, brackets removed and
    lowercased: a model that drops the brackets still copies ``safest words``."""
    found = (m.strip().casefold() for m in _PLACEHOLDER.findall(template))
    return frozenset(m for m in found if " " in m)


def placeholder_problems(rule: object, phrases: frozenset[str] = frozenset()) -> list[str]:
    """Fragments copied from the prompt's placeholders: ``<safest words>``,
    ``safest words`` with the brackets dropped, or the ``...`` of a shape."""
    groups = rule.get("groups") if isinstance(rule, dict) else None
    copied = sorted({w for g in groups or [] if isinstance(g, dict)
                     for w in g.get("contains") or [] if isinstance(w, str)
                     and ("<" in w or w.strip().casefold() in phrases
                          or not w.strip(" .\u2026"))})
    return [f"fragments {copied} are the prompt's placeholders; write real words"] if copied else []


def override_problems(rule: object, register: dict[str, int]) -> list[str]:
    """An override may only raise an asset of the policy's register. Only an
    asset-name rule reads overrides; on any other kind they are ignored."""
    if not (isinstance(rule, dict) and rule.get("kind") == "register"):
        return []
    overrides = rule.get("overrides")
    problems = []
    for o in overrides if isinstance(overrides, list) else []:
        asset, level = (o.get("asset"), o.get("level")) if isinstance(o, dict) else (None, None)
        if asset not in register:
            problems.append(f"override {asset} names no asset of the policy's register")
        elif isinstance(level, int) and level < register[asset]:
            problems.append(f"override {asset} at {level} lowers its scanned level "
                            f"{register[asset]}; an override only raises")
    return problems


def _too_few_values(rule: object) -> bool:
    """A ``values`` rule with fewer than five distinct values: the input cannot
    take five levels, so it gets no rule rather than an invented fifth value."""
    if not (isinstance(rule, dict) and rule.get("kind") == "values"
            and isinstance(rule.get("values"), list)):
        return False
    distinct = {str(e.get("value")).casefold() for e in rule["values"] if isinstance(e, dict)}
    return len(distinct) < FIVE_LEVELS


def repaired(rule: object, register: dict[str, int]) -> object:
    """The model's rule with the program's repairs: the policy's register as an
    asset-name rule's table, the credential words in a text rule."""
    if not isinstance(rule, dict):
        return rule
    return with_credential_words(with_register_assets(rule, register))


def judge_row(row: dict, key: str, tool_paths: frozenset[str],
              assets: dict[str, int], window_with: str | None = None,
              left_out: str | None = None, phrases: frozenset[str] = frozenset(),
              fact: dict | None = None,
              policy_named: bool = False) -> tuple[dict | None, list[str]]:
    """One answer turned into a decided row, or None and the problems to quote back.

    ``assets`` is the policy's whole register with scanned levels (empty with no
    policy); ``left_out`` the policy row that calls leaving this input out
    risky, if any; ``policy_named`` whether a policy row names the input. Two
    decisions are the program's: an identifier keeps a rule only as a lookup in
    the register (or when the policy names it), and leaving an input out is
    rated at most 3 unless the policy calls it risky. The problems of a
    rejected rule end with the rule itself, as written and repaired, so a
    failure can be read in the output rather than guessed at."""
    effect = row.get("effect")
    if row["rule"] is None:
        if left_out is not None:
            return None, [*absent_problems(None, None, left_out), "rule as written: null"]
        return {"path": key, "status": "null", "important": False, "effect": effect,
                "reason": str(row["reason"])}, []
    if _too_few_values(row["rule"]):
        return {"path": key, "status": "null", "important": False, "effect": effect,
                "reason": "fewer than five possible values; decided by the program"}, []
    if is_identifier(key) and not policy_named and not (
            isinstance(row["rule"], dict) and row["rule"].get("kind") == "register" and assets):
        return {"path": key, "status": "null", "important": False, "effect": effect,
                "reason": "an id: only the id of an asset in the policy's register can be "
                          "rated; decided by the program"}, []
    fixed = repaired(row["rule"], assets)
    rule = drop_clashing_name_words(fixed, assets) if isinstance(fixed, dict) else fixed
    absent = row.get("when_absent")
    if left_out is None and isinstance(absent, int) and absent > ORDINARY_TOP:
        absent = ORDINARY_TOP  # the policy does not call leaving it out risky
    candidate = {"path": key, "rule": rule, "when_absent": absent}
    problems = rule_problems(candidate, tool_paths, all_levels=True, assets=assets)
    problems += placeholder_problems(rule, phrases) + window_problems(rule, window_with)
    problems += override_problems(rule, assets)
    problems += absent_problems(rule, row.get("when_absent"), left_out)
    problems += invented_values(rule, fact) + unreachable_levels(rule, fact)
    if problems and isinstance(fixed, dict):
        problems += [f"name word {w} at level {lv} was dropped: it is part of a listed asset "
                     "at a level more than one away; use words no listed asset contains"
                     for w, lv in dropped_name_words(fixed, rule)]
    if problems:
        return None, [*problems, "rule as written: " + json.dumps(rule)]
    return {**candidate, "status": "rule", "important": True, "effect": effect,
            "reason": str(row["reason"])}, []


def levels_for_tool(template: str, tool: dict, facts: dict, org: dict, props: dict,
                    out_dir: Path, register: dict[str, int] | None = None,
                    ) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Every input of one tool decided: (path -> row, path -> last problems).

    Switches are decided first, without asking. Each round asks only the inputs
    still without a usable answer. A re-ask hands back the rule the model wrote
    last time with the problems it had, so the model repairs that rule (adds the
    missing levels) rather than writing a new one that misses others. ``register``
    is the policy's whole asset register with scanned levels; empty with no policy."""
    assets = dict(register or {})
    org = with_level_hint(org, assets)
    tool_paths = frozenset(facts)
    windows = window_pairs(facts)
    left_out = left_out_in_policy(org, facts)
    policy_named = named_by_policy(org, facts)
    phrases = placeholder_phrases(template)
    facts = {p: {**f, **({"window_with": windows[p]} if p in windows else {})}
             for p, f in facts.items()}
    decided: dict[str, dict] = {p: row for p, f in facts.items()
                                if (row := decided_by_program(p, f, policy_named)) is not None}
    problems: dict[str, list[str]] = {}
    for round_ in range(_ROUNDS):
        pending = {p: {**f, **(_repair_note(problems[p]) if p in problems else {})}
                   for p, f in facts.items() if p not in decided}
        if not pending:
            break
        size = _BATCH if round_ == 0 else _REASK_BATCH
        for batch in batched(pending, size):
            label = f"{tool['tool_name']}-levels"
            # every other input of the tool, so a batch sees the inputs of the others
            context = {p: {"description": facts[p].get("description"),
                           "enum": facts[p].get("enum")} for p in facts if p not in batch}
            prompt = fill(template, tool, batch, context, org)
            for row in _ask(prompt, props, label, round_, out_dir):
                key = match_path(row["path"], batch)
                if key is None or key in decided:
                    continue
                done, found = judge_row(row, key, tool_paths, assets, windows.get(key),
                                        left_out.get(key), phrases, facts[key],
                                        key in policy_named)
                if done is None:
                    problems[key] = found
                else:
                    decided[key] = done
                    problems.pop(key, None)
    return decided, problems


def _repair_note(problems: list[str]) -> dict:
    """What a re-ask adds to an input: the rule written last time and what failed.

    The program's own additions (the register's asset table, the credential
    group) are left out: the model repairs what it wrote, and they are added
    again."""
    last = json.loads(problems[-1].removeprefix("rule as written: "))
    if isinstance(last, dict):
        last = {k: v for k, v in last.items() if k != "assets"}
        if isinstance(last.get("groups"), list):
            last["groups"] = [g for g in last["groups"]
                              if not (isinstance(g, dict) and g.get("added_by"))]
    return {"your_last_rule": last, "problems_last_time": problems[:-1]}


def tool_rows(facts: dict, decided: dict[str, dict], problems: dict[str, list[str]]) -> list:
    """One row per declared input, in schema order, undecided ones marked."""
    rows = []
    for path, fact in facts.items():
        if path in decided:
            row = decided[path]
        elif path in problems:
            row = {"path": path, "status": "broken", "important": True,
                   "reason": "the rule never passed the check: " + "; ".join(problems[path][:-1]),
                   "last_rule": problems[path][-1].removeprefix("rule as written: ")}
        else:
            row = {"path": path, "status": "unanswered", "important": False,
                   "reason": "no round answered this input"}
        default = fact.get("default")
        if row["status"] == "rule" and default not in (None, ""):
            row = {**row, "schema_default": default}  # rated when a call leaves it out
        rows.append({**row, "choices": choices(fact)})
    return rows


# --------------------------------------------------------------------------- server


def _catalog_block(server: str) -> dict:
    catalog = CATALOGS[server]
    return {"server": server,
            "catalog": {"path": str(catalog.path.relative_to(CAT_REPO)),
                        "sha256": hashlib.sha256(catalog.path.read_bytes()).hexdigest(),
                        "package": catalog.package, "captured": catalog.captured},
            "slurm_job": os.environ.get("SLURM_JOB_ID", "")}


def run_server(server: str, out_dir: Path) -> int:
    """Every tool of ``server``; writes ``<server>.json`` and returns 1 if a tool failed."""
    template = load_prompt()
    digest = snapshot(template, out_dir)
    register = register_assets(server)
    results, failed = [], []
    for tool in load_tools(server):
        name = tool["tool_name"]
        props = (tool["input_schema"] or {}).get("properties", {})
        if not props:
            results.append({"tool_name": name, "arguments": [], "no_declared_schema": True})
            continue
        org = org_for_tool(server, name)
        facts = facts_for(tool["input_schema"])
        decided, problems = levels_for_tool(template, tool, facts, org, props, out_dir,
                                            register)
        if not decided and not problems:
            failed.append(name)
            continue
        rows = tool_rows(facts, decided, problems)
        kept = [r["path"] for r in rows if r["status"] == "rule"]
        logger.info("  %s: %d of %d input(s) with a rule, %d broken, %d unanswered", name,
                    len(kept), len(rows), sum(r["status"] == "broken" for r in rows),
                    sum(r["status"] == "unanswered" for r in rows))
        results.append({"tool_name": name, "policy_slice": org, "arguments": rows,
                        "shortlist": kept,
                        "missing_rules": [r["path"] for r in rows if r["status"] == "broken"],
                        "rule_problems": problems})
    out = out_dir / f"{server}.json"
    out.write_text(json.dumps({
        **_catalog_block(server), "prompt_sha256": digest, "prompt": PROMPT_SNAPSHOT,
        "policy_section": POLICY_SECTIONS.get(server), "rounds": _ROUNDS,
        "tools": results, "failed": failed}, indent=2))
    logger.info("wrote %s: %d tool(s), %d failed", out, len(results), len(failed))
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--server", required=True, choices=sorted(CATALOGS))
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s %(message)s")
    return run_server(args.server, _run_dir())


if __name__ == "__main__":
    raise SystemExit(main())
