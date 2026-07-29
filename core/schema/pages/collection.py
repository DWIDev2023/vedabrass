from ..helpers import (
    absolute_url,
    clean_text,
    get_collection_image,
)


def collection_schema(request, collection):
    """
    Generates CollectionPage schema.

    Used on:
    /collections/<slug>
    /collection-products/<slug>
    """

    description = (
        getattr(collection, "short_description", None)
        or getattr(collection, "description", "")
        or collection.name
    )

    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "@id": absolute_url(
            request,
            collection.get_absolute_url()
        ) + "#collection",
        "name": collection.name,
        "url": absolute_url(
            request,
            collection.get_absolute_url()
        ),
        "description": clean_text(description)
    }

    image = get_collection_image(
        request,
        collection
    )

    if image:
        schema["primaryImageOfPage"] = image

    return schema