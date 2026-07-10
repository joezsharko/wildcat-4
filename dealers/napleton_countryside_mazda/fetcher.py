"""Fetcher for Napleton's Countryside Mazda (DealerInspire platform)."""

from dealers.common.dealerinspire_fetcher import make_fetcher

fetch_all_pages = make_fetcher("https://www.napletonscountrysidemazda.com/new-vehicles/")
