from core.schema.helpers import (
    absolute_url,
    get_product_image,
    get_brand,
    get_availability,
    get_price,
    get_currency,
    get_condition,
    clean_text,
)


def product_schema(request, product):
    """
    Product Schema
    """

    approved_reviews = product.reviews.filter(
        is_approved=True
    )

    review_count = approved_reviews.count()

    average_rating = 0

    if review_count:
        average_rating = round(
            sum(
                review.rating
                for review in approved_reviews
            ) / review_count,
            1
        )

    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": absolute_url(
            request,
            product.get_absolute_url()
        ) + "#product",
        "name": product.name,
        "description": clean_text(
            product.short_description
            or product.description
        ),
        "sku": product.unique_code,
        "image": [
            get_product_image(
                request,
                product
            )
        ],
        "brand": get_brand(),

        "offers": {
            "@type": "Offer",
            "url": absolute_url(
                request,
                product.get_absolute_url()
            ),
            "priceCurrency": get_currency(),
            "price": get_price(product),
            "availability": get_availability(product),
            "itemCondition": get_condition(),
        },
    }

    if review_count:

        data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": average_rating,
            "reviewCount": review_count,
        }

        reviews = []

        for review in approved_reviews[:10]:

            reviews.append(
                {
                    "@type": "Review",
                    "author": {
                        "@type": "Person",
                        "name": (
                            review.customer.name
                            if review.customer
                            else "Verified Customer"
                        ),
                    },
                    "reviewRating": {
                        "@type": "Rating",
                        "ratingValue": review.rating,
                        "bestRating": "5",
                    },
                    "headline": review.title,
                    "reviewBody": review.comment,
                    "datePublished": review.created_at.date().isoformat(),
                }
            )

        data["review"] = reviews

    return [data]