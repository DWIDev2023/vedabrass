from core.bundle_engine.rules import (
    PRODUCT_FAMILY,
    ROLE_RULES,
    EXCLUDED_COMBINATIONS,
    COMPATIBILITY_SCORE,
    BUNDLE_TEMPLATES,
    MATERIALS,
    COMPATIBILITY_SCORE,
    MIN_COMPATIBILITY_SCORE,
)


class ProductMatcher:
    def match(
        self,
        profile,
        profiles,
    ):
        """
        Returns compatible products sorted by score.

        [
            (profile, score),
            ...
        ]
        """
        matches = []

        for candidate in profiles:
            if candidate.product.pk == profile.product.pk:
                continue

            score = self.score(
                profile,
                candidate,
            )

            if score < MIN_COMPATIBILITY_SCORE:
                continue

            matches.append(
                (
                    candidate,
                    score,
                )
            )

        matches.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        profile.compatible_with = [
            p
            for p, _ in matches
        ]

        return matches

    # ---------------------------------------------------------

    def score(
        self,
        left,
        right,
    ):
        if self._excluded(
            left,
            right,
        ):
            return 0

        if not self._same_family(
            left,
            right,
        ):
            return 0

        score = 0

        score += self._role_score(
            left,
            right,
        )

        score += self._compatibility_score(
            left,
            right,
        )

        score += self._material_score(
            left,
            right,
        )

        score += self._usage_score(
            left,
            right,
        )

        score += self._room_score(
            left,
            right,
        )

        score += self._occasion_score(
            left,
            right,
        )

        score += self._style_score(
            left,
            right,
        )

        score += self._deity_score(
            left,
            right,
        )

        score += self._template_score(
            left,
            right,
        )

        score += self._priority_bonus(
            left,
            right,
        )

        return score

    # ---------------------------------------------------------

    def _excluded(
        self,
        left,
        right,
    ):
        pair = tuple(
            sorted(
                (
                    left.product_type,
                    right.product_type,
                )
            )
        )

        return pair in EXCLUDED_COMBINATIONS

    # ---------------------------------------------------------

    def _same_family(
        self,
        left,
        right,
    ):
        return (
            PRODUCT_FAMILY.get(
                left.product_type
            )
            ==
            PRODUCT_FAMILY.get(
                right.product_type
            )
        )

    # ---------------------------------------------------------

    def _role_score(
        self,
        left,
        right,
    ):
        rules = ROLE_RULES.get(
            left.product_type,
            {},
        )

        if right.product_type in rules.get(
            "preferred",
            [],
        ):
            return 35

        if right.product_type in rules.get(
            "optional",
            [],
        ):
            return 15

        return 0

    # ---------------------------------------------------------

    def _compatibility_score(
        self,
        left,
        right,
    ):
        return COMPATIBILITY_SCORE.get(
            (
                left.product_type,
                right.product_type,
            ),
            COMPATIBILITY_SCORE.get(
                (
                    right.product_type,
                    left.product_type,
                ),
                0,
            ),
        )

    # ---------------------------------------------------------

    def _material_score(
        self,
        left,
        right,
    ):
        if left.material == right.material:
            return 20

        compatible = MATERIALS.get(
            left.material,
            [],
        )

        if right.material in compatible:
            return 10

        return 0

    # ---------------------------------------------------------

    def _usage_score(
        self,
        left,
        right,
    ):
        return (
            len(
                left.usages
                &
                right.usages
            )
            * 10
        )

    # ---------------------------------------------------------

    def _room_score(
        self,
        left,
        right,
    ):
        return (
            len(
                left.rooms
                &
                right.rooms
            )
            * 5
        )

    # ---------------------------------------------------------

    def _occasion_score(
        self,
        left,
        right,
    ):
        return (
            len(
                left.occasions
                &
                right.occasions
            )
            * 5
        )

    # ---------------------------------------------------------

    def _style_score(
        self,
        left,
        right,
    ):
        return (
            len(
                left.styles
                &
                right.styles
            )
            * 5
        )

    # ---------------------------------------------------------

    def _deity_score(
        self,
        left,
        right,
    ):
        if (
            left.deity
            and
            right.deity
            and
            left.deity == right.deity
        ):
            return 20

        return 0

    # ---------------------------------------------------------

    def _template_score(
        self,
        left,
        right,
    ):
        templates = BUNDLE_TEMPLATES.get(
            left.product_type,
            [],
        )

        for template in templates:

            if (
                left.product_type in template
                and
                right.product_type in template
            ):
                return 20

        return 0

    # ---------------------------------------------------------

    def _priority_bonus(
        self,
        left,
        right,
    ):
        return min(
            left.priority,
            right.priority,
        ) // 10
    
