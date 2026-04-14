from django.contrib import admin

from apps.access.models import Role, UserArea


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


@admin.register(UserArea)
class UserAreaAdmin(admin.ModelAdmin):
    list_display = ("user", "area", "created_at")
    search_fields = ("user__full_name", "user__email", "area__name")
    autocomplete_fields = ("user", "area")
