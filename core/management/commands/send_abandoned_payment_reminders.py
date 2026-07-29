from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Order
from core.services.notifications import (
    send_order_notification,
    PAYMENT_ABANDONED,
)


class Command(BaseCommand):
    help = "Send abandoned payment reminders"

    def handle(self, *args, **kwargs):
        cutoff = timezone.now() - timedelta(minutes=45)

        orders = Order.objects.filter(
            payment_status="Pending",
            status="Pending",
            payment_reminder_sent=False,
            created_at__lte=cutoff,
            is_deleted=False,
        ).exclude(
            customer__mobile=""
        ).exclude(
            customer__email=""
        )

        for order in orders:
            try:
                send_order_notification(
                    order,
                    PAYMENT_ABANDONED
                )

                order.payment_reminder_sent = True
                order.payment_reminder_sent_at = timezone.now()

                order.save(
                    update_fields=[
                        "payment_reminder_sent",
                        "payment_reminder_sent_at",
                    ]
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Reminder sent for {order.order_id}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"{order.order_id}: {e}"
                    )
                )