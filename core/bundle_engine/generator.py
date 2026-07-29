from core.bundle_engine.bundle import BundleCandidate
from core.bundle_engine.matcher import ProductMatcher

from core.bundle_engine.rules import (
    BUNDLE_TEMPLATES,
    PRODUCT_FAMILY,
    MAX_PRODUCTS,
    MIN_PRODUCTS,
)


class BundleGenerator:

    def __init__(self):

        self.matcher = ProductMatcher()

    # -----------------------------------------------------

    def generate(
        self,
        profile,
        profiles,
    ):

        bundles = []

        matches = self.matcher.match(
            profile,
            profiles,
        )

        for candidate, score in matches:

            bundle = self._build_pair(
                profile,
                candidate,
                score,
            )

            if bundle:
                bundles.append(bundle)

            if MAX_PRODUCTS >= 3:

                bundle = self._build_triple(
                    profile,
                    candidate,
                    matches,
                )

                if bundle:
                    bundles.append(bundle)

        return bundles

    # -----------------------------------------------------

    def _build_pair(
        self,
        hero,
        accessory,
        score,
    ):

        if not self._valid_template(
            hero,
            accessory,
        ):
            return None

        return BundleCandidate(
            products=[
                hero,
                accessory,
            ],
            bundle_type=self._bundle_type(hero),
            priority=max(
                hero.priority,
                accessory.priority,
            ),
            score=score,
        )

    # -----------------------------------------------------

    def _build_triple(
        self,
        hero,
        accessory,
        matches,
    ):

        for third, third_score in matches:

            if third.product.pk in (
                hero.product.pk,
                accessory.product.pk,
            ):
                continue

            if not self._valid_template(
                hero,
                accessory,
                third,
            ):
                continue

            score = (
                self.matcher.score(
                    hero,
                    accessory,
                )
                +
                self.matcher.score(
                    hero,
                    third,
                )
                +
                self.matcher.score(
                    accessory,
                    third,
                )
            )

            return BundleCandidate(
                products=[
                    hero,
                    accessory,
                    third,
                ],
                bundle_type=self._bundle_type(hero),
                priority=max(
                    hero.priority,
                    accessory.priority,
                    third.priority,
                ),
                score=score,
            )

        return None

    # -----------------------------------------------------

    def _bundle_type(
        self,
        profile,
    ):

        return PRODUCT_FAMILY.get(
            profile.product_type,
            "misc",
        )

    # -----------------------------------------------------

    def _valid_template(
        self,
        *profiles,
    ):

        product_types = {
            profile.product_type
            for profile in profiles
        }

        templates = BUNDLE_TEMPLATES.get(
            profiles[0].product_type,
            [],
        )

        for template in templates:

            if product_types.issubset(
                set(template)
            ):
                return True

        return False
    
