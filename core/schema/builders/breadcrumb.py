from core.schema.helpers import absolute_url

def breadcrumb_schema(request, items):
    """
    Generate BreadcrumbList schema.

    Parameters:
    items = [
        ("Home", "/"),
        ("Categories", "/categories"),
        ("Brass Idols", "/categories/brass-idols"),
        ("Ganesha Idol", "/product-details/brass-ganesha-idol"),
    ]

    Returns:
    [{
        "@context": "...",
        "@type": "BreadcrumbList",
        ...
    }]
    """

    if not items:
        return []

    breadcrumb_items = []

    for index, (name, url) in enumerate(items, start=1):
        breadcrumb_items.append({
            "@type": "ListItem",
            "position": index,
            "name": name,
            "item": absolute_url(
                request,
                url
            )
        })

    return [{
        "@type": "BreadcrumbList",
        "@id":"https://vedabrass.com/#breadcrumb",
        "itemListElement": breadcrumb_items
    }]