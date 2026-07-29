from core.schema.helpers import (
    absolute_url,
    get_availability,
    get_condition,
    get_currency,
    get_price,
)


def offer_schema(request, product):
    """
    Returns Product Offer schema.
    """

    return [{
        "@type": "Offer",
        "@id":"https://vedabrass.com/#offer",
        "url": absolute_url(
            request,
            product.get_absolute_url()
        ),
        "priceCurrency": get_currency(),
        "price": get_price(product),
        "availability": get_availability(product),
        "itemCondition": get_condition(),
    }]