import requests
from django.conf import settings


INCH_TO_CM = 2.54


def safe_float(value, default=0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def get_order_dimensions(order):
    length_cm = 0
    breadth_cm = 0
    height_cm = 0
    weight_kg = 0

    for item in order.items.select_related("product"):
        product = item.product
        qty = int(item.quantity or 1)

        product_length_cm = safe_float(getattr(product, "width", None), 1) * INCH_TO_CM
        product_breadth_cm = safe_float(getattr(product, "width", None), 1) * INCH_TO_CM
        product_height_cm = safe_float(getattr(product, "height", None), 1) * INCH_TO_CM
        product_weight_kg = safe_float(getattr(product, "weight", None), 0.5)

        length_cm = max(length_cm, product_length_cm)
        breadth_cm = max(breadth_cm, product_breadth_cm)
        height_cm += product_height_cm * qty
        weight_kg += product_weight_kg * qty

    return {
        "length": max(round(length_cm, 2), 1),
        "breadth": max(round(breadth_cm, 2), 1),
        "height": max(round(height_cm, 2), 1),
        "weight": max(round(weight_kg, 2), 0.5),
    }


def get_shiprocket_token():
    url = f"{settings.SHIPROCKET_BASE_URL}/auth/login"

    response = requests.post(url, json={
        "email": settings.SHIPROCKET_EMAIL,
        "password": settings.SHIPROCKET_PASSWORD,
    }, timeout=30)

    response.raise_for_status()
    data = response.json()

    token = data.get("token")

    if not token:
        raise Exception(f"Shiprocket token missing: {data}")

    return token


def shiprocket_headers():
    token = get_shiprocket_token()

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def create_shiprocket_order(order):
    url = f"{settings.SHIPROCKET_BASE_URL}/orders/create/adhoc"

    order_items = []

    for item in order.items.select_related("product"):
        product = item.product

        order_items.append({
            "name": product.name[:120],
            "sku": product.sku or product.product_code or str(product.id),
            "units": int(item.quantity),
            "selling_price": float(item.price),
        })

    billing = order.billing_address
    shipping = order.shipping_address
    customer = order.customer
    dimensions = get_order_dimensions(order)

    payload = {
        "order_id": order.order_id,
        "order_date": order.created_at.strftime("%Y-%m-%d %H:%M"),
        "pickup_location": settings.SHIPROCKET_PICKUP_LOCATION,

        "billing_customer_name": customer.name,
        "billing_last_name": "",
        "billing_address": billing.address_line_1,
        "billing_address_2": billing.address_line_2 or "",
        "billing_city": billing.city,
        "billing_pincode": billing.postal_code,
        "billing_state": billing.state,
        "billing_country": billing.country or "India",
        "billing_email": customer.email,
        "billing_phone": customer.mobile,

        "shipping_is_billing": False,
        "shipping_customer_name": customer.name,
        "shipping_last_name": "",
        "shipping_address": shipping.address_line_1,
        "shipping_address_2": shipping.address_line_2 or "",
        "shipping_city": shipping.city,
        "shipping_pincode": shipping.postal_code,
        "shipping_state": shipping.state,
        "shipping_country": shipping.country or "India",
        "shipping_email": customer.email,
        "shipping_phone": customer.mobile,

        "order_items": order_items,
        "payment_method": "Prepaid",
        "sub_total": float(order.subtotal),

        "length": dimensions["length"],
        "breadth": dimensions["breadth"],
        "height": dimensions["height"],
        "weight": dimensions["weight"],
    }

    response = requests.post(
        url,
        json=payload,
        headers=shiprocket_headers(),
        timeout=30
    )

    if not response.ok:
        raise Exception(f"Shiprocket order error: {response.text}")

    return response.json()


def assign_awb(shipment_id):
    url = f"{settings.SHIPROCKET_BASE_URL}/courier/assign/awb"

    response = requests.post(
        url,
        json={"shipment_id": shipment_id},
        headers=shiprocket_headers(),
        timeout=30
    )

    if not response.ok:
        raise Exception(f"Shiprocket AWB error: {response.text}")

    return response.json()


def track_by_awb(awb_code):
    url = f"{settings.SHIPROCKET_BASE_URL}/courier/track/awb/{awb_code}"

    response = requests.get(
        url,
        headers=shiprocket_headers(),
        timeout=30
    )

    if not response.ok:
        raise Exception(f"Shiprocket tracking error: {response.text}")

    return response.json()

def generate_pickup(shipment_id):
    url = f"{settings.SHIPROCKET_BASE_URL}/courier/generate/pickup"

    response = requests.post(
        url,
        json={"shipment_id": [int(shipment_id)]},
        headers=shiprocket_headers(),
        timeout=30
    )

    if not response.ok:
        raise Exception(f"Shiprocket pickup error: {response.text}")

    return response.json()


def generate_label(shipment_id):
    url = f"{settings.SHIPROCKET_BASE_URL}/courier/generate/label"

    response = requests.post(
        url,
        json={"shipment_id": [int(shipment_id)]},
        headers=shiprocket_headers(),
        timeout=30
    )

    if not response.ok:
        raise Exception(f"Shiprocket label error: {response.text}")

    return response.json()


def generate_invoice(order_id):
    url = f"{settings.SHIPROCKET_BASE_URL}/orders/print/invoice"

    response = requests.post(
        url,
        json={"ids": [int(order_id)]},
        headers=shiprocket_headers(),
        timeout=30
    )

    if not response.ok:
        raise Exception(f"Shiprocket invoice error: {response.text}")

    return response.json()