from core.bundle_engine.profile import ProductProfile
from core.bundle_engine.rules import (
    CATEGORY_MAPPING,
    COLLECTION_DEITY_MAPPING,
    PRODUCT_TYPES,
    MATERIALS,
    STYLE_KEYWORDS,
    ROOM_MAPPING,
    USAGE_MAPPING,
    OCCASION_MAPPING,
    PRODUCT_PRIORITY,
)


DEFAULT_CATEGORY = "misc"
DEFAULT_PRODUCT_TYPE = "unknown"
DEFAULT_MATERIAL = "unknown"
DEFAULT_PRIORITY = 10

class ProductClassifier:
    def classify(self, product):
        product_type = self.classify_product_type(product)

        return ProductProfile(
            product=product,
            category=self.classify_category(product),
            product_type=product_type,
            deity=self.classify_deity(product),
            material=self.classify_material(product),
            collection=self.classify_collection(product),
            styles=self.classify_styles(product),
            rooms=self.classify_rooms(product_type),
            usages=self.classify_usages(product_type),
            occasions=self.classify_occasions(product_type),
            priority=self.classify_priority(product_type),
        )

    # ---------------------------------------------------------

    def searchable_text(self, product):
        parts = [
            getattr(product, "name", ""),
            getattr(product, "short_description", ""),
            getattr(product, "description", ""),
        ]

        if getattr(product, "category", None):
            parts.append(product.category.name)

        if getattr(product, "collection", None):
            parts.append(product.collection.name)

        return " ".join(filter(None, parts)).lower()

    # ---------------------------------------------------------

    def classify_category(self, product):
        if not getattr(product, "category", None):
            return DEFAULT_CATEGORY

        return CATEGORY_MAPPING.get(
            product.category.name.strip(),
            DEFAULT_CATEGORY,
        )

    # ---------------------------------------------------------

    def classify_collection(self, product):
        if not getattr(product, "collection", None):
            return None

        return product.collection.name

    # ---------------------------------------------------------

    def classify_deity(self, product):
        if not getattr(product, "collection", None):
            return None

        return COLLECTION_DEITY_MAPPING.get(
            product.collection.name
        )

    # ---------------------------------------------------------

    def classify_product_type(self, product):
        text = self.searchable_text(product)

        for product_type, keywords in PRODUCT_TYPES.items():

            if any(keyword in text for keyword in keywords):
                return product_type

        return DEFAULT_PRODUCT_TYPE

    # ---------------------------------------------------------

    def classify_material(self, product):
        text = self.searchable_text(product)

        for material, keywords in MATERIALS.items():

            if any(keyword in text for keyword in keywords):
                return material

        return DEFAULT_MATERIAL

    # ---------------------------------------------------------

    def classify_styles(self, product):
        text = self.searchable_text(product)

        styles = set()

        for style, keywords in STYLE_KEYWORDS.items():

            if any(keyword in text for keyword in keywords):
                styles.add(style)

        return styles

    # ---------------------------------------------------------

    def classify_rooms(self, product_type):
        return set(
            ROOM_MAPPING.get(
                product_type,
                [],
            )
        )

    # ---------------------------------------------------------

    def classify_usages(self, product_type):
        return set(
            USAGE_MAPPING.get(
                product_type,
                [],
            )
        )

    # ---------------------------------------------------------

    def classify_occasions(self, product_type):
        return set(
            OCCASION_MAPPING.get(
                product_type,
                [],
            )
        )

    # ---------------------------------------------------------

    def classify_priority(self, product_type):
        return PRODUCT_PRIORITY.get(
            product_type,
            DEFAULT_PRIORITY,
        )
    
