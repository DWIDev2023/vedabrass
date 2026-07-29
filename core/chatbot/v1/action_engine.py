from django.urls import reverse
from core.models import Order, SupportTicket, Review
from core.chatbot.v1.recommendation_engine import RecommendationEngine
from core.chatbot.v1.faq_engine import FAQEngine


class ActionEngine:
    @staticmethod
    def support_links():
        return [
            {
                "label": "WhatsApp Support",
                "url": "https://wa.me/918712495444"
            },
            {
                "label": "Contact Page",
                "url": "/contact-us"
            }
        ]

    @staticmethod
    def execute(action, message=None, context=None, chat_session=None):
        context = context or {}

        if action == "TRACK_ORDER":
            return ActionEngine.track_order(message)

        if action == "GET_INVOICE":
            return ActionEngine.get_invoice(message)

        if action == "SHIPPING_HELP":
            return {
                "reply": "Orders are processed after successful payment. Once shipped, tracking details are shared by email, SMS or WhatsApp.",
                "links": [
                    {"label": "Track Order", "url": "/track-order"},
                    {"label": "Shipping Policy", "url": "/shipping-policy"},
                    {"label": "Contact Support", "url": "/contact-us"}
                ]
            }

        if action == "RECOMMEND_PRODUCTS":
            recommendation = RecommendationEngine.recommend(
                context=context,
                message=message,
                limit=5
            )

            products = recommendation.get("products", [])
            links = recommendation.get("links", [])
            category = recommendation.get("category")

            if products:
                return {
                    "reply": recommendation.get(
                        "reply",
                        "Here are some products you may like."
                    ),
                    "products": products,
                    "links": links,
                    "category": category,
                    "quick_replies": [
                        {"label": "Main Menu", "message": "Main Menu"},
                        {"label": "Talk to Support", "message": "Talk to Support"},
                    ]
                }

            return {
                "reply": "I could not find exact matching products right now. You can view all products from the selected category or contact support.",
                "links": links or ActionEngine.support_links()
            }

        if action == "FAQ_LOOKUP":
            result = FAQEngine.find_answer(message)

            if result["found"]:
                return {
                    "reply": result["answer"]
                }

            return {
                "reply": "I could not find a clear answer for that. Please contact support for help.",
                "links": ActionEngine.support_links()
            }

        if action == "SHOW_SUPPORT":
            ActionEngine.create_support_ticket(
                chat_session=chat_session,
                message=message
            )

            return {
                "reply": "You can connect with VedaBrass support using the options below.",
                "links": ActionEngine.support_links()
            }

        return {
            "reply": "I could not process that request. Please try again."
        }

    @staticmethod
    def track_order(message):
        order_id = str(message or "").strip()

        order = Order.objects.filter(
            order_id__iexact=order_id,
            is_deleted=False
        ).select_related("customer").first()

        if not order:
            order = Order.objects.filter(
                unique_code__iexact=order_id,
                is_deleted=False
            ).select_related("customer").first()

        if not order:
            return {
                "reply": "I could not find this Order ID. Please check and try again.",
                "quick_replies": [
                    {"label": "Try Again", "message": "Track Order"},
                    {"label": "Talk to Support", "message": "Talk to Support"}
                ]
            }
        
        review_links = []

        for item in order.items.select_related("product").all():
            already_reviewed = Review.objects.filter(
                product=item.product,
                customer=order.customer
            ).exists()

            if not already_reviewed:
                review_links.append({
                    "label": f"Review {item.product.name}",
                    "url": reverse(
                        "ProductDetails",
                        kwargs={"slug": item.product.slug}
                    )
                })

        links = []

        if order.tracking_url:
            links.append({
                "label": "Open Tracking",
                "url": order.tracking_url
            })

        links.append({
            "label": "Track Page",
            "url": "/track-order"
        })
        links.extend(review_links)

        return {
            "reply": f"Order {order.order_id} is currently {order.status}. Payment status: {order.payment_status}.",
            "links": links
        }

    @staticmethod
    def get_invoice(message):
        order_id = str(message or "").strip()

        order = Order.objects.filter(
            order_id__iexact=order_id,
            is_deleted=False,
            payment_status="Paid"
        ).first()

        if not order:
            order = Order.objects.filter(
                unique_code__iexact=order_id,
                is_deleted=False,
                payment_status="Paid"
            ).first()

        if not order or not order.invoice_number:
            return {
                "reply": "Invoice is available only for paid orders. Please check your Order ID.",
                "quick_replies": [
                    {"label": "Try Again", "message": "Download Invoice"},
                    {"label": "Talk to Support", "message": "Talk to Support"}
                ]
            }

        return {
            "reply": f"Invoice for order {order.order_id} is available.",
            "links": [
                {
                    "label": "Download Invoice",
                    "url": reverse(
                        "InvoiceView",
                        kwargs={"invoice_number": order.invoice_number}
                    )
                }
            ]
        }

    @staticmethod
    def create_support_ticket(chat_session=None, message=None):
        if not chat_session:
            return None

        return SupportTicket.objects.create(
            session=chat_session,
            subject="Chatbot Support Request",
            message=message or "Customer requested chatbot support.",
            status="Open"
        )