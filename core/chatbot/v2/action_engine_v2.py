from django.urls import reverse
from core.models import (
    Customer,
    Order,
    Review,
    SupportTicket,
)
from .recommendation_engine_v2 import RecommendationEngineV2
from .faq_engine_v2 import FAQEngineV2


class ActionEngineV2:
    @staticmethod
    def _faq_log(faq):
        if not faq:
            return None

        return {
            "id": getattr(faq, "id", None),
            "question": getattr(faq, "question", None),
        }

    @staticmethod
    def _model_log(obj):
        if not obj:
            return None

        return {
            "id": getattr(obj, "id", None),
            "name": getattr(obj, "name", None),
            "slug": getattr(obj, "slug", None),
        }

    @staticmethod
    def _ticket_log(ticket):
        if not ticket:
            return None

        return {
            "id": ticket.id,
            "status": ticket.status,
            "subject": ticket.subject,
        }

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
    def get_or_create_customer(
        name,
        email,
        mobile,
    ):

        customer = None

        if mobile:
            customer = Customer.objects.filter(
                mobile=mobile
            ).first()

        if not customer and email:
            customer = Customer.objects.filter(
                email__iexact=email
            ).first()

        if customer:

            if name:
                customer.name = name

            if email:
                customer.email = email

            if mobile:
                customer.mobile = mobile

            customer.customer_type = "Potential"

            customer.save()

            return customer

        return Customer.objects.create(
            name=name or "Website Lead",
            email=email,
            mobile=mobile,
            customer_type="Potential",
        )
    
    @staticmethod
    def create_support_ticket(
        chat_session=None,
        context=None,
        message=None
    ):

        if not chat_session:
            return None

        context = context or {}

        customer = ActionEngineV2.get_or_create_customer(
            name=context.get("customer_name"),
            email=context.get("customer_email"),
            mobile=context.get("customer_mobile"),
        )

        chat_session.customer = customer
        chat_session.save(update_fields=["customer"])

        return SupportTicket.objects.create(
            session=chat_session,
            customer=customer,
            subject="Chatbot Support Request",
            message=message or "Customer requested chatbot support.",
            status="Open",
        )

    @staticmethod
    def execute(
        action,
        message=None,
        context=None,
        chat_session=None
    ):

        context = context or {}

        if action == "TRACK_ORDER":
            return ActionEngineV2.track_order(message)

        if action == "GET_INVOICE":
            return ActionEngineV2.get_invoice(message)

        if action == "SHIPPING_HELP":
            return {
                "reply": (
                    "Orders are processed after successful payment. "
                    "Once shipped, tracking details are shared via Email, SMS or WhatsApp."
                ),
                "links": [
                    {
                        "label": "Track Order",
                        "url": "/track-order"
                    },
                    {
                        "label": "Shipping Policy",
                        "url": "/shipping-policy"
                    },
                    {
                        "label": "Contact Support",
                        "url": "/contact-us"
                    }
                ],
                "log": {
                    "result_type": "FAQ",
                    "matched_faq": None,
                    "matched_bundle": None,
                    "matched_products": [],
                }
            }

        if action == "RECOMMEND_PRODUCTS":

            result = RecommendationEngineV2.recommend(
                message=message,
                context=context,
                limit=5
            )

            return {
                "reply": result.get("reply"),
                "products": result.get("products", []),
                "bundle": result.get("bundle"),
                "links": result.get("links", []),
                "category": result.get("category"),
                "quick_replies": result.get("quick_replies", []),
                "log": result.get("log"),
            }

        if action == "FAQ_LOOKUP":

            faq = FAQEngineV2.search(message)

            if faq["found"]:

                return {
                    "reply": faq["answer"],
                    "log": {
                        "result_type": "FAQ",
                        "matched_faq": ActionEngineV2._faq_log(faq["faq"]),
                        "matched_bundle": ActionEngineV2._model_log(faq.get("bundle")),
                        "matched_products": (
                            [ActionEngineV2._model_log(faq["product"])]
                            if faq.get("product")
                            else []
                        )
                    }
                }

            return {
                "reply": (
                    "I couldn't find a clear answer for that. "
                    "Please contact support."
                ),
                "links": ActionEngineV2.support_links(),
                "log": {
                    "result_type": "EMPTY",
                    "matched_faq": None,
                    "matched_bundle": None,
                    "matched_products": [],
                }
            }

        if action == "SHOW_SUPPORT":

            ticket = ActionEngineV2.create_support_ticket(
                chat_session=chat_session,
                context=context,
                message=message,
            )

            return {
                "reply": (
                    "Our support team has received your request. "
                    "You can also continue on WhatsApp using the link below."
                ),
                "links": ActionEngineV2.support_links(),
                "log": {
                    "result_type": "SUPPORT",
                    "matched_faq": None,
                    "matched_bundle": None,
                    "matched_products": [],
                    "support_ticket": ActionEngineV2._ticket_log(ticket),
                }
            }

        return {
            "reply": (
                "I couldn't process your request. Please try again."
            ),
            "log": {
                "result_type": "EMPTY",
                "matched_faq": None,
                "matched_bundle": None,
                "matched_products": [],
            }
        }

    @staticmethod
    def track_order(message):

        order_id = str(message or "").strip()

        order = (
            Order.objects.filter(
                order_id__iexact=order_id,
                is_deleted=False
            )
            .select_related("customer")
            .first()
        )

        if not order:

            order = (
                Order.objects.filter(
                    unique_code__iexact=order_id,
                    is_deleted=False
                )
                .select_related("customer")
                .first()
            )

        if not order:

            return {
                "reply": (
                    "I couldn't find this Order ID."
                ),
                "quick_replies": [
                    {
                        "label": "Try Again",
                        "message": "Track Order"
                    },
                    {
                        "label": "Talk to Support",
                        "message": "Talk to Support"
                    }
                ]
            }

        review_links = []

        for item in order.items.select_related("product").all():

            already_reviewed = Review.objects.filter(
                product=item.product,
                customer=order.customer
            ).exists()

            if not already_reviewed:

                review_links.append(
                    {
                        "label": f"Review {item.product.name}",
                        "url": reverse(
                            "ProductDetails",
                            kwargs={
                                "slug": item.product.slug
                            }
                        )
                    }
                )

        links = []

        if order.tracking_url:

            links.append(
                {
                    "label": "Open Tracking",
                    "url": order.tracking_url
                }
            )

        links.append(
            {
                "label": "Track Page",
                "url": "/track-order"
            }
        )

        links.extend(review_links)

        return {
            "reply": (
                f"Order {order.order_id} is currently "
                f"{order.status}. "
                f"Payment Status: {order.payment_status}."
            ),
            "links": links,
            "log": {
                "result_type": "TRACK_ORDER",
                "matched_faq": None,
                "matched_bundle": None,
                "matched_products": [],
            }
        }

    @staticmethod
    def get_invoice(message):

        order_id = str(message or "").strip()

        order = (
            Order.objects.filter(
                order_id__iexact=order_id,
                payment_status="Paid",
                is_deleted=False
            )
            .first()
        )

        if not order:

            order = (
                Order.objects.filter(
                    unique_code__iexact=order_id,
                    payment_status="Paid",
                    is_deleted=False
                )
                .first()
            )

        if not order or not order.invoice_number:

            return {
                "reply": (
                    "Invoice is available only for paid orders."
                ),
                "quick_replies": [
                    {
                        "label": "Try Again",
                        "message": "Download Invoice"
                    },
                    {
                        "label": "Talk to Support",
                        "message": "Talk to Support"
                    }
                ]
            }

        return {
            "reply": (
                f"Invoice for order {order.order_id} is ready."
            ),
            "links": [
                {
                    "label": "Download Invoice",
                    "url": reverse(
                        "InvoiceView",
                        kwargs={
                            "invoice_number": order.invoice_number
                        }
                    )
                }
            ],
            "log": {
                "result_type": "INVOICE",
                "matched_faq": None,
                "matched_bundle": None,
                "matched_products": [],
            }
        }

    @staticmethod
    def create_basic_support_ticket(
        chat_session=None,
        message=None
    ):

        if not chat_session:
            return None

        return SupportTicket.objects.create(
            session=chat_session,
            customer=getattr(chat_session, "customer", None),
            subject="Chatbot Support Request",
            message=message or "Customer requested chatbot support.",
            status="Open"
        )