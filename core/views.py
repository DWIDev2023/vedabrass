from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Prefetch, Sum, Count, Avg, F, Max, Q, Case, When, Value, IntegerField
from decimal import Decimal, InvalidOperation
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate
from django.db import IntegrityError, transaction
from django.conf import settings
from core.utils.payu import generate_payu_hash, verify_payu_response_hash
from core.utils.shiprocket import create_shiprocket_order, assign_awb, track_by_awb, generate_pickup, generate_label, generate_invoice
from django.views.decorators.http import require_POST
from core.chatbot.v2.session_manager_v2 import SessionManagerV2
from core.chatbot.v2.state_engine_v2 import StateEngineV2
from core.utils.blog_formatter import BlogFormatter
from core.services.notifications import (
    send_order_notification,
    ORDER_PAID,
    ORDER_CANCELLED,
    INVOICE_AVAILABLE
)
from core.services.notifications import TRACKING_AVAILABLE
from .models import *
from .serializers import *
import json, uuid, traceback

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip

def get_cart(request):
    if not request.session.session_key:
        request.session.create()

    cart_id = request.session.get("cart_id")
    session_key = request.session.session_key

    cart = None

    if cart_id:
        cart = Cart.objects.filter(
            id=cart_id,
            is_completed=False
        ).first()

    if not cart:
        cart = Cart.objects.filter(
            session_key=session_key,
            is_completed=False
        ).first()

    if not cart:
        cart = Cart.objects.create(
            session_key=session_key,
            ip_address=get_client_ip(request)
        )

    request.session["cart_id"] = cart.id
    request.session.modified = True

    return cart

def cart_totals(cart):
    subtotal = 0

    for item in cart.items.select_related("product").all():
        price = item.product.discount_price or item.product.price
        subtotal += price * item.quantity

    return subtotal

def generate_order_id(cart_items):
    first_item = cart_items.first()
    product_code = first_item.product.product_code if first_item and first_item.product else "ORDER"

    base_code = f"VB{product_code}"

    last_order = Order.objects.filter(
        order_id__startswith=base_code
    ).order_by("-order_id").first()

    if last_order and last_order.order_id:
        last_number = last_order.order_id[-4:]

        try:
            next_number = int(last_number) + 1
        except ValueError:
            next_number = 1
    else:
        next_number = 1

    return f"{base_code}{next_number:04}"
        
def clear_paid_cart(order, request):
    cart = order.cart

    if cart:
        cart.customer = order.customer
        cart.is_completed = True
        cart.save()

        cart.items.all().delete()

    request.session.pop("cart_id", None)
    request.session.modified = True

def generate_invoice_number(order):
    if order.invoice_number:
        return order.invoice_number

    invoice_number = f"INV-{order.created_at.strftime('%Y%m%d')}-{order.id:05d}"

    order.invoice_number = invoice_number
    order.save(update_fields=["invoice_number"])

    return invoice_number

def get_page_faqs(request=None, page=None, product=None, bundle=None):
    if product:
        return product.faqs.filter(is_active=True)

    if bundle:
        return bundle.faqs.filter(is_active=True)

    if page is None and request is not None:
        page = getattr(request, "path", request)

    if page:
        return FAQ.objects.filter(
            is_active=True,
            page=page,
        ).order_by("id")

    return FAQ.objects.none()

def build_subcategory_breadcrumb(category, request):
    return [
        ("Home", "/"),
        ("All Categories", "/categories/"),
        (category.name, request.path),
    ]

def build_collection_breadcrumb(subcategory, request):
    return [
        ("Home", "/"),
        ("All Categories", "/categories/"),
        (subcategory.name, f"/categories/{subcategory.slug}/"),
        ("Collections", None),
    ]


def RobotsTxt(request):
    return render(request, "robots.txt", content_type="text/plain")

def WebError400(request, exception=None):
    context = {
        "meta_title": "Vedabrass | Bad Request",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'errors/web/400.html', context, status=400)

def WebError403(request, exception=None):
    context = {
        "meta_title": "Vedabrass | Access Denied",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'errors/web/403.html', context, status=403)

def WebError404(request, exception=None):
    context = {
        "meta_title": "Vedabrass | Page Not Found",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'errors/web/408.html', context, status=404)

def WebError405(request, exception=None):
    context = {
        "meta_title": "Vedabrass | Method Not Allowed",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'errors/web/405.html', context, status=405)

def WebError408(request, exception=None):
    context = {
        "meta_title": "Vedabrass | Request Timeout",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'errors/web/408.html', context, status=408)

def WebError419(request, exception=None):
    context = {
        "meta_title": "Vedabrass | Session Expired",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'errors/web/419.html', context, status=419)

def WebError500(request, exception=None):
    context = {
        "meta_title": "Vedabrass | Something Went Wrong",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'errors/web/500.html', context, status=500)

def WebError503(request, exception=None):
    context = {
        "meta_title": "Vedabrass | Service Unavailable",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'errors/web/505.html', context, status=503)

def Welcome(request):
    trending_products = Product.objects.filter(
        is_active=True
    ).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("-is_primary"),
            to_attr="ordered_images"
        )
    ).order_by("?")[:4]

    stone_products = Product.objects.filter(
        is_active=True,
        category__slug="stone-idols"
    ).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("-is_primary"),
            to_attr="ordered_images"
        )
    ).order_by("-created_at")[:4]

    gift_collections = Collection.objects.filter(
        is_active=True,
        category__slug="festival-gifts"
    ).order_by("?")[:5]
    
    all_products = list(trending_products) + list(stone_products)

    for product in all_products:
        if product.discount_price and product.price and product.discount_price < product.price:
            product.discount_percentage = round(
                ((product.price - product.discount_price) / product.price) * 100
            )
        else:
            product.discount_percentage = 0

    context = {
        "page_type": "home",
        "meta_title": "Buy Brass Idols Online India | VedaBrass",
        "meta_description": "Explore handcrafted brass products India from VedaBrass. Shop authentic brass idols, home decore, pooja items, and gifts with trusted quality and delivery across India.",
        "meta_keywords": "",
        "trending_products": trending_products,
        "stone_products": stone_products,
        "gift_collections": gift_collections,
        "faqs": get_page_faqs(request),
    }
    return render(request, 'index.html', context)

def WhoWeAre(request):
    context = {
        "page_type": "about",
        "breadcrumbs": [
            ("Home", "/"),
            ("Who We Are", request.path),
        ],
        "meta_title": "VedaBrass Brass Store Hyderabad - Handcrafted Brass Store India",
        "meta_description": "Discover VedaBrass brass store Hyderabad, your trusted destination for handcrafted brass idols, pooja articles, home décor, and traditional metal crafts made with exceptional quality and craftsmanship.",
        "meta_keywords": "",
        "faqs": get_page_faqs(request)
    }
    return render(request, 'web/about.html', context)

def Categories(request):
    categories = Category.objects.filter(parent__isnull=True)

    context = {
        "page_type": "categories",
        "breadcrumbs": [
            ("Home", "/"),
            ("Categories", request.path),
        ],
        "meta_title": "Brass Products Online India | VedaBrass",
        "meta_description": "Discover brass idols decor pooja kitchen collections at VedaBrass. Browse premium brass products crafted for homes, temples, gifting, and decore.",
        "meta_keywords": "",
        "categories": categories,
        "faqs": get_page_faqs(request=request)
    }
    return render(request, 'web/categories.html', context)

def Subcategory(request, slug):
    category = Category.objects.filter(slug=slug).first()
    subcategories = Category.objects.filter(parent=category)

    context = {
        "page_type": "subcategories",
        "breadcrumbs": build_subcategory_breadcrumb(category, request),
        "meta_title": category.meta_title,
        "meta_description": category.meta_description,
        "meta_keywords": '',
        "category": category,
        "subcategories": subcategories,
    }
    return render(request, 'web/subcategories.html', context)

def Collections(request, slug):
    subcategory = get_object_or_404(Category, slug=slug, is_active=True)
    collections = Collection.objects.filter(category=subcategory, is_active=True).select_related("category")

    context = {
        "page_type": "collections",
        "breadcrumbs": build_collection_breadcrumb(subcategory, request),
        "meta_title": subcategory.meta_title,
        "meta_description": subcategory.meta_description,
        "meta_keywords": '',
        "subcategory": subcategory,
        "collections": collections
    }
    return render(request, 'web/collections.html', context)

def SearchProducts(request):
    query = request.GET.get("productquery", "").strip()
    products = Product.objects.none()

    if query:
        search_filter = (
            Q(name__icontains=query) |
            Q(collection__name__icontains=query) |
            Q(tags__name__icontains=query) |
            Q(category__name__icontains=query) |
            Q(category__parent__name__icontains=query) |
            Q(attributes__name__icontains=query) |
            Q(attributes__value__icontains=query) |
            Q(brand__icontains=query) |
            Q(sku__icontains=query) |
            Q(product_code__icontains=query) |
            Q(meta_title__icontains=query) |
            Q(meta_description__icontains=query) |
            Q(description__icontains=query)
        )

        products = (
            Product.objects.filter(
                search_filter,
                is_active=True,
                is_deleted=False
            )
            .annotate(
                relevance=Case(

                    # Product Name
                    When(name__icontains=query, then=Value(100)),

                    # Collection
                    When(collection__name__icontains=query, then=Value(80)),

                    # Tag
                    When(tags__name__icontains=query, then=Value(70)),

                    # Category
                    When(category__name__icontains=query, then=Value(60)),

                    # Parent Category
                    When(category__parent__name__icontains=query, then=Value(55)),

                    # Brand
                    When(brand__icontains=query, then=Value(50)),

                    # Attribute Value
                    When(attributes__value__icontains=query, then=Value(45)),

                    # Attribute Name
                    When(attributes__name__icontains=query, then=Value(40)),

                    # SKU
                    When(sku__icontains=query, then=Value(35)),

                    # Product Code
                    When(product_code__icontains=query, then=Value(35)),

                    # Meta Title
                    When(meta_title__icontains=query, then=Value(30)),

                    # Meta Description
                    When(meta_description__icontains=query, then=Value(25)),

                    # Description
                    When(description__icontains=query, then=Value(20)),

                    default=Value(0),
                    output_field=IntegerField()
                )
            )
            .select_related(
                "category",
                "category__parent",
                "collection",
                "vendor",
                "inventory"
            )
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=ProductImage.objects.order_by("-is_primary"),
                    to_attr="ordered_images"
                ),
                "attributes",
                "tags"
            )
            .distinct()
            .order_by("-relevance", "-created_at")
        )

        for product in products:
            if (product.discount_price and product.price and product.discount_price < product.price):
                product.discount_percentage = round(((product.price - product.discount_price) / product.price) * 100)
            else:
                product.discount_percentage = 0

    categories = Category.objects.filter(
        parent__isnull=True,
        is_active=True
    ).prefetch_related(
        Prefetch(
            "category_set",
            queryset=Category.objects.filter(
                is_active=True
            )
        )
    )
    
    context = {
        "page_type": "search",
        "breadcrumbs": [
            ("Home", "/"),
            ("SearchProducts", request.path),
        ],
        "meta_title": "Vedabrass | Product Search",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
        "query": query,
        "products": products,
        "categories": categories,
        "results_count": products.count()
    }
    return render(request, 'web/products/search.html', context)

def Products(request):
    products = Product.objects.filter(
        is_active=True
    ).select_related(
        "category",
        "vendor",
        "collection",
        "inventory"
    ).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("-is_primary"),
            to_attr="ordered_images"
        ),
        "attributes"
    )

    for product in products:
        if (product.discount_price and product.price and product.discount_price < product.price):
            product.discount_percentage = round(((product.price - product.discount_price) / product.price) * 100)
        else:
            product.discount_percentage = 0

    categories = Category.objects.filter(
        parent__isnull=True,
        is_active=True
    ).prefetch_related(
        Prefetch(
            "category_set",
            queryset=Category.objects.filter(is_active=True)
        )
    )
    print(type(request), request)
    context = {
        "page_type": "products",
        "breadcrumbs": [
            ("Home", "/"),
            ("Products", request.path),
        ],
        "meta_title": "Buy Brass Products Online India | VedaBrass",
        "meta_description": "Shop from a premium brass handicrafts shop at VedaBrass featuring authentic brass idols, decore, pooja essentials, and gifting collections.",
        "meta_keywords": "",
        "categories": categories,
        "products": products,
        "faqs": get_page_faqs(page="/products")
    }
    return render(request, 'web/products/all.html', context)

def ProductsByCategory(request, slug):
    category = get_object_or_404(Category, slug=slug, parent__isnull=True, is_active=True)
    subcategories = Category.objects.filter(parent=category,is_active=True)
    products = Product.objects.filter(
        is_active=True, category__in=subcategories
    ).select_related(
        "category",
        "vendor",
        "collection",
        "inventory"
    ).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("-is_primary"),
            to_attr="ordered_images"
        ),
        "attributes"
    )

    for product in products:
        if (product.discount_price and product.price and product.discount_price < product.price):
            product.discount_percentage = round(((product.price - product.discount_price) / product.price) * 100)
        else:
            product.discount_percentage = 0

    categories = Category.objects.filter(
        parent__isnull=True,
        is_active=True
    ).prefetch_related(
        Prefetch(
            "category_set",
            queryset=Category.objects.filter(is_active=True)
        )
    )

    context = {
        "meta_title": category.meta_title,
        "meta_description": category.meta_description,
        "meta_keywords": "",
        "category": category,
        "products": products,
        "categories": categories
    }
    return render(request, 'web/products/category.html', context)

def ProductsBySubcategory(request, slug):
    subcategory = get_object_or_404(Category.objects.select_related("parent"), slug=slug, parent__isnull=False, is_active=True)
    category = subcategory.parent
    products = Product.objects.filter(
        is_active=True, category=subcategory
    ).select_related(
        "category",
        "vendor",
        "collection",
        "inventory"
    ).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("-is_primary"),
            to_attr="ordered_images"
        ),
        "attributes"
    )

    for product in products:
        if (product.discount_price and product.price and product.discount_price < product.price):
            product.discount_percentage = round(((product.price - product.discount_price) / product.price) * 100)
        else:
            product.discount_percentage = 0

    categories = Category.objects.filter(
        parent__isnull=True,
        is_active=True
    ).prefetch_related(
        Prefetch(
            "category_set",
            queryset=Category.objects.filter(is_active=True)
        )
    )

    context = {
        "meta_title": subcategory.meta_title,
        "meta_description": subcategory.meta_description,
        "meta_keywords": "",
        "category": category,
        "subcategory": subcategory,
        "products": products,
        "categories": categories
    }
    return render(request, 'web/products/subcategory.html', context)

def ProductsByCollection(request, slug):
    collection = get_object_or_404(
        Collection.objects.select_related(
            "category",
            "category__parent"
        ),
        slug=slug,
        is_active=True
    )
    subcategory = collection.category
    category = subcategory.parent if subcategory and subcategory.parent else None

    other_collections = Collection.objects.filter(
        category=subcategory,
        is_active=True
    ).exclude(
        id=collection.id
    ).only(
        "name",
        "slug",
        "image"
    )

    categories = Category.objects.filter(
        parent__isnull=True,
        is_active=True
    ).prefetch_related(
        Prefetch(
            "category_set",
            queryset=Category.objects.filter(is_active=True)
        )
    )

    is_gifting_collection = (
        subcategory
        and subcategory.parent
        and subcategory.parent.slug == "gifting-items"
    )

    if is_gifting_collection:
        gifting_products = GiftingCollectionProduct.objects.filter(
            collection=collection,
            is_active=True,
            product__is_active=True
        ).select_related(
            "product",
            "product__category",
            "product__collection",
            "product__vendor",
            "product__inventory"
        ).prefetch_related(
            Prefetch(
                "product__images",
                queryset=ProductImage.objects.order_by("-is_primary"),
                to_attr="ordered_images"
            ),
            "product__attributes"
        ).order_by(
            "sort_order",
            "-created_at"
        )

        products = [item.product for item in gifting_products]
    else:
        products = Product.objects.filter(
            is_active=True,
            collection=collection
        ).select_related(
            "category",
            "collection",
            "vendor",
            "inventory"
        ).prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("-is_primary"),
                to_attr="ordered_images"
            ),
            "attributes"
        )

    for product in products:
        if (product.discount_price and product.price and product.discount_price < product.price):
            product.discount_percentage = round(((product.price - product.discount_price) / product.price) * 100)
        else:
            product.discount_percentage = 0

    context = {
        "meta_title": collection.meta_title,
        "meta_description": collection.meta_description,
        "meta_keywords": "",
        "categories": categories,
        "category": category,
        "subcategory": subcategory,
        "collection": collection,
        "other_collections": other_collections,
        "products": products,
    }
    return render(request, 'web/products/collection.html', context)

def ProductsPremiumCollection(request):
    products = Product.objects.filter(
        is_active=True,
        price__gt=50000
    ).select_related(
        "category",
        "vendor",
        "collection",
        "inventory"
    ).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("-is_primary"),
            to_attr="ordered_images"
        ),
        "attributes"
    )

    for product in products:
        if (product.discount_price and product.price and product.discount_price < product.price):
            product.discount_percentage = round(((product.price - product.discount_price) / product.price) * 100)
        else:
            product.discount_percentage = 0

    categories = Category.objects.filter(
        parent__isnull=True,
        is_active=True
    ).prefetch_related(
        Prefetch(
            "category_set",
            queryset=Category.objects.filter(is_active=True)
        )
    )

    context = {
        "meta_title": "Premium Brass Idols India | VedaBrass",
        "meta_description": "Browse luxury brass handicrafts online at VedaBrass with exquisite brass idols, sculptures, and decore handcrafted for timeless elegance.",
        "meta_keywords": "",
        "categories": categories,
        "products": products,
        "faqs": get_page_faqs(request)
    }
    return render(request, 'web/products/premium.html', context)

def ProductDetails(request, slug):
    product = get_object_or_404(
        Product.objects.select_related(
            "category",
            "category__parent",
            "collection",
            "vendor",
            "inventory"
        ).prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("-is_primary"),
                to_attr="ordered_images"
            ),
            "attributes",
            "tags",
            Prefetch(
                "reviews",
                queryset=Review.objects.filter(
                    is_approved=True
                ).select_related("customer")
            )
        ),
        slug=slug,
        is_active=True
    )

    if product.discount_price and product.price and product.discount_price < product.price:
        product.discount_percentage = round(((product.price - product.discount_price) / product.price) * 100)
    else:
        product.discount_percentage = 0

    subcategory = product.category
    category = subcategory.parent if subcategory and subcategory.parent else None

    # First priority: same collection
    related_products = list(
        Product.objects.filter(
            collection=product.collection,
            is_active=True
        ).exclude(
            id=product.id
        ).prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("-is_primary"),
                to_attr="ordered_images"
            )
        )[:8]
    )

    remaining = 8 - len(related_products)

    # Second priority: same category
    if remaining > 0:
        existing_ids = [p.id for p in related_products] + [product.id]

        fallback_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(
            id__in=existing_ids
        ).prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("-is_primary"),
                to_attr="ordered_images"
            )
        )[:remaining]

        related_products.extend(fallback_products)

    for related in related_products:
        if (
            related.discount_price
            and related.price
            and related.discount_price < related.price
        ):
            related.discount_percentage = round(
                ((related.price - related.discount_price) / related.price) * 100
            )
        else:
            related.discount_percentage = 0

    bundle = ProductBundle.objects.filter(
        is_active=True,
        products=product
    ).prefetch_related(
        Prefetch(
            "products",
            queryset=Product.objects.prefetch_related(
                Prefetch(
                    "images",
                    queryset=ProductImage.objects.order_by("-is_primary"),
                    to_attr="ordered_images"
                )
            )
        )
    ).first()

    related_title = "Related Products"
    related_url = None
    related_url_text = "View All"

    if product.collection:
        related_title = f"More from {product.collection.name}"
        related_url = product.collection.get_absolute_url()
    elif product.category:
        related_title = f"More from {product.category.name}"
        related_url = product.category.get_absolute_url()
    elif product.category and product.category.parent:
        related_title = f"More from {product.category.parent.name}"
        related_url = product.category.parent.get_absolute_url()
    
    context = {
        "meta_title": product.meta_title,
        "meta_description": product.meta_description,
        "meta_keywords": "",
        "faqs": get_page_faqs(request, product=product),
        "product": product,
        "category": category,
        "subcategory": subcategory,
        "related_products": related_products,
        "bundle": bundle,
        "bundle_products": bundle.products.all() if bundle else [],

        "related_title": related_title,
        "related_url": related_url,
        "related_url_text": related_url_text,
    }
    return render(request, 'web/products/product-details.html', context)

def AddToCart(request, slug):
    if request.method != "POST":
        return JsonResponse({
            "success": False
        })

    product = get_object_or_404(
        Product,
        unique_code=slug,
        is_active=True
    )

    cart = get_cart(request)
    request.session["cart_id"] = cart.id
    request.session.modified = True

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={
            "quantity": 1
        }
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    cart_count = sum(
        item.quantity
        for item in cart.items.all()
    )

    return JsonResponse({"success": True,"cart_count": cart_count})

def Carts(request):
    cart = get_cart(request)
    cart_items = cart.items.select_related(
        "product"
    ).prefetch_related(
        Prefetch(
            "product__images",
            queryset=ProductImage.objects.order_by("-is_primary"),
            to_attr="ordered_images"
        )
    )

    subtotal = 0

    for item in cart_items:
        price = (
            item.product.discount_price
            if item.product.discount_price
            else item.product.price
        )

        item.total = price * item.quantity
        subtotal += item.total

    product_ids = cart_items.values_list("product_id", flat=True)

    bundles = ProductBundle.objects.filter(
        is_active=True,
        products__id__in=product_ids
    ).distinct().prefetch_related("products")

    context = {
        "meta_title": "Buy Brass Idols Online India | VedaBrass",
        "meta_description": "Explore handcrafted brass products India from VedaBrass. Shop authentic brass idols, home decore, pooja items, and gifts with trusted quality and delivery across India.",
        "meta_keywords": "",
        "cart": cart,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "total": subtotal,
        "bundles": bundles
    }
    return render(request, "web/products/cart.html", context)

def UpdateCart(request, code):
    if request.method != "POST":
        return JsonResponse({"success": False})

    cart = get_cart(request)

    item = get_object_or_404(
        CartItem,
        id=code,
        cart=cart
    )

    action = request.POST.get("action")

    if action == "plus":
        item.quantity += 1
        item.save()

    elif action == "minus":
        item.quantity -= 1

        if item.quantity <= 0:
            item.delete()
        else:
            item.save()

    subtotal = cart_totals(cart)

    cart_count = sum(
        item.quantity for item in cart.items.all()
    )

    return JsonResponse({
        "success": True,
        "quantity": item.quantity if item.id else 0,
        "subtotal": str(subtotal),
        "total": str(subtotal),
        "cart_count": cart_count
    })

def AddBundleToCart(request, slug):
    if request.method != "POST":
        return JsonResponse({
            "success": False
        })
    
    bundle = get_object_or_404(ProductBundle, slug=slug, is_active=True)

    cart = get_cart(request)
    request.session["cart_id"] = cart.id
    request.session.modified = True

    added_count = 0

    for product in bundle.products.filter(is_active=True):

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": 1}
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        added_count += 1

    cart_count = sum(item.quantity for item in cart.items.all())

    return JsonResponse({
        "success": True,
        "cart_count": cart_count,
        "added_items": added_count
    })

def RemoveFromCart(request, code):
    if request.method != "POST":
        return JsonResponse({"success": False})

    cart = get_cart(request)

    item = get_object_or_404(
        CartItem,
        id=code,
        cart=cart
    )

    item.delete()

    subtotal = cart_totals(cart)

    cart_count = sum(
        item.quantity for item in cart.items.all()
    )

    return JsonResponse({
        "success": True,
        "subtotal": str(subtotal),
        "total": str(subtotal),
        "cart_count": cart_count
    })

def CheckOut(request):
    cart = get_cart(request)

    cart_items = cart.items.select_related(
        "product"
    ).prefetch_related(
        Prefetch(
            "product__images",
            queryset=ProductImage.objects.order_by("-is_primary"),
            to_attr="ordered_images"
        )
    )

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("Cart")

    subtotal = 0

    for item in cart_items:
        price = item.product.discount_price or item.product.price
        item.price = price
        item.total = price * item.quantity
        subtotal += item.total

    context = {
        "meta_title": "Buy Brass Idols Online India | VedaBrass",
        "meta_description": "Explore handcrafted brass products India from VedaBrass. Shop authentic brass idols, home decore, pooja items, and gifts with trusted quality and delivery across India.",
        "meta_keywords": "",
        "cart": cart,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping": 0,
        "total": subtotal,
    }
    return render(request, 'web/products/checkout.html', context)

def PlaceOrder(request):
    if request.method != "POST":
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    cart = get_cart(request)
    cart_items = cart.items.select_related("product").all()

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("Cart")

    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    mobile = request.POST.get("mobile", "").strip()
    company_name = request.POST.get("company_name", "").strip() or None
    gst_number = request.POST.get("gst_number", "").strip() or None
    same_as_billing = request.POST.get("same_as_billing") == "on"

    if not name or not email or not mobile:
        messages.error(request, "Customer details are required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        with transaction.atomic():
            customer, created = Customer.objects.get_or_create(
                email=email,
                defaults={
                    "name": name,
                    "mobile": mobile,
                    "company_name": company_name,
                    "gst_number": gst_number,
                }
            )

            if not created:
                customer.name = name
                customer.mobile = mobile
                customer.company_name = company_name
                customer.gst_number = gst_number
                customer.save()

            billing_address = CustomerAddress.objects.create(
                customer=customer,
                address_type="Billing",
                address_line_1=request.POST.get("billing_address_line_1"),
                address_line_2=request.POST.get("billing_address_line_2") or None,
                landmark=request.POST.get("billing_landmark") or None,
                city=request.POST.get("billing_city"),
                state=request.POST.get("billing_state"),
                country=request.POST.get("billing_country") or "India",
                postal_code=request.POST.get("billing_postal_code"),
            )

            if same_as_billing:
                shipping_address = CustomerAddress.objects.create(
                    customer=customer,
                    address_type="Shipping",
                    address_line_1=billing_address.address_line_1,
                    address_line_2=billing_address.address_line_2,
                    landmark=billing_address.landmark,
                    city=billing_address.city,
                    state=billing_address.state,
                    country=billing_address.country,
                    postal_code=billing_address.postal_code,
                )
            else:
                shipping_address = CustomerAddress.objects.create(
                    customer=customer,
                    address_type="Shipping",
                    address_line_1=request.POST.get("shipping_address_line_1"),
                    address_line_2=request.POST.get("shipping_address_line_2") or None,
                    landmark=request.POST.get("shipping_landmark") or None,
                    city=request.POST.get("shipping_city"),
                    state=request.POST.get("shipping_state"),
                    country=request.POST.get("shipping_country") or "India",
                    postal_code=request.POST.get("shipping_postal_code"),
                )

            subtotal = Decimal("0.00")

            for item in cart_items:
                price = item.product.discount_price or item.product.price
                subtotal += price * item.quantity

            shipping = Decimal("0.00")
            total = subtotal + shipping

            order_id = generate_order_id(cart_items)

            order = Order.objects.create(
                customer=customer,
                cart=cart,
                billing_address=billing_address,
                shipping_address=shipping_address,
                order_id=order_id,
                subtotal=subtotal,
                shipping=shipping,
                total=total,
                status="Pending",
                payment_status="Pending",
                shipment_status="Pending",
            )

            for item in cart_items:
                price = item.product.discount_price or item.product.price

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=price,
                    total=price * item.quantity
                )

            cart.customer = customer
            cart.save(update_fields=["customer"])

        return redirect("PayURedirect", order_id=order.order_id)
    except Exception as e:
        print("PLACE ORDER ERROR:", e)
        messages.error(request,f"Something went wrong: {e}")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def PayURedirect(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    customer = order.customer
    amount = f"{order.total:.2f}"
    productinfo = (f"Vedabrass Order {order.order_id}")
    payu_txnid = f"{order.order_id}-{uuid.uuid4().hex[:8]}"

    order.payu_txnid = payu_txnid
    order.save(update_fields=["payu_txnid"])

    payu_hash = generate_payu_hash(
        settings.PAYU_KEY,
        payu_txnid,
        amount,
        productinfo,
        customer.name,
        customer.email,
        settings.PAYU_SALT,
    )

    payu_data = {
        "key": settings.PAYU_KEY,
        "txnid": payu_txnid,
        "amount": amount,
        "productinfo": productinfo,
        "firstname": customer.name,
        "email": customer.email,
        "phone": customer.mobile,
        "surl": request.build_absolute_uri(reverse("PayUSuccess")),
        "furl": request.build_absolute_uri(reverse("PayUFailure")),
        "hash": payu_hash,
    }

    context = {
        "payu_url": settings.PAYU_BASE_URL,
        "payu_data": payu_data,
        "order": order,
    }
    return render(request, "web/products/payu-redirect.html", context)

@csrf_exempt
def PayUSuccess(request):
    order = None
    try:
        response_data = request.POST
        payu_txnid = response_data.get("txnid")
        order = Order.objects.filter(payu_txnid=payu_txnid).first()

        if request.method != "POST":
            return redirect("Products")

        if not order:
            messages.error(request, "Order not found.")
            return redirect("Products")

        if not verify_payu_response_hash(response_data, settings.PAYU_SALT):
            order.payment_status = "Failed"
            order.status = "Cancelled"
            order.payment_response = response_data.dict()
            order.save()
            return redirect("PaymentFailed", code=order.unique_code)

        if order.payment_status == "Paid":
            return redirect("ThankYou", code=order.unique_code)

        order.payment_status = "Paid"
        order.payment_mode = response_data.get("mode") or "PayU"
        order.payment_id = response_data.get("mihpayid")
        order.payu_mihpayid = response_data.get("mihpayid")
        order.payment_response = response_data.dict()
        order.status = "Confirmed"
        order.save()

        clear_paid_cart(order, request)
        generate_invoice_number(order)
        send_order_notification(order, ORDER_PAID)

        try:
            shiprocket_response = create_shiprocket_order(order)

            if shiprocket_response.get("shipment_id"):
                order.shiprocket_order_id = str(shiprocket_response.get("order_id", ""))
                order.shiprocket_shipment_id = str(shiprocket_response.get("shipment_id", ""))
                order.shiprocket_response = shiprocket_response
                order.shipment_status = "Shiprocket Order Created"
                order.save()
            else:
                order.shiprocket_response = shiprocket_response
                order.shipment_status = "Shiprocket Order Failed"
                order.save()

        except Exception as shiprocket_error:
            print("SHIPROCKET ORDER CREATE ERROR:", shiprocket_error)

        messages.success(request, "Payment successful.")
        return redirect("ThankYou", code=order.unique_code)
    except Exception as e:
        print("PAYU SUCCESS ERROR:", e)

        if order:
            return redirect("PaymentFailed", code=order.unique_code)

        return redirect("Products")

@csrf_exempt
def PayUFailure(request):
    try:
        if request.method != "POST":
            return redirect("Products")
        
        payu_txnid = request.POST.get("txnid")
        order = None

        if payu_txnid:
            order = Order.objects.filter(payu_txnid=payu_txnid).first()

            if order and order.payment_status != "Paid":
                order.payment_status = "Failed"
                order.status = "Cancelled"
                order.payment_response = request.POST.dict()
                order.save()

        if order:
            return redirect("PaymentFailed", code=order.unique_code)

        messages.error(request, "Payment failed.")
        return redirect("Products")
    except Exception as e:
        print("PAYU FAILURE ERROR:", e)
        return redirect("Products")
    
def PaymentFailed(request, code):
    order = get_object_or_404(Order, unique_code=code)

    context = {
        "meta_title": "Buy Brass Idols Online India | VedaBrass",
        "meta_description": "Explore handcrafted brass products India from VedaBrass. Shop authentic brass idols, home decore, pooja items, and gifts with trusted quality and delivery across India.",
        "meta_keywords": "",
        "order": order,
    }
    return render(request, "web/products/payment-failed.html", context)

def ThankYou(request, code):
    order = get_object_or_404(
        Order.objects.select_related(
            "customer",
            "billing_address",
            "shipping_address"
        ).prefetch_related(
            "items",
            "items__product",
            Prefetch(
                "items__product__images",
                queryset=ProductImage.objects.order_by("-is_primary"),
                to_attr="ordered_images"
            )
        ),
        unique_code=code
    )
    
    first_item = order.items.first()
    ordered_product_ids = order.items.values_list("product_id", flat=True)

    recommended_products = Product.objects.none()

    if first_item and first_item.product and first_item.product.category:
        category = first_item.product.category
        parent_category = first_item.product.category.parent

        if parent_category:
            recommended_products = Product.objects.filter(
                is_active=True,
                category__parent=parent_category
            )
        else:
            recommended_products = Product.objects.filter(
                is_active=True,
                category=category
            )

        recommended_products = recommended_products.exclude(
            id__in=ordered_product_ids
        ).prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("-is_primary"),
                to_attr="ordered_images"
            )
        )[:4]

        for product in recommended_products:
            if product.discount_price and product.price and product.discount_price < product.price:
                product.discount_percentage = round(
                    ((product.price - product.discount_price) / product.price) * 100
                )
            else:
                product.discount_percentage = 0
    
    context = {
        "meta_title": "Buy Brass Idols Online India | VedaBrass",
        "meta_description": "Explore handcrafted brass products India from VedaBrass. Shop authentic brass idols, home decore, pooja items, and gifts with trusted quality and delivery across India.",
        "meta_keywords": "",
        "order": order,
        "recommended_products": recommended_products
    }
    return render(request, 'web/thank-you.html', context)

def TrackOrder(request, code=None):
    order = None

    order_queryset = Order.objects.select_related(
        "customer",
        "billing_address",
        "shipping_address"
    ).prefetch_related(
        Prefetch(
            "items",
            queryset=OrderItem.objects.select_related(
                "product"
            ).prefetch_related(
                Prefetch(
                    "product__images",
                    queryset=ProductImage.objects.order_by("-is_primary"),
                    to_attr="ordered_images"
                )
            )
        )
    )

    if code:
        order = order_queryset.filter(
            unique_code=code
        ).first()

    elif request.method == "POST":
        order_id = request.POST.get("order_id", "").strip()

        order = order_queryset.filter(
            unique_code=order_id
        ).first()

        if not order:
            messages.error(request, "No order found.")
    
    context = {
        "meta_title": "Buy Brass Idols Online India | VedaBrass",
        "meta_description": "Explore handcrafted brass products India from VedaBrass. Shop authentic brass idols, home decore, pooja items, and gifts with trusted quality and delivery across India.",
        "meta_keywords": "",
        "order": order
    }
    return render(request, 'web/track-order.html', context)

def InvoiceView(request, invoice_number):
    order = get_object_or_404(
        Order.objects.select_related(
            "customer",
            "billing_address",
            "shipping_address"
        ).prefetch_related("items__product"),
        invoice_number=invoice_number,
        is_deleted=False,
        payment_status="Paid"
    )

    context = {
        "meta_title": "Buy Brass Idols Online India | VedaBrass",
        "meta_description": "Explore handcrafted brass products India from VedaBrass. Shop authentic brass idols, home decore, pooja items, and gifts with trusted quality and delivery across India.",
        "meta_keywords": "",
        "order": order,
        "customer": order.customer,
        "billing_address": order.billing_address,
        "shipping_address": order.shipping_address,
        "order_items": order.items.select_related("product"),
    }
    return render(request, "web/products/invoice.html", context)

def Contact(request):
    if request.method != 'POST':
        context = {
            "meta_title": "VedaBrass Hyderabad | Contact VedaBrass",
            "meta_description": "Get in touch using our contact brass store Kondapur details. Reach VedaBrass for product enquiries, orders, and customer support.",
            "meta_keywords": "",
        }
        return render(request, 'web/contact.html', context)
    
    name = request.POST.get("name", "").strip()
    mobile = request.POST.get("mobile", "").strip()
    email = request.POST.get("email", "").strip() or None
    subject = request.POST.get("subject", "").strip()
    message_text = request.POST.get("message", "").strip()

    if not name or not mobile or not subject or not message_text:
        messages.error(request, "Please fill all required fields.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    ContactInquiry.objects.create(
        name=name,
        mobile=mobile,
        email=email,
        subject=subject,
        message=message_text
    )

    messages.success(request, "Your message has been submitted successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def ShippingPolicy(request):
    context = {
        "meta_title": "Vedabrass | Shipping Policy",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'web/policies/shipping.html', context)

def ReturnPolicy(request):
    context = {
        "meta_title": "Vedabrass | Return Policy",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'web/policies/return.html', context)

def PrivacyPolicy(request):
    context = {
        "meta_title": "Vedabrass | Privacy Policy",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'web/policies/privacy.html', context)

def TermsUse(request):
    context = {
        "meta_title": "Vedabrass | Terms of Use",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'web/policies/terms.html', context)

def Blogs(request):
    blogs = Blog.objects.filter(is_active=True).select_related("category").order_by("-created_at")
    featured_blog = blogs.filter(is_featured=True).first()
    categories = BlogCategory.objects.filter(is_active=True)

    context = {
        "meta_title": "Brass Idol Care Tips India | VedaBrass",
        "meta_description": "Learn how to clean brass idols with expert care guides, maintenance tips, and practical advice to keep your brass products shining for years.",
        "meta_keywords": "",
        "blogs": blogs,
        "featured_blog": featured_blog,
        "categories": categories,
    }
    return render(request, 'web/blogs/all.html', context)

def CategoryBlogs(request, slug):
    category = get_object_or_404(BlogCategory, slug=slug, is_active=True)
    blogs = Blog.objects.filter(is_active=True, category=category).order_by("-created_at")
    featured_blog = blogs.filter(is_featured=True).first()
    categories = BlogCategory.objects.filter(is_active=True)

    context = {
        "meta_title": "Brass Idol Care Tips India | VedaBrass",
        "meta_description": "Learn how to clean brass idols with expert care guides, maintenance tips, and practical advice to keep your brass products shining for years.",
        "meta_keywords": "",
        "blogs": blogs,
        "featured_blog": featured_blog,
        "categories": categories,
    }
    return render(request, 'web/blogs/category.html', context)

def BlogDetails(request, slug):
    blog = get_object_or_404(Blog.objects.select_related("category"), slug=slug, is_active=True)
    related_blogs = Blog.objects.filter(is_active=True, category=blog.category).exclude(id=blog.id)[:3]
    latest_blogs = Blog.objects.filter(is_active=True).exclude(id=blog.id).order_by("-created_at")[:5]

    context = {
        "meta_title": blog.meta_title,
        "meta_description": blog.meta_description,
        "meta_keywords": blog.meta_keywords,
        "blog": blog,
        "related_blogs": related_blogs,
        "latest_blogs": latest_blogs,
    }
    return render(request, "web/blogs/details.html",context)

def CuratedBundles(request):
    bundles = (
        ProductBundle.objects
        .filter(is_active=True)
        .prefetch_related(
            "products",
            "products__images"
        )
    )

    enriched_bundles = []

    for bundle in bundles:
        products = bundle.products.all()

        # fallback pricing from products
        total_price = sum((p.price for p in products), Decimal("0.00"))
        total_discount = sum(
            (p.discount_price if p.discount_price else p.price for p in products),
            Decimal("0.00")
        )

        final_price = bundle.bundle_price or total_price
        final_discounted_price = bundle.discounted_bundle_price or total_discount

        savings = final_price - final_discounted_price if final_price and final_discounted_price else Decimal("0.00")

        discount_percent = 0
        if final_price and final_price > 0:
            discount_percent = (savings / final_price) * 100

        bundle.final_price = final_price
        bundle.final_discounted_price = final_discounted_price
        bundle.savings = savings
        bundle.discount_percent = discount_percent

        enriched_bundles.append(bundle)

    context = {
        "meta_title": "Brass Combo Sets India | VedaBrass",
        "meta_description": "Browse curated brass bundles online featuring thoughtfully paired brass idols, decore, and gifting combinations for every occasion.",
        "meta_keywords": "",
        "bundles": enriched_bundles,
        "faqs": get_page_faqs(request)
    }
    return render(request, 'web/products/bundles.html', context)

def CuratedBundleDetails(request, slug):
    context = {
        "meta_title": "",
        "meta_description": "",
        "meta_keywords": "",
    }
    return render(request, 'web/products/bundle-details.html', context)

def NewsEvents(request):
    news_events = NewsEvent.objects.filter(
        is_active=True
    ).select_related(
        "product",
        "bundle"
    ).order_by("-created_at")

    timeline_events = news_events[:12]

    context = {
        "meta_title": "VedaBrass News and Events | VedaBrass",
        "meta_description": "Stay updated with brass store events Hyderabad, product launches, exhibitions, and the latest news from VedaBrass.",
        "meta_keywords": "",
        "news_events": news_events,
        "timeline_events": timeline_events,
        "platforms": NewsEvent.PLATFORM_CHOICES,
    }
    return render(request, 'web/news.html', context)

def NewsReels(request):
    page = int(request.GET.get("page", 1))
    platform = request.GET.get("platform")
    reels = NewsEvent.objects.filter(is_active=True)

    if platform and platform != "all":
        reels = reels.filter(platform=platform)

    reels = reels.order_by("-created_at")
    paginator = Paginator(reels, 9)
    page_obj = paginator.get_page(page)
    data = []

    for item in page_obj:
        data.append({
            "id": item.id,
            "title": item.title,
            "media_type": item.media_type,
            "media_url": item.media_url,
            "description": item.description,
            "platform": item.get_platform_display(),
            "external_url": item.external_url,
            "product_url":
                item.product.slug
                if item.product else None,
            "bundle_url":
                item.bundle.slug
                if item.bundle else None,
        })

    return JsonResponse({
        "results": data,
        "has_next": page_obj.has_next()
    })

def ReelsTrack(request):
    if request.method == "POST":
        reel = get_object_or_404(
            NewsEvent,
            id=id
        )

        reel.views += 1

        reel.save(
            update_fields=["views"]
        )

        return JsonResponse({
            "success": True
        })

def Faqs(request):
    faqs = FAQ.objects.filter(is_active=True).select_related("product")

    context = {
        "meta_title": "VedaBrass FAQs | VedaBrass",
        "meta_description": "Find answers to brass idol care questions, ordering, shipping, maintenance, and other frequently asked questions at VedaBrass.",
        "meta_keywords": "",
        "faqs": faqs
    }
    return render(request, 'web/faqs.html', context)

def Reviews(request):
    reviews = Review.objects.filter(
        is_approved=True,
        is_featured=True
    ).select_related(
        "product",
        "customer"
    ).order_by(
        "featured_order",
        "-created_at"
    )
        
    context = {
        "meta_title": "VedaBrass Customer Reviews | VedaBrass",
        "meta_description": "Read brass idol reviews India from happy customers and discover why VedaBrass is trusted for premium handcrafted brass products.",
        "meta_keywords": "",
        "reviews": reviews,
        "total_reviews": reviews.count(),
        "reviewed_products": reviews.values("product").distinct().count(),
        "average_rating": round(
            reviews.aggregate(
                Avg("rating")
            )["rating__avg"] or 0,
            1
        ),
    }
    return render(request, 'web/reviews.html', context)

def Subscribe(request):
    if request.method != "POST":
        return redirect(request.META.get("HTTP_REFERER"))

    email = request.POST.get("semail", "").strip()

    if not email:
        messages.error(request, "Please enter your email address.")
        return redirect(request.META.get("HTTP_REFERER"))

    subscriber, created = Subscriber.objects.get_or_create(
        email=email
    )

    if created:
        messages.success(request, "Thank you for subscribing to Vedabrass.")
    else:
        messages.info(request, "You are already subscribed.")

    return redirect(request.META.get("HTTP_REFERER"))

def SubmitReview(request):
    if request.method != "POST":
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    product_code = request.POST.get("product", "").strip()
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    mobile = request.POST.get("mobile", "").strip()
    title = request.POST.get("title", "").strip()
    rating = request.POST.get("rating", "").strip()
    comment = request.POST.get("comment", "").strip()
    image = request.FILES.get("image")

    if not product_code:
        messages.error(request, "Product is required.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    if not name or not email or not mobile:
        messages.error(request, "Name, email and mobile are required.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    if not title or not rating or not comment:
        messages.error(request, "Rating, title and comment are required.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    product = get_object_or_404(
        Product,
        unique_code=product_code,
        is_active=True
    )

    try:
        rating = int(rating)

        if rating < 1 or rating > 5:
            messages.error(request, "Rating must be between 1 and 5.")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    except (TypeError, ValueError):
        messages.error(request, "Invalid rating.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    customer, created = Customer.objects.get_or_create(
        email=email,
        defaults={
            "name": name,
            "mobile": mobile,
        }
    )

    if not created:
        customer.name = name
        customer.mobile = mobile
        customer.save(update_fields=["name", "mobile"])

    Review.objects.create(
        product=product,
        customer=customer,
        title=title,
        rating=rating,
        comment=comment,
        image=image,
        is_approved=False
    )

    messages.success(request, "Review submitted successfully. It will appear after admin approval.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@require_POST
def ChatbotReply(request):
    message = request.POST.get("message", "").strip()

    if not message:
        return JsonResponse({
            "reply": "Please enter a message."
        })

    chat_session = SessionManagerV2.get_or_create_session(request)

    SessionManagerV2.log_message(
        chat_session=chat_session,
        sender="user",
        message=message,
        state=chat_session.current_state
    )

    result = StateEngineV2.handle(
        chat_session=chat_session,
        message=message
    )

    SessionManagerV2.log_search(
        request=request,
        chat_session=chat_session,
        query=message,
        result=result,
    )

    SessionManagerV2.log_message(
        chat_session=chat_session,
        sender="bot",
        message=result.get("reply", ""),
        intent=result.get("intent"),
        state=chat_session.current_state
    )

    return JsonResponse(result)

def SignUp(request):
    if request.method != 'POST':
        return render(request, 'auth/register.html')
    
    try:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not all([first_name, last_name, email, password]):
            messages.error(request, "Please provide all the details")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with the given email already exists")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        account = User(
            username=email,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=make_password(password),
        )
        account.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except Exception as e:
        traceback.print_exc()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def SignIn(request):
    if request.method != 'POST':
        return render(request, 'auth/login.html')
    
    try:
        email = request.POST.get("email")
        password = request.POST.get("password")

        auths = authenticate(request, username=email, password=password)

        user = User.objects.filter(email=email).first()
        
        if not user:
            messages.error(request, "Invalid credentials")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        login(request, user)
        return redirect(AdminDashboard, user.unique_code)
    except Exception as e:
        traceback.print_exc()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminError400(request, exception=None):
    return render(request, 'errors/admin/400.html', status=400)

@login_required
def AdminError403(request, exception=None):
    return render(request, 'errors/admin/403.html', status=403)

@login_required
def AdminError404(request, exception=None):
    return render(request, 'errors/admin/404.html', status=404)

@login_required
def AdminError405(request, exception=None):
    return render(request, 'errors/admin/405.html', status=405)

@login_required
def AdminError408(request, exception=None):
    return render(request, 'errors/admin/408.html', status=408)

@login_required
def AdminError419(request, exception=None):
    return render(request, 'errors/admin/419.html', status=419)

@login_required
def AdminError500(request, exception=None):
    return render(request, 'errors/admin/500.html', status=500)

@login_required
def AdminError503(request, exception=None):
    return render(request, 'errors/admin/503.html', status=503)

@login_required
def AdminDashboard(request, code):
    today = datetime.today().date()
    month_start = today.replace(day=1)

    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status="Confirmed", shipment_status__in=["Pending", "Shiprocket Order Created"]).count()
    delivered_orders = Order.objects.filter(status="Delivered").count()

    total_revenue = Order.objects.filter(status="Delivered").aggregate(total=Sum("total"))["total"] or 0
    monthly_revenue = Order.objects.filter(
        created_at__date__gte=month_start
    ).exclude(
        status="Cancelled"
    ).aggregate(
        total=Sum("total")
    )["total"] or 0

    products_count = Product.objects.filter(is_active=True).count()
    customers_count = Customer.objects.count()
    pending_reviews = Review.objects.filter(is_approved=False).count()

    recent_orders = Order.objects.select_related("customer").order_by("-created_at")[:8]

    low_stock_products = ProductInventory.objects.select_related(
        "product"
    ).filter(
        quantity__lte=5
    ).order_by(
        "quantity"
    )[:8]

    top_products = OrderItem.objects.values(
        "product__name"
    ).annotate(
        total_sold=Sum("quantity"),
        revenue=Sum("total")
    ).order_by(
        "-total_sold"
    )[:5]

    abandoned_carts = Cart.objects.filter(
        is_completed=False,
        items__isnull=False,
        created_at__lte=datetime.now() - timedelta(minutes=30)
    ).distinct().count()

    context = {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "total_revenue": total_revenue,
        "monthly_revenue": monthly_revenue,
        "products_count": products_count,
        "customers_count": customers_count,
        "pending_reviews": pending_reviews,
        "recent_orders": recent_orders,
        "low_stock_products": low_stock_products,
        "top_products": top_products,
        "abandoned_carts": abandoned_carts,
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
def AdminOrders(request, code):
    orders = Order.objects.select_related(
        "customer",
        "billing_address",
        "shipping_address"
    ).prefetch_related(
        "items"
    ).order_by("-created_at")

    context = {
        "orders": orders
    }
    return render(request, 'admin/web/orders/all.html', context)

@login_required
def AdminViewOrder(request, code, cid):
    order = get_object_or_404(
        Order.objects.select_related(
            "customer",
            "billing_address",
            "shipping_address",
            "cart"
        ).prefetch_related(
            Prefetch(
                "items",
                queryset=OrderItem.objects.select_related(
                    "product"
                ).prefetch_related(
                    Prefetch(
                        "product__images",
                        queryset=ProductImage.objects.order_by("-is_primary"),
                        to_attr="ordered_images"
                    )
                )
            )
        ),
        unique_code=cid
    )
    logs = order.notification_logs.order_by(
        "-created_at"
    )

    context = {
        "order": order,
        "context_logs": logs
    }
    return render(request, "admin/web/orders/view.html", context)

def to_decimal(value, fallback="0.00"):
    try:
        return Decimal(str(value if value not in [None, ""] else fallback))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(fallback)
@login_required
def AdminEditOrder(request, code):
    order = get_object_or_404(
        Order.objects.select_related(
            "customer",
            "billing_address",
            "shipping_address"
        ),
        unique_code=code
    )

    is_shipment_created = bool(order.shiprocket_shipment_id)
    is_awb_assigned = bool(order.shiprocket_awb_code)

    if request.method != "POST":
        context = {
            "order": order,
            "is_shipment_created": is_shipment_created,
            "is_awb_assigned": is_awb_assigned,
        }
        return render(request, "admin/web/orders/edit.html", context)
    
    try:
        with transaction.atomic():
            order.status = request.POST.get("status") or order.status
            order.shipping = to_decimal(request.POST.get("shipping"), order.shipping)
            order.total = order.subtotal + order.shipping

            if not is_shipment_created and not is_awb_assigned:
                customer = order.customer

                if customer:
                    customer.name = request.POST.get("name", "").strip()
                    customer.email = request.POST.get("email", "").strip()
                    customer.mobile = request.POST.get("mobile", "").strip()
                    customer.company_name = request.POST.get("company_name", "").strip() or None
                    customer.gst_number = request.POST.get("gst_number", "").strip() or None
                    customer.save()

                billing = order.billing_address

                if billing:
                    billing.address_line_1 = request.POST.get("billing_address_line_1", "").strip()
                    billing.address_line_2 = request.POST.get("billing_address_line_2", "").strip() or None
                    billing.landmark = request.POST.get("billing_landmark", "").strip() or None
                    billing.city = request.POST.get("billing_city", "").strip()
                    billing.state = request.POST.get("billing_state", "").strip()
                    billing.country = request.POST.get("billing_country", "").strip() or "India"
                    billing.postal_code = request.POST.get("billing_postal_code", "").strip()
                    billing.save()

                shipping_address = order.shipping_address

                if shipping_address:
                    shipping_address.address_line_1 = request.POST.get("shipping_address_line_1", "").strip()
                    shipping_address.address_line_2 = request.POST.get("shipping_address_line_2", "").strip() or None
                    shipping_address.landmark = request.POST.get("shipping_landmark", "").strip() or None
                    shipping_address.city = request.POST.get("shipping_city", "").strip()
                    shipping_address.state = request.POST.get("shipping_state", "").strip()
                    shipping_address.country = request.POST.get("shipping_country", "").strip() or "India"
                    shipping_address.postal_code = request.POST.get("shipping_postal_code", "").strip()
                    shipping_address.save()
            else:
                messages.warning(request, "Customer and address details were not updated because shipment has already been created.")

            order.save()

        messages.success(request, "Order updated successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except Exception as e:
        messages.error(request, f"Something went wrong: {e}")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminCreateShipment(request, code):
    order = get_object_or_404(Order, unique_code=code)

    if order.payment_status != "Paid":
        messages.error(request, "Shipment can be created only for paid orders.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if order.shiprocket_shipment_id:
        messages.info(request, "Shiprocket order already exists.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        shiprocket_response = create_shiprocket_order(order)

        if shiprocket_response.get("shipment_id"):
            order.shiprocket_order_id = str(shiprocket_response.get("order_id", ""))
            order.shiprocket_shipment_id = str(shiprocket_response.get("shipment_id", ""))
            order.shiprocket_response = shiprocket_response
            order.shipment_status = "Shiprocket Order Created"
            order.save()

            messages.success(request, "Shiprocket order created successfully.")
        else:
            order.shiprocket_response = shiprocket_response
            order.shipment_status = "Shiprocket Order Failed"
            order.save()

            messages.error(request, shiprocket_response.get("message", "Shiprocket order creation failed."))
    except Exception as e:
        messages.error(request, f"Shiprocket error: {e}")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminAssignAWB(request, code):
    order = get_object_or_404(Order, unique_code=code)

    if not order.shiprocket_shipment_id:
        messages.error(request, "Shipment ID not found. Create Shiprocket order first.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if order.shiprocket_awb_code:
        messages.info(request, "AWB already assigned.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        awb_response = assign_awb(order.shiprocket_shipment_id)
        awb_data = awb_response.get("response", {}).get("data", {})
        awb_code = awb_data.get("awb_code")
        courier_name = awb_data.get("courier_name")

        if awb_code:
            order.shiprocket_awb_code = awb_code
            order.shiprocket_courier_name = courier_name
            order.shipment_status = "AWB Assigned"
            order.save()

            messages.success(request, "AWB assigned successfully.")
        else:
            messages.error(request, f"AWB not assigned: {awb_response}")
    except Exception as e:
        messages.error(request, f"AWB error: {e}")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminRefreshTracking(request, code):
    order = get_object_or_404(Order, unique_code=code)

    if not order.shiprocket_awb_code:
        messages.error(request, "AWB code not found.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        tracking_response = track_by_awb(order.shiprocket_awb_code)
        tracking_data = tracking_response.get("tracking_data", {})
        order.tracking_url = (
            tracking_data.get("track_url")
            or tracking_data.get("tracking_url")
            or order.tracking_url
        )
        shipment_status = (
            tracking_data.get("shipment_track", [{}])[0].get("current_status")
            if tracking_data.get("shipment_track")
            else None
        )

        if shipment_status:
            order.shipment_status = shipment_status

        order.save()

        messages.success(request, "Tracking refreshed successfully.")

    except Exception as e:
        messages.error(request, f"Tracking error: {e}")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminSendTrackingEmail(request, code):
    order = get_object_or_404(Order, unique_code=code)

    if not order.tracking_url:
        messages.error(request, "Tracking URL is not available yet.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    send_order_notification(order, TRACKING_AVAILABLE)

    messages.success(request, "Tracking email sent successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminGeneratePickup(request, code):
    order = get_object_or_404(Order, unique_code=code)

    if not order.shiprocket_shipment_id:
        messages.error(request, "Shipment ID not found.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        response = generate_pickup(order.shiprocket_shipment_id)
        order.shipment_status = "Pickup Scheduled"
        order.save(update_fields=["shipment_status"])

        messages.success(request, "Pickup generated successfully.")

    except Exception as e:
        messages.error(request, f"Pickup error: {e}")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminGenerateLabel(request, code):
    order = get_object_or_404(Order, unique_code=code)

    if not order.shiprocket_shipment_id:
        messages.error(request, "Shipment ID not found.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        response = generate_label(order.shiprocket_shipment_id)

        label_url = (
            response.get("label_url")
            or response.get("response", {}).get("label_url")
            or response.get("label_created")
        )

        if label_url:
            order.shiprocket_label_url = label_url
            order.save(update_fields=["shiprocket_label_url"])

        messages.success(request, "Label generated successfully.")

    except Exception as e:
        messages.error(request, f"Label error: {e}")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminGenerateInvoice(request, code):
    order = get_object_or_404(Order, unique_code=code)

    if not order.shiprocket_order_id:
        messages.error(request, "Shiprocket order ID not found.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        response = generate_invoice(order.shiprocket_order_id)

        invoice_url = (
            response.get("invoice_url")
            or response.get("invoice_url_print")
            or response.get("url")
        )

        if invoice_url:
            order.shiprocket_invoice_url = invoice_url
            order.save(update_fields=["shiprocket_invoice_url"])

        messages.success(request, "Invoice generated successfully.")

    except Exception as e:
        messages.error(request, f"Invoice error: {e}")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminViewInvoice(request, code):
    order = get_object_or_404(
        Order.objects.select_related(
            "customer",
            "billing_address",
            "shipping_address"
        ).prefetch_related("items__product"),
        unique_code=code,
        is_deleted=False
    )

    if order.payment_status != "Paid":
        messages.error(request, "Invoice is available only for paid orders.")
        return redirect("AdminViewOrder", code=order.unique_code, cid=order.customer.unique_code)

    if not order.invoice_number:
        messages.error(request, "Invoice number is not generated for this order.")
        return redirect("AdminViewOrder", code=order.unique_code, cid=order.customer.unique_code)

    context = {
        "order": order,
        "customer": order.customer,
        "billing_address": order.billing_address,
        "shipping_address": order.shipping_address,
        "order_items": order.items.select_related("product"),
    }

    return render(request, "admin/web/orders/invoice.html", context)

@login_required
def AdminEmailInvoice(request, code):
    order = get_object_or_404(
        Order.objects.select_related("customer"),
        unique_code=code,
        is_deleted=False
    )

    if order.payment_status != "Paid":
        messages.error(request, "Invoice can be emailed only for paid orders.")
        return redirect("AdminViewOrder", code=order.unique_code, cid=order.customer.unique_code)

    if not order.invoice_number:
        messages.error(request, "Invoice number is not generated for this order.")
        return redirect("AdminViewOrder", code=order.unique_code, cid=order.customer.unique_code)

    send_order_notification(order, INVOICE_AVAILABLE)

    messages.success(request, "Invoice email notification sent.")
    return redirect("AdminViewOrder", code=order.unique_code, cid=order.customer.unique_code)

@login_required
def AdminCancelOrder(request, code):
    if request.method != "POST":
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
    
    order = get_object_or_404(Order, unique_code=request.POST.get("order_id"))

    if order.status == "Delivered":
        messages.error(request, "Delivered orders cannot be cancelled.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    order.status = "Cancelled"
    order.save(update_fields=["status"])

    send_order_notification(
        order,
        ORDER_CANCELLED
    )

    messages.success(request, "Order cancelled successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteOrder(request, code):
    if request.method != "POST":
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    order = get_object_or_404(Order, unique_code=request.POST.get("order_id"))

    if (order.payment_status == "Paid" or order.shiprocket_shipment_id or order.shiprocket_awb_code):
        messages.error(request, "Paid or shipped orders cannot be deleted. Cancel the order instead.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    order.is_deleted = True
    order.save(update_fields=["is_deleted"])

    messages.success(request, "Order deleted successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminCustomers(request, code):
    customers = Customer.objects.all().order_by("-created_at")

    context = {
        "customers": customers
    }
    return render(request, 'admin/web/customers/all.html', context)

@login_required
def AdminViewCustomer(request, code, ccode):
    customer = get_object_or_404(
        Customer.objects.prefetch_related(
            "addresses",
            "orders"
        ),
        unique_code=ccode
    )

    context = {
        "customer": customer
    }
    return render(request, "admin/web/customers/view.html", context)

@login_required
def AdminEditCustomer(request, code):
    customer = get_object_or_404(Customer, unique_code=code)

    if request.method != "POST":
        context = {
            "customer": customer
        }
        return render(request, "admin/web/customers/edit.html", context)

    customer.name = request.POST.get("name", "").strip()
    customer.email = request.POST.get("email", "").strip()
    customer.mobile = request.POST.get("mobile", "").strip()
    customer.company_name = request.POST.get("company_name", "").strip() or None
    customer.gst_number = request.POST.get("gst_number", "").strip() or None
    customer.save()

    messages.success(request, "Customer updated successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminEditCustomerAddress(request, code):
    address = get_object_or_404(
        CustomerAddress.objects.select_related("customer"),
        unique_code=code
    )

    if request.method != "POST":
        context = {
            "address": address,
            "customer": address.customer
        }
        return render(request, "admin/customers/address-edit.html", context)

    address.address_line_1 = request.POST.get("address_line_1", "").strip()
    address.address_line_2 = request.POST.get("address_line_2", "").strip() or None
    address.landmark = request.POST.get("landmark", "").strip() or None
    address.city = request.POST.get("city", "").strip()
    address.state = request.POST.get("state", "").strip()
    address.country = request.POST.get("country", "").strip() or "India"
    address.postal_code = request.POST.get("postal_code", "").strip()
    address.address_type = request.POST.get("address_type", address.address_type)
    address.is_default = request.POST.get("is_default") == "on"
    address.save()

    messages.success(request, "Address updated successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteCustomer(request, code):
    if request.method == "POST":
        customer_id = request.POST.get("customer_id")
        customer = get_object_or_404(Customer, unique_code=customer_id)
        customer.delete()

        messages.success(request, "Customer deleted successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminProductReviews(request, code):
    reviews = Review.objects.select_related(
        "product",
        "customer"
    ).order_by("-created_at")

    context = {
        "reviews": reviews
    }
    return render(request, 'admin/web/reviews/all.html', context)

@login_required
def AdminEditProductReview(request, code, rcode):
    review = get_object_or_404(
        Review.objects.select_related(
            "product",
            "customer"
        ),
        unique_code=rcode
    )

    if request.method != "POST":
        context = {
            "review": review
        }
        return render(request, "admin/web/reviews/edit.html", context)
    
    review.title = request.POST.get("title", "").strip()
    review.rating = request.POST.get("rating")
    review.comment = request.POST.get("comment", "").strip()
    review.is_approved = request.POST.get("is_approved") == "True"

    if request.FILES.get("image"):
        review.image = request.FILES.get("image")

    review.save()

    messages.success(request, "Review updated successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteProductReview(request, code):
    if request.method == "POST":
        review_id = request.POST.get("review_id")
        review = get_object_or_404(Review, id=review_id)
        review.delete()

        messages.success(request, "Review deleted successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminContacts(request, code):
    inquiries = ContactInquiry.objects.all().order_by("-created_at")

    context = {
        "inquiries": inquiries
    }
    return render(request, 'admin/web/contacts/all.html', context)

@login_required
def AdminDeleteContact(request, code):
    if request.method == "POST":
        inquiry_id = request.POST.get("inquiry_id")
        inquiry = get_object_or_404(ContactInquiry, unique_code=inquiry_id)
        inquiry.delete()

        messages.success(request, "Contact inquiry deleted successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminNewsletterSubscribers(request, code):
    subscribers = Subscriber.objects.all().order_by("-created_at")

    context = {
        "subscribers": subscribers
    }
    return render(request, 'admin/web/subscribed/all.html', context)

@login_required
def AdminDeleteNewsletterSubscribers(request, code):
    if request.method == "POST":
        subscriber_id = request.POST.get("subscriber_id")
        subscriber = get_object_or_404(Subscriber, unique_code=subscriber_id)
        subscriber.delete()

        messages.success(request, "Subscriber deleted successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminVendors(request, code):
    vendors = Vendor.objects.all()

    context = {
        'vendors': vendors
    }
    return render(request, 'admin/vendors/all.html', context)

@login_required
def AdminNewVendor(request, code):
    if request.method != 'POST':
        return render(request, 'admin/vendors/new.html')
    
    name = request.POST.get("name", "").strip()
    vcode = request.POST.get("vcode", "").strip()
    email = request.POST.get("email", "").strip()
    mobile = request.POST.get("mobile", "").strip()
    address = request.POST.get("address", "").strip()
    city = request.POST.get("city", "").strip()
    state = request.POST.get("state", "").strip()
    country = request.POST.get("country", "").strip()
    zip = request.POST.get("zip", "").strip()
    is_active = request.POST.get("is_active") in ["True", "true", "on", "1"]
    
    city_codes = {
        "Hyderabad": "H",
        "Aligadh": "A",
    }
    ccode = city_codes.get(city, "")

    try:
        Vendor.objects.create(
            name=name,
            vendor_code=vcode,
            mobile=mobile,
            email=email,
            address=address,
            city=city,
            state=state,
            country=country,
            zip=zip,
            city_code=ccode,
            is_active=is_active
        )
        messages.success(request, "Vendor added successfully!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except IntegrityError:
        messages.error(request, "Something went wrong.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminEditVendor(request, code):
    vendor = Vendor.objects.filter(unique_code=code).first()

    if request.method != 'POST':
        context = {
            'vendor': vendor,
        }
        return render(request, 'admin/vendors/edit.html', context)
    
    name = request.POST.get("name", "").strip()
    vcode = request.POST.get("vcode", "").strip()
    email = request.POST.get("email", "").strip()
    mobile = request.POST.get("mobile", "").strip()
    address = request.POST.get("address", "").strip()
    city = request.POST.get("city", "").strip()
    state = request.POST.get("state", "").strip()
    country = request.POST.get("country", "").strip()
    zip = request.POST.get("zip", "").strip()
    is_active = request.POST.get("is_active") in ["True", "true", "on", "1"]
    
    city_codes = {
        "Hyderabad": "H",
        "Aligadh": "A",
    }
    ccode = city_codes.get(city, "")

    try:
        vendor.name = name
        vendor.vendor_code = vcode
        vendor.email = email
        vendor.mobile = mobile
        vendor.address = address
        vendor.city = city
        vendor.state = state
        vendor.country = country
        vendor.zip = zip
        vendor.country_code = ccode
        vendor.is_active = is_active

        vendor.save()

        messages.success(request, "Vendor details updated successfully!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except IntegrityError:
        messages.error(request, "Something went wrong.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteVendor(request, code):
    if request.method == "POST":
        vendor_id = request.POST.get("vendor_id")
        vendor = get_object_or_404(Category, unique_code=vendor_id)

        # proceed to delete
        vendor.delete()
        messages.success(request, "Vendor deleted successfully.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminCategories(request, code):
    categories = Category.objects.filter(parent__isnull=True)

    context = {
        'categories': categories
    }
    return render(request, 'admin/categories/all.html', context)

@login_required
def AdminNewCategory(request, code):
    if request.method != 'POST':
        categories = Category.objects.all()

        context = {
            'categories': categories
        }
        return render(request, 'admin/categories/new.html', context)
    
    name = request.POST.get("name", "").strip()
    slug = request.POST.get("slug", "").strip()
    description = request.POST.get("description") or None
    meta_title = request.POST.get("meta_title") or None
    meta_description = request.POST.get("meta_description") or None
    is_active = request.POST.get("is_active") in ["True", "true", "on", "1"]
    parent_id = request.POST.get("parent")
    image = request.FILES.get("image")

    parent = None
    if parent_id and parent_id != "None":
        parent = get_object_or_404(Category, id=parent_id)

    if not slug:
        messages.error(request, "Slug is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(slug=slug).exists():
        messages.error(request, "Slug already exists. Please use a unique slug.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(name__iexact=name).exists():
        messages.error(request, "Category name already exists.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(name__iexact=name, parent=parent).exists():
        messages.error(request, "Category name already exists under the parent.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        Category.objects.create(
            name=name,
            slug=slug,
            description=description,
            meta_title=meta_title,
            meta_description=meta_description,
            parent=parent,
            image=image,
            is_active=is_active
        )
        messages.success(request, "Category created successfully!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except IntegrityError:
        messages.error(request, "Something went wrong. Slug or code might already exist.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminEditCategory(request, code):
    category = Category.objects.filter(unique_code=code).first()

    if request.method != 'POST':
        categories = Category.objects.all()

        context = {
            'category': category,
            'categories': categories
        }
        return render(request, 'admin/categories/edit.html', context)
    
    name = request.POST.get("name", "").strip()
    slug = request.POST.get("slug", "").strip()
    description = request.POST.get("description") or None
    meta_title = request.POST.get("meta_title") or None
    meta_description = request.POST.get("meta_description") or None
    is_active = request.POST.get("is_active") in ["True", "true", "on", "1"]
    parent_id = request.POST.get("parent")
    image = request.FILES.get("image")

    parent = None
    if parent_id and parent_id != "None":
        parent = get_object_or_404(Category, id=parent_id)

    if not slug:
        messages.error(request, "Slug is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(slug=slug).exclude(id=category.id).exists():
        messages.error(request, "Slug already exists. Please use a unique slug.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(name__iexact=name).exclude(id=category.id).exists():
        messages.error(request, "Category name already exists.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(name__iexact=name, parent=parent).exclude(id=category.id).exists():
        messages.error(request, "Category name already exists under the parent.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        category.name = name
        category.slug = slug
        category.description = description
        category.meta_title = meta_title
        category.meta_description = meta_description
        category.parent = parent
        category.is_active = is_active

        if image:
            category.image = image

        category.save()

        messages.success(request, "Category updated successfully!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except IntegrityError:
        messages.error(request, "Something went wrong. Slug or code might already exist.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteCategory(request, code):
    if request.method == "POST":
        category_id = request.POST.get("category_id")
        category = get_object_or_404(Category, unique_code=category_id)

        # Prevent delete if children exist
        if category.category_set.exists():
            messages.error(request, "Cannot delete category with subcategories.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        if category.image:
            category.image.delete(save=False)

        # proceed to delete
        category.delete()
        messages.success(request, "Category deleted successfully.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminFetchSubcategory(request):
    if request.method == "POST":
        data = json.loads(request.body)
        category_id = data.get("category_id")
        subcategories = Category.objects.filter(
            parent_id=category_id
        ).values("id", "name")

        return JsonResponse({
            "subcategories": list(subcategories)
        })

@login_required
def AdminViewSubcategory(request, code, slug):
    category = Category.objects.filter(slug=slug).first()
    subcats = Category.objects.filter(parent_id=category.id)
    categories = Category.objects.filter(parent__isnull=True).exclude(slug=slug)
    
    context = {
        'category': category,
        'categories': categories,
        'subcats': subcats
    }
    return render(request, 'admin/categories/subcats.html', context)

@login_required
def AdminNewSubcategory(request, code, slug):
    if request.method != 'POST':
        category = Category.objects.filter(slug=slug).first()

        context = {
            'category': category
        }
        return render(request, 'admin/categories/subcat-new.html', context)
    
    name = request.POST.get("name", "").strip()
    slug = request.POST.get("slug", "").strip()
    description = request.POST.get("description") or None
    meta_title = request.POST.get("meta_title") or None
    meta_description = request.POST.get("meta_description") or None
    is_active = request.POST.get("is_active") in ["True", "true", "on", "1"]
    parent_id = request.POST.get("parent")
    image = request.FILES.get("image")

    parent = None
    if parent_id and parent_id != "None":
        parent = get_object_or_404(Category, id=parent_id)

    if not slug:
        messages.error(request, "Slug is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(slug=slug).exists():
        messages.error(request, "Slug already exists. Please use a unique slug.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(name__iexact=name).exists():
        messages.error(request, "Category name already exists.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(name__iexact=name, parent=parent).exists():
        messages.error(request, "Category name already exists under the parent.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        Category.objects.create(
            name=name,
            slug=slug,
            description=description,
            meta_title=meta_title,
            meta_description=meta_description,
            parent=parent,
            image=image,
            is_active=is_active
        )
        messages.success(request, "Category created successfully!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except IntegrityError:
        messages.error(request, "Something went wrong. Slug or code might already exist.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminEditSubcategory(request, code):
    subcat = Category.objects.filter(unique_code=code).first()

    if request.method != 'POST':
        category = Category.objects.filter(parent=subcat.parent).first()
        categories = Category.objects.all()

        context = {
            'subcat': subcat,
            'category': category,
            'categories': categories
        }
        return render(request, 'admin/categories/subcat-edit.html', context)
    
    name = request.POST.get("name", "").strip()
    slug = request.POST.get("slug", "").strip()
    description = request.POST.get("description") or None
    meta_title = request.POST.get("meta_title") or None
    meta_description = request.POST.get("meta_description") or None
    is_active = request.POST.get("is_active") in ["True", "true", "on", "1"]
    parent_id = request.POST.get("parent")
    image = request.FILES.get("image")

    parent = None
    if parent_id and parent_id != "None":
        parent = get_object_or_404(Category, id=parent_id)

    if not slug:
        messages.error(request, "Slug is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(slug=slug).exclude(id=subcat.id).exists():
        messages.error(request, "Slug already exists. Please use a unique slug.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(name__iexact=name).exclude(id=subcat.id).exists():
        messages.error(request, "Subcategory name already exists.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Category.objects.filter(name__iexact=name, parent=parent).exclude(id=subcat.id).exists():
        messages.error(request, "Subcategory name already exists under the parent.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        subcat.name = name
        subcat.slug = slug
        subcat.description = description
        subcat.meta_title = meta_title
        subcat.meta_description = meta_description
        subcat.parent = parent
        subcat.is_active = is_active

        if image:
            subcat.image = image

        subcat.save()

        messages.success(request, "Subcategory updated successfully!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except IntegrityError:
        messages.error(request, "Something went wrong. Slug or code might already exist.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteSubcategory(request, code):
    if request.method == "POST":
        subcategory_id = request.POST.get("category_id")
        subcategory = get_object_or_404(Category, unique_code=subcategory_id)
        
        if subcategory.image:
            subcategory.image.delete(save=False)

        # proceed to delete
        subcategory.delete()
        messages.success(request, "Subcategory deleted successfully.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminFetchCollection(request):
    if request.method == "POST":
        data = json.loads(request.body)
        subcategory_id = data.get("subcategory_id")
        collections = Collection.objects.filter(
            category_id=subcategory_id
        ).values("id", "name")

        return JsonResponse({
            "collections": list(collections)
        })

@login_required
def AdminViewCollection(request, code, slug1, slug2):
    category = Category.objects.filter(slug=slug1).first()
    subcategory = Category.objects.filter(slug=slug2).first()
    subcategories = Category.objects.filter(parent=category).exclude(slug=slug2)
    collections = Collection.objects.filter(category=subcategory)

    context = {
        'category': category,
        'subcategory': subcategory,
        'subcategories': subcategories,
        'collections': collections
    }
    return render(request, 'admin/categories/collections.html', context)

@login_required
def AdminNewCollection(request, code, slug1, slug2):
    category = Category.objects.filter(slug=slug1).first()
    subcategory = Category.objects.filter(slug=slug2).first()

    if request.method != 'POST':
        context = {
            'category': category,
            'subcategory': subcategory
        }
        return render(request, 'admin/categories/collection-new.html', context)
    
    name = request.POST.get("name", "").strip()
    slug = request.POST.get("slug", "").strip()
    scode = request.POST.get("scode", "").strip()
    description = request.POST.get("description") or None
    meta_title = request.POST.get("meta_title") or None
    meta_description = request.POST.get("meta_description") or None
    is_active = request.POST.get("is_active") in ["True", "true", "on", "1"]
    image = request.FILES.get("image")

    if not slug:
        messages.error(request, "Slug is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Collection.objects.filter(name__iexact=name, slug=slug, category_id=subcategory.id).exists():
        messages.error(request, "Collection name already exists under the parent.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        Collection.objects.create(
            name=name,
            slug=slug,
            description=description,
            meta_title=meta_title,
            meta_description=meta_description,
            category_id=subcategory.id,
            scode=scode,
            image=image,
            is_active=is_active
        )
        messages.success(request, "Collection created successfully!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except IntegrityError:
        messages.error(request, "Something went wrong. Slug or code might already exist.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminEditCollection(request, code):
    collection = get_object_or_404(
        Collection.objects.select_related(
            "category",
            "category__parent"
        ),
        unique_code=code
    )

    if request.method != 'POST':
        categories = Category.objects.filter(parent__isnull=True, is_active=True)

        parent_category = None
        subcategories = Category.objects.none()

        if collection.category:
            if collection.category.parent:
                parent_category = collection.category.parent
                subcategories = Category.objects.filter(parent=parent_category, is_active=True)
            else:
                parent_category = collection.category

        context = {
            "collection": collection,
            "categories": categories,
            "subcategories": subcategories,
            "parent_category": parent_category,
        }
        return render(request, 'admin/categories/collection-edit.html', context)

    name = request.POST.get("name", "").strip()
    slug = request.POST.get("slug", "").strip()
    scode = request.POST.get("ccode", "").strip()
    category_id = request.POST.get("category")
    subcategory_id = request.POST.get("subcategory")
    description = request.POST.get("description") or None
    meta_title = request.POST.get("meta_title") or None
    meta_description = request.POST.get("meta_description") or None
    is_active = request.POST.get("is_active") in ["True", "true", "on", "1"]
    image = request.FILES.get("image")

    if not name:
        messages.error(request, "Collection name is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not slug:
        messages.error(request, "Slug is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    final_category_id = subcategory_id or category_id

    if not final_category_id:
        messages.error(request, "Subcategory is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    category = get_object_or_404(Category, id=final_category_id)

    if Collection.objects.filter(slug=slug, category=category).exclude(id=collection.id).exists():
        messages.error(request, "Slug already exists.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        with transaction.atomic():
            collection.name = name
            collection.slug = slug
            collection.scode = scode
            collection.category = category
            collection.description = description
            collection.meta_title = meta_title
            collection.meta_description = meta_description
            collection.is_active = is_active

            if image:
                if collection.image:
                    collection.image.delete(save=False)

                collection.image = image

            collection.save()

        messages.success(request, "Collection updated successfully.")
    except IntegrityError:
        messages.error(request, "Something went wrong while updating collection.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminAddProductInCollection(request, code):
    collection = get_object_or_404(Collection, unique_code=code)

    products = Product.objects.filter(is_active=True).order_by("name")

    selected_ids = GiftingCollectionProduct.objects.filter(
        collection=collection,
        is_active=True
    ).values_list("product_id", flat=True)

    if request.method != 'POST':
        context = {
            "collection": collection,
            "products": products,
            "selected_ids": list(selected_ids),
        }
        return render(request, 'admin/products/collection-add.html', context)

    product_ids = request.POST.getlist("products")

    GiftingCollectionProduct.objects.filter(collection=collection).delete()

    mappings = [
        GiftingCollectionProduct(
            collection=collection,
            product_id=product_id
        )
        for product_id in product_ids
    ]

    GiftingCollectionProduct.objects.bulk_create(mappings)

    messages.success(request, "Collection products updated successfully.")
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

@login_required
def AdminDeleteCollection(request, code):
    if request.method == "POST":
        collection_id = request.POST.get("collection_id")
        collection = get_object_or_404(Collection.objects.prefetch_related("products"), unique_code=collection_id)

        try:
            with transaction.atomic():
                if collection.image:
                    collection.image.delete(save=False)

                collection.products.clear()
                collection.delete()

            messages.success(request, "Collection deleted successfully.")
        except Exception:
            messages.error(request, "Something went wrong while deleting collection.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminProducts(request, code):
    if request.method != 'POST':
        products = Product.objects.select_related(
            "category",
            "vendor",
            "inventory"
        ).prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("-is_primary"),
                to_attr="ordered_images"
            )
        )

        context = {
            'products': products
        }
        return render(request, 'admin/products/all.html', context)

@login_required
def AdminAddProduct(request, code):
    if request.method != 'POST':
        categories = Category.objects.filter(parent__isnull=True, is_active=True)
        vendors = Vendor.objects.filter(is_active=True)
        tags = Tags.objects.filter(is_active=True)

        context = {
            'categories': categories,
            'vendors': vendors,
            'tags': tags
        }
        return render(request, 'admin/products/new.html', context)
    
    name = request.POST.get("name", "").strip()
    slug = request.POST.get("slug", "").strip()
    brand = request.POST.get("brand", "").strip()
    description = request.POST.get("description") or None

    meta_title = request.POST.get("meta_title") or None
    meta_description = request.POST.get("meta_description") or None

    category_id = request.POST.get("category")
    subcategory_id = request.POST.get("subcategory")
    is_active = request.POST.get("is_active") in ["True", "true", "on", "1"]

    vendor_id = request.POST.get("vendor")
    collection_id = request.POST.get("collection")
    tag_ids = request.POST.getlist("tags")

    price = request.POST.get("price")
    discount_price = request.POST.get("discount_price") or None

    weight = request.POST.get("weight") or None
    width = request.POST.get("width") or None
    height = request.POST.get("height") or None

    quantity = request.POST.get("quantity")
    low_stock_threshold = request.POST.get("low_stock_threshold") or 5

    images = request.FILES.getlist("images")
    alt_texts = request.POST.getlist("alt_text[]")
    primary_index = request.POST.get("primary_image")

    attribute_names = request.POST.getlist("attribute_name[]")
    attribute_values = request.POST.getlist("attribute_value[]")

    final_category_id = subcategory_id or category_id

    if not final_category_id:
        messages.error(request, "Category is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    if not collection_id:
        messages.error(request, "Collection is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    category = get_object_or_404(Category, id=final_category_id)
    
    vendor = None
    if vendor_id:
        vendor = get_object_or_404(Vendor, id=vendor_id)

    collection = None
    if collection_id:
        collection = get_object_or_404(Collection, id=collection_id)

    if not name:
        messages.error(request, "Product name is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not slug:
        messages.error(request, "Slug is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not price:
        messages.error(request, "Price is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not quantity:
        messages.error(request, "Quantity is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Product.objects.filter(slug=slug).exists():
        messages.error(request, "Slug already exists.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    try:
        with transaction.atomic():
            material_code = ""

            for attr_name, attr_value in zip(attribute_names, attribute_values):
                attr_name = attr_name.strip()
                attr_value = attr_value.strip()

                if attr_name.lower() == "material" and attr_value:
                    material_code = attr_value[0].upper()
                    break

            ccode = vendor.city[0].upper() if vendor and vendor.city else ""
            vcode = vendor.vendor_code if vendor else ""
            hcode = f"{int(float(height) + 0.5):02}" if height else "00"

            selected_tags = Tags.objects.filter(
                id__in=tag_ids,
                is_active=True
            )

            tag_names = [
                tag.name.strip().lower()
                for tag in selected_tags
            ]

            tag_scode_map = {
                "buddha": "31",
                "budhha": "31",
                "elephant": "32",
                "lion": "33",
                "turtle": "34",
                "horse": "35",
                "rishi": "36",
            }

            scode = collection.scode if collection.scode else "00"

            collection_name = (
                collection.name.strip().lower()
                if collection and collection.name
                else ""
            )
            subcategory_name = (
                category.name.strip().lower()
                if category and category.name
                else ""
            )
            use_collection_scode = (
                collection_name == "elephant urli"
                or subcategory_name == "wall decor"
            )

            if not use_collection_scode:
                for tag_name in tag_names:
                    if tag_name in tag_scode_map:
                        scode = tag_scode_map[tag_name]
                        break

            base_code = f"{ccode}{vcode}{material_code}{hcode}{scode}"

            category_ids = [category.id]

            if category.parent_id:
                category_ids.append(category.parent_id)
            else:
                child_ids = Category.objects.filter(
                    parent=category
                ).values_list("id", flat=True)

                category_ids.extend(list(child_ids))

            matching_products = Product.objects.filter(
                category_id__in=category_ids,
            ).exclude(
                product_code__isnull=True
            ).exclude(
                product_code=""
            )

            max_pcode = 0

            for old_product in matching_products:
                old_code = old_product.product_code or ""

                old_scode = old_code[-6:-4] if len(old_code) >= 6 else ""

                if old_scode != scode:
                    continue

                try:
                    old_pcode = int(old_code[-4:])
                    max_pcode = max(max_pcode, old_pcode)
                except (ValueError, TypeError):
                    continue

            pcode = f"{max_pcode + 1:04}"
            product_code = f"{base_code}{pcode}"

            if Product.objects.filter(product_code=product_code).exists():
                messages.error(request, "Product code already exists.")
                return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
            
            final_category_id = subcategory_id or category_id
            category = get_object_or_404(Category, id=final_category_id)

            # Create product
            product = Product.objects.create(
                category=category,
                collection=collection,
                vendor=vendor,
                name=name,
                slug=slug,
                product_code=product_code,
                price=Decimal(price),
                discount_price=Decimal(discount_price) if discount_price else None,
                weight=Decimal(weight) if weight else None,
                width=Decimal(width) if width else None,
                height=Decimal(height) if height else None,
                description=description,
                meta_title=meta_title,
                meta_description=meta_description,
                brand=brand,
                is_active=is_active
            )

            product.tags.set(tag_ids)

            # Inventory
            ProductInventory.objects.create(
                product=product,
                quantity=int(quantity),
                low_stock_threshold=int(low_stock_threshold)
            )

            # Images
            for index, image in enumerate(images):
                alt_text = alt_texts[index] if index < len(alt_texts) else ""

                ProductImage.objects.create(
                    product=product,
                    image=image,
                    alt_text=alt_text,
                    is_primary=str(index) == str(primary_index)
                )

            # Attributes
            for attr_name, attr_value in zip(attribute_names, attribute_values):
                attr_name = attr_name.strip()
                attr_value = attr_value.strip()

                if attr_name and attr_value:
                    ProductAttribute.objects.create(
                        product=product,
                        name=attr_name,
                        value=attr_value
                    )

        messages.success(request, "Product created successfully.")
    except IntegrityError:
        messages.error(
            request,
            "Something went wrong while saving product data."
        )

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminEditProduct(request, code):
    product = get_object_or_404(
        Product.objects.select_related(
            "category",
            "category__parent",
            "collection",
            "vendor",
            "inventory"
        ).prefetch_related(
            "tags",
            "images",
            "attributes",
        ),
        unique_code=code
    )

    if request.method != 'POST':
        categories = Category.objects.filter(parent__isnull=True, is_active=True)
        vendors = Vendor.objects.filter(is_active=True)
        tags = Tags.objects.filter(is_active=True)

        parent_category = None
        subcategories = Category.objects.none()

        if product.category:
            if product.category.parent:
                parent_category = product.category.parent
                subcategories = Category.objects.filter(
                    parent=parent_category,
                    is_active=True
                )
            else:
                parent_category = product.category
                subcategories = Category.objects.filter(
                    parent=parent_category,
                    is_active=True
                )

        collections = Collection.objects.filter(
            category=product.category,
            is_active=True
        )

        selected_collection_id = product.collection_id
        selected_tag_ids = product.tags.values_list("id", flat=True)

        context = {
            "categories": categories,
            "subcategories": subcategories,
            "collections": collections,
            "selected_collection_id": selected_collection_id,
            "selected_tag_ids": list(selected_tag_ids),
            "vendors": vendors,
            "tags": tags,
            "product": product,
            "parent_category": parent_category,
        }
        return render(request, 'admin/products/edit.html', context)
    
    old_category_id = product.category_id
    old_collection_id = product.collection_id

    name = request.POST.get("name", "").strip()
    slug = request.POST.get("slug", "").strip()
    brand = request.POST.get("brand", "").strip()
    description = request.POST.get("description") or None
    meta_title = request.POST.get("meta_title") or None
    meta_description = request.POST.get("meta_description") or None

    category_id = request.POST.get("category")
    subcategory_id = request.POST.get("subcategory")
    final_category_id = subcategory_id or category_id

    vendor_id = request.POST.get("vendor")
    collection_id = request.POST.get("collection")
    tag_ids = request.POST.getlist("tags")

    price = request.POST.get("price")
    discount_price = request.POST.get("discount_price") or None

    weight = request.POST.get("weight") or None
    height = request.POST.get("height") or None
    length = request.POST.get("length") or None
    width = request.POST.get("width") or None

    quantity = request.POST.get("quantity")
    low_stock_threshold = request.POST.get("low_stock_threshold") or 5

    is_active = request.POST.get("is_active") in ["True", "true", "on", "1"]

    images = request.FILES.getlist("images")
    alt_texts = request.POST.getlist("alt_text[]")

    existing_image_ids = request.POST.getlist("existing_image_ids[]")
    existing_alt_texts = request.POST.getlist("existing_alt_text[]")
    delete_images = request.POST.getlist("delete_images[]")
    primary_existing_image = request.POST.get("primary_existing_image")
    primary_new_image = request.POST.get("primary_image")

    attribute_names = request.POST.getlist("attribute_name[]")
    attribute_values = request.POST.getlist("attribute_value[]")

    if not name:
        messages.error(request, "Product name is required.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    if not slug:
        messages.error(request, "Slug is required.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    if not final_category_id:
        messages.error(request, "Category is required.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    if not vendor_id:
        messages.error(request, "Vendor is required.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    if not collection_id:
        messages.error(request, "Collection is required.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    if not price:
        messages.error(request, "Price is required.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    if not quantity:
        messages.error(request, "Quantity is required.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    if Product.objects.filter(slug=slug).exclude(id=product.id).exists():
        messages.error(request, "Slug already exists.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    category = get_object_or_404(Category, id=final_category_id)
    vendor = get_object_or_404(Vendor, id=vendor_id)
    collection = get_object_or_404(Collection, id=collection_id)

    should_regenerate_product_code = (
        old_category_id != category.id
        or old_collection_id != collection.id
    )

    try:
        with transaction.atomic():
            if should_regenerate_product_code:
                selected_tags = Tags.objects.filter(
                    id__in=tag_ids,
                    is_active=True
                )

                tag_names = [
                    tag.name.strip().lower()
                    for tag in selected_tags
                ]

                tag_scode_map = {
                    "buddha": "31",
                    "budhha": "31",
                    "elephant": "32",
                    "lion": "33",
                    "turtle": "34",
                    "horse": "35",
                    "rishi": "36",
                }

                scode = collection.scode if collection.scode else "00"

                collection_name = (
                    collection.name.strip().lower()
                    if collection and collection.name
                    else ""
                )

                subcategory_name = (
                    category.name.strip().lower()
                    if category and category.name
                    else ""
                )

                use_collection_scode = (
                    collection_name == "elephant urli"
                    or subcategory_name == "wall decor"
                )

                if not use_collection_scode:
                    for tag_name in tag_names:
                        if tag_name in tag_scode_map:
                            scode = tag_scode_map[tag_name]
                            break

                material_code = ""

                for attr_name, attr_value in zip(attribute_names, attribute_values):
                    attr_name = attr_name.strip()
                    attr_value = attr_value.strip()

                    if attr_name.lower() == "material" and attr_value:
                        material_code = attr_value[0].upper()
                        break

                ccode = vendor.city[0].upper() if vendor and vendor.city else ""
                vcode = vendor.vendor_code if vendor and vendor.vendor_code else "00"
                hcode = f"{int(float(height) + 0.5):02}" if height else "00"

                base_code = f"{ccode}{vcode}{material_code}{hcode}{scode}"

                category_ids = [category.id]

                if category.parent_id:
                    category_ids.append(category.parent_id)
                else:
                    child_ids = Category.objects.filter(
                        parent=category
                    ).values_list("id", flat=True)

                    category_ids.extend(list(child_ids))

                matching_products = Product.objects.filter(
                    category_id__in=category_ids
                ).exclude(
                    id=product.id
                ).exclude(
                    product_code__isnull=True
                ).exclude(
                    product_code=""
                )

                max_pcode = 0

                for old_product in matching_products:
                    old_code = old_product.product_code or ""
                    old_scode = old_code[-6:-4] if len(old_code) >= 6 else ""

                    if old_scode != scode:
                        continue

                    try:
                        old_pcode = int(old_code[-4:])
                        max_pcode = max(max_pcode, old_pcode)
                    except (ValueError, TypeError):
                        continue

                pcode = f"{max_pcode + 1:04}"
                product.product_code = f"{base_code}{pcode}"
            
            product.category = category
            product.collection = collection
            product.vendor = vendor
            product.name = name
            product.slug = slug
            product.price = Decimal(price)
            product.discount_price = Decimal(discount_price) if discount_price else None
            product.weight = Decimal(weight) if weight else None
            product.height = Decimal(height) if height else None
            product.width = Decimal(width) if width else None
            product.length = Decimal(length) if length else None
            product.description = description
            product.meta_title = meta_title
            product.meta_description = meta_description
            product.brand = brand
            product.is_active = is_active
            product.save()

            product.tags.set(tag_ids)

            inventory, created = ProductInventory.objects.get_or_create(
                product=product
            )
            inventory.quantity = int(quantity)
            inventory.low_stock_threshold = int(low_stock_threshold)
            inventory.save()

            if delete_images:
                ProductImage.objects.filter(
                    id__in=delete_images,
                    product=product
                ).delete()

            ProductImage.objects.filter(product=product).update(
                is_primary=False
            )

            for image_id, alt_text in zip(existing_image_ids, existing_alt_texts):
                if str(image_id) in delete_images:
                    continue

                image_obj = ProductImage.objects.filter(
                    id=image_id,
                    product=product
                ).first()

                if image_obj:
                    image_obj.alt_text = alt_text
                    image_obj.is_primary = (
                        str(image_obj.id) == str(primary_existing_image)
                    )
                    image_obj.save()

            for index, image in enumerate(images):
                alt_text = alt_texts[index] if index < len(alt_texts) else ""

                ProductImage.objects.create(
                    product=product,
                    image=image,
                    alt_text=alt_text,
                    is_primary=str(index) == str(primary_new_image)
                )

            ProductAttribute.objects.filter(product=product).delete()

            for attr_name, attr_value in zip(attribute_names, attribute_values):
                attr_name = attr_name.strip()
                attr_value = attr_value.strip()

                if attr_name and attr_value:
                    ProductAttribute.objects.create(
                        product=product,
                        name=attr_name,
                        value=attr_value
                    )
        messages.success(request, "Product updated successfully.")
    except IntegrityError:
        messages.error(request, "Something went wrong while updating product data.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))   

@login_required
def AdminDeleteProduct(request, code):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(
            Product.objects.prefetch_related(
                "images",
                "attributes",
                "collection",
                "reviews"
            ).select_related(
                "inventory"
            ),
            unique_code=product_id
        )

        try:
            with transaction.atomic():
                for image in product.images.all():
                    if image.image:
                        image.image.delete(save=False)
                        
                product.delete()

            messages.success(request, "Product deleted successfully.")
        except Exception:
            messages.error(request, "Something went wrong while deleting product.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminBlogCategories(request, code):
    categories = BlogCategory.objects.all()
    
    context = {
        "categories": categories
    }
    return render(request, 'admin/blogs/categories.html', context)

@login_required
def AdminNewBlogCategory(request, code):
    if request.method != "POST":
        return render(request, "admin/blogs/category-new.html")

    name = request.POST.get("name", "").strip()
    slug = request.POST.get("slug", "").strip() or slugify(name)
    is_active = request.POST.get("is_active") == "True"

    BlogCategory.objects.create(
        name=name,
        slug=slug,
        is_active=is_active
    )

    messages.success(request, "Blog category created successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminEditBlogCategory(request, code):
    category = get_object_or_404(BlogCategory, unique_code=code)

    if request.method != "POST":
        context = {
            "category": category
        }
        return render(request, "admin/blogs/category-edit.html", context)

    category.name = request.POST.get("name", "").strip()
    category.slug = request.POST.get("slug", "").strip() or slugify(category.name)
    category.is_active = request.POST.get("is_active") == "True"
    category.save()

    messages.success(request, "Blog category updated successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteBlogCategory(request, code):
    if request.method == "POST":
        category_id = request.POST.get("category_id")
        category = get_object_or_404(BlogCategory, unique_code=category_id)
        category.delete()

        messages.success(request, "Blog category deleted successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminBlogs(request, code):
    blogs = Blog.objects.select_related("category").order_by("-created_at")

    context = {
        "blogs": blogs
    }
    return render(request, 'admin/blogs/all.html', context)

@login_required
def AdminAddNewBlog(request, code):
    categories = BlogCategory.objects.filter(is_active=True)

    if request.method != "POST":
        context = {
            "categories": categories
        }
        return render(request, "admin/blogs/new.html", context)

    title = request.POST.get("title", "").strip()
    slug = request.POST.get("slug", "").strip() or slugify(title)
    content = BlogFormatter.to_html(
        request.POST.get("content", "")
    )

    blog = Blog.objects.create(
        category_id=request.POST.get("category"),
        title=title,
        slug=slug,
        image=request.FILES.get("image"),
        thumbnail=request.FILES.get("thumbnail"),
        short_description=request.POST.get("short_description", "").strip(),
        content=content,

        meta_title=request.POST.get("meta_title", "").strip() or title,
        meta_description=request.POST.get("meta_description", "").strip(),
        meta_keywords=request.POST.get("meta_keywords", "").strip(),

        is_featured=request.POST.get("is_featured") == "True",
        is_active=request.POST.get("is_active") == "True",
    )

    faq_objects = []

    for i in range(1, 7):
        question = request.POST.get(f"question{i}", "",).strip()
        answer = request.POST.get(f"answer{i}", "",).strip()

        if not question or not answer:
            continue

        faq_objects.append(
            FAQ(
                category="Blog",
                page="Blog Details",
                question=question,
                answer=answer,
                blog=blog,
                is_active=True,
            )
        )

    if faq_objects:
        FAQ.objects.bulk_create(faq_objects)

    messages.success(request, "Blog created successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminEditBlog(request, code):
    blog = get_object_or_404(Blog, unique_code=code)
    faq_list = list(
        FAQ.objects.filter(blog=blog).order_by("created_at")
    )
    categories = BlogCategory.objects.filter(is_active=True)

    if request.method != "POST":
        context = {
            "blog": blog,
            "faqs": faq_list,
            "categories": categories
        }
        return render(request, "admin/blogs/edit.html", context)

    blog.category_id = request.POST.get("category")
    blog.title = request.POST.get("title", "").strip()
    blog.slug = request.POST.get("slug", "").strip() or slugify(blog.title)
    blog.short_description = request.POST.get("short_description", "").strip()
    
    blog.content = BlogFormatter.to_html(
        request.POST.get("content", "")
    )

    blog.meta_title = request.POST.get("meta_title", "").strip() or blog.title
    blog.meta_description = request.POST.get("meta_description", "").strip()
    blog.meta_keywords = request.POST.get("meta_keywords", "").strip()

    blog.is_featured = request.POST.get("is_featured") == "True"
    blog.is_active = request.POST.get("is_active") == "True"

    if request.FILES.get("thumbnail"):
        blog.thumbnail = request.FILES.get("thumbnail")

    if request.FILES.get("image"):
        blog.image = request.FILES.get("image")

    blog.save()

    FAQ.objects.filter(blog=blog).delete()
    faq_objects = []
    MAX_FAQS = 6

    for i in range(1, MAX_FAQS + 1):
        question = request.POST.get(f"question{i}", "",).strip()
        answer = request.POST.get(f"answer{i}", "",).strip()

        if not question or not answer:
            continue

        faq_objects.append(
            FAQ(
                category="Blog",
                page="Blog Details",
                question=question,
                answer=answer,
                blog=blog,
                is_active=True,
            )
        )

    if faq_objects:
        FAQ.objects.bulk_create(faq_objects)

    messages.success(request, "Blog updated successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteBlog(request, code):
    if request.method == "POST":
        blog_id = request.POST.get("blog_id")
        blog = get_object_or_404(Blog, unique_code=blog_id)

        if blog.thumbnail:
            blog.thumbnail.delete(save=False)
        
        if blog.image:
            blog.image.delete(save=False)

        blog.delete()

        messages.success(request, "Blog deleted successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminAccSettings(request, code):
    return render(request, 'admin/settings.html')

@login_required
def AdminNotifications(request, code):
    logs = NotificationLog.objects.select_related("order", "order__customer").order_by("-created_at")

    channel = request.GET.get("channel")
    status = request.GET.get("status")
    event = request.GET.get("event")
    search = request.GET.get("search")

    if channel:
        logs = logs.filter(channel=channel)

    if status:
        logs = logs.filter(status=status)

    if event:
        logs = logs.filter(event=event)

    if search:
        logs = logs.filter(
            Q(order__order_id__icontains=search) |
            Q(order__customer__name__icontains=search) |
            Q(order__customer__mobile__icontains=search) |
            Q(recipient__icontains=search)
        )

    context = {
        "logs": logs,
        "channel": channel,
        "status": status,
        "event": event,
        "search": search,
    }
    return render(request, 'admin/notify.html', context)

@login_required
def AdminReports(request, code):
    today = datetime.now().date()
    month_start = today.replace(day=1)

    orders = Order.objects.filter(is_deleted=False)
    paid_orders = orders.filter(payment_status="Paid")
    today_paid_orders = paid_orders.filter(created_at__date=today)
    month_paid_orders = paid_orders.filter(created_at__date__gte=month_start)
    total_revenue = (paid_orders.aggregate(total=Sum("total"))["total"] or 0)
    today_revenue = (today_paid_orders.aggregate(total=Sum("total"))["total"] or 0)
    month_revenue = (month_paid_orders.aggregate(total=Sum("total"))["total"] or 0)

    context = {
        "total_revenue": total_revenue,
        "today_revenue": today_revenue,
        "month_revenue": month_revenue,
        "total_orders": orders.count(),
        "today_orders": orders.filter(created_at__date=today).count(),
        "paid_orders": paid_orders.count(),
        "pending_orders": orders.filter(payment_status="Pending").count(),
        "failed_orders": orders.filter(payment_status="Failed").count(),
        "cancelled_orders": orders.filter(status="Cancelled").count(),
        "confirmed_orders": orders.filter(status="Confirmed").count(),
        "processing_orders": orders.filter(status="Processing").count(),
        "shipped_orders": orders.filter(status="Shipped").count(),
        "delivered_orders": orders.filter(status="Delivered").count(),
        "total_customers": Customer.objects.count(),
        "new_customers_today": Customer.objects.filter(created_at__date=today).count(),
        "avg_order_value": paid_orders.aggregate(avg=Avg("total"))["avg"] or 0,
        "recent_orders": orders.select_related("customer").order_by("-created_at")[:8],
    }
    return render(request, "admin/reports/overview.html", context)

@login_required
def AdminReportsSales(request, code):
    today = datetime.now().date()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start_date_obj = today - timedelta(days=30)

    if end_date:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_date_obj = today

    paid_orders = Order.objects.filter(
        is_deleted=False,
        payment_status="Paid",
        created_at__date__gte=start_date_obj,
        created_at__date__lte=end_date_obj,
    )

    total_revenue = paid_orders.aggregate(total=Sum("total"))["total"] or 0
    total_orders = paid_orders.count()
    avg_order_value = paid_orders.aggregate(avg=Avg("total"))["avg"] or 0
    shipping_revenue = paid_orders.aggregate(total=Sum("shipping"))["total"] or 0

    daily_sales = (
        paid_orders
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            orders=Count("id"),
            revenue=Sum("total"),
            avg_order=Avg("total"),
        )
        .order_by("-day")
    )

    context = {
        "start_date": start_date_obj,
        "end_date": end_date_obj,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "avg_order_value": avg_order_value,
        "shipping_revenue": shipping_revenue,
        "daily_sales": daily_sales,
    }
    return render(request, "admin/reports/sales.html", context)

@login_required
def AdminReportsOrders(request, code):
    today = datetime.now().date()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    status = request.GET.get("status")
    payment_status = request.GET.get("payment_status")

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else today - timedelta(days=30)
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else today

    orders = Order.objects.filter(
        is_deleted=False,
        created_at__date__gte=start_date_obj,
        created_at__date__lte=end_date_obj,
    ).select_related("customer")

    if status:
        orders = orders.filter(status=status)

    if payment_status:
        orders = orders.filter(payment_status=payment_status)

    context = {
        "start_date": start_date_obj,
        "end_date": end_date_obj,
        "status": status,
        "payment_status": payment_status,
        "total_orders": orders.count(),
        "pending_orders": orders.filter(status="Pending").count(),
        "confirmed_orders": orders.filter(status="Confirmed").count(),
        "processing_orders": orders.filter(status="Processing").count(),
        "shipped_orders": orders.filter(status="Shipped").count(),
        "delivered_orders": orders.filter(status="Delivered").count(),
        "cancelled_orders": orders.filter(status="Cancelled").count(),
        "paid_orders": orders.filter(payment_status="Paid").count(),
        "pending_payment_orders": orders.filter(payment_status="Pending").count(),
        "failed_payment_orders": orders.filter(payment_status="Failed").count(),
        "orders": orders.order_by("-created_at"),
    }

    return render(request, "admin/reports/orders.html", context)

@login_required
def AdminReportsCustomers(request, code):
    customers = (
        Customer.objects
        .annotate(
            total_orders=Count(
                "orders",
                filter=Q(
                    orders__is_deleted=False,
                    orders__payment_status="Paid"
                )
            ),
            total_spent=Sum(
                "orders__total",
                filter=Q(
                    orders__is_deleted=False,
                    orders__payment_status="Paid"
                )
            ),
            last_order_date=Max(
                "orders__created_at",
                filter=Q(
                    orders__is_deleted=False,
                    orders__payment_status="Paid"
                )
            ),
        )
        .order_by("-total_spent")
    )

    context = {
        "customers": customers,
        "total_customers": Customer.objects.count(),
        "repeat_customers": customers.filter(total_orders__gt=1).count(),
        "one_time_customers": customers.filter(total_orders=1).count(),
    }
    return render(request, "admin/reports/customers.html", context)

@login_required
def AdminReportsProducts(request, code):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    order_items = OrderItem.objects.filter(order__payment_status="Paid", order__is_deleted=False,)

    if start_date:
        order_items = order_items.filter(order__created_at__date__gte=start_date)
    
    if end_date:
        order_items = order_items.filter(order__created_at__date__lte=end_date)

    products = (
        order_items
        .values(
            "product__id",
            "product__name",
            "product__product_code",
        )
        .annotate(
            units_sold=Sum("quantity"),
            revenue=Sum(
                F("quantity") * F("price")
            ),
            orders_count=Count(
                "order",
                distinct=True
            ),
        )
        .order_by("-revenue")
    )

    collections = (
        order_items
        .values(
            "product__collection__name"
        )
        .annotate(
            revenue=Sum(
                F("quantity") * F("price")
            ),
            units_sold=Sum("quantity"),
        )
        .order_by("-revenue")
    )

    context = {
        "products": products,
        "collections": collections[:10],
        "start_date": start_date,
        "end_date": end_date,
    }
    return render(request, "admin/reports/products.html", context)

@login_required
def AdminReportsPayments(request, code):
    today = datetime.now().date()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    payment_status = request.GET.get("payment_status")
    payment_mode = request.GET.get("payment_mode")

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else today - timedelta(days=30)
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else today

    payments = Order.objects.filter(
        is_deleted=False,
        created_at__date__gte=start_date_obj,
        created_at__date__lte=end_date_obj,
    ).select_related("customer").order_by("-created_at")

    abandoned_payments = payments.filter(
        payment_status="Pending",
        payment_reminder_sent=True
    ).count()

    recovered_orders = payments.filter(
        payment_status="Paid",
        payment_reminder_sent=True
    )

    recovered_payments = recovered_orders.count()

    recovery_revenue = (
        recovered_orders.aggregate(total=Sum("total"))["total"] or 0
    )

    if payment_status:
        payments = payments.filter(payment_status=payment_status)

    if payment_mode:
        payments = payments.filter(payment_mode=payment_mode)

    context = {
        "start_date": start_date_obj,
        "end_date": end_date_obj,
        "payment_status": payment_status,
        "payment_mode": payment_mode,
        "total_amount": payments.aggregate(total=Sum("total"))["total"] or 0,
        "paid_amount": payments.filter(payment_status="Paid").aggregate(total=Sum("total"))["total"] or 0,
        "pending_amount": payments.filter(payment_status="Pending").aggregate(total=Sum("total"))["total"] or 0,
        "failed_amount": payments.filter(payment_status="Failed").aggregate(total=Sum("total"))["total"] or 0,
        "total_payments": payments.count(),
        "paid_count": payments.filter(payment_status="Paid").count(),
        "pending_count": payments.filter(payment_status="Pending").count(),
        "failed_count": payments.filter(payment_status="Failed").count(),
        "payments": payments,
        "abandoned_orders":abandoned_payments,
        "recovered_payments": recovered_payments,
        "recovery_revenue": recovery_revenue
    }
    return render(request, "admin/reports/payments.html", context)

@login_required
def AdminReportsShipments(request, code):
    shipment_status = request.GET.get("shipment_status")
    courier = request.GET.get("courier")
    shipments = Order.objects.filter(
        is_deleted=False,
        payment_status="Paid"
    ).select_related("customer").order_by("-created_at")

    if shipment_status:
        shipments = shipments.filter(shipment_status=shipment_status)

    if courier:
        shipments = shipments.filter(shiprocket_courier_name__icontains=courier)

    context = {
        "shipments": shipments,
        "shipment_status": shipment_status,
        "courier": courier,
        "total_shipments": shipments.count(),
        "created_shipments": shipments.exclude(shiprocket_shipment_id__isnull=True).exclude(shiprocket_shipment_id="").count(),
        "awb_assigned": shipments.exclude(shiprocket_awb_code__isnull=True).exclude(shiprocket_awb_code="").count(),
        "tracking_available": shipments.exclude(tracking_url__isnull=True).exclude(tracking_url="").count(),
    }
    return render(request, "admin/reports/shipments.html", context)

@login_required
def AdminReportsNotifications(request, code):
    channel = request.GET.get("channel")
    status = request.GET.get("status")
    event = request.GET.get("event")
    logs = NotificationLog.objects.select_related(
        "order",
        "order__customer"
    ).order_by("-created_at")

    if channel:
        logs = logs.filter(channel=channel)

    if status:
        logs = logs.filter(status=status)

    if event:
        logs = logs.filter(event=event)

    context = {
        "logs": logs,
        "channel": channel,
        "status": status,
        "event": event,
        "total_logs": logs.count(),
        "success_logs": logs.filter(status="Success").count(),
        "failed_logs": logs.filter(status="Failed").count(),
        "email_logs": logs.filter(channel="Email").count(),
        "whatsapp_logs": logs.filter(channel="WhatsApp").count(),
        "sms_logs": logs.filter(channel="SMS").count(),
    }
    return render(request, "admin/reports/notifications.html", context)

@login_required
def AdminReportsChatbot(request, code):
    logs = ChatbotSearchLog.objects.select_related(
        "customer",
        "session",
        "matched_faq",
        "matched_bundle",
        "support_ticket",
        "selected_product",
    ).prefetch_related(
        "matched_products",
    )

    total_searches = logs.count()
    faq_hits = logs.filter(result_type="FAQ").count()
    product_hits = logs.filter(result_type="PRODUCT").count()
    bundle_hits = logs.filter(result_type="BUNDLE").count()
    support_hits = logs.filter(result_type="SUPPORT").count()
    empty_hits = logs.filter(result_type="EMPTY").count()
    success_rate = 0

    if total_searches:
        success_rate = round(
            (
                (
                    faq_hits
                    + product_hits
                    + bundle_hits
                )
                /
                total_searches
            ) * 100,
            1
        )

    top_keywords = (
        logs.values("query")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")[:20]
    )

    top_products = (
        Product.objects.annotate(
            total=Count("chatbot_logs")
        )
        .filter(total__gt=0)
        .order_by("-total")[:10]
    )

    top_bundles = (
        ProductBundle.objects.annotate(
            total=Count("chatbotsearchlog")
        )
        .filter(total__gt=0)
        .order_by("-total")[:10]
    )

    top_faqs = (
        FAQ.objects.annotate(
            total=Count("chatbotsearchlog")
        )
        .filter(total__gt=0)
        .order_by("-total")[:10]
    )

    failed_queries = logs.filter(result_type="EMPTY").order_by("-created_at")[:20]
    recent_activity = logs.order_by("-created_at")[:20]
    support_tickets = SupportTicket.objects.count()

    context = {
        "total_searches": total_searches,
        "faq_hits": faq_hits,
        "product_hits": product_hits,
        "bundle_hits": bundle_hits,
        "support_hits": support_hits,
        "support_tickets": support_tickets,
        "empty_hits": empty_hits,
        "success_rate": success_rate,
        "top_keywords": top_keywords,
        "top_products": top_products,
        "top_bundles": top_bundles,
        "top_faqs": top_faqs,
        "failed_queries": failed_queries,
        "recent_activity": recent_activity,

        "result_chart": json.dumps([faq_hits, product_hits, bundle_hits, support_hits, empty_hits,]),
        "keyword_labels": json.dumps([k["query"] for k in top_keywords]),
        "keyword_values": json.dumps([k["total"] for k in top_keywords]),
        "product_labels": json.dumps([p.name for p in top_products]),
        "product_values": json.dumps([p.total for p in top_products]),
        "bundle_labels": json.dumps([b.name for b in top_bundles]),
        "bundle_values": json.dumps([b.total for b in top_bundles])
    }
    
    return render(request, "admin/reports/chatbot.html", context)

@login_required
def AdminReportsInsights(request, code):
    today = datetime.now().date()
    current_start = today - timedelta(days=30)
    previous_start = today - timedelta(days=60)
    previous_end = current_start - timedelta(days=1)

    def percent_change(current, previous):
        if not previous:
            return 100 if current else 0
        return round(((current - previous) / previous) * 100, 2)

    def percentage(part, total):
        if not total:
            return 0
        return round((part / total) * 100, 2)

    current_orders = Order.objects.filter(
        is_deleted=False,
        payment_status="Paid",
        created_at__date__gte=current_start,
        created_at__date__lte=today,
    )

    previous_orders = Order.objects.filter(
        is_deleted=False,
        payment_status="Paid",
        created_at__date__gte=previous_start,
        created_at__date__lte=previous_end,
    )

    all_current_orders = Order.objects.filter(
        is_deleted=False,
        created_at__date__gte=current_start,
        created_at__date__lte=today,
    )

    current_revenue = current_orders.aggregate(total=Sum("total"))["total"] or 0
    previous_revenue = previous_orders.aggregate(total=Sum("total"))["total"] or 0

    current_order_count = current_orders.count()
    previous_order_count = previous_orders.count()

    current_aov = current_orders.aggregate(avg=Avg("total"))["avg"] or 0
    previous_aov = previous_orders.aggregate(avg=Avg("total"))["avg"] or 0

    revenue_trend = percent_change(current_revenue, previous_revenue)
    order_trend = percent_change(current_order_count, previous_order_count)
    aov_trend = percent_change(current_aov, previous_aov)

    avg_daily_revenue = current_revenue / 30 if current_revenue else 0
    avg_daily_orders = current_order_count / 30 if current_order_count else 0

    forecast_revenue_30 = avg_daily_revenue * 30
    forecast_orders_30 = round(avg_daily_orders * 30)

    total_payment_attempts = all_current_orders.count()
    paid_payment_attempts = all_current_orders.filter(payment_status="Paid").count()
    abandoned_payments = all_current_orders.filter(
        payment_status="Pending",
        payment_reminder_sent=True,
    ).count()

    payment_success_rate = percentage(
        paid_payment_attempts,
        total_payment_attempts
    )

    abandoned_payment_rate = percentage(
        abandoned_payments,
        total_payment_attempts
    )

    total_notifications = NotificationLog.objects.filter(
        created_at__date__gte=current_start,
        created_at__date__lte=today,
    ).count()

    failed_notifications = NotificationLog.objects.filter(
        status="Failed",
        created_at__date__gte=current_start,
        created_at__date__lte=today,
    ).count()

    notification_success_rate = percentage(
        total_notifications - failed_notifications,
        total_notifications
    )

    paid_orders_count = current_orders.count()

    shipment_ready_count = current_orders.exclude(
        shiprocket_shipment_id__isnull=True
    ).exclude(
        shiprocket_shipment_id=""
    ).count()

    shipment_readiness_rate = percentage(
        shipment_ready_count,
        paid_orders_count
    )

    health_score = 100

    if revenue_trend < 0:
        health_score -= 15

    if order_trend < 0:
        health_score -= 10

    if aov_trend < 0:
        health_score -= 8

    if payment_success_rate < 80:
        health_score -= 15

    if abandoned_payment_rate > 5:
        health_score -= 10

    if notification_success_rate < 95 and total_notifications > 0:
        health_score -= 8

    if shipment_readiness_rate < 80 and paid_orders_count > 0:
        health_score -= 12

    health_score = max(0, min(100, health_score))

    if health_score >= 90:
        health_label = "Excellent"
    elif health_score >= 75:
        health_label = "Good"
    elif health_score >= 60:
        health_label = "Needs Attention"
    else:
        health_label = "Critical"

    insights = []

    if revenue_trend > 0:
        insights.append(f"Revenue increased by {revenue_trend}% compared to the previous 30 days.")
    elif revenue_trend < 0:
        insights.append(f"Revenue decreased by {abs(revenue_trend)}% compared to the previous 30 days.")
    else:
        insights.append("Revenue remained stable compared to the previous 30 days.")

    if order_trend > 0:
        insights.append(f"Paid orders increased by {order_trend}% compared to the previous 30 days.")
    elif order_trend < 0:
        insights.append(f"Paid orders decreased by {abs(order_trend)}% compared to the previous 30 days.")

    if aov_trend < 0:
        insights.append(f"Average order value dropped by {abs(aov_trend)}%.")
        actions.append("Create product bundles, upsells, or free shipping thresholds to improve average order value.")
    elif aov_trend > 0:
        insights.append(f"Average order value improved by {aov_trend}%.")

    if failed_notifications > 0:
        insights.append(f"{failed_notifications} notification failures were recorded in the last 30 days.")

    actions = []

    def add_action(priority, category, title, description):
        actions.append({
            "priority": priority,
            "category": category,
            "title": title,
            "description": description,
        })

    if aov_trend < 0:
        add_action(
            "Medium",
            "Revenue",
            "Improve Average Order Value",
            "Average order value is dropping. Add bundles, upsells, or free shipping thresholds."
        )

    if abandoned_payment_rate > 5:
        add_action(
            "High",
            "Payments",
            "Reduce Abandoned Payments",
            "Abandoned payment rate is above the safe range. Review checkout flow and reminder timing."
        )

    if notification_success_rate < 95 and total_notifications > 0:
        add_action(
            "High",
            "Notifications",
            "Fix Notification Failures",
            "Notification success rate is below 95%. Check Email, WhatsApp, and SMS logs."
        )

    if shipment_readiness_rate < 80 and paid_orders_count > 0:
        add_action(
            "High",
            "Operations",
            "Create Pending Shipments",
            "Some paid orders are not yet converted into Shiprocket shipments."
        )

    if revenue_trend > 10:
        add_action(
            "Low",
            "Growth",
            "Promote Winning Products",
            "Revenue is growing. Promote best-selling products and keep inventory ready."
        )

    context = {
        "current_revenue": current_revenue,
        "previous_revenue": previous_revenue,
        "current_order_count": current_order_count,
        "previous_order_count": previous_order_count,
        "current_aov": current_aov,
        "revenue_trend": revenue_trend,
        "order_trend": order_trend,
        "aov_trend": aov_trend,
        "forecast_revenue_30": forecast_revenue_30,
        "forecast_orders_30": forecast_orders_30,
        "abandoned_payments": abandoned_payments,
        "failed_notifications": failed_notifications,
        "payment_success_rate": payment_success_rate,
        "abandoned_payment_rate": abandoned_payment_rate,
        "notification_success_rate": notification_success_rate,
        "shipment_readiness_rate": shipment_readiness_rate,
        "insights": insights,
        "actions": actions,
        "health_score": health_score,
        "health_label": health_label,
    }
    return render(request, "admin/reports/insights.html", context)

@login_required
def AdminChatKeywords(request, code):
    chat_keywords = (
        ChatbotKeyword.objects
        .select_related(
            "category",
            "collection",
            "tag"
        )
        .order_by(
            "-priority",
            "-id"
        )
    )

    context = {
        "chat_keywords": chat_keywords,
    }
    return render(request, "admin/chatbot/keywords/all.html", context)

@login_required
def AdminAddChatKeywords(request, code):
    if request.method != 'POST':
        categories = Category.objects.filter(is_active=True)
        collections = Collection.objects.filter(is_active=True)
        tags = Tags.objects.filter(is_active=True)

        context = {
            'categories': categories,
            'collections': collections,
            'tags': tags
        }
        return render(request, 'admin/chatbot/keywords/add.html', context)
    
    ChatbotKeyword.objects.create(
        keyword=request.POST.get("keyword"),
        category_id=request.POST.get("category") or None,
        collection_id=request.POST.get("collection") or None,
        tag_id=request.POST.get("tag") or None,
        priority=request.POST.get("priority") or 10,
        is_active=request.POST.get("is_active") == "True"
    )

    messages.success(request, "Chat keyword added successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminUpdateChatKeywords(request, code):
    categories = Category.objects.filter(is_active=True)
    collections = Collection.objects.filter(is_active=True)
    tags = Tags.objects.filter(is_active=True)
    keyword = get_object_or_404(ChatbotKeyword, unique_code=code)

    if request.method != "POST":
        context = {
            'categories': categories,
            'collections': collections,
            'tags': tags,
            'keyword': keyword
        }
        return render(request, "admin/chatbot/keywords/update.html", context)
    
    keyword.keyword = request.POST.get("keyword")
    keyword.category_id = (request.POST.get("category") or None)
    keyword.collection_id = (request.POST.get("collection") or None)
    keyword.tag_id = (request.POST.get("tag") or None)
    keyword.priority = (request.POST.get("priority") or 10)
    keyword.is_active = (request.POST.get("is_active") == "True")
    keyword.save()

    messages.success(request, "Keyword updated successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteChatKeywords(request, code):
    if request.method == "POST":
        keyword_id = request.POST.get("keyword_id")
        keyword = get_object_or_404(ChatbotKeyword.objects.prefetch_related("products"), unique_code=keyword_id)

        try:
            with transaction.atomic():
                keyword.delete()

            messages.success(request, "Chat keyword deleted successfully.")
        except Exception:
            messages.error(request, "Something went wrong while deleting keyword.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminFaqs(request, code):
    faqs = (
        FAQ.objects
        .select_related(
            "product",
        )
        .order_by(
            "-created_at"
        )
    )

    context = {
        'faqs': faqs,
        "total_faqs": FAQ.objects.count(),
    }
    return render(request, "admin/chatbot/faqs/all.html", context)

@login_required
def AdminAddFaq(request, code):
    if request.method != "POST":
        products = Product.objects.filter(is_active=True).order_by("name")
        bundles = ProductBundle.objects.filter(is_active=True).order_by("name")

        context = {
            'products': products,
            'bundles': bundles
        }
        return render(request, "admin/chatbot/faqs/add.html", context)
    
    FAQ.objects.create(
        page=request.POST.get("page"),
        category=request.POST.get("category"),
        bundle=request.POST.get("bundle"),
        question=request.POST.get("question"),
        answer=request.POST.get("answer"),
        keywords=request.POST.get("keywords"),
        product_id=request.POST.get("products") or None,
        is_active=(
            request.POST.get("is_active") == "True"
        )
    )

    messages.success(request, "FAQ added successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminUpdateFaq(request, code):
    faq = get_object_or_404(FAQ, unique_code=code)
    selected_product = Product.objects.filter(is_active=True).order_by("name")
    selected_bundle = ProductBundle.objects.filter(is_active=True).order_by("name")
    
    if request.method != "POST":
        context = {
            'faq': faq,
            'products': selected_product,
            'bundles': selected_bundle,
        }
        return render(request, "admin/chatbot/faqs/update.html", context)
    
    faq.page = request.POST.get("page")
    faq.category = request.POST.get("category")
    faq.question = request.POST.get("question")
    faq.answer = request.POST.get("answer")
    faq.keywords = request.POST.get("keywords")
    faq.product_id = (request.POST.get("products") or None)
    faq.bundle_id = (request.POST.get("bundle") or None)
    faq.is_active = (request.POST.get("is_active") == "True")
    faq.save()

    messages.success(request, "FAQ updated successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteFaq(request, code):
    if request.method == "POST":
        faq_id = request.POST.get("faq_id")
        faq = get_object_or_404(FAQ.objects.prefetch_related("products"), unique_code=faq_id)

        try:
            with transaction.atomic():
                faq.delete()

            messages.success(request, "FAQ deleted successfully.")
        except Exception:
            messages.error(request, "Something went wrong while deleting FAQ.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminSuggestMap(request, code):
    bundles = (ProductBundle.objects.prefetch_related("products").order_by("-id"))

    context = {
        'bundles': bundles
    }
    return render(request, "admin/chatbot/suggestion-map/all.html", context)

@login_required
def AdminAddSuggestMap(request, code):
    if request.method != "POST":
        products = Product.objects.filter(is_active=True)

        context = {
            'products': products
        }
        return render(request, "admin/chatbot/suggestion-map/add.html", context)
    
    product_ids = request.POST.getlist("products")
    products = Product.objects.filter(id__in=product_ids)

    total_price = sum([p.price for p in products])
    total_discount = sum([
        p.discount_price if p.discount_price else p.price
        for p in products
    ])

    bundle_price = request.POST.get("bundle_price")
    discounted_bundle_price = request.POST.get("discounted_bundle_price")
    
    bundle = ProductBundle.objects.create(
        name=request.POST.get("name"),
        slug=request.POST.get("slug"),
        short_description=request.POST.get("short_description"),
        description=request.POST.get("description"),
        bundle_price=Decimal(bundle_price) if bundle_price else Decimal(total_price),
        discounted_bundle_price=(
            Decimal(discounted_bundle_price)
            if discounted_bundle_price
            else Decimal(total_discount)
        ),
        is_active=(
            request.POST.get("is_active")
            == "True"
        )
    )

    bundle.products.set(request.POST.getlist("products"))

    messages.success(request, "Suggestion Map Created")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminUpdateSuggestMap(request, code):
    bundle = get_object_or_404(ProductBundle, unique_code=code)
    products = Product.objects.filter(is_active=True)
    selected_ids = bundle.products.values_list("id", flat=True)

    if request.method != "POST":
        context = {
            'bundle': bundle,
            'products': products,
            "selected_ids": list(selected_ids),
        }
        return render(request, "admin/chatbot/suggestion-map/update.html", context)

    product_ids = request.POST.getlist("products")
    selected_products = Product.objects.filter(id__in=product_ids)

    total_price = sum((p.price for p in selected_products), Decimal("0.00"))
    total_discount_price = sum(
        (
            p.discount_price if p.discount_price is not None else p.price
            for p in selected_products
        ),
        Decimal("0.00")
    )

    bundle_price = request.POST.get("bundle_price")
    discounted_bundle_price = request.POST.get("discounted_bundle_price")

    bundle.name = request.POST.get("name")
    bundle.slug = request.POST.get("slug")
    bundle.short_description = request.POST.get("short_description")
    bundle.description = request.POST.get("description")

    bundle.bundle_price = (
        Decimal(bundle_price)
        if bundle_price
        else total_price
    )

    bundle.discounted_bundle_price = (
        Decimal(discounted_bundle_price)
        if discounted_bundle_price
        else total_discount_price
    )

    bundle.is_active = request.POST.get("is_active") == "True"
    bundle.save()

    bundle.products.set(selected_products)

    messages.success(request, "Suggestion Map updated successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteSuggestMap(request, code):
    if request.method == "POST":
        map_id = request.POST.get("map_id")
        map = get_object_or_404(ProductBundle.objects.prefetch_related("products"), unique_code=map_id)

        try:
            with transaction.atomic():
                map.delete()

            messages.success(request, "Bundle deleted successfully.")
        except Exception:
            messages.error(request, "Something went wrong while deleting bundle.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminMedias(request, code):
    medias = (
        NewsEvent.objects
        .prefetch_related(
            "product",
            "bundle"
        )
        .order_by("-id")
    )

    context = {
        'medias': medias
    }
    return render(request, "admin/medias/all.html", context)

@login_required
def AdminAddMedia(request, code):
    if request.method != "POST":
        products = Product.objects.filter(is_active=True).order_by("name")
        bundles = ProductBundle.objects.filter(is_active=True).order_by("name")

        context = {
            'products': products,
            'bundles': bundles
        }
        return render(request, "admin/medias/add.html", context)
    
    NewsEvent.objects.create(
        title=request.POST.get("title"),
        platform=request.POST.get("platform"),
        media_type=request.POST.get("media_type"),
        media_url=request.POST.get("media_url"),
        external_url=request.POST.get("external_url"),
        description=request.POST.get("description"),
        product_id=request.POST.get("product") or None,
        bundle_id=request.POST.get("bundle") or None,
        is_active=request.POST.get("is_active") == "True"
    )

    messages.success(request, "Media added successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminUpdateMedia(request, code):
    media = get_object_or_404(NewsEvent, unique_code=code)
    bundle = get_object_or_404(ProductBundle, unique_code=code)
    products = Product.objects.filter(is_active=True).order_by("name")
    selected_ids = list(media.products.values_list("id", flat=True))
    selected_bundle = (media.bundle.id if media.bundle else None)

    if request.method != "POST":
        context = {
            'media': media,
            'bundle': bundle,
            'products': products,
            "selected_ids": selected_ids,
            "selected_bundle": selected_bundle,
        }
        return render(request, "admin/medias/update.html", context)
    
    media.title = request.POST.get("title")
    media.platform = request.POST.get("platform")
    media.media_type = request.POST.get("media_type")
    media.media_url = request.POST.get("media_url")
    media.external_url = request.POST.get("external_url")
    media.description = request.POST.get("description")
    media.product_id = (request.POST.get("product") or None)
    media.bundle_id = (request.POST.get("bundle") or None)
    media.is_active = (request.POST.get("is_active") == "True")
    media.save()

    messages.success(request, "Media updated successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteMedia(request, code):
    if request.method == "POST":
        media_id = request.POST.get("media_id")
        media = get_object_or_404(NewsEvent.objects.prefetch_related("products"), unique_code=media_id)

        try:
            with transaction.atomic():
                media.delete()

            messages.success(request, "Media deleted successfully.")
        except Exception:
            messages.error(request, "Something went wrong while deleting media.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminSupportTickets(request, code):
    tickets = SupportTicket.objects.all()

    context = {
        'tickets': tickets
    }
    return render(request, "admin/support/all.html", context)

@login_required
def AdminCreateSupportTicket(request, code):
    if request.method != "POST":
        customers = Customer.objects.order_by("name")
        orders = Order.objects.select_related("customer").order_by("-id")

        context = {
            "customers": customers,
            "orders": orders,
        }
        return render(request, "admin/support/add.html", context)
    
    SupportTicket.objects.create(
        customer_id=request.POST.get("customer") or None,
        order_id=request.POST.get("order") or None,
        subject=request.POST.get("subject"),
        message=request.POST.get("message"),
        status=request.POST.get("status")
    )

    messages.success(request, "Support ticket created successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminUpdateSupportTicket(request, code):
    ticket = get_object_or_404(SupportTicket, unique_code=code)
    customers = Customer.objects.order_by("name")
    orders = Order.objects.select_related("customer").order_by("-id")

    if request.method != "POST":
        context = {
            "ticket": ticket,
            "customers": customers,
            "orders": orders,
        }
        return render(request, "admin/support/update.html", context)
    
    ticket.customer_id = (request.POST.get("customer") or None)
    ticket.order_id = (request.POST.get("order") or None)
    ticket.subject = request.POST.get("subject")
    ticket.message = request.POST.get("message")
    ticket.status = request.POST.get("status")
    ticket.save()

    messages.success(request, "Support ticket updated successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteSupportTicket(request, code):
    if request.method == "POST":
        ticket_id = request.POST.get("ticket_id")
        ticket = get_object_or_404(SupportTicket.objects.prefetch_related("products"), unique_code=ticket_id)

        try:
            with transaction.atomic():
                ticket.delete()

            messages.success(request, "Support ticket deleted successfully.")
        except Exception:
            messages.error(request, "Something went wrong while deleting support ticket.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def SignOut(request):
    account = User.objects.filter(unique_code=request.user.unique_code).first()
    account.is_online = False
    account.save()

    request.session.flush()
    logout(request)
    return redirect("SignIn")

