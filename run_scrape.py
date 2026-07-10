#!/usr/bin/env python3
"""
One full scrape run: fetch inventory -> parse vehicles -> save to DB -> export JSON.

Usage:
    python3 run_scrape.py

Intended to be triggered by cron on a schedule, e.g. every 6 hours:
    0 */6 * * * cd /path/to/mazda_scraper && /usr/bin/python3 run_scrape.py >> scrape.log 2>&1
"""

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

    listings = parse_inventory_text(page_text)
    if not listings:
        log.warning("No vehicles parsed — site structure may have changed, "
                     "or the site returned an error/blocked page. Check "
                     "latest_fetch.html isn't needed to debug this.")
        sys.exit(1)

    count = save_snapshot(listings)
    export_json()
    dashboard_path = generate_dashboard()
    log.info(f"Saved {count} vehicle price records at {datetime.now().isoformat()}")
    log.info(f"Dashboard updated: {dashboard_path}")


if __name__ == "__main__":
    main()
