class ProductSerializer:

    @staticmethod
    def serialize(product):

        image = (
            product.images
            .filter(is_primary=True)
            .first()
        )

        if not image:
            image = product.images.first()

        return {
            "name": product.name,
            "price": str(
                product.discount_price
                or product.price
            ),
            "mrp": str(product.price),
            "slug": product.slug,
            "url": f"/product-details/{product.slug}",
            "image": (
                image.image.url
                if image else None
            )
        }