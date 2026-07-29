from django.db.models import Q

from core.models import Product
from .dictionaries import DEITY_EQUIVALENTS


class ProductFilter:

    @staticmethod
    def filter(parsed):

        qs = (
            Product.objects
            .filter(is_active=True)
            .select_related(
                "category",
                "collection"
            )
            .prefetch_related(
                "images",
                "tags"
            )
        )

        deity = parsed["deity"]
        product_type = parsed["product_type"]
        collection_type = parsed["collection_type"]

        # ----------------------------------
        # DEITY FILTER
        # ----------------------------------

        if deity:

            aliases = DEITY_EQUIVALENTS.get(
                deity,
                [deity]
            )

            deity_query = Q()

            for alias in aliases:

                deity_query |= (
                    Q(name__icontains=alias)
                    |
                    Q(collection__name__icontains=alias)
                    |
                    Q(tags__name__icontains=alias)
                )

            qs = qs.filter(
                deity_query
            )

        # ----------------------------------
        # PRODUCT TYPE FILTER
        # ----------------------------------

        if product_type:

            words = product_type.split()

            query = Q()

            for word in words:

                query &= (
                    Q(name__icontains=word)
                    |
                    Q(collection__name__icontains=word)
                    |
                    Q(tags__name__icontains=word)
                )

            qs = qs.filter(query)

        # ----------------------------------
        # COLLECTION TYPE FILTER
        # ----------------------------------

        if collection_type:

            qs = qs.filter(
                Q(collection__name__icontains=collection_type)
                |
                Q(tags__name__icontains=collection_type)
                |
                Q(name__icontains=collection_type)
            )

        # ----------------------------------
        # BUDGET FILTER
        # ----------------------------------

        min_budget = parsed["budget_min"]
        max_budget = parsed["budget_max"]

        if min_budget is not None:

            qs = qs.filter(
                price__gte=min_budget
            )

        if max_budget is not None:

            qs = qs.filter(
                price__lte=max_budget
            )

        return qs.distinct()