from django.contrib import admin

from apps.notificacoes.models import NotificationEvent


@admin.register(NotificationEvent)
class NotificationEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "entity_name", "entity_id", "status", "occurred_at")
    list_filter = ("status", "event_type")
    search_fields = ("entity_name", "entity_id", "event_type")
    autocomplete_fields = ("area",)
