from difflib import SequenceMatcher


class ProductRanker:

    MIN_SCORE = 80

    @staticmethod
    def similarity(a, b):
        return SequenceMatcher(
            None,
            a.lower(),
            b.lower()
        ).ratio()

    @staticmethod
    def rank(products, entities):

        deity = (entities.get("deity") or "").lower()
        product_type = (entities.get("product_type") or "").lower()
        collection_type = (entities.get("collection_type") or "").lower()

        search_terms = [
            term
            for term in (
                deity,
                product_type,
                collection_type,
            )
            if term
        ]

        scored = []

        for product in products:

            score = 0

            product_name = (product.name or "").lower()

            category_name = (
                product.category.name.lower()
                if product.category
                else ""
            )

            collection_name = (
                product.collection.name.lower()
                if product.collection
                else ""
            )

            searchable = (
                f"{product_name} "
                f"{category_name} "
                f"{collection_name}"
            )

            # ---------------------------------
            # Exact phrase matches
            # ---------------------------------

            for term in search_terms:

                if term in product_name:
                    score += 300

                elif term in collection_name:
                    score += 220

                elif term in category_name:
                    score += 150

            # ---------------------------------
            # Individual keyword matches
            # ---------------------------------

            for term in search_terms:

                for word in term.split():

                    if len(word) < 3:
                        continue

                    if word in searchable:
                        score += 35

            # ---------------------------------
            # Fuzzy similarity
            # ---------------------------------

            if search_terms:

                similarity = max(
                    ProductRanker.similarity(
                        term,
                        product_name,
                    )
                    for term in search_terms
                )

                score += int(similarity * 120)

            # ---------------------------------
            # Reject irrelevant products
            # ---------------------------------

            if score < ProductRanker.MIN_SCORE:
                continue

            price = float(
                product.discount_price
                or product.price
                or 0
            )

            scored.append(
                (
                    score,
                    price,
                    product,
                )
            )

        scored.sort(
            key=lambda x: (
                x[0],
                x[1],
            ),
            reverse=True,
        )

        return [
            product
            for _, _, product in scored
        ]