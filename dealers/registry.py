"""
Registry of all dealers to scrape.

To add a new dealer:
  1. Create dealers/<dealer_slug>/ with: __init__.py, config.py, fetcher.py, parser.py
     (config.py defines DEALER_INFO; fetcher.py defines fetch_all_pages();
      parser.py defines parse_inventory_text())
  2. Import it below and add it to DEALERS.
"""

from dealers.mcgrath_mazda import config as mcgrath_config
from dealers.mcgrath_mazda import fetcher as mcgrath_fetcher
from dealers.mcgrath_mazda import parser as mcgrath_parser

from dealers.castle_mazda import config as castle_config
from dealers.castle_mazda import fetcher as castle_fetcher
from dealers.castle_mazda import parser as castle_parser

DEALERS = [
    {
        "slug": "mcgrath_mazda",
        "info": mcgrath_config.DEALER_INFO,
        "fetch_all_pages": mcgrath_fetcher.fetch_all_pages,
        "parse_inventory_text": mcgrath_parser.parse_inventory_text,
    },
    {
        "slug": "castle_mazda",
        "info": castle_config.DEALER_INFO,
        "fetch_all_pages": castle_fetcher.fetch_all_pages,
        "parse_inventory_text": castle_parser.parse_inventory_text,
    },
    # Add the next dealer here, e.g.:
    # {
    #     "slug": "some_other_mazda",
    #     "info": some_other_config.DEALER_INFO,
    #     "fetch_all_pages": some_other_fetcher.fetch_all_pages,
    #     "parse_inventory_text": some_other_parser.parse_inventory_text,
    # },
]
