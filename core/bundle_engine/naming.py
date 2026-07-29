from random import choice
from django.utils.text import slugify
from core.bundle_engine.rules import (
    BUNDLE_ADJECTIVES,
    BUNDLE_ENDINGS,
    PRODUCT_PRIORITY,
)


class BundleNamingEngine:

    def generate(
        self,
        bundle,
        existing_slugs,
    ):

        hero = self.hero(bundle)

        bundle.name = self.build_name(
            hero,
            bundle,
        )

        bundle.slug = self.build_slug(
            bundle.name,
            existing_slugs,
        )

    # ---------------------------------------------------------

    def build_name(
        self,
        hero,
        bundle,
    ):

        parts = []

        adjective = self.adjective(
            hero,
            bundle,
        )

        if adjective:
            parts.append(adjective)

        if (
            getattr(hero, "material", None)
            and hero.material != "unknown"
        ):
            parts.append(
                hero.material.replace(
                    "_",
                    " ",
                ).title()
            )

        if getattr(hero, "festival", None):

            parts.append(
                hero.festival.replace(
                    "_",
                    " ",
                ).title()
            )

        elif getattr(hero, "deity", None):

            parts.append(
                hero.deity.replace(
                    "_",
                    " ",
                ).title()
            )

        elif getattr(hero, "collection", None):

            parts.append(
                hero.collection
            )

        elif (
            getattr(hero, "category", None)
            and hero.category != "misc"
        ):

            parts.append(
                hero.category.replace(
                    "_",
                    " ",
                ).title()
            )

        else:

            parts.append(
                hero.product_type.replace(
                    "_",
                    " ",
                ).title()
            )

        parts.append(
            self.ending(bundle)
        )

        return " ".join(parts)

    # ---------------------------------------------------------

    def hero(
        self,
        bundle,
    ):

        return max(
            bundle.products,
            key=lambda profile: PRODUCT_PRIORITY.get(
                profile.product_type,
                profile.priority,
            ),
        )

    # ---------------------------------------------------------

    def adjective(
        self,
        hero,
        bundle,
    ):

        styles = getattr(
            hero,
            "styles",
            set(),
        )

        style_priority = [

            "premium",

            "antique",

            "traditional",

            "modern",

            "decorative",

            "handcrafted",

        ]

        for style in style_priority:

            adjectives = BUNDLE_ADJECTIVES.get(
                style,
            )

            if (
                style in styles
                and adjectives
            ):
                return choice(
                    adjectives
                )

        adjectives = BUNDLE_ADJECTIVES.get(
            bundle.bundle_type,
        )

        if adjectives:
            return choice(
                adjectives
            )

        return ""

    # ---------------------------------------------------------

    def ending(
        self,
        bundle,
    ):

        endings = BUNDLE_ENDINGS.get(
            bundle.bundle_type,
            BUNDLE_ENDINGS.get(
                "default",
                ["Bundle"],
            ),
        )

        return choice(
            endings
        )

    # ---------------------------------------------------------

    def build_slug(
        self,
        name,
        existing_slugs,
    ):

        base = slugify(name)

        slug = base

        counter = 2

        while slug in existing_slugs:

            slug = f"{base}-{counter}"

            counter += 1

        return slug