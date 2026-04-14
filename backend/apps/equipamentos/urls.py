from django.urls import path

from apps.equipamentos.views import EquipmentCreateView, EquipmentDetailView, EquipmentListView, EquipmentToggleStatusView, EquipmentUpdateView


app_name = "equipamentos"

urlpatterns = [
    path("equipamentos/", EquipmentListView.as_view(), name="list"),
    path("equipamentos/novo/", EquipmentCreateView.as_view(), name="create"),
    path("equipamentos/<uuid:pk>/", EquipmentDetailView.as_view(), name="detail"),
    path("equipamentos/<uuid:pk>/editar/", EquipmentUpdateView.as_view(), name="update"),
    path("equipamentos/<uuid:pk>/alternar-status/", EquipmentToggleStatusView.as_view(), name="toggle-status"),
]
