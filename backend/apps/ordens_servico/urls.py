from django.urls import path

from apps.ordens_servico import views


app_name = "ordens-servico"

urlpatterns = [
    path("ordens-servico/", views.ServiceOrderListView.as_view(), name="list"),
    path("ordens-servico/<uuid:pk>/", views.ServiceOrderDetailView.as_view(), name="detail"),
]
