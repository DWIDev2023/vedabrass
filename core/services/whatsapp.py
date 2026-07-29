import json
import requests
from django.urls import reverse
from django.conf import settings
from core.services.notifications import (
    ORDER_PAID,
    TRACKING_AVAILABLE,
    ORDER_CANCELLED,
    PAYMENT_ABANDONED,
    INVOICE_AVAILABLE
)
from core.services.log_service import create_notification_log


def normalize_indian_mobile(mobile):
    mobile = str(mobile or "").strip().replace(" ", "").replace("-", "")

    if mobile.startswith("+"):
        mobile = mobile.replace("+", "")

    if mobile.startswith("91") and len(mobile) == 12:
        return mobile

    if len(mobile) == 10:
        return f"91{mobile}"

    return mobile


def send_whatsapp_template(order, to, template_name, event, parameters=None):
    mobile = normalize_indian_mobile(to)

    if not settings.WHATSAPP_ENABLED:
        create_notification_log(
            order=order,
            channel="WhatsApp",
            event=event,
            status="Failed",
            recipient=mobile,
            response="WhatsApp Disabled",
        )
        return None

    if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        create_notification_log(
            order=order,
            channel="WhatsApp",
            event=event,
            status="Failed",
            recipient=mobile,
            response="WhatsApp Config Missing",
        )
        return None

    if not template_name:
        create_notification_log(
            order=order,
            channel="WhatsApp",
            event=event,
            status="Failed",
            recipient=mobile,
            response="WhatsApp Template Missing",
        )
        return None

    url = (
        f"https://graph.facebook.com/v20.0/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    components = []

    if parameters:
        components.append({
            "type": "body",
            "parameters": [
                {
                    "type": "text",
                    "text": str(value)
                }
                for value in parameters
            ]
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": mobile,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": settings.WHATSAPP_LANGUAGE_CODE
            },
            "components": components
        }
    }

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )

        response_text = response.text[:5000]

        create_notification_log(
            order=order,
            channel="WhatsApp",
            event=event,
            status="Success" if response.ok else "Failed",
            recipient=mobile,
            response=response_text,
        )

        if not response.ok:
            print("WHATSAPP ERROR:", response.text)
            return None

        return response.json()

    except Exception as e:
        create_notification_log(
            order=order,
            channel="WhatsApp",
            event=event,
            status="Failed",
            recipient=mobile,
            response=str(e),
        )
        raise


def send_whatsapp_event(order, event):
    customer = order.customer

    if not customer or not customer.mobile:
        return None

    if event == ORDER_PAID:
        return send_whatsapp_template(
            order=order,
            to=customer.mobile,
            template_name=settings.WHATSAPP_ORDER_PAID_TEMPLATE,
            event=ORDER_PAID,
            parameters=[
                customer.name,
                order.order_id,
                f"₹{order.total}",
            ]
        )

    elif event == TRACKING_AVAILABLE:
        return send_whatsapp_template(
            order=order,
            to=customer.mobile,
            template_name=settings.WHATSAPP_TRACKING_TEMPLATE,
            event=TRACKING_AVAILABLE,
            parameters=[
                customer.name,
                order.order_id,
                order.tracking_url or "Tracking will be updated shortly",
            ]
        )

    elif event == ORDER_CANCELLED:
        return send_whatsapp_template(
            order=order,
            to=customer.mobile,
            template_name=settings.WHATSAPP_ORDER_CANCELLED_TEMPLATE,
            event=ORDER_CANCELLED,
            parameters=[
                customer.name,
                order.order_id,
            ]
        )

    elif event == PAYMENT_ABANDONED:
        resume_url = (
            settings.SITE_URL
            + reverse(
                "PayURedirect",
                kwargs={
                    "order_id": order.order_id
                }
            )
        )

        return send_whatsapp_template(
            order=order,
            to=customer.mobile,
            template_name=settings.WHATSAPP_PAYMENT_ABANDONED_TEMPLATE,
            event=PAYMENT_ABANDONED,
            parameters=[
                customer.name,
                order.order_id,
                f"₹{order.total}",
                resume_url,
            ]
        )
    
    elif event == INVOICE_AVAILABLE:
        return send_whatsapp_template(
            customer.mobile,
            settings.WHATSAPP_INVOICE_TEMPLATE,
            [
                customer.name,
                order.invoice_number,
                order.order_id,
                f"₹{order.total}",
                settings.SITE_URL + reverse(
                    "AdminViewInvoice",
                    kwargs={"code": order.unique_code}
                )
            ]
        )

    return None