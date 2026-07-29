from core.bundle_engine.rules import (
    DESCRIPTION_INTROS,
    DESCRIPTION_CLOSINGS,
    PRODUCT_PRIORITY,
)


class BundleDescriptionEngine:
    def generate(
        self,
        bundle,
    ):
        bundle.short_description = self.short_description(
            bundle,
        )

        bundle.description = self.description(
            bundle,
        )

    # ---------------------------------------------------------

    def hero(
        self,
        bundle,
    ):
        return max(
            bundle.products,
            key=lambda p: PRODUCT_PRIORITY.get(
                p.product_type,
                0,
            ),
        )

    # ---------------------------------------------------------

    def short_description(
        self,
        bundle,
    ):
        hero = self.hero(bundle)

        parts = []

        if hero.material and hero.material != "unknown":
            parts.append(hero.material.title())

        if hero.deity:
            parts.append(
                hero.deity.replace(
                    "_",
                    " ",
                ).title()
            )

        elif hero.collection:
            parts.append(hero.collection)

        else:
            parts.append(
                hero.product_type.replace(
                    "_",
                    " ",
                ).title()
            )

        parts.append(bundle.bundle_type.title())
        parts.append("Bundle")

        text = " ".join(parts)

        usage = self.join(
            hero.usages,
            limit=2,
        )

        if usage:
            text += f" curated for {usage}."

        return text

    # ---------------------------------------------------------

    def description(
        self,
        bundle,
    ):
        return "\n\n".join(
            filter(
                None,
                [
                    self.introduction(bundle),
                    self.includes(bundle),
                    self.material(bundle),
                    self.applications(bundle),
                    self.rooms(bundle),
                    self.occasions(bundle),
                    self.closing(bundle),
                ],
            )
        )

    # ---------------------------------------------------------

    def introduction(
        self,
        bundle,
    ):
        return DESCRIPTION_INTROS.get(
            bundle.bundle_type,
            "A thoughtfully curated collection of complementary products.",
        )

    # ---------------------------------------------------------

    def includes(
        self,
        bundle,
    ):
        lines = [
            "This bundle includes:",
        ]

        for profile in bundle.products:
            lines.append(
                f"• {profile.product.name}"
            )

        return "\n".join(lines)

    # ---------------------------------------------------------

    def material(
        self,
        bundle,
    ):
        hero = self.hero(bundle)

        if (
            not hero.material
            or hero.material == "unknown"
        ):
            return ""

        return (
            "Material\n"
            f"• {hero.material.title()}"
        )

    # ---------------------------------------------------------

    def applications(
        self,
        bundle,
    ):
        hero = self.hero(bundle)

        if not hero.usages:
            return ""

        lines = ["Ideal for:"]

        for item in sorted(hero.usages):
            lines.append(
                f"• {item.replace('_', ' ').title()}"
            )

        return "\n".join(lines)

    # ---------------------------------------------------------

    def rooms(
        self,
        bundle,
    ):
        hero = self.hero(bundle)

        if not hero.rooms:
            return ""

        lines = ["Recommended for:"]

        for room in sorted(hero.rooms):
            lines.append(
                f"• {room.replace('_', ' ').title()}"
            )

        return "\n".join(lines)

    # ---------------------------------------------------------

    def occasions(
        self,
        bundle,
    ):
        hero = self.hero(bundle)

        if not hero.occasions:
            return ""

        lines = ["Suitable for:"]

        for occasion in sorted(hero.occasions):
            lines.append(
                f"• {occasion.replace('_', ' ').title()}"
            )

        return "\n".join(lines)

    # ---------------------------------------------------------

    def closing(
        self,
        bundle,
    ):
        return DESCRIPTION_CLOSINGS.get(
            bundle.bundle_type,
            "",
        )

    # ---------------------------------------------------------

    def join(
        self,
        values,
        limit=None,
    ):
        if not values:
            return ""

        items = sorted(values)

        if limit:
            items = items[:limit]

        items = [
            item.replace(
                "_",
                " ",
            )
            for item in items
        ]

        if len(items) == 1:
            return items[0]

        return (
            ", ".join(items[:-1])
            + " and "
            + items[-1]
        )