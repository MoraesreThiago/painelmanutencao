from django.utils import timezone

from apps.integracoes.models import SyncOutboxEntry


def enqueue_sync_item(*, entity_name: str, action: str, payload: dict, entity_id: str | None = None):
    return SyncOutboxEntry.objects.create(
        entity_name=entity_name,
        entity_id=entity_id,
        action=action,
        payload=payload,
    )


def mark_sync_processed(entry: SyncOutboxEntry):
    entry.synced_at = timezone.now()
    entry.last_error = ""
    entry.save(update_fields=["synced_at", "last_error", "updated_at"])
    return entry
