#!/usr/bin/env python3
"""
One full scrape run: fetch inventory -> parse vehicles -> save to DB -> export JSON.
"""

import os
import sys
import logging
from datetime import datetime

from fetcher import fetch_all_pages
from parser import parse_inventory_text
from storage import save_snapshot, export_json
from generate_dashboard import generate as generate_dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def main():
    log.info("Starting scrape run")
    try:
        page_text = fetch_all_pages()
    except Exception as e:
        log.error(f"Fetch failed: {e}")
        sys.exit(1)

    # Always save what we actually fetched, so we can debug parsing issues
    # even when zero vehicles are found.
    os.makedirs("data", exist_ok=True)
    with open("data/debug_latest_fetch.txt", "w") as f:
        f.write(page_text)

    listings = parse_inventory_text(page_text)
    if not listings:
        log.warning(
            "No vehicles parsed — check data/debug_latest_fetch.txt "
            "(committed even on failure) to see what was actually fetched."
        )
        sys.exit(1)

    count = save_snapshot(listings)
    export_json()
    dashboard_path = generate_dashboard()
    log.info(f"Saved {count} vehicle price records at {datetime.now().isoformat()}")
    log.info(f"Dashboard updated: {dashboard_path}")


if __name__ == "__main__":
    main()
