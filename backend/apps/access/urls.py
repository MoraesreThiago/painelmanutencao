from django.urls import path

from apps.access import views


app_name = "access"

urlpatterns = [
    path("dashboard/", views.LegacyDashboardRedirectView.as_view(), name="dashboard"),
    path("PainelPrincipal/", views.LegacyDashboardRedirectView.as_view(), name="area-dashboard-legacy"),
    path("painelprincipal/", views.DashboardView.as_view(), name="area-dashboard"),
    path("contexto/aplicar/", views.ContextSwitchView.as_view(), name="context-switch"),
    path("contexto/restaurar/", views.ContextResetView.as_view(), name="context-reset"),
    path("dashboard/metricas/", views.DashboardMetricsPartialView.as_view(), name="dashboard-metrics"),
    path("energia/tensao-corrente-geracao/", views.PowerMonitoringView.as_view(), name="power-monitoring"),
    path("relatorios/resumo-mensal/", views.MonthlySummaryView.as_view(), name="monthly-summary"),
    path("eletrica/", views.ElectricalWorkspaceView.as_view(), name="workspace-eletrica"),
    path("mecanica/", views.MechanicalWorkspaceView.as_view(), name="workspace-mecanica"),
    path("instrumentacao/", views.InstrumentationWorkspaceView.as_view(), name="workspace-instrumentacao"),
]
