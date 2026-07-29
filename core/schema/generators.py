from .builders.organization import organization_schema
from .builders.faq import faq_schema
from .pages.static import static_page_schema
from .pages.home import home_schema
from .pages.product import product_schema
from .pages.category import category_schema
from .pages.collection import collection_schema
from .pages.blog import blog_schema
from .pages.video import video_schema
from .builders.website import website_schema


def generate_schema(request, context):
    schemas = []

    schemas.extend(
        organization_schema()
    )

    schemas.extend(
        website_schema()
    )

    page_type = context.get("page_type")

    if page_type == "home":
        schemas.extend(
            home_schema(request, context)
        )

    elif page_type == "about":
        schemas.extend(
            static_page_schema(request, context)
        )

    elif page_type == "contact":
        schemas.extend(
            static_page_schema(request, context)
        )

    elif page_type == "privacy":
        schemas.extend(
            static_page_schema(request, context)
        )

    elif page_type == "terms":
        schemas.extend(
            static_page_schema(request, context)
        )

    elif page_type == "product":
        schemas.extend(
            product_schema(request, context)
        )

    elif page_type == "category":
        schemas.extend(
            category_schema(request, context)
        )

    elif page_type == "collection":
        schemas.extend(
            collection_schema(request, context)
        )

    elif page_type == "blog":
        schemas.extend(
            blog_schema(request, context)
        )

    elif page_type == "video":
        schemas.extend(
            video_schema(request, context)
        )

    schemas.extend(
        faq_schema(request, context)
    )

    return schemas