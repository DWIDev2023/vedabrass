from django import template
from django.utils.safestring import mark_safe
import json
from core.schema.generators import generate_schema

register = template.Library()


@register.simple_tag(takes_context=True)
def render_schema(context):
    data = context.flatten()

    schemas = generate_schema(
        data["request"],
        data,
    )

    graph = {
        "@context": "https://schema.org",
        "@graph": schemas,
    }

    return mark_safe(
        '<script type="application/ld+json">'
        + json.dumps(graph, ensure_ascii=False)
        + "</script>"
    )