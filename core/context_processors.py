from django.db.models import Sum
from .models import Collection, Category, Cart, CartItem, FAQ
from .schema.builders.organization import organization_schema
from .schema.builders.faq import faq_schema

def menu_collections(request):
    gods = Collection.objects.filter(
        category__slug="god",
        is_active=True
    ).only("name", "slug")

    goddess = Collection.objects.filter(
        category__slug="goddess",
        is_active=True
    ).only("name", "slug")

    popular = Category.objects.filter(
        parent_id=1,
        is_active=True
    ).exclude(
        slug__in=["god", "goddess"]
    ).only(
        "name",
        "slug"
    ).order_by("name")

    home_decore = Category.objects.filter(
        parent__slug="home-decor",
        is_active=True
    ).only(
        "name",
        "slug"
    )

    pooja_essentials = Category.objects.filter(
        parent__slug="pooja-essentials",
        is_active=True
    ).only(
        "name",
        "slug"
    )

    home_essentials = Category.objects.filter(
        parent__slug="kitchen-essentials",
        is_active=True
    ).only(
        "name",
        "slug"
    )

    return {
        "menu_gods": gods,
        "menu_goddess": goddess,
        "menu_popular": popular,
        "menu_home_decore": home_decore,
        "menu_pooja_essentials": pooja_essentials,
        "menu_home_essentials": home_essentials
    }

def cart_data(request):
    cart_count = 0

    cart_id = request.session.get("cart_id")
    session_key = request.session.session_key

    cart = None

    if cart_id:
        cart = Cart.objects.filter(
            id=cart_id,
            is_completed=False
        ).first()

    if not cart and session_key:
        cart = Cart.objects.filter(
            session_key=session_key,
            is_completed=False
        ).first()

    if cart:
        cart_count = CartItem.objects.filter(
            cart=cart
        ).aggregate(
            total=Sum("quantity")
        )["total"] or 0

        request.session["cart_id"] = cart.id
        request.session.modified = True
    
    return {
        "cart_count": cart_count
    }

def canonical_url(request):
    return {
        "canonical_url": request.build_absolute_uri(request.path)
    }

def page_faqs(request):
    page = request.path

    # Skip dynamic product pages
    if page.startswith("/products/"):
        return {"page_faqs": []}

    faqs = FAQ.objects.filter(
        page=page,
        is_active=True
    ).order_by("created_at")

    return {
        "page_faqs": faqs
    }

