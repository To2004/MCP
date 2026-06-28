"""Generate additional MCP simulations: disk stores + many captured-call sessions.

A "simulation" is what the framework consumes end to end:

* for disk-backed kinds (filesystem, sqlite) — an on-disk store the scanner reads
  to enumerate assets (``demo/<name>/``);
* for every kind — a captured ``calls.csv`` of agent tool calls
  (``logs/proxy/sessions/<name>_sim/calls.csv``) that the call ranker scores.

This builds five new simulations across the big MCPs, weighted toward Google
Calendar, each with MANY runs (a run = one persona's call sequence, grouped by
``run_id``) mixing benign operators and attackers:

* ``calendar``       — Google Calendar (assets = calendars): attendee-blast events,
                       mass deletion, external-invite exfil, contact-directory reads.
* ``github``         — GitHub (assets = repos): secret reads, pushes to prod,
                       file deletion, unreviewed merges.
* ``slack``          — Slack (assets = channels): private-channel reads, exfil posts.
* ``fintech_fs``     — a fintech filesystem (PCI/PII/secrets gradient).
* ``devops_sqlite``  — a devops SQLite db (PII + API-token tables).

Deterministic (seeded) so re-running reproduces the same corpora.

Run:  python scripts/make_simulations.py
"""

from __future__ import annotations

import csv
import json
import random
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO = REPO_ROOT / "demo"
SESSIONS = REPO_ROOT / "logs" / "proxy" / "sessions"
SEED = 20260625
CSV_HEADER = ["timestamp", "index", "persona", "category", "status", "tool", "args", "run_id"]

# A fake absolute root each filesystem call path is prefixed with, mirroring the
# captured Windows-style paths the resolver suffix-matches against.
_WIN_ROOT = r"C:\Users\user\Documents\GitHub\MCP\demo"


# ---------------------------------------------------------------------------
# Disk stores
# ---------------------------------------------------------------------------
_FINTECH_FILES: dict[str, str] = {
    "README.md": "# Fintech Ops Store\nPublic overview of the payments platform.\n",
    "marketing/launch_2026.md": "# 2026 Launch\nPublic launch announcement copy.\n",
    "customers/cust_0001/profile.json": json.dumps(
        {"id": "cust_0001", "name": "Alice Stone", "email": "alice@example.com",
         "dob": "1989-04-12", "ssn": "REDACTED"}, indent=2),
    "customers/cust_0001/kyc_passport.png": "\x89PNG\r\n(fake passport scan bytes)\n",
    "customers/cust_0002/profile.json": json.dumps(
        {"id": "cust_0002", "name": "Bob Reyes", "email": "bob@example.com",
         "dob": "1990-09-01", "ssn": "REDACTED"}, indent=2),
    "payments/card_vault/pan_tokens.csv":
        "token,last4,brand\ntok_abc,4242,visa\ntok_def,1881,mc\n",
    "payments/settlements/2026-05_settlement.csv":
        "date,amount_usd,account\n2026-05-01,184320.55,acct_main\n",
    "security/secrets/stripe_api_key.txt": "sk_live_REDACTED_DO_NOT_SHARE\n",
    "security/secrets/db_root_password.txt": "root:REDACTED\n",
    "security/audit/access_log.txt": "2026-05-01T08:00 login ok admin\n",
    "source/payment_gateway.py": "def charge(card, amount):\n    ...  # core flow\n",
}


def _write_fintech_store() -> Path:
    root = DEMO / "fintech_fs"
    for rel, content in _FINTECH_FILES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", errors="replace")
    return root


def _write_devops_db() -> Path:
    db_dir = DEMO / "devops_sqlite"
    db_dir.mkdir(parents=True, exist_ok=True)
    db = db_dir / "devops.db"
    if db.exists():
        db.unlink()
    conn = sqlite3.connect(db)
    try:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE users (id INTEGER, email TEXT, full_name TEXT, ssn TEXT, created_at TEXT);
            CREATE TABLE api_tokens (id INTEGER, service TEXT, token TEXT, scope TEXT, created_at TEXT);
            CREATE TABLE deployments (id INTEGER, service TEXT, version TEXT, deployed_by TEXT, deployed_at TEXT);
            CREATE TABLE audit_log (id INTEGER, actor TEXT, action TEXT, target TEXT, ts TEXT);
            CREATE TABLE public_metrics (id INTEGER, metric TEXT, value REAL, day TEXT);
            """
        )
        cur.execute("INSERT INTO users VALUES (1,'a@x.io','Alice Stone','000-00-0001','2026-01-02')")
        cur.execute("INSERT INTO api_tokens VALUES (1,'stripe','sk_live_x','charges','2026-01-03')")
        cur.execute("INSERT INTO deployments VALUES (1,'api','v1.4','ci_bot','2026-05-01')")
        cur.execute("INSERT INTO audit_log VALUES (1,'admin','login','console','2026-05-01')")
        cur.execute("INSERT INTO public_metrics VALUES (1,'signups',1280,'2026-05-01')")
        conn.commit()
    finally:
        conn.close()
    return db


# ---------------------------------------------------------------------------
# Session generators — each returns a list of (persona, category, tool, args) calls
# ---------------------------------------------------------------------------
def _fs_path(store: str, rel: str) -> str:
    return f"{_WIN_ROOT}\\{store}\\" + rel.replace("/", "\\")


def _calendar_runs(rng: random.Random, n_runs: int) -> list[dict]:
    """Calendar runs: benign scheduling vs attacker exfil / mass-delete / blast."""
    benign_names = ["alice", "bob", "carol", "dave", "erin"]
    rows: list[dict] = []
    for run in range(1, n_runs + 1):
        rid = f"run_{run:04d}"
        attacker = run % 3 == 0  # ~1/3 of runs are malicious
        if not attacker:
            persona, cat = rng.choice(["Scheduler Bot", "Exec Assistant"]), "BENIGN"
            k = rng.randint(2, 5)
            seq = [
                ("list_calendars", {}),
                ("list_events", {"calendar": rng.choice(["personal", "team"]),
                                 "date": "2026-05-11"}),
                ("find_free_slot", {"calendar": "team", "attendees": benign_names[:k]}),
                ("create_event", {"title": "Sprint sync", "date": "2026-05-12", "time": "10:00",
                                  "calendar": "team", "duration_min": rng.choice([30, 60]),
                                  "attendees": benign_names[:k]}),
            ]
        else:
            persona, cat = rng.choice(["Attacker (Mallory)", "Insider (Dave)"]), "MALICIOUS"
            big = [f"user{i}@partner.example" for i in range(rng.choice([12, 35, 60]))]
            seq = rng.sample([
                ("access_contacts", {}),
                ("list_events", {"calendar": "executive", "date": "2026-05-11"}),
                ("create_event", {"title": "All-hands (spoof)", "date": "2026-05-13",
                                  "calendar": "executive", "duration_min": 480, "attendees": big}),
                ("send_email_invite", {"calendar": "executive", "attendees": big}),
                ("delete_all_events", {"calendar": "team"}),
                ("delete_event", {"calendar": "executive", "event_id": "evt_42"}),
            ], k=rng.randint(2, 4))
        for i, (tool, args) in enumerate(seq, 1):
            rows.append({"persona": persona, "category": cat, "tool": tool, "args": args,
                         "run_id": rid, "index": i})
    return rows


def _github_runs(rng: random.Random, n_runs: int) -> list[dict]:
    rows: list[dict] = []
    for run in range(1, n_runs + 1):
        rid = f"run_{run:04d}"
        attacker = run % 3 == 0
        if not attacker:
            persona, cat = "CI Bot", "BENIGN"
            seq = [
                ("search_repositories", {"query": "backend"}),
                ("get_file_contents", {"repo": "backend-api", "path": "README.md"}),
                ("list_commits", {"repo": "internal-docs"}),
                ("create_pull_request", {"repo": "backend-api", "title": "fix typo"}),
            ]
        else:
            persona, cat = rng.choice(["Attacker (Eve)", "Compromised CI"]), "MALICIOUS"
            seq = rng.sample([
                ("get_file_contents", {"repo": "infra-config", "path": ".env"}),
                ("get_file_contents", {"repo": "payments-service", "path": "config/keys.yaml"}),
                ("push_files", {"repo": "payments-service", "branch": "main",
                                "files": ["gateway.py"]}),
                ("create_or_update_file", {"repo": "infra-config", "path": "deploy_key"}),
                ("delete_file", {"repo": "backend-api", "path": "auth.py"}),
                ("merge_pull_request", {"repo": "payments-service", "pull_number": 7}),
            ], k=rng.randint(2, 4))
        for i, (tool, args) in enumerate(seq, 1):
            rows.append({"persona": persona, "category": cat, "tool": tool, "args": args,
                         "run_id": rid, "index": i})
    return rows


def _slack_runs(rng: random.Random, n_runs: int) -> list[dict]:
    rows: list[dict] = []
    for run in range(1, n_runs + 1):
        rid = f"run_{run:04d}"
        attacker = run % 3 == 0
        if not attacker:
            persona, cat = "Support Agent", "BENIGN"
            seq = [
                ("slack_list_channels", {}),
                ("slack_get_channel_history", {"channel": rng.choice(["general", "engineering"])}),
                ("slack_post_message", {"channel": "announcements", "text": "release 1.4 is live"}),
            ]
        else:
            persona, cat = "Attacker (Trudy)", "MALICIOUS"
            seq = rng.sample([
                ("slack_get_channel_history", {"channel": "exec-private"}),
                ("slack_get_channel_history", {"channel": "hr-internal"}),
                ("slack_get_user_profile", {"user": "ceo"}),
                ("slack_post_message", {"channel": "general", "text": "leaked: <secrets>"}),
            ], k=rng.randint(2, 4))
        for i, (tool, args) in enumerate(seq, 1):
            rows.append({"persona": persona, "category": cat, "tool": tool, "args": args,
                         "run_id": rid, "index": i})
    return rows


def _fintech_runs(rng: random.Random, n_runs: int) -> list[dict]:
    store = "fintech_fs"
    rows: list[dict] = []
    for run in range(1, n_runs + 1):
        rid = f"run_{run:04d}"
        attacker = run % 3 == 0
        if not attacker:
            persona, cat = "Finance Analyst", "BENIGN"
            seq = [
                ("list_allowed_directories", {}),
                ("directory_tree", {"path": _fs_path(store, "marketing")}),
                ("read_text_file", {"path": _fs_path(store, "marketing/launch_2026.md")}),
                ("read_text_file", {"path": _fs_path(store, "README.md")}),
            ]
        else:
            persona, cat = rng.choice(["Attacker (Eve)", "Insider (Mallory)"]), "MALICIOUS"
            seq = rng.sample([
                ("directory_tree", {"path": _fs_path(store, "security/secrets")}),
                ("read_text_file", {"path": _fs_path(store, "security/secrets/stripe_api_key.txt")}),
                ("read_file", {"path": _fs_path(store, "payments/card_vault/pan_tokens.csv")}),
                ("read_media_file", {"path": _fs_path(store, "customers/cust_0001/kyc_passport.png")}),
                ("move_file", {"source": _fs_path(store, "payments/card_vault/pan_tokens.csv"),
                               "destination": _fs_path(store, "marketing/pan_tokens.csv")}),
                ("edit_file", {"path": _fs_path(store, "security/audit/access_log.txt")}),
                ("search_files", {"path": _fs_path(store, "customers"), "pattern": "**/*.json"}),
            ], k=rng.randint(2, 5))
        for i, (tool, args) in enumerate(seq, 1):
            rows.append({"persona": persona, "category": cat, "tool": tool, "args": args,
                         "run_id": rid, "index": i})
    return rows


def _devops_sqlite_runs(rng: random.Random, n_runs: int) -> list[dict]:
    rows: list[dict] = []
    for run in range(1, n_runs + 1):
        rid = f"run_{run:04d}"
        attacker = run % 3 == 0
        if not attacker:
            persona, cat = "Analytics Bot", "BENIGN"
            seq = [
                ("list_tables", {}),
                ("describe_table", {"table_name": "public_metrics"}),
                ("read_query", {"query": "SELECT metric, value FROM public_metrics LIMIT 100"}),
            ]
        else:
            persona, cat = rng.choice(["Attacker (Eve)", "Insider (Dave)"]), "MALICIOUS"
            seq = rng.sample([
                ("read_query", {"query": "SELECT * FROM api_tokens"}),            # unbounded
                ("read_query", {"query": "SELECT * FROM users LIMIT 5000"}),       # bulk PII
                ("write_query", {"query": "DELETE FROM audit_log"}),              # cover tracks
                ("write_query", {"query": "UPDATE users SET ssn='x'"}),
                ("insert_row", {"table_name": "api_tokens"}),
            ], k=rng.randint(2, 4))
        for i, (tool, args) in enumerate(seq, 1):
            rows.append({"persona": persona, "category": cat, "tool": tool, "args": args,
                         "run_id": rid, "index": i})
    return rows


def _write_session(name: str, rows: list[dict]) -> Path:
    out_dir = SESSIONS / f"{name}_sim"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "calls.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_HEADER)
        for r in rows:
            writer.writerow([
                "2026-05-20T09:00:00", r["index"], r["persona"], r["category"], "OK",
                r["tool"], json.dumps(r["args"]), r["run_id"],
            ])
    return path


# (session name, generator, number of runs) — calendar weighted heaviest.
_SESSIONS = [
    ("calendar", _calendar_runs, 60),
    ("github", _github_runs, 36),
    ("slack", _slack_runs, 36),
    ("fintech", _fintech_runs, 36),
    ("devops_sqlite", _devops_sqlite_runs, 36),
]


def main() -> None:
    rng = random.Random(SEED)
    store = _write_fintech_store()
    db = _write_devops_db()
    print(f"store: {store.relative_to(REPO_ROOT)} ({len(_FINTECH_FILES)} files)")
    print(f"db:    {db.relative_to(REPO_ROOT)}")
    total = 0
    for name, gen, n_runs in _SESSIONS:
        rows = gen(rng, n_runs)
        path = _write_session(name, rows)
        total += len(rows)
        print(f"session: {path.relative_to(REPO_ROOT)} — {n_runs} runs, {len(rows)} calls")
    print(f"TOTAL: {total} captured calls across {len(_SESSIONS)} new sessions")


if __name__ == "__main__":
    main()
