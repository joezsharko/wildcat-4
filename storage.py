"""SQLite storage for vehicle price history across multiple dealerships."""

import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = "data/prices.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scraped_at TEXT NOT NULL,

    -- Dealership / location context (constant per dealer, repeated per row
    -- for simplicity -- fine at this scale, easy to query/filter/sort on)
    dealership TEXT NOT NULL,
    dealership_city TEXT,
    dealership_state TEXT,
    dealership_zip TEXT,

    -- Vehicle data
    make TEXT,
    year TEXT,
    model TEXT,
    vin TEXT NOT NULL,
    stock_number TEXT,
    exterior_color TEXT,
    interior_color TEXT,
    msrp INTEGER,
    your_price INTEGER
);
CREATE INDEX IF NOT EXISTS idx_vin ON price_snapshots(vin);
CREATE INDEX IF NOT EXISTS idx_scraped_at ON price_snapshots(scraped_at);
CREATE INDEX IF NOT EXISTS idx_dealership ON price_snapshots(dealership);
CREATE INDEX IF NOT EXISTS idx_zip ON price_snapshots(dealership_zip);
"""


def init_db(db_path: str = DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def save_snapshot(listings: list, dealer_info: dict, db_path: str = DB_PATH) -> int:
    """
    Insert one row per vehicle for this scrape run.

    listings: list of VehicleListing objects (from a dealer's parser.py)
    dealer_info: dict with keys: name, city, state, zip_code, make
    """
    conn = init_db(db_path)
    scraped_at = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            scraped_at,
            dealer_info["name"],
            dealer_info.get("city"),
            dealer_info.get("state"),
            dealer_info.get("zip_code"),
            dealer_info.get("make"),
            v.year,
            v.model,
            v.vin,
            v.stock_number,
            v.exterior_color,
            v.interior_color,
            v.msrp,
            v.your_price,
        )
        for v in listings
    ]
    conn.executemany(
        """INSERT INTO price_snapshots
           (scraped_at, dealership, dealership_city, dealership_state,
            dealership_zip, make, year, model, vin, stock_number,
            exterior_color, interior_color, msrp, your_price)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    conn.close()
    return len(rows)


def export_json(db_path: str = DB_PATH, out_path: str = "data/price_history.json"):
    """Export all snapshots as JSON (handy for debugging/other tools)."""
    import json

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM price_snapshots ORDER BY scraped_at ASC"
    ).fetchall()
    conn.close()

    data = [dict(r) for r in rows]
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    return out_path


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")
