import re


class EntityExtractor:
    @staticmethod
    def extract_budget(message):
        message = str(message or "").lower().replace(",", "").replace("₹", "")

        if "under" in message or "below" in message:
            amount = re.findall(r"\d+", message)
            if amount:
                return {
                    "min": 0,
                    "max": int(amount[0])
                }

        if "above" in message or "over" in message:
            amount = re.findall(r"\d+", message)
            if amount:
                return {
                    "min": int(amount[0]),
                    "max": None
                }

        numbers = re.findall(r"\d+", message)

        if len(numbers) >= 2:
            return {
                "min": int(numbers[0]),
                "max": int(numbers[1])
            }

        if len(numbers) == 1:
            value = int(numbers[0])
            return {
                "min": 0,
                "max": value
            }

        return None

    @staticmethod
    def extract_use_case(message):
        message = str(message or "").lower()

        mapping = {
            "gifting": [
                "gift", "gifting", "present", "client", "employee",
                "boss", "return gift", "housewarming", "anniversary"
            ],
            "festival": [
                "diwali", "onam", "holi", "navratri", "ganesh",
                "janmashtami", "dussehra", "festival", "wedding"
            ],
            "home_decor": [
                "home decor", "decor", "living room", "interior",
                "wall decor", "urli"
            ],
            "pooja": [
                "pooja", "worship", "temple", "mandir",
                "daily worship", "diya", "lamp", "aarti"
            ],
            "corporate": [
                "corporate", "employee", "client", "office",
                "company", "bulk order"
            ],
            "kitchen": [
                "kitchen", "kitchen essentials", "utensils",
                "cookware", "serveware", "dinnerware"
            ]
        }

        for use_case, keywords in mapping.items():
            if any(keyword in message for keyword in keywords):
                return use_case

        return None

    @staticmethod
    def extract_category(message):
        message = str(message or "").lower()

        mapping = {
            "brass idols": [
                "idol", "idols", "god", "goddess", "ganesha",
                "ganpati", "lakshmi", "krishna", "shiva",
                "hanuman", "durga", "saraswati", "balaji"
            ],
            "home decor": [
                "decor", "home decor", "wall decor", "urli"
            ],
            "pooja essentials": [
                "pooja", "diya", "lamp", "aarti", "mandir"
            ],
            "kitchen essentials": [
                "kitchen", "kitchen essentials", "utensils",
                "cookware", "serveware", "dinnerware"
            ],
            "gifting": [
                "gift", "gifting", "corporate gift", "festival gift",
                "return gift", "housewarming gift"
            ]
        }

        for category, keywords in mapping.items():
            if any(keyword in message for keyword in keywords):
                return category

        return None
    
    @staticmethod
    def normalize_text(text):
        return str(text or "").lower().strip().replace("-", " ")


    @staticmethod
    def extract_search_terms(message):
        message = EntityExtractor.normalize_text(message)

        stop_words = [
            "show", "me", "need", "want", "looking", "for",
            "under", "below", "above", "over", "rs", "inr",
            "price", "budget", "product", "products"
        ]

        words = re.findall(r"[a-z0-9]+", message)

        clean_words = [
            word for word in words
            if word not in stop_words and not word.isdigit()
        ]

        return clean_words
    
    @staticmethod
    def extract_product_terms(message):
        message = str(message or "").lower()

        mapping = {
            "ganesha": ["ganesha", "ganesh", "ganpati", "vinayaka"],
            "lakshmi": ["lakshmi", "mahalakshmi"],
            "krishna": ["krishna", "radha krishna"],
            "shiva": ["shiva", "mahadev"],
            "hanuman": ["hanuman"],
            "durga": ["durga"],
            "diya": ["diya", "deepam", "lamp"],
            "urli": ["urli"],
            "bell": ["bell", "ghanti"],
            "thali": ["thali", "pooja thali"],
        }

        matched_terms = []

        for term, keywords in mapping.items():
            if any(keyword in message for keyword in keywords):
                matched_terms.append(term)

        return matched_terms

    @staticmethod
    def extract_order_id(message):
        message = str(message or "").strip()
        match = re.search(r"[A-Z0-9\-]{6,}", message, re.I)
        return match.group(0) if match else None