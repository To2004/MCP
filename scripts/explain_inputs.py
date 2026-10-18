"""Explain every tool input of a run — one markdown file per MCP server.

Joins three sources so a reader can check the model's answer against the
evidence it had: the tool's **declared schema** (type, description, constraints),
the **classification** the model returned with its reason, and the **log** (was
this tool sent to the model at all, and how long the call took). Writes ``<server>.md`` into the
run folder, one per MCP, so each server can be read on its own.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
V10 = REPO / "reports" / "experiments" / "v10"

# What each class means for the run-time layer, phrased for one argument.
AT_RUNTIME = {
    "RANGE": "Band the value: {bands}. Boundaries {bounds}.",
    "POLICY": "Resolve “{concept}” against the organisation's policy: may this "
              "caller act on the one it named?",
    "IGNORE": "Not evaluated by this component.",
    "UNKNOWN": "Undecided — needs a human or a better tool description.",
}


sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_catalogs import REPO as CAT_REPO  # noqa: E402


def _schemas_for(blob: dict) -> dict[str, dict] | None:
    """The declared schemas this run was actually typed against.

    Read from the catalog the run recorded, never from whichever catalog is
    current — repointing a server at a different capture must not silently
    re-label an archived run. Runs that predate catalog recording return None,
    and the declared column is dropped rather than filled with guesses.
    """
    cat = blob.get("catalog")
    if not cat:
        return None
    path = CAT_REPO / cat["path"]
    if not path.exists():
        raise SystemExit(f"catalog {cat['path']} recorded by this run is missing")
    tools = json.loads(path.read_text())["tools"]
    return {t["name"]: (t.get("input_schema") or t.get("inputSchema") or {}).get(
        "properties", {}) for t in tools}


def _declared(spec: dict) -> str:
    """The schema's own words about one argument, as a short cell."""
    if not isinstance(spec, dict):
        return "—"
    bits = [f"`{spec.get('type', 'any')}`"]
    for key in ("enum", "minimum", "maximum", "format", "default"):
        if key in spec:
            bits.append(f"{key}={json.dumps(spec[key])}")
    desc = (spec.get("description") or "").strip()
    return " · ".join(bits) + (f" — {desc}" if desc else "")


def _log_facts(run: Path) -> tuple[dict[str, str], set[str]]:
    """Per-tool call duration, and which tools the log says were skipped."""
    seconds: dict[str, str] = {}
    skipped: set[str] = set()
    for log in (run / "logs").glob("*.log"):
        text = log.read_text(errors="replace")
        skipped |= set(re.findall(r"-- (\S+) declares no inputs", text))
        stamps = re.findall(r"^\S+ (\d\d):(\d\d):(\d\d),\d+\s+(.*)$", text, re.M)
        for (h1, m1, s1, msg), (h2, m2, s2, _) in zip(stamps, stamps[1:]):
            call = re.search(r"-> (\S+) \(", msg)
            if call:
                delta = (int(h2) * 3600 + int(m2) * 60 + int(s2)) - (
                    int(h1) * 3600 + int(m1) * 60 + int(s1))
                seconds[call.group(1)] = f"{delta}s"
    return seconds, skipped


def main() -> int:
    run = Path(sys.argv[1]) if len(sys.argv) > 1 else max(
        (d for d in V10.glob("run*") if d.name[3:].isdigit()), key=lambda d: int(d.name[3:]))
    seconds, skipped = _log_facts(run)

    written = []
    for path in sorted(run.glob("*.json")):
        blob = json.loads(path.read_text())
        server = blob["server"]
        schemas = _schemas_for(blob)
        cat = blob.get("catalog") or {}
        counts = Counter(str(a.get("classification", "UNKNOWN")).upper()
                         for t in blob["tools"] for a in t.get("arguments", []))
        out_lines = [f"# {server} — every tool input, explained", "",
                     f"Run `{run.name}`. One table per tool. **Declared** is what the tool's",
                     "own schema says — the only evidence the model had. **Class** is what the",
                     "model returned and why. **At run time** is what that classification asks",
                     "the dynamic layer to do with the value.", "",
                     "Classes: `RANGE` compares by magnitude · `POLICY` resolves which entity",
                     "was named against policy · `IGNORE` is not evaluated · `UNKNOWN` is",
                     "undecided.", "",
                     " · ".join(f"**{c}** {counts[c]}" for c in
                                ("RANGE", "POLICY", "IGNORE", "UNKNOWN"))
                     + f" · {sum(t.get('declared_arguments', 0) for t in blob['tools'])}"
                       " declared across "
                     + f"{len(blob['tools'])} tool(s).", "",
                      f"Prompt `{blob.get('prompt_sha256', '?')[:12]}` · "
                     f"job `{blob.get('slurm_job', '?')}`"
                     + (f" · catalog `{cat['path']}` ({cat.get('package', '?')}, "
                        f"captured {cat.get('captured', '?')})." if cat else "."), ""]
        if schemas is None:
            out_lines += ["This run predates catalog recording, so the schemas it was typed",
                          "against cannot be identified with certainty. The **declared**",
                          "column is omitted rather than filled from whichever catalog is",
                          "current — that would re-label the run against a server it never saw.", ""]

        for tool in sorted(blob["tools"], key=lambda t: t["tool_name"]):
            name = tool["tool_name"]
            args = tool.get("arguments", [])
            if not args:
                continue
            props = (schemas or {}).get(name, {})
            took = seconds.get(name, "?")
            head = ("| input | declared | class | why the model said so | at run time |\n"
                    "|---|---|---|---|---|" if schemas is not None else
                    "| input | class | why the model said so | at run time |\n|---|---|---|---|")
            out_lines += [f"### `{name}`", "",
                          f"{len(args)} argument(s), one model call, {took}.", "", head]
            for a in args:
                path_ = str(a.get("path", ""))
                root = path_.split(".")[0].split("[")[0]
                cls = str(a.get("classification", "UNKNOWN")).upper()
                sub = a.get("subtype")
                src = a.get("bounds_source") or "unstated"
                bounds = ("come from the schema's declared minimum/maximum" if src == "schema"
                          else "come from limits stated in the description" if src == "documented"
                          else "were placed from ordinary practice, so traffic should correct them")
                unit = a.get("unit") or ""
                bands = " · ".join(
                    f"**{name}** {a.get(key) or '—'}"
                    for name, key in (("low", "low"), ("medium", "medium"), ("high", "high")))
                runtime = AT_RUNTIME.get(cls, "—").format(
                    bands=bands + (f" {unit}" if unit else ""), bounds=bounds,
                    concept=a.get("policy_concept") or root)
                items = a.get("items") or {}
                if items:
                    runtime += (f" Each item is **{items.get('classification')}**"
                                f"{' — ' + items['policy_concept'] if items.get('policy_concept') else ''},"
                                " so the members are checked as well as the count.")
                declared = (f"| {_declared(props.get(root, {}))} "
                            if schemas is not None else "| ")
                out_lines.append(
                    f"| `{path_}` {declared}"
                    f"| **{cls}**{' / ' + sub if sub else ''} "
                    f"| {a.get('reason', '—')} | {runtime} |")
            out_lines.append("")

        never_sent = [t["tool_name"] for t in blob["tools"] if t.get("no_declared_schema")]
        if never_sent:
            out_lines += ["### Tools with no inputs to explain", "",
                          "These declare no arguments, so they were never sent to the model —",
                          "asking about an empty schema invites it to invent the arguments it",
                          "expects. The log records each one as `declares no inputs`.", "",
                          ", ".join(f"`{t}`" for t in never_sent) + ".", ""]
            missing = [t for t in never_sent if t not in skipped]
            if missing:
                out_lines += [f"(Not corroborated by the log: {', '.join(missing)}.)", ""]

        doc = f"{server}.md"
        (run / doc).write_text("\n".join(out_lines))
        written.append(doc)

    for name in written:
        print(f"wrote {run / name}")
    if not written:
        print(f"no result files in {run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
