from core.bundle_engine.rules import (
    MIN_PRODUCTS,
    MAX_PRODUCTS,
    MIN_BUNDLE_SCORE,
    MAX_HERO_PRODUCTS,
    MIN_ACCESSORIES,
    MAX_ACCESSORIES,
    HERO_PRODUCT_TYPES,
    ACCESSORY_PRODUCT_TYPES,
    EXCLUDED_COMBINATIONS,
    PRODUCT_FAMILY,
    ROLE_RULES,
    BUNDLE_TEMPLATES,
)


class BundleValidator:

    def validate(self, bundle):

        return (
            self._validate_product_count(bundle)
            and self._validate_score(bundle)
            and self._validate_roles(bundle)
            and self._validate_family(bundle)
            and self._validate_exclusions(bundle)
            and self._validate_template(bundle)
            and self._validate_role_rules(bundle)
        )

    # ---------------------------------------------------------

    def _validate_product_count(self, bundle):

        count = len(bundle.products)

        return MIN_PRODUCTS <= count <= MAX_PRODUCTS

    # ---------------------------------------------------------

    def _validate_score(self, bundle):

        return bundle.score >= MIN_BUNDLE_SCORE

    # ---------------------------------------------------------

    def _validate_roles(self, bundle):

        hero_count = sum(
            profile.product_type in HERO_PRODUCT_TYPES
            for profile in bundle.products
        )

        accessory_count = sum(
            profile.product_type in ACCESSORY_PRODUCT_TYPES
            for profile in bundle.products
        )

        if hero_count > MAX_HERO_PRODUCTS:
            return False

        if accessory_count < MIN_ACCESSORIES:
            return False

        if accessory_count > MAX_ACCESSORIES:
            return False

        return True

    # ---------------------------------------------------------

    def _validate_family(self, bundle):

        families = {
            PRODUCT_FAMILY.get(profile.product_type)
            for profile in bundle.products
        }

        families.discard(None)

        return len(families) <= 1

    # ---------------------------------------------------------

    def _validate_exclusions(self, bundle):

        product_types = [
            profile.product_type
            for profile in bundle.products
        ]

        for i, left in enumerate(product_types):

            for right in product_types[i + 1:]:

                if (
                    (left, right) in EXCLUDED_COMBINATIONS
                    or
                    (right, left) in EXCLUDED_COMBINATIONS
                ):
                    return False

        return True

    # ---------------------------------------------------------

    def _validate_template(self, bundle):

        hero = max(
            bundle.products,
            key=lambda profile: profile.priority,
        )

        templates = BUNDLE_TEMPLATES.get(
            hero.product_type,
            [],
        )

        bundle_types = {
            profile.product_type
            for profile in bundle.products
        }

        for template in templates:

            if bundle_types == set(template):
                return True

        return False
    
    def _validate_role_rules(self, bundle):
        hero = max(
            bundle.products,
            key=lambda p: p.priority,
        )

        rules = ROLE_RULES.get(
            hero.product_type,
        )

        if not rules:
            return True

        product_types = {
            p.product_type
            for p in bundle.products
        }

        # Forbidden products
        if product_types.intersection(rules.get("forbidden", [])):
            return False

        # At least one preferred product
        preferred = set(rules.get("preferred", []))

        if preferred and not product_types.intersection(preferred):
            return False

        return True