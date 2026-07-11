"""
Parser for Mazda of Crystal Lake inventory pages (Dealer eProcess platform).

STATUS: best-effort. Built against real page content captured via a
markdown-rendering fetch, but not yet verified against the actual
BeautifulSoup get_text() output the live fetcher will produce -- table-like
layouts sometimes render with different whitespace than markdown
conversion implies. Treat this like the DealerInspire parsers' first
version: check data/debug/mazda_of_crystal_lake_latest_fetch.txt after the
first real run and adjust if the vehicle count comes back at/near zero.

Each vehicle block looks like (label/value pairs separated by whitespace,
not a fixed delimiter):

    New 2026 Mazda CX-30 2.5 S Select Sport AWD
    Location: ... [In Transit, if applicable]
    ... engine/MPG blurb ...
    Mileage <n> Trim 2.5 S Select Sport AWD Stock # 45054
    VIN 3MVDMBBL2TM207515
    Exterior Color Jet Black Mica Interior Color Black Drivetrain AWD
    ... feature bullets ...
    MSRP $29,780
    [Anderson Discount -$746] [Customer Cash -$1,000] Doc Fee +377 ERT +35
    Anderson Price $28,446
    Conditional Specials -$2,500

Note: the final price label varies by dealer on this platform (this one
happens to be owned by "Anderson Motor Company", hence "Anderson Price")
-- the regex below matches whatever word precedes "Price" rather than a
fixed label.
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
    in_transit: bool = False

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
            "in_transit": self.in_transit,
        }


BLOCK_START_RE = re.compile(
    r"(?:New\s+)?(?P<year>20\d{2})\s+Mazda\s+(?P<model>.+?)\s+Location:",
    re.DOTALL | re.IGNORECASE,
)

VIN_RE = re.compile(r"\bVIN\s+([A-HJ-NPR-Z0-9]{17})")
STOCK_RE = re.compile(r"Stock #\s*(\S*?)\s*VIN", re.DOTALL)
TRIM_RE = re.compile(r"\bTrim\s+(.+?)\s+Stock #", re.DOTALL)
EXT_COLOR_RE = re.compile(r"Exterior Color\s+(.+?)\s+Interior Color", re.DOTALL)
INT_COLOR_RE = re.compile(r"Interior Color\s+(.+?)\s+Drivetrain", re.DOTALL)
MSRP_RE = re.compile(r"\bMSRP\s+\$([\d,]+)")
# Final price label varies per dealer (e.g. "Anderson Price") -- match
# whatever precedes "Price $X" right after the ERT line.
FINAL_PRICE_RE = re.compile(r"ERT\s+[+\-]?[\d,]+\s+[A-Za-z]+\s+Price\s+\$([\d,]+)")
IN_TRANSIT_RE = re.compile(r"\bIn Transit\b", re.IGNORECASE)


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
            continue

        listings.append(
            VehicleListing(
                year=start_match.group("year"),
                model=start_match.group("model").strip(),
                vin=vin,
                stock_number=_first(STOCK_RE, block) or "",
                exterior_color=_first(EXT_COLOR_RE, block),
                interior_color=_first(INT_COLOR_RE, block),
                msrp=_to_int(_first(MSRP_RE, block)),
                your_price=_to_int(_first(FINAL_PRICE_RE, block)),
                in_transit=bool(IN_TRANSIT_RE.search(block)),
            )
        )
    return listings


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "crystal_lake_sample.txt"
    with open(path) as f:
        text = f.read()
    results = parse_inventory_text(text)
    for r in results:
        print(r.to_dict())
    print(f"\nParsed {len(results)} vehicles")
