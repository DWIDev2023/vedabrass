from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Product, ProductBundle
from core.bundle_engine.classifier import ProductClassifier
from core.bundle_engine.generator import BundleGenerator
from core.bundle_engine.naming import BundleNamingEngine
from core.bundle_engine.pricing import BundlePricingEngine
from core.bundle_engine.descriptions import BundleDescriptionEngine
from core.bundle_engine.validator import BundleValidator
from core.bundle_engine import utils


class Command(BaseCommand):
    help = "Generate curated product bundles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing bundles before generation.",
        )

        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace bundles having the same slug.",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Generate bundles without saving.",
        )

        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of products processed.",
        )

    def handle(self, *args, **options):
        BATCH_SIZE = 100
        MAX_BUNDLES_PER_PRODUCT = 5

        clear = options["clear"]
        overwrite = options["overwrite"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        if clear:
            self.stdout.write("Removing existing bundles...")
            ProductBundle.objects.all().delete()

        self.stdout.write("Loading products...")

        queryset = (
            Product.objects.filter(
                is_active=True,
                is_deleted=False,
            )
            .select_related(
                "category",
                "collection",
            )
            .prefetch_related(
                "tags",
            )
        )

        if limit:
            queryset = queryset[:limit]

        products = list(queryset)

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(products)} products loaded."
            )
        )

        # --------------------------------------------------
        # Engines
        # --------------------------------------------------

        classifier = ProductClassifier()
        generator = BundleGenerator()
        validator = BundleValidator()
        naming = BundleNamingEngine()
        pricing = BundlePricingEngine()
        descriptions = BundleDescriptionEngine()

        # --------------------------------------------------

        profiles = [
            classifier.classify(product)
            for product in products
        ]

        existing_slugs = set(
            ProductBundle.objects.values_list(
                "slug",
                flat=True,
            )
        )

        generated_signatures = set()

        pending = []

        total = len(profiles)

        generated = 0
        saved = 0
        skipped = 0
        invalid = 0
        duplicates = 0

        self.stdout.write("Generating bundles...\n")

        for index, profile in enumerate(
            profiles,
            start=1,
        ):
            self._progress(
                index,
                total,
            )

            bundles = generator.generate(
                profile,
                profiles,
            )[:MAX_BUNDLES_PER_PRODUCT]

            for bundle in bundles:
                try:
                    if not validator.validate(bundle):
                        invalid += 1
                        continue

                    signature = (
                        bundle.bundle_type,
                        utils.signature(
                            bundle.products
                        ),
                    )

                    if signature in generated_signatures:
                        duplicates += 1
                        continue

                    generated_signatures.add(
                        signature
                    )

                    naming.generate(
                        bundle,
                        existing_slugs,
                    )

                    if overwrite:
                        ProductBundle.objects.filter(
                            slug=bundle.slug
                        ).delete()

                    existing_slugs.add(
                        bundle.slug
                    )

                    pricing.generate(
                        bundle,
                    )

                    descriptions.generate(
                        bundle,
                    )

                    generated += 1

                    if dry_run:
                        continue

                    pending.append(
                        bundle
                    )

                    if len(pending) >= BATCH_SIZE:
                        pending.sort(
                            key=lambda b: (
                                b.priority,
                                len(b.products),
                            ),
                            reverse=True,
                        )

                        self._save_batch(
                            pending
                        )

                        saved += len(
                            pending
                        )

                        pending.clear()

                except Exception as exc:
                    skipped += 1

                    self.stdout.write(
                        self.style.ERROR(
                            f"\nSkipped bundle: {exc}"
                        )
                    )

        if pending and not dry_run:
            pending.sort(
                key=lambda b: (
                    b.priority,
                    len(b.products),
                ),
                reverse=True,
            )

            self._save_batch(
                pending
            )

            saved += len(
                pending
            )

            pending.clear()

        print()

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"Products Loaded : {len(products)}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Bundles Generated : {generated}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Bundles Saved : {saved if not dry_run else generated}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Validation Failed : {invalid}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Duplicates : {duplicates}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Skipped : {skipped}"
            )
        )

    @transaction.atomic
    def _save_batch(
        self,
        bundles,
    ):
        # -------------------------------------------------
        # Bulk create ProductBundle objects
        # -------------------------------------------------
        bundle_objects = [
            ProductBundle(
                name=bundle.name,

                slug=bundle.slug,

                short_description=bundle.short_description,

                description=bundle.description,

                bundle_price=bundle.bundle_price,

                discounted_bundle_price=bundle.discounted_bundle_price,

                bundle_type=bundle.bundle_type,

                priority=bundle.priority,
            )

            for bundle in bundles
        ]

        ProductBundle.objects.bulk_create(
            bundle_objects,
            batch_size=100,
        )

        # -------------------------------------------------
        # Fetch created bundles
        # -------------------------------------------------

        saved_lookup = {
            bundle.slug: bundle

            for bundle in ProductBundle.objects.filter(
                slug__in=[
                    bundle.slug

                    for bundle in bundles
                ]
            )
        }

        # -------------------------------------------------
        # Bulk create M2M relations
        # -------------------------------------------------

        through = ProductBundle.products.through

        relations = []

        for bundle in bundles:
            obj = saved_lookup[bundle.slug]

            for profile in bundle.products:
                relations.append(
                    through(
                        productbundle_id=obj.id,

                        product_id=profile.product.id,
                    )
                )

        through.objects.bulk_create(
            relations,
            batch_size=500,
        )

    def _progress(
        self,
        current,
        total,
    ):
        width = 30

        progress = current / total

        filled = int(
            width * progress
        )

        bar = (
            "█" * filled
            + "-" * (width - filled)
        )

        print(
            f"\r[{bar}] {current}/{total}",
            end="",
            flush=True,
        )


# Run Command:
# python manage.py seed_generate_bundles --dry-run
# python manage.py seed_generate_bundles --clear
# python manage.py seed_generate_bundles --overwrite
# python manage.py seed_generate_bundles --limit=20
# python manage.py seed_generate_bundles --dry-run --limit=20
# python manage.py seed_generate_bundles --help
# python manage.py seed_generate_bundles