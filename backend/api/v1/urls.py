from django.urls import path

from api.v1.views import (
    CurrentUserApiView,
    DashboardApiView,
    EquipmentDetailApiView,
    EquipmentListCreateApiView,
    EquipmentToggleStatusApiView,
    OccurrenceDetailApiView,
    OccurrenceListCreateApiView,
    OccurrenceStatusApiView,
    OfflineOutboxApiView,
    SessionLoginApiView,
    SessionLogoutApiView,
)


urlpatterns = [
    path("auth/login/", SessionLoginApiView.as_view(), name="api-login"),
    path("auth/logout/", SessionLogoutApiView.as_view(), name="api-logout"),
    path("auth/me/", CurrentUserApiView.as_view(), name="api-me"),
    path("dashboard/", DashboardApiView.as_view(), name="api-dashboard"),
    path("equipamentos/", EquipmentListCreateApiView.as_view(), name="api-equipamentos"),
    path("equipamentos/<uuid:pk>/", EquipmentDetailApiView.as_view(), name="api-equipamento-detail"),
    path("equipamentos/<uuid:pk>/toggle-status/", EquipmentToggleStatusApiView.as_view(), name="api-equipamento-toggle-status"),
    path("ocorrencias/", OccurrenceListCreateApiView.as_view(), name="api-ocorrencias"),
    path("ocorrencias/<uuid:pk>/", OccurrenceDetailApiView.as_view(), name="api-ocorrencia-detail"),
    path("ocorrencias/<uuid:pk>/status/", OccurrenceStatusApiView.as_view(), name="api-ocorrencia-status"),
    path("sync/outbox/", OfflineOutboxApiView.as_view(), name="api-sync-outbox"),
]
