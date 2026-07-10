"""Fetcher for Napleton's Schaumburg Mazda (DealerInspire platform)."""

from dealers.common.dealerinspire_fetcher import make_fetcher

fetch_all_pages = make_fetcher("https://www.schaumburgmazda.com/new-vehicles/")
