import re
from .dictionaries import (
    DEITIES,
    PRODUCT_TYPES,
    COLLECTION_TYPES
)


class EntityMatcher:

    @staticmethod
    def normalize(text):
        return (
            str(text or "")
            .lower()
            .replace("&", " and ")
            .replace("-", " ")
            .replace("_", " ")
            .replace("/", " ")
            .strip()
        )

    @staticmethod
    def extract_budget(message):

        message = (
            EntityMatcher.normalize(message)
            .replace("₹", "")
            .replace(",", "")
        )

        numbers = re.findall(r"\d+", message)

        if "under" in message or "below" in message:
            if numbers:
                return 0, int(numbers[0])

        if "above" in message or "over" in message:
            if numbers:
                return int(numbers[0]), None

        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])

        return None, None

    @staticmethod
    def find_matches(message, dictionary):

        matches = []

        for canonical, aliases in dictionary.items():

            best_alias_length = 0

            for alias in aliases:

                alias = EntityMatcher.normalize(alias)

                if alias in message:

                    best_alias_length = max(
                        best_alias_length,
                        len(alias)
                    )

            if best_alias_length:
                matches.append(
                    (
                        canonical,
                        best_alias_length
                    )
                )

        matches.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return [m[0] for m in matches]

    @staticmethod
    def extract(message):

        message = EntityMatcher.normalize(message)

        min_budget, max_budget = (
            EntityMatcher.extract_budget(message)
        )

        deity_matches = EntityMatcher.find_matches(
            message,
            DEITIES
        )

        product_matches = EntityMatcher.find_matches(
            message,
            PRODUCT_TYPES
        )

        collection_matches = EntityMatcher.find_matches(
            message,
            COLLECTION_TYPES
        )

        deity = deity_matches[0] if deity_matches else None

        return {
            "deity": deity,

            "deity_matches": deity_matches,

            "product_type":
                product_matches[0]
                if product_matches
                else None,

            "product_matches":
                product_matches,

            "collection_type":
                collection_matches[0]
                if collection_matches
                else None,

            "collection_matches":
                collection_matches,

            "budget_min": min_budget,
            "budget_max": max_budget,

            "query": message
        }