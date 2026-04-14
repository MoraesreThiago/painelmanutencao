from django.contrib import admin

from apps.ocorrencias.models import BurnedMotorRecord, InstrumentServiceRequest, Movement, Occurrence


@admin.register(Occurrence)
class OccurrenceAdmin(admin.ModelAdmin):
    list_display = ("equipment", "classification", "status", "occurred_at", "area", "had_downtime")
    list_filter = ("classification", "status", "had_downtime", "area")
    search_fields = ("equipment__code", "equipment__tag", "description", "notes")
    autocomplete_fields = ("equipment", "area", "location", "responsible_collaborator", "reported_by_user")


@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ("equipment", "moved_by_user", "moved_at", "reason")
    search_fields = ("equipment__code", "equipment__description", "reason")
    autocomplete_fields = ("equipment", "previous_location", "new_location", "moved_by_user")


@admin.register(BurnedMotorRecord)
class BurnedMotorRecordAdmin(admin.ModelAdmin):
    list_display = ("motor", "area", "status", "recorded_at", "recorded_by_user")
    list_filter = ("status", "area")
    search_fields = ("motor__unique_identifier", "source_equipment_tag", "diagnosis")
    autocomplete_fields = ("area", "motor", "recorded_by_user")


@admin.register(InstrumentServiceRequest)
class InstrumentServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("instrument", "service_type", "service_status", "requested_at", "area")
    list_filter = ("service_type", "service_status", "area")
    search_fields = ("instrument__unique_identifier", "vendor_name", "reason")
    autocomplete_fields = ("area", "instrument", "registered_by_user")
