from django.db.models import Q
from django.core.exceptions import FieldError

from core.models import Product
from .entity_matcher import EntityMatcher
from .product_filter import ProductFilter
from .product_ranker import ProductRanker
from .serializer import ProductSerializer
from .link_builder import LinkBuilder
from .faq_engine_v2 import FAQEngineV2


class RecommendationEngineV2:
    SHOPPING_WORDS = {
        "buy",
        "purchase",
        "gift",
        "wedding",
        "housewarming",
        "decor",
        "decoration",
        "pooja",
        "mandir",
        "temple",
        "bell",
        "idol",
        "statue",
        "urli",
        "handle",
        "door",
        "ganesha",
        "krishna",
        "lakshmi",
        "shiv",
        "brass",
        "home",
        "office",
        "wall",
        "lamp",
        "diya",
        "showpiece",
        "vastu",
    }

    GIFTING_CATEGORY_SLUG = "gifting-items"

    GIFTING_SUBCATEGORY_SLUGS = {
        "festival gifts": "festival-gifts",
        "festival-gifts": "festival-gifts",
        "special occasion gifts": "special-occassion-gifts",
        "special occassion gifts": "special-occassion-gifts",
        "special-occassion-gifts": "special-occassion-gifts",
        "special-occasion-gifts": "special-occassion-gifts",
        "corporate gifting": "corporate-gifting",
        "corporate-gifting": "corporate-gifting",
    }

    GIFTING_COLLECTION_SLUGS = {
        "diwali": "diwali",
        "onam": "onam",
        "holi": "holi",
        "dussehra": "dussehra",
        "janmashtami": "jamashtami",
        "jamashtami": "jamashtami",
        "ganesh chaturthi": "ganesh-caturthi",
        "ganesh caturthi": "ganesh-caturthi",
        "ganesh-caturthi": "ganesh-caturthi",
        "ganesh-chaturthi": "ganesh-caturthi",
        "navratri": "navratri",
        "happy rakhi": "happy-rakhi",
        "happy-rakhi": "happy-rakhi",
        "house warming gift": "house-warming-gift",
        "housewarming gift": "house-warming-gift",
        "house-warming-gift": "house-warming-gift",
        "wedding anniversary": "wedding-anniversary",
        "wedding-anniversary": "wedding-anniversary",
        "gift hamper": "gift-hamper",
        "gift-hamper": "gift-hamper",
        "work anniversary": "work-anniversary",
        "work-anniversary": "work-anniversary",
        "special combos": "special-combos",
        "special-combos": "special-combos",
    }

    @staticmethod
    def has_product_intent(message):

        text = (message or "").lower()

        return any(
            word in text
            for word in RecommendationEngineV2.SHOPPING_WORDS
        )

    @staticmethod
    def recommend(
        message,
        context=None,
        limit=5,
    ):

        context = context or {}

        # ----------------------------------------
        # Guided chatbot flow
        # ----------------------------------------

        if context.get("category") or context.get("use_case"):

            return RecommendationEngineV2.recommend_from_context(
                context=context,
                limit=limit,
            )

        # ----------------------------------------
        # Free typing
        # ----------------------------------------

        return RecommendationEngineV2.recommend_from_text(
            message=message,
            limit=limit,
        )

    @staticmethod
    def _context_terms(value):
        """
        Convert guided-flow quick-reply values into search terms that can
        match category, collection, tags, and product names.
        """
        text = (value or "").strip().lower()

        term_map = {
            "brass idols": [
                "brass", "idol", "idols", "murti", "statue",
                "ganesha", "ganesh", "krishna", "lakshmi", "shiva", "shiv",
                "balaji", "hanuman", "durga", "saraswati",
            ],
            "home decor": [
                "home decor", "decor", "decoration", "wall", "urli",
                "lamp", "showpiece", "vase", "horse", "elephant",
            ],
            "pooja essentials": [
                "pooja", "puja", "diya", "deep", "lamp", "bell",
                "aarti", "arti", "mandir", "kalash", "thali",
            ],
            "gifting": [
                "gift", "gifting", "corporate", "wedding", "housewarming",
                "return gift",
            ],
            "kitchen essentials": [
                "kitchen", "dining", "serve", "serving", "bowl", "plate",
                "spoon", "glass", "jar",
            ],
            "daily worship": [
                "pooja", "puja", "worship", "diya", "lamp", "bell",
                "aarti", "arti", "mandir", "idol", "murti",
            ],
            "festival wedding": [
                "festival", "wedding", "gift", "gifting", "pooja", "puja",
                "diya", "lamp", "decor",
            ],
        }

        return term_map.get(text, [text] if text else [])

    @staticmethod
    def _build_terms_query(terms):
        query = Q()

        for term in terms:
            if not term:
                continue

            query |= (
                Q(name__icontains=term)
                | Q(category__name__icontains=term)
                | Q(category__slug__icontains=term)
                | Q(collection__name__icontains=term)
                | Q(collection__slug__icontains=term)
                | Q(tags__name__icontains=term)
            )

        return query

    @staticmethod
    def _safe_filter(queryset, query):
        try:
            return queryset.filter(query)
        except FieldError:
            return queryset.none()

    @staticmethod
    def _normalize_choice(value):
        return (value or "").strip().lower().replace("_", "-")

    @staticmethod
    def _gift_slug(value, mapping):
        text = RecommendationEngineV2._normalize_choice(value)
        return mapping.get(text) or text.replace(" ", "-")

    @staticmethod
    def _filter_gifting_hierarchy(queryset, context):
        category_slug = context.get("category_slug") or RecommendationEngineV2.GIFTING_CATEGORY_SLUG
        subcategory_slug = RecommendationEngineV2._gift_slug(
            context.get("gifting_subcategory"),
            RecommendationEngineV2.GIFTING_SUBCATEGORY_SLUGS,
        )
        collection_slug = RecommendationEngineV2._gift_slug(
            context.get("gift_collection"),
            RecommendationEngineV2.GIFTING_COLLECTION_SLUGS,
        )

        # Exact hierarchy first. Supports common schemas:
        # product.category = subcategory with category.parent = gifting-items,
        # product.category = gifting-items + product.collection = selected collection,
        # or product.collection has category/subcategory relationships.
        hierarchy_query = (
            Q(category__slug=category_slug)
            | Q(category__parent__slug=category_slug)
            | Q(collection__category__slug=category_slug)
            | Q(collection__category__parent__slug=category_slug)
        )

        if subcategory_slug:
            hierarchy_query &= (
                Q(category__slug=subcategory_slug)
                | Q(category__parent__slug=subcategory_slug)
                | Q(collection__category__slug=subcategory_slug)
                | Q(collection__category__parent__slug=subcategory_slug)
            )

        if collection_slug:
            hierarchy_query &= (
                Q(collection__slug=collection_slug)
                | Q(collection__name__iexact=(context.get("gift_collection") or ""))
            )

        filtered = RecommendationEngineV2._safe_filter(queryset, hierarchy_query).distinct()

        # If some relationship fields do not exist in the local schema, fall
        # back to the parts we know exist from the current codebase.
        if not filtered.exists() and collection_slug:
            filtered = queryset.filter(
                Q(collection__slug=collection_slug)
                | Q(collection__name__iexact=(context.get("gift_collection") or ""))
            ).distinct()

        if not filtered.exists() and subcategory_slug:
            filtered = queryset.filter(
                Q(category__slug=subcategory_slug)
                | Q(category__name__icontains=(context.get("gifting_subcategory") or ""))
            ).distinct()

        if not filtered.exists():
            filtered = queryset.filter(
                Q(category__slug=category_slug)
                | Q(category__name__icontains="gifting")
                | Q(category__name__icontains="gift")
            ).distinct()

        return filtered



    @staticmethod
    def _faq_log(faq):
        if not faq:
            return None

        return {
            "id": faq.id,
            "question": faq.question,
        }

    @staticmethod
    def _product_log(product):
        if not product:
            return None

        return {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
        }

    @staticmethod
    def _bundle_log(bundle):
        if not bundle:
            return None

        return {
            "id": bundle.id,
            "name": bundle.name,
            "slug": bundle.slug,
        }

    @staticmethod
    def _products_log(products):
        return [
            RecommendationEngineV2._product_log(product)
            for product in products
            if product
        ]

    @staticmethod
    def _apply_budget_filter(queryset, budget):
        """
        Apply budget to discount_price when available, with price fallback.
        This avoids hiding valid products whose discount_price is null.
        """
        ranges = {
            "Under 1000": (None, 1000),
            "1000 to 3000": (1000, 3000),
            "3000 to 7000": (3000, 7000),
            "7000 to 10000": (7000, 10000),
            "10000 to 15000": (10000, 15000),
            "15000 to 20000": (15000, 20000),
            "20000 to 25000": (20000, 25000),
            "Above 25000": (25000, None),
        }

        if budget not in ranges:
            return queryset

        min_price, max_price = ranges[budget]
        price_query = Q()

        if min_price is not None:
            price_query &= (
                Q(discount_price__gte=min_price)
                | Q(discount_price__isnull=True, price__gte=min_price)
            )

        if max_price is not None:
            price_query &= (
                Q(discount_price__lte=max_price)
                | Q(discount_price__isnull=True, price__lte=max_price)
            )

        return queryset.filter(price_query)

    @staticmethod
    def _empty_context_response():
        return {
            "reply": "I couldn't find products matching your selection.",
            "products": [],
            "links": [],
            "category": None,
            "quick_replies": [
                {
                    "label": "Browse Again",
                    "message": "Browse Products"
                },
                {
                    "label": "Main Menu",
                    "message": "Main Menu"
                }
            ],
            "log": {
                "result_type": "EMPTY",
                "matched_faq": None,
                "matched_bundle": None,
                "matched_products": [],
            }
        }

    @staticmethod
    def recommend_from_context(
        context,
        limit=5,
    ):

        base_queryset = Product.objects.filter(
            is_active=True,
        ).select_related(
            "category",
            "collection",
        ).prefetch_related(
            "tags",
            "images",
        )

        category = context.get("category")
        use_case = context.get("use_case")
        budget = context.get("budget")

        category_terms = RecommendationEngineV2._context_terms(category)
        use_case_terms = RecommendationEngineV2._context_terms(use_case)
        is_gifting_context = (
            context.get("category_slug") == RecommendationEngineV2.GIFTING_CATEGORY_SLUG
            or RecommendationEngineV2._normalize_choice(category) in {"gifting", "gifting-items"}
            or RecommendationEngineV2._normalize_choice(use_case) in {"gifting", "gifting-items"}
            or bool(context.get("gifting_subcategory"))
            or bool(context.get("gift_collection"))
        )

        queryset = base_queryset

        if is_gifting_context:
            queryset = RecommendationEngineV2._filter_gifting_hierarchy(
                queryset,
                context,
            )
        else:
            if category_terms:
                queryset = queryset.filter(
                    RecommendationEngineV2._build_terms_query(category_terms)
                )

            if use_case_terms:
                queryset = queryset.filter(
                    RecommendationEngineV2._build_terms_query(use_case_terms)
                )

        queryset_before_budget = queryset.distinct()

        if budget:
            queryset = RecommendationEngineV2._apply_budget_filter(
                queryset_before_budget,
                budget,
            )
        else:
            queryset = queryset_before_budget

        queryset = queryset.distinct()

        # Keep hierarchy relevance first. If a selected collection has products
        # but none inside the selected budget, show products from that exact
        # hierarchy instead of falling back to unrelated active products.
        if not queryset.exists() and budget:
            queryset = queryset_before_budget

        if not queryset.exists() and not is_gifting_context and (category_terms or use_case_terms):
            combined_terms = category_terms or use_case_terms
            queryset = base_queryset.filter(
                RecommendationEngineV2._build_terms_query(combined_terms)
            ).distinct()

        if not queryset.exists() and not is_gifting_context:
            fallback_queryset = base_queryset

            if budget:
                fallback_queryset = RecommendationEngineV2._apply_budget_filter(
                    fallback_queryset,
                    budget,
                )

            queryset = fallback_queryset.distinct()

        if not queryset.exists():
            return RecommendationEngineV2._empty_context_response()

        ranked = list(queryset.order_by("-id")[:limit])

        return {
            "reply": "Here are some products you may like.",
            "products": [
                ProductSerializer.serialize(p)
                for p in ranked
            ],
            "links": LinkBuilder.build(ranked),
            "category": (
                ranked[0].category.name
                if ranked and ranked[0].category
                else None
            ),
            "quick_replies": [
                {
                    "label": "Browse Again",
                    "message": "Browse Products"
                },
                {
                    "label": "Main Menu",
                    "message": "Main Menu"
                }
            ],
            "log": {
                "result_type": "PRODUCT",
                "matched_faq": None,
                "matched_bundle": None,
                "matched_products": RecommendationEngineV2._products_log(ranked),
            }
        }

    @staticmethod
    def recommend_from_text(
        message,
        limit=5,
    ):

        shopping_intent = RecommendationEngineV2.has_product_intent(message)

        if shopping_intent:

            parsed = EntityMatcher.extract(message)

            queryset = ProductFilter.filter(parsed)

            if queryset.exists():

                ranked = ProductRanker.rank(
                    queryset,
                    parsed,
                )[:limit]

                if ranked:

                    return {
                        "reply": "Here are some products you may like.",
                        "products": [
                            ProductSerializer.serialize(p)
                            for p in ranked
                        ],
                        "links": LinkBuilder.build(ranked),
                        "category": (
                            ranked[0].category.name
                            if ranked[0].category
                            else None
                        ),
                        "log": {
                            "result_type": "PRODUCT",
                            "matched_faq": None,
                            "matched_bundle": None,
                            "matched_products": RecommendationEngineV2._products_log(ranked),
                        }
                    }

        faq_result = FAQEngineV2.search(message)

        if faq_result["found"]:

            product = faq_result.get("product")
            bundle = faq_result.get("bundle")

            if product:

                return {
                    "reply": faq_result["answer"],
                    "products": [
                        ProductSerializer.serialize(product)
                    ],
                    "links": LinkBuilder.build([product]),
                    "category": product.category.name if product.category else None,
                    "log": {
                        "result_type": "FAQ",
                        "matched_faq": RecommendationEngineV2._faq_log(faq_result["faq"]),
                        "matched_bundle": None,
                        "matched_products": RecommendationEngineV2._products_log([product]),
                    }
                }

            if bundle:

                bundle_products = bundle.products.filter(
                    is_active=True
                )[:limit]

                return {
                    "reply": faq_result["answer"],
                    "bundle": {
                        "id": bundle.id,
                        "name": bundle.name,
                        "slug": bundle.slug,
                        "bundle_price": str(bundle.bundle_price),
                        "discounted_bundle_price": str(bundle.discounted_bundle_price),
                    },
                    "products": [
                        ProductSerializer.serialize(p)
                        for p in bundle_products
                    ],
                    "links": [
                        {
                            "label": "View Bundle",
                            "url": f"/bundles/{bundle.slug}"
                        }
                    ],
                    "category": None,
                    "log": {
                        "result_type": "BUNDLE",
                        "matched_faq": RecommendationEngineV2._faq_log(faq_result["faq"]),
                        "matched_bundle": RecommendationEngineV2._bundle_log(bundle),
                        "matched_products": RecommendationEngineV2._products_log(bundle_products),
                    }
                }

            return {
                "reply": faq_result["answer"],
                "products": [],
                "links": [],
                "category": None,
                "log": {
                    "result_type": "FAQ",
                    "matched_faq": RecommendationEngineV2._faq_log(faq_result["faq"]),
                    "matched_bundle": None,
                    "matched_products": [],
                }
            }

        return {
            "reply": (
                "I couldn't find anything relevant. "
                "Please try another search or contact our support team."
            ),
            "products": [],
            "links": [],
            "category": None,
            "log": {
                "result_type": "EMPTY",
                "matched_faq": None,
                "matched_bundle": None,
                "matched_products": [],
            }
        }