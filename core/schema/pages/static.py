from core.schema.builders.webpage import webpage_schema
from core.schema.builders.breadcrumb import breadcrumb_schema


def static_page_schema(request, context):
    schemas = []

    page_type = {
        "about": "AboutPage",
        "categories": "Categories",
        "subcategories": "Subcategories",
        "collections": "Collections",
        "search": "SearchProducts",
        "products": "Products",
        "contact": "ContactPage",
        "privacy": "WebPage",
        "terms": "WebPage",
    }.get(context["page_type"], "WebPage")

    schemas.extend(
        webpage_schema(
            request,
            context,
            page_type,
            main_entity=(
                {"@id": "https://vedabrass.com/#organization"}
            )
        )
    )

    if context.get("breadcrumbs"):
        schemas.extend(
            breadcrumb_schema(
                request,
                context["breadcrumbs"]
            )
        )

    return schemas