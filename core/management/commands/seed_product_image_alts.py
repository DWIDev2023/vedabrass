"""
Reads alt texts directly from the Excel sheet at runtime and maps them
to ProductImage rows by product slug.

Images are ordered: is_primary=True first, then created_at ascending.
Alt texts assigned positionally (image 1 → Alt1, image 2 → Alt2, etc.).

"""
import openpyxl
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Product


class Command(BaseCommand):
    help = "Seed ProductImage.alt_text from an Excel sheet keyed by product slug."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to the Excel file (e.g. /path/to/alts.xlsx).",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Commit changes to DB. Omit for dry-run.",
        )
        parser.add_argument(
            "--slug",
            type=str,
            default=None,
            help="Run for a single product slug only.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        filepath = options["file"]
        apply    = options["apply"]
        only_slug = options["slug"]

        # ── 1. Load Excel ────────────────────────────────────────────────────
        try:
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {filepath}"))
            return

        ws = wb.active
        rows = ws.iter_rows(min_row=2, values_only=True)  # skip header row

        # ── 2. Build slug → [alt1..alt6] map from sheet ──────────────────────
        # Expected columns: #, Page, URL, Slug, Alt1, Alt2, Alt3, Alt4, Alt5, Alt6
        alt_map = {}
        for row in rows:
            slug = (row[3] or "").strip().rstrip("/")
            if not slug:
                continue
            if only_slug and slug != only_slug:
                continue
            alts = [row[4 + i] or "" for i in range(6)]
            alt_map[slug] = alts

        wb.close()
        self.stdout.write(f"Loaded {len(alt_map)} slug(s) from {filepath}")

        if not alt_map:
            self.stdout.write(self.style.WARNING("No matching rows found. Check --slug or the file."))
            return

        # ── 3. Seed ProductImage.alt_text ────────────────────────────────────
        updated = skipped = missing = 0

        for slug, alts in alt_map.items():
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"  Not found in DB: {slug}"))
                missing += 1
                continue

            # is_primary image first, then rest by creation order
            images = list(product.images.all().order_by("-is_primary", "created_at"))

            if not images:
                self.stdout.write(self.style.WARNING(f"  No images: {slug}"))
                skipped += 1
                continue

            for i, img in enumerate(images):
                if i >= len(alts):
                    break
                new_alt = alts[i]
                if apply:
                    img.alt_text = new_alt
                    img.save(update_fields=["alt_text"])
                self.stdout.write(
                    f"  {'✓' if apply else '[DRY]'} {slug} | img {i+1} | {new_alt[:80]}"
                )
                updated += 1

        verb = "Updated" if apply else "Would update"
        self.stdout.write(self.style.SUCCESS(
            f"\n{verb} {updated} image(s). Not found: {missing}. No images: {skipped}."
        ))
        if not apply:
            self.stdout.write(self.style.WARNING("  ↳ Re-run with --apply to commit."))

# Run Command: python manage.py seed_product_image_alts --file /path/to/alts.xlsx --apply