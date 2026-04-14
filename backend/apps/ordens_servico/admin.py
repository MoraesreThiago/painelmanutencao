from django.contrib import admin

from apps.ordens_servico.models import ExternalServiceOrder


@admin.register(ExternalServiceOrder)
class ExternalServiceOrderAdmin(admin.ModelAdmin):
    list_display = ("work_order_number", "motor", "vendor_name", "service_status", "sent_at")
    list_filter = ("service_status",)
    search_fields = ("work_order_number", "vendor_name", "motor__unique_identifier", "reason")
    autocomplete_fields = ("motor", "authorized_by_user", "registered_by_user")
