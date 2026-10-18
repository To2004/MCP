"""Render a run's logs as an annotated markdown page.

Each run folder keeps a SLURM log (what the job allocated and did) and one log
per server (what the runner sent the model, tool by tool). Both are short and
tell the story of the run, but only if you know what the lines mean — so this
writes ``LOGS.md``: the log text, with the meaning of each kind of line beside
it and a short verdict at the end.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
V10 = REPO / "reports" / "experiments" / "v10"

# What each recognisable line means. Order matters: first match wins.
MEANINGS: list[tuple[str, str]] = [
    (r"^=== run folder:", "The folder this run writes to, chosen once by the job "
                          "so all servers agree."),
    (r"^=== servers:", "Which servers were typed. `TYPE_SERVERS` overrides the default."),
    (r"^=== .*GPU\(s\)", "The node and how many GPUs it got; one Ollama is served per GPU."),
    (r"prompt [0-9a-f]{8,}", "The sha256 of the prompt text, read once at the start of "
                             "the run and snapshotted as `prompt-AS-RUN.md`. Every result "
                             "file repeats this digest, so results can never be read "
                             "against the wrong prompt."),
    (r"typing \d+ tool\(s\)", "How many tools the server contributed."),
    (r"declares no inputs", "Skipped deliberately: a tool with an empty schema is never "
                            "sent to the model, because asking about nothing invites it "
                            "to invent the arguments it expects."),
    (r"-> \S+ \(\d+ argument", "One model call. The gap to the next timestamp is how long "
                               "it took; the first call of a run also pays for loading "
                               "the model."),
    (r"no usable JSON", "The model's reply could not be parsed as a JSON object. The "
                        "tool is recorded in `failed` rather than silently dropped."),
    (r"^wrote ", "The result file, written once at the end of the server's pass."),
    (r"^Traceback|^\w*Error:", "The run crashed here. Anything the model had already "
                               "returned was lost, because results are written only at "
                               "the end."),
    (r"^=== DONE rc=", "Exit status of the whole job: `rc=0` all servers succeeded, "
                       "`rc=1` at least one did not."),
]


def _meaning(line: str) -> str | None:
    for pattern, text in MEANINGS:
        if re.search(pattern, line):
            return text
    return None


def _timings(text: str) -> list[tuple[str, float]]:
    """Seconds between one model call and the next line, per tool."""
    stamps = re.findall(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+\s+(.*)$", text, re.M)
    out = []
    for (t1, msg), (t2, _) in zip(stamps, stamps[1:]):
        call = re.search(r"-> (\S+) \((\d+) argument", msg)
        if not call:
            continue
        h1, m1, s1 = (int(x) for x in t1.split(" ")[1].split(":"))
        h2, m2, s2 = (int(x) for x in t2.split(" ")[1].split(":"))
        out.append((call.group(1), (h2 * 3600 + m2 * 60 + s2) - (h1 * 3600 + m1 * 60 + s1)))
    return out


def main() -> int:
    run = Path(sys.argv[1]) if len(sys.argv) > 1 else max(
        (d for d in V10.glob("run*") if d.name[3:].isdigit()), key=lambda d: int(d.name[3:]))
    logs = sorted((run / "logs").glob("*"))
    if not logs:
        raise SystemExit(f"no logs under {run}")

    lines = [f"# {run.name} — run log", "",
             "What the job did, line by line. The log text is verbatim; the notes",
             "beside it explain what each kind of line means.", ""]

    for log in logs:
        text = log.read_text(errors="replace")
        kind = ("SLURM job log — allocation and the shell script's own echoes"
                if log.suffix == ".out" else
                f"Runner log for `{log.name.split('-')[0]}` — one line per tool")
        lines += [f"## `{log.name}`", "", kind, "", "```", text.rstrip(), "```", ""]

        seen, notes = set(), []
        for line in text.splitlines():
            meaning = _meaning(line.strip())
            if meaning and meaning not in seen:
                seen.add(meaning)
                notes.append(f"- `{line.strip()[:72]}`  \n  {meaning}")
        if notes:
            lines += ["**What those lines mean**", "", *notes, ""]

        timings = _timings(text)
        if timings:
            lines += ["**Time per model call**", "",
                      "| tool | seconds |", "|---|---|",
                      *(f"| `{name}` | {secs} |" for name, secs in timings), ""]

    results = sorted(p for p in run.glob("*.json"))
    if results:
        lines += ["## What the run produced", "",
                  "| file | tools | arguments described | declared | failed | no schema |",
                  "|---|---|---|---|---|---|"]
        for path in results:
            blob = json.loads(path.read_text())
            tools = blob.get("tools", [])
            lines.append(
                f"| `{path.name}` | {len(tools)} "
                f"| {sum(len(t.get('arguments', t.get('inputs', []))) for t in tools)} "
                f"| {sum(t.get('declared_arguments', t.get('declared_inputs', 0)) for t in tools)} "
                f"| {len(blob.get('failed', []))} "
                f"| {len(blob.get('no_declared_schema', []))} |")
        lines.append("")
    else:
        lines += ["## What the run produced", "",
                  "**No result files.** The run did not get as far as writing any.", ""]

    out = run / "LOGS.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
