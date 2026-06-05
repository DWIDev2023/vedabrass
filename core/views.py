from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from decimal import Decimal
from django.core.mail import send_mail, EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from email.utils import formataddr
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.urls import reverse, NoReverseMatch
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Prefetch, Sum, Count
from decimal import Decimal, InvalidOperation
from django.apps import apps
from django.contrib import messages
from functools import wraps
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from django.db import IntegrityError, transaction
from django.db.models import Q
from collections import defaultdict
from django.conf import settings
from .models import *
from .serializers import *
import json, requests, traceback, random, string, secrets, pycountry, pytz, math

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
    ).order_by("?")[:5]

    new_products = Product.objects.filter(
        is_active=True
    ).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("-is_primary"),
            to_attr="ordered_images"
        )
    ).order_by("-created_at")[:5]

    stone_products = Product.objects.filter(
        is_active=True,
        category__slug="stone-idols"
    ).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("-is_primary"),
            to_attr="ordered_images"
        )
    ).order_by("-created_at")[:5]

    gift_collections = Collection.objects.filter(
        is_active=True,
        category__slug="festival-gifts"
    ).order_by("?")[:5]
    
    all_products = list(trending_products) + list(new_products) + list(stone_products)

    for product in all_products:
        if product.discount_price and product.price and product.discount_price < product.price:
            product.discount_percentage = round(
                ((product.price - product.discount_price) / product.price) * 100
            )
        else:
            product.discount_percentage = 0

    context = {
        "meta_title": "Vedabrass | Welcome Page",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
        "trending_products": trending_products,
        "new_products": new_products,
        "stone_products": stone_products,
        "gift_collections": gift_collections
    }
    return render(request, 'index.html', context)

def WhoWeAre(request):
    context = {
        "meta_title": "Vedabrass | Who We Are",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
    }
    return render(request, 'web/about.html', context)

def Categories(request):
    categories = Category.objects.filter(parent__isnull=True)

    context = {
        "meta_title": "Vedabrass | Categories",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
        "categories": categories
    }
    return render(request, 'web/categories.html', context)

def Subcategory(request, slug):
    category = Category.objects.filter(slug=slug).first()
    subcategories = Category.objects.filter(parent=category)

    context = {
        "meta_title": "Vedabrass | Subcategories",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
        "category": category,
        "subcategories": subcategories
    }
    return render(request, 'web/subcategories.html', context)

def Collections(request, slug):
    subcategory = Category.objects.filter(slug=slug).first()
    collections = Collection.objects.filter(category_id=subcategory.id)

    context = {
        "meta_title": "Vedabrass | Collections",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
        "subcategory": subcategory,
        "collections": collections
    }
    return render(request, 'web/collections.html', context)

def SearchProducts(request):
    query = request.GET.get("productquery", "").strip()
    products = Product.objects.none()

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query) |
            Q(collections__name__icontains=query),
            is_active=True
        ).select_related(
            "category",
            "vendor",
            "inventory"
        ).prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("-is_primary"),
                to_attr="ordered_images"
            ),
            "collections",
            "attributes"
        ).distinct()

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

    context = {
        "meta_title": "Vedabrass | All Products",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
        "categories": categories,
        "products": products
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
        "meta_title": "Vedabrass | Welcome Page",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
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
        "meta_title": "Vedabrass | Welcome Page",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
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
    products = Product.objects.filter(
        is_active=True, collection=collection
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
        "meta_title": "Vedabrass | Welcome Page",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
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
        "meta_title": "Vedabrass | All Products",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
        "categories": categories,
        "products": products
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

    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(
        id=product.id
    ).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("-is_primary"),
            to_attr="ordered_images"
        )
    )[:4]

    for related in related_products:
        if (related.discount_price and related.price and related.discount_price < related.price):
            related.discount_percentage = round(((related.price - related.discount_price) / related.price) * 100)
        else:
            related.discount_percentage = 0

    context = {
        "meta_title": "Vedabrass | Welcome Page",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
        "product": product,
        "category": category,
        "subcategory": subcategory,
        "related_products": related_products,
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

    context = {
        "cart": cart,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "total": subtotal
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
        "cart": cart,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping": 0,
        "total": subtotal,
    }
    return render(request, 'web/products/checkout.html', context)

def PlaceOrder(request):
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
        return redirect("Checkout")

    try:
        with transaction.atomic():
            customer = Customer.objects.filter(email=email).first()

            if not customer:
                customer = Customer.objects.create(
                    name=name,
                    email=email,
                    mobile=mobile,
                    company_name=company_name,
                    gst_number=gst_number,
                )
            else:
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
                status="Pending"
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
            cart.is_completed = True
            cart.save()

            cart.items.all().delete()

            request.session.pop("cart_id", None)
            request.session.modified = True

            def send_order_emails():
                try:
                    order_items = order.items.select_related("product")
                    customer_context = {
                        "order": order,
                        "customer": customer,
                        "order_items": order_items,
                    }
                    customer_html = render_to_string(
                        "emails/order_confirmation.html",
                        customer_context
                    )
                    customer_email = EmailMultiAlternatives(
                        subject=f"Order Confirmation - {order.order_id}",
                        body=f"Thank you for your order {order.order_id}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[customer.email],
                    )
                    customer_email.attach_alternative(customer_html, "text/html")
                    customer_email.send()

                    admin_html = render_to_string(
                        "emails/new_order_admin.html",
                        customer_context
                    )
                    admin_email = EmailMultiAlternatives(
                        subject=f"New Order Received - {order.order_id}",
                        body=f"New order received {order.order_id}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=settings.ORDER_ADMIN_EMAILS,
                    )
                    admin_email.attach_alternative(admin_html, "text/html")
                    admin_email.send()
                except Exception as e:
                    print("EMAIL ERROR:", e)

            transaction.on_commit(send_order_emails)

        messages.success(request, "Order placed successfully.")

        return redirect("ThankYou", code=order.unique_code)
    except Exception as e:
        print("PLACE ORDER ERROR:", e)
        messages.error(request,f"Something went wrong: {e}")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

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
        parent_category = first_item.product.category.parent

        recommended_products = Product.objects.filter(
            is_active=True,
            category__parent=parent_category
        ).exclude(
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
        "meta_title": "Vedabrass | Welcome Page",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
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
        "meta_title": "Vedabrass | Track Order",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
        "order": order
    }
    return render(request, 'web/track-order.html', context)

def Contact(request):
    if request.method != 'POST':
        context = {
            "meta_title": "Vedabrass | Welcome Page",
            "meta_description": "Vedabrass handcrafted brass idols",
            "meta_keywords": "brass idols, decor",
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

def PrivayPolicy(request):
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
        "meta_title": "Vedabrass | Welcome Page",
        "meta_description": "Vedabrass handcrafted brass idols",
        "meta_keywords": "brass idols, decor",
        "blogs": blogs,
        "featured_blog": featured_blog,
        "categories": categories,
    }
    return render(request, 'web/blogs/all.html', context)

def BlogDetails(request, slug):
    blog = get_object_or_404(Blog.objects.select_related("category"), slug=slug, is_active=True)
    related_blogs = Blog.objects.filter(is_active=True, category=blog.category).exclude(id=blog.id)[:3]
    latest_blogs = Blog.objects.filter(is_active=True).exclude(id=blog.id).order_by("-created_at")[:5]

    context = {
        "meta_title": blog.title,
        "meta_description": blog.short_description,
        "blog": blog,
        "related_blogs": related_blogs,
        "latest_blogs": latest_blogs,
    }
    return render(request, "web/blogs/details.html",context)

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
    product_id = request.POST.get("product", "").strip()
    product = get_object_or_404(Product, unique_code=product_id, is_active=True)

    if request.method == "POST":
        Review.objects.create(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            name=request.POST.get("name", "").strip(),
            email=request.POST.get("email", "").strip() or None,
            title=request.POST.get("title", "").strip(),
            rating=request.POST.get("rating"),
            comment=request.POST.get("comment", "").strip(),
            image=request.FILES.get("image"),
            is_approved=False
        )

        messages.success(request, "Review submitted successfully. It will appear after admin approval.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

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
    pending_orders = Order.objects.filter(status="Pending").count()
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

    context = {
        "order": order
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

    if request.method != "POST":
        context = {
            "order": order
        }
        return render(request, "admin/web/orders/edit.html", context)
    
    try:
        with transaction.atomic():
            order.status = request.POST.get("status") or order.status

            order.shipping = to_decimal(
                request.POST.get("shipping"),
                order.shipping
            )

            order.total = order.subtotal + order.shipping

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

            order.save()

        messages.success(request, "Order updated successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except Exception as e:
        messages.error(request, f"Something went wrong: {e}")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteOrder(request, code):
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        order = get_object_or_404(Order, unique_code=order_id)
        order.delete()

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
    
    name = request.POST.get("name", "").strip()
    slug = request.POST.get("slug", "").strip()
    brand = request.POST.get("brand", "").strip()
    description = request.POST.get("description") or None

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
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not slug:
        messages.error(request, "Slug is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not final_category_id:
        messages.error(request, "Category is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not vendor_id:
        messages.error(request, "Vendor is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not collection_id:
        messages.error(request, "Collection is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not price:
        messages.error(request, "Price is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not quantity:
        messages.error(request, "Quantity is required.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if Product.objects.filter(slug=slug).exclude(id=product.id).exists():
        messages.error(request, "Slug already exists.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    category = get_object_or_404(Category, id=final_category_id)
    vendor = get_object_or_404(Vendor, id=vendor_id)
    collection = get_object_or_404(Collection, id=collection_id)

    try:
        with transaction.atomic():
            selected_tags = Tags.objects.filter(id__in=tag_ids, is_active=True)

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
                category_id__in=category_ids,
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

                # product_code format:
                # ccode + vcode + material_code + hcode + scode + pcode
                # scode is before last 4 digits
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
            product.description = description
            product.brand = brand
            product.is_active = is_active
            product.save()

            product.tags.set(tag_ids)

            inventory, created = ProductInventory.objects.get_or_create(product=product)
            inventory.quantity = int(quantity)
            inventory.low_stock_threshold = int(low_stock_threshold)
            inventory.save()

            if delete_images:
                ProductImage.objects.filter(id__in=delete_images, product=product).delete()

            ProductImage.objects.filter(product=product).update(is_primary=False)

            for image_id, alt_text in zip(existing_image_ids, existing_alt_texts):
                if str(image_id) in delete_images:
                    continue

                image_obj = ProductImage.objects.filter(id=image_id, product=product).first()

                if image_obj:
                    image_obj.alt_text = alt_text
                    image_obj.is_primary = str(image_obj.id) == str(primary_existing_image)
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
    categories = BlogCategory.objects.all().order_by("-created_at")

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

    Blog.objects.create(
        category_id=request.POST.get("category"),
        title=title,
        slug=slug,
        image=request.FILES.get("image"),
        short_description=request.POST.get("short_description", "").strip(),
        content=request.POST.get("content", "").strip(),

        meta_title=request.POST.get("meta_title", "").strip() or title,
        meta_description=request.POST.get("meta_description", "").strip(),
        meta_keywords=request.POST.get("meta_keywords", "").strip(),

        is_featured=request.POST.get("is_featured") == "True",
        is_active=request.POST.get("is_active") == "True",
    )

    messages.success(request, "Blog created successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminEditBlog(request, code):
    blog = get_object_or_404(Blog, unique_code=code)
    categories = BlogCategory.objects.filter(is_active=True)

    if request.method != "POST":
        context = {
            "blog": blog,
            "categories": categories
        }
        return render(request, "admin/blogs/edit.html", context)

    blog.category_id = request.POST.get("category")
    blog.title = request.POST.get("title", "").strip()
    blog.slug = request.POST.get("slug", "").strip() or slugify(blog.title)
    blog.short_description = request.POST.get("short_description", "").strip()
    blog.content = request.POST.get("content", "").strip()

    blog.meta_title = request.POST.get("meta_title", "").strip() or blog.title
    blog.meta_description = request.POST.get("meta_description", "").strip()
    blog.meta_keywords = request.POST.get("meta_keywords", "").strip()

    blog.is_featured = request.POST.get("is_featured") == "True"
    blog.is_active = request.POST.get("is_active") == "True"

    if request.FILES.get("image"):
        blog.image = request.FILES.get("image")

    blog.save()

    messages.success(request, "Blog updated successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminDeleteBlog(request, code):
    if request.method == "POST":
        blog_id = request.POST.get("blog_id")
        blog = get_object_or_404(Blog, unique_code=blog_id)
        blog.delete()

        messages.success(request, "Blog deleted successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def AdminAccSettings(request, code):
    return render(request, 'admin/settings.html')



@login_required
def SignOut(request):
    account = User.objects.filter(unique_code=request.user.unique_code).first()
    account.is_online = False
    account.save()

    request.session.flush()
    logout(request)
    return redirect("SignIn")