from django.utils.text import slugify
from core.models import ProductBundle


def signature(products):
    """
    Stable identifier for a bundle.

    Example:
    5-18
    5-18-42
    """
    return "-".join(
        sorted(
            str(profile.product.pk)
            for profile in products
        )
    )


def slug(name, existing_slugs):
    base = slugify(name)

    result = base

    counter = 2

    while result in existing_slugs:
        result = f"{base}-{counter}"
        counter += 1

    existing_slugs.add(result)

    return result


def exists(products):
    """
    Checks whether an identical bundle already exists.
    """
    ids = sorted(
        profile.product.pk
        for profile in products
    )

    count = len(ids)

    for bundle in ProductBundle.objects.prefetch_related("products"):
        bundle_ids = sorted(
            bundle.products.values_list("pk", flat=True)
        )

        if len(bundle_ids) != count:
            continue

        if bundle_ids == ids:
            return True

    return False


def save(bundle, existing_slugs):
    """
    Persist a BundleCandidate as a ProductBundle.

    NOTE: existing_slugs must be passed in and shared across calls in the
    same run — slug() mutates it in place to avoid generating duplicate
    slugs across bundles saved in the same batch.
    """
    if exists(bundle.products):
        return None

    db_bundle = ProductBundle.objects.create(
        name=bundle.name,
        slug=slug(bundle.name, existing_slugs),
        short_description=bundle.short_description,
        description=bundle.description,
        bundle_price=bundle.bundle_price,
        discounted_bundle_price=bundle.discounted_bundle_price,
        bundle_type=bundle.bundle_type,
        priority=bundle.priority,
        is_active=True,
    )

    db_bundle.products.set(
        [profile.product for profile in bundle.products]
    )

    return db_bundle