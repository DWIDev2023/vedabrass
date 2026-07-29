CATEGORY_MAPPING = {
    "Idols": "pooja",
    "Statue": "decor",
    "God": "pooja",
    "Goddess": "pooja",
    "Divine Pair": "pooja",
    "Gomatha": "decor",
    "Pooja": "pooja",
    "Dining": "kitchen",
    "Kitchen": "kitchen",
    "Cook": "kitchen",
    "Serve": "kitchen",
    "Drink": "kitchen",
    "Home Decor": "decor",
    "Wall Decor": "decor",
    "Table Decor": "decor",
    "Urli": "decor",
    "Kalash": "pooja",
    "Chowki": "pooja",
    "Diya": "pooja",
    "Bells": "pooja",
    "Lamps": "pooja",
    "Asan": "pooja",
}
COLLECTION_DEITY_MAPPING = {
    "Lord Ganesha": "ganesha",
    "Lord Krishna": "krishna",
    "Laddu Gopal": "krishna",
    "Lord Hanuman": "hanuman",
    "Lord Balaji": "balaji",
    "Lord Narsimha": "narsimha",
    "Lord Dattatreya": "dattatreya",
    "Lord Murugan": "murugan",
    "Lord Vishnu": "vishnu",
    "Lord Kartikeya": "kartikeya",
    "Ayappa Swami": "ayyappa",
    "Nataraj Swami": "nataraj",
    "Sai Baba": "sai",
    "Shri Khandoba": "khandoba",
    "Khatu Shyam": "khatu-shyam",
    "Shri Ram": "ram",
    "Lord Shiva": "shiva",
    "Lalitha Masta": "lalitha",
    "Lakshmi Devi": "lakshmi",
    "Renuka Maata": "renuka",
    "Radha Devi": "radha",
    "Annapurna Devi": "annapurna",
    "Saraswati Devi": "saraswati",
    "Durga Maata": "durga",
    "Karumari Amman": "karumari-amman",
    "Radha Krishna": "radha-krishna",
    "Ganesh Lakshmi": "ganesh-lakshmi",
    "Ram Sita": "ram-sita",
    "Vishnu Lakshmi": "vishnu-lakshmi",
}
DEITY_COMPATIBILITY = {
    "ganesha": ["ganesha"],
    "lakshmi": [
        "lakshmi",
        "ganesha",
    ],
    "shiva": [
        "nandi",
    ],
    "krishna": [
        "radha",
        "krishna",
    ],
    "rama": [
        "hanuman",
    ],
}
PRODUCT_TYPES = {
    "idol": ["idol", "murti", "statue"],
    "diya": ["diya", "deepam", "lamp"],
    "bell": ["bell", "ghanti"],
    "kalash": ["kalash"],
    "plate": ["plate", "thali"],
    "glass": ["glass", "tumbler"],
    "cup": ["cup"],
    "jug": ["jug"],
    "mug": ["mug"],
    "bowl": ["bowl", "vati"],
    "wall_decor": ["wall"],
    "table_decor": ["table"],
    "chowki": ["chowki"],
    "urli": ["urli"],
    "spoon": ["spoon"],
    "tray": ["tray"],
    "serveware": ["serveware"],
    "incense_holder": ["incense holder", "agarbatti"],
    "camphor_holder": ["camphor"],
    "serveware": ["serveware"],
    "mug": ["mug"],
}
MATERIALS = {
    "brass": ["brass"],
    "copper": ["copper"],
    "bronze": ["bronze"],
    "stone": ["stone", "marble", "granite"],
    "wood": ["wood"],
    "glass": ["glass"],
    "stainless_steel": ["stainless steel", "steel",],
}
MATERIAL_COMPATIBILITY = {
    "brass": [
        "brass",
        "bronze",
        "copper",
    ],
    "bronze": [
        "bronze",
        "brass",
        "copper",
    ],
    "copper": [
        "copper",
        "brass",
        "bronze",
    ],
    "stone": [
        "stone",
        "marble",
        "granite",
    ],
    "wood": [
        "wood",
    ],
    "glass": [
        "glass",
    ],
    "stainless_steel": [
        "stainless_steel",
        "steel",
    ],
}
STYLE_KEYWORDS = {
    "handcrafted": ["handcrafted", "hand made"],
    "traditional": ["traditional"],
    "modern":["modern"],
    "vintage":["vintage"],
    "antique": ["antique"],
    "premium": ["premium", "luxury"],
    "decorative": ["decorative"],
    "engraved": ["engraved", "etched"],
    "hammered": ["hammered"],
    "polished":["polished"],
    "matte":["matte"],
    "glossy":["glossy"],
    "panchamukhi": ["panchamukhi"],
    "standing": ["standing"],
    "sitting": ["sitting"],
}
HERO_PRODUCT_TYPES = {
    "idol",
    "urli",
    "wall_decor",
    "table_decor",
    "plate",
    "pooja_set",
}
ACCESSORY_PRODUCT_TYPES = {
    "bell",
    "diya",
    "kalash",
    "incense_holder",
    "camphor_holder",
    "spoon",
    "glass",
    "bowl",
    "saucer",
}
PRODUCT_FAMILY = {
    "idol":"pooja",
    "bell":"pooja",
    "diya":"pooja",
    "kalash":"pooja",
    "chowki":"pooja",
    "pooja_set":"pooja",
    "incense_holder":"pooja",
    "camphor_holder":"pooja",
    "plate":"kitchen",
    "glass":"kitchen",
    "cup":"kitchen",
    "mug":"kitchen",
    "jug":"kitchen",
    "bowl":"kitchen",
    "spoon":"kitchen",
    "tray":"kitchen",
    "serveware":"kitchen",
    "urli":"decor",
    "wall_decor":"decor",
    "table_decor":"decor",
    "flower_bowl":"decor",
    "planter":"decor",
}
USAGE_MAPPING = {
    # Pooja
    "idol": ["pooja", "decor"],
    "pooja_set": ["pooja"],
    "bell": ["pooja"],
    "diya": ["pooja", "decor"],
    "kalash": ["pooja"],
    "chowki": ["pooja"],
    "aarti_plate": ["pooja"],
    "incense_holder": ["pooja"],
    "camphor_holder": ["pooja"],
    # Kitchen
    "plate": ["kitchen", "dining"],
    "glass": ["kitchen", "dining"],
    "cup": ["kitchen", "dining"],
    "jug": ["kitchen", "dining"],
    "bowl": ["kitchen", "dining"],
    "tray": ["kitchen", "serving"],
    "serveware": ["kitchen", "serving"],
    "spoon": ["kitchen"],
    # Decor
    "urli": ["decor"],
    "wall_decor": ["decor"],
    "table_decor": ["decor"],
    "flower_bowl": ["decor"],
    "planter": ["decor"],
}
ROOM_MAPPING = {
    "idol": [
        "pooja_room",
        "living_room",
        "office",
        "temple",
    ],
    "pooja_set": [
        "pooja_room",
        "temple",
    ],
    "bell": [
        "pooja_room",
    ],
    "diya": [
        "pooja_room",
        "entrance",
        "living_room",
    ],
    "kalash": [
        "pooja_room",
    ],
    "chowki": [
        "pooja_room",
    ],
    "plate": [
        "kitchen",
        "dining",
    ],
    "glass": [
        "kitchen",
        "dining",
    ],
    "cup": [
        "kitchen",
        "office",
    ],
    "jug": [
        "kitchen",
        "dining",
    ],
    "bowl": [
        "kitchen",
        "dining",
    ],
    "tray": [
        "kitchen",
        "dining",
    ],
    "urli": [
        "entrance",
        "living_room",
    ],
    "wall_decor": [
        "living_room",
        "office",
    ],
    "table_decor": [
        "living_room",
        "office",
    ],
    "flower_bowl": [
        "living_room",
    ],
    "planter": [
        "living_room",
        "balcony",
    ],
    "chowki":[
        "pooja_room",
        "temple",
    ],
    "bell":[
        "pooja_room",
        "temple",
    ]
}
OCCASION_MAPPING = {
    "idol": [
        "housewarming",
        "wedding",
        "festival",
    ],
    "pooja_set": [
        "festival",
        "housewarming",
    ],
    "bell": [
        "festival",
    ],
    "diya": [
        "diwali",
        "festival",
        "housewarming",
    ],
    "kalash": [
        "wedding",
        "housewarming",
    ],
    "urli": [
        "housewarming",
        "wedding",
    ],
    "wall_decor": [
        "housewarming",
    ],
    "table_decor": [
        "housewarming",
        "wedding",
    ],
    "plate": [
        "wedding",
        "return_gift",
    ],
    "glass": [
        "return_gift",
    ],
    "cup": [
        "return_gift",
    ],
    "jug": [
        "wedding",
    ],
}
ROLE_RULES = {
    "idol": {
        "preferred": [
            "chowki",
            "bell",
            "diya",
            "kalash",
        ],
        "optional": [
            "incense_holder",
            "camphor_holder",
            "kalash",
        ],
        "forbidden": [
            "plate",
            "glass",
            "cup",
        ],
    },
    "pooja_set": {
        "preferred": [
            "bell",
            "diya",
        ],
        "optional": [
            "kalash",
        ],
        "forbidden": [],
    },
    "plate": {
        "preferred": [
            "bowl",
            "glass",
        ],
        "optional": [
            "tray",
            "jug",
            "spoon",
        ],
        "forbidden": [
            "idol",
            "bell",
        ],
    },
    "cup": {
        "preferred": [
            "saucer",
        ],
        "optional": [],
        "forbidden": [
            "idol",
        ],
    },
    "urli": {
        "preferred": [
            "flower_bowl",
            "table_decor",
        ],
        "optional": [
            "wall_decor",
        ],
        "forbidden": [
            "plate",
            "glass",
        ],
    },
    "wall_decor": {
        "preferred": [
            "table_decor",
        ],
        "optional": [
            "urli",
        ],
        "forbidden": [
            "plate",
        ],
    },
}
BUNDLE_TEMPLATES = {
    "idol": [
        ["idol", "bell"],
        ["idol", "diya"],
        ["idol", "bell", "diya"],
        ["idol", "chowki", "bell"],
        ["idol", "diya", "kalash"],
        ["idol","chowki","diya"],
    ],
    "pooja_set": [
        ["pooja_set", "bell"],
        ["pooja_set", "diya"],
    ],
    "plate": [
        ["plate", "glass"],
        ["plate", "bowl"],
        ["plate", "glass", "bowl"],
        ["plate", "jug", "glass"],
        ["plate","bowl","spoon"],
    ],
    "cup": [
        ["cup", "saucer"],
    ],
    "urli": [
        ["urli", "flower_bowl"],
        ["urli", "table_decor"],
        ["urli", "flower_bowl", "table_decor"],
    ],
    "wall_decor": [
        ["wall_decor", "table_decor"],
    ],
}
EXCLUDED_COMBINATIONS = {
    ("idol", "plate"),
    ("idol", "glass"),
    ("idol", "cup"),
    ("idol", "jug"),
    ("bell", "glass"),
    ("bell", "jug"),
    ("diya", "glass"),
    ("diya", "cup"),
    ("kalash", "glass"),
    ("plate", "bell"),
    ("urli", "plate"),
    ("wall_decor", "glass"),
}
PRODUCT_PRIORITY = {
    "idol": 100,
    "pooja_set": 95,
    "plate": 90,
    "urli": 85,
    "chowki": 80,
    "wall_decor": 75,
    "table_decor": 75,
    "jug": 70,
    "glass": 65,
    "bowl": 65,
    "cup": 60,
    "tray": 60,
    "mug": 60,
    "bell": 55,
    "diya": 55,
    "kalash": 50,
    "aarti_plate":45,
    "incense_holder":40,
    "camphor_holder":40,
    "spoon": 40,
    "saucer": 30,
}
COMPATIBILITY_SCORE = {
    # Pooja
    ("idol", "bell"): 95,
    ("idol", "diya"): 90,
    ("idol", "chowki"): 100,
    ("idol", "kalash"): 85,
    ("idol", "incense_holder"): 80,
    ("bell", "diya"): 75,
    ("bell", "kalash"): 70,
    ("diya", "kalash"): 70,
    # Kitchen
    ("plate", "bowl"): 95,
    ("plate", "glass"): 90,
    ("plate", "jug"): 85,
    ("plate", "spoon"): 80,
    ("cup", "saucer"): 100,
    ("glass", "jug"): 85,
    # Decor
    ("urli", "flower_bowl"): 95,
    ("urli", "table_decor"): 90,
    ("wall_decor", "table_decor"): 85,
    ("jug", "glass"): 90,
    ("table_decor", "wall_decor"): 85,
    ("urli", "table_decor"): 90,
}
REQUIRED_MATCHES = {
    "idol":[
        "material",
    ],
    "plate":[
        "material",
    ],
    "wall_decor":[
        "material",
    ],
}
DESCRIPTION_INTROS = {
    "pooja": (
        "Bring home divine blessings with this thoughtfully curated pooja bundle featuring complementary handcrafted products."
    ),
    "decor": (
        "Enhance your interiors with this carefully curated décor bundle designed to create a harmonious living space."
    ),
    "kitchen": (
        "A coordinated collection of premium dining essentials curated for everyday elegance."
    ),
}
DESCRIPTION_CLOSINGS = {
    "pooja": (
        "Perfect for daily worship, festive celebrations and creating a sacred atmosphere at home."
    ),
    "decor": (
        "A timeless collection that complements both traditional and contemporary interiors."
    ),
    "kitchen": (
        "Designed to bring functionality, elegance and lasting value to your dining experience."
    ),
}
BUNDLE_KEYWORD_PRIORITY = [
    "festival",
    "deity",
    "collection",
    "category",
]
BUNDLE_ADJECTIVES = {

    "pooja": [
        "Sacred",
        "Traditional",
        "Divine",
        "Spiritual",
    ],

    "decor": [
        "Elegant",
        "Decorative",
        "Artisan",
        "Timeless",
    ],

    "kitchen": [
        "Traditional",
        "Authentic",
        "Classic",
        "Heritage",
    ],

    "premium": [
        "Premium",
        "Luxury",
        "Heritage",
        "Signature",
    ],

    "festival": [
        "Festive",
        "Celebration",
        "Auspicious",
    ],

    "modern": [
        "Modern",
        "Contemporary",
    ],

    "antique": [
        "Antique",
        "Vintage",
    ],

}
BUNDLE_ENDINGS = {

    "pooja": [
        "Pooja Set",
        "Pooja Combo",
        "Pooja Collection",
        "Pooja Essentials",
    ],

    "decor": [
        "Decor Set",
        "Decor Collection",
        "Decor Combo",
        "Home Decor Set",
    ],

    "kitchen": [
        "Kitchen Set",
        "Kitchen Combo",
        "Dining Set",
        "Dining Collection",
    ],

    "festival": [
        "Festival Combo",
        "Festival Collection",
        "Festival Essentials",
        "Festival Set",
    ],

    "default": [
        "Bundle",
        "Collection",
        "Combo",
    ],

}

PREMIUM_PRICE = 25000

MIN_PRODUCTS = 2
MAX_PRODUCTS = 3

MAX_HERO_PRODUCTS = 1
MIN_ACCESSORIES = 1
MAX_ACCESSORIES = 2

MIN_BUNDLE_SCORE = 60
MAX_BUNDLES_PER_PRODUCT = 5
MIN_COMPATIBILITY_SCORE = 60