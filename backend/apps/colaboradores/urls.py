from django.urls import path

from apps.colaboradores.views import TeamManagementListView


app_name = "colaboradores"

urlpatterns = [
    path("equipe/", TeamManagementListView.as_view(), name="team"),
]
