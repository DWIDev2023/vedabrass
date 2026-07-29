def webpage_schema(request, context, page_type="WebPage", main_entity=None,):
    page = {
        "@type": page_type,
        "@id": request.build_absolute_uri() + "#webpage",
        "url": request.build_absolute_uri(),
        "name": context.get("meta_title"),
        "primaryImageOfPage":{
            "@type":"ImageObject",
            "url":"https://vedabrass.com/static/front/images/banner.jpg"
        },
        "description": context.get("meta_description"),
        "isPartOf": {
            "@id": "https://vedabrass.com/#website"
        },
        "about": {
            "@id": "https://vedabrass.com/#organization"
        }
    }

    if main_entity:
        page["mainEntity"] = main_entity
    
    return [page]