"""
Fetches new-vehicle inventory pages from McGrath City Mazda.

Run this on a machine with real internet access (this won't work inside
an isolated sandbox) -- your own laptop, a Raspberry Pi, or a small VPS.
"""

import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.mcgrathcitymazda.com/inventory/new/mazda"
HEADERS = {
    # Identify as a normal browser; be a good citizen, don't hammer the site.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    )
}
PARAMS = {
    "paymenttype": "cash",
    "instock": "true",
    "intransit": "true",
    "inproduction": "true",
}
REQUEST_DELAY_SECONDS = 2  # be polite between page requests
MAX_PAGES = 25  # safety cap


def html_to_text(html: str) -> str:
    """Strip tags down to visible text, same shape the parser expects."""
    soup = BeautifulSoup(html, "html.parser")
    # Drop script/style content -- it can contain "VIN:"-like noise
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator=" ")


def fetch_all_pages() -> str:
    """Fetch every inventory page and return the concatenated page text."""
    all_text = []
    for page in range(1, MAX_PAGES + 1):
        params = {**PARAMS, "page": page}
        resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        text = html_to_text(resp.text)

        # Stop once we hit a page with no vehicle blocks (past the last page)
        if "VIN:" not in text:
            break

        all_text.append(text)
        time.sleep(REQUEST_DELAY_SECONDS)

    return "\n".join(all_text)


if __name__ == "__main__":
    text = fetch_all_pages()
    with open("latest_fetch.html", "w") as f:
        f.write(text)
    print(f"Fetched {len(text)} characters, saved to latest_fetch.html")
