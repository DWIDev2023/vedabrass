"""
Reads meta_title and meta_description directly from the Excel sheet
at runtime and maps them to Product rows by slug.
"""
import openpyxl
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Product


class Command(BaseCommand):
    help = "Seed Product.meta_title and Product.meta_description from an Excel sheet keyed by slug."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to the Excel file (e.g. /path/to/metas.xlsx).",
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
        filepath  = options["file"]
        apply     = options["apply"]
        only_slug = options["slug"]

        # ── 1. Load Excel ────────────────────────────────────────────────────
        try:
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {filepath}"))
            return

        ws = wb.active

        # Expected columns: #, Page, URL, Slug, Meta Title, Meta Description
        meta_map = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            slug = (row[3] or "").strip().rstrip("/")
            if not slug:
                continue
            if only_slug and slug != only_slug:
                continue
            meta_map[slug] = {
                "meta_title":       (row[4] or "").strip(),
                "meta_description": (row[5] or "").strip(),
            }

        wb.close()
        self.stdout.write(f"Loaded {len(meta_map)} slug(s) from {filepath}\n")

        if not meta_map:
            self.stdout.write(self.style.WARNING("No matching rows found. Check --slug or the file."))
            return

        # ── 2. Seed Product.meta_title / meta_description ────────────────────
        updated = missing = 0

        for slug, metas in meta_map.items():
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"  Not found in DB: {slug}"))
                missing += 1
                continue

            if apply:
                product.meta_title       = metas["meta_title"]
                product.meta_description = metas["meta_description"]
                product.save(update_fields=["meta_title", "meta_description"])

            self.stdout.write(
                f"  {'✓' if apply else '[DRY]'} {slug}\n"
                f"       title : {metas['meta_title'][:80]}\n"
                f"       desc  : {metas['meta_description'][:80]}\n"
            )
            updated += 1

        verb = "Updated" if apply else "Would update"
        self.stdout.write(self.style.SUCCESS(
            f"\n{verb} {updated} product(s). Not found in DB: {missing}."
        ))
        if not apply:
            self.stdout.write(self.style.WARNING("  ↳ Re-run with --apply to commit."))

# Run Command: python manage.py seed_product_metas --file metas.xlsx --apply