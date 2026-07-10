"""
Parser for McGrath City Mazda inventory pages -- this dealer's site runs on
the same underlying platform as several other Mazda dealers, so all the
real parsing logic lives in dealers/common/dealercom_parser.py and is
simply re-exported here.
"""

from dealers.common.dealercom_parser import parse_inventory_text, VehicleListing

__all__ = ["parse_inventory_text", "VehicleListing"]


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "real_page.txt"
    with open(path) as f:
        text = f.read()
    results = parse_inventory_text(text)
    for r in results[:5]:
        print(r.to_dict())
    print(f"\nParsed {len(results)} vehicles")
