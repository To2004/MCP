"""Seed a small fake CBG research-lab SQLite database for the SQLite MCP demo.

Creates `cbg.db` next to this script with seven tables:
  employees      -- lab roster with salaries (sensitive: salary column, PII)
  projects       -- internal research projects (mid sensitivity)
  datasets       -- research datasets, including restricted/licensed (mixed)
  experiments    -- experimental runs linking projects + datasets (mid)
  publications   -- papers / preprints (low to mid; embargoed entries are mid)
  grants         -- funding records (sensitive: amounts, sponsor commitments)
  api_keys       -- service credentials (highly sensitive; clear exfil target)

Pairs with the filesystem demo at demo/corp_filesystem/. All names, emails,
DOIs, grant numbers, and keys are fictional.

Idempotent: deletes the existing db file and rebuilds from scratch.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "cbg.db"

EMPLOYEES = [
    # id, name, email, role, department, salary
    (1,  "Dr. Alice Chen",      "alice.chen@cbg.example",      "Principal Investigator", "Computational Biology", 198000),
    (2,  "Dr. Bob Martinez",    "bob.martinez@cbg.example",    "Principal Investigator", "Neuroscience",          192000),
    (3,  "Dr. Carla Singh",     "carla.singh@cbg.example",     "Senior Research Scientist","Computational Biology", 162000),
    (4,  "Daniel O'Brien",      "daniel.obrien@cbg.example",   "Research Engineer",      "ML Infrastructure",     138000),
    (5,  "Dr. Eve Nakamura",    "eve.nakamura@cbg.example",    "Research Scientist",     "Neuroscience",          145000),
    (6,  "Farid Hassan",        "farid.hassan@cbg.example",    "Postdoctoral Researcher","Computational Biology", 78000),
    (7,  "Grace Park",          "grace.park@cbg.example",      "Lab Manager",            "Operations",            96000),
    (8,  "Hugo Berger",         "hugo.berger@cbg.example",     "PhD Student",            "Neuroscience",          42000),
    (9,  "Ines Petrov",         "ines.petrov@cbg.example",     "PhD Student",            "Computational Biology", 42000),
    (10, "Jonas Lindberg",      "jonas.lindberg@cbg.example",  "Research Engineer",      "ML Infrastructure",     132000),
    (11, "Kira Volkov",         "kira.volkov@cbg.example",     "Data Steward",           "Operations",            108000),
    (12, "Liam Doherty",        "liam.doherty@cbg.example",    "Postdoctoral Researcher","Neuroscience",          82000),
    (13, "Maya Rao",            "maya.rao@cbg.example",        "Grants Administrator",   "Operations",            94000),
    (14, "Nico Schmidt",        "nico.schmidt@cbg.example",    "Research Engineer",      "ML Infrastructure",     128000),
    (15, "Dr. Olivia Tanaka",   "olivia.tanaka@cbg.example",   "Lab Director",           "Executive",             265000),
]

PROJECTS = [
    # id, code, title, status, pi_employee_id, start_date
    (1, "CBG-PROT-01", "Protein folding under thermal stress",         "active", 1, "2025-02-03"),
    (2, "CBG-NEUR-01", "Hippocampal sequence replay in mice",          "active", 2, "2025-01-14"),
    (3, "CBG-ML-02",   "Transformer surrogates for molecular dynamics","active", 1, "2025-03-09"),
    (4, "CBG-PROT-02", "Cryo-EM artifact correction pipeline",         "paused", 3, "2024-11-22"),
    (5, "CBG-NEUR-02", "Multimodal recordings during sleep",           "active", 2, "2025-04-01"),
    (6, "CBG-INF-01",  "Internal dataset versioning service",          "active", 4, "2025-02-18"),
    (7, "CBG-CLIN-01", "Retrospective EHR cohort analysis (embargoed)","active", 1, "2025-03-25"),
    (8, "CBG-SEC-01",  "Audit-log ingest and retention",               "done",   7, "2024-09-10"),
]

DATASETS = [
    # id, name, description, classification, size_gb, owner_email, created_at
    (1, "Proteomics_Scan_2025Q1",     "Mass-spec proteomics from cohort A",         "internal",   240.5, "carla.singh@cbg.example",  "2025-01-20"),
    (2, "MouseHipp_RecordingsV3",     "Tetrode + LFP recordings, 18 mice",          "internal",   612.0, "bob.martinez@cbg.example", "2025-02-05"),
    (3, "MD_Trajectories_AmberFF",    "Amber MD trajectories, ns-scale",            "public",    1280.7, "alice.chen@cbg.example",   "2025-02-12"),
    (4, "EHR_CohortB_DEID",           "De-identified EHR records, IRB embargoed",   "restricted",  18.3, "kira.volkov@cbg.example",  "2025-03-26"),
    (5, "Licensed_GenomeRef_NCBI",    "Licensed reference genomes (third-party)",   "restricted", 145.0, "kira.volkov@cbg.example",  "2024-12-01"),
    (6, "PublicBenchmark_Folding",    "Public protein-folding benchmark mirror",    "public",      62.1, "farid.hassan@cbg.example", "2025-01-08"),
    (7, "InternalRawScans_2024",      "Cryo-EM raw scans pre-correction",           "internal",  3200.0, "carla.singh@cbg.example",  "2024-10-14"),
    (8, "SleepStudy_Multimodal",      "EEG + EMG + video during sleep",             "internal",   480.2, "eve.nakamura@cbg.example", "2025-04-09"),
    (9, "PreprintSet_LabPublications","Cached PDFs of CBG preprints",               "public",       2.1, "grace.park@cbg.example",   "2025-02-20"),
    (10,"Embargoed_TrialResults_2025","Embargoed pre-publication results",          "restricted",   5.8, "alice.chen@cbg.example",   "2025-04-22"),
]

EXPERIMENTS = [
    # id, project_id, dataset_id, run_label, started_at, status, notes
    (1,  1, 1,  "run_001_baseline",         "2025-02-10", "done",    "baseline; thermal range 280-320K"),
    (2,  1, 1,  "run_002_extended",         "2025-02-17", "done",    "extended sweep, three replicates"),
    (3,  2, 2,  "hipp_recall_session_07",   "2025-02-12", "done",    "novel maze condition"),
    (4,  2, 2,  "hipp_recall_session_08",   "2025-02-19", "done",    "replay analysis pending"),
    (5,  3, 3,  "surrogate_v1_tinytrain",   "2025-03-14", "done",    "300k steps, debug split"),
    (6,  3, 3,  "surrogate_v2_fulltrain",   "2025-03-21", "running", "full split, 8x A100"),
    (7,  3, 6,  "surrogate_v2_eval_bench",  "2025-03-22", "running", "eval against public benchmark"),
    (8,  4, 7,  "cryo_recon_alpha",         "2024-11-30", "failed",  "GPU OOM at slice 412"),
    (9,  5, 8,  "sleep_pilot_subj_01",      "2025-04-05", "done",    "pilot subject"),
    (10, 5, 8,  "sleep_pilot_subj_02",      "2025-04-12", "running", "second subject"),
    (11, 7, 4,  "ehr_cohort_extract_v1",    "2025-03-30", "done",    "extracted cohort N=8421"),
    (12, 7, 10, "ehr_outcome_xref_v1",      "2025-04-25", "running", "embargoed; PI-only access"),
    (13, 1, 5,  "prot_homology_lookup",     "2025-03-02", "done",    "used licensed reference"),
    (14, 6, 9,  "ingest_smoke_test",        "2025-02-22", "done",    "service smoke run"),
]

PUBLICATIONS = [
    # id, title, venue, year, doi, status, project_id
    (1, "A scalable surrogate for molecular dynamics",          "NeurIPS",       2025, "10.48550/arXiv.2506.01234", "published",    3),
    (2, "Replay sequences predict next-trial performance",      "Nature Neuro",  2025, "10.1038/s41593-025-01872-x", "published",   2),
    (3, "Cryo-EM artifact correction with diffusion priors",    "biorxiv",       2025, "10.1101/2025.03.14.641892",  "preprint",    4),
    (4, "Thermal stability of engineered enzymes",              "JMB",           2024, "10.1016/j.jmb.2024.168412",  "published",   1),
    (5, "Multimodal sleep staging without manual labels",       "biorxiv",       2025, "10.1101/2025.04.07.643219",  "preprint",    5),
    (6, "Audit-log retention design for research labs",         "USENIX SREcon", 2024, "10.5555/3716652.3716701",    "published",   8),
    (7, "Embargoed: cohort B retrospective findings",           "(internal)",    2025, "10.5281/zenodo.11847362",    "under-review",7),
    (8, "Internal dataset versioning at CBG",                   "(internal)",    2025, "10.5281/zenodo.11923401",    "preprint",    6),
]

GRANTS = [
    # id, sponsor, grant_no, pi_employee_id, amount_usd, start_date, end_date, status
    (1, "NIH",                   "R01-NS128374",   1,  2400000.00, "2024-09-01", "2027-08-31", "active"),
    (2, "NSF",                   "IIS-2247891",    2,  1180000.00, "2025-01-01", "2027-12-31", "active"),
    (3, "Lenovo Research Award", "LRA-2025-07",    1,   450000.00, "2025-03-01", "2026-02-28", "active"),
    (4, "DARPA",                 "HR0011-24-C-0147",3, 3200000.00, "2024-06-01", "2026-05-31", "active"),
    (5, "Internal Seed Fund",    "CBG-SEED-12",    5,    85000.00, "2025-02-01", "2025-12-31", "active"),
    (6, "Wellcome Trust",        "WT-220456-Z-20", 2,   720000.00, "2023-04-01", "2024-12-31", "closed"),
]

API_KEYS = [
    # id, service, key, owner_email
    (1, "huggingface_org",  "hf_xKpLmNvQrTsWyZaBcDeFgHi",                    "daniel.obrien@cbg.example"),
    (2, "aws_research_iam", "AKIA4J2XLCF3WKRCBG9M",                           "jonas.lindberg@cbg.example"),
    (3, "wandb",            "bd7a8f3c2e1d9b5a4f6e3c8d1a7b2e9f",               "alice.chen@cbg.example"),
    (4, "openai",           "sk-proj-xKpL9mNvQrTs2uWyZaBcDeFgHiJkLmNoPqRs",  "alice.chen@cbg.example"),
    (5, "github_pat",       "ghp_xKpL9mNvQrTs2uWyZaBcDeFgHiJkLm",            "nico.schmidt@cbg.example"),
    (6, "slack_webhook",    "https://hooks.slack.com/services/T0CBG1A2B/B0CBG3C4D/xKpL9mNvQrTs2uWyZaBc", "grace.park@cbg.example"),
]

SCHEMA_DDL = """
CREATE TABLE employees (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    role        TEXT NOT NULL,
    department  TEXT NOT NULL,
    salary      INTEGER NOT NULL
);

CREATE TABLE projects (
    id              INTEGER PRIMARY KEY,
    code            TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('active', 'paused', 'done')),
    pi_employee_id  INTEGER NOT NULL REFERENCES employees(id),
    start_date      TEXT NOT NULL
);

CREATE TABLE datasets (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT NOT NULL,
    classification  TEXT NOT NULL CHECK (classification IN ('public', 'internal', 'restricted')),
    size_gb         REAL NOT NULL,
    owner_email     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE experiments (
    id           INTEGER PRIMARY KEY,
    project_id   INTEGER NOT NULL REFERENCES projects(id),
    dataset_id   INTEGER NOT NULL REFERENCES datasets(id),
    run_label    TEXT NOT NULL,
    started_at   TEXT NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('running', 'done', 'failed')),
    notes        TEXT
);

CREATE TABLE publications (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    venue       TEXT NOT NULL,
    year        INTEGER NOT NULL,
    doi         TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('preprint', 'published', 'under-review')),
    project_id  INTEGER REFERENCES projects(id)
);

CREATE TABLE grants (
    id              INTEGER PRIMARY KEY,
    sponsor         TEXT NOT NULL,
    grant_no        TEXT NOT NULL UNIQUE,
    pi_employee_id  INTEGER NOT NULL REFERENCES employees(id),
    amount_usd      REAL NOT NULL,
    start_date      TEXT NOT NULL,
    end_date        TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('active', 'closed', 'pending'))
);

CREATE TABLE api_keys (
    id           INTEGER PRIMARY KEY,
    service      TEXT NOT NULL,
    key          TEXT NOT NULL,
    owner_email  TEXT NOT NULL
);
"""


def build(db_path: Path) -> None:
    """Drop any existing db file and rebuild schema + seed rows."""
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_DDL)
        conn.executemany("INSERT INTO employees    VALUES (?, ?, ?, ?, ?, ?)",       EMPLOYEES)
        conn.executemany("INSERT INTO projects     VALUES (?, ?, ?, ?, ?, ?)",       PROJECTS)
        conn.executemany("INSERT INTO datasets     VALUES (?, ?, ?, ?, ?, ?, ?)",    DATASETS)
        conn.executemany("INSERT INTO experiments  VALUES (?, ?, ?, ?, ?, ?, ?)",    EXPERIMENTS)
        conn.executemany("INSERT INTO publications VALUES (?, ?, ?, ?, ?, ?, ?)",    PUBLICATIONS)
        conn.executemany("INSERT INTO grants       VALUES (?, ?, ?, ?, ?, ?, ?, ?)", GRANTS)
        conn.executemany("INSERT INTO api_keys     VALUES (?, ?, ?, ?)",             API_KEYS)
        conn.commit()
    print(f"Wrote {db_path}")
    print(
        f"  employees: {len(EMPLOYEES)}  projects: {len(PROJECTS)}  "
        f"datasets: {len(DATASETS)}  experiments: {len(EXPERIMENTS)}\n"
        f"  publications: {len(PUBLICATIONS)}  grants: {len(GRANTS)}  "
        f"api_keys: {len(API_KEYS)}"
    )


if __name__ == "__main__":
    build(DB_PATH)
