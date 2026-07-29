from ..helpers import absolute_url


def video_schema(request, obj=None):
    """
    Generates VideoObject schema.
    """

    if not obj:
        return []

    if not getattr(obj, "video", None):
        return []

    return [{
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": getattr(obj, "title", ""),
        "description": getattr(obj, "description", ""),
        "thumbnailUrl": [],
        "uploadDate": obj.created_at.isoformat() if hasattr(obj, "created_at") else "",
        "contentUrl": absolute_url(request, obj.video.url),
        "embedUrl": absolute_url(request, obj.video.url),
    }]