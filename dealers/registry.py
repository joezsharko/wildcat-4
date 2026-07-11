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

from dealers.napleton_palatine_mazda import config as palatine_config
from dealers.napleton_palatine_mazda import fetcher as palatine_fetcher
from dealers.napleton_palatine_mazda import parser as palatine_parser

from dealers.napleton_schaumburg_mazda import config as schaumburg_config
from dealers.napleton_schaumburg_mazda import fetcher as schaumburg_fetcher
from dealers.napleton_schaumburg_mazda import parser as schaumburg_parser

from dealers.napleton_countryside_mazda import config as countryside_config
from dealers.napleton_countryside_mazda import fetcher as countryside_fetcher
from dealers.napleton_countryside_mazda import parser as countryside_parser

from dealers.napleton_oaklawn_mazda import config as oaklawn_config
from dealers.napleton_oaklawn_mazda import fetcher as oaklawn_fetcher
from dealers.napleton_oaklawn_mazda import parser as oaklawn_parser

from dealers.sam_leman_mazda import config as samleman_config
from dealers.sam_leman_mazda import fetcher as samleman_fetcher
from dealers.sam_leman_mazda import parser as samleman_parser

from dealers.mazda_of_crystal_lake import config as crystallake_config
from dealers.mazda_of_crystal_lake import fetcher as crystallake_fetcher
from dealers.mazda_of_crystal_lake import parser as crystallake_parser

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
    {
        "slug": "napleton_palatine_mazda",
        "info": palatine_config.DEALER_INFO,
        "fetch_all_pages": palatine_fetcher.fetch_all_pages,
        "parse_inventory_text": palatine_parser.parse_inventory_text,
    },
    {
        "slug": "napleton_schaumburg_mazda",
        "info": schaumburg_config.DEALER_INFO,
        "fetch_all_pages": schaumburg_fetcher.fetch_all_pages,
        "parse_inventory_text": schaumburg_parser.parse_inventory_text,
    },
    {
        "slug": "napleton_countryside_mazda",
        "info": countryside_config.DEALER_INFO,
        "fetch_all_pages": countryside_fetcher.fetch_all_pages,
        "parse_inventory_text": countryside_parser.parse_inventory_text,
    },
    {
        "slug": "napleton_oaklawn_mazda",
        "info": oaklawn_config.DEALER_INFO,
        "fetch_all_pages": oaklawn_fetcher.fetch_all_pages,
        "parse_inventory_text": oaklawn_parser.parse_inventory_text,
    },
    {
        "slug": "sam_leman_mazda",
        "info": samleman_config.DEALER_INFO,
        "fetch_all_pages": samleman_fetcher.fetch_all_pages,
        "parse_inventory_text": samleman_parser.parse_inventory_text,
    },
    {
        "slug": "mazda_of_crystal_lake",
        "info": crystallake_config.DEALER_INFO,
        "fetch_all_pages": crystallake_fetcher.fetch_all_pages,
        "parse_inventory_text": crystallake_parser.parse_inventory_text,
    },
    # Add the next dealer here, e.g.:
    # {
    #     "slug": "some_other_mazda",
    #     "info": some_other_config.DEALER_INFO,
    #     "fetch_all_pages": some_other_fetcher.fetch_all_pages,
    #     "parse_inventory_text": some_other_parser.parse_inventory_text,
    # },
]
