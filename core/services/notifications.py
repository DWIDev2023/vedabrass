ORDER_PAID = "order_paid"
TRACKING_AVAILABLE = "tracking_available"
ORDER_CANCELLED = "order_cancelled"
PAYMENT_ABANDONED = "payment_abandoned"
INVOICE_AVAILABLE = "invoice_available"

def send_order_notification(order, event):
    from core.services.email import send_order_email_event
    try:
        send_order_email_event(order, event)
    except Exception as e:
        print("EMAIL ERROR:", e)

    from core.services.whatsapp import send_whatsapp_event
    try:
        send_whatsapp_event(order, event)
    except Exception as e:
        print("WHATSAPP NOTIFICATION ERROR:", e)

    from core.services.sms import send_sms_event
    try:
        send_sms_event(order, event)
    except Exception as e:
        print("SMS ERROR:", e)
