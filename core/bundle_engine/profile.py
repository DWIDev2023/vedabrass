from dataclasses import dataclass, field


@dataclass(slots=True)
class ProductProfile:
    product: object

    category: str = "misc"

    product_type: str = "unknown"

    collection: str | None = None

    deity: str |None = None

    material: str = "unknown"

    styles: set[str] = field(default_factory=set)

    usages: set[str] = field(default_factory=set)

    rooms: set[str] = field(default_factory=set)

    occasions: set[str] = field(default_factory=set)

    priority: int = 10

    # populated by matcher
    score: int = 0

    matched_tags: set[str] = field(default_factory=set)

    compatible_with: list = field(default_factory=list)

