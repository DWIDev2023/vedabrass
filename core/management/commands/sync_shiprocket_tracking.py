from django.core.management.base import BaseCommand
from core.models import Order
from core.utils.shiprocket import track_by_awb


class Command(BaseCommand):
    help = "Sync Shiprocket tracking status"

    def handle(self, *args, **kwargs):
        orders = Order.objects.filter(
            is_deleted=False,
            payment_status="Paid",
        ).exclude(
            shiprocket_awb_code__isnull=True
        ).exclude(
            shiprocket_awb_code=""
        )

        for order in orders:
            try:
                response = track_by_awb(order.shiprocket_awb_code)
                tracking_data = response.get("tracking_data", {})

                track_url = (
                    tracking_data.get("track_url")
                    or tracking_data.get("tracking_url")
                    or order.tracking_url
                )

                shipment_status = None

                shipment_track = tracking_data.get("shipment_track")

                if shipment_track:
                    shipment_status = shipment_track[0].get("current_status")

                if track_url:
                    order.tracking_url = track_url

                if shipment_status:
                    order.shipment_status = shipment_status

                order.save(
                    update_fields=[
                        "tracking_url",
                        "shipment_status",
                    ]
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Tracking synced: {order.order_id}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"{order.order_id}: {e}"
                    )
                )