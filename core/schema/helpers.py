from django.conf import settings
from django.templatetags.static import static


def absolute_url(request, path):
    """
    Converts a relative URL into an absolute URL.
    """

    if not path:
        return ""

    if path.startswith("http://") or path.startswith("https://"):
        return path

    return request.build_absolute_uri(path)


def site_url(request):
    """
    Returns the site's base URL.
    """

    return request.build_absolute_uri("/").rstrip("/")


def get_product_image(request, product):
    """
    Returns the primary product image.
    """

    image = (
        product.images.filter(is_primary=True).first()
        or product.images.first()
    )

    if image and image.image:
        return absolute_url(request, image.image.url)

    return absolute_url(
        request,
        static("front/images/no-image.webp")
    )


def get_collection_image(request, collection):
    """
    Returns collection image.
    """

    if getattr(collection, "image", None):
        return absolute_url(request, collection.image.url)

    return ""


def get_blog_image(request, blog):
    """
    Returns blog featured image.
    """

    if getattr(blog, "image", None):
        return absolute_url(request, blog.image.url)

    return ""


def get_news_image(request, news):
    """
    Returns NewsEvent thumbnail.
    """

    if getattr(news, "thumbnail", None):
        return absolute_url(request, news.thumbnail.url)

    return ""


def get_brand():
    """
    Common Brand Schema.
    """

    return {
        "@type": "Brand",
        "name": "VedaBrass"
    }


def get_organization():
    """
    Common Organization Schema.
    """

    return {
        "@type": "Organization",
        "name": "VedaBrass",
        "url": settings.SITE_URL,
        "logo": f"{settings.SITE_URL}/static/front/images/logo.png"
    }


def get_availability(product):
    """
    Returns Schema.org availability.
    """

    if hasattr(product, "stock"):
        return (
            "https://schema.org/InStock"
            if product.stock > 0
            else "https://schema.org/OutOfStock"
        )

    # Default if inventory isn't managed
    return "https://schema.org/InStock"


def get_price(product):
    """
    Returns selling price.
    """

    if getattr(product, "discount_price", None):
        return float(product.discount_price)

    return float(product.price)


def get_original_price(product):
    """
    Returns original price.
    """

    return float(product.price)


def get_discount(product):
    """
    Returns discount percentage.
    """

    if (
        product.discount_price
        and product.discount_price < product.price
    ):
        return round(
            (
                (
                    product.price
                    - product.discount_price
                )
                / product.price
            )
            * 100
        )

    return 0


def clean_text(text):
    """
    Cleans HTML and unnecessary spaces.
    """

    if not text:
        return ""

    from django.utils.html import strip_tags

    return " ".join(
        strip_tags(text).split()
    )


def get_currency():
    return "INR"


def get_condition():
    return "https://schema.org/NewCondition"