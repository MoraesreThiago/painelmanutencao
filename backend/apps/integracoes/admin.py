from django.contrib import admin

from apps.integracoes.models import SyncOutboxEntry


@admin.register(SyncOutboxEntry)
class SyncOutboxEntryAdmin(admin.ModelAdmin):
    list_display = ("entity_name", "action", "source", "received_at", "synced_at")
    list_filter = ("source", "action")
    search_fields = ("entity_name", "entity_id", "action")
