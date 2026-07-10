#!/usr/bin/env python3
"""
Full scrape run across every registered dealer:
  fetch -> parse -> save to DB -> export JSON -> rebuild dashboard.

One dealer failing (site down, structure changed) does not stop the
others -- each dealer is fetched/parsed independently and errors are
logged, not raised.
"""

import os
import sys
import logging
from datetime import datetime

from dealers.registry import DEALERS
from storage import save_snapshot, export_json
from generate_dashboard import generate as generate_dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def scrape_one_dealer(dealer: dict) -> int:
    """Returns number of vehicles saved for this dealer (0 on failure)."""
    slug = dealer["slug"]
    name = dealer["info"]["name"]
    log.info(f"[{slug}] Starting scrape for {name}")

    try:
        page_text = dealer["fetch_all_pages"]()
    except Exception as e:
        log.error(f"[{slug}] Fetch failed: {e}")
        return 0

    # Save what was actually fetched for debugging, even on parse failure.
    os.makedirs("data/debug", exist_ok=True)
    with open(f"data/debug/{slug}_latest_fetch.txt", "w") as f:
        f.write(page_text)

    listings = dealer["parse_inventory_text"](page_text)
    if not listings:
        log.warning(
            f"[{slug}] No vehicles parsed -- check data/debug/{slug}_latest_fetch.txt "
            "to see what was actually fetched (site structure may have changed)."
        )
        return 0

    count = save_snapshot(listings, dealer["info"])
    log.info(f"[{slug}] Saved {count} vehicle price records")
    return count


def main():
    total = 0
    any_success = False

    for dealer in DEALERS:
        count = scrape_one_dealer(dealer)
        total += count
        if count > 0:
            any_success = True

    if not any_success:
        log.error("All dealers failed to produce data this run.")
        sys.exit(1)

    export_json()
    dashboard_path = generate_dashboard()
    log.info(f"Done. {total} total records saved at {datetime.now().isoformat()}")
    log.info(f"Dashboard updated: {dashboard_path}")


if __name__ == "__main__":
    main()
