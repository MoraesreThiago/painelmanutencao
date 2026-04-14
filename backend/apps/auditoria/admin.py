from django.contrib import admin

from apps.auditoria.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("entity_name", "entity_id", "action", "actor_user", "created_at")
    list_filter = ("entity_name", "action")
    search_fields = ("entity_name", "entity_id", "summary")
    autocomplete_fields = ("actor_user", "area")
