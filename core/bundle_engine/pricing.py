from decimal import Decimal

from core.bundle_engine.rules import (
    PREMIUM_PRICE,
)


class BundlePricingEngine:

    def generate(
        self,
        bundle,
    ):

        price = self.bundle_price(
            bundle,
        )

        discount = self.discount_percentage(
            bundle,
            price,
        )

        discounted_price = self.discounted_price(
            price,
            discount,
        )

        bundle.bundle_price = price

        bundle.discount_percentage = discount

        bundle.discounted_bundle_price = discounted_price

        bundle.savings = (
            price
            - discounted_price
        )

    # ---------------------------------------------------------

    def bundle_price(
        self,
        bundle,
    ):

        return sum(
            getattr(
                profile.product,
                "discount_price",
                0,
            ) or 0
            for profile in bundle.products
        )

    # ---------------------------------------------------------

    def discount_percentage(
        self,
        bundle,
        price,
    ):

        discount = 5

        # Premium bundles

        if price >= PREMIUM_PRICE:
            discount += 3

        # Bigger bundles

        if len(bundle.products) == 3:
            discount += 2

        # Bundle type bonus

        if bundle.bundle_type == "pooja":
            discount += 2

        elif bundle.bundle_type == "decor":
            discount += 1

        return min(
            discount,
            15,
        )

    # ---------------------------------------------------------

    def discounted_price(
        self,
        price,
        discount,
    ):

        final = (
            Decimal(price)
            * (
                Decimal("100")
                - Decimal(discount)
            )
            / Decimal("100")
        )

        return self.round_price(
            final,
        )

    # ---------------------------------------------------------

    def round_price(
        self,
        price,
    ):
        """
        ₹18,432 → ₹18,490
        ₹9,830  → ₹9,990
        ₹4,212  → ₹4,290
        """

        value = int(price)

        return (
            value // 100
        ) * 100 + 90