"""
Parser for DealerInspire platform inventory pages.

STATUS: placeholder. Unlike the dealercom_parser (built and verified
against real fetched content from McGrath/Castle), this one hasn't been
written against real rendered output yet -- Playwright's headless browser
can only run where it has real internet access (GitHub Actions), not in
the sandbox this was built in.

This intentionally returns an empty list for now. run_scrape.py already
saves the actual fetched text to data/debug/<slug>_latest_fetch.txt on
every run (even when 0 vehicles are parsed), so the plan is:
  1. Run the scrape once via GitHub Actions.
  2. Pull the debug file to see the real rendered text/structure.
  3. Replace this placeholder with real regexes based on that, the same
     way dealercom_parser.py was built from McGrath's real page content.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VehicleListing:
    year: str
    model: str
    vin: str
    stock_number: str
    exterior_color: Optional[str]
    interior_color: Optional[str]
    msrp: Optional[int]
    your_price: Optional[int]

    def to_dict(self):
        return {
            "year": self.year,
            "model": self.model,
            "vin": self.vin,
            "stock_number": self.stock_number,
            "exterior_color": self.exterior_color,
            "interior_color": self.interior_color,
            "msrp": self.msrp,
            "your_price": self.your_price,
        }


def parse_inventory_text(page_text: str) -> list[VehicleListing]:
    """Placeholder -- see module docstring. Returns [] until real regexes
    are written against actual DealerInspire output."""
    return []
