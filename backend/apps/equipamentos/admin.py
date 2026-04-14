from django.contrib import admin

from apps.equipamentos.models import Equipment, Instrument, Motor


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("code", "description", "type", "status", "area", "location")
    list_filter = ("type", "status", "area")
    search_fields = ("code", "tag", "description", "serial_number")
    autocomplete_fields = ("area", "location")


@admin.register(Motor)
class MotorAdmin(admin.ModelAdmin):
    list_display = ("unique_identifier", "equipment", "current_status", "last_internal_service_at")
    list_filter = ("current_status",)
    search_fields = ("unique_identifier", "equipment__code", "equipment__description")
    autocomplete_fields = ("equipment",)


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ("unique_identifier", "instrument_type", "current_status", "calibration_due_date")
    list_filter = ("current_status", "instrument_type")
    search_fields = ("unique_identifier", "equipment__code", "equipment__description")
    autocomplete_fields = ("equipment",)
