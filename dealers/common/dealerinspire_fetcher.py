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

import re
import time
from playwright.sync_api import sync_playwright

REQUEST_DELAY_SECONDS = 2


def make_fetcher(inventory_url: str, max_pages: int = 40):
    """
    Returns a fetch_all_pages() function bound to the given dealer's
    inventory URL. DealerInspire sites use one of two pagination styles:
    a "Load More" button that appends more results to the same page, or
    numbered pages with a "Next" link. This handles both -- accumulating
    text across every page/batch until neither pattern advances further.
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

            all_text = [page.inner_text("body")]
            seen_page_markers = set()

            for _ in range(max_pages):
                advanced = False

                # Style 1: "Load More" appends more vehicles to the same page.
                for label in ["Load More", "Show More", "View More"]:
                    locator = page.get_by_text(label, exact=False)
                    if locator.count() > 0:
                        try:
                            locator.first.click(timeout=3000)
                            time.sleep(REQUEST_DELAY_SECONDS)
                            all_text.append(page.inner_text("body"))
                            advanced = True
                            break
                        except Exception:
                            pass
                if advanced:
                    continue

                # Style 2: numbered pages with a "Next" link. Guard against
                # an infinite loop by tracking which "Page X of Y" marker
                # we've already seen -- if it repeats, we've reached the end.
                next_locator = page.get_by_text("Next", exact=False)
                if next_locator.count() > 0:
                    page_marker_match = re.search(r"Page \d+ of \d+", all_text[-1])
                    marker = page_marker_match.group(0) if page_marker_match else None
                    if marker:
                        seen_page_markers.add(marker)
                    try:
                        next_locator.first.click(timeout=3000)
                        time.sleep(REQUEST_DELAY_SECONDS)
                        page.wait_for_load_state("networkidle", timeout=15000)
                        new_text = page.inner_text("body")
                        new_marker_match = re.search(r"Page \d+ of \d+", new_text)
                        new_marker = new_marker_match.group(0) if new_marker_match else None
                        if new_marker and new_marker in seen_page_markers:
                            break  # looped back -- we've reached the last page
                        all_text.append(new_text)
                        advanced = True
                    except Exception:
                        pass

                if not advanced:
                    break

            browser.close()
            return "\n".join(all_text)

    return fetch_all_pages
