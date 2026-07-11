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
# A single User-Agent header, with no other browser-typical headers, is a
# common bot-detection trigger -- this site was outright blocking requests
# (403) until a fuller, more realistic header set was sent.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.mazdaofcrystallake.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
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
    session = requests.Session()
    session.headers.update(HEADERS)

    # Visit the homepage first to pick up cookies -- a cold direct hit to a
    # deep search URL (no prior navigation) is itself a common bot signal.
    try:
        session.get("https://www.mazdaofcrystallake.com/", timeout=15)
        time.sleep(1)
    except requests.RequestException:
        pass  # not fatal -- proceed to the real fetch either way

    all_text = []
    for page in range(1, MAX_PAGES + 1):
        params = {**PARAMS, "p": page}
        resp = session.get(BASE_URL, params=params, timeout=15)
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