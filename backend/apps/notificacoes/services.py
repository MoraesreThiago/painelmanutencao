from apps.notificacoes.models import NotificationEvent
from common.enums import NotificationStatus


def pending_notifications():
    return NotificationEvent.objects.filter(status=NotificationStatus.PENDING).order_by("occurred_at")
