"""
Generic fetcher for dealer sites built on the DealerInspire platform.

Unlike the Dealer.com/DealerOn-style sites (McGrath, Castle), DealerInspire
renders inventory listings client-side via JavaScript -- the initial page
HTML contains no vehicle data at all. This fetcher uses Playwright to
actually run a headless browser, load the page, wait for the inventory
to render, and then extract the rendered text.

Usage from a dealer's own fetcher.py:

    from dealers.common.dealerinspire_fetcher import make_fetcher
    fetch_all_pages = make_fetcher("https://www.example-dealer.com/new-vehicles/")
"""

import time
from playwright.sync_api import sync_playwright

REQUEST_DELAY_SECONDS = 2


def make_fetcher(inventory_url: str, max_pages: int = 40):
    """
    Returns a fetch_all_pages() function bound to the given dealer's
    inventory URL. DealerInspire sites often show all vehicles on one
    page with a "Load More" button rather than numbered pages -- this
    clicks "Load More" repeatedly until no more appears, then returns
    the full rendered page text.
    """

    def fetch_all_pages() -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
                )
            )
            page.goto(inventory_url, wait_until="networkidle", timeout=60000)
            time.sleep(3)  # let any post-load XHR-driven rendering settle

            # Try clicking a "Load More" / "Show More" button repeatedly,
            # common on DealerInspire inventory pages, to get the full list
            # rather than just the first batch. If no such button exists,
            # this simply does nothing and we fetch what's on the page.
            clicks = 0
            while clicks < max_pages:
                clicked = False
                for label in ["Load More", "Show More", "View More"]:
                    locator = page.get_by_text(label, exact=False)
                    if locator.count() > 0:
                        try:
                            locator.first.click(timeout=3000)
                            time.sleep(REQUEST_DELAY_SECONDS)
                            clicked = True
                            clicks += 1
                            break
                        except Exception:
                            pass
                if not clicked:
                    break

            text = page.inner_text("body")
            browser.close()
            return text

    return fetch_all_pages
