"""Fetcher for Napleton's Oak Lawn Mazda (DealerInspire platform)."""

from dealers.common.dealerinspire_fetcher import make_fetcher

fetch_all_pages = make_fetcher("https://www.oaklawnmazda.com/new-vehicles/")
