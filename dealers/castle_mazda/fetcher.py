"""
Fetches new-vehicle inventory pages from Castle Mazda Downers Grove.

Same underlying platform as McGrath City Mazda, so this fetcher is
structurally identical -- only BASE_URL differs.
"""

import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.castlemazdadownersgrove.com/inventory/new/mazda"
HEADERS = {
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
MAX_PAGES = 40  # safety cap -- this dealer's site showed ~27 pages of listings


def html_to_text(html: str) -> str:
    """Strip tags down to visible text, same shape the parser expects."""
    soup = BeautifulSoup(html, "html.parser")
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
