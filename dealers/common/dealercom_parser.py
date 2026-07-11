"""
Shared parser for dealer inventory pages built on the common platform pattern
seen across many Mazda dealer sites (McGrath City Mazda, Castle Mazda
Downers Grove, and likely others): each vehicle renders as a text block
containing, in order:

  <year> Mazda/MAZDA <model/trim> ... View All Features
  Location: ...
  VIN: <17-char VIN> Stock: #<stock#>
  Exterior Color: ... Interior Color: ...
  [optional: Transmission: ... DriveTrain: ...]
  Highway/City MPG: ..
  MSRP $X,XXX ... Your Price $X,XXX

This parses the *rendered text* of the page rather than relying on CSS
class names, since those are more likely to change across site updates
than the underlying labels ("VIN:", "MSRP", "Your Price"). If a new
dealer's site turns out to follow this same pattern, it can reuse this
parser as-is (see dealers/mcgrath_mazda/parser.py and
dealers/castle_mazda/parser.py for the thin per-dealer wrappers).
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


# Marks the start of each vehicle block: "<year> MAZDA<model...> View All Features"
#
# Some sites (e.g. Castle Mazda) render a duplicate title right before the
# real one -- e.g. "2026 Mazda MAZDA3 Sedan 2.5 S New2026 MAZDA3 Sedan 2.5 S
# View All Features" -- where the first "2026 Mazda MAZDA3..." is a
# duplicate (alt-text style) and the second, right before "View All
# Features", is the one we actually want. The negative lookahead below
# forbids another "20XX MAZDA" sequence from appearing inside the captured
# model text, which makes the match fall through to the LAST such sequence
# before "View All Features" when a duplicate exists, while leaving
# single-occurrence sites (McGrath) unaffected.
BLOCK_START_RE = re.compile(
    r"(?P<year>20\d{2})\s+MAZDA(?P<model>\d?(?:(?!20\d{2}\s+MAZDA).)*?)\s+View All Features",
    re.DOTALL | re.IGNORECASE,
)

VIN_RE = re.compile(r"VIN:\s*([A-HJ-NPR-Z0-9]{17})")
STOCK_RE = re.compile(r"Stock:\s*#?(\S+?)\s*(?=Exterior Color:|Interior Color:|Highway|MSRP|$)")
EXT_COLOR_RE = re.compile(r"Exterior Color:\s*(.+?)\s*(?=Interior Color:)", re.DOTALL)
# Some sites insert Transmission:/DriveTrain: between Interior Color and
# Highway/City MPG -- stop there too so those fields don't get swallowed
# into interior_color.
INT_COLOR_RE = re.compile(
    r"Interior Color:\s*(.+?)\s*(?=Transmission:|Highway|MSRP)", re.DOTALL
)
MSRP_RE = re.compile(r"MSRP\s*\$([\d,]+)")
YOUR_PRICE_RE = re.compile(r"Your Price\s*\$([\d,]+)")
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
            continue  # skip malformed/incomplete blocks

        model = start_match.group("model").strip()
        # Reattach "MAZDA" prefix for sedans branded as "MAZDA3"/"MAZDA6"
        # (the digit was captured separately from the brand name above).
        if model[:1].isdigit():
            model = f"MAZDA{model}"

        # Some dealers display the VIN itself in place of a stock number
        # for vehicles that are "in transit" and haven't been physically
        # tagged yet. That's not a real stock number, so treat it as blank
        # rather than storing a duplicate of the VIN.
        stock_number = _first(STOCK_RE, block) or ""
        if stock_number == vin:
            stock_number = ""

        in_transit = bool(IN_TRANSIT_RE.search(block))

        listings.append(
            VehicleListing(
                year=start_match.group("year"),
                model=model,
                vin=vin,
                stock_number=stock_number,
                exterior_color=_first(EXT_COLOR_RE, block),
                interior_color=_first(INT_COLOR_RE, block),
                msrp=_to_int(_first(MSRP_RE, block)),
                your_price=_to_int(_first(YOUR_PRICE_RE, block)),
                in_transit=in_transit,
            )
        )
    return listings
