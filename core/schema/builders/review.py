from django.utils.timezone import localtime

def reviews_schema(product):
    reviews = (
        product.reviews
        .filter(is_approved=True)
        .select_related("customer")
    )

    if not reviews.exists():
        return []

    return [{
        "@type": "Review",
        "@id":"https://vedabrass.com/#review",
        "author": {
            "@type": "Person",
            "name": review.customer.name if review.customer else "Verified Buyer"
        },
        "reviewRating": {
            "@type": "Rating",
            "ratingValue": review.rating,
            "bestRating": 5
        },
        "headline": review.title,
        "reviewBody": review.comment,
        "datePublished": localtime(review.created_at).date().isoformat()
    } for review in reviews]