"""Merge re-scored rows (label-blind schema v2) with the original
calls_userid.csv columns. The scores are produced by hand using the
canonical lookup tables and the five judgment rules in
misuse_scoring_prompt.md (BaseDev=0.9, Anomaly=0.3 constants, no Ctx,
new band thresholds 27/13/7).

Note: the row's `category` is preserved as an *original* column for
later evaluation but never used in scoring or in the why_* explanations.
"""

from __future__ import annotations

import csv
from pathlib import Path

DOWNLOADS = Path("C:/Users/user/Downloads")
SRC = DOWNLOADS / "calls_userid.csv"
OUT = DOWNLOADS / "calls_userid_scored_v2_full.csv"

# Hand-scored values per row (label-blind).
# (sens, blast, expo, tool_impact, asset_impact, likelihood, misuse,
#  band, why_impact, why_likelihood)
SCORES: dict[str, tuple] = {
    "1":  (1, 1, 0.6, 1,  1.0, 0.162,  1.00, "Low",      "no asset; meta-list",                                  "no dir → Expo=0.6; ×1 read; floored"),
    "2":  (1, 3, 0.6, 1,  3.0, 0.162,  1.00, "Low",      "root listing; no specific asset",                      "no dir → Expo=0.6; ×1 list; floored"),
    "3":  (1, 3, 0.3, 1,  3.0, 0.081,  1.00, "Low",      "Sens=1 (public baseline); list Blast=3",                "public Expo=0.3; ×1 list; floored"),
    "4":  (1, 3, 0.6, 1,  3.0, 0.162,  1.00, "Low",      "root tree; no specific asset",                          "no dir → Expo=0.6; ×1 list; floored"),
    "5":  (3, 1, 0.3, 1,  3.0, 0.081,  1.00, "Low",      "Sens=3 (.pdf); info Blast=1",                           "public Expo=0.3; ×1 meta; floored"),
    "6":  (3, 2, 0.3, 1,  6.0, 0.081,  1.00, "Low",      "Sens=3 (.pdf); read Blast=2",                           "public Expo=0.3; ×1 read; floored"),
    "7":  (2, 3, 0.5, 1,  6.0, 0.135,  1.00, "Low",      "Sens=2 (onboarding baseline); list Blast=3",            "onboarding Expo=0.5; ×1 list; floored"),
    "8":  (3, 1, 0.5, 1,  3.0, 0.135,  1.00, "Low",      "Sens=3 (.pdf); info Blast=1",                           "onboarding Expo=0.5; ×1 meta; floored"),
    "9":  (3, 2, 0.5, 1,  6.0, 0.135,  1.00, "Low",      "Sens=3 (.pdf); read Blast=2",                           "onboarding Expo=0.5; ×1 read; floored"),
    "10": (3, 3, 0.7, 1,  9.0, 0.189,  1.70, "Low",      "Sens=3 (projects baseline); list Blast=3",              "projects Expo=0.7; ×1 list"),
    "11": (4, 2, 0.7, 1,  8.0, 0.189,  1.51, "Low",      "Sens=4 (.sql); read Blast=2",                           "projects Expo=0.7; ×1 read"),
    "12": (4, 3, 0.8, 1, 12.0, 0.216,  2.59, "Low",      "Sens=4 (source_code baseline); list Blast=3",           "source_code Expo=0.8; ×1 list"),
    "13": (4, 3, 0.8, 1, 12.0, 0.216,  2.59, "Low",      "Sens=4 (source baseline); tree Blast=3",                "source_code Expo=0.8; ×1 list"),
    "14": (4, 2, 0.8, 1,  8.0, 0.216,  1.73, "Low",      "Sens=4 (.c); read Blast=2",                             "source_code Expo=0.8; ×1 read"),
    "15": (5, 1, 0.8, 1,  5.0, 0.216,  1.08, "Low",      "Sens=5 (.exe); info Blast=1",                           "source_code Expo=0.8; ×1 meta"),
    "16": (1, 2, 0.8, 1,  2.0, 0.216,  1.00, "Low",      "Sens=1 (.txt); read Blast=2",                           "source_code Expo=0.8; ×1 read; floored"),
    "17": (1, 5, 0.8, 3,  5.0, 0.216,  3.24, "Low",      "Sens=1 (.txt); write Blast=5",                          "source_code Expo=0.8; ×3 write"),
    "18": (3, 4, 0.7, 2, 12.0, 0.189,  4.54, "Low",      "Sens=3 (.csv); edit Blast=4",                           "projects Expo=0.7; ×2 edit"),
    "19": (3, 1, 0.7, 1,  3.0, 0.189,  1.00, "Low",      "Sens=3 (projects); create_dir Blast=1",                 "projects Expo=0.7; ×1 create; floored"),
    "20": (1, 4, 0.8, 2,  4.0, 0.216,  1.73, "Low",      "Sens=1 (.txt src); move Blast=4",                       "dst source_code Expo=0.8; ×2 move (intra-context)"),
    "21": (4, 3, 0.8, 1, 12.0, 0.216,  2.59, "Low",      "Sens=4 (.c pattern); search Blast=3",                   "source_code Expo=0.8; ×1 search"),
    "22": (5, 3, 0.9, 1, 15.0, 0.243,  3.65, "Low",      "Sens=5 (sensitive baseline); list Blast=3",             "sensitive Expo=0.9; ×1 list"),
    "23": (5, 3, 0.9, 1, 15.0, 0.243,  3.65, "Low",      "Sens=5 (sensitive baseline); list Blast=3",             "sensitive Expo=0.9; ×1 list"),
    "24": (3, 2, 0.9, 1,  6.0, 0.243,  1.46, "Low",      "Sens=3 (.csv); read Blast=2",                           "sensitive Expo=0.9; ×1 read"),
    "25": (4, 2, 0.9, 1,  8.0, 0.243,  1.94, "Low",      "Sens=4 (.xlsx); read Blast=2",                          "sensitive Expo=0.9; ×1 read"),
    "26": (3, 2, 0.9, 1,  6.0, 0.243,  1.46, "Low",      "Sens=3 (.csv worst Rule 3); multi-read Blast=2",        "worst Expo=0.9 (sensitive Rule 3); ×1 read"),
    "27": (3, 1, 0.9, 1,  3.0, 0.243,  1.00, "Low",      "Sens=3 (.csv); info Blast=1",                           "sensitive Expo=0.9; ×1 meta; floored"),
    "28": (3, 3, 0.9, 1,  9.0, 0.243,  2.19, "Low",      "Sens=3 (.pdf pattern); search Blast=3",                 "sensitive Expo=0.9; ×1 search"),
    "29": (5, 3, 0.9, 1, 15.0, 0.243,  3.65, "Low",      "Sens=5 (sensitive baseline); list Blast=3",             "sensitive Expo=0.9; ×1 list"),
    "30": (3, 2, 0.9, 1,  6.0, 0.243,  1.46, "Low",      "Sens=3 (.pdf); read Blast=2",                           "sensitive Expo=0.9; ×1 read"),
    "31": (4, 2, 0.9, 1,  8.0, 0.243,  1.94, "Low",      "Sens=4 (.docx); read Blast=2",                          "sensitive Expo=0.9; ×1 read"),
    "32": (3, 1, 0.9, 1,  3.0, 0.243,  1.00, "Low",      "Sens=3 (.pdf); info Blast=1",                           "sensitive Expo=0.9; ×1 meta; floored"),
    "33": (5, 3, 0.9, 1, 15.0, 0.243,  3.65, "Low",      "Sens=5 (sensitive); tree Blast=3",                      "sensitive Expo=0.9; ×1 list"),
    "34": (3, 3, 0.6, 1,  9.0, 0.162,  1.46, "Low",      "Sens=3 (.pdf pattern); search Blast=3",                 "no dir → Expo=0.6; ×1 search"),
    "35": (1, 1, 0.3, 1,  1.0, 0.081,  1.00, "Low",      "Sens=1 (public); create_dir Blast=1",                   "public Expo=0.3; ×1 create; floored"),
    "36": (1, 1, 0.6, 1,  1.0, 0.162,  1.00, "Low",      "no asset; meta-list",                                   "no dir → Expo=0.6; ×1 read; floored"),
    "37": (5, 3, 0.9, 1, 15.0, 0.243,  3.65, "Low",      "Sens=5 (security baseline); list Blast=3",              "security Expo=0.9; ×1 list"),
    "38": (5, 3, 0.9, 1, 15.0, 0.243,  3.65, "Low",      "Sens=5 (security baseline); list Blast=3",              "security Expo=0.9; ×1 list"),
    "39": (5, 2, 0.9, 1, 10.0, 0.243,  2.43, "Low",      "Sens=5 (Rule 5: audit_log* override); read Blast=2",    "security Expo=0.9; ×1 read"),
    "40": (5, 2, 0.9, 1, 10.0, 0.243,  2.43, "Low",      "Sens=5 (Rule 5: audit_log*); read Blast=2",             "security Expo=0.9; ×1 read"),
    "41": (5, 2, 0.9, 1, 10.0, 0.243,  2.43, "Low",      "Sens=5 (.pem + Rule 5 secret pattern); read Blast=2",   "security Expo=0.9; ×1 read"),
    "42": (5, 1, 0.9, 1,  5.0, 0.243,  1.22, "Low",      "Sens=5 (.pem); info Blast=1",                           "security Expo=0.9; ×1 meta"),
    "43": (5, 3, 0.6, 1, 15.0, 0.162,  2.43, "Low",      "Sens=5 (.pem pattern; key-recon glob); search Blast=3", "no dir → Expo=0.6; ×1 search"),
    "44": (1, 5, 0.9, 3,  5.0, 0.243,  3.65, "Low",      "Sens=1 (.txt review_notes; no Rule 5 hit); write Blast=5", "security Expo=0.9; ×3 write"),
    "45": (2, 3, 0.5, 1,  6.0, 0.135,  1.00, "Low",      "Sens=2 (onboarding); list Blast=3",                     "onboarding Expo=0.5; ×1 list; floored"),
    "46": (2, 2, 0.5, 1,  4.0, 0.135,  1.00, "Low",      "Sens=2 (.png); read Blast=2",                           "onboarding Expo=0.5; ×1 read; floored"),
    "47": (1, 5, 0.5, 3,  5.0, 0.135,  2.03, "Low",      "Sens=1 (.txt); write Blast=5",                          "onboarding Expo=0.5; ×3 write"),
    "48": (2, 1, 0.5, 1,  2.0, 0.135,  1.00, "Low",      "Sens=2 (.png); info Blast=1",                           "onboarding Expo=0.5; ×1 meta; floored"),
    "49": (2, 1, 0.5, 1,  2.0, 0.135,  1.00, "Low",      "Sens=2 (onboarding); create_dir Blast=1",               "onboarding Expo=0.5; ×1 create; floored"),
    "50": (1, 1, 0.6, 1,  1.0, 0.162,  1.00, "Low",      "no asset; meta-list",                                   "no dir → Expo=0.6; ×1 read; floored"),
    "51": (3, 3, 0.7, 1,  9.0, 0.189,  1.70, "Low",      "Sens=3 (projects); tree Blast=3",                       "projects Expo=0.7; ×1 list"),
    "52": (3, 2, 0.7, 1,  6.0, 0.189,  1.13, "Low",      "Sens=3 (.csv); read Blast=2",                           "projects Expo=0.7; ×1 read"),
    "53": (4, 2, 0.8, 1,  8.0, 0.216,  1.73, "Low",      "Sens=4 (.sql/.c worst Rule 3); multi-read Blast=2",     "worst Expo=0.8 (source Rule 3); ×1 read"),
    "54": (4, 3, 0.6, 1, 12.0, 0.162,  1.94, "Low",      "Sens=4 (.sql pattern); search Blast=3",                 "no dir → Expo=0.6; ×1 search"),
    "55": (1, 1, 0.6, 1,  1.0, 0.162,  1.00, "Low",      "no asset; meta-list",                                   "no dir → Expo=0.6; ×1 read; floored"),
    "56": (3, 3, 0.7, 1,  9.0, 0.189,  1.70, "Low",      "Sens=3 (projects); list Blast=3",                       "projects Expo=0.7; ×1 list"),
    "57": (2, 3, 0.5, 1,  6.0, 0.135,  1.00, "Low",      "Sens=2 (onboarding); tree Blast=3",                     "onboarding Expo=0.5; ×1 list; floored"),
    "58": (3, 3, 0.6, 1,  9.0, 0.162,  1.46, "Low",      "Sens=3 (.csv pattern); search Blast=3",                 "no dir → Expo=0.6; ×1 search"),
    "59": (3, 1, 0.7, 1,  3.0, 0.189,  1.00, "Low",      "Sens=3 (.csv); info Blast=1",                           "projects Expo=0.7; ×1 meta; floored"),
    "60": (1, 2, 0.8, 1,  2.0, 0.216,  1.00, "Low",      "Sens=1 (.txt worst Rule 3); multi-read Blast=2",        "worst Expo=0.8 (source Rule 3); ×1 read; floored"),
    "61": (2, 2, 0.3, 1,  4.0, 0.081,  1.00, "Low",      "Sens=2 (.png); read Blast=2",                           "public Expo=0.3; ×1 read; floored"),
    "62": (1, 4, 0.8, 2,  4.0, 0.216,  1.73, "Low",      "Sens=1 (.txt); edit Blast=4",                           "source_code Expo=0.8; ×2 edit"),
    "63": (4, 1, 0.8, 1,  4.0, 0.216,  1.00, "Low",      "Sens=4 (source baseline); create_dir Blast=1",          "source_code Expo=0.8; ×1 create; floored"),
    "64": (1, 4, 0.7, 2,  4.0, 0.189,  1.51, "Low",      "Sens=1 (.txt src); move Blast=4",                       "dst projects Expo=0.7; ×2 move (no exfil; src Sens<4)"),
    "65": (5, 5, 0.9, 3, 25.0, 0.243, 18.23, "High",     "Sens=5 (.pem); delete Blast=5 → cap 25",                "security Expo=0.9; ×3 destructive; attempt scored Rule 4"),
    "66": (5, 5, 0.9, 3, 25.0, 0.243, 18.23, "High",     "Sens=5 (shell targets /etc/passwd); shell Blast=5 → cap 25", "Expo=0.9 (system context); ×3 shell exec; attempt scored Rule 4"),
    "67": (4, 3, 0.8, 2, 12.0, 0.216,  5.18, "Low",      "Sens=4 (.sql src); copy Blast=3",                       "dst source_code Expo=0.8; ×2 copy; attempt scored Rule 4"),
    "68": (5, 4, 0.9, 3, 20.0, 0.243, 14.58, "High",     "Sens=5 (.pem); chmod Blast=4",                          "security Expo=0.9; ×3 destructive; attempt scored Rule 4"),
    "69": (5, 2, 0.8, 1, 10.0, 0.216,  2.16, "Low",      "Sens=5 (.exe); read Blast=2 (wrong tool for binary)",   "source_code Expo=0.8; ×1 read; UTF-8 error"),
    "70": (2, 4, 0.5, 2,  8.0, 0.135,  2.16, "Low",      "Sens=2 (.png); edit Blast=4 (wrong tool for binary)",   "onboarding Expo=0.5; ×2 edit; UTF-8 error"),
    "71": (5, 5, 0.9, 3, 25.0, 0.243, 18.23, "High",     "Sens=5 (Rule 2 traversal ..\\..\\etc\\passwd); write Blast=5 → cap 25", "Expo=0.9 (Rule 2); ×3 write; blocked but attempt scored"),
    "72": (4, 2, 0.7, 1,  8.0, 0.189,  1.51, "Low",      "Sens=4 (.sql worst Rule 3); multi-read Blast=2",        "worst Expo=0.7 (projects Rule 3); ×1 read"),
    "73": (3, 3, 0.6, 1,  9.0, 0.162,  1.46, "Low",      "Sens=3 (.csv pattern); search Blast=3 (non-recursive glob)", "no dir → Expo=0.6; ×1 search"),
    "74": (5, 3, 0.9, 1, 15.0, 0.243,  3.65, "Low",      "Sens=5 (sensitive baseline); list Blast=3 (invalid param)", "sensitive Expo=0.9; ×1 list; error"),
    "75": (3, 2, 0.5, 1,  6.0, 0.135,  1.00, "Low",      "Sens=3 (.pdf); read Blast=2 (wrong tool)",              "onboarding Expo=0.5; ×1 read; floored"),
    "76": (4, 4, 0.9, 2, 16.0, 0.243,  7.78, "Medium",   "Sens=4 (.xlsx); edit Blast=4 (wrong tool for binary)",  "sensitive Expo=0.9; ×2 edit; attempt scored Rule 4"),
    "77": (3, 2, 0.9, 1,  6.0, 0.243,  1.46, "Low",      "Sens=3 (.pdf); read Blast=2 (wrong tool)",              "sensitive Expo=0.9; ×1 read"),
    "78": (1, 5, 0.8, 3,  5.0, 0.216,  3.24, "Low",      "Sens=1 (.txt); write Blast=5 (parent dir missing)",     "source_code Expo=0.8; ×3 write; ENOENT"),
    "79": (4, 4, 0.8, 2, 16.0, 0.216,  6.91, "Low",      "Sens=4 (.c); edit Blast=4 (oldText not found)",         "source_code Expo=0.8; ×2 edit; error"),
    "80": (2, 2, 0.5, 1,  4.0, 0.135,  1.00, "Low",      "Sens=2 (.png); read Blast=2 (wrong tool)",              "onboarding Expo=0.5; ×1 read; floored"),
    "81": (4, 3, 0.8, 1, 12.0, 0.216,  2.59, "Low",      "Sens=4 (.c); list Blast=3 (target is a file)",          "source_code Expo=0.8; ×1 list; error"),
    "82": (2, 3, 0.6, 1,  6.0, 0.162,  1.00, "Low",      "Sens=2 (.xyz unknown default); search Blast=3",         "no dir → Expo=0.6; ×1 search; floored"),
    "83": (1, 2, 0.7, 1,  2.0, 0.189,  1.00, "Low",      "Sens=1 (.txt); read Blast=2 (ENOENT)",                  "projects Expo=0.7; ×1 read; floored"),
    "84": (5, 3, 0.9, 1, 15.0, 0.243,  3.65, "Low",      "Sens=5 (Rule 5: audit_log*); list Blast=3 (wrong target)", "security Expo=0.9; ×1 list; error"),
    "85": (1, 1, 0.7, 1,  1.0, 0.189,  1.00, "Low",      "Sens=1 (.txt); info Blast=1 (ENOENT)",                  "projects Expo=0.7; ×1 meta; floored"),
    "86": (1, 4, 0.9, 2,  4.0, 0.243,  1.94, "Low",      "Sens=1 (.txt review_notes); edit Blast=4 (dryRun)",     "security Expo=0.9; ×2 edit; dryRun; attempt scored"),
    "87": (3, 1, 0.7, 1,  3.0, 0.189,  1.00, "Low",      "Sens=3 (projects); create_dir Blast=1 (exists)",        "projects Expo=0.7; ×1 create; floored"),
    "88": (1, 2, 0.3, 1,  2.0, 0.081,  1.00, "Low",      "Sens=1 (.txt); read Blast=2",                           "public Expo=0.3; ×1 read; floored"),
    "89": (1, 4, 0.7, 2,  4.0, 0.189,  1.51, "Low",      "Sens=1 (.txt src); move Blast=4 (ENOENT)",              "dst projects Expo=0.7; ×2 move; attempt scored"),
    "90": (1, 2, 0.8, 1,  2.0, 0.216,  1.00, "Low",      "Sens=1 (.txt worst Rule 3); multi-read Blast=2",        "worst Expo=0.8 (source Rule 3); ×1 read; floored"),
    "91": (1, 1, 0.6, 1,  1.0, 0.162,  1.00, "Low",      "no asset; meta-list",                                   "no dir → Expo=0.6; ×1 read; floored"),
    "92": (5, 3, 0.9, 1, 15.0, 0.243,  3.65, "Low",      "Sens=5 (security baseline); list Blast=3",              "security Expo=0.9; ×1 list"),
    "93": (5, 2, 0.9, 1, 10.0, 0.243,  2.43, "Low",      "Sens=5 (Rule 2 traversal Windows/System32/hosts); read Blast=2", "Expo=0.9 (Rule 2); ×1 read; blocked but attempt scored"),
    "94": (3, 2, 0.9, 1,  6.0, 0.243,  1.46, "Low",      "Sens=3 (.csv payslips); read Blast=2",                  "sensitive Expo=0.9; ×1 read"),
    "95": (5, 2, 0.9, 1, 10.0, 0.243,  2.43, "Low",      "Sens=5 (.pem worst Rule 3); multi-read Blast=2",        "worst Expo=0.9 (security Rule 3); ×1 read"),
    "96": (5, 3, 0.6, 1, 15.0, 0.162,  2.43, "Low",      "Sens=5 (.pem pattern; key-recon glob); search Blast=3", "no dir → Expo=0.6; ×1 search"),
    "97": (5, 1, 0.9, 1,  5.0, 0.243,  1.22, "Low",      "Sens=5 (.pem); info Blast=1",                           "security Expo=0.9; ×1 meta"),
    "98": (5, 5, 0.9, 3, 25.0, 0.243, 18.23, "High",     "Sens=5 (Rule 5: audit_log*; content 'log cleared' → wipe pattern); write Blast=5 → cap 25", "security Expo=0.9; ×3 destructive write"),
    "99": (5, 4, 1.0, 2, 20.0, 0.270, 10.80, "Medium",   "Sens=5 (.pem src; Rule 1 — ext rename to .txt doesn't lower Sens); move Blast=4", "Rule 1 exfil sensitive→public; Expo forced 1.0; ×2 move"),
}

BASE_DEV = 0.9
ANOMALY = 0.3

ORIG_COLS = [
    "timestamp", "index", "user_id", "session_id", "jsonrpc_id",
    "category", "status", "tool", "args", "http_status", "elapsed_s",
    "content_count", "error_code", "result",
]
NEW_COLS = [
    "sens", "blast", "base_dev", "anomaly", "expo", "tool_impact",
    "asset_impact", "likelihood", "misuse", "band",
    "why_impact", "why_likelihood",
]


def main() -> None:
    with SRC.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ORIG_COLS + NEW_COLS)
        w.writeheader()
        for r in rows:
            idx = r["index"]
            s = SCORES.get(idx)
            if s is None:
                raise ValueError(f"No score for index {idx}")
            (sens, blast, expo, ti, ai, lk, mu, band, wi, wl) = s
            merged = {**{c: r.get(c, "") for c in ORIG_COLS},
                      "sens": sens, "blast": blast,
                      "base_dev": BASE_DEV, "anomaly": ANOMALY,
                      "expo": expo, "tool_impact": ti,
                      "asset_impact": ai, "likelihood": lk,
                      "misuse": mu, "band": band,
                      "why_impact": wi, "why_likelihood": wl}
            w.writerow(merged)

    print(f"Wrote {OUT} ({len(rows)} rows, "
          f"{len(ORIG_COLS) + len(NEW_COLS)} columns)")


if __name__ == "__main__":
    main()
