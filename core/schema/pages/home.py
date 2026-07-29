from core.schema.builders.webpage import webpage_schema
from core.schema.builders.breadcrumb import breadcrumb_schema
from core.schema.builders.itemlist import itemlist_schema
from core.schema.builders.store import onlinestore_schema


def home_schema(request, context):
    schemas = []

    # Breadcrumb
    schemas.extend(
        breadcrumb_schema(
            request,
            [("Home", "/")]
        )
    )

    schemas.extend(
        onlinestore_schema()
    )

    schemas.extend(
        webpage_schema(
            request,
            context,
            "WebPage",
            main_entity=(
                {"@id": "https://vedabrass.com/#organization"}
            )
        )
    )

    # Trending Products
    trending = context.get("trending_products")
    if trending:
        schemas.extend(
            itemlist_schema(
                request,
                trending,
                name="Trending Products",
            )
        )

    # New Arrivals
    new_products = context.get("new_products")
    if new_products:
        schemas.extend(
            itemlist_schema(
                request,
                new_products,
                name="New Arrivals",
            )
        )

    # Stone Idols
    stone_products = context.get("stone_products")
    if stone_products:
        schemas.extend(
            itemlist_schema(
                request,
                stone_products,
                name="Stone Idols",
            )
        )

    # Festival Collections
    gift_collections = context.get("gift_collections")
    if gift_collections:
        schemas.extend(
            itemlist_schema(
                request,
                gift_collections,
                item_type="Collection",
                name="Festival Gifts",
            )
        )

    return schemas