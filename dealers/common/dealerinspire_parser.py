"""
Parser for DealerInspire platform inventory pages, built against real
rendered content captured from Napleton's Palatine Mazda (via the
Playwright fetcher in dealers/common/dealerinspire_fetcher.py).

Each vehicle renders as a text block shaped like:

    Location:
    At Dealership
    NEW 2026
    MAZDA3 SEDAN 2.5 S SELECT SPORT
    Stock: PM101037
    VIN: JM1BPABL3T1874682
    DETAILS
    MSRP
    $26,865
    DEALER DISCOUNT
    $674
    CUSTOMER CASH
    $1,500
    ...
    SALE PRICE
    $25,103
    ...
    Trim: 2.5 S Select Sport
    Exterior: Platinum Quartz Metallic
    Interior: Black Leatherette
    KEY FEATURES:

Two different label/value shapes appear:
  - "Stock: X" / "VIN: X" -- label and value on the SAME line
  - "MSRP" / "$X" and "SALE PRICE" / "$X" -- label alone, value on the
    NEXT line
"""

import re
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


# Marks the start of each vehicle block: "NEW <year>\n<MODEL NAME>\n"
# Requiring the 4-digit year directly after "NEW" avoids matching the
# unrelated "NEW" nav link that appears elsewhere on the page.
BLOCK_START_RE = re.compile(r"NEW\s+(?P<year>20\d{2})\s*\n(?P<model>[A-Z][^\n]*)\n")

VIN_RE = re.compile(r"VIN:\s*([A-HJ-NPR-Z0-9]{17})")
STOCK_RE = re.compile(r"Stock:\s*(\S+)")
EXT_COLOR_RE = re.compile(r"Exterior:\s*([^\n]+)")
INT_COLOR_RE = re.compile(r"Interior:\s*([^\n]+)")
# These two have their value on the line AFTER the label, not the same line.
MSRP_RE = re.compile(r"MSRP\s*\n\$([\d,]+)")
SALE_PRICE_RE = re.compile(r"SALE PRICE\s*\n\$([\d,]+)")


def _to_int(money_str: Optional[str]) -> Optional[int]:
    if not money_str:
        return None
    return int(money_str.replace(",", ""))


def _first(pattern: re.Pattern, text: str) -> Optional[str]:
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def parse_inventory_text(page_text: str) -> list[VehicleListing]:
    """Extract all vehicle listings found in the given page text."""
    starts = list(BLOCK_START_RE.finditer(page_text))
    listings = []

    for i, start_match in enumerate(starts):
        block_end = starts[i + 1].start() if i + 1 < len(starts) else len(page_text)
        block = page_text[start_match.start():block_end]

        vin = _first(VIN_RE, block)
        if not vin:
            continue  # skip malformed/incomplete blocks

        listings.append(
            VehicleListing(
                year=start_match.group("year"),
                model=start_match.group("model").strip(),
                vin=vin,
                stock_number=_first(STOCK_RE, block) or "",
                exterior_color=_first(EXT_COLOR_RE, block),
                interior_color=_first(INT_COLOR_RE, block),
                msrp=_to_int(_first(MSRP_RE, block)),
                your_price=_to_int(_first(SALE_PRICE_RE, block)),
            )
        )
    return listings


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "palatine_debug.txt"
    with open(path) as f:
        text = f.read()
    results = parse_inventory_text(text)
    for r in results[:5]:
        print(r.to_dict())
    print(f"\nParsed {len(results)} vehicles")
