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
PAGE_MARKER_RE = re.compile(r"Page (\d+) of (\d+)")


def make_fetcher(inventory_url: str, max_pages: int = 40):
    """
    Returns a fetch_all_pages() function bound to the given dealer's
    inventory URL. DealerInspire sites use one of two pagination styles:
    a "Load More" button that appends more results to the same page, or
    numbered pages with a "Next" link showing "Page X of Y". This handles
    both -- accumulating text across every page/batch.

    For the numbered-page style, this polls for the "Page X of Y" marker
    to actually change after clicking Next, rather than waiting for
    network-idle -- background chat widgets/analytics can keep a page
    "busy" indefinitely, making network-idle an unreliable signal here.
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
            page.goto(inventory_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)  # let post-load XHR-driven rendering settle

            all_text = [page.inner_text("body")]

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

                # Style 2: numbered pages with a "Next" control.
                current_text = all_text[-1]
                marker_match = PAGE_MARKER_RE.search(current_text)
                if not marker_match:
                    break  # no pagination marker at all -- single page site

                current_page_num = int(marker_match.group(1))
                total_pages = int(marker_match.group(2))
                if current_page_num >= total_pages:
                    break  # already on the last page

                # Try a few ways of locating the real "Next" control, since
                # a plain text match can accidentally hit an unrelated
                # "Next" elsewhere on the page (e.g. an image carousel).
                next_locator = None
                for get_locator in (
                    lambda: page.get_by_role("link", name="Next", exact=False),
                    lambda: page.get_by_role("button", name="Next", exact=False),
                    lambda: page.get_by_text("Next", exact=False),
                ):
                    try:
                        loc = get_locator()
                        if loc.count() > 0:
                            next_locator = loc.first
                            break
                    except Exception:
                        continue

                if next_locator is None:
                    break

                try:
                    next_locator.scroll_into_view_if_needed(timeout=5000)
                    next_locator.click(timeout=5000)
                except Exception:
                    break

                # Poll for the page marker to actually change (up to ~15s)
                # instead of trusting network-idle.
                changed = False
                for _ in range(30):
                    time.sleep(0.5)
                    new_text = page.inner_text("body")
                    new_marker_match = PAGE_MARKER_RE.search(new_text)
                    if new_marker_match and int(new_marker_match.group(1)) != current_page_num:
                        all_text.append(new_text)
                        changed = True
                        break

                if not changed:
                    break

            browser.close()
            return "\n".join(all_text)

    return fetch_all_pages