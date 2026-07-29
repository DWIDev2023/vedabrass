from django.urls import reverse


class LinkBuilder:

    @staticmethod
    def build(products):

        links = {}
        categories = {}
        collections = {}

        for product in products:

            if product.category:

                categories[
                    product.category.slug
                ] = product.category

            if product.collection:

                collections[
                    product.collection.slug
                ] = product.collection

        result = []

        for category in categories.values():

            result.append({
                "label": f"View All {category.name}",
                "url": reverse(
                    "ProductsByCategory",
                    kwargs={
                        "slug": category.slug
                    }
                )
            })

        for collection in collections.values():

            result.append({
                "label": f"View All {collection.name}",
                "url": reverse(
                    "ProductsByCollection",
                    kwargs={
                        "slug": collection.slug
                    }
                )
            })

        return result[:6]