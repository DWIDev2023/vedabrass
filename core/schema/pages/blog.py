from ..helpers import (
    absolute_url,
    clean_text,
    get_blog_image,
    get_organization,
)


def blog_schema(request, blogs):
    """
    Blog Schema
    Used on:
        /blogs
        /blog-category/<slug>
    """

    if not blogs:
        return []

    return [{
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "VedaBrass Blogs",
        "url": absolute_url(
            request,
            request.path
        ),
        "publisher": get_organization(),
        "blogPost": [
            {
                "@type": "BlogPosting",
                "headline": blog.title,
                "url": absolute_url(
                    request,
                    blog.get_absolute_url()
                )
            }
            for blog in blogs
        ]
    }]


def blog_post_schema(request, blog):
    """
    BlogPosting Schema
    Used on:
        /blog/<slug>
    """

    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "@id": absolute_url(
            request,
            blog.get_absolute_url()
        ) + "#blog",

        "headline": blog.title,

        "description": clean_text(
            blog.meta_description
            or blog.short_description
            or blog.description
        ),

        "url": absolute_url(
            request,
            blog.get_absolute_url()
        ),

        "publisher": get_organization(),

        "author": {
            "@type": "Organization",
            "name": "VedaBrass"
        },

        "datePublished": blog.created_at.date().isoformat(),

        "dateModified": blog.updated_at.date().isoformat(),
    }

    image = get_blog_image(
        request,
        blog
    )

    if image:
        schema["image"] = image

    if getattr(blog, "category", None):
        schema["articleSection"] = blog.category.name

    return schema