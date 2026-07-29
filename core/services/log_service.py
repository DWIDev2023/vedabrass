from core.models import NotificationLog

def create_notification_log(
    order,
    channel,
    event,
    status,
    recipient=None,
    response=None,
):
    NotificationLog.objects.create(
        order=order,
        channel=channel,
        event=event,
        status=status,
        recipient=recipient,
        response=response,
    )