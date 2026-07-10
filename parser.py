"""
Parser for McGrath City Mazda inventory pages.

The site renders each vehicle as a text block containing, in order:
  <year> Mazda <model/trim> ... VIN: <17-char VIN> Stock: #<stock#>
  Exterior Color: ... Interior Color: ... Highway/City MPG: ..
  MSRP $X,XXX ... Your Price $X,XXX

This parses the *rendered text* of the page rather than relying on CSS
class names, since those are more likely to change across site updates
than the underlying labels ("VIN:", "MSRP", "Your Price").
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


# Marks the start of each vehicle block: "<year> Mazda <model...> playbutton"
# Splitting on these boundaries first (rather than one giant regex) avoids
# a field from one vehicle leaking into the next.
BLOCK_START_RE = re.compile(r"(?P<year>20\d{2})\s+Mazda\s+(?P<model>.+?)\s+playbutton")

VIN_RE = re.compile(r"VIN:\s*([A-HJ-NPR-Z0-9]{17})")
STOCK_RE = re.compile(r"Stock:\s*#?(\S+?)(?=Exterior Color:|Interior Color:|Highway|MSRP|$)")
EXT_COLOR_RE = re.compile(r"Exterior Color:\s*(.+?)(?=Interior Color:)")
INT_COLOR_RE = re.compile(r"Interior Color:\s*(.+?)(?=Highway|MSRP)")
MSRP_RE = re.compile(r"MSRP\s*\$([\d,]+)")
YOUR_PRICE_RE = re.compile(r"Your Price\s*\$([\d,]+)")


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
                your_price=_to_int(_first(YOUR_PRICE_RE, block)),
            )
        )
    return listings


if __name__ == "__main__":
    with open("sample_page.txt") as f:
        text = f.read()
    results = parse_inventory_text(text)
    for r in results:
        print(r.to_dict())
    print(f"\nParsed {len(results)} vehicles")
