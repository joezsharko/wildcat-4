"""
Fetches new-vehicle inventory pages from Mazda of Crystal Lake.

This dealer's site is built on the "Dealer eProcess" platform -- like
McGrath/Castle (Dealer.com-style), it's server-rendered, so a plain HTTP
fetch + BeautifulSoup works fine; no headless browser needed.
"""

import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.mazdaofcrystallake.com/search/new-mazda-crystal-lake-il/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    )
}
PARAMS = {"cy": "60014", "tp": "new"}
REQUEST_DELAY_SECONDS = 2
MAX_PAGES = 20


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator=" ")


def fetch_all_pages() -> str:
    """Fetch every inventory page and return the concatenated page text."""
    all_text = []
    for page in range(1, MAX_PAGES + 1):
        params = {**PARAMS, "p": page}
        resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        text = html_to_text(resp.text)

        if "VIN" not in text:
            break

        all_text.append(text)
        time.sleep(REQUEST_DELAY_SECONDS)

    return "\n".join(all_text)


if __name__ == "__main__":
    text = fetch_all_pages()
    with open("latest_fetch.html", "w") as f:
        f.write(text)
    print(f"Fetched {len(text)} characters, saved to latest_fetch.html")
