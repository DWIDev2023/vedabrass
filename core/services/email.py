from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from datetime import datetime
from core.services.log_service import create_notification_log
from core.services.notifications import (
    ORDER_PAID,
    TRACKING_AVAILABLE,
    ORDER_CANCELLED,
    PAYMENT_ABANDONED,
    INVOICE_AVAILABLE
)


def send_email_with_log(order, event, subject, body, html, recipients, recipient_label=None):
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        email.attach_alternative(html, "text/html")
        email.send(fail_silently=False)

        create_notification_log(
            order=order,
            channel="Email",
            event=event,
            status="Success",
            recipient=recipient_label or ", ".join(recipients),
            response="Email sent successfully",
        )

    except Exception as e:
        create_notification_log(
            order=order,
            channel="Email",
            event=event,
            status="Failed",
            recipient=recipient_label or ", ".join(recipients),
            response=str(e),
        )
        raise


def send_order_confirmation_email(order):
    customer = order.customer
    order_items = order.items.select_related("product")

    context = {
        "order": order,
        "customer": customer,
        "order_items": order_items,
        "billing_address": order.billing_address,
        "shipping_address": order.shipping_address,
    }

    customer_html = render_to_string(
        "emails/order_confirmation.html",
        context
    )

    send_email_with_log(
        order=order,
        event=ORDER_PAID,
        subject=f"Order Confirmation - {order.order_id}",
        body=f"Thank you for your order {order.order_id}",
        html=customer_html,
        recipients=[customer.email],
        recipient_label=customer.email,
    )

    admin_html = render_to_string(
        "emails/new_order_admin.html",
        context
    )

    send_email_with_log(
        order=order,
        event=ORDER_PAID,
        subject=f"New Paid Order Received - {order.order_id}",
        body=f"New paid order received {order.order_id}",
        html=admin_html,
        recipients=settings.ORDER_ADMIN_EMAILS,
        recipient_label=", ".join(settings.ORDER_ADMIN_EMAILS),
    )


def send_tracking_update_email(order):
    if not order.tracking_url:
        create_notification_log(
            order=order,
            channel="Email",
            event=TRACKING_AVAILABLE,
            status="Failed",
            recipient=order.customer.email if order.customer else None,
            response="Tracking URL not available",
        )
        return

    context = {
        "order": order,
        "customer": order.customer,
    }

    html = render_to_string(
        "emails/tracking_update.html",
        context
    )

    send_email_with_log(
        order=order,
        event=TRACKING_AVAILABLE,
        subject=f"Tracking Details - {order.order_id}",
        body=f"Your tracking details are available for order {order.order_id}.",
        html=html,
        recipients=[order.customer.email],
        recipient_label=order.customer.email,
    )


def send_order_cancelled_email(order):
    context = {
        "order": order,
        "customer": order.customer,
    }

    html = render_to_string(
        "emails/order_cancelled.html",
        context
    )

    send_email_with_log(
        order=order,
        event=ORDER_CANCELLED,
        subject=f"Order Cancelled - {order.order_id}",
        body=f"Your order {order.order_id} has been cancelled.",
        html=html,
        recipients=[order.customer.email],
        recipient_label=order.customer.email,
    )


def send_abandoned_payment_email(order):
    customer = order.customer

    context = {
        "order": order,
        "customer": customer,
        "resume_url": settings.SITE_URL + reverse(
            "PayURedirect",
            kwargs={"order_id": order.order_id}
        )
    }

    html = render_to_string(
        "emails/payment_reminder.html",
        context
    )

    send_email_with_log(
        order=order,
        event=PAYMENT_ABANDONED,
        subject=f"Complete Your Vedabrass Order - {order.order_id}",
        body="Your order is waiting for payment.",
        html=html,
        recipients=[customer.email],
        recipient_label=customer.email,
    )


def send_invoice_email(order):
    customer = order.customer

    context = {
        "order": order,
        "customer": customer,
        "billing_address": order.billing_address,
        "shipping_address": order.shipping_address,
        "order_items": order.items.select_related("product"),
    }

    html = render_to_string("emails/invoice_email.html", context)

    send_email_with_log(
        order=order,
        event=INVOICE_AVAILABLE,
        subject=f"Invoice - {order.invoice_number}",
        body=f"Invoice for your Vedabrass order {order.order_id}.",
        html=html,
        recipients=[customer.email],
        recipient_label=customer.email,
    )

    order.invoice_email_sent = True
    order.invoice_email_sent_at = datetime.now()
    order.save(update_fields=["invoice_email_sent", "invoice_email_sent_at"])


def send_order_email_event(order, event):
    try:
        if event == ORDER_PAID:
            send_order_confirmation_email(order)

        elif event == TRACKING_AVAILABLE:
            send_tracking_update_email(order)

        elif event == ORDER_CANCELLED:
            send_order_cancelled_email(order)

        elif event == PAYMENT_ABANDONED:
            send_abandoned_payment_email(order)

        elif event == INVOICE_AVAILABLE:
            send_invoice_email(order)

    except Exception as e:
        print("EMAIL NOTIFICATION ERROR:", e)