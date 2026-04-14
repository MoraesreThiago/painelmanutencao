from django.contrib import admin

from apps.colaboradores.models import Collaborator


@admin.register(Collaborator)
class CollaboratorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "registration_number", "job_title", "area", "status")
    list_filter = ("area", "status")
    search_fields = ("full_name", "registration_number", "job_title")
    autocomplete_fields = ("area", "linked_user")
