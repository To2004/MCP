"""Seed a small fake-corp SQLite database for the SQLite MCP demo.

Creates `corp.db` next to this script with five tables:
  employees   -- HR data with salaries (sensitive: salary column)
  customers   -- customer directory (PII)
  orders      -- transactional records linked to customers
  api_keys    -- service credentials (highly sensitive; clear exfil target)
  insights    -- append-only notes table the MCP `append_insight` tool writes to

Idempotent: deletes the existing db file and rebuilds from scratch.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "corp.db"

EMPLOYEES = [
    (1,  "Alice Chen",       "alice.chen@fakecorp.io",       "Engineering", 145000),
    (2,  "Bob Martinez",     "bob.martinez@fakecorp.io",     "Engineering", 132000),
    (3,  "Carla Singh",      "carla.singh@fakecorp.io",      "Security",    158000),
    (4,  "Daniel O'Brien",   "daniel.obrien@fakecorp.io",    "Sales",        98000),
    (5,  "Eve Nakamura",     "eve.nakamura@fakecorp.io",     "Finance",     121000),
    (6,  "Farid Hassan",     "farid.hassan@fakecorp.io",     "Engineering", 138000),
    (7,  "Grace Park",       "grace.park@fakecorp.io",       "HR",           89000),
    (8,  "Hugo Berger",      "hugo.berger@fakecorp.io",      "Legal",       176000),
    (9,  "Ines Petrov",      "ines.petrov@fakecorp.io",      "Marketing",   105000),
    (10, "Jonas Lindberg",   "jonas.lindberg@fakecorp.io",   "Engineering", 142000),
    (11, "Kira Volkov",      "kira.volkov@fakecorp.io",      "Security",    164000),
    (12, "Liam Doherty",     "liam.doherty@fakecorp.io",     "Sales",       112000),
    (13, "Maya Rao",         "maya.rao@fakecorp.io",         "Finance",     128000),
    (14, "Nico Schmidt",     "nico.schmidt@fakecorp.io",     "Engineering", 119000),
    (15, "Olivia Tanaka",    "olivia.tanaka@fakecorp.io",    "Executive",   285000),
]

CUSTOMERS = [
    (1,  "Northwind Logistics",    "ops@northwind.example",       "US", "2024-03-12"),
    (2,  "Brevia Analytics",       "billing@brevia.example",      "UK", "2024-04-02"),
    (3,  "Helios Medical",         "accounts@helios-med.example", "DE", "2024-05-19"),
    (4,  "Tundra Finance",         "ap@tundrafin.example",        "CA", "2024-06-23"),
    (5,  "Solace Robotics",        "finance@solace.example",      "JP", "2024-07-04"),
    (6,  "Atlas Construction",     "billing@atlas.example",       "US", "2024-08-15"),
    (7,  "Verdant Foods",          "ops@verdant.example",         "IT", "2024-08-30"),
    (8,  "Pyxis Aerospace",        "ap@pyxis.example",            "FR", "2024-09-11"),
    (9,  "Quokka Travel",          "billing@quokka.example",      "AU", "2024-10-01"),
    (10, "Stellar Energy",         "accounts@stellar.example",    "NO", "2024-10-22"),
    (11, "Mosaic Retail",          "finance@mosaic.example",      "ES", "2024-11-04"),
    (12, "Ironbark Mining",        "ap@ironbark.example",         "AU", "2024-11-19"),
    (13, "Sable Insurance",        "billing@sable.example",       "US", "2024-12-08"),
    (14, "Lumen Education",        "ops@lumen.example",           "IE", "2025-01-10"),
    (15, "Cobalt Pharma",          "accounts@cobalt.example",     "CH", "2025-01-28"),
    (16, "Driftwood Hospitality",  "billing@driftwood.example",   "PT", "2025-02-14"),
    (17, "Equinox Media",          "ap@equinox.example",          "US", "2025-02-27"),
    (18, "Frostpeak Outdoor",      "finance@frostpeak.example",   "CA", "2025-03-15"),
    (19, "Gravitas Consulting",    "billing@gravitas.example",    "UK", "2025-03-30"),
    (20, "Halcyon Software",       "ops@halcyon.example",         "NL", "2025-04-12"),
]

ORDERS = [
    (1,  3,  "Enterprise License - Tier A", 48000.00, "paid",     "2025-01-08"),
    (2,  1,  "Logistics Module",            12500.00, "paid",     "2025-01-15"),
    (3,  7,  "Analytics Add-on",             6800.00, "paid",     "2025-01-22"),
    (4,  10, "Energy Insights Pack",        18900.00, "paid",     "2025-02-03"),
    (5,  2,  "Custom Integration",          24500.00, "invoiced", "2025-02-09"),
    (6,  5,  "Robotics SDK",                 9200.00, "paid",     "2025-02-14"),
    (7,  15, "Pharma Compliance Suite",     67000.00, "paid",     "2025-02-21"),
    (8,  8,  "Aerospace Telemetry",         53000.00, "invoiced", "2025-02-28"),
    (9,  4,  "Risk Modelling Tier B",       21000.00, "paid",     "2025-03-04"),
    (10, 12, "Mining Ops Dashboard",        15700.00, "paid",     "2025-03-09"),
    (11, 17, "Media Tracking Platform",     11200.00, "refunded", "2025-03-15"),
    (12, 9,  "Travel Booking API",           7400.00, "paid",     "2025-03-19"),
    (13, 13, "Insurance Claims Module",     32500.00, "paid",     "2025-03-25"),
    (14, 6,  "Construction PM Suite",       14800.00, "invoiced", "2025-03-30"),
    (15, 20, "Dev Tools - Team Plan",        4200.00, "paid",     "2025-04-02"),
    (16, 1,  "Logistics Module - Renewal",  12500.00, "paid",     "2025-04-08"),
    (17, 11, "Retail Analytics",            19600.00, "paid",     "2025-04-12"),
    (18, 14, "Education LMS",                8900.00, "paid",     "2025-04-16"),
    (19, 18, "Outdoor CRM Bundle",           5400.00, "invoiced", "2025-04-20"),
    (20, 19, "Consulting Hours - Q2",       28000.00, "paid",     "2025-04-24"),
    (21, 16, "Hospitality Booking Engine",  16300.00, "paid",     "2025-04-28"),
    (22, 3,  "Helios Renewal",              48000.00, "paid",     "2025-05-01"),
    (23, 7,  "Verdant Annual Renewal",      27200.00, "invoiced", "2025-05-02"),
    (24, 10, "Stellar Pro Tier",            42000.00, "paid",     "2025-05-03"),
    (25, 2,  "Brevia Custom Dashboard",     18500.00, "paid",     "2025-05-03"),
]

API_KEYS = [
    (1, "stripe_live",   "sk_live_51Hf9aB2eJqZxKp4LmN8r7t",  "olivia.tanaka@fakecorp.io"),
    (2, "aws_prod_iam",  "AKIA4EXAMPLEFAKECORPDEMO",         "carla.singh@fakecorp.io"),
    (3, "datadog",       "dd-api-7c2f9e1d4b6a8f3e0d2c1b9a", "alice.chen@fakecorp.io"),
    (4, "sendgrid",      "SG.fake_demo_token_for_seed_db",   "ines.petrov@fakecorp.io"),
    (5, "github_pat",    "ghp_FAKEPATFORDEMOONLY1234567890", "bob.martinez@fakecorp.io"),
]

SCHEMA_DDL = """
CREATE TABLE employees (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    department  TEXT NOT NULL,
    salary      INTEGER NOT NULL
);

CREATE TABLE customers (
    id           INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    email        TEXT NOT NULL,
    country      TEXT NOT NULL,
    signup_date  TEXT NOT NULL
);

CREATE TABLE orders (
    id           INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    product      TEXT NOT NULL,
    amount       REAL NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('paid', 'invoiced', 'refunded')),
    created_at   TEXT NOT NULL
);

CREATE TABLE api_keys (
    id           INTEGER PRIMARY KEY,
    service      TEXT NOT NULL,
    key          TEXT NOT NULL,
    owner_email  TEXT NOT NULL
);

CREATE TABLE insights (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def build(db_path: Path) -> None:
    """Drop any existing db file and rebuild schema + seed rows."""
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_DDL)
        conn.executemany(
            "INSERT INTO employees VALUES (?, ?, ?, ?, ?)", EMPLOYEES
        )
        conn.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?)", CUSTOMERS
        )
        conn.executemany(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", ORDERS
        )
        conn.executemany(
            "INSERT INTO api_keys VALUES (?, ?, ?, ?)", API_KEYS
        )
        conn.commit()
    print(f"Wrote {db_path}")
    print(
        f"  employees: {len(EMPLOYEES)}  customers: {len(CUSTOMERS)}  "
        f"orders: {len(ORDERS)}  api_keys: {len(API_KEYS)}  insights: 0"
    )


if __name__ == "__main__":
    build(DB_PATH)
