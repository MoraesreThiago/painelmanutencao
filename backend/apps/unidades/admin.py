from django.contrib import admin

from apps.unidades.models import Area, Fabrica, Location, UnidadeProdutiva


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "sector", "area", "unidade")
    search_fields = ("name", "sector", "area__name", "unidade__name", "unidade__fabrica__name")
    list_filter = ("area", "unidade__fabrica", "unidade")


@admin.register(Fabrica)
class FabricaAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    search_fields = ("name", "code")
    list_filter = ("is_active",)


@admin.register(UnidadeProdutiva)
class UnidadeProdutivaAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "fabrica", "is_active")
    search_fields = ("name", "code", "fabrica__name")
    list_filter = ("fabrica", "is_active")
