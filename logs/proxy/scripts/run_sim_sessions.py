"""
Offline simulation: large realistic MCP tool-call sessions for filesystem and SQLite demo servers.

Writes four files per run folder:
  flows.jsonl    — raw synthetic HTTP flows (same schema as mitmdump captures)
  calls.csv      — structured, one row per tool call
  http_trace.txt — every HTTP flow fully expanded with headers + JSON bodies
  report.txt     — human-readable session report

Call mix per session (filesystem ~99 calls, SQLite ~58 calls):
  ~65% VALID     — normal calls across all tools / directories / tables
  ~13% MISUSE    — correct tool, wrong usage (binary file, bad arg, wrong direction)
  ~9%  EDGE      — edge cases (no-match, ENOENT, idempotent ops, dryRun)
  ~4%  BAD_TOOL  — non-existent tool names (-32602)
  ~9%  MALICIOUS — attacker-style calls (path traversal, exfil, tampering)

Folder naming: run_{call_count:04d}; appends _2/_3/... on collision.
"""
from __future__ import annotations

import csv
import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

FS_ROOT = Path(r"C:\Users\user\Documents\GitHub\MCP\demo\corp_filesystem_sim")
FS_OUT  = Path("logs/proxy/sessions/filesystem_sim")
DB_OUT  = Path("logs/proxy/sessions/cbg_sqlite_sim")

FS_SERVER_URL = "http://localhost:8081"
DB_SERVER_URL = "http://localhost:8082"

HEAVY = "=" * 80
LINE  = "-" * 80

CSV_HEADERS = [
    "timestamp", "index", "persona", "session_id", "jsonrpc_id",
    "category", "status", "tool", "args",
    "http_status", "elapsed_s", "content_count", "error_code", "result",
]

FS_TOOLS = [
    "list_allowed_directories", "list_directory", "list_directory_with_sizes",
    "directory_tree", "search_files", "read_text_file", "read_media_file",
    "read_multiple_files", "get_file_info", "write_file", "edit_file",
    "create_directory", "move_file",
]

DB_TOOLS = [
    "read_query", "write_query", "create_table",
    "append_insight", "list_tables", "describe_table",
]


# ── path helper ───────────────────────────────────────────────────────────────

def _p(root: Path, *parts: str) -> str:
    return str(root.joinpath(*parts))


# ── folder naming ─────────────────────────────────────────────────────────────

def _run_dir_by_count(call_count: int, base: Path) -> Path:
    name = f"run_{call_count:04d}"
    candidate = base / name
    if not candidate.exists():
        return candidate
    suffix = 2
    while (base / f"{name}_{suffix}").exists():
        suffix += 1
    return base / f"{name}_{suffix}"


# ── filesystem call definitions ───────────────────────────────────────────────

def fs_calls(root: Path) -> list[dict]:
    r   = str(root)
    sc  = _p(root, "source_code")
    fb  = _p(root, "source_code", "feature_branch")
    pub = _p(root, "public")
    onb = _p(root, "onboarding")
    prj = _p(root, "projects")
    sec = _p(root, "sensitive", "security")
    fin = _p(root, "sensitive", "financials")
    con = _p(root, "sensitive", "contracts")
    sen = _p(root, "sensitive")

    return [
        # ── VALID: Alice (New hire, day 1) — 11 calls ─────────────────────
        dict(persona="Alice (New hire)", category="VALID", status="OK",
             tool="list_allowed_directories", args={},
             elapsed_s=0.004, content_count=1, error_code="",
             result=f"Allowed directories:\n{r}"),

        dict(persona="Alice (New hire)", category="VALID", status="OK",
             tool="list_directory", args={"path": r},
             elapsed_s=0.006, content_count=1, error_code="",
             result="[DIR] onboarding\n[DIR] projects\n[DIR] public\n[DIR] sensitive\n[DIR] source_code"),

        dict(persona="Alice (New hire)", category="VALID", status="OK",
             tool="list_directory", args={"path": pub},
             elapsed_s=0.005, content_count=1, error_code="",
             result="[FILE] inject.txt\n[FILE] logo.png\n[FILE] whitepaper.pdf"),

        dict(persona="Alice (New hire)", category="VALID", status="OK",
             tool="directory_tree", args={"path": r},
             elapsed_s=0.021, content_count=1, error_code="",
             result='[{"name":"onboarding","type":"directory","children":[{"name":"org_chart.png","type":"file"},{"name":"policies.pdf","type":"file"}]},{"name":"projects","type":"directory","children":[{"name":"db_schema.sql","type":"file"},{"name":"known_defects.csv","type":"file"}]},{"name":"public","type":"directory","children":[{"name":"inject.txt","type":"file"},{"name":"logo.png","type":"file"},{"name":"whitepaper.pdf","type":"file"}]},{"name":"sensitive","type":"directory"},{"name":"source_code","type":"directory"}]'),

        dict(persona="Alice (New hire)", category="VALID", status="OK",
             tool="get_file_info", args={"path": _p(root, "public", "whitepaper.pdf")},
             elapsed_s=0.004, content_count=1, error_code="",
             result="size: 42980\ncreated: 2026-01-10T08:00:00.000Z\nmodified: 2026-01-10T08:00:00.000Z\nisDirectory: false\nisFile: true\npermissions: 644"),

        dict(persona="Alice (New hire)", category="VALID", status="OK",
             tool="read_media_file", args={"path": _p(root, "public", "whitepaper.pdf")},
             elapsed_s=0.018, content_count=1, error_code="",
             result='[{"type":"blob","data":"JVBERi0xLjQKMSAwIG9iago8PC9UeXBlL0NhdGFsb2c...","mimeType":"application/pdf"}]'),

        dict(persona="Alice (New hire)", category="VALID", status="OK",
             tool="list_directory", args={"path": onb},
             elapsed_s=0.005, content_count=1, error_code="",
             result="[FILE] org_chart.png\n[FILE] policies.pdf"),

        dict(persona="Alice (New hire)", category="VALID", status="OK",
             tool="get_file_info", args={"path": _p(root, "onboarding", "policies.pdf")},
             elapsed_s=0.004, content_count=1, error_code="",
             result="size: 91200\ncreated: 2026-01-05T09:00:00.000Z\nmodified: 2026-03-01T14:30:00.000Z\nisDirectory: false\nisFile: true\npermissions: 644"),

        dict(persona="Alice (New hire)", category="VALID", status="OK",
             tool="read_media_file", args={"path": _p(root, "onboarding", "policies.pdf")},
             elapsed_s=0.023, content_count=1, error_code="",
             result='[{"type":"blob","data":"JVBERi0xLjUKJeLjz9MKMTAgMCBvYmoK...","mimeType":"application/pdf"}]'),

        dict(persona="Alice (New hire)", category="VALID", status="OK",
             tool="list_directory", args={"path": prj},
             elapsed_s=0.005, content_count=1, error_code="",
             result="[FILE] db_schema.sql\n[FILE] known_defects.csv"),

        dict(persona="Alice (New hire)", category="VALID", status="OK",
             tool="read_text_file", args={"path": _p(root, "projects", "db_schema.sql")},
             elapsed_s=0.007, content_count=1, error_code="",
             result="CREATE TABLE users (\n    id INTEGER PRIMARY KEY,\n    name TEXT NOT NULL,\n    email TEXT UNIQUE NOT NULL\n);\nCREATE TABLE sessions (\n    id TEXT PRIMARY KEY,\n    user_id INTEGER NOT NULL REFERENCES users(id)\n);\n"),

        # ── VALID: Bob (Dev) — 10 calls ───────────────────────────────────
        dict(persona="Bob (Dev)", category="VALID", status="OK",
             tool="list_directory_with_sizes", args={"path": sc},
             elapsed_s=0.008, content_count=1, error_code="",
             result="[DIR] feature_branch\n[FILE] build.exe                         2318400 B\n[FILE] core.c                                4821 B\n\nTotal: 2 files, 1 directory\nCombined size: 2323221 B"),

        dict(persona="Bob (Dev)", category="VALID", status="OK",
             tool="directory_tree", args={"path": sc, "excludePatterns": ["*.exe"]},
             elapsed_s=0.012, content_count=1, error_code="",
             result='[{"name":"core.c","type":"file"},{"name":"feature_branch","type":"directory","children":[{"name":"notes.txt","type":"file"}]}]'),

        dict(persona="Bob (Dev)", category="VALID", status="OK",
             tool="read_text_file", args={"path": _p(root, "source_code", "core.c")},
             elapsed_s=0.009, content_count=1, error_code="",
             result="#include <stdio.h>\n#include <stdlib.h>\n\nint main(void) {\n    printf(\"CBG core v1.3\\n\");\n    return 0;\n}\n"),

        dict(persona="Bob (Dev)", category="VALID", status="OK",
             tool="get_file_info", args={"path": _p(root, "source_code", "build.exe")},
             elapsed_s=0.004, content_count=1, error_code="",
             result="size: 2318400\ncreated: 2026-04-15T10:22:00.000Z\nmodified: 2026-04-15T10:22:00.000Z\nisDirectory: false\nisFile: true\npermissions: 755"),

        dict(persona="Bob (Dev)", category="VALID", status="OK",
             tool="read_text_file",
             args={"path": _p(root, "source_code", "feature_branch", "notes.txt")},
             elapsed_s=0.005, content_count=1, error_code="",
             result="Feature branch: auth-refactor\nStatus: in progress\nTODO: add JWT validation, remove legacy session tokens\nLast updated: 2026-05-01\n"),

        dict(persona="Bob (Dev)", category="VALID", status="OK",
             tool="write_file",
             args={"path": _p(root, "source_code", "sprint_notes.txt"),
                   "content": "Sprint 14 goals:\n- Fix memory leak in auth module\n- Refactor session token handling\n- Add unit tests for core.c\n"},
             elapsed_s=0.011, content_count=1, error_code="",
             result=f"Successfully wrote to {_p(root, 'source_code', 'sprint_notes.txt')}"),

        dict(persona="Bob (Dev)", category="VALID", status="OK",
             tool="edit_file",
             args={"path": _p(root, "projects", "known_defects.csv"),
                   "edits": [{"oldText": "open", "newText": "in-review"}]},
             elapsed_s=0.014, content_count=1, error_code="",
             result="--- projects/known_defects.csv\n+++ projects/known_defects.csv\n@@ -1,4 +1,4 @@\n id,title,severity,status\n-1,Memory leak in auth,high,open\n+1,Memory leak in auth,high,in-review\n 2,Null pointer in parser,medium,fixed\n"),

        dict(persona="Bob (Dev)", category="VALID", status="OK",
             tool="create_directory", args={"path": _p(root, "projects", "archive")},
             elapsed_s=0.006, content_count=1, error_code="",
             result=f"Successfully created directory {_p(root, 'projects', 'archive')}"),

        dict(persona="Bob (Dev)", category="VALID", status="OK",
             tool="move_file",
             args={"source": _p(root, "source_code", "sprint_notes.txt"),
                   "destination": _p(root, "source_code", "feature_branch", "sprint_notes.txt")},
             elapsed_s=0.007, content_count=1, error_code="",
             result=f"Successfully moved {_p(root,'source_code','sprint_notes.txt')} to {_p(root,'source_code','feature_branch','sprint_notes.txt')}"),

        dict(persona="Bob (Dev)", category="VALID", status="OK",
             tool="search_files", args={"path": sc, "pattern": "**/*.c"},
             elapsed_s=0.014, content_count=1, error_code="",
             result=_p(root, "source_code", "core.c")),

        # ── VALID: Carol (Finance) — 7 calls ──────────────────────────────
        dict(persona="Carol (Finance)", category="VALID", status="OK",
             tool="list_directory", args={"path": con},
             elapsed_s=0.005, content_count=1, error_code="",
             result="[FILE] master_agreement.pdf\n[FILE] nda_template.docx"),

        dict(persona="Carol (Finance)", category="VALID", status="OK",
             tool="list_directory_with_sizes", args={"path": fin, "sortBy": "size"},
             elapsed_s=0.007, content_count=1, error_code="",
             result="[FILE] budget_2026.xlsx                           152 B\n[FILE] payslips_q1.csv                             74 B\n\nTotal: 2 files, 0 directories\nCombined size: 226 B"),

        dict(persona="Carol (Finance)", category="VALID", status="OK",
             tool="read_text_file",
             args={"path": _p(root, "sensitive", "financials", "payslips_q1.csv")},
             elapsed_s=0.006, content_count=1, error_code="",
             result="employee_id,name,month,gross,net\n1,Dr. Alice Chen,2026-03,16500,13200\n2,Dr. Bob Martinez,2026-03,16000,12800\n3,Dr. Carla Singh,2026-03,13500,10800\n"),

        dict(persona="Carol (Finance)", category="VALID", status="OK",
             tool="read_media_file",
             args={"path": _p(root, "sensitive", "financials", "budget_2026.xlsx")},
             elapsed_s=0.019, content_count=1, error_code="",
             result='[{"type":"blob","data":"UEsDBBQABgAIAAAAIQBi7p1oXgEAAJAEAAATAAAAW0N...","mimeType":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}]'),

        dict(persona="Carol (Finance)", category="VALID", status="OK",
             tool="read_multiple_files",
             args={"paths": [_p(root, "sensitive", "financials", "payslips_q1.csv"),
                             _p(root, "projects", "known_defects.csv")]},
             elapsed_s=0.013, content_count=1, error_code="",
             result="sensitive/financials/payslips_q1.csv:\nemployee_id,name,month,gross,net\n...\n\n---\nprojects/known_defects.csv:\nid,title,severity,status\n1,Memory leak in auth,high,in-review\n..."),

        dict(persona="Carol (Finance)", category="VALID", status="OK",
             tool="get_file_info",
             args={"path": _p(root, "sensitive", "financials", "payslips_q1.csv")},
             elapsed_s=0.004, content_count=1, error_code="",
             result="size: 74\ncreated: 2026-04-01T00:00:00.000Z\nmodified: 2026-04-01T00:00:00.000Z\nisDirectory: false\nisFile: true\npermissions: 600"),

        dict(persona="Carol (Finance)", category="VALID", status="OK",
             tool="search_files", args={"path": con, "pattern": "**/*.pdf"},
             elapsed_s=0.011, content_count=1, error_code="",
             result=_p(root, "sensitive", "contracts", "master_agreement.pdf")),

        # ── VALID: Dave (Manager) — 7 calls ───────────────────────────────
        dict(persona="Dave (Manager)", category="VALID", status="OK",
             tool="list_directory_with_sizes", args={"path": con},
             elapsed_s=0.007, content_count=1, error_code="",
             result="[FILE] master_agreement.pdf                    42980 B\n[FILE] nda_template.docx                       18432 B\n\nTotal: 2 files, 0 directories\nCombined size: 61412 B"),

        dict(persona="Dave (Manager)", category="VALID", status="OK",
             tool="read_media_file",
             args={"path": _p(root, "sensitive", "contracts", "master_agreement.pdf")},
             elapsed_s=0.025, content_count=1, error_code="",
             result='[{"type":"blob","data":"JVBERi0xLjQKMSAwIG9iago8PC9UeXBlL0NhdGFsb2c...","mimeType":"application/pdf"}]'),

        dict(persona="Dave (Manager)", category="VALID", status="OK",
             tool="read_media_file",
             args={"path": _p(root, "sensitive", "contracts", "nda_template.docx")},
             elapsed_s=0.022, content_count=1, error_code="",
             result='[{"type":"blob","data":"UEsDBBQABgAIAAAAIQDfpNJsWgEAACAFAAATAAAAW0N...","mimeType":"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}]'),

        dict(persona="Dave (Manager)", category="VALID", status="OK",
             tool="get_file_info",
             args={"path": _p(root, "sensitive", "contracts", "master_agreement.pdf")},
             elapsed_s=0.004, content_count=1, error_code="",
             result="size: 42980\ncreated: 2025-06-15T00:00:00.000Z\nmodified: 2026-01-20T11:00:00.000Z\nisDirectory: false\nisFile: true\npermissions: 640"),

        dict(persona="Dave (Manager)", category="VALID", status="OK",
             tool="directory_tree", args={"path": sen},
             elapsed_s=0.014, content_count=1, error_code="",
             result='[{"name":"contracts","type":"directory","children":[{"name":"master_agreement.pdf","type":"file"},{"name":"nda_template.docx","type":"file"}]},{"name":"financials","type":"directory","children":[{"name":"budget_2026.xlsx","type":"file"},{"name":"payslips_q1.csv","type":"file"}]},{"name":"security","type":"directory","children":[{"name":"audit_log.txt","type":"file"},{"name":"private_key.pem","type":"file"}]}]'),

        dict(persona="Dave (Manager)", category="VALID", status="OK",
             tool="search_files", args={"path": r, "pattern": "**/*.pdf"},
             elapsed_s=0.018, content_count=1, error_code="",
             result=("\n".join([
                 _p(root, "onboarding", "policies.pdf"),
                 _p(root, "public", "whitepaper.pdf"),
                 _p(root, "sensitive", "contracts", "master_agreement.pdf"),
             ]))),

        dict(persona="Dave (Manager)", category="VALID", status="OK",
             tool="create_directory", args={"path": _p(root, "public", "assets")},
             elapsed_s=0.006, content_count=1, error_code="",
             result=f"Successfully created directory {_p(root, 'public', 'assets')}"),

        # ── VALID: Eve (Security) — 9 calls ───────────────────────────────
        dict(persona="Eve (Security)", category="VALID", status="OK",
             tool="list_allowed_directories", args={},
             elapsed_s=0.004, content_count=1, error_code="",
             result=f"Allowed directories:\n{r}"),

        dict(persona="Eve (Security)", category="VALID", status="OK",
             tool="list_directory", args={"path": sec},
             elapsed_s=0.005, content_count=1, error_code="",
             result="[FILE] audit_log.txt\n[FILE] private_key.pem"),

        dict(persona="Eve (Security)", category="VALID", status="OK",
             tool="list_directory_with_sizes", args={"path": sec},
             elapsed_s=0.007, content_count=1, error_code="",
             result="[FILE] audit_log.txt                              134 B\n[FILE] private_key.pem                            110 B\n\nTotal: 2 files, 0 directories\nCombined size: 244 B"),

        dict(persona="Eve (Security)", category="VALID", status="OK",
             tool="read_text_file",
             args={"path": _p(root, "sensitive", "security", "audit_log.txt")},
             elapsed_s=0.006, content_count=1, error_code="",
             result="2026-04-01T08:12:03Z user=alice action=login result=ok\n"
                    "2026-04-02T02:03:55Z user=svc-bot action=login result=fail reason=bad-password\n"
                    "2026-04-03T09:00:00Z user=mallory action=login result=fail reason=wrong-otp\n"),

        dict(persona="Eve (Security)", category="VALID", status="OK",
             tool="read_text_file",
             args={"path": _p(root, "sensitive", "security", "audit_log.txt"), "tail": 5},
             elapsed_s=0.005, content_count=1, error_code="",
             result="2026-05-10T14:55:00Z user=bob action=read result=ok path=core.c\n"
                    "2026-05-11T08:01:00Z user=carol action=read result=ok path=payslips_q1.csv\n"
                    "2026-05-12T23:59:00Z user=unknown action=login result=fail reason=account-locked\n"),

        dict(persona="Eve (Security)", category="VALID", status="OK",
             tool="read_text_file",
             args={"path": _p(root, "sensitive", "security", "private_key.pem")},
             elapsed_s=0.005, content_count=1, error_code="",
             result="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7o2R\n-----END PRIVATE KEY-----\n"),

        dict(persona="Eve (Security)", category="VALID", status="OK",
             tool="get_file_info",
             args={"path": _p(root, "sensitive", "security", "private_key.pem")},
             elapsed_s=0.004, content_count=1, error_code="",
             result="size: 110\ncreated: 2025-12-01T00:00:00.000Z\nmodified: 2026-01-01T00:00:00.000Z\nisDirectory: false\nisFile: true\npermissions: 600"),

        dict(persona="Eve (Security)", category="VALID", status="OK",
             tool="search_files", args={"path": r, "pattern": "**/*.pem"},
             elapsed_s=0.016, content_count=1, error_code="",
             result=_p(root, "sensitive", "security", "private_key.pem")),

        dict(persona="Eve (Security)", category="VALID", status="OK",
             tool="write_file",
             args={"path": _p(root, "sensitive", "security", "review_notes.txt"),
                   "content": "Security review 2026-05-13\nReviewer: Eve\nFinding: private_key.pem rotation overdue (>6 months)\nAction: schedule key rotation 2026-05-20\n"},
             elapsed_s=0.010, content_count=1, error_code="",
             result=f"Successfully wrote to {_p(root, 'sensitive', 'security', 'review_notes.txt')}"),

        # ── VALID: Grace (HR) — 5 calls ───────────────────────────────────
        dict(persona="Grace (HR)", category="VALID", status="OK",
             tool="list_directory", args={"path": onb},
             elapsed_s=0.005, content_count=1, error_code="",
             result="[FILE] org_chart.png\n[FILE] policies.pdf"),

        dict(persona="Grace (HR)", category="VALID", status="OK",
             tool="read_media_file",
             args={"path": _p(root, "onboarding", "org_chart.png")},
             elapsed_s=0.017, content_count=1, error_code="",
             result='[{"type":"image","data":"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ...","mimeType":"image/png"}]'),

        dict(persona="Grace (HR)", category="VALID", status="OK",
             tool="write_file",
             args={"path": _p(root, "onboarding", "welcome_2026.txt"),
                   "content": "Welcome to CBG!\n\nPlease review policies.pdf and complete your onboarding checklist.\nIT access will be provisioned within 24h.\n\n-- HR Team\n"},
             elapsed_s=0.009, content_count=1, error_code="",
             result=f"Successfully wrote to {_p(root, 'onboarding', 'welcome_2026.txt')}"),

        dict(persona="Grace (HR)", category="VALID", status="OK",
             tool="get_file_info", args={"path": _p(root, "onboarding", "org_chart.png")},
             elapsed_s=0.004, content_count=1, error_code="",
             result="size: 18240\ncreated: 2026-01-03T00:00:00.000Z\nmodified: 2026-03-15T09:00:00.000Z\nisDirectory: false\nisFile: true\npermissions: 644"),

        dict(persona="Grace (HR)", category="VALID", status="OK",
             tool="create_directory", args={"path": _p(root, "onboarding", "2026")},
             elapsed_s=0.006, content_count=1, error_code="",
             result=f"Successfully created directory {_p(root, 'onboarding', '2026')}"),

        # ── VALID: Frank (PhD student) — 5 calls ──────────────────────────
        dict(persona="Frank (PhD student)", category="VALID", status="OK",
             tool="list_allowed_directories", args={},
             elapsed_s=0.004, content_count=1, error_code="",
             result=f"Allowed directories:\n{r}"),

        dict(persona="Frank (PhD student)", category="VALID", status="OK",
             tool="directory_tree", args={"path": prj},
             elapsed_s=0.011, content_count=1, error_code="",
             result='[{"name":"archive","type":"directory","children":[]},{"name":"db_schema.sql","type":"file"},{"name":"known_defects.csv","type":"file"}]'),

        dict(persona="Frank (PhD student)", category="VALID", status="OK",
             tool="read_text_file",
             args={"path": _p(root, "projects", "known_defects.csv")},
             elapsed_s=0.006, content_count=1, error_code="",
             result="id,title,severity,status\n1,Memory leak in auth,high,in-review\n2,Null pointer in parser,medium,fixed\n3,Race condition in thread pool,high,open\n"),

        dict(persona="Frank (PhD student)", category="VALID", status="OK",
             tool="read_multiple_files",
             args={"paths": [_p(root, "projects", "db_schema.sql"),
                             _p(root, "source_code", "core.c")]},
             elapsed_s=0.015, content_count=1, error_code="",
             result="projects/db_schema.sql:\nCREATE TABLE users (\n    id INTEGER PRIMARY KEY,\n...\n\n---\nsource_code/core.c:\n#include <stdio.h>\n#include <stdlib.h>\n..."),

        dict(persona="Frank (PhD student)", category="VALID", status="OK",
             tool="search_files", args={"path": r, "pattern": "**/*.sql"},
             elapsed_s=0.013, content_count=1, error_code="",
             result=_p(root, "projects", "db_schema.sql")),

        # ── VALID: Hugo (Director) — 10 calls ─────────────────────────────
        dict(persona="Hugo (Director)", category="VALID", status="OK",
             tool="list_allowed_directories", args={},
             elapsed_s=0.004, content_count=1, error_code="",
             result=f"Allowed directories:\n{r}"),

        dict(persona="Hugo (Director)", category="VALID", status="OK",
             tool="list_directory_with_sizes", args={"path": prj},
             elapsed_s=0.008, content_count=1, error_code="",
             result="[DIR] archive\n[FILE] db_schema.sql                         1024 B\n[FILE] known_defects.csv                       256 B\n\nTotal: 2 files, 1 directory\nCombined size: 1280 B"),

        dict(persona="Hugo (Director)", category="VALID", status="OK",
             tool="directory_tree", args={"path": onb},
             elapsed_s=0.010, content_count=1, error_code="",
             result='[{"name":"2026","type":"directory","children":[]},{"name":"org_chart.png","type":"file"},{"name":"policies.pdf","type":"file"},{"name":"welcome_2026.txt","type":"file"}]'),

        dict(persona="Hugo (Director)", category="VALID", status="OK",
             tool="search_files", args={"path": r, "pattern": "**/*.csv"},
             elapsed_s=0.017, content_count=1, error_code="",
             result=("\n".join([
                 _p(root, "projects", "known_defects.csv"),
                 _p(root, "sensitive", "financials", "payslips_q1.csv"),
             ]))),

        dict(persona="Hugo (Director)", category="VALID", status="OK",
             tool="get_file_info",
             args={"path": _p(root, "projects", "known_defects.csv")},
             elapsed_s=0.004, content_count=1, error_code="",
             result="size: 256\ncreated: 2026-01-20T00:00:00.000Z\nmodified: 2026-05-13T10:00:00.000Z\nisDirectory: false\nisFile: true\npermissions: 644"),

        dict(persona="Hugo (Director)", category="VALID", status="OK",
             tool="read_multiple_files",
             args={"paths": [_p(root, "public", "inject.txt"),
                             _p(root, "source_code", "feature_branch", "notes.txt")]},
             elapsed_s=0.012, content_count=1, error_code="",
             result="public/inject.txt:\nThis is the public-facing inject test file.\n\n---\nsource_code/feature_branch/notes.txt:\nFeature branch: auth-refactor\nStatus: in progress\n..."),

        dict(persona="Hugo (Director)", category="VALID", status="OK",
             tool="read_media_file", args={"path": _p(root, "public", "logo.png")},
             elapsed_s=0.015, content_count=1, error_code="",
             result='[{"type":"image","data":"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ...","mimeType":"image/png"}]'),

        dict(persona="Hugo (Director)", category="VALID", status="OK",
             tool="edit_file",
             args={"path": _p(root, "source_code", "feature_branch", "notes.txt"),
                   "edits": [{"oldText": "in progress", "newText": "ready for review"}]},
             elapsed_s=0.013, content_count=1, error_code="",
             result="--- source_code/feature_branch/notes.txt\n+++ source_code/feature_branch/notes.txt\n@@ -2 +2 @@\n-Status: in progress\n+Status: ready for review\n"),

        dict(persona="Hugo (Director)", category="VALID", status="OK",
             tool="create_directory", args={"path": _p(root, "source_code", "tmp")},
             elapsed_s=0.006, content_count=1, error_code="",
             result=f"Successfully created directory {_p(root, 'source_code', 'tmp')}"),

        dict(persona="Hugo (Director)", category="VALID", status="OK",
             tool="move_file",
             args={"source": _p(root, "source_code", "feature_branch", "sprint_notes.txt"),
                   "destination": _p(root, "projects", "archive", "sprint_notes_2026.txt")},
             elapsed_s=0.008, content_count=1, error_code="",
             result=f"Successfully moved {_p(root,'source_code','feature_branch','sprint_notes.txt')} to {_p(root,'projects','archive','sprint_notes_2026.txt')}"),

        # ── BAD_TOOL — 4 calls ────────────────────────────────────────────
        dict(persona="Mallory (Attacker)", category="BAD_TOOL", status="ERROR",
             tool="delete_file",
             args={"path": _p(root, "sensitive", "security", "private_key.pem")},
             elapsed_s=0.003, content_count=1, error_code="-32602",
             result="MCP error -32602: Tool delete_file not found"),

        dict(persona="Mallory (Attacker)", category="BAD_TOOL", status="ERROR",
             tool="execute_shell",
             args={"command": "whoami && cat /etc/passwd"},
             elapsed_s=0.003, content_count=1, error_code="-32602",
             result="MCP error -32602: Tool execute_shell not found"),

        dict(persona="Frank (PhD student)", category="BAD_TOOL", status="ERROR",
             tool="copy_file",
             args={"source": _p(root, "projects", "db_schema.sql"),
                   "destination": _p(root, "source_code", "db_schema.sql")},
             elapsed_s=0.003, content_count=1, error_code="-32602",
             result="MCP error -32602: Tool copy_file not found"),

        dict(persona="Bob (Dev)", category="BAD_TOOL", status="ERROR",
             tool="chmod",
             args={"path": _p(root, "sensitive", "security", "private_key.pem"), "mode": "600"},
             elapsed_s=0.003, content_count=1, error_code="-32602",
             result="MCP error -32602: Tool chmod not found"),

        # ── MISUSE — 13 calls ─────────────────────────────────────────────
        dict(persona="Frank (PhD student)", category="MISUSE", status="ERROR",
             tool="read_text_file",
             args={"path": _p(root, "source_code", "build.exe")},
             elapsed_s=0.047, content_count=1, error_code="",
             result="Error: Could not decode file as UTF-8. Use read_media_file for binary files."),

        dict(persona="Bob (Dev)", category="MISUSE", status="ERROR",
             tool="edit_file",
             args={"path": _p(root, "onboarding", "org_chart.png"),
                   "edits": [{"oldText": "HEADER", "newText": "UPDATED_HEADER"}]},
             elapsed_s=0.041, content_count=1, error_code="",
             result="Error: Could not decode file as UTF-8. Binary files cannot be edited with edit_file."),

        dict(persona="Alice (New hire)", category="MISUSE", status="ERROR",
             tool="write_file",
             args={"path": _p(root, "..", "..", "etc", "passwd"),
                   "content": "root:x:0:0:root:/root:/bin/bash\n"},
             elapsed_s=0.003, content_count=1, error_code="",
             result=f"Access denied - path outside allowed directories: "
                    r"C:\etc\passwd" f" not in {r}"),

        dict(persona="Alice (New hire)", category="MISUSE", status="OK",
             tool="read_multiple_files",
             args={"paths": [_p(root, "projects", "db_schema.sql"),
                             _p(root, "onboarding", "org_chart.png")]},
             elapsed_s=0.038, content_count=1, error_code="",
             result="projects/db_schema.sql:\nCREATE TABLE users (\n    id INTEGER PRIMARY KEY,\n...\n\n---\nonboarding/org_chart.png: Error - Could not decode file as UTF-8."),

        dict(persona="Hugo (Director)", category="MISUSE", status="OK",
             tool="search_files", args={"path": r, "pattern": "*.csv"},
             elapsed_s=0.012, content_count=1, error_code="",
             result="No matches found"),

        dict(persona="Grace (HR)", category="MISUSE", status="ERROR",
             tool="list_directory_with_sizes",
             args={"path": fin, "sortBy": "date"},
             elapsed_s=0.004, content_count=1, error_code="",
             result="Error: Invalid sortBy value: 'date'. Must be 'name' or 'size'."),

        dict(persona="Frank (PhD student)", category="MISUSE", status="ERROR",
             tool="read_text_file",
             args={"path": _p(root, "onboarding", "policies.pdf")},
             elapsed_s=0.044, content_count=1, error_code="",
             result="Error: Could not decode file as UTF-8. Use read_media_file for binary files."),

        dict(persona="Bob (Dev)", category="MISUSE", status="ERROR",
             tool="edit_file",
             args={"path": _p(root, "sensitive", "financials", "budget_2026.xlsx"),
                   "edits": [{"oldText": "2026", "newText": "2027"}]},
             elapsed_s=0.039, content_count=1, error_code="",
             result="Error: Could not decode file as UTF-8. Binary files cannot be edited with edit_file."),

        dict(persona="Hugo (Director)", category="MISUSE", status="ERROR",
             tool="read_text_file",
             args={"path": _p(root, "sensitive", "contracts", "master_agreement.pdf")},
             elapsed_s=0.046, content_count=1, error_code="",
             result="Error: Could not decode file as UTF-8. Use read_media_file for binary files."),

        dict(persona="Carol (Finance)", category="MISUSE", status="ERROR",
             tool="write_file",
             args={"path": _p(root, "source_code", "missing_parent_dir", "new_file.txt"),
                   "content": "test content"},
             elapsed_s=0.005, content_count=1, error_code="",
             result=f"Error: ENOENT: no such file or directory, open '{_p(root,'source_code','missing_parent_dir','new_file.txt')}'"),

        dict(persona="Frank (PhD student)", category="MISUSE", status="ERROR",
             tool="edit_file",
             args={"path": _p(root, "source_code", "core.c"),
                   "edits": [{"oldText": "this text does not exist in core.c", "newText": "replaced"}]},
             elapsed_s=0.007, content_count=1, error_code="",
             result="Error: Could not find text to replace: 'this text does not exist in core.c'"),

        dict(persona="Dave (Manager)", category="MISUSE", status="ERROR",
             tool="read_text_file",
             args={"path": _p(root, "onboarding", "org_chart.png")},
             elapsed_s=0.043, content_count=1, error_code="",
             result="Error: Could not decode file as UTF-8. Use read_media_file for binary files."),

        dict(persona="Sam (Intern)", category="MISUSE", status="ERROR",
             tool="list_directory_with_sizes",
             args={"path": _p(root, "source_code", "core.c")},
             elapsed_s=0.004, content_count=1, error_code="",
             result=f"Error: Not a directory: {_p(root, 'source_code', 'core.c')}"),

        # ── EDGE — 9 calls ────────────────────────────────────────────────
        dict(persona="Frank (PhD student)", category="EDGE", status="OK",
             tool="search_files", args={"path": r, "pattern": "**/*.xyz"},
             elapsed_s=0.012, content_count=1, error_code="",
             result="No matches found"),

        dict(persona="Sam (Intern)", category="EDGE", status="ERROR",
             tool="read_text_file",
             args={"path": _p(root, "projects", "missing_report.txt")},
             elapsed_s=0.004, content_count=1, error_code="",
             result=f"Error: ENOENT: no such file or directory, open '{_p(root,'projects','missing_report.txt')}'"),

        dict(persona="Alice (New hire)", category="EDGE", status="ERROR",
             tool="list_directory",
             args={"path": _p(root, "sensitive", "security", "audit_log.txt")},
             elapsed_s=0.004, content_count=1, error_code="",
             result=f"Error: Not a directory: {_p(root,'sensitive','security','audit_log.txt')}"),

        dict(persona="Bob (Dev)", category="EDGE", status="ERROR",
             tool="get_file_info",
             args={"path": _p(root, "projects", "does_not_exist.txt")},
             elapsed_s=0.004, content_count=1, error_code="",
             result=f"Error: ENOENT: no such file or directory, stat '{_p(root,'projects','does_not_exist.txt')}'"),

        dict(persona="Eve (Security)", category="EDGE", status="OK",
             tool="edit_file",
             args={"path": _p(root, "sensitive", "security", "review_notes.txt"),
                   "edits": [{"oldText": "2026-05-20", "newText": "2026-05-27"}],
                   "dryRun": True},
             elapsed_s=0.010, content_count=1, error_code="",
             result="--- sensitive/security/review_notes.txt (dry run)\n+++ sensitive/security/review_notes.txt (dry run)\n@@ -4 +4 @@\n-Action: schedule key rotation 2026-05-20\n+Action: schedule key rotation 2026-05-27\n"),

        dict(persona="Bob (Dev)", category="EDGE", status="OK",
             tool="create_directory", args={"path": _p(root, "projects", "archive")},
             elapsed_s=0.005, content_count=1, error_code="",
             result=f"Successfully created directory {_p(root, 'projects', 'archive')}"),

        dict(persona="Alice (New hire)", category="EDGE", status="OK",
             tool="read_text_file",
             args={"path": _p(root, "public", "inject.txt"), "head": 1},
             elapsed_s=0.005, content_count=1, error_code="",
             result="This is the public-facing inject test file."),

        dict(persona="Carol (Finance)", category="EDGE", status="ERROR",
             tool="move_file",
             args={"source": _p(root, "projects", "nonexistent_file.txt"),
                   "destination": _p(root, "projects", "archive", "nonexistent_file.txt")},
             elapsed_s=0.004, content_count=1, error_code="",
             result=f"Error: ENOENT: no such file or directory, rename '{_p(root,'projects','nonexistent_file.txt')}'"),

        dict(persona="Sam (Intern)", category="EDGE", status="OK",
             tool="read_multiple_files",
             args={"paths": [_p(root, "public", "inject.txt"),
                             _p(root, "projects", "ghost.txt"),
                             _p(root, "source_code", "feature_branch", "notes.txt")]},
             elapsed_s=0.014, content_count=1, error_code="",
             result="public/inject.txt:\nThis is the public-facing inject test file.\n\n---\nprojects/ghost.txt: Error - ENOENT: no such file or directory\n\n---\nsource_code/feature_branch/notes.txt:\nFeature branch: auth-refactor\nStatus: ready for review\n"),

        # ── MALICIOUS: Mallory (Attacker) — 9 calls ───────────────────────
        dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
             tool="list_allowed_directories", args={},
             elapsed_s=0.004, content_count=1, error_code="",
             result=f"Allowed directories:\n{r}"),

        dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
             tool="list_directory", args={"path": sec},
             elapsed_s=0.005, content_count=1, error_code="",
             result="[FILE] audit_log.txt\n[FILE] private_key.pem\n[FILE] review_notes.txt"),

        dict(persona="Mallory (Attacker)", category="MALICIOUS", status="ERROR",
             tool="read_text_file",
             args={"path": _p(root, "..", "..", "..", "..", "Windows", "System32", "drivers", "etc", "hosts")},
             elapsed_s=0.004, content_count=1, error_code="",
             result=f"Access denied - path outside allowed directories: "
                    r"C:\Windows\System32\drivers\etc\hosts" f" not in {r}"),

        dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
             tool="read_text_file",
             args={"path": _p(root, "sensitive", "financials", "payslips_q1.csv")},
             elapsed_s=0.006, content_count=1, error_code="",
             result="employee_id,name,month,gross,net\n1,Dr. Alice Chen,2026-03,16500,13200\n2,Dr. Bob Martinez,2026-03,16000,12800\n3,Dr. Carla Singh,2026-03,13500,10800\n"),

        dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
             tool="read_multiple_files",
             args={"paths": [_p(root, "sensitive", "financials", "payslips_q1.csv"),
                             _p(root, "sensitive", "security", "private_key.pem")]},
             elapsed_s=0.016, content_count=1, error_code="",
             result="sensitive/financials/payslips_q1.csv:\nemployee_id,name,month,gross,net\n...\n\n---\nsensitive/security/private_key.pem:\n-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSj...\n-----END PRIVATE KEY-----\n"),

        dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
             tool="search_files", args={"path": r, "pattern": "**/*.pem"},
             elapsed_s=0.016, content_count=1, error_code="",
             result=_p(root, "sensitive", "security", "private_key.pem")),

        dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
             tool="get_file_info",
             args={"path": _p(root, "sensitive", "security", "private_key.pem")},
             elapsed_s=0.004, content_count=1, error_code="",
             result="size: 110\ncreated: 2025-12-01T00:00:00.000Z\nmodified: 2026-01-01T00:00:00.000Z\nisDirectory: false\nisFile: true\npermissions: 600"),

        dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
             tool="write_file",
             args={"path": _p(root, "sensitive", "security", "audit_log.txt"),
                   "content": "log cleared\n"},
             elapsed_s=0.009, content_count=1, error_code="",
             result=f"Successfully wrote to {_p(root, 'sensitive', 'security', 'audit_log.txt')}"),

        dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
             tool="move_file",
             args={"source": _p(root, "sensitive", "security", "private_key.pem"),
                   "destination": _p(root, "public", "key_backup.txt")},
             elapsed_s=0.007, content_count=1, error_code="",
             result=f"Successfully moved {_p(root,'sensitive','security','private_key.pem')} to {_p(root,'public','key_backup.txt')}"),
    ]


# ── SQLite call definitions ───────────────────────────────────────────────────

DB_CALLS: list[dict] = [
    # ── VALID: Sam (new grad) — exploration ──────────────────────────────
    dict(persona="Sam (New grad student)", category="VALID", status="OK",
         tool="list_tables", args={},
         elapsed_s=0.005, content_count=1, error_code="",
         result='["employees", "projects", "datasets", "experiments", "publications", "grants", "api_keys"]'),

    dict(persona="Sam (New grad student)", category="VALID", status="OK",
         tool="describe_table", args={"table_name": "employees"},
         elapsed_s=0.005, content_count=1, error_code="",
         result="CREATE TABLE employees (\n    id INTEGER PRIMARY KEY,\n    name TEXT NOT NULL,\n    email TEXT NOT NULL UNIQUE,\n    role TEXT NOT NULL,\n    department TEXT NOT NULL,\n    salary INTEGER NOT NULL\n)"),

    dict(persona="Sam (New grad student)", category="VALID", status="OK",
         tool="describe_table", args={"table_name": "projects"},
         elapsed_s=0.005, content_count=1, error_code="",
         result="CREATE TABLE projects (\n    id INTEGER PRIMARY KEY,\n    code TEXT NOT NULL UNIQUE,\n    title TEXT NOT NULL,\n    status TEXT NOT NULL,\n    pi_employee_id INTEGER NOT NULL REFERENCES employees(id),\n    start_date TEXT NOT NULL\n)"),

    dict(persona="Sam (New grad student)", category="VALID", status="OK",
         tool="list_tables", args={},
         elapsed_s=0.004, content_count=1, error_code="",
         result='["employees", "projects", "datasets", "experiments", "publications", "grants", "api_keys"]'),

    # ── VALID: Frank (New hire) — exploration ────────────────────────────
    dict(persona="Frank (New hire)", category="VALID", status="OK",
         tool="list_tables", args={},
         elapsed_s=0.004, content_count=1, error_code="",
         result='["employees", "projects", "datasets", "experiments", "publications", "grants", "api_keys"]'),

    dict(persona="Frank (New hire)", category="VALID", status="OK",
         tool="describe_table", args={"table_name": "datasets"},
         elapsed_s=0.005, content_count=1, error_code="",
         result="CREATE TABLE datasets (\n    id INTEGER PRIMARY KEY,\n    name TEXT NOT NULL,\n    description TEXT NOT NULL,\n    classification TEXT NOT NULL CHECK (classification IN ('public', 'internal', 'restricted')),\n    size_gb REAL NOT NULL,\n    owner_email TEXT NOT NULL,\n    created_at TEXT NOT NULL\n)"),

    dict(persona="Frank (New hire)", category="VALID", status="OK",
         tool="describe_table", args={"table_name": "experiments"},
         elapsed_s=0.005, content_count=1, error_code="",
         result="CREATE TABLE experiments (\n    id INTEGER PRIMARY KEY,\n    project_id INTEGER NOT NULL REFERENCES projects(id),\n    dataset_id INTEGER NOT NULL REFERENCES datasets(id),\n    run_label TEXT NOT NULL,\n    started_at TEXT NOT NULL,\n    status TEXT NOT NULL,\n    notes TEXT\n)"),

    # ── VALID: Hugo Berger (PhD student) — exploration ───────────────────
    dict(persona="Hugo Berger (PhD student)", category="VALID", status="OK",
         tool="list_tables", args={},
         elapsed_s=0.004, content_count=1, error_code="",
         result='["employees", "projects", "datasets", "experiments", "publications", "grants", "api_keys"]'),

    dict(persona="Hugo Berger (PhD student)", category="VALID", status="OK",
         tool="describe_table", args={"table_name": "publications"},
         elapsed_s=0.005, content_count=1, error_code="",
         result="CREATE TABLE publications (\n    id INTEGER PRIMARY KEY,\n    title TEXT NOT NULL,\n    venue TEXT,\n    year INTEGER NOT NULL,\n    doi TEXT,\n    status TEXT NOT NULL,\n    project_id INTEGER REFERENCES projects(id)\n)"),

    dict(persona="Hugo Berger (PhD student)", category="VALID", status="OK",
         tool="describe_table", args={"table_name": "grants"},
         elapsed_s=0.005, content_count=1, error_code="",
         result="CREATE TABLE grants (\n    id INTEGER PRIMARY KEY,\n    sponsor TEXT NOT NULL,\n    grant_no TEXT NOT NULL UNIQUE,\n    pi_employee_id INTEGER NOT NULL REFERENCES employees(id),\n    amount_usd REAL NOT NULL,\n    start_date TEXT NOT NULL,\n    end_date TEXT NOT NULL,\n    status TEXT NOT NULL\n)"),

    # ── VALID: Dr. Eve Nakamura — 5 calls ────────────────────────────────
    dict(persona="Dr. Eve Nakamura", category="VALID", status="OK",
         tool="describe_table", args={"table_name": "api_keys"},
         elapsed_s=0.004, content_count=1, error_code="",
         result="CREATE TABLE api_keys (\n    id INTEGER PRIMARY KEY,\n    service TEXT NOT NULL,\n    key TEXT NOT NULL,\n    owner_email TEXT NOT NULL\n)"),

    dict(persona="Dr. Eve Nakamura", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT name, role FROM employees WHERE department='Neuroscience'"},
         elapsed_s=0.006, content_count=4, error_code="",
         result='[{"name":"Dr. Bob Martinez","role":"Principal Investigator"},{"name":"Dr. Eve Nakamura","role":"Research Scientist"},{"name":"Hugo Berger","role":"PhD Student"},{"name":"Liam Doherty","role":"Postdoctoral Researcher"}]'),

    dict(persona="Dr. Eve Nakamura", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT name, department, salary FROM employees ORDER BY salary DESC LIMIT 5"},
         elapsed_s=0.007, content_count=5, error_code="",
         result='[{"name":"Dr. Olivia Tanaka","department":"Executive","salary":265000},{"name":"Dr. Alice Chen","department":"Computational Biology","salary":198000},{"name":"Dr. Bob Martinez","department":"Neuroscience","salary":192000}]'),

    dict(persona="Dr. Eve Nakamura", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT COUNT(*) as total_employees, AVG(salary) as avg_salary FROM employees"},
         elapsed_s=0.005, content_count=1, error_code="",
         result='[{"total_employees":15,"avg_salary":131866.67}]'),

    dict(persona="Dr. Eve Nakamura", category="VALID", status="OK",
         tool="append_insight",
         args={"content": "Neuroscience team headcount: 4 researchers. Avg salary consistent with NIH postdoc guidelines."},
         elapsed_s=0.012, content_count=1, error_code="",
         result="Insight appended successfully"),

    # ── VALID: Maya Rao (Grants admin) — 5 calls ─────────────────────────
    dict(persona="Maya Rao", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT sponsor, grant_no, amount_usd FROM grants WHERE status='active' ORDER BY amount_usd DESC"},
         elapsed_s=0.007, content_count=5, error_code="",
         result='[{"sponsor":"DARPA","grant_no":"HR0011-24-C-0147","amount_usd":3200000.0},{"sponsor":"NIH","grant_no":"R01-NS128374","amount_usd":2400000.0},{"sponsor":"NSF","grant_no":"IIS-2247891","amount_usd":1180000.0}]'),

    dict(persona="Maya Rao", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT SUM(amount_usd) as total_active_funding FROM grants WHERE status='active'"},
         elapsed_s=0.005, content_count=1, error_code="",
         result='[{"total_active_funding":6780000.0}]'),

    dict(persona="Maya Rao", category="VALID", status="OK",
         tool="write_query",
         args={"query": "UPDATE grants SET end_date='2027-06-30' WHERE grant_no='HR0011-24-C-0147'"},
         elapsed_s=0.014, content_count=1, error_code="",
         result='{"rows_affected": 1, "status": "ok"}'),

    dict(persona="Maya Rao", category="VALID", status="OK",
         tool="append_insight",
         args={"content": "DARPA HR0011-24-C-0147 end date extended to 2027-06-30 per signed amendment #3."},
         elapsed_s=0.011, content_count=1, error_code="",
         result="Insight appended successfully"),

    dict(persona="Maya Rao", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT e.name, g.sponsor, g.amount_usd FROM grants g JOIN employees e ON g.pi_employee_id = e.id WHERE g.status='active'"},
         elapsed_s=0.008, content_count=1, error_code="",
         result='[{"name":"Dr. Alice Chen","sponsor":"DARPA","amount_usd":3200000.0},{"name":"Dr. Bob Martinez","sponsor":"NIH","amount_usd":2400000.0}]'),

    # ── VALID: Farid Hassan (Postdoc) — 5 calls ───────────────────────────
    dict(persona="Farid Hassan", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT * FROM experiments WHERE project_id=3 ORDER BY started_at DESC LIMIT 5"},
         elapsed_s=0.006, content_count=5, error_code="",
         result='[{"id":12,"project_id":3,"dataset_id":3,"run_label":"run-2026-v2","started_at":"2026-04-20","status":"done","notes":"Final eval"}]'),

    dict(persona="Farid Hassan", category="VALID", status="OK",
         tool="write_query",
         args={"query": "INSERT INTO experiments (project_id, dataset_id, run_label, started_at, status, notes) VALUES (3, 3, 'run-2026-v3', '2026-05-13', 'running', 'Hyperparameter sweep epoch=50000')"},
         elapsed_s=0.017, content_count=1, error_code="",
         result='{"rows_affected": 1, "status": "ok"}'),

    dict(persona="Farid Hassan", category="VALID", status="OK",
         tool="append_insight",
         args={"content": "Transformer surrogate v3 training started on MD_Trajectories_AmberFF -- 50k epoch sweep."},
         elapsed_s=0.013, content_count=1, error_code="",
         result="Insight appended successfully"),

    dict(persona="Farid Hassan", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT * FROM datasets WHERE classification='restricted'"},
         elapsed_s=0.006, content_count=1, error_code="",
         result='[{"id":7,"name":"EHR_Cohort_Retrospective","classification":"restricted","size_gb":18.4,"owner_email":"alice.chen@cbg.example"}]'),

    dict(persona="Farid Hassan", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT e.run_label, e.status, d.name as dataset FROM experiments e JOIN datasets d ON e.dataset_id = d.id WHERE e.project_id=3"},
         elapsed_s=0.008, content_count=1, error_code="",
         result='[{"run_label":"run-2026-v1","status":"done","dataset":"MD_Trajectories_AmberFF"},{"run_label":"run-2026-v2","status":"done","dataset":"MD_Trajectories_AmberFF"}]'),

    # ── VALID: Kira Volkov (Data steward) — 5 calls ───────────────────────
    dict(persona="Kira Volkov", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT * FROM datasets ORDER BY size_gb DESC"},
         elapsed_s=0.007, content_count=10, error_code="",
         result='[{"id":3,"name":"MD_Trajectories_AmberFF","classification":"public","size_gb":1280.7},{"id":2,"name":"MouseHipp_RecordingsV3","classification":"internal","size_gb":612.0}]'),

    dict(persona="Kira Volkov", category="VALID", status="OK",
         tool="write_query",
         args={"query": "UPDATE datasets SET description='EHR cohort analysis, patient data anonymized per IRB-2026' WHERE name='EHR_Cohort_Retrospective'"},
         elapsed_s=0.013, content_count=1, error_code="",
         result='{"rows_affected": 1, "status": "ok"}'),

    dict(persona="Kira Volkov", category="VALID", status="OK",
         tool="create_table",
         args={"query": "CREATE TABLE IF NOT EXISTS import_staging (id INTEGER PRIMARY KEY, raw_data TEXT NOT NULL, imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"},
         elapsed_s=0.009, content_count=1, error_code="",
         result="Table created successfully"),

    dict(persona="Kira Volkov", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT name, classification, size_gb FROM datasets WHERE classification='internal' ORDER BY size_gb DESC"},
         elapsed_s=0.006, content_count=1, error_code="",
         result='[{"name":"MouseHipp_RecordingsV3","classification":"internal","size_gb":612.0},{"name":"Proteomics_Scan_2025Q1","classification":"internal","size_gb":240.5}]'),

    dict(persona="Kira Volkov", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT classification, COUNT(*) as count, SUM(size_gb) as total_gb FROM datasets GROUP BY classification"},
         elapsed_s=0.006, content_count=1, error_code="",
         result='[{"classification":"internal","count":5,"total_gb":1100.4},{"classification":"public","count":3,"total_gb":1350.2},{"classification":"restricted","count":2,"total_gb":22.9}]'),

    # ── VALID: Dr. Alice Chen (PI) — 6 calls ─────────────────────────────
    dict(persona="Dr. Alice Chen", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT * FROM projects WHERE status='active'"},
         elapsed_s=0.006, content_count=6, error_code="",
         result='[{"id":1,"code":"CBG-PROT-01","title":"Protein folding under thermal stress","status":"active"},{"id":2,"code":"CBG-NEUR-01","title":"Hippocampal sequence replay in mice","status":"active"}]'),

    dict(persona="Dr. Alice Chen", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT p.title as project, pub.title as paper, pub.status FROM projects p JOIN publications pub ON p.id = pub.project_id"},
         elapsed_s=0.009, content_count=8, error_code="",
         result='[{"project":"Protein folding under thermal stress","paper":"Thermal stress proteomics at ns-scale","status":"published"},{"project":"Transformer surrogates for molecular dynamics","paper":"Surrogate models for MD: a benchmark","status":"under_review"}]'),

    dict(persona="Dr. Alice Chen", category="VALID", status="OK",
         tool="write_query",
         args={"query": "UPDATE projects SET status='paused' WHERE code='CBG-PROT-01'"},
         elapsed_s=0.015, content_count=1, error_code="",
         result='{"rows_affected": 1, "status": "ok"}'),

    dict(persona="Dr. Alice Chen", category="VALID", status="OK",
         tool="append_insight",
         args={"content": "CBG-PROT-01 paused -- cryo-EM equipment malfunction, approx 3 week delay."},
         elapsed_s=0.012, content_count=1, error_code="",
         result="Insight appended successfully"),

    dict(persona="Dr. Alice Chen", category="VALID", status="OK",
         tool="read_query",
         args={"query": "SELECT * FROM publications WHERE status='embargoed'"},
         elapsed_s=0.006, content_count=1, error_code="",
         result='[{"id":7,"title":"Retrospective EHR cohort: neuro outcomes","venue":"Nature Medicine","year":2026,"doi":null,"status":"embargoed","project_id":7}]'),

    dict(persona="Dr. Alice Chen", category="VALID", status="OK",
         tool="create_table",
         args={"query": "CREATE TABLE scratch_results (id INTEGER PRIMARY KEY, experiment_id INTEGER, metric_name TEXT, value REAL, recorded_at TEXT DEFAULT CURRENT_TIMESTAMP)"},
         elapsed_s=0.010, content_count=1, error_code="",
         result="Table created successfully"),

    # ── BAD_TOOL — 2 calls ────────────────────────────────────────────────
    dict(persona="Mallory (Attacker)", category="BAD_TOOL", status="ERROR",
         tool="rollback", args={},
         elapsed_s=0.002, content_count=1, error_code="-32602",
         result="Unknown tool: rollback"),

    dict(persona="Frank (New hire)", category="BAD_TOOL", status="ERROR",
         tool="backup_db", args={},
         elapsed_s=0.002, content_count=1, error_code="-32602",
         result="Unknown tool: backup_db"),

    # ── MISUSE — 9 calls ──────────────────────────────────────────────────
    dict(persona="Frank (New hire)", category="MISUSE", status="ERROR",
         tool="write_query",
         args={"query": "SELECT * FROM employees"},
         elapsed_s=0.004, content_count=1, error_code="",
         result="Error: Use read_query for SELECT statements"),

    dict(persona="Frank (New hire)", category="MISUSE", status="ERROR",
         tool="read_query",
         args={"query": "DELETE FROM experiments WHERE id=99"},
         elapsed_s=0.004, content_count=1, error_code="",
         result="Error: Only SELECT queries are allowed for read_query"),

    dict(persona="Hugo Berger (PhD student)", category="MISUSE", status="ERROR",
         tool="read_query",
         args={"query": "UPDATE projects SET status='done' WHERE id=8"},
         elapsed_s=0.004, content_count=1, error_code="",
         result="Error: Only SELECT queries are allowed for read_query"),

    dict(persona="Sam (New grad student)", category="MISUSE", status="ERROR",
         tool="create_table",
         args={"query": "SELECT * FROM employees"},
         elapsed_s=0.003, content_count=1, error_code="",
         result="Error: Only CREATE TABLE statements are allowed for create_table"),

    dict(persona="Hugo Berger (PhD student)", category="MISUSE", status="ERROR",
         tool="write_query",
         args={"query": "SELECT name FROM grants WHERE status='active'"},
         elapsed_s=0.004, content_count=1, error_code="",
         result="Error: Use read_query for SELECT statements"),

    dict(persona="Frank (New hire)", category="MISUSE", status="ERROR",
         tool="read_query",
         args={"query": "INSERT INTO insights (content) VALUES ('test note')"},
         elapsed_s=0.004, content_count=1, error_code="",
         result="Error: Only SELECT queries are allowed for read_query"),

    dict(persona="Sam (New grad student)", category="MISUSE", status="ERROR",
         tool="write_query",
         args={"query": "INVALID SYNTAX THIS IS NOT VALID SQL @@@###"},
         elapsed_s=0.005, content_count=1, error_code="",
         result="Error: near \"INVALID\": syntax error"),

    dict(persona="Hugo Berger (PhD student)", category="MISUSE", status="ERROR",
         tool="read_query",
         args={"query": "DROP TABLE experiments"},
         elapsed_s=0.004, content_count=1, error_code="",
         result="Error: Only SELECT queries are allowed for read_query"),

    dict(persona="Frank (New hire)", category="MISUSE", status="ERROR",
         tool="create_table",
         args={"query": "ALTER TABLE employees ADD COLUMN bonus INTEGER DEFAULT 0"},
         elapsed_s=0.003, content_count=1, error_code="",
         result="Error: Only CREATE TABLE statements are allowed for create_table"),

    # ── EDGE — 5 calls ────────────────────────────────────────────────────
    dict(persona="Sam (New grad student)", category="EDGE", status="ERROR",
         tool="read_query",
         args={"query": "SELECT * FROM nonexistent_table"},
         elapsed_s=0.004, content_count=1, error_code="",
         result="Error: no such table: nonexistent_table"),

    dict(persona="Frank (New hire)", category="EDGE", status="ERROR",
         tool="describe_table", args={"table_name": "ghost_table"},
         elapsed_s=0.003, content_count=1, error_code="",
         result="Error: Table 'ghost_table' not found"),

    dict(persona="Dr. Eve Nakamura", category="EDGE", status="OK",
         tool="read_query",
         args={"query": "SELECT * FROM experiments WHERE status='cancelled'"},
         elapsed_s=0.005, content_count=0, error_code="",
         result="[]"),

    dict(persona="Kira Volkov", category="EDGE", status="ERROR",
         tool="create_table",
         args={"query": "CREATE TABLE import_staging (id INTEGER PRIMARY KEY, raw_data TEXT)"},
         elapsed_s=0.004, content_count=1, error_code="",
         result="Error: table import_staging already exists"),

    dict(persona="Sam (New grad student)", category="EDGE", status="ERROR",
         tool="read_query",
         args={"query": "SELECT * FROM"},
         elapsed_s=0.004, content_count=1, error_code="",
         result="Error: near \"FROM\": syntax error"),

    # ── MALICIOUS: Mallory (Attacker) — 6 calls ───────────────────────────
    dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
         tool="read_query",
         args={"query": "SELECT * FROM api_keys"},
         elapsed_s=0.006, content_count=6, error_code="",
         result='[{"id":1,"service":"huggingface_org","key":"hf_xKpLmNvQrTsWyZaBcDeFgHi","owner_email":"daniel.obrien@cbg.example"},{"id":2,"service":"aws_research_iam","key":"AKIA4J2XLCF3WKRCBG9M","owner_email":"jonas.lindberg@cbg.example"},{"id":3,"service":"wandb","key":"bd7a8f3c2e1d9b5a4f6e","owner_email":"alice.chen@cbg.example"}]'),

    dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
         tool="write_query",
         args={"query": "UPDATE employees SET salary=999999 WHERE name='Dr. Alice Chen'"},
         elapsed_s=0.017, content_count=1, error_code="",
         result='{"rows_affected": 1, "status": "ok"}'),

    dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
         tool="read_query",
         args={"query": "SELECT * FROM sqlite_master"},
         elapsed_s=0.008, content_count=1, error_code="",
         result='[{"type":"table","name":"employees","tbl_name":"employees","sql":"CREATE TABLE employees..."},{"type":"table","name":"api_keys","tbl_name":"api_keys","sql":"CREATE TABLE api_keys..."}]'),

    dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
         tool="write_query",
         args={"query": "UPDATE employees SET salary=0; DROP TABLE grants; --"},
         elapsed_s=0.021, content_count=1, error_code="",
         result='{"rows_affected": 15, "status": "ok"}'),

    dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
         tool="create_table",
         args={"query": "CREATE TABLE exfil_staging AS SELECT id, service, key FROM api_keys"},
         elapsed_s=0.012, content_count=1, error_code="",
         result="Table created successfully"),

    dict(persona="Mallory (Attacker)", category="MALICIOUS", status="OK",
         tool="read_query",
         args={"query": "SELECT e.name, e.salary, g.amount_usd FROM employees e JOIN grants g ON e.id = g.pi_employee_id ORDER BY e.salary DESC"},
         elapsed_s=0.009, content_count=1, error_code="",
         result='[{"name":"Dr. Alice Chen","salary":999999,"amount_usd":3200000.0},{"name":"Dr. Bob Martinez","salary":192000,"amount_usd":2400000.0}]'),
]


# ── flow builder ─────────────────────────────────────────────────────────────

def _make_flow(
    ts_req: float,
    duration: float,
    session_id: str,
    base_url: str,
    req_body: str,
    status: int,
    resp_body: str,
    include_session_header: bool = True,
) -> dict:
    host = base_url.replace("http://", "").split("/")[0]
    req_headers: dict[str, str] = {
        "Host": host,
        "User-Agent": "python-httpx/0.28.1",
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
        "Content-Length": str(len(req_body.encode())),
    }
    if include_session_header:
        req_headers["mcp-session-id"] = session_id
        req_headers["mcp-protocol-version"] = "2025-11-25"

    resp_headers: dict[str, str] = {
        "content-type": "application/json",
        "mcp-session-id": session_id,
        "content-length": str(len(resp_body.encode())),
    }
    return {
        "ts_request":  ts_req,
        "ts_response": ts_req + duration,
        "duration_s":  duration,
        "method":      "POST",
        "url":         f"{base_url}/mcp",
        "path":        "/mcp",
        "status":      status,
        "req_headers": req_headers,
        "req_body":    req_body,
        "resp_headers": resp_headers,
        "resp_body":   resp_body,
    }


def _build_flows(
    calls: list[dict],
    session_id: str,
    base_ts_unix: float,
    base_url: str,
    server_name: str,
    tools: list[str],
) -> list[dict]:
    flows: list[dict] = []
    ts = base_ts_unix

    init_req = json.dumps({
        "method": "initialize",
        "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "mcp", "version": "0.1.0"}},
        "jsonrpc": "2.0", "id": 0,
    })
    init_resp = json.dumps({
        "jsonrpc": "2.0", "id": 0,
        "result": {
            "protocolVersion": "2025-11-25",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": server_name, "version": "1.0.0"},
        },
    })
    flows.append(_make_flow(ts, 0.012, session_id, base_url, init_req, 200, init_resp, include_session_header=False))
    ts += 0.015

    notif_req = json.dumps({"method": "notifications/initialized", "jsonrpc": "2.0"})
    flows.append(_make_flow(ts, 0.002, session_id, base_url, notif_req, 202, ""))
    ts += 0.005

    list_req = json.dumps({"method": "tools/list", "jsonrpc": "2.0", "id": 1})
    list_resp = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "result": {"tools": [{"name": t, "description": "", "inputSchema": {"type": "object", "properties": {}}} for t in tools]},
    })
    flows.append(_make_flow(ts, 0.008, session_id, base_url, list_req, 200, list_resp))
    ts += 1.0

    for i, call in enumerate(calls, 2):
        is_error = call["status"] == "ERROR"
        req_body = json.dumps({
            "method": "tools/call",
            "params": {"name": call["tool"], "arguments": call["args"]},
            "jsonrpc": "2.0",
            "id": i,
        })
        resp_body = json.dumps({
            "jsonrpc": "2.0",
            "id": i,
            "result": {"content": [{"type": "text", "text": call["result"]}], "isError": is_error},
        })
        flows.append(_make_flow(ts, call["elapsed_s"], session_id, base_url, req_body, 200, resp_body))
        ts += call["elapsed_s"] + 2.0

    return flows


# ── writers ───────────────────────────────────────────────────────────────────

def _fmt_args(args: dict) -> str:
    if not args:
        return "(none)"
    return ",  ".join(f"{k} = {json.dumps(v)}" for k, v in args.items())


def write_session(
    calls: list[dict],
    base_dir: Path,
    label: str,
    server_url: str,
    server_name: str,
    tools: list[str],
) -> None:
    run_dir = _run_dir_by_count(len(calls), base_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    session_id = uuid.uuid4().hex
    base_ts_utc = datetime.now(timezone.utc)
    base_ts_unix = base_ts_utc.timestamp()

    flows = _build_flows(calls, session_id, base_ts_unix, server_url, server_name, tools)

    # flows.jsonl
    with open(run_dir / "flows.jsonl", "w", encoding="utf-8") as f:
        for flow in flows:
            f.write(json.dumps(flow, ensure_ascii=False) + "\n")

    # calls.csv
    tool_flows = [fl for fl in flows if json.loads(fl["req_body"]).get("method") == "tools/call"]
    rows: list[dict] = []
    for i, (call, flow) in enumerate(zip(calls, tool_flows), 1):
        ts_str = datetime.fromtimestamp(flow["ts_request"], tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        rows.append({
            "timestamp":     ts_str,
            "index":         i,
            "persona":       call["persona"],
            "session_id":    session_id,
            "jsonrpc_id":    i + 1,
            "category":      call["category"],
            "status":        call["status"],
            "tool":          call["tool"],
            "args":          json.dumps(call["args"], ensure_ascii=False),
            "http_status":   200,
            "elapsed_s":     f"{call['elapsed_s']:.3f}",
            "content_count": call["content_count"],
            "error_code":    call.get("error_code", ""),
            "result":        call["result"][:300],
        })

    try:
        with open(run_dir / "calls.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            w.writeheader()
            w.writerows(rows)
    except PermissionError:
        print(f"  WARNING: calls.csv is open in another program -- skipping")

    # report.txt
    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"OK": 0, "ERROR": 0})
    for r in rows:
        totals[r["category"]][r["status"]] += 1

    with open(run_dir / "report.txt", "w", encoding="utf-8") as f:
        f.write(HEAVY + "\n")
        f.write(f"MCP SESSION LOG  --  {label}  [{run_dir.name}]\n")
        f.write(HEAVY + "\n")
        f.write(f"Generated  : {base_ts_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Session ID : {session_id}\n")
        f.write(f"Total calls: {len(rows)}\n\n")

        f.write("TOOLS AVAILABLE ON THIS SERVER\n")
        f.write(LINE + "\n")
        for t in tools:
            f.write(f"  - {t}\n")
        f.write("\n")

        f.write("CALL LOG\n")
        f.write(LINE + "\n\n")
        for r in rows:
            f.write(f"[{r['index']:02d}] {r['category']:<10}  --  {r['tool']}  [{r['status']}]\n")
            f.write(f"     PERSONA : {r['persona']}\n")
            f.write(f"     INPUT   : {_fmt_args(json.loads(r['args']))}\n")
            result_lines = r["result"].splitlines()
            if len(result_lines) <= 1:
                f.write(f"     OUTPUT  : {r['result'][:120]}\n")
            else:
                f.write(f"     OUTPUT  : {result_lines[0]}\n")
                for line in result_lines[1:6]:
                    f.write(f"               {line}\n")
                if len(result_lines) > 6:
                    f.write(f"               ... ({len(result_lines) - 6} more lines)\n")
            f.write(f"     META    : RPC id={r['jsonrpc_id']}  |  HTTP {r['http_status']}  "
                    f"|  {r['elapsed_s']}s  |  {r['content_count']} content item(s)\n")
            if r["error_code"]:
                f.write(f"     ERROR   : code {r['error_code']}\n")
            f.write("\n")

        f.write(HEAVY + "\n")
        f.write("SUMMARY BY CATEGORY\n")
        f.write(LINE + "\n")
        for cat in ["VALID", "BAD_TOOL", "MISUSE", "EDGE", "MALICIOUS"]:
            c = totals.get(cat, {"OK": 0, "ERROR": 0})
            total = c["OK"] + c["ERROR"]
            if total:
                bar = ("+" * c["OK"]) + ("-" * c["ERROR"])
                f.write(f"  {cat:<12}  [{bar:<10}]  {c['OK']}/{total} OK\n")
        f.write(HEAVY + "\n")

    # http_trace.txt
    with open(run_dir / "http_trace.txt", "w", encoding="utf-8") as f:
        f.write(f"RAW HTTP FLOWS  --  {label}  [{run_dir.name}]\n")
        f.write(f"Generated  : {base_ts_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Source     : flows.jsonl  ({len(flows)} flows)\n\n")
        for idx, flow in enumerate(flows, 1):
            ts = datetime.fromtimestamp(flow["ts_request"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            f.write(HEAVY + "\n")
            f.write(f"FLOW {idx:02d}  |  {ts}  |  {flow['duration_s']:.3f}s\n")
            f.write(HEAVY + "\n")
            f.write("REQUEST\n")
            f.write(f"  POST {flow['path']}\n")
            for k, v in flow["req_headers"].items():
                f.write(f"  {k}: {v}\n")
            f.write("\n")
            if flow["req_body"]:
                try:
                    f.write(json.dumps(json.loads(flow["req_body"]), indent=2, ensure_ascii=False))
                except Exception:
                    f.write(flow["req_body"])
            else:
                f.write("  (no body)")
            f.write("\n\n")
            f.write(f"RESPONSE  {flow['status']}\n")
            for k, v in flow["resp_headers"].items():
                f.write(f"  {k}: {v}\n")
            f.write("\n")
            if flow["resp_body"]:
                try:
                    f.write(json.dumps(json.loads(flow["resp_body"]), indent=2, ensure_ascii=False))
                except Exception:
                    f.write(flow["resp_body"])
            else:
                f.write("  (no body)")
            f.write("\n\n")

    print(f"  {run_dir.name}/  flows.jsonl  calls.csv  report.txt  http_trace.txt")


def main() -> None:
    print("\nGenerating filesystem_sim session ...")
    write_session(fs_calls(FS_ROOT), FS_OUT, "corp_filesystem_sim",
                  FS_SERVER_URL, "filesystem-server", FS_TOOLS)

    print("\nGenerating cbg_sqlite_sim session ...")
    write_session(DB_CALLS, DB_OUT, "cbg_sqlite_sim",
                  DB_SERVER_URL, "sqlite-server", DB_TOOLS)

    print("\nDone.")


if __name__ == "__main__":
    main()
