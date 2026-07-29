from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import BlogCategory


class Command(BaseCommand):
    help = "Seed Blog Categories"

    def handle(self, *args, **kwargs):
        categories = [
            "Buying Guides",
            "Comparisons",
            "Use Cases",
            "Care & Maintenance",
            "Seasonal",
            "Trends",
            "Brass Knowledge Center",
            "Vastu Guides",
            "Gift Guides",
        ]

        created = 0

        for name in categories:
            _, was_created = BlogCategory.objects.get_or_create(
                slug=slugify(name),
                defaults={
                    "name": name,
                    "is_active": True,
                },
            )

            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{created} blog categories created successfully."
            )
        )

# Run Command: python manage.py seed_blog_categories