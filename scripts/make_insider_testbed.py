"""Generate the INSIDER variant of the dynamic testbed — no external attackers.

Differences from :mod:`make_dynamic_testbed` (which it reuses for all call
construction):

* **Every persona is a legitimate insider with a mixed record.** There are no
  ``Attacker (Eve)`` personas and no external sessions: each of the 4 role
  personas per org produces ~:data:`CALLS_PER_PERSONA` calls of its own —
  mostly benign work, several accidental-misuse sessions, and one or two
  insider-attack sessions (read a crown jewel, then exfiltrate). Identity
  therefore carries no label signal by construction: the dynamic scorer must
  separate categories from behavior alone.
* **Two organizations** instead of twenty, so per-persona history is deep
  (~100 calls) rather than wide.
* **Sessions are globally shuffled** before indexing, so the chronological
  stream interleaves personas and categories the way real traffic would.
* Only the big three servers (calendar, github, slack) are generated.

Output: ``logs/proxy/sessions/dyn_<server>_ins/calls.csv`` (the original
``dyn_<server>_cbg`` corpora are left untouched). Deterministic under
:data:`SEED`; purely synthetic and offline.

Run::

    uv run python scripts/make_insider_testbed.py
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_dynamic_testbed as base  # noqa: E402

SEED = 20260712
ORG_COUNT = 2
CALLS_PER_PERSONA = 100
# Per persona: how many misuse and insider-attack sessions its record contains.
MISUSE_SESSIONS_PER_PERSONA = (3, 5)  # rng.randint range (~10-20 calls)
INSIDER_SESSIONS_PER_PERSONA = (1, 2)  # rng.randint range (~4-10 calls)

SERVERS = {
    "calendar_cbg": "calendar",
    "github_cbg": "repo",
    "slack_cbg": "channel",
}


def _session_rows(build, *args) -> list[dict]:
    """Run one session builder into a throwaway builder and return its rows."""
    scratch = base._RowBuilder()
    build(*args, scratch)
    return scratch.rows


def build_persona_sessions(
    model: base.ServerModel, rng: random.Random, persona: str
) -> list[list[dict]]:
    """All of one persona's sessions: benign filler to ~CALLS_PER_PERSONA plus
    its fixed quota of misuse and insider sessions."""
    tag = persona.replace(" ", "_").replace("@", "_at_")
    sessions: list[list[dict]] = []
    n_calls = 0

    for i in range(rng.randint(*INSIDER_SESSIONS_PER_PERSONA)):
        rows = _session_rows(base._insider_session, model, rng, persona, f"insider_{tag}_{i}")
        sessions.append(rows)
        n_calls += len(rows)

    for i in range(rng.randint(*MISUSE_SESSIONS_PER_PERSONA)):
        impact = base._pick_impact(rng)
        scratch = base._RowBuilder()
        base._misuse_session(model, rng, persona, f"misuse_{impact}_{tag}_{i}", scratch, impact)
        sessions.append(scratch.rows)
        n_calls += len(scratch.rows)

    i = 0
    while n_calls < CALLS_PER_PERSONA:
        rows = _session_rows(base._benign_session, model, rng, persona, f"benign_{tag}_{i}")
        sessions.append(rows)
        n_calls += len(rows)
        i += 1
    return sessions


def build_server_testbed(model: base.ServerModel, rng: random.Random) -> list[dict]:
    """Every persona's sessions across ORG_COUNT orgs, globally shuffled then indexed."""
    sessions: list[list[dict]] = []
    for org_index in range(ORG_COUNT):
        org = base._org_slug(org_index)
        for persona in base.BENIGN_PERSONAS:
            sessions.extend(build_persona_sessions(model, rng, f"{persona}@{org}"))

    rng.shuffle(sessions)  # interleave personas/categories in stream order
    rows: list[dict] = []
    for session in sessions:
        for row in session:
            row["index"] = len(rows) + 1
            rows.append(row)
    return rows


def main() -> int:
    rng = random.Random(SEED)
    for stem, asset_key in SERVERS.items():
        model = base.load_server_model(stem, asset_key)
        rows = build_server_testbed(model, rng)
        out_dir = base.SESSIONS / f"dyn_{stem.replace('_cbg', '')}_ins"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "calls.csv"
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=base.CSV_HEADER)
            writer.writeheader()
            writer.writerows(rows)
        counts: dict[str, int] = {}
        personas = {r["persona"] for r in rows}
        for r in rows:
            counts[r["category"]] = counts.get(r["category"], 0) + 1
        print(
            f"{stem}: {len(rows)} calls, {len(personas)} personas "
            f"(~{len(rows) // len(personas)}/persona), {counts} -> {out_path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
