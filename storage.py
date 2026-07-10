"""SQLite storage for vehicle price history across multiple dealerships."""

import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = "data/prices.db"

# Base table -- created fresh if the DB doesn't exist yet.
BASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scraped_at TEXT NOT NULL,
    vin TEXT NOT NULL
);
"""

# Every column the app currently expects, beyond the base ones above.
# Adding a new field later just means adding one line here -- init_db()
# will ALTER TABLE to add it to any existing database automatically,
# so old data is never wiped out by a schema change.
REQUIRED_COLUMNS = {
    "dealership": "TEXT",
    "dealership_city": "TEXT",
    "dealership_state": "TEXT",
    "dealership_zip": "TEXT",
    "make": "TEXT",
    "year": "TEXT",
    "model": "TEXT",
    "stock_number": "TEXT",
    "exterior_color": "TEXT",
    "interior_color": "TEXT",
    "msrp": "INTEGER",
    "your_price": "INTEGER",
}

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_vin ON price_snapshots(vin);
CREATE INDEX IF NOT EXISTS idx_scraped_at ON price_snapshots(scraped_at);
CREATE INDEX IF NOT EXISTS idx_dealership ON price_snapshots(dealership);
CREATE INDEX IF NOT EXISTS idx_zip ON price_snapshots(dealership_zip);
"""

# Tracks each vehicle's lifecycle on a dealer's site: when we first saw it,
# when we most recently saw it, and -- if it has since disappeared from the
# site -- when we noticed that. This deliberately does NOT claim the vehicle
# was "sold"; it only tracks presence/absence on the website itself.
VEHICLE_TRACKING_SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicle_tracking (
    dealership TEXT NOT NULL,
    vin TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    removed_at TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    PRIMARY KEY (dealership, vin)
);
CREATE INDEX IF NOT EXISTS idx_tracking_status ON vehicle_tracking(status);
"""


def init_db(db_path: str = DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(BASE_SCHEMA)

    # Migrate: add any columns the current code expects but this database
    # (possibly created by an older version of this script) doesn't have yet.
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(price_snapshots)")}
    for col, col_type in REQUIRED_COLUMNS.items():
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE price_snapshots ADD COLUMN {col} {col_type}")

    conn.executescript(INDEXES)
    conn.executescript(VEHICLE_TRACKING_SCHEMA)
    conn.commit()
    return conn


def save_snapshot(
    listings: list, dealer_info: dict, scraped_at: str = None, db_path: str = DB_PATH
) -> int:
    """
    Insert one row per vehicle for this scrape run.

    listings: list of VehicleListing objects (from a dealer's parser.py)
    dealer_info: dict with keys: name, city, state, zip_code, make
    scraped_at: shared timestamp for this run (so save_snapshot and
        update_vehicle_tracking agree on exactly when "now" was); generated
        if not provided.
    """
    conn = init_db(db_path)
    if scraped_at is None:
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


def update_vehicle_tracking(
    dealership: str, current_vins: list, scraped_at: str, db_path: str = DB_PATH
):
    """
    Call once per dealer per scrape run, with the full list of VINs found
    in that run. Updates first_seen_at/last_seen_at for everything present,
    and marks anything that WAS active but is no longer present as
    'removed' (with a removed_at timestamp) -- without claiming it sold.

    If a previously-removed VIN reappears, it's marked 'active' again and
    removed_at is cleared, but first_seen_at is left untouched (so "days on
    website" reflects the original listing date, not the reappearance).
    """
    conn = init_db(db_path)
    current_set = set(current_vins)

    for vin in current_set:
        existing = conn.execute(
            "SELECT 1 FROM vehicle_tracking WHERE dealership=? AND vin=?",
            (dealership, vin),
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE vehicle_tracking
                   SET last_seen_at=?, status='active', removed_at=NULL
                   WHERE dealership=? AND vin=?""",
                (scraped_at, dealership, vin),
            )
        else:
            conn.execute(
                """INSERT INTO vehicle_tracking
                   (dealership, vin, first_seen_at, last_seen_at, status, removed_at)
                   VALUES (?, ?, ?, ?, 'active', NULL)""",
                (dealership, vin, scraped_at, scraped_at),
            )

    previously_active = conn.execute(
        "SELECT vin FROM vehicle_tracking WHERE dealership=? AND status='active'",
        (dealership,),
    ).fetchall()
    for (vin,) in previously_active:
        if vin not in current_set:
            conn.execute(
                """UPDATE vehicle_tracking
                   SET status='removed', removed_at=?
                   WHERE dealership=? AND vin=?""",
                (scraped_at, dealership, vin),
            )

    conn.commit()
    conn.close()


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


def export_tracking_json(db_path: str = DB_PATH, out_path: str = "data/vehicle_tracking.json"):
    """Export the vehicle_tracking table as JSON for the dashboard."""
    import json

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM vehicle_tracking").fetchall()
    conn.close()

    data = [dict(r) for r in rows]
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    return out_path


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")
