from ..helpers import (
    absolute_url,
    clean_text,
)


def category_schema(request, category):
    """
    Generates CollectionPage schema for Category pages.

    Used on:
    - /categories/<slug>
    - /category-products/<slug>
    - /subcategory-products/<slug>
    """

    description = (
        getattr(category, "short_description", None)
        or getattr(category, "description", "")
        or category.name
    )

    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "@id": absolute_url(
            request,
            category.get_absolute_url()
        ) + "#category",
        "name": category.name,
        "url": absolute_url(
            request,
            category.get_absolute_url()
        ),
        "description": clean_text(description)
    }

    if getattr(category, "image", None):
        schema["primaryImageOfPage"] = absolute_url(
            request,
            category.image.url
        )

    return schema