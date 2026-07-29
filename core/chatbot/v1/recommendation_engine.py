from decimal import Decimal
from django.db.models import Q
from django.urls import reverse
from core.chatbot.v1.entity_extractor import EntityExtractor
from core.models import Product, Category, ChatbotKeyword
import re, unicodedata


class RecommendationEngine:
    @staticmethod
    def normalize(text):
        text = str(text or "")
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")

        return (
            text.lower()
            .replace("&", " and ")
            .replace("-", " ")
            .replace("_", " ")
            .replace("/", " ")
            .strip()
        )

    @staticmethod
    def extract_search_words(message):
        stop_words = {
            "show", "me", "need", "want", "looking", "for",
            "under", "below", "above", "over", "rs", "inr",
            "price", "budget", "product", "products", "item", "items",
            "brass", "please", "suggest", "recommend", "collection"
        }

        words = re.findall(r"[a-z0-9]+", RecommendationEngine.normalize(message))

        return [
            word for word in words
            if len(word) > 2
            and not word.isdigit()
            and word not in stop_words
        ]

    @staticmethod
    def parse_budget_range(budget):
        if isinstance(budget, dict):
            return budget.get("min"), budget.get("max")

        budget = RecommendationEngine.normalize(
            str(budget or "").replace("₹", "").replace(",", "")
        )

        numbers = [int(num) for num in re.findall(r"\d+", budget)]

        if ("under" in budget or "below" in budget) and numbers:
            return 0, numbers[0]

        if ("above" in budget or "over" in budget) and numbers:
            return numbers[0], None

        if len(numbers) >= 2:
            return min(numbers[0], numbers[1]), max(numbers[0], numbers[1])

        if len(numbers) == 1:
            return 0, numbers[0]

        return None, None

    @staticmethod
    def get_product_price(product):
        return product.discount_price or product.price or Decimal("0")

    @staticmethod
    def is_in_budget(product, budget):
        min_price, max_price = RecommendationEngine.parse_budget_range(budget)

        if min_price is None and max_price is None:
            return True

        price = RecommendationEngine.get_product_price(product)

        if min_price is not None and price < Decimal(str(min_price)):
            return False

        if max_price is not None and price > Decimal(str(max_price)):
            return False

        return True

    @staticmethod
    def base_products():
        return Product.objects.filter(
            is_active=True
        ).select_related(
            "category",
            "collection",
            "inventory"
        ).prefetch_related(
            "images",
            "tags",
            "attributes"
        ).distinct()

    SPECIFIC_KEYWORD_GROUPS = {
        "radha krishna": ["radha krishna"],
        "vishnu lakshmi": ["vishnu lakshmi"],
        "ganesh lakshmi": ["ganesh lakshmi", "ganesha lakshmi"],
        "ram sita": ["ram sita", "ram seeta", "ram darbar"],

        "laddu gopal": ["laddu gopal", "chhote krishna"],
        "khatu shyam": ["khatu shyam", "khatu shyam baba"],
        "sai baba": ["sai baba"],

        "ganesha": ["ganesha", "ganapati", "ganesh"],
        "lakshmi": ["lakshmi", "laxmi"],
        "krishna": ["krishna", "kanha", "kanhaiya", "kisna"],
        "shiva": ["shiva"],
        "hanuman": ["hanuman", "bajrangbali"],
        "durga": ["durga"],
        "narsimha": ["narsimha", "narasimha", "narsimham"],
        "balaji": ["balaji", "venkateshwara"],
        "murugan": ["murugan"],
        "vishnu": ["vishnu"],
        "saraswati": ["saraswati", "saraswathi"],
    }
    @staticmethod
    def get_specific_keyword_group(message):
        text = RecommendationEngine.normalize(message)

        best_canonical = None
        best_aliases = []
        best_alias = ""

        for canonical, aliases in RecommendationEngine.SPECIFIC_KEYWORD_GROUPS.items():
            for alias in aliases:
                alias_text = RecommendationEngine.normalize(alias)

                if alias_text in text and len(alias_text) > len(best_alias):
                    best_canonical = canonical
                    best_aliases = [
                        RecommendationEngine.normalize(item)
                        for item in aliases
                    ]
                    best_alias = alias_text

        return best_canonical, best_aliases

    @staticmethod
    def get_context_terms(message):
        text = RecommendationEngine.normalize(message)
        terms = []

        if "wax" in text or "wax casting" in text:
            terms.append("wax")

        if "stone" in text or "stone idol" in text or "stone idols" in text:
            terms.append("stone")

        if "silver" in text:
            terms.append("silver")

        return terms

    @staticmethod
    def get_category_ids(category):
        if not category:
            return []

        category_ids = [category.id]
        queue = [category.id]

        while queue:
            child_ids = list(
                Category.objects.filter(
                    parent_id__in=queue,
                    is_active=True
                ).values_list("id", flat=True)
            )

            new_ids = [
                child_id for child_id in child_ids
                if child_id not in category_ids
            ]

            category_ids.extend(new_ids)
            queue = new_ids

        return category_ids

    @staticmethod
    def get_direct_category_lock(message):
        text = RecommendationEngine.normalize(message)

        category_map = {
            "brass idols": "idols-and-statues",
            "idol": "idols-and-statues",
            "idols": "idols-and-statues",
            "home decor": "home-decor",
            "pooja essentials": "pooja-essentials",
            "pooja": "pooja-essentials",
            "kitchen essentials": "kitchen-essentials",
            "kitchen": "kitchen-essentials",
            "gifting": "gifting-items",
            "gift": "gifting-items",
        }

        best_slug = None
        best_length = 0

        for keyword, slug in category_map.items():
            if keyword in text and len(keyword) > best_length:
                best_slug = slug
                best_length = len(keyword)

        if not best_slug:
            return None

        return Category.objects.filter(
            slug=best_slug,
            is_active=True
        ).first()

    @staticmethod
    def find_keyword_matches(message):
        text = RecommendationEngine.normalize(message)

        keywords = ChatbotKeyword.objects.filter(
            is_active=True
        ).select_related(
            "category",
            "collection",
            "tag"
        ).order_by(
            "-priority",
            "keyword"
        )

        matches = []

        for item in keywords:
            keyword = RecommendationEngine.normalize(item.keyword)

            if keyword and keyword in text:
                matches.append(item)

        return matches

    @staticmethod
    def target_text(keyword_obj):
        if keyword_obj.collection:
            return RecommendationEngine.normalize(
                f"{keyword_obj.collection.name} {keyword_obj.collection.slug}"
            )

        if keyword_obj.category:
            return RecommendationEngine.normalize(
                f"{keyword_obj.category.name} {keyword_obj.category.slug}"
            )

        if keyword_obj.tag:
            return RecommendationEngine.normalize(
                f"{keyword_obj.tag.name} {keyword_obj.tag.slug}"
            )

        return ""

    @staticmethod
    def select_lock(matches, message):
        if not matches:
            return None

        text = RecommendationEngine.normalize(message)
        context_terms = RecommendationEngine.get_context_terms(message)
        specific_key, specific_aliases = RecommendationEngine.get_specific_keyword_group(text)

        if specific_key:
            specific_matches = [
                item for item in matches
                if RecommendationEngine.normalize(item.keyword) in specific_aliases
                and item.collection_id
            ]

            if context_terms:
                contextual = [
                    item for item in specific_matches
                    if any(term in RecommendationEngine.target_text(item) for term in context_terms)
                ]

                if contextual:
                    contextual.sort(key=lambda item: item.priority, reverse=True)
                    return contextual[0]

            if specific_matches:
                specific_matches.sort(key=lambda item: item.priority, reverse=True)
                return specific_matches[0]

        direct_category = RecommendationEngine.get_direct_category_lock(text)

        if direct_category:
            return ChatbotKeyword(
                keyword=direct_category.name,
                category=direct_category,
                priority=100
            )

        matches.sort(
            key=lambda item: (
                len(RecommendationEngine.normalize(item.keyword)),
                4 if item.collection else 3 if item.category else 2 if item.tag else 1,
                item.priority
            ),
            reverse=True
        )

        return matches[0]

    @staticmethod
    def related_links(matches, lock, message):
        links = []
        seen = set()

        text = RecommendationEngine.normalize(message)
        specific_key, specific_aliases = RecommendationEngine.get_specific_keyword_group(text)

        if specific_key:
            related = [
                item for item in matches
                if RecommendationEngine.normalize(item.keyword) in specific_aliases
                and item.collection_id
            ]
        else:
            related = [lock] if lock else []

        related.sort(key=lambda item: item.priority, reverse=True)

        for item in related:
            link = RecommendationEngine.build_link_from_keyword(item)

            if link and link["url"] not in seen:
                links.append(link)
                seen.add(link["url"])

        return links[:4]

    @staticmethod
    def get_products_from_keyword(keyword_obj):
        products = RecommendationEngine.base_products()

        if keyword_obj.collection:
            return products.filter(collection=keyword_obj.collection)

        if keyword_obj.category:
            category_ids = RecommendationEngine.get_category_ids(keyword_obj.category)
            return products.filter(category_id__in=category_ids)

        if keyword_obj.tag:
            return products.filter(tags=keyword_obj.tag)

        return Product.objects.none()

    @staticmethod
    def build_link_from_keyword(keyword_obj):
        if not keyword_obj:
            return {
                "label": "View All Products",
                "url": reverse("Products")
            }

        if keyword_obj.collection:
            return {
                "label": f"View All {keyword_obj.collection.name}",
                "url": reverse(
                    "ProductsByCollection",
                    kwargs={"slug": keyword_obj.collection.slug}
                )
            }

        if keyword_obj.category:
            category = keyword_obj.category

            if category.parent_id:
                return {
                    "label": f"View All {category.name}",
                    "url": reverse(
                        "ProductsBySubcategory",
                        kwargs={"slug": category.slug}
                    )
                }

            return {
                "label": f"View All {category.name}",
                "url": reverse(
                    "ProductsByCategory",
                    kwargs={"slug": category.slug}
                )
            }

        return {
            "label": "View All Products",
            "url": reverse("Products")
        }

    @staticmethod
    def remove_decor_style_products(products, message):
        text = RecommendationEngine.normalize(message)

        if "idol" not in text and "idols" not in text and "brass idols" not in text:
            return products

        return products.exclude(
            Q(name__icontains="wall decor") |
            Q(name__icontains="home decor") |
            Q(name__icontains="wall hanging") |
            Q(description__icontains="wall decor") |
            Q(description__icontains="home decor") |
            Q(description__icontains="wall hanging") |
            Q(slug__icontains="wall-decor") |
            Q(slug__icontains="home-decor") |
            Q(slug__icontains="wall-hanging")
        )

    @staticmethod
    def score_product(product, words, keyword_obj=None):
        score = 0

        name = RecommendationEngine.normalize(product.name)
        slug = RecommendationEngine.normalize(product.slug)
        description = RecommendationEngine.normalize(product.description)

        category_text = ""
        if product.category:
            category_text = RecommendationEngine.normalize(
                f"{product.category.name} {product.category.slug}"
            )

        collection_text = ""
        if product.collection:
            collection_text = RecommendationEngine.normalize(
                f"{product.collection.name} {product.collection.slug}"
            )

        tag_text = " ".join(
            RecommendationEngine.normalize(f"{tag.name} {tag.slug}")
            for tag in product.tags.all()
        )

        attribute_text = " ".join(
            RecommendationEngine.normalize(f"{attr.name} {attr.value}")
            for attr in product.attributes.all()
        )

        if keyword_obj:
            keyword = RecommendationEngine.normalize(keyword_obj.keyword)

            if keyword in name:
                score += 120
            if keyword in slug:
                score += 100
            if keyword in collection_text:
                score += 90
            if keyword in tag_text:
                score += 70
            if keyword in category_text:
                score += 50
            if keyword in description:
                score += 30

            score += keyword_obj.priority

        for word in words:
            if word in name:
                score += 60
            if word in slug:
                score += 50
            if word in collection_text:
                score += 45
            if word in tag_text:
                score += 35
            if word in category_text:
                score += 25
            if word in description:
                score += 15
            if word in attribute_text:
                score += 10

        return score

    @staticmethod
    def rank_products(products, words, keyword_obj=None):
        scored = []

        for product in products[:300]:
            score = RecommendationEngine.score_product(
                product=product,
                words=words,
                keyword_obj=keyword_obj
            )

            scored.append((product, score))

        scored.sort(
            key=lambda item: (
                item[1],
                RecommendationEngine.get_product_price(item[0]) or Decimal("0"),
                item[0].created_at or item[0].updated_at
            ),
            reverse=True
        )

        return [product for product, score in scored]

    @staticmethod
    def fallback_search(message):
        words = RecommendationEngine.extract_search_words(message)

        if not words:
            return []

        query = Q()

        for word in words:
            query |= Q(name__icontains=word)
            query |= Q(slug__icontains=word)
            query |= Q(description__icontains=word)
            query |= Q(collection__name__icontains=word)
            query |= Q(collection__slug__icontains=word)
            query |= Q(category__name__icontains=word)
            query |= Q(category__slug__icontains=word)
            query |= Q(tags__name__icontains=word)
            query |= Q(tags__slug__icontains=word)
            query |= Q(attributes__name__icontains=word)
            query |= Q(attributes__value__icontains=word)

        products = RecommendationEngine.base_products().filter(query).distinct()

        return RecommendationEngine.rank_products(
            products=products,
            words=words
        )
    

    @staticmethod
    def get_candidate_locks(matches, message):
        text = RecommendationEngine.normalize(message)
        context_terms = RecommendationEngine.get_context_terms(text)
        specific_key, specific_aliases = RecommendationEngine.get_specific_keyword_group(text)

        if specific_key:
            locks = [
                item for item in matches
                if RecommendationEngine.normalize(item.keyword) in specific_aliases
                and item.collection_id
            ]

            if context_terms:
                locks = [
                    item for item in locks
                    if any(
                        term in RecommendationEngine.target_text(item)
                        for term in context_terms
                    )
                ]

            unique = []
            seen = set()

            for item in sorted(locks, key=lambda x: x.priority, reverse=True):
                if item.collection_id not in seen:
                    unique.append(item)
                    seen.add(item.collection_id)

            return unique

        lock = RecommendationEngine.select_lock(matches, message)
        return [lock] if lock else []
    

    @staticmethod
    def same_keyword_fallback_products(search_text, specific_aliases):
        products = RecommendationEngine.base_products()

        query = Q()

        for alias in specific_aliases:
            query |= Q(name__icontains=alias)
            query |= Q(slug__icontains=alias.replace(" ", "-"))
            query |= Q(description__icontains=alias)
            query |= Q(tags__name__icontains=alias)
            query |= Q(tags__slug__icontains=alias.replace(" ", "-"))

        return products.filter(query).distinct()


    @staticmethod
    def recommend(context=None, message=None, limit=5):
        context = context or {}
        message = str(message or "").strip()

        context_text = " ".join([
            str(context.get("category", "")),
            str(context.get("use_case", "")),
            str(context.get("product_type", "")),
            str(context.get("intent", "")),
        ]).strip()

        search_text = f"{context_text} {message}".strip()
        words = RecommendationEngine.extract_search_words(search_text)

        budget = (
            context.get("budget")
            or EntityExtractor.extract_budget(message)
            or EntityExtractor.extract_budget(search_text)
        )

        matches = RecommendationEngine.find_keyword_matches(search_text)
        candidate_locks = RecommendationEngine.get_candidate_locks(
            matches,
            search_text
        )

        lock = candidate_locks[0] if candidate_locks else None

        links = RecommendationEngine.related_links(
            matches=matches,
            lock=lock,
            message=search_text
        )

        category_label = None
        ranked_products = []

        for candidate_lock in candidate_locks:
            products = RecommendationEngine.get_products_from_keyword(candidate_lock)

            products = RecommendationEngine.remove_decor_style_products(
                products,
                search_text
            )

            ranked = RecommendationEngine.rank_products(
                products=products,
                words=words,
                keyword_obj=candidate_lock
            )

            if budget:
                ranked = [
                    product for product in ranked
                    if RecommendationEngine.is_in_budget(product, budget)
                ]

            if ranked:
                ranked_products = ranked
                lock = candidate_lock
                break

        specific_key, specific_aliases = RecommendationEngine.get_specific_keyword_group(search_text)

        if not ranked_products and specific_key:
            fallback_products = RecommendationEngine.same_keyword_fallback_products(
                search_text,
                specific_aliases
            )

            ranked_products = RecommendationEngine.rank_products(
                products=fallback_products,
                words=words
            )

            if budget:
                ranked_products = [
                    product for product in ranked_products
                    if RecommendationEngine.is_in_budget(product, budget)
                ]

        if not ranked_products and not lock:
            ranked_products = RecommendationEngine.fallback_search(search_text)

        if budget:
            ranked_products.sort(
                key=lambda product: (
                    RecommendationEngine.get_product_price(product) or Decimal("0"),
                    product.created_at or product.updated_at
                ),
                reverse=True
            )

        final_products = ranked_products[:limit]

        return {
            "products": [
                RecommendationEngine.serialize_product(product)
                for product in final_products
            ],
            "links": links[:4],
            "category": category_label,
        }

    @staticmethod
    def serialize_product(product):
        image = product.images.first()
        price = product.discount_price or product.price

        return {
            "name": product.name,
            "price": str(price),
            "mrp": str(product.price),
            "slug": product.slug,
            "url": reverse(
                "ProductDetails",
                kwargs={"slug": product.slug}
            ),
            "image": image.image.url if image and image.image else "",
        }
    
