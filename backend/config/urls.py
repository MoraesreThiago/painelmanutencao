from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("", include("common.urls")),
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("", include("apps.access.urls")),
    path("", include("apps.assistente.urls")),
    path("", include("apps.colaboradores.urls")),
    path("", include("apps.equipamentos.urls")),
    path("", include("apps.motores.urls")),
    path("", include("apps.ocorrencias.urls")),
    path("", include("apps.ordens_servico.urls")),
    path("api/v1/", include("api.v1.urls")),
]
