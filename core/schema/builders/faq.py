from core.models import FAQ


def faq_schema(request, context):

    product = context.get("product")

    if product:
        faqs = FAQ.objects.filter(
            is_active=True,
            product=product
        )
    else:
        faqs = context.get("faqs")

        if faqs is None:
            faqs = FAQ.objects.filter(
                is_active=True,
                page=request.path
            )

    if not faqs.exists():
        return []

    return [{
        "@type": "FAQPage",
        "@id": request.build_absolute_uri() + "#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq.question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq.answer,
                }
            }
            for faq in faqs
        ]
    }]