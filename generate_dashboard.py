#!/usr/bin/env python3
"""
Builds the multi-page dashboard in docs/:
  index.html     -- summary: stats, filtered/ranged chart, dealer grid, removed summary
  inventory.html -- full sortable current-inventory table
  removed.html   -- full sortable removed-vehicles table
  style.css, common.js, chart.umd.js -- shared assets
  data.json, tracking.json -- data, fetched at runtime by all three pages

This replaced the old single-self-contained-HTML-file approach: since these
pages are only ever viewed via the live GitHub Pages URL (not opened as a
local file), fetch()-based loading of shared JSON works fine and avoids
tripling the embedded data/chart-library payload across three pages.
"""

import json
import os
import shutil
import sqlite3

DB_PATH = "data/prices.db"
DOCS_DIR = "docs"
SRC_DIR = "dashboard_src"
CHARTJS_PATH = "vendor/chart.umd.js"

STATIC_FILES = ["style.css", "common.js", "index.html", "inventory.html", "removed.html"]


def _ensure_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraped_at TEXT NOT NULL,
            vin TEXT NOT NULL,
            year TEXT,
            model TEXT,
            stock_number TEXT,
            exterior_color TEXT,
            interior_color TEXT,
            msrp INTEGER,
            your_price INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_tracking (
            dealership TEXT NOT NULL,
            vin TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            removed_at TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            PRIMARY KEY (dealership, vin)
        )
    """)


def generate(db_path: str = DB_PATH, docs_dir: str = DOCS_DIR,
             src_dir: str = SRC_DIR, chartjs_path: str = CHARTJS_PATH):
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # ---- Copy static page templates + shared assets verbatim ----
    for fname in STATIC_FILES:
        shutil.copyfile(os.path.join(src_dir, fname), os.path.join(docs_dir, fname))
    shutil.copyfile(chartjs_path, os.path.join(docs_dir, "chart.umd.js"))

    # ---- Export data as JSON for the pages to fetch() at runtime ----
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _ensure_tables(conn)

    price_rows = [dict(r) for r in conn.execute(
        "SELECT * FROM price_snapshots ORDER BY scraped_at ASC"
    ).fetchall()]
    tracking_rows = [dict(r) for r in conn.execute(
        "SELECT * FROM vehicle_tracking"
    ).fetchall()]
    conn.close()

    with open(os.path.join(docs_dir, "data.json"), "w") as f:
        json.dump(price_rows, f)
    with open(os.path.join(docs_dir, "tracking.json"), "w") as f:
        json.dump(tracking_rows, f)

    return os.path.join(docs_dir, "index.html")


if __name__ == "__main__":
    path = generate()
    print(f"Dashboard written to {path}")
