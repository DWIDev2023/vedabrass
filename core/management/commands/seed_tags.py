from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import Tags

class Command(BaseCommand):
    help = "Seed default product tags"

    DEFAULT_TAGS = [
        "Lord Ganesha",
        "Ganapati",
        "Panchamukhi Ganesha",
        "Dancing Ganesha",
        "Lotus Ganesha",
        "Ganesha Diya",
        "Ganesha Wall Hanging",
        "Lord Hanuman",
        "Panchamukhi Hanuman",
        "Lord Krishna",
        "Laddu Gopal",
        "Radha Krishna",
        "Radha Krishna Swing",
        "Lord Rama",
        "Ram Darbar",
        "Lord Shiva",
        "Nataraja",
        "Lord Vishnu",
        "Lord Balaji",
        "Venkateshwara",
        "Lord Murugan",
        "Kartikeya",
        "Ayyappa Swami",
        "Lord Dattatreya",
        "Lord Narasimha",
        "Sai Baba",
        "Khatu Shyam Baba",
        "Khandoba",

        "Lakshmi Devi",
        "Saraswati Devi",
        "Durga Maatha",
        "Radha Devi",
        "Annapurna Devi",
        "Lalitha Maatha",
        "Renuka Maatha",
        "Karumari Amman",

        "Buddha",
        "Laughing Buddha",
        "Rishi",
        "Elephant",
        "Elephant Pair",
        "Lion",
        "Lion Decor",
        "Turtle",
        "Turtle Decor",
        "Horse",
        "Horse Decor",
        "Gomatha",
        "Peacock",
        "Camel",
        "Bullock Cart",
        "Chariot",
        "Vintage Car",
        "Scooter",
        "Jet Fighter Plane",

        "Diya",
        "Akhanda Diya",
        "Swastik Diya",
        "Peacock Diya",
        "Crystal Diya",
        "Oil Lamp",
        "Harathi",
        "Dhoop Dhani",
        "Kalash",
        "Lota",
        "Chowki",
        "Stand",
        "Stool",
        "Singhasan",
        "Throne",
        "Peetam",
        "Asan",

        "Urli",
        "Wall Decor",
        "Table Decor",
        "Office Decor",
        "Temple Decor",
        "Home Decor",
        "Wall Hanging",
        "Wall Hook",
        "Wall Bracket",
        "Bells",
        "Om Symbol",
        "Swastik Symbol",
        "Swastik Decor",
        "Om Trishul",
        "Dashavatara",
        "Kalpavriksha",

        "Cookware",
        "Serveware",
        "Cooking Pot",
        "Cook And Serve Pot",
        "Kerala Serving Pot",
        "Ghee Pot",
        "Tea Pot",
        "Kettle",
        "Copper Glass",
        "Brass Glass",
        "Cup And Saucer",
        "Mug",
        "Drinkware",

        "Wax Casting",
        "Stone Idol",
        "Silver Plated",
        "Brass",
        "Copper",
        "Antique Finish",

        "Ganesh Chaturthi",
        "Navratri",
        "Diwali",
        "Dussehra",
        "Rakhi",
        "Onam",
        "Shivratri",
        "Janmashtami",
        "Holi",
        "Festival Gifts",

        "Corporate Gifting",
        "Wedding Return Gifts",
        "Wedding Anniversary Gifts",
        "Work Anniversary Gifts",
        "House Warming Return Gifts",
        "Pooja Return Gifts",
        "Festival Gifting",
        "Gift Hamper",
        "Special Combo",
        "New Arrival",
        "Special Offer",
    ]

    def handle(self, *args, **kwargs):
        created_count = 0

        for tag_name in self.DEFAULT_TAGS:
            slug = slugify(tag_name)

            tag, created = Tags.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": tag_name,
                    "is_active": True
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created tag: {tag.name}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeder completed. {created_count} tags created."
            )
        )

# Run: python manage.py seed_tags