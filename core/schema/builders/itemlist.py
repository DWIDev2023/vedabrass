from core.schema.helpers import (
    absolute_url,
)


def itemlist_schema(
    request,
    items,
    item_type="Product",
    name=None,
):
    """
    Generic ItemList Schema.

    Supports:
        Products
        Blogs
        Collections
        Categories
        Bundles
    """

    if not items:
        return []

    list_items = []

    for position, item in enumerate(items, start=1):
        data = {
            "@type": "ListItem",
            "position": position,
        }

        if item_type == "Product":

            data["item"] = {
                "@type": "Product",
                "name": item.name,
                "url": absolute_url(
                    request,
                    item.get_absolute_url()
                )
            }

        elif item_type == "Blog":

            data["item"] = {
                "@type": "BlogPosting",
                "headline": item.title,
                "url": absolute_url(
                    request,
                    item.get_absolute_url()
                )
            }

        elif item_type == "Collection":

            data["item"] = {
                "@type": "CollectionPage",
                "name": item.name,
                "url": absolute_url(
                    request,
                    item.get_absolute_url()
                )
            }

        elif item_type == "Category":

            data["item"] = {
                "@type": "CollectionPage",
                "name": item.name,
                "url": absolute_url(
                    request,
                    item.get_absolute_url()
                )
            }

        elif item_type == "Bundle":

            data["item"] = {
                "@type": "Product",
                "name": item.name,
                "url": absolute_url(
                    request,
                    item.get_absolute_url()
                )
            }

        list_items.append(data)

    schema = {
        "@type": "ItemList",
        "numberOfItems": len(list_items),
        "itemListElement": list_items,
    }

    if name:
        schema["name"] = name

    return [schema]