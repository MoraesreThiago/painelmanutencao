from django.urls import path

from apps.ocorrencias import views


app_name = "ocorrencias"

urlpatterns = [
    path("ocorrencias/", views.OccurrenceListView.as_view(), name="list"),
    path("ocorrencias/historico/", views.OccurrenceHistoryView.as_view(), name="history"),
    path("ocorrencias/nova/", views.OccurrenceCreateView.as_view(), name="create"),
    path("ocorrencias/<uuid:pk>/", views.OccurrenceDetailView.as_view(), name="detail"),
    path("ocorrencias/<uuid:pk>/editar/", views.OccurrenceUpdateView.as_view(), name="update"),
    path("ocorrencias/<uuid:pk>/status/", views.OccurrenceStatusUpdateView.as_view(), name="update-status"),
]
