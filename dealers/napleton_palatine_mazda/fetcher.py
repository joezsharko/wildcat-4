"""Fetcher for Napleton's Palatine Mazda (DealerInspire platform)."""

from dealers.common.dealerinspire_fetcher import make_fetcher

fetch_all_pages = make_fetcher("https://www.palatinemazda.com/new-vehicles/")
