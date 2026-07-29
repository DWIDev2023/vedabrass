from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(slots=True)
class BundleCandidate:

    products: list

    bundle_type: str

    score: int

    priority: int

    name: str = ""

    slug: str = ""

    short_description: str = ""

    description: str = ""

    bundle_price: float = 0

    discounted_bundle_price: float = 0

    bundle_price: Decimal | int = 0
    discounted_bundle_price: Decimal | int = 0
    discount_percentage: int = 0
    savings: Decimal | int = 0