from django.urls import path

from apps.motores.views import (
    BurnedMotorCaseCreateView,
    BurnedMotorCaseDetailView,
    BurnedMotorCaseListView,
    BurnedMotorCaseSendPCMEmailView,
    BurnedMotorCaseStatusUpdateView,
    BurnedMotorCaseUpdateView,
    BurnedMotorProcessCreateView,
    BurnedMotorProcessUpdateView,
    MotorCreateView,
    MotorDetailView,
    MotorListView,
    MotorUpdateView,
)


app_name = "motores"

urlpatterns = [
    path("motores-eletricos/", MotorListView.as_view(), name="list"),
    path("motores-eletricos/novo/", MotorCreateView.as_view(), name="create"),
    path("motores-eletricos/<uuid:pk>/", MotorDetailView.as_view(), name="detail"),
    path("motores-eletricos/<uuid:pk>/editar/", MotorUpdateView.as_view(), name="update"),
    path("motores-queimados/", BurnedMotorCaseListView.as_view(), name="burned-case-list"),
    path("motores-queimados/novo/", BurnedMotorCaseCreateView.as_view(), name="burned-case-create"),
    path("motores-queimados/<uuid:pk>/", BurnedMotorCaseDetailView.as_view(), name="burned-case-detail"),
    path("motores-queimados/<uuid:pk>/editar/", BurnedMotorCaseUpdateView.as_view(), name="burned-case-update"),
    path("motores-queimados/<uuid:pk>/status/", BurnedMotorCaseStatusUpdateView.as_view(), name="burned-case-status"),
    path("motores-queimados/<uuid:pk>/enviar-pcm/", BurnedMotorCaseSendPCMEmailView.as_view(), name="burned-case-send-pcm"),
    path("motores-eletricos/<uuid:motor_pk>/fluxos/novo/", BurnedMotorProcessCreateView.as_view(), name="flow-create"),
    path(
        "motores-eletricos/<uuid:motor_pk>/fluxos/<uuid:process_pk>/editar/",
        BurnedMotorProcessUpdateView.as_view(),
        name="flow-update",
    ),
]
