"""Fetcher for Sam Leman Mazda (DealerInspire platform)."""

from dealers.common.dealerinspire_fetcher import make_fetcher

fetch_all_pages = make_fetcher("https://www.samlemanmazda.com/new-vehicles/")