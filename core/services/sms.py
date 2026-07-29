import re, requests
from django.conf import settings
from django.urls import reverse
from core.services.notifications import (
    ORDER_PAID,
    TRACKING_AVAILABLE,
    ORDER_CANCELLED,
    PAYMENT_ABANDONED,
    INVOICE_AVAILABLE
)
from core.services.log_service import (
    create_notification_log,
)

def normalize_sms_mobile(mobile):
    mobile = str(mobile or "").strip()
    mobile = mobile.replace(" ", "").replace("-", "")

    if mobile.startswith("+91"):
        mobile = mobile[3:]

    if mobile.startswith("91") and len(mobile) == 12:
        mobile = mobile[2:]

    if not re.match(r"^[6-9][0-9]{9}$", mobile):
        return None

    return f"91{mobile}"

def send_sms(order, mobile, message, event):
    mobile = normalize_sms_mobile(mobile)

    if not settings.SMS_ENABLED:
        create_notification_log(
            order=order,
            channel="SMS",
            event=event,
            status="Failed",
            recipient=str(mobile),
            response="SMS Disabled",
        )
        return None

    if not mobile:
        create_notification_log(
            order=order,
            channel="SMS",
            event=event,
            status="Failed",
            recipient=str(mobile),
            response="Invalid Mobile Number",
        )
        return None

    payload = {
        "key": settings.SMS_API_KEY,
        "campaign": settings.SMS_CAMPAIGN,
        "routeid": settings.SMS_ROUTE_ID,
        "type": "text",
        "contacts": mobile,
        "senderid": settings.SMS_SENDER_ID,
        "msg": message,
    }

    try:
        response = requests.post(
            settings.SMS_API_URL,
            data=payload,
            timeout=30
        )

        create_notification_log(
            order=order,
            channel="SMS",
            event=event,
            status="Success" if response.ok else "Failed",
            recipient=mobile,
            response=response.text[:5000],
        )

        return response.text

    except Exception as e:
        create_notification_log(
            order=order,
            channel="SMS",
            event=event,
            status="Failed",
            recipient=mobile,
            response=str(e),
        )
        raise

def send_sms_event(order, event):
    customer = order.customer

    if not customer or not customer.mobile:
        return None

    if event == ORDER_PAID:
        message = (
            f"Thank you for your order with VedaBrass. "
            f"Order ID: {order.order_id}. "
            f"We will notify you once it is shipped. "
            f"Thank you for shopping with us. "
            f"By Bright Saffron."
        )

        return send_sms(
            order,
            customer.mobile,
            message,
            ORDER_PAID
        )

    elif event == TRACKING_AVAILABLE:
        message = (
            f"Your VedaBrass order {order.order_id} has been shipped. "
            f"Track here: {order.tracking_url} "
            f"By Bright Saffron"
        )

        return send_sms(
            order,
            customer.mobile,
            message,
            TRACKING_AVAILABLE
        )

    elif event == ORDER_CANCELLED:
        message = (
            f"Your VedaBrass order {order.order_id} has been cancelled. "
            f"For support please contact VedaBrass. "
            f"By Bright Saffron"
        )

        return send_sms(
            order,
            customer.mobile,
            message,
            ORDER_CANCELLED
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

        message = (
            f"Your VedaBrass order {order.order_id} is waiting for payment. "
            f"Complete your order here: {resume_url} "
            f"By Bright Saffron"
        )

        return send_sms(
            order,
            customer.mobile,
            message,
            PAYMENT_ABANDONED
        )
    
    elif event == INVOICE_AVAILABLE:
        invoice_url = (
            settings.SITE_URL +
            reverse(
                "AdminViewInvoice",
                kwargs={
                    "code": order.unique_code
                }
            )
        )

        message = (
            f"VedaBrass Invoice for your order has been generated. "
            f"Order ID: {order.order_id}. "
            f"View: {invoice_url} "
            f"Thank you for shopping with VedaBrass. "
            f"By Bright Saffron"
        )

        return send_sms(
            customer.mobile,
            message
        )

    return None